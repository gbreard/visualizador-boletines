"""
Procesador para IPC mensual empalmado.

Fuente: https://github.com/matuteiglesias/IPC-Argentina
CSV con indice de precios mensual base Ene 2016=100.
Serie empalmada 2000-2025 usando IPC provincial (CABA, Cordoba, San Luis).

Dataset generado:
  IPC: Indice de precios al consumidor mensual

Uso:
    python scripts/preprocess/ipc.py
"""

import sys
import os
import logging

import pandas as pd

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW_DIR = os.path.join(BASE_DIR, 'data', 'raw')
PROCESSED_DIR = os.path.join(BASE_DIR, 'data', 'processed')
OPTIMIZED_DIR = os.path.join(BASE_DIR, 'data', 'optimized')

MESES_ES = {
    1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
    5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
    9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
}


def run():
    """Procesa IPC CSV y genera CSV + Parquet."""
    raw_path = os.path.join(RAW_DIR, 'ipc_mensual.csv')
    if not os.path.exists(raw_path):
        logger.error(f"Archivo no encontrado: {raw_path}")
        logger.info("Descargue con: python scripts/download_oede.py --source ipc")
        return None

    logger.info(f"Procesando IPC desde {raw_path}...")

    # Leer CSV: index_col=0 es la fecha (ej: '2024-01-01'), columna 'index' tiene el IPC
    df_raw = pd.read_csv(raw_path, index_col=0, parse_dates=True)

    if 'index' not in df_raw.columns:
        logger.error(f"Columna 'index' no encontrada. Columnas disponibles: {list(df_raw.columns)}")
        return None

    # Construir DataFrame limpio
    rows = []
    for date, row in df_raw.iterrows():
        if pd.isna(row['index']):
            continue
        periodo = f"{MESES_ES.get(date.month, str(date.month))} {date.year}"
        rows.append({
            'Período': periodo,
            'IPC': float(row['index']),
        })

    df = pd.DataFrame(rows)
    logger.info(f"  IPC: {len(df)} filas ({df['Período'].iloc[0]} a {df['Período'].iloc[-1]})")

    # Guardar CSV
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    csv_path = os.path.join(PROCESSED_DIR, 'IPC.csv')
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    logger.info(f"  IPC: {len(df)} filas -> {csv_path}")

    # Guardar Parquet
    os.makedirs(OPTIMIZED_DIR, exist_ok=True)
    parquet_path = os.path.join(OPTIMIZED_DIR, 'ipc.parquet')
    df.to_parquet(parquet_path, index=False)
    logger.info(f"  IPC: {len(df)} filas -> {parquet_path}")

    return {'IPC': df}


if __name__ == '__main__':
    result = run()
    if not result:
        sys.exit(1)
