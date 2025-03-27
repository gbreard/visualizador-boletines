import os
import sys
import subprocess
import time
import webbrowser
from pathlib import Path

def verificar_requisitos():
    """
    Verifica que todas las bibliotecas necesarias estén instaladas.
    """
    requisitos = [
        "pandas",
        "numpy",
        "plotly",
        "dash",
        "openpyxl"  # Para leer archivos Excel
    ]
    
    faltantes = []
    
    for req in requisitos:
        try:
            __import__(req)
        except ImportError:
            faltantes.append(req)
    
    if faltantes:
        print(f"Se requieren instalar las siguientes bibliotecas: {', '.join(faltantes)}")
        respuesta = input("¿Desea instalarlas ahora? (s/n): ")
        
        if respuesta.lower() in ['s', 'si', 'sí', 'y', 'yes']:
            for req in faltantes:
                print(f"Instalando {req}...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", req])
            print("Bibliotecas instaladas correctamente.")
        else:
            print("No se pueden ejecutar los scripts sin las bibliotecas necesarias.")
            sys.exit(1)

def verificar_archivo_excel():
    """
    Verifica que el archivo Excel de entrada exista.
    """
    archivo_excel = "nacional_serie_empleo_trimestral_actualizado241312.xlsx"
    
    if not os.path.exists(archivo_excel):
        print(f"Error: No se encontró el archivo {archivo_excel} en el directorio actual.")
        print("Asegúrese de colocar el archivo Excel en el mismo directorio que este script.")
        sys.exit(1)
    
    return archivo_excel

def ejecutar_preprocesamiento():
    """
    Ejecuta el script de preprocesamiento.
    """
    from preprocesamiento_mejorado import main_preprocessing
    
    print("Iniciando preprocesamiento de datos...")
    rutas = main_preprocessing()
    
    print("\nPreprocesamiento completado. Verificando archivos generados...")
    
    # Verificar que se generaron los archivos necesarios
    archivos_requeridos = ["series_temporales", "datos_sectoriales"]
    for archivo in archivos_requeridos:
        if rutas[archivo] and os.path.exists(rutas[archivo]):
            print(f"✅ {os.path.basename(rutas[archivo])} generado correctamente")
        else:
            print(f"⚠️ {archivo} no se generó correctamente")
    
    return all(rutas[archivo] and os.path.exists(rutas[archivo]) for archivo in archivos_requeridos)

def ejecutar_dashboard():
    """
    Ejecuta el dashboard.
    """
    try:
        import dash
        
        print("\nIniciando Dashboard...")
        print("El dashboard estará disponible en http://127.0.0.1:8050/")
        print("Presione Ctrl+C para detener la ejecución")
        
        # Intentar abrir automáticamente el navegador
        webbrowser.open('http://127.0.0.1:8050/')
        
        # Importar y ejecutar el dashboard
        from dashboard_empleo import app
        app.run_server(debug=False)
        
    except Exception as e:
        print(f"Error al ejecutar el dashboard: {e}")
        return False
    
    return True

def main():
    """
    Función principal que ejecuta todo el proceso.
    """
    print("="*80)
    print("DASHBOARD DE EMPLEO REGISTRADO EN ARGENTINA".center(80))
    print("="*80)
    
    # Verificar requisitos
    verificar_requisitos()
    
    # Verificar archivo Excel
    archivo_excel = verificar_archivo_excel()
    print(f"✅ Archivo {archivo_excel} encontrado")
    
    # Ejecutar preprocesamiento
    preprocesamiento_ok = ejecutar_preprocesamiento()
    
    if preprocesamiento_ok:
        # Ejecutar dashboard
        ejecutar_dashboard()
    else:
        print("\n⚠️ No se pudo completar el preprocesamiento correctamente.")
        print("Por favor, revise los errores y vuelva a intentarlo.")
        sys.exit(1)

if __name__ == "__main__":
    main()