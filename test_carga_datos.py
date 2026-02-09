"""
Script de prueba para verificar la carga de datos
"""
import os
import sys
import pandas as pd

# Agregar src al path
sys.path.append('src')

# Cambiar al directorio src para simular ejecución normal
os.chdir('src')

print("="*60)
print("TEST DE CARGA DE DATOS")
print("="*60)

print(f"\nDirectorio actual: {os.getcwd()}")
print(f"Existe ../data/processed? {os.path.exists('../data/processed')}")
print(f"Existe ../data/optimized? {os.path.exists('../data/optimized')}")

# Intentar cargar como lo hace el dashboard
DATA_DIR = '../data/processed'
parquet_dir = '../data/optimized'

print(f"\nBuscando datos en:")
print(f"  CSV: {DATA_DIR}")
print(f"  Parquet: {parquet_dir}")

# Mapeo de nombres para archivos Parquet
parquet_mapping = {
    'C1.1': 'c11.parquet',
    'C1.2': 'c12.parquet',
    'C2.1': 'c2_1.parquet',
    'C2.2': 'c2_2.parquet',
    'C3': 'c3.parquet',
    'C4': 'c4.parquet',
    'C5': 'c5.parquet',
    'C6': 'c6.parquet',
    'C7': 'c7.parquet',
    'descriptores_CIIU': 'descriptores.parquet'
}

print("\n" + "-"*40)
print("INTENTANDO CARGAR ARCHIVOS:")
print("-"*40)

data = {}
errores = []

for key in ['C1.1', 'C1.2', 'C3', 'descriptores_CIIU']:  # Prueba con algunos archivos
    # Intentar cargar Parquet primero (más rápido)
    parquet_file = parquet_mapping.get(key)
    parquet_path = os.path.join(parquet_dir, parquet_file) if parquet_file else None
    csv_path = os.path.join(DATA_DIR, f'{key}.csv')
    
    print(f"\n{key}:")
    print(f"  Parquet: {parquet_path}")
    print(f"  CSV: {csv_path}")
    
    try:
        if parquet_path and os.path.exists(parquet_path):
            df = pd.read_parquet(parquet_path)
            data[key] = df
            print(f"  [OK] Cargado desde Parquet: {len(df)} registros")
        elif os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            data[key] = df
            print(f"  [OK] Cargado desde CSV: {len(df)} registros")
        else:
            print(f"  [ERROR] No se encontro archivo")
            errores.append(f"{key}: No encontrado")
    except Exception as e:
        print(f"  [ERROR] Error: {str(e)}")
        errores.append(f"{key}: {str(e)}")

print("\n" + "="*60)
print("RESUMEN:")
print("="*60)
print(f"Archivos cargados: {len(data)}/{len(parquet_mapping)}")
print(f"Total registros: {sum(len(df) for df in data.values())}")

if errores:
    print(f"\nErrores encontrados:")
    for error in errores:
        print(f"  - {error}")
else:
    print("\n[OK] Todos los archivos se cargaron correctamente")

# Verificar estructura de datos
if data:
    print("\n" + "-"*40)
    print("ESTRUCTURA DE DATOS CARGADOS:")
    print("-"*40)
    for key, df in data.items():
        print(f"\n{key}:")
        print(f"  Forma: {df.shape}")
        print(f"  Columnas: {list(df.columns)[:5]}...")
        if 'Período' in df.columns:
            print(f"  Períodos: {df['Período'].nunique()} únicos")
            print(f"  Rango: {df['Período'].min()} a {df['Período'].max()}")

print("\n" + "="*60)
print("FIN DEL TEST")
print("="*60)