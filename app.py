"""
Wrapper para compatibilidad con Render.com
Este archivo permite que Render encuentre la aplicación con el comando por defecto 'gunicorn app:app'
"""
from dashboard import server as app

# Exponer la aplicación para Gunicorn
__all__ = ['app']