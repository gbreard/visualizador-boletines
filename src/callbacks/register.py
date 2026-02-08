"""
Registro centralizado de todos los callbacks.
"""

from src.callbacks.global_controls import register_global_callbacks
from src.tabs.resumen import register_resumen_callbacks
from src.tabs.analisis import register_analisis_callbacks, register_sectorial_callbacks, register_tamaño_callbacks
from src.tabs.comparaciones import register_comparaciones_callbacks
from src.tabs.alertas import register_alertas_callbacks
from src.tabs.datos import register_datos_callbacks


def register_all_callbacks(app):
    """Registra todos los callbacks de la aplicacion."""
    register_global_callbacks(app)
    register_resumen_callbacks(app)
    register_analisis_callbacks(app)
    register_sectorial_callbacks(app)
    register_tamaño_callbacks(app)
    register_comparaciones_callbacks(app)
    register_alertas_callbacks(app)
    register_datos_callbacks(app)
