#!/usr/bin/env python3
"""
Script de diagnóstico completo para Render
Verifica todos los aspectos de la carga de datos
"""
import os
import sys
import pandas as pd
import traceback
from pathlib import Path

print("="*70)
print("DIAGNÓSTICO COMPLETO DE RENDER")
print("="*70)

# 1. Información del sistema
print("\n1. INFORMACIÓN DEL SISTEMA:")
print("-"*40)
print(f"Python version: {sys.version}")
print(f"Pandas version: {pd.__version__}")
print(f"Working directory: {os.getcwd()}")
print(f"Script location: {os.path.abspath(__file__)}")

# 2. Estructura de directorios
print("\n2. ESTRUCTURA DE DIRECTORIOS:")
print("-"*40)
for item in sorted(os.listdir('.')):
    path = Path(item)
    if path.is_dir():
        count = len(list(path.glob('*')))
        print(f"  [DIR] {item}/ ({count} archivos)")
    else:
        size = path.stat().st_size / 1024  # KB
        print(f"  [FILE] {item} ({size:.1f} KB)")

# 3. Verificar directorio datos_rapidos
print("\n3. CONTENIDO DE datos_rapidos:")
print("-"*40)
if os.path.exists('datos_rapidos'):
    files = sorted(os.listdir('datos_rapidos'))
    print(f"Total archivos: {len(files)}")
    for f in files:
        path = Path('datos_rapidos') / f
        size = path.stat().st_size / 1024  # KB
        print(f"  - {f} ({size:.1f} KB)")
else:
    print("[ERROR] No existe el directorio datos_rapidos")

# 4. Intentar cargar cada archivo Parquet
print("\n4. PRUEBA DE CARGA DE ARCHIVOS:")
print("-"*40)

parquet_files = {
    'c11.parquet': 'C1.1 - Empleo principal',
    'c12.parquet': 'C1.2 - Empleo secundario',
    'c2_1.parquet': 'C2.1 - Datos sector 1',
    'c2_2.parquet': 'C2.2 - Datos sector 2',
    'c3.parquet': 'C3 - Datos agregados',
    'c4.parquet': 'C4 - Por rama',
    'c5.parquet': 'C5 - Por región',
    'c6.parquet': 'C6 - Detallado',
    'c7.parquet': 'C7 - Serie completa',
    'descriptores.parquet': 'Descriptores CIIU'
}

successful_loads = 0
failed_loads = 0

for filename, description in parquet_files.items():
    filepath = f'datos_rapidos/{filename}'
    print(f"\n  Probando: {filename} ({description})")
    
    if not os.path.exists(filepath):
        print(f"    [X] Archivo no existe")
        failed_loads += 1
        continue
    
    try:
        # Intentar cargar el archivo
        df = pd.read_parquet(filepath)
        successful_loads += 1
        
        # Información básica
        print(f"    [OK] Cargado exitosamente")
        print(f"    - Registros: {len(df)}")
        print(f"    - Columnas: {list(df.columns)[:5]}")
        
        # Verificar columnas clave
        if 'Período' in df.columns or 'Per�odo' in df.columns:
            print(f"    - Columna Período: SI")
        else:
            print(f"    - Columna Período: NO (columnas: {df.columns.tolist()})")
            
    except Exception as e:
        failed_loads += 1
        print(f"    [ERROR] Error al cargar: {str(e)}")
        print(f"    Traceback:")
        print(traceback.format_exc())

# 5. Resumen
print("\n" + "="*70)
print("RESUMEN:")
print("-"*40)
print(f"✅ Archivos cargados exitosamente: {successful_loads}/{len(parquet_files)}")
print(f"❌ Archivos con error: {failed_loads}/{len(parquet_files)}")

# 6. Test de importación del dashboard
print("\n6. TEST DE IMPORTACIÓN DEL DASHBOARD:")
print("-"*40)
try:
    from dashboard import load_all_data
    print("✅ Dashboard importado correctamente")
    
    print("\nIntentando cargar todos los datos...")
    data = load_all_data()
    print(f"✅ Datos cargados: {len(data)} tablas")
    print(f"   Tablas: {list(data.keys())}")
    
    # Verificar contenido
    for key, df in data.items():
        if df is not None and not df.empty:
            print(f"   - {key}: {len(df)} registros")
        else:
            print(f"   - {key}: VACÍO o None")
            
except Exception as e:
    print(f"❌ Error: {str(e)}")
    print(traceback.format_exc())

# 7. Variables de entorno
print("\n7. VARIABLES DE ENTORNO RELEVANTES:")
print("-"*40)
env_vars = ['PORT', 'RENDER', 'RENDER_SERVICE_NAME', 'PYTHONPATH', 'PATH']
for var in env_vars:
    value = os.environ.get(var, 'No definida')
    if var == 'PATH':
        value = value[:100] + '...' if len(value) > 100 else value
    print(f"  {var}: {value}")

print("\n" + "="*70)
print("FIN DEL DIAGNÓSTICO")
print("="*70)