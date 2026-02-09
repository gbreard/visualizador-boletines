#!/usr/bin/env python
"""
Script de Sincronización: Desarrollo → Producción
=================================================
Este script automatiza el proceso de copiar cambios desde desarrollo
hacia la carpeta deploy/ para su posterior despliegue en GitHub.

Autor: Sistema de Deploy
Fecha: 13 de agosto de 2025
"""

import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
import hashlib
import json

# Colores para terminal
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")

def print_success(text):
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")

def print_warning(text):
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")

def print_error(text):
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")

def print_info(text):
    print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")

def calculate_file_hash(filepath):
    """Calcula el hash MD5 de un archivo."""
    hash_md5 = hashlib.md5()
    try:
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except:
        return None

def detect_changes():
    """Detecta qué archivos han cambiado desde la última sincronización."""
    changes = {
        'dashboard': False,
        'data_processed': False,
        'data_optimized': False,
        'preprocesamiento': False
    }
    
    # Archivo para guardar hashes de la última sincronización
    hash_file = '.sync_hashes.json'
    last_hashes = {}
    
    if os.path.exists(hash_file):
        with open(hash_file, 'r') as f:
            last_hashes = json.load(f)
    
    current_hashes = {}
    
    # Verificar dashboard.py
    dashboard_path = 'src/dashboard.py'
    if os.path.exists(dashboard_path):
        current_hash = calculate_file_hash(dashboard_path)
        current_hashes['dashboard'] = current_hash
        if last_hashes.get('dashboard') != current_hash:
            changes['dashboard'] = True
            print_info("Dashboard modificado")
    
    # Verificar datos procesados
    data_files = []
    if os.path.exists('data/processed'):
        for file in os.listdir('data/processed'):
            if file.endswith('.csv'):
                data_files.append(f'data/processed/{file}')
    
    if os.path.exists('data/optimized'):
        for file in os.listdir('data/optimized'):
            if file.endswith('.parquet'):
                data_files.append(f'data/optimized/{file}')
    
    for filepath in data_files:
        file_hash = calculate_file_hash(filepath)
        if file_hash:
            key = filepath.replace('/', '_')
            current_hashes[key] = file_hash
            if last_hashes.get(key) != file_hash:
                if 'processed' in filepath:
                    changes['data_processed'] = True
                else:
                    changes['data_optimized'] = True
    
    # Guardar hashes actuales para próxima comparación
    with open(hash_file, 'w') as f:
        json.dump(current_hashes, f, indent=2)
    
    return changes

def sync_dashboard():
    """Sincroniza el dashboard.py actualizado."""
    src_file = 'src/dashboard.py'
    dest_file = 'deploy/dashboard.py'
    
    if not os.path.exists(src_file):
        print_error(f"No se encuentra {src_file}")
        return False
    
    try:
        # Hacer backup del anterior
        if os.path.exists(dest_file):
            backup_file = f'deploy/dashboard_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.py'
            shutil.copy2(dest_file, backup_file)
            print_info(f"Backup creado: {backup_file}")
        
        # Leer el dashboard de desarrollo
        with open(src_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Ajustar rutas para producción
        content = content.replace("DATA_DIR = '../data/processed'", "DATA_DIR = 'datos_limpios'")
        content = content.replace("parquet_dir = '../data/optimized'", "parquet_dir = 'datos_rapidos'")
        
        # Escribir versión de producción
        with open(dest_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print_success(f"Dashboard sincronizado a {dest_file}")
        return True
        
    except Exception as e:
        print_error(f"Error sincronizando dashboard: {str(e)}")
        return False

def sync_data():
    """Sincroniza los datos procesados y optimizados."""
    success = True
    
    # Sincronizar CSV
    if os.path.exists('data/processed'):
        print_info("Sincronizando datos CSV...")
        dest_dir = 'deploy/datos_limpios'
        
        for file in os.listdir('data/processed'):
            if file.endswith('.csv'):
                src = f'data/processed/{file}'
                dest = f'{dest_dir}/{file}'
                try:
                    shutil.copy2(src, dest)
                    print_success(f"  {file}")
                except Exception as e:
                    print_error(f"  Error con {file}: {str(e)}")
                    success = False
    
    # Sincronizar Parquet
    if os.path.exists('data/optimized'):
        print_info("Sincronizando datos Parquet...")
        dest_dir = 'deploy/datos_rapidos'
        
        for file in os.listdir('data/optimized'):
            if file.endswith('.parquet'):
                src = f'data/optimized/{file}'
                dest = f'{dest_dir}/{file}'
                try:
                    shutil.copy2(src, dest)
                    print_success(f"  {file}")
                except Exception as e:
                    print_error(f"  Error con {file}: {str(e)}")
                    success = False
    
    return success

def git_status():
    """Verifica el estado de Git en deploy/."""
    try:
        os.chdir('deploy')
        result = subprocess.run(['git', 'status', '--short'], 
                              capture_output=True, text=True)
        os.chdir('..')
        
        if result.stdout:
            print_info("Archivos modificados en deploy/:")
            for line in result.stdout.strip().split('\n'):
                print(f"  {line}")
            return True
        else:
            print_info("No hay cambios en deploy/")
            return False
    except Exception as e:
        print_error(f"Error verificando Git: {str(e)}")
        return False

def git_commit_and_push(message=None):
    """Hace commit y push de los cambios a GitHub."""
    if not message:
        message = f"Actualización desde desarrollo - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    
    try:
        os.chdir('deploy')
        
        # Git add
        subprocess.run(['git', 'add', '-A'], check=True)
        
        # Git commit
        result = subprocess.run(['git', 'commit', '-m', message],
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print_success("Commit creado")
            
            # Git push
            result = subprocess.run(['git', 'push', 'origin', 'master'],
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print_success("Cambios subidos a GitHub")
                print_info("Render debería comenzar el deploy automáticamente")
                return True
            else:
                print_error(f"Error en push: {result.stderr}")
                return False
        else:
            print_warning("No hay cambios para commit")
            return True
            
    except Exception as e:
        print_error(f"Error con Git: {str(e)}")
        return False
    finally:
        os.chdir('..')

def main():
    """Función principal del script de sincronización."""
    print_header("SINCRONIZACIÓN A PRODUCCIÓN")
    
    # Detectar cambios
    print("\n1. Detectando cambios...")
    changes = detect_changes()
    
    if not any(changes.values()):
        print_success("No hay cambios para sincronizar")
        return
    
    # Mostrar cambios detectados
    print("\n2. Cambios detectados:")
    if changes['dashboard']:
        print_info("  • Dashboard modificado")
    if changes['data_processed']:
        print_info("  • Datos CSV actualizados")
    if changes['data_optimized']:
        print_info("  • Datos Parquet actualizados")
    
    # Preguntar confirmación
    print(f"\n{Colors.WARNING}¿Deseas sincronizar estos cambios a producción? (s/n): {Colors.ENDC}", end='')
    response = input().strip().lower()
    
    if response != 's':
        print_warning("Sincronización cancelada")
        return
    
    # Sincronizar
    print("\n3. Sincronizando archivos...")
    
    success = True
    if changes['dashboard']:
        success = sync_dashboard() and success
    
    if changes['data_processed'] or changes['data_optimized']:
        success = sync_data() and success
    
    if not success:
        print_error("Hubo errores durante la sincronización")
        return
    
    # Git
    print("\n4. Preparando para GitHub...")
    if git_status():
        print(f"\n{Colors.WARNING}¿Deseas subir los cambios a GitHub? (s/n): {Colors.ENDC}", end='')
        response = input().strip().lower()
        
        if response == 's':
            print_info("Mensaje de commit (Enter para usar mensaje por defecto): ")
            message = input().strip()
            
            if git_commit_and_push(message if message else None):
                print_header("✅ SINCRONIZACIÓN COMPLETADA")
                print_success("Los cambios están en GitHub")
                print_success("Render debería iniciar el deploy automáticamente")
                print_info("Verifica el estado en: https://dashboard.render.com")
            else:
                print_error("Error subiendo a GitHub")
    else:
        print_success("No hay cambios para Git")
    
    print("\n" + "="*60)

def quick_sync():
    """Sincronización rápida sin confirmaciones."""
    print_header("SINCRONIZACIÓN RÁPIDA")
    
    # Sincronizar todo
    print("Sincronizando archivos...")
    sync_dashboard()
    sync_data()
    
    # Git automático
    if git_status():
        git_commit_and_push()
    
    print_success("Sincronización rápida completada")

if __name__ == "__main__":
    # Verificar que estamos en el directorio correcto
    if not os.path.exists('src') or not os.path.exists('deploy'):
        print_error("Este script debe ejecutarse desde el directorio raíz del proyecto")
        print_info("Directorio actual: " + os.getcwd())
        sys.exit(1)
    
    # Verificar argumento para sincronización rápida
    if len(sys.argv) > 1 and sys.argv[1] == '--quick':
        quick_sync()
    else:
        main()