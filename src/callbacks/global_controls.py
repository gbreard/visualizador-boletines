"""
Callbacks de controles globales: tab switching.
"""

from dash import html, Input, Output

from src.tabs.resumen import create_resumen_layout
from src.tabs.analisis import create_analisis_layout
from src.tabs.comparaciones import create_comparaciones_layout
from src.tabs.alertas import create_alertas_layout
from src.tabs.datos import create_datos_layout
from src.tabs.metodologia import create_metodologia_layout


def register_global_callbacks(app):
    """Registra callbacks globales."""

    # Tab switching
    @app.callback(
        Output('tab-content', 'children'),
        Input('tabs-main', 'value')
    )
    def update_tab_content(active_tab):
        if active_tab == 'tab-resumen':
            return create_resumen_layout()
        elif active_tab == 'tab-analisis':
            return create_analisis_layout()
        elif active_tab == 'tab-comparaciones':
            return create_comparaciones_layout()
        elif active_tab == 'tab-alertas':
            return create_alertas_layout()
        elif active_tab == 'tab-datos':
            return create_datos_layout()
        elif active_tab == 'tab-metodologia':
            return create_metodologia_layout()
        return html.Div("Vista no disponible", className="text-center p-5")
