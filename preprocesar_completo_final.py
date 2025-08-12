"""
Preprocesador COMPLETO FINAL - Procesa TODAS las tablas C1 a C7
"""
import pandas as pd
import numpy as np
import time
import os
import warnings
warnings.filterwarnings('ignore')

def procesar_completo_final():
    """Procesa TODAS las hojas del Excel incluyendo C4, C5, C6, C7"""
    
    print("\n" + "="*70)
    print(" PREPROCESAMIENTO COMPLETO - TODAS LAS TABLAS (C1 a C7)")
    print("="*70)
    
    inicio_total = time.time()
    excel_file = 'nacional_serie_empleo_trimestral_actualizado241312.xlsx'
    
    if not os.path.exists(excel_file):
        print(f"ERROR: No se encuentra {excel_file}")
        return False
    
    os.makedirs('datos_rapidos', exist_ok=True)
    
    print(f"\nArchivo: {excel_file}")
    print(f"Tamaño: {os.path.getsize(excel_file) / (1024*1024):.2f} MB\n")
    
    stats = {'hojas': 0, 'registros': 0, 'archivos': []}
    
    try:
        # =========================================
        # 1. DESCRIPTORES (necesarios para todo)
        # =========================================
        print("1. DESCRIPTORES DE ACTIVIDAD")
        print("-" * 40)
        inicio = time.time()
        
        df_desc = pd.read_excel(excel_file, sheet_name='Descriptores de actividad', header=None)
        descriptores = {}
        
        for i in range(1, len(df_desc)):
            if pd.notna(df_desc.iloc[i, 0]):
                codigo = str(df_desc.iloc[i, 0]).strip()
                descripcion = str(df_desc.iloc[i, 1]) if pd.notna(df_desc.iloc[i, 1]) else ""
                descriptores[codigo] = descripcion
        
        df_descriptores = pd.DataFrame(list(descriptores.items()), 
                                      columns=['codigo', 'descripcion'])
        df_descriptores.to_parquet('datos_rapidos/descriptores.parquet', 
                                  engine='pyarrow', compression='snappy', index=False)
        
        print(f"  OK: {len(descriptores)} códigos ({time.time()-inicio:.2f}s)")
        stats['hojas'] += 1
        stats['archivos'].append('descriptores.parquet')
        
        # =========================================
        # 2-3. C1.1 y C1.2 (Ya funcionan bien)
        # =========================================
        for hoja in ['C1.1', 'C1.2']:
            print(f"\n{hoja} - EMPLEO TOTAL")
            print("-" * 40)
            inicio = time.time()
            
            df = pd.read_excel(excel_file, sheet_name=hoja, header=None)
            
            registros = []
            for i in range(4, len(df)):
                periodo = df.iloc[i, 0]
                if pd.notna(periodo) and 'Trim' in str(periodo):
                    try:
                        partes = str(periodo).replace('º', '').replace('°', '').split()
                        trimestre = int(partes[0][0])
                        año = int(partes[-1])
                        fecha = pd.Timestamp(year=año, month=(trimestre-1)*3 + 1, day=1)
                        
                        registro = {
                            'fecha': fecha,
                            'año': año,
                            'trimestre': trimestre,
                            'periodo_str': str(periodo),
                            'Total': float(df.iloc[i, 1]) if pd.notna(df.iloc[i, 1]) else None
                        }
                        
                        if registro['Total'] is not None:
                            registros.append(registro)
                    except:
                        pass
            
            df_proc = pd.DataFrame(registros)
            nombre_archivo = hoja.lower().replace('.', '') + '.parquet'
            df_proc.to_parquet(f'datos_rapidos/{nombre_archivo}', 
                             engine='pyarrow', compression='snappy', index=False)
            
            print(f"  OK: {len(registros)} registros ({time.time()-inicio:.2f}s)")
            stats['hojas'] += 1
            stats['registros'] += len(registros)
            stats['archivos'].append(nombre_archivo)
        
        # =========================================
        # 4. C3 - Por sector (ya funciona)
        # =========================================
        print("\nC3 - POR SECTOR CIIU")
        print("-" * 40)
        inicio = time.time()
        
        df_c3 = pd.read_excel(excel_file, sheet_name='C3', header=None)
        
        # Períodos en fila 2, desde columna 2
        periodos = []
        columnas_periodo = []
        for col in range(2, df_c3.shape[1]):
            val = df_c3.iloc[2, col]
            if pd.notna(val) and 'Trim' in str(val):
                periodos.append(str(val))
                columnas_periodo.append(col)
        
        # Sectores desde fila 3
        registros_c3 = []
        for row in range(3, len(df_c3)):
            codigo_sector = df_c3.iloc[row, 0]
            if pd.notna(codigo_sector):
                codigo_sector = str(codigo_sector).strip()
                descripcion_sector = str(df_c3.iloc[row, 1]) if pd.notna(df_c3.iloc[row, 1]) else ""
                
                for periodo_str, col_idx in zip(periodos, columnas_periodo):
                    valor = df_c3.iloc[row, col_idx]
                    if pd.notna(valor):
                        try:
                            partes = periodo_str.replace('º', '').replace('°', '').split()
                            trimestre = int(partes[0][0])
                            año = int(partes[-1])
                            fecha = pd.Timestamp(year=año, month=(trimestre-1)*3 + 1, day=1)
                            
                            registros_c3.append({
                                'fecha': fecha,
                                'año': año,
                                'trimestre': trimestre,
                                'sector': codigo_sector,
                                'descripcion': descripcion_sector[:50],
                                'valor': float(valor)
                            })
                        except:
                            pass
        
        df_c3_final = pd.DataFrame(registros_c3)
        df_c3_final.to_parquet('datos_rapidos/c3.parquet', 
                              engine='pyarrow', compression='snappy', index=False)
        
        print(f"  OK: {len(registros_c3)} registros ({time.time()-inicio:.2f}s)")
        stats['hojas'] += 1
        stats['registros'] += len(registros_c3)
        stats['archivos'].append('c3.parquet')
        
        # =========================================
        # 5. C4 - Por rama detallada
        # =========================================
        print("\nC4 - POR RAMA DETALLADA")
        print("-" * 40)
        inicio = time.time()
        
        df_c4 = pd.read_excel(excel_file, sheet_name='C4', header=None)
        
        # Períodos en fila 2, desde columna 2
        periodos = []
        columnas_periodo = []
        for col in range(2, df_c4.shape[1]):
            val = df_c4.iloc[2, col]
            if pd.notna(val) and 'Trim' in str(val):
                periodos.append(str(val))
                columnas_periodo.append(col)
        
        # Datos desde fila 3
        registros_c4 = []
        for row in range(3, len(df_c4)):
            codigo = df_c4.iloc[row, 0]
            descripcion = df_c4.iloc[row, 1]
            
            if pd.notna(descripcion):
                codigo_str = str(codigo) if pd.notna(codigo) else ""
                descripcion_str = str(descripcion)[:100]
                
                for periodo_str, col_idx in zip(periodos, columnas_periodo):
                    valor = df_c4.iloc[row, col_idx]
                    if pd.notna(valor):
                        try:
                            partes = periodo_str.replace('º', '').replace('°', '').split()
                            trimestre = int(partes[0][0])
                            año = int(partes[-1])
                            fecha = pd.Timestamp(year=año, month=(trimestre-1)*3 + 1, day=1)
                            
                            registros_c4.append({
                                'fecha': fecha,
                                'año': año,
                                'trimestre': trimestre,
                                'codigo': codigo_str,
                                'descripcion': descripcion_str,
                                'valor': float(valor)
                            })
                        except:
                            pass
        
        df_c4_final = pd.DataFrame(registros_c4)
        df_c4_final.to_parquet('datos_rapidos/c4.parquet', 
                              engine='pyarrow', compression='snappy', index=False)
        
        print(f"  OK: {len(registros_c4)} registros ({time.time()-inicio:.2f}s)")
        stats['hojas'] += 1
        stats['registros'] += len(registros_c4)
        stats['archivos'].append('c4.parquet')
        
        # =========================================
        # 6. C5 - Por tamaño de empresa
        # =========================================
        print("\nC5 - POR TAMAÑO DE EMPRESA")
        print("-" * 40)
        inicio = time.time()
        
        df_c5 = pd.read_excel(excel_file, sheet_name='C5', header=None)
        
        # Períodos en fila 2, desde columna 1
        periodos = []
        columnas_periodo = []
        for col in range(1, df_c5.shape[1]):
            val = df_c5.iloc[2, col]
            if pd.notna(val) and 'Trim' in str(val):
                periodos.append(str(val))
                columnas_periodo.append(col)
        
        # Datos desde fila 3
        registros_c5 = []
        sector_actual = ""
        
        for row in range(3, len(df_c5)):
            categoria = df_c5.iloc[row, 0]
            
            if pd.notna(categoria):
                categoria_str = str(categoria).strip()
                
                # Si es un sector principal (Industria, Comercio, etc)
                if categoria_str in ['Industria', 'Comercio', 'Resto']:
                    sector_actual = categoria_str
                
                # Para cada período
                for periodo_str, col_idx in zip(periodos, columnas_periodo):
                    valor = df_c5.iloc[row, col_idx]
                    if pd.notna(valor):
                        try:
                            partes = periodo_str.replace('º', '').replace('°', '').split()
                            trimestre = int(partes[0][0])
                            año = int(partes[-1])
                            fecha = pd.Timestamp(year=año, month=(trimestre-1)*3 + 1, day=1)
                            
                            registros_c5.append({
                                'fecha': fecha,
                                'año': año,
                                'trimestre': trimestre,
                                'sector': sector_actual,
                                'tamaño': categoria_str,
                                'valor': float(valor)
                            })
                        except:
                            pass
        
        df_c5_final = pd.DataFrame(registros_c5)
        df_c5_final.to_parquet('datos_rapidos/c5.parquet', 
                              engine='pyarrow', compression='snappy', index=False)
        
        print(f"  OK: {len(registros_c5)} registros ({time.time()-inicio:.2f}s)")
        stats['hojas'] += 1
        stats['registros'] += len(registros_c5)
        stats['archivos'].append('c5.parquet')
        
        # =========================================
        # 7. C6 - Detalle fino CIIU
        # =========================================
        print("\nC6 - DETALLE FINO CIIU")
        print("-" * 40)
        inicio = time.time()
        
        df_c6 = pd.read_excel(excel_file, sheet_name='C6', header=None)
        
        # Períodos en fila 2, desde columna 2
        periodos = []
        columnas_periodo = []
        for col in range(2, df_c6.shape[1]):
            val = df_c6.iloc[2, col]
            if pd.notna(val) and 'Trim' in str(val):
                periodos.append(str(val))
                columnas_periodo.append(col)
        
        # Datos desde fila 3
        registros_c6 = []
        for row in range(3, len(df_c6)):
            codigo = df_c6.iloc[row, 0]
            descripcion = df_c6.iloc[row, 1]
            
            if pd.notna(codigo):
                codigo_str = str(codigo).strip()
                descripcion_str = str(descripcion)[:100] if pd.notna(descripcion) else ""
                
                for periodo_str, col_idx in zip(periodos, columnas_periodo):
                    valor = df_c6.iloc[row, col_idx]
                    if pd.notna(valor):
                        try:
                            partes = periodo_str.replace('º', '').replace('°', '').split()
                            trimestre = int(partes[0][0])
                            año = int(partes[-1])
                            fecha = pd.Timestamp(year=año, month=(trimestre-1)*3 + 1, day=1)
                            
                            registros_c6.append({
                                'fecha': fecha,
                                'año': año,
                                'trimestre': trimestre,
                                'codigo_ciiu': codigo_str,
                                'descripcion': descripcion_str,
                                'valor': float(valor)
                            })
                        except:
                            pass
        
        df_c6_final = pd.DataFrame(registros_c6)
        df_c6_final.to_parquet('datos_rapidos/c6.parquet', 
                              engine='pyarrow', compression='snappy', index=False)
        
        print(f"  OK: {len(registros_c6)} registros ({time.time()-inicio:.2f}s)")
        stats['hojas'] += 1
        stats['registros'] += len(registros_c6)
        stats['archivos'].append('c6.parquet')
        
        # =========================================
        # 8. C7 - Máximo detalle
        # =========================================
        print("\nC7 - MÁXIMO DETALLE CIIU")
        print("-" * 40)
        inicio = time.time()
        
        df_c7 = pd.read_excel(excel_file, sheet_name='C7', header=None)
        
        # Períodos en fila 2, desde columna 2
        periodos = []
        columnas_periodo = []
        for col in range(2, df_c7.shape[1]):
            val = df_c7.iloc[2, col]
            if pd.notna(val) and 'Trim' in str(val):
                periodos.append(str(val))
                columnas_periodo.append(col)
        
        # Datos desde fila 3
        registros_c7 = []
        for row in range(3, len(df_c7)):
            codigo = df_c7.iloc[row, 0]
            descripcion = df_c7.iloc[row, 1]
            
            if pd.notna(codigo):
                codigo_str = str(codigo).strip()
                descripcion_str = str(descripcion)[:100] if pd.notna(descripcion) else ""
                
                for periodo_str, col_idx in zip(periodos, columnas_periodo):
                    valor = df_c7.iloc[row, col_idx]
                    if pd.notna(valor):
                        try:
                            partes = periodo_str.replace('º', '').replace('°', '').split()
                            trimestre = int(partes[0][0])
                            año = int(partes[-1])
                            fecha = pd.Timestamp(year=año, month=(trimestre-1)*3 + 1, day=1)
                            
                            registros_c7.append({
                                'fecha': fecha,
                                'año': año,
                                'trimestre': trimestre,
                                'codigo_ciiu_detalle': codigo_str,
                                'descripcion': descripcion_str,
                                'valor': float(valor)
                            })
                        except:
                            pass
        
        df_c7_final = pd.DataFrame(registros_c7)
        df_c7_final.to_parquet('datos_rapidos/c7.parquet', 
                              engine='pyarrow', compression='snappy', index=False)
        
        print(f"  OK: {len(registros_c7)} registros ({time.time()-inicio:.2f}s)")
        stats['hojas'] += 1
        stats['registros'] += len(registros_c7)
        stats['archivos'].append('c7.parquet')
        
        # =========================================
        # RESUMEN FINAL
        # =========================================
        tiempo_total = time.time() - inicio_total
        
        print("\n" + "="*70)
        print(" PROCESAMIENTO COMPLETADO")
        print("="*70)
        
        print(f"\nEstadísticas:")
        print(f"  - Hojas procesadas: {stats['hojas']}")
        print(f"  - Registros totales: {stats['registros']:,}")
        print(f"  - Archivos creados: {len(stats['archivos'])}")
        print(f"  - Tiempo total: {tiempo_total:.2f} segundos")
        
        print(f"\nArchivos en 'datos_rapidos/':")
        total_size = 0
        for archivo in os.listdir('datos_rapidos'):
            if archivo.endswith('.parquet'):
                size = os.path.getsize(f'datos_rapidos/{archivo}')
                total_size += size
                print(f"  - {archivo:30} {size/1024:8.1f} KB")
        
        print(f"\nTamaño total: {total_size/1024:.1f} KB")
        print(f"Tamaño Excel: {os.path.getsize(excel_file)/(1024*1024):.1f} MB")
        print(f"Reducción: {(1 - total_size/os.path.getsize(excel_file))*100:.1f}%")
        
        print("\nOK: Todas las tablas procesadas correctamente")
        
        return True
        
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    procesar_completo_final()