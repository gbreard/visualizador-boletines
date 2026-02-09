"""
Funciones de procesamiento de datos.
Soporta periodos trimestrales, mensuales y anuales.
"""

import re
import pandas as pd
from src.config import TRIMESTRE_MES

# Mapeo de meses en espanol a numero
MES_MAP = {
    'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
    'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
    'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12,
    'ene': 1, 'feb': 2, 'mar': 3, 'abr': 4,
    'may': 5, 'jun': 6, 'jul': 7, 'ago': 8,
    'sep': 9, 'oct': 10, 'nov': 11, 'dic': 12,
}


def parse_period_string(period_str):
    """
    Convierte un string de periodo a pd.Timestamp.
    Soporta:
      - Trimestral: '4o Trim 2004', '1er Trim 2024'
      - Mensual: 'Enero 2024', 'Ene 2024', '01/2024', '2024-01'
      - Anual: '2024'
    """
    if not period_str:
        return None
    try:
        s = str(period_str).strip().rstrip('*')

        # Trimestral: '4o Trim 2004'
        parts = s.split(' ')
        if len(parts) >= 3 and 'trim' in parts[1].lower():
            trimestre = f"{parts[0]} {parts[1]}"
            year = int(parts[2])
            month = TRIMESTRE_MES.get(trimestre, 2)
            return pd.Timestamp(year=year, month=month, day=1)

        # Mensual: 'Enero 2024' o 'Ene 2024'
        if len(parts) == 2:
            mes_str = parts[0].lower().rstrip('.')
            if mes_str in MES_MAP:
                month = MES_MAP[mes_str]
                year = int(parts[1])
                return pd.Timestamp(year=year, month=month, day=1)

        # Mensual: '01/2024' o '1/2024'
        m = re.match(r'^(\d{1,2})/(\d{4})$', s)
        if m:
            month, year = int(m.group(1)), int(m.group(2))
            return pd.Timestamp(year=year, month=month, day=1)

        # Mensual: '2024-01'
        m = re.match(r'^(\d{4})-(\d{1,2})$', s)
        if m:
            year, month = int(m.group(1)), int(m.group(2))
            return pd.Timestamp(year=year, month=month, day=1)

        # Anual: '2024'
        m = re.match(r'^(\d{4})$', s)
        if m:
            year = int(m.group(1))
            return pd.Timestamp(year=year, month=7, day=1)  # Mitad del anio

        return None
    except Exception:
        return None


def detect_frequency(df):
    """
    Detecta la frecuencia de un DataFrame basandose en la columna Date.
    Retorna 'monthly', 'quarterly', 'annual' o 'unknown'.
    """
    if df.empty or 'Date' not in df.columns:
        return 'unknown'

    dates = df['Date'].dropna().sort_values().unique()
    if len(dates) < 2:
        return 'unknown'

    # Calcular diferencias medianas en dias
    diffs = pd.Series(dates[1:]) - pd.Series(dates[:-1])
    median_days = diffs.dt.days.median()

    if median_days < 50:
        return 'monthly'
    elif median_days < 120:
        return 'quarterly'
    else:
        return 'annual'


def process_periods(df):
    """Convierte la columna Periodo a formato Date y agrega columnas auxiliares."""
    if 'Período' not in df.columns or df.empty:
        return df

    df = df.copy()
    df['Date'] = pd.to_datetime(df['Período'].apply(parse_period_string))
    valid = df['Date'].notna()
    if valid.any():
        df.loc[valid, 'Year'] = df.loc[valid, 'Date'].dt.year.astype(int)
        df.loc[valid, 'Quarter'] = df.loc[valid, 'Date'].dt.quarter.astype(int)
    else:
        df['Year'] = None
        df['Quarter'] = None
    return df


def calculate_variations(df):
    """Calcula variaciones trimestrales e interanuales."""
    if 'Empleo' not in df.columns or 'Date' not in df.columns:
        return df

    df = df.copy()
    df = df.sort_values('Date')
    df['var_trim'] = df['Empleo'].pct_change(fill_method=None) * 100
    df['var_yoy'] = df['Empleo'].pct_change(periods=4, fill_method=None) * 100

    if len(df) > 0 and df['Empleo'].iloc[0] != 0:
        df['index_100'] = (df['Empleo'] / df['Empleo'].iloc[0]) * 100

    return df


def calculate_variations_generic(df, value_col, periods_short=1, periods_yoy=12):
    """
    Calcula variaciones y indice base 100 para cualquier columna y frecuencia.

    Args:
        df: DataFrame con columnas Date y value_col.
        value_col: nombre de la columna de valores (ej: 'Remuneracion', 'IPC').
        periods_short: periodos para variacion corta (1=mensual, 1=trimestral).
        periods_yoy: periodos para variacion interanual (12=mensual, 4=trimestral).

    Returns:
        DataFrame con columnas adicionales: var_periodo, var_yoy, index_100.
    """
    if value_col not in df.columns or 'Date' not in df.columns:
        return df

    df = df.copy()
    df = df.sort_values('Date')
    df['var_periodo'] = df[value_col].pct_change(periods=periods_short, fill_method=None) * 100
    df['var_yoy'] = df[value_col].pct_change(periods=periods_yoy, fill_method=None) * 100

    if len(df) > 0 and df[value_col].iloc[0] != 0:
        df['index_100'] = (df[value_col] / df[value_col].iloc[0]) * 100

    return df


def get_latest_period_data(c1_df):
    """Obtiene datos del ultimo periodo disponible para KPIs."""
    if c1_df.empty or 'Date' not in c1_df.columns:
        return {
            'empleo_actual': 0,
            'var_trim': 0,
            'var_yoy': 0,
            'periodo': 'No disponible',
            'fecha': None
        }

    latest = c1_df.nlargest(1, 'Date').iloc[0]
    return {
        'empleo_actual': latest.get('Empleo', 0),
        'var_trim': latest.get('var_trim', 0),
        'var_yoy': latest.get('var_yoy', 0),
        'index_100': latest.get('index_100', 'N/D'),
        'periodo': latest.get('Período', ''),
        'fecha': latest.get('Date', None)
    }


def get_latest_period_str(df):
    """Obtiene el string del ultimo periodo usando la columna Date (no string max)."""
    if df.empty or 'Date' not in df.columns or 'Período' not in df.columns:
        return None
    return df.loc[df['Date'].idxmax(), 'Período']


def filter_by_dates(df, fecha_desde, fecha_hasta):
    """Filtra un DataFrame por rango de fechas usando strings de periodo."""
    if df.empty or 'Date' not in df.columns:
        return df

    result = df
    # Asegurar que Date sea datetime (puede venir como Categorical de Parquet)
    if hasattr(result['Date'], 'cat'):
        result = result.copy()
        result['Date'] = pd.to_datetime(result['Date'])

    if fecha_desde:
        dt = parse_period_string(fecha_desde)
        if dt:
            result = result[result['Date'] >= dt]
    if fecha_hasta:
        dt = parse_period_string(fecha_hasta)
        if dt:
            result = result[result['Date'] <= dt]
    return result
