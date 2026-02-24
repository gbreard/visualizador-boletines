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
from src.tabs.remuneraciones import create_remuneraciones_layout
from src.tabs.empresas import create_empresas_layout
from src.tabs.flujos import create_flujos_layout
from src.tabs.genero import create_genero_layout


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
        elif active_tab == 'tab-remuneraciones':
            return create_remuneraciones_layout()
        elif active_tab == 'tab-empresas':
            return create_empresas_layout()
        elif active_tab == 'tab-flujos':
            return create_flujos_layout()
        elif active_tab == 'tab-genero':
            return create_genero_layout()
        elif active_tab == 'tab-comparaciones':
            return create_comparaciones_layout()
        elif active_tab == 'tab-alertas':
            return create_alertas_layout()
        elif active_tab == 'tab-datos':
            return create_datos_layout()
        elif active_tab == 'tab-metodologia':
            return create_metodologia_layout()
        elif active_tab == 'tab-admin':
            from src.auth.manager import auth_enabled
            if auth_enabled():
                from flask_login import current_user
                if current_user.is_authenticated and current_user.is_admin:
                    from src.tabs.admin import create_admin_layout
                    return create_admin_layout()
            else:
                # Dev mode: acceso libre
                from src.tabs.admin import create_admin_layout
                return create_admin_layout()
            return html.Div("Acceso no autorizado", className="text-center p-5")
        return html.Div("Vista no disponible", className="text-center p-5")
