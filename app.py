"""
Wrapper para compatibilidad con Render.com
Este archivo permite que Render encuentre la aplicación con el comando por defecto 'gunicorn app:app'
"""
# Usar el dashboard SUPER RÁPIDO con todos los datos Parquet
from dashboard_super_rapido import server as app

# Exponer la aplicación para Gunicorn
__all__ = ['app']