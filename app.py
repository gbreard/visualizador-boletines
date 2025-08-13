"""
Wrapper para compatibilidad con servidores de producción
Este archivo permite que Gunicorn encuentre la aplicación
"""
from dashboard import server as app

# Exponer la aplicación para Gunicorn
__all__ = ['app']