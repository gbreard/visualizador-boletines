"""
Wrapper para compatibilidad con servidores de producción
Este archivo permite que Gunicorn encuentre la aplicación
"""
# Usar dashboard_test super simple
from dashboard_test import server as app

# Exponer la aplicación para Gunicorn
__all__ = ['app']