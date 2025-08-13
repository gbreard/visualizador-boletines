"""
Wrapper para compatibilidad con servidores de producción
Este archivo permite que Gunicorn encuentre la aplicación
"""
# Usar dashboard_hybrid que funciona con o sin pandas
from dashboard_hybrid import server as app

# Exponer la aplicación para Gunicorn
__all__ = ['app']