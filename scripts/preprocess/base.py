"""
Clase base para procesadores de archivos Excel OEDE.

Cada fuente OEDE tiene un procesador que hereda de ExcelProcessor
y define como leer y transformar las hojas del Excel.
"""

import os
import logging
import pandas as pd
import openpyxl
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW_DIR = os.path.join(BASE_DIR, 'data', 'raw')
PROCESSED_DIR = os.path.join(BASE_DIR, 'data', 'processed')
OPTIMIZED_DIR = os.path.join(BASE_DIR, 'data', 'optimized')


class ExcelProcessor(ABC):
    """Clase base para procesar archivos Excel OEDE."""

    source_name: str = ''       # ej: 'empleo_trimestral'
    frequency: str = ''         # 'monthly', 'quarterly', 'annual'
    raw_filename: str = ''      # nombre del .xlsx en data/raw/

    def __init__(self, raw_dir=None, processed_dir=None, optimized_dir=None):
        self.raw_dir = raw_dir or RAW_DIR
        self.processed_dir = processed_dir or PROCESSED_DIR
        self.optimized_dir = optimized_dir or OPTIMIZED_DIR

    @property
    def raw_path(self):
        return os.path.join(self.raw_dir, self.raw_filename)

    def read_sheets(self):
        """Lee todas las hojas del Excel y retorna dict {nombre_hoja: worksheet}."""
        if not os.path.exists(self.raw_path):
            logger.error(f"Archivo no encontrado: {self.raw_path}")
            return {}
        wb = openpyxl.load_workbook(self.raw_path, data_only=True)
        sheets = {name: wb[name] for name in wb.sheetnames}
        self._workbook = wb
        return sheets

    def close(self):
        """Cierra el workbook si esta abierto."""
        if hasattr(self, '_workbook'):
            self._workbook.close()

    @abstractmethod
    def process(self):
        """
        Procesa el Excel y retorna dict {dataset_key: pd.DataFrame}.
        Cada implementacion define que hojas leer y como transformarlas.
        """
        ...

    def save_csv(self, datasets=None, output_dir=None):
        """Guarda datasets como CSV en el directorio de salida."""
        if datasets is None:
            datasets = self.process()
        out = output_dir or self.processed_dir
        os.makedirs(out, exist_ok=True)

        for key, df in datasets.items():
            if df.empty:
                logger.warning(f"  {key}: DataFrame vacio, no se guarda")
                continue
            path = os.path.join(out, f'{key}.csv')
            df.to_csv(path, index=False, encoding='utf-8-sig')
            logger.info(f"  {key}: {len(df)} filas -> {path}")

    def save_parquet(self, datasets=None, output_dir=None):
        """Guarda datasets como Parquet en el directorio optimizado."""
        if datasets is None:
            datasets = self.process()
        out = output_dir or self.optimized_dir
        os.makedirs(out, exist_ok=True)

        for key, df in datasets.items():
            if df.empty:
                continue
            # Convertir nombre a formato parquet: R1 -> r1.parquet
            parquet_name = key.lower().replace('.', '').replace('_', '_') + '.parquet'
            path = os.path.join(out, parquet_name)
            df.to_parquet(path, index=False)
            logger.info(f"  {key}: {len(df)} filas -> {path}")

    def run(self, save_csv=True, save_parquet=True):
        """Ejecuta el pipeline completo: procesar + guardar."""
        logger.info(f"Procesando {self.source_name} ({self.raw_filename})...")
        try:
            datasets = self.process()
            if not datasets:
                logger.error(f"No se obtuvieron datasets de {self.source_name}")
                return {}
            if save_csv:
                self.save_csv(datasets)
            if save_parquet:
                self.save_parquet(datasets)
            logger.info(f"{self.source_name}: {len(datasets)} datasets procesados")
            return datasets
        finally:
            self.close()
