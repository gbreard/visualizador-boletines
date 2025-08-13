"""
Wrapper para compatibilidad con servidores de producción
Este archivo permite que Gunicorn encuentre la aplicación
"""
# Usar dashboard_final sin pandas
from dashboard_final import server as app

# Exponer la aplicación para Gunicorn
__all__ = ['app']