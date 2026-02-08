"""
Procesador para empleo por genero (boletin_estadisticas_laborales_segun_sexo).

Estructura del Excel (31 hojas):
  C 1.1: Tasas (actividad, empleo, desocupacion) por sexo - serie temporal
  C 1.2: Poblacion (PEA, ocupada, desocupada) en miles por sexo - serie temporal
  C 2.1-C 2.6: Empleo registrado (asalariados) por sexo y sector
  C 3.1-C 3.8: Remuneraciones por sexo
  C 4.1-C 4.2: Brecha salarial
  C 5.1-C 5.2: Puestos de trabajo

Datasets generados:
  G1: Empleo por genero total (serie temporal trimestral)
  G2: Brecha salarial por genero (serie temporal)
  G3: Empleo por genero y sector (ultimo periodo)

Periodos: desde '3 Trim 03' trimestral, formato '3º Trim 2003'

Uso:
    python scripts/preprocess/genero.py
"""

import sys
import os
import logging
import re

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


def _normalize_genero_period(period_str):
    """
    Normaliza periodos de genero: '3° Trim 03' -> '3º Trim 2003'
    Soporta: '3° Trim 03', '1º Trim 2025', '3 trim. 2003', etc.
    """
    if not period_str:
        return None
    s = str(period_str).strip()
    # Normalizar simbolos de grado
    s = s.replace('°', '').replace('º', '')

    # Patron: N trim YYYY o N Trim YY
    m = re.match(r'^(\d)\s*[Tt]rim\.?\s+(\d{2,4})$', s)
    if m:
        trim = m.group(1)
        year_str = m.group(2)
        year = int(year_str)
        if year < 100:
            year += 2000 if year < 50 else 1900
        return f"{trim}º Trim {year}"

    return None


class GeneroProcessor(ExcelProcessor):
    source_name = 'genero'
    frequency = 'quarterly'
    raw_filename = 'genero.xlsx'

    def process(self):
        sheets = self.read_sheets()
        if not sheets:
            return {}

        datasets = {}

        # G1: Empleo por genero desde hoja "C 1.2" (poblacion en miles)
        if 'C 1.2' in sheets:
            df = self._process_empleo_genero(sheets['C 1.2'])
            if not df.empty:
                datasets['G1'] = df
                logger.info(f"  G1: {len(df)} filas")

        # G2: Intentar extraer brecha salarial o remuneraciones por genero
        # Buscar hojas C 3.x o C 4.x
        for sheet_name in ['C 3.1', 'C 4.1']:
            if sheet_name in sheets:
                df = self._process_remuneraciones_genero(sheets[sheet_name])
                if not df.empty:
                    datasets['G2'] = df
                    logger.info(f"  G2 (from {sheet_name}): {len(df)} filas")
                    break

        # G3: Empleo por genero y sector desde C 2.1 o C 2.2
        for sheet_name in ['C 2.1', 'C 2.2']:
            if sheet_name in sheets:
                df = self._process_empleo_sector_genero(sheets[sheet_name])
                if not df.empty:
                    datasets['G3'] = df
                    logger.info(f"  G3 (from {sheet_name}): {len(df)} filas")
                    break

        return datasets

    def _process_empleo_genero(self, ws):
        """
        C 1.2: Poblacion en miles de personas por sexo.
        Estructura:
          Row 3: headers nivel 1 (PEA, Ocupada, Desocupada, Subocupada, Informal, Asalariada)
          Row 4: headers nivel 2 (Mujeres, Varones repetido)
          Row 5+: datos (periodo en col 0)
        Usamos Poblacion Ocupada (cols 3=Mujeres, 4=Varones).
        """
        data = list(ws.iter_rows(values_only=True))
        if len(data) < 6:
            return pd.DataFrame()

        # Buscar fila con 'Mujeres'/'Varones' para encontrar columnas
        mujeres_cols = []
        varones_cols = []
        data_start = 5

        for idx in range(min(7, len(data))):
            row = data[idx]
            if not row:
                continue
            found_gender = False
            for col_idx, val in enumerate(row):
                if val and isinstance(val, str):
                    v = val.strip().lower()
                    if 'mujeres' in v:
                        mujeres_cols.append(col_idx)
                        found_gender = True
                    elif 'varones' in v:
                        varones_cols.append(col_idx)
                        found_gender = True
            if found_gender:
                data_start = idx + 1
                break

        # Buscar columnas de "Poblacion Ocupada" (segunda pareja Mujeres/Varones)
        # Row 3 tiene los nombres de grupo, row 4 tiene Mujeres/Varones
        # "Poblacion Ocupada" esta en cols 3-4 (segunda pareja despues de PEA en 1-2)
        if len(mujeres_cols) >= 2:
            mujeres_col = mujeres_cols[1]  # 2da ocurrencia = Poblacion Ocupada
            varones_col = varones_cols[1]
        elif len(mujeres_cols) == 1:
            mujeres_col = mujeres_cols[0]
            varones_col = varones_cols[0] if varones_cols else mujeres_col + 1
        else:
            # Fallback: Poblacion Ocupada en cols 3, 4
            mujeres_col = 3
            varones_col = 4

        rows = []
        for row in data[data_start:]:
            if not row or row[0] is None:
                continue
            periodo = _normalize_genero_period(row[0])
            if not periodo:
                continue

            fem = _safe_float(row[mujeres_col]) if mujeres_col < len(row) else None
            masc = _safe_float(row[varones_col]) if varones_col < len(row) else None

            if fem is not None:
                rows.append({'Período': periodo, 'Sexo': 'Mujeres', 'Empleo': fem})
            if masc is not None:
                rows.append({'Período': periodo, 'Sexo': 'Varones', 'Empleo': masc})

        return pd.DataFrame(rows)

    def _process_remuneraciones_genero(self, ws):
        """
        C 3.1 or C 4.1: Remuneraciones por sexo.
        Intenta extraer columnas Mujeres, Varones, y calcular brecha.
        """
        data = list(ws.iter_rows(values_only=True))
        if len(data) < 6:
            return pd.DataFrame()

        mujeres_col = None
        varones_col = None

        for idx in range(min(6, len(data))):
            row = data[idx]
            if not row:
                continue
            for col_idx, val in enumerate(row):
                if val and isinstance(val, str):
                    v = val.strip().lower()
                    if 'mujeres' in v or 'femenino' in v:
                        mujeres_col = col_idx
                    elif 'varones' in v or 'masculino' in v:
                        varones_col = col_idx

        if mujeres_col is None or varones_col is None:
            return pd.DataFrame()

        rows = []
        data_start = 5
        for row in data[data_start:]:
            if not row or row[0] is None:
                continue
            periodo = _normalize_genero_period(row[0])
            if not periodo:
                continue

            fem = _safe_float(row[mujeres_col]) if mujeres_col < len(row) else None
            masc = _safe_float(row[varones_col]) if varones_col < len(row) else None

            brecha = None
            if fem is not None and masc is not None and masc != 0:
                brecha = round((1 - fem / masc) * 100, 2)

            if fem is not None:
                rows.append({'Período': periodo, 'Sexo': 'Mujeres', 'Remuneracion': fem, 'Brecha': brecha})
            if masc is not None:
                rows.append({'Período': periodo, 'Sexo': 'Varones', 'Remuneracion': masc, 'Brecha': brecha})

        return pd.DataFrame(rows)

    def _process_empleo_sector_genero(self, ws):
        """
        C 2.1/C 2.2: Empleo registrado por sexo y sector.
        """
        data = list(ws.iter_rows(values_only=True))
        if len(data) < 6:
            return pd.DataFrame()

        # Look for structure: this could be sector breakdown with gender columns
        # or period-based with sector rows
        # Try to detect the structure from headers
        mujeres_col = None
        varones_col = None

        for idx in range(min(6, len(data))):
            row = data[idx]
            if not row:
                continue
            for col_idx, val in enumerate(row):
                if val and isinstance(val, str):
                    v = val.strip().lower()
                    if 'mujeres' in v or 'femenino' in v:
                        mujeres_col = col_idx
                    elif 'varones' in v or 'masculino' in v:
                        varones_col = col_idx

        if mujeres_col is None or varones_col is None:
            return pd.DataFrame()

        rows = []
        data_start = 5
        for row in data[data_start:]:
            if not row or row[0] is None:
                continue

            # Could be period in col 0 with sector in col 1, or just period
            periodo = _normalize_genero_period(row[0])
            if periodo:
                # Simple case: periodo + mujeres + varones columns
                fem = _safe_float(row[mujeres_col]) if mujeres_col < len(row) else None
                masc = _safe_float(row[varones_col]) if varones_col < len(row) else None
                if fem is not None:
                    rows.append({'Período': periodo, 'Sexo': 'Mujeres', 'Sector': 'Total', 'Empleo': fem})
                if masc is not None:
                    rows.append({'Período': periodo, 'Sexo': 'Varones', 'Sector': 'Total', 'Empleo': masc})

        return pd.DataFrame(rows)

    def save_parquet(self, datasets=None, output_dir=None):
        if datasets is None:
            datasets = self.process()
        out = output_dir or self.optimized_dir
        os.makedirs(out, exist_ok=True)
        parquet_names = {'G1': 'g1.parquet', 'G2': 'g2.parquet', 'G3': 'g3.parquet'}
        for key, df in datasets.items():
            if df.empty:
                continue
            name = parquet_names.get(key, f'{key.lower()}.parquet')
            path = os.path.join(out, name)
            df.to_parquet(path, index=False)
            logger.info(f"  {key}: {len(df)} filas -> {path}")


if __name__ == '__main__':
    processor = GeneroProcessor()
    if not os.path.exists(processor.raw_path):
        logger.error(f"Archivo no encontrado: {processor.raw_path}")
        logger.info("Descargue con: python scripts/download_oede.py --source genero")
        sys.exit(1)
    processor.run()
