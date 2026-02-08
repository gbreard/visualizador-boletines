"""
Procesador para flujos de empleo (flujos_de_creacion_y_destruccion_de_empleo).

Estructura del Excel (9 hojas):
  T1: Flujos de creacion/destruccion de empleo (con estacionalidad)
  T2: Flujos sin estacionalidad
  T3: Flujos por sector CIIU letra (con estacionalidad)
  T4: Dinamica de empresas (con estacionalidad)
  T5: Dinamica de empresas (sin estacionalidad)
  T6: Dinamica de empresas por sector

Datasets generados:
  F1: Flujos totales (altas/bajas/cambio neto) - desde T1
  F2: Tasas de rotacion (entrada/salida/rotacion) - desde T1 derivado
  F3: Flujos por sector - desde T3

Periodos: '2 trim 1996' a '2 trim 2025' (trimestral)

Uso:
    python scripts/preprocess/flujos.py
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


def _normalize_flujos_period(period_str):
    """
    Normaliza periodos de flujos: '2° trim 1996' -> '2º Trim 1996'
    Soporta: '2° trim 1996', '2º trim 1996', '2 trim 1996', numerico 199602
    """
    if not period_str:
        return None
    s = str(period_str).strip()
    # Normalizar simbolos de grado
    s = s.replace('°', '').replace('º', '')

    # Formato texto: '2 trim 1996'
    m = re.match(r'^(\d)\s*trim\w*\.?\s+(\d{4})$', s, re.IGNORECASE)
    if m:
        return f"{m.group(1)}º Trim {m.group(2)}"

    # Formato numerico 199602 -> '2º Trim 1996'
    m = re.match(r'^(\d{4})(\d{2})$', s)
    if m:
        anio = m.group(1)
        mes = int(m.group(2))
        # Mapeo mes a trimestre: 02/03->1, 05/06->2, 08/09->3, 11/12->4
        trim_map = {1: '1', 2: '1', 3: '1', 4: '2', 5: '2', 6: '2',
                    7: '3', 8: '3', 9: '3', 10: '4', 11: '4', 12: '4'}
        t = trim_map.get(mes)
        if t:
            return f"{t}º Trim {anio}"

    return None


class FlujosEmpleoProcessor(ExcelProcessor):
    source_name = 'flujos_empleo'
    frequency = 'quarterly'
    raw_filename = 'flujos_empleo.xlsx'

    def process(self):
        sheets = self.read_sheets()
        if not sheets:
            return {}

        datasets = {}

        # F1: Flujos totales desde T1
        if 'T1' in sheets:
            df = self._process_t1(sheets['T1'])
            if not df.empty:
                datasets['F1'] = df
                logger.info(f"  F1: {len(df)} filas")

        # F2: Tasas de rotacion (derivado de F1)
        if 'F1' in datasets and not datasets['F1'].empty:
            df = self._derive_rates(datasets['F1'])
            if not df.empty:
                datasets['F2'] = df
                logger.info(f"  F2: {len(df)} filas")

        # F3: Flujos por sector desde T3
        if 'T3' in sheets:
            df = self._process_t3(sheets['T3'])
            if not df.empty:
                datasets['F3'] = df
                logger.info(f"  F3: {len(df)} filas")

        return datasets

    def _process_t1(self, ws):
        """
        T1: Flujos agregados con estacionalidad.
        Col 0 = Periodo ('2 trim 1996')
        Col structure (from header rows 3-4):
          Creacion bruta: Aperturas(1), Continuadoras(2), Total(3)
          Destruccion bruta: Continuadoras(4), Cierres(5), Total(6)
          Cambio Neto(7)
          Empleo total(8)
        """
        data = list(ws.iter_rows(values_only=True))

        # Find data start (after headers)
        data_start = 5
        for idx, row in enumerate(data):
            if row and row[0] and 'trim' in str(row[0]).lower():
                data_start = idx
                break

        rows = []
        for row in data[data_start:]:
            if not row or row[0] is None:
                continue
            periodo = _normalize_flujos_period(row[0])
            if not periodo:
                continue

            # Extraer valores segun posiciones conocidas
            creacion_total = _safe_float(row[3]) if len(row) > 3 else None
            destruccion_total = _safe_float(row[6]) if len(row) > 6 else None
            cambio_neto = _safe_float(row[7]) if len(row) > 7 else None
            empleo_total = _safe_float(row[8]) if len(row) > 8 else None

            # Si cambio_neto no esta disponible, calcularlo
            if cambio_neto is None and creacion_total is not None and destruccion_total is not None:
                cambio_neto = creacion_total - destruccion_total

            rows.append({
                'Período': periodo,
                'Altas': creacion_total,
                'Bajas': destruccion_total,
                'Creacion_Neta': cambio_neto,
                'Empleo_Total': empleo_total,
            })

        return pd.DataFrame(rows)

    def _derive_rates(self, f1_df):
        """Calcula tasas de rotacion a partir de F1."""
        if f1_df.empty:
            return pd.DataFrame()

        rows = []
        for _, row in f1_df.iterrows():
            empleo = row.get('Empleo_Total')
            altas = row.get('Altas')
            bajas = row.get('Bajas')

            if empleo and empleo > 0:
                tasa_entrada = (altas / empleo * 100) if altas else None
                tasa_salida = (bajas / empleo * 100) if bajas else None
                tasa_rotacion = ((altas + bajas) / empleo * 100) if (altas and bajas) else None
            else:
                tasa_entrada = tasa_salida = tasa_rotacion = None

            rows.append({
                'Período': row['Período'],
                'Tasa_Entrada': tasa_entrada,
                'Tasa_Salida': tasa_salida,
                'Tasa_Rotacion': tasa_rotacion,
            })

        return pd.DataFrame(rows)

    def _process_t3(self, ws):
        """
        T3: Flujos por sector CIIU letra.
        Col 0 = Letra, Col 1 = Periodo (numerico ej: 199602)
        Cols 2+: Creacion(Aperturas, Continuadoras, Total), Destruccion(...), Cambio Neto
        """
        data = list(ws.iter_rows(values_only=True))

        # Find data start
        data_start = 5
        for idx, row in enumerate(data):
            if row and row[0] and isinstance(row[0], str) and len(row[0].strip()) == 1:
                data_start = idx
                break

        rows = []
        for row in data[data_start:]:
            if not row or row[0] is None or row[1] is None:
                continue

            sector = str(row[0]).strip()
            if not sector or len(sector) != 1 or not sector.isalpha():
                continue

            periodo = _normalize_flujos_period(row[1])
            if not periodo:
                continue

            creacion_total = _safe_float(row[4]) if len(row) > 4 else None
            destruccion_total = _safe_float(row[7]) if len(row) > 7 else None
            cambio_neto = _safe_float(row[8]) if len(row) > 8 else None

            if cambio_neto is None and creacion_total is not None and destruccion_total is not None:
                cambio_neto = creacion_total - destruccion_total

            rows.append({
                'Período': periodo,
                'Sector': sector,
                'Altas': creacion_total,
                'Bajas': destruccion_total,
                'Creacion_Neta': cambio_neto,
            })

        return pd.DataFrame(rows)

    def save_parquet(self, datasets=None, output_dir=None):
        if datasets is None:
            datasets = self.process()
        out = output_dir or self.optimized_dir
        os.makedirs(out, exist_ok=True)
        parquet_names = {'F1': 'f1.parquet', 'F2': 'f2.parquet', 'F3': 'f3.parquet'}
        for key, df in datasets.items():
            if df.empty:
                continue
            name = parquet_names.get(key, f'{key.lower()}.parquet')
            path = os.path.join(out, name)
            df.to_parquet(path, index=False)
            logger.info(f"  {key}: {len(df)} filas -> {path}")


if __name__ == '__main__':
    processor = FlujosEmpleoProcessor()
    if not os.path.exists(processor.raw_path):
        logger.error(f"Archivo no encontrado: {processor.raw_path}")
        logger.info("Descargue con: python scripts/download_oede.py --source flujos_empleo")
        sys.exit(1)
    processor.run()
