"""
Wrapper para compatibilidad con Render.com
Este archivo permite que Render encuentre la aplicación con el comando por defecto 'gunicorn app:app'
"""
# Usar el dashboard ORIGINAL con optimización Parquet (mantiene todo el diseño)
from dashboard_original_optimizado import server as app

# Exponer la aplicación para Gunicorn
__all__ = ['app']