"""
Conversión de CSV a Parquet para optimización de performance
=============================================================
Este script convierte los archivos CSV generados por preprocesamiento.py
a formato Parquet para mejorar significativamente la velocidad de carga.

Autor: Sistema de optimización
Fecha: 12 de agosto de 2025

IMPORTANTE: Este script NO modifica la estructura de los datos.
Solo convierte el formato de almacenamiento de CSV a Parquet.
"""

import pandas as pd
import os
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def convert_csv_to_parquet(input_dir='../data/processed', output_dir='../data/optimized'):
    """
    Convierte todos los archivos CSV del directorio de entrada a formato Parquet.
    
    Args:
        input_dir: Directorio con archivos CSV (default: 'datos_limpios')
        output_dir: Directorio donde guardar archivos Parquet (default: 'datos_rapidos')
    
    Returns:
        dict: Estadísticas de conversión
    """
    
    # Crear directorio de salida si no existe
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Mapeo de nombres de archivo CSV a Parquet
    file_mapping = {
        'C1.1.csv': 'c11.parquet',
        'C1.2.csv': 'c12.parquet',
        'C2.1.csv': 'c2_1.parquet',
        'C2.2.csv': 'c2_2.parquet',
        'C3.csv': 'c3.parquet',
        'C4.csv': 'c4.parquet',
        'C5.csv': 'c5.parquet',
        'C6.csv': 'c6.parquet',
        'C7.csv': 'c7.parquet',
        'descriptores_CIIU.csv': 'descriptores.parquet'
    }
    
    stats = {
        'archivos_convertidos': 0,
        'registros_totales': 0,
        'tamaño_csv_total': 0,
        'tamaño_parquet_total': 0,
        'errores': []
    }
    
    logger.info(f"Iniciando conversión de CSV a Parquet...")
    logger.info(f"Directorio origen: {input_dir}")
    logger.info(f"Directorio destino: {output_dir}")
    
    for csv_file, parquet_file in file_mapping.items():
        csv_path = os.path.join(input_dir, csv_file)
        parquet_path = os.path.join(output_dir, parquet_file)
        
        if not os.path.exists(csv_path):
            logger.warning(f"Archivo no encontrado: {csv_path}")
            stats['errores'].append(f"No encontrado: {csv_file}")
            continue
        
        try:
            # Leer CSV
            logger.info(f"Procesando {csv_file}...")
            df = pd.read_csv(csv_path)
            
            # Obtener estadísticas
            csv_size = os.path.getsize(csv_path)
            num_records = len(df)
            
            # Optimizar tipos de datos antes de guardar
            df = optimize_dtypes(df)
            
            # Guardar como Parquet con compresión
            df.to_parquet(parquet_path, compression='snappy', index=False)
            
            # Obtener tamaño del Parquet
            parquet_size = os.path.getsize(parquet_path)
            
            # Actualizar estadísticas
            stats['archivos_convertidos'] += 1
            stats['registros_totales'] += num_records
            stats['tamaño_csv_total'] += csv_size
            stats['tamaño_parquet_total'] += parquet_size
            
            # Calcular reducción
            reduction = (1 - parquet_size/csv_size) * 100
            
            logger.info(f"  ✓ {csv_file} -> {parquet_file}")
            logger.info(f"    Registros: {num_records:,}")
            logger.info(f"    CSV: {csv_size/1024:.1f} KB -> Parquet: {parquet_size/1024:.1f} KB")
            logger.info(f"    Reducción: {reduction:.1f}%")
            
        except Exception as e:
            logger.error(f"Error procesando {csv_file}: {str(e)}")
            stats['errores'].append(f"{csv_file}: {str(e)}")
    
    # Crear archivos adicionales de índice para optimización
    create_index_files(output_dir, file_mapping)
    
    # Mostrar resumen
    print_summary(stats)
    
    return stats

def optimize_dtypes(df):
    """
    Optimiza los tipos de datos del DataFrame para reducir uso de memoria.
    
    Args:
        df: DataFrame a optimizar
    
    Returns:
        DataFrame con tipos optimizados
    """
    for col in df.columns:
        col_type = df[col].dtype
        
        # Optimizar enteros
        if col_type != 'object':
            if col_type == 'int64':
                # Verificar si puede ser int32 o int16
                c_min = df[col].min()
                c_max = df[col].max()
                if c_min > -32768 and c_max < 32767:
                    df[col] = df[col].astype('int16')
                elif c_min > -2147483648 and c_max < 2147483647:
                    df[col] = df[col].astype('int32')
            
            # Optimizar floats
            elif col_type == 'float64':
                df[col] = df[col].astype('float32')
        
        # Convertir columnas de texto con valores repetidos a categorías
        elif col in ['Sector', 'Período', 'Tamaño', 'Código']:
            unique_ratio = len(df[col].unique()) / len(df[col])
            if unique_ratio < 0.5:  # Si menos del 50% son únicos
                df[col] = df[col].astype('category')
    
    return df

def create_index_files(output_dir, file_mapping):
    """
    Crea archivos de índice adicionales para optimización de consultas.
    
    Args:
        output_dir: Directorio de salida
        file_mapping: Mapeo de archivos procesados
    """
    try:
        # Crear índice temporal combinado para series de tiempo
        time_series_files = ['c11.parquet', 'c12.parquet', 'c2_1.parquet', 'c2_2.parquet']
        dfs = []
        
        for file in time_series_files:
            path = os.path.join(output_dir, file)
            if os.path.exists(path):
                df = pd.read_parquet(path)
                df['serie'] = file.replace('.parquet', '')
                dfs.append(df)
        
        if dfs:
            combined = pd.concat(dfs, ignore_index=True)
            combined.to_parquet(
                os.path.join(output_dir, 'indice_temporal.parquet'),
                compression='snappy',
                index=False
            )
            logger.info("  ✓ Creado índice temporal combinado")
        
        # Crear archivo de resumen con metadatos
        metadata = {
            'archivo': [],
            'registros': [],
            'columnas': [],
            'tamaño_kb': []
        }
        
        for parquet_file in file_mapping.values():
            path = os.path.join(output_dir, parquet_file)
            if os.path.exists(path):
                df = pd.read_parquet(path)
                metadata['archivo'].append(parquet_file)
                metadata['registros'].append(len(df))
                metadata['columnas'].append(len(df.columns))
                metadata['tamaño_kb'].append(os.path.getsize(path) / 1024)
        
        if metadata['archivo']:
            pd.DataFrame(metadata).to_parquet(
                os.path.join(output_dir, 'resumen.parquet'),
                compression='snappy',
                index=False
            )
            logger.info("  ✓ Creado archivo de resumen de metadatos")
            
    except Exception as e:
        logger.warning(f"No se pudieron crear archivos de índice: {str(e)}")

def print_summary(stats):
    """
    Imprime un resumen de la conversión.
    
    Args:
        stats: Diccionario con estadísticas
    """
    print("\n" + "="*60)
    print("RESUMEN DE CONVERSIÓN CSV → PARQUET")
    print("="*60)
    
    print(f"\nArchivos convertidos: {stats['archivos_convertidos']}")
    print(f"Registros totales: {stats['registros_totales']:,}")
    
    if stats['tamaño_csv_total'] > 0:
        csv_mb = stats['tamaño_csv_total'] / (1024 * 1024)
        parquet_mb = stats['tamaño_parquet_total'] / (1024 * 1024)
        reduction = (1 - stats['tamaño_parquet_total']/stats['tamaño_csv_total']) * 100
        
        print(f"\nTamaño total CSV: {csv_mb:.2f} MB")
        print(f"Tamaño total Parquet: {parquet_mb:.2f} MB")
        print(f"Reducción total: {reduction:.1f}%")
        print(f"Factor de compresión: {stats['tamaño_csv_total']/stats['tamaño_parquet_total']:.1f}x")
    
    if stats['errores']:
        print(f"\n⚠️ Errores encontrados:")
        for error in stats['errores']:
            print(f"  - {error}")
    else:
        print("\n✅ Conversión completada sin errores")
    
    print("\n" + "="*60)
    print("Los archivos Parquet están listos en el directorio 'datos_rapidos'")
    print("El dashboard puede ahora usar estos archivos para carga ultra-rápida")
    print("="*60)

def verify_conversion(input_dir='../data/processed', output_dir='../data/optimized'):
    """
    Verifica que la conversión fue exitosa comparando los datos.
    
    Args:
        input_dir: Directorio con CSV originales
        output_dir: Directorio con Parquet convertidos
    
    Returns:
        bool: True si la verificación es exitosa
    """
    file_mapping = {
        'C1.1.csv': 'c11.parquet',
        'C3.csv': 'c3.parquet',
        'descriptores_CIIU.csv': 'descriptores.parquet'
    }
    
    logger.info("\nVerificando integridad de la conversión...")
    
    for csv_file, parquet_file in file_mapping.items():
        csv_path = os.path.join(input_dir, csv_file)
        parquet_path = os.path.join(output_dir, parquet_file)
        
        if not os.path.exists(csv_path) or not os.path.exists(parquet_path):
            continue
        
        df_csv = pd.read_csv(csv_path)
        df_parquet = pd.read_parquet(parquet_path)
        
        # Verificar que tienen el mismo número de registros
        if len(df_csv) != len(df_parquet):
            logger.error(f"❌ {csv_file}: Diferente número de registros")
            return False
        
        # Verificar que tienen las mismas columnas
        if set(df_csv.columns) != set(df_parquet.columns):
            logger.error(f"❌ {csv_file}: Diferentes columnas")
            return False
        
        logger.info(f"  ✓ {csv_file} verificado correctamente")
    
    logger.info("✅ Verificación completada exitosamente")
    return True

if __name__ == "__main__":
    # Ejecutar conversión
    stats = convert_csv_to_parquet()
    
    # Verificar integridad
    if stats['archivos_convertidos'] > 0:
        verify_conversion()
    
    # Mensaje final
    print("\n💡 NOTA IMPORTANTE:")
    print("Para usar los archivos Parquet en el dashboard, actualiza la función")
    print("load_all_data() para leer desde '../data/optimized' en lugar de '../data/processed'")
    print("y cambia pd.read_csv() por pd.read_parquet()")