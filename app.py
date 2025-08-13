"""
Wrapper para compatibilidad con servidores de producción
Este archivo permite que Gunicorn encuentre la aplicación
"""
# Temporalmente usar dashboard_simple para debug
from dashboard_simple import server as app

# Exponer la aplicación para Gunicorn
__all__ = ['app']