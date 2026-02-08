"""
Procesador para empresas anuales (nacional_serie_empresas).

Estructura del Excel (14 hojas):
  C 1: Total empresas privadas (anual, por anio)
  C 2: Empresas por sector CIIU letra (anual)
  C 6: Empresas por tamano (Grandes/Medianas/Pequenas/Micro)

Datasets generados:
  E1: Total empresas (anual)
  E2: Empresas por sector letra CIIU (anual)
  E3: Empresas por tamano (anual)

Uso:
    python scripts/preprocess/empresas.py
"""

import sys
import os
import logging

import pandas as pd
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from scripts.preprocess.base import ExcelProcessor

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def _safe_float(val):
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return None if (np.isnan(val) or np.isinf(val)) else float(val)
    s = str(val).strip().lower()
    if s in ('s.d.', 'sd', 's.d', 'n.d.', '-', '...', ''):
        return None
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


class EmpresasAnualProcessor(ExcelProcessor):
    source_name = 'empresas_anual'
    frequency = 'annual'
    raw_filename = 'empresas_anual.xlsx'

    def process(self):
        sheets = self.read_sheets()
        if not sheets:
            return {}

        datasets = {}

        # E1: Total empresas desde hoja "C 1"
        if 'C 1' in sheets:
            df = self._process_c1(sheets['C 1'])
            if not df.empty:
                datasets['E1'] = df
                logger.info(f"  E1: {len(df)} filas")

        # E2: Empresas por sector desde hoja "C 2"
        if 'C 2' in sheets:
            df = self._process_c2(sheets['C 2'])
            if not df.empty:
                datasets['E2'] = df
                logger.info(f"  E2: {len(df)} filas")

        # E3: Empresas por tamano desde hoja "C 6"
        if 'C 6' in sheets:
            df = self._process_c6(sheets['C 6'])
            if not df.empty:
                datasets['E3'] = df
                logger.info(f"  E3: {len(df)} filas")

        return datasets

    def _process_c1(self, ws):
        """
        C 1: Total empresas privadas por anio.
        Estructura: col 0 = anio, col 1 = total empresas, col 2 = var %
        Headers en primeras filas, datos desde ~fila 5.
        """
        data = list(ws.iter_rows(values_only=True))

        rows = []
        for row in data:
            if not row or row[0] is None:
                continue
            # Buscar filas con anio numerico
            try:
                anio = int(row[0])
                if anio < 1990 or anio > 2030:
                    continue
            except (ValueError, TypeError):
                continue

            empresas = _safe_float(row[1])
            rows.append({
                'Período': str(anio),
                'Empresas': empresas,
            })

        return pd.DataFrame(rows)

    def _process_c2(self, ws):
        """
        C 2: Empresas por sector CIIU letra.
        Estructura: col 0 = 'Período', cols 1-14 = sectores A-O, col 15 = Total
        Datos: una fila por anio.
        """
        data = list(ws.iter_rows(values_only=True))

        # Buscar fila de headers con letras de sector
        sector_headers = None
        data_start = 0
        for idx, row in enumerate(data):
            if row and any(isinstance(c, str) and len(c) == 1 and c.isalpha() for c in row if c):
                sector_headers = list(row)
                data_start = idx + 1
                break

        if not sector_headers:
            return pd.DataFrame()

        rows = []
        for row in data[data_start:]:
            if not row or row[0] is None:
                continue
            # Skip blank rows
            try:
                anio = int(row[0])
                if anio < 1990 or anio > 2030:
                    continue
            except (ValueError, TypeError):
                continue

            for col_idx in range(1, min(len(row), len(sector_headers))):
                sector = sector_headers[col_idx]
                if not sector or not isinstance(sector, str):
                    continue
                sector = str(sector).strip()
                if sector.lower() in ('total', 'período', 'periodo'):
                    continue

                empresas = _safe_float(row[col_idx])
                rows.append({
                    'Período': str(anio),
                    'Sector': sector,
                    'Empresas': empresas,
                })

        return pd.DataFrame(rows)

    def _process_c6(self, ws):
        """
        C 6: Empresas por tamano (Grandes/Medianas/Pequenas/Micro).
        Transposed: rows = categorias, columns = anios.
        """
        data = list(ws.iter_rows(values_only=True))

        # Buscar fila de headers con anios
        year_headers = None
        data_start = 0
        for idx, row in enumerate(data):
            if not row:
                continue
            # Check if row contains years as columns
            years = []
            for val in row:
                try:
                    y = int(val)
                    if 1990 <= y <= 2030:
                        years.append(y)
                except (ValueError, TypeError):
                    pass
            if len(years) >= 5:
                year_headers = list(row)
                data_start = idx + 1
                break

        if not year_headers:
            return pd.DataFrame()

        # Build year column mapping
        year_cols = {}
        for col_idx, val in enumerate(year_headers):
            try:
                y = int(val)
                if 1990 <= y <= 2030:
                    year_cols[col_idx] = str(y)
            except (ValueError, TypeError):
                pass

        tamano_keywords = ['grandes', 'medianas', 'pequeñas', 'pequenas', 'micro', 'total']

        rows = []
        for row in data[data_start:]:
            if not row or row[0] is None:
                continue
            cat = str(row[0]).strip()
            if not any(kw in cat.lower() for kw in tamano_keywords):
                continue

            for col_idx, anio in year_cols.items():
                if col_idx < len(row):
                    empresas = _safe_float(row[col_idx])
                    rows.append({
                        'Período': anio,
                        'Tamano': cat.title(),
                        'Empresas': empresas,
                    })

        return pd.DataFrame(rows)

    def save_parquet(self, datasets=None, output_dir=None):
        if datasets is None:
            datasets = self.process()
        out = output_dir or self.optimized_dir
        os.makedirs(out, exist_ok=True)
        parquet_names = {'E1': 'e1.parquet', 'E2': 'e2.parquet', 'E3': 'e3.parquet'}
        for key, df in datasets.items():
            if df.empty:
                continue
            name = parquet_names.get(key, f'{key.lower()}.parquet')
            path = os.path.join(out, name)
            df.to_parquet(path, index=False)
            logger.info(f"  {key}: {len(df)} filas -> {path}")


if __name__ == '__main__':
    processor = EmpresasAnualProcessor()
    if not os.path.exists(processor.raw_path):
        logger.error(f"Archivo no encontrado: {processor.raw_path}")
        logger.info("Descargue con: python scripts/download_oede.py --source empresas_anual")
        sys.exit(1)
    processor.run()
