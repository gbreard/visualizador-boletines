"""
Carga de datos desde archivos locales o base de datos.
Soporta multiples fuentes: empleo, remuneraciones, empresas, flujos, genero.
"""

import os
import logging
import pandas as pd
from src.config import DATA_DIR, OPTIMIZED_DIR, PARQUET_MAPPING, ALL_DATASET_KEYS
from src.data.processing import process_periods, calculate_variations, calculate_variations_generic

logger = logging.getLogger(__name__)

# Datasets que requieren calculo de variaciones (tienen columna Empleo)
VARIATION_KEYS = {'C1.1', 'C1.2', 'C2.1', 'C2.2', 'C3', 'C4', 'C5', 'C6', 'C7'}


def _load_single_file(key):
    """Carga un dataset individual desde Parquet o CSV. Retorna None si no existe."""
    parquet_file = PARQUET_MAPPING.get(key)
    parquet_path = os.path.join(OPTIMIZED_DIR, parquet_file) if parquet_file else None
    csv_path = os.path.join(DATA_DIR, f'{key}.csv')

    if parquet_path and os.path.exists(parquet_path):
        df = pd.read_parquet(parquet_path)
        for col in df.columns:
            if hasattr(df[col], 'cat'):
                df[col] = df[col].astype(df[col].cat.categories.dtype)
        logger.info(f"  {key}: {len(df)} registros desde Parquet")
        return df
    elif os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        logger.info(f"  {key}: {len(df)} registros desde CSV")
        return df

    return None


def load_from_files():
    """Carga todos los datos desde Parquet (si existe) o CSV."""
    logger.info("Cargando datos desde archivos locales...")
    data = {}

    for key in ALL_DATASET_KEYS:
        df = _load_single_file(key)
        if df is None:
            # Solo advertir si es un dataset de empleo (obligatorios)
            if key.startswith('C') or key == 'descriptores_CIIU':
                logger.warning(f"  {key}: No se encontro archivo")
            continue

        if 'Período' in df.columns:
            df = process_periods(df)

        if key in VARIATION_KEYS:
            df = calculate_variations(df)

        data[key] = df

    # Post-procesamiento: variaciones mensuales y salario real
    _compute_monthly_variations(data)

    loaded = [k for k in data.keys()]
    logger.info(f"Datasets cargados: {len(loaded)} ({', '.join(loaded)})")
    return data


def _compute_monthly_variations(data):
    """Calcula variaciones mensuales para R1, R2, IPC y genera datasets de salario real."""
    # Variaciones para IPC
    if 'IPC' in data:
        data['IPC'] = calculate_variations_generic(data['IPC'], 'IPC', periods_short=1, periods_yoy=12)
        logger.info("  IPC: variaciones mensuales calculadas")

    # Variaciones para R1, R2 (remuneracion nominal)
    for key in ('R1', 'R2'):
        if key in data:
            data[key] = calculate_variations_generic(data[key], 'Remuneracion', periods_short=1, periods_yoy=12)
            logger.info(f"  {key}: variaciones mensuales calculadas")

    # Salario real: deflactar R1/R2 por IPC
    if 'IPC' not in data:
        return

    ipc_df = data['IPC']
    if 'Date' not in ipc_df.columns:
        return

    for key_nom, key_real in [('R1', 'R1_real'), ('R2', 'R2_real')]:
        if key_nom not in data:
            continue
        df_nom = data[key_nom]
        if 'Date' not in df_nom.columns:
            continue

        # Merge por Date
        df_merged = df_nom.merge(
            ipc_df[['Date', 'IPC']],
            on='Date',
            how='inner'
        )

        if df_merged.empty or df_merged['IPC'].isna().all():
            logger.warning(f"  {key_real}: sin datos tras merge con IPC")
            continue

        # Deflactar: salario_real = salario_nominal / IPC * 100
        df_merged['Remuneracion_Real'] = df_merged['Remuneracion'] / df_merged['IPC'] * 100

        # Calcular variaciones del salario real
        df_merged = calculate_variations_generic(
            df_merged, 'Remuneracion_Real', periods_short=1, periods_yoy=12
        )

        data[key_real] = df_merged
        logger.info(f"  {key_real}: {len(df_merged)} filas (salario real calculado)")

    # Salario real sectorial: deflactar R3 por IPC
    if 'R3' in data and 'Date' in data['R3'].columns:
        df_r3 = data['R3']
        df_merged = df_r3.merge(
            ipc_df[['Date', 'IPC']],
            on='Date',
            how='inner'
        )
        if not df_merged.empty and not df_merged['IPC'].isna().all():
            df_merged['Remuneracion_Real'] = df_merged['Remuneracion'] / df_merged['IPC'] * 100
            data['R3_real'] = df_merged
            logger.info(f"  R3_real: {len(df_merged)} filas (salario real por sector)")


def load_all_data():
    """Carga datos con fallback: BD -> archivos locales."""
    engine = _get_engine()
    if engine:
        try:
            return load_from_db(engine)
        except Exception as e:
            logger.warning(f"BD fallo ({e}), fallback a archivos")
    return load_from_files()


def _get_engine():
    """Obtiene engine de SQLAlchemy si DATABASE_URL esta configurada."""
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        return None
    try:
        from sqlalchemy import create_engine
        return create_engine(db_url)
    except Exception as e:
        logger.warning(f"No se pudo crear engine: {e}")
        return None


def load_from_db(engine):
    """Carga datos desde PostgreSQL."""
    logger.info("Cargando datos desde PostgreSQL...")
    data = {}

    # C1.1 y C1.2: empleo total
    for key, serie in [('C1.1', 'estacional'), ('C1.2', 'desest')]:
        query = """
            SELECT p.periodo_texto as "Período", et.empleo as "Empleo",
                   et.var_trim, et.var_interanual as var_yoy
            FROM empleo_total et
            JOIN periodos p ON et.periodo_id = p.id
            WHERE et.serie = %s AND et.sector IS NULL
            ORDER BY p.fecha
        """
        df = pd.read_sql(query, engine, params=[serie])
        df = process_periods(df)
        if 'Empleo' in df.columns and len(df) > 0 and df['Empleo'].iloc[0] != 0:
            df['index_100'] = (df['Empleo'] / df['Empleo'].iloc[0]) * 100
        data[key] = df

    # C2.1 y C2.2: empleo por sector
    for key, serie in [('C2.1', 'estacional'), ('C2.2', 'desest')]:
        query = """
            SELECT p.periodo_texto as "Período", et.sector, et.empleo
            FROM empleo_total et
            JOIN periodos p ON et.periodo_id = p.id
            WHERE et.serie = %s AND et.sector IS NOT NULL
            ORDER BY p.fecha
        """
        df = pd.read_sql(query, engine, params=[serie])
        if not df.empty:
            df_pivot = df.pivot_table(index='Período', columns='sector', values='empleo')
            df_pivot = df_pivot.reset_index()
            df_pivot = process_periods(df_pivot)
            data[key] = df_pivot
        else:
            data[key] = pd.DataFrame()

    # C3, C4, C5, C6, C7: empleo sectorial
    for key in ['C3', 'C4', 'C5', 'C6', 'C7']:
        query = """
            SELECT p.periodo_texto as "Período", es.codigo_sector as "Sector", es.empleo as "Empleo"
            FROM empleo_sectorial es
            JOIN periodos p ON es.periodo_id = p.id
            WHERE es.tabla_origen = %s
            ORDER BY p.fecha, es.codigo_sector
        """
        df = pd.read_sql(query, engine, params=[key])
        df = process_periods(df)
        df = calculate_variations(df)
        data[key] = df

    # Descriptores
    query = "SELECT codigo as \"Código\", descripcion as \"Descripción\", tabla_origen as \"Tabla\" FROM sectores_ciiu"
    data['descriptores_CIIU'] = pd.read_sql(query, engine)

    logger.info("Datos cargados desde PostgreSQL")
    return data
