"""
Wrapper para compatibilidad con servidores de producción
Este archivo permite que Gunicorn encuentre la aplicación
"""
# Usar dashboard_simple con pandas 1.5.3
from dashboard_simple import server as app

# Exponer la aplicación para Gunicorn
__all__ = ['app']