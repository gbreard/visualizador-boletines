"""
Funciones de procesamiento de datos.
"""

import pandas as pd
from src.config import TRIMESTRE_MES


def parse_period_string(period_str):
    """Convierte un string de periodo (ej: '4o Trim 2004') a pd.Timestamp."""
    try:
        parts = period_str.strip().rstrip('*').split(' ')
        trimestre = f"{parts[0]} {parts[1]}"
        year = int(parts[2])
        month = TRIMESTRE_MES.get(trimestre, 2)
        return pd.Timestamp(year=year, month=month, day=1)
    except Exception:
        return None


def process_periods(df):
    """Convierte la columna Periodo a formato Date y agrega columnas auxiliares."""
    if 'Período' not in df.columns or df.empty:
        return df

    df = df.copy()
    df['Date'] = pd.to_datetime(df['Período'].apply(parse_period_string))
    df['Year'] = df['Date'].dt.year
    df['Quarter'] = df['Date'].dt.quarter
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
