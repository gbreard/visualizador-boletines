"""
Procesador para empleo trimestral (nacional_serie_empleo_trimestral).
Genera datasets C1.1, C1.2, C2.1, C2.2, C3, C4, C5, C6, C7 y descriptores_CIIU.

Refactoriza la logica de src/preprocesamiento.py en la clase ExcelProcessor.

Uso:
    python scripts/preprocess/empleo_trimestral.py
"""

import sys
import os
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from scripts.preprocess.base import ExcelProcessor

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class EmpleoTrimestralProcessor(ExcelProcessor):
    source_name = 'empleo_trimestral'
    frequency = 'quarterly'
    raw_filename = 'empleo_trimestral.xlsx'

    def process(self):
        """Procesa el Excel de empleo trimestral usando las funciones existentes."""
        # Importar funciones del preprocesamiento existente
        from src.preprocesamiento import (
            process_time_series, process_sectorial_table, process_c5,
            create_master_descriptors
        )

        sheets = self.read_sheets()
        if not sheets:
            return {}

        datasets = {}
        all_descriptors = []

        # Series temporales: C1.1, C1.2, C2.1, C2.2
        for sheet_name in ['C1.1', 'C1.2', 'C2.1', 'C2.2']:
            if sheet_name in sheets:
                df = process_time_series(sheets[sheet_name], sheet_name)
                if not df.empty:
                    datasets[sheet_name] = df

        # C5 (sector/tamano)
        if 'C5' in sheets:
            df = process_c5(sheets['C5'])
            if not df.empty:
                datasets['C5'] = df

        # Sectoriales: C3, C4, C6, C7
        nivel_map = {
            'C3': 'Letra', 'C4': '2 digitos',
            'C6': '3 digitos', 'C7': '4 digitos'
        }
        for sheet_name in ['C3', 'C4', 'C6', 'C7']:
            if sheet_name in sheets:
                df_datos, df_desc = process_sectorial_table(sheets[sheet_name], sheet_name)
                if not df_datos.empty:
                    datasets[sheet_name] = df_datos
                if not df_desc.empty:
                    df_desc['Nivel'] = nivel_map[sheet_name]
                    df_desc['Tabla'] = sheet_name
                    all_descriptors.append(df_desc)

        # Tabla maestra de descriptores
        if all_descriptors:
            import pandas as pd
            df_maestro = pd.concat(all_descriptors, ignore_index=True)
            df_maestro = df_maestro[['Código', 'Descripción', 'Nivel', 'Tabla']]
            datasets['descriptores_CIIU'] = df_maestro

        return datasets

    def save_parquet(self, datasets=None, output_dir=None):
        """Override para usar nombres de parquet compatibles con config.py."""
        if datasets is None:
            datasets = self.process()
        out = output_dir or self.optimized_dir
        os.makedirs(out, exist_ok=True)

        # Mapping compatible con PARQUET_MAPPING en config.py
        parquet_names = {
            'C1.1': 'c11.parquet', 'C1.2': 'c12.parquet',
            'C2.1': 'c2_1.parquet', 'C2.2': 'c2_2.parquet',
            'C3': 'c3.parquet', 'C4': 'c4.parquet',
            'C5': 'c5.parquet', 'C6': 'c6.parquet',
            'C7': 'c7.parquet', 'descriptores_CIIU': 'descriptores.parquet',
        }

        for key, df in datasets.items():
            if df.empty:
                continue
            name = parquet_names.get(key, f'{key.lower()}.parquet')
            path = os.path.join(out, name)
            df.to_parquet(path, index=False)
            logger.info(f"  {key}: {len(df)} filas -> {path}")


if __name__ == '__main__':
    processor = EmpleoTrimestralProcessor()

    # Verificar si existe el archivo
    if not os.path.exists(processor.raw_path):
        # Buscar alternativas en data/raw
        raw_dir = processor.raw_dir
        alternatives = [f for f in os.listdir(raw_dir) if 'empleo' in f.lower() and f.endswith('.xlsx')]
        if alternatives:
            logger.info(f"Archivo no encontrado: {processor.raw_filename}")
            logger.info(f"Alternativas encontradas: {alternatives}")
            logger.info("Use: python scripts/download_oede.py --source empleo_trimestral")
        else:
            logger.error(f"No se encontro archivo de empleo trimestral en {raw_dir}")
            logger.info("Descargue con: python scripts/download_oede.py --source empleo_trimestral")
        sys.exit(1)

    processor.run()
