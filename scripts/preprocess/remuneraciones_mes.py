"""
Procesador para remuneraciones mensuales (nacional_serie_remuneraciones_mensual).

Estructura del Excel (16 hojas):
  C 1: Remuneracion promedio total (por todo concepto + normal y permanente)
  C 2: Remuneracion mediana total
  C 3: Remuneracion promedio (trabajadores con 5+ anios antiguedad)
  C 4: Dispersion salarial (desvio estandar + coef. variacion)
  C 5.1: Remuneracion promedio por sector CIIU (Original)
  C 5.2: Remuneracion promedio por sector CIIU (Desestacionalizada)
  C 5.3: Remuneracion promedio por sector CIIU (Tendencia-Ciclo)
  C 6: Remuneracion mediana por sector CIIU
  C 7: Remuneracion promedio por rama 2 digitos CIIU (transpuesta)
  C 8: Remuneracion promedio por rama 3 digitos CIIU (transpuesta)
  C 9: Remuneracion promedio por rama 4 digitos CIIU (transpuesta)
  Descriptores de actividad: Tabla de codigos CIIU

Datasets generados:
  R1: Remuneracion promedio total (mensual)
  R2: Remuneracion mediana total (mensual)
  R3: Remuneracion promedio por sector letra CIIU (mensual)
  R4: Remuneracion mediana por sector letra CIIU (mensual)
  descriptores_remuneraciones: Tabla de descriptores CIIU

Uso:
    python scripts/preprocess/remuneraciones_mes.py
"""

import sys
import os
import logging
import datetime

import pandas as pd
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from scripts.preprocess.base import ExcelProcessor

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Meses en espanol para formatear periodos
MESES_ES = {
    1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
    5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
    9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
}


def _datetime_to_period(dt):
    """Convierte datetime a string de periodo mensual: 'Enero 2024'."""
    if isinstance(dt, datetime.datetime):
        return f"{MESES_ES.get(dt.month, str(dt.month))} {dt.year}"
    if isinstance(dt, pd.Timestamp):
        return f"{MESES_ES.get(dt.month, str(dt.month))} {dt.year}"
    return None


def _safe_float(val):
    """Convierte un valor a float, manejando 's.d.' y otros no-numericos."""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        if np.isnan(val) or np.isinf(val):
            return None
        return float(val)
    s = str(val).strip().lower()
    if s in ('s.d.', 'sd', 's.d', 'n.d.', '-', '...', ''):
        return None
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


class RemuneracionesMensualesProcessor(ExcelProcessor):
    source_name = 'remuneraciones_mensual'
    frequency = 'monthly'
    raw_filename = 'remuneraciones_mensual.xlsx'

    def process(self):
        sheets = self.read_sheets()
        if not sheets:
            return {}

        datasets = {}

        # R1: Remuneracion promedio total desde hoja "C 1"
        if 'C 1' in sheets:
            df = self._process_c1(sheets['C 1'])
            if not df.empty:
                datasets['R1'] = df
                logger.info(f"  R1: {len(df)} filas")

        # R2: Remuneracion mediana total desde hoja "C 2"
        if 'C 2' in sheets:
            df = self._process_c2(sheets['C 2'])
            if not df.empty:
                datasets['R2'] = df
                logger.info(f"  R2: {len(df)} filas")

        # R3: Remuneracion promedio por sector CIIU desde hoja "C 5.1"
        if 'C 5.1' in sheets:
            df = self._process_sector(sheets['C 5.1'], 'promedio')
            if not df.empty:
                datasets['R3'] = df
                logger.info(f"  R3: {len(df)} filas")

        # R4: Remuneracion mediana por sector CIIU desde hoja "C 6"
        if 'C 6' in sheets:
            df = self._process_sector(sheets['C 6'], 'mediana')
            if not df.empty:
                datasets['R4'] = df
                logger.info(f"  R4: {len(df)} filas")

        # Descriptores de actividad
        if 'Descriptores de actividad' in sheets:
            df = self._process_descriptores(sheets['Descriptores de actividad'])
            if not df.empty:
                datasets['descriptores_remuneraciones'] = df
                logger.info(f"  descriptores_remuneraciones: {len(df)} filas")

        return datasets

    def _process_c1(self, ws):
        """
        Procesa C 1: Remuneracion promedio total.
        Estructura: col 0 = fecha, col 1 = vacia, col 2 = "En $" (Original),
                    col 3 = "Var %" (Original), col 5 = "En $" (Desest.)
        Headers en filas 0-6, datos desde fila 7.
        """
        data = list(ws.iter_rows(values_only=True))
        if len(data) < 8:
            return pd.DataFrame()

        rows = []
        for row in data[7:]:
            if not row or row[0] is None:
                continue
            dt = row[0]
            if not isinstance(dt, (datetime.datetime, pd.Timestamp)):
                continue
            periodo = _datetime_to_period(dt)
            if not periodo:
                continue

            remuneracion = _safe_float(row[2]) if len(row) > 2 else None
            rows.append({
                'Período': periodo,
                'Remuneracion': remuneracion,
            })

        return pd.DataFrame(rows)

    def _process_c2(self, ws):
        """Procesa C 2: Remuneracion mediana total. Misma estructura que C1."""
        data = list(ws.iter_rows(values_only=True))
        if len(data) < 8:
            return pd.DataFrame()

        rows = []
        for row in data[7:]:
            if not row or row[0] is None:
                continue
            dt = row[0]
            if not isinstance(dt, (datetime.datetime, pd.Timestamp)):
                continue
            periodo = _datetime_to_period(dt)
            if not periodo:
                continue

            remuneracion = _safe_float(row[2]) if len(row) > 2 else None
            rows.append({
                'Período': periodo,
                'Remuneracion': remuneracion,
            })

        return pd.DataFrame(rows)

    def _process_sector(self, ws, tipo):
        """
        Procesa hojas C 5.1 / C 6: remuneracion por sector CIIU letra.
        Estructura: fila 4 = headers ('Período', 'A', 'B', ..., 'O', 'Total')
        Datos empiezan en fila 6 (0-indexed).
        """
        data = list(ws.iter_rows(values_only=True))
        if len(data) < 7:
            return pd.DataFrame()

        # Buscar la fila con letras de sector (tipicamente fila 4)
        sector_headers = None
        data_start_idx = 6
        for header_row_idx in range(min(7, len(data))):
            row = data[header_row_idx]
            if row and any(isinstance(c, str) and len(c) == 1 and c.isalpha() and c.upper() != 'L'
                          for c in row if c):
                sector_headers = list(row)
                data_start_idx = header_row_idx + 2  # skip blank row after headers
                break

        if not sector_headers:
            sector_letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'M', 'N', 'O']
            sector_headers = ['Período'] + sector_letters + ['Total']

        rows = []
        for row in data[data_start_idx:]:
            if not row or row[0] is None:
                continue
            dt = row[0]
            if not isinstance(dt, (datetime.datetime, pd.Timestamp)):
                continue
            periodo = _datetime_to_period(dt)
            if not periodo:
                continue

            for col_idx in range(1, min(len(row), len(sector_headers))):
                sector = sector_headers[col_idx]
                if not sector or not isinstance(sector, str):
                    continue
                sector = str(sector).strip()
                if not sector or sector.lower() in ('total', 'período', 'periodo', 'fecha', 'volver al indice'):
                    continue

                valor = _safe_float(row[col_idx])
                rows.append({
                    'Período': periodo,
                    'Sector': sector,
                    'Remuneracion': valor,
                })

        return pd.DataFrame(rows)

    def _process_descriptores(self, ws):
        """Procesa la hoja de descriptores de actividad CIIU."""
        data = list(ws.iter_rows(values_only=True))
        rows = []
        for row in data:
            if not row or row[0] is None:
                continue
            codigo = str(row[0]).strip()
            descripcion = str(row[1]).strip() if len(row) > 1 and row[1] else ''
            if not codigo or not descripcion:
                continue
            # Saltar headers
            if codigo.lower() in ('código', 'codigo', 'cod', 'cód'):
                continue
            rows.append({
                'Código': codigo,
                'Descripción': descripcion,
            })
        return pd.DataFrame(rows)

    def save_parquet(self, datasets=None, output_dir=None):
        """Override para nombres de parquet consistentes."""
        if datasets is None:
            datasets = self.process()
        out = output_dir or self.optimized_dir
        os.makedirs(out, exist_ok=True)

        parquet_names = {
            'R1': 'r1.parquet',
            'R2': 'r2.parquet',
            'R3': 'r3.parquet',
            'R4': 'r4.parquet',
            'descriptores_remuneraciones': 'descriptores_remuneraciones.parquet',
        }

        for key, df in datasets.items():
            if df.empty:
                continue
            name = parquet_names.get(key, f'{key.lower()}.parquet')
            path = os.path.join(out, name)
            df.to_parquet(path, index=False)
            logger.info(f"  {key}: {len(df)} filas -> {path}")


if __name__ == '__main__':
    processor = RemuneracionesMensualesProcessor()

    if not os.path.exists(processor.raw_path):
        logger.error(f"Archivo no encontrado: {processor.raw_path}")
        logger.info("Descargue con: python scripts/download_oede.py --source remuneraciones_mensual")
        sys.exit(1)

    processor.run()
