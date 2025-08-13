"""
Wrapper para compatibilidad con servidores de producción
Este archivo permite que Gunicorn encuentre la aplicación
"""
# Usar dashboard_minimal sin pandas para debug
from dashboard_minimal import server as app

# Exponer la aplicación para Gunicorn
__all__ = ['app']