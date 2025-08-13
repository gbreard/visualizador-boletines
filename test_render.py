"""
Script de verificación para Render
Ejecutar esto para verificar que los datos se cargan correctamente
"""
import os
import pandas as pd

print("="*60)
print("TEST DE CARGA DE DATOS EN RENDER")
print("="*60)

print(f"\nDirectorio actual: {os.getcwd()}")
print(f"\nArchivos en el directorio:")
for item in os.listdir('.'):
    print(f"  - {item}")

print("\n" + "-"*40)
print("VERIFICANDO DATOS:")
print("-"*40)

# Verificar CSV
csv_dir = 'datos_limpios'
if os.path.exists(csv_dir):
    csv_files = os.listdir(csv_dir)
    print(f"\nArchivos CSV en {csv_dir}: {len(csv_files)}")
    for f in csv_files[:5]:
        print(f"  - {f}")
else:
    print(f"\n[ERROR] No existe directorio {csv_dir}")

# Verificar Parquet
parquet_dir = 'datos_rapidos'
if os.path.exists(parquet_dir):
    parquet_files = os.listdir(parquet_dir)
    print(f"\nArchivos Parquet en {parquet_dir}: {len(parquet_files)}")
    for f in parquet_files[:5]:
        print(f"  - {f}")
else:
    print(f"\n[ERROR] No existe directorio {parquet_dir}")

# Intentar cargar un archivo
print("\n" + "-"*40)
print("INTENTANDO CARGAR DATOS:")
print("-"*40)

try:
    # Probar Parquet
    if os.path.exists('datos_rapidos/c11.parquet'):
        df = pd.read_parquet('datos_rapidos/c11.parquet')
        print(f"\n[OK] Parquet cargado: {len(df)} registros")
        print(f"Columnas: {list(df.columns)}")
        print(f"Primeras filas:")
        print(df.head())
    elif os.path.exists('datos_limpios/C1.1.csv'):
        df = pd.read_csv('datos_limpios/C1.1.csv')
        print(f"\n[OK] CSV cargado: {len(df)} registros")
        print(f"Columnas: {list(df.columns)}")
        print(f"Primeras filas:")
        print(df.head())
    else:
        print("\n[ERROR] No se encontraron archivos de datos")
except Exception as e:
    print(f"\n[ERROR] Error cargando datos: {str(e)}")

print("\n" + "="*60)
print("FIN DEL TEST")
print("="*60)