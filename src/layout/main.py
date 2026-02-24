"""
Layout principal del dashboard: tabs + header institucional + footer.
"""

from dash import html, dcc
from src.data.cache import cache
from src.layout.feedback_components import create_feedback_modal, set_feedback_enabled


def create_main_layout(role='admin', user_name=''):
    """Construye el layout principal de la aplicacion."""
    periods = cache.periods
    period_options = [{'label': p, 'value': p} for p in periods]

    # Valores por defecto: ultimos 5 anos
    value_hasta = periods[-1] if periods else None
    value_desde = periods[-20] if len(periods) > 20 else periods[0] if periods else None

    last_period = cache.last_period

    is_admin = role == 'admin'

    # Habilitar/deshabilitar feedback buttons segun rol
    set_feedback_enabled(is_admin)

    # Tabs base
    tabs = [
        dcc.Tab(label='Resumen', value='tab-resumen'),
        dcc.Tab(label='Analisis', value='tab-analisis'),
        dcc.Tab(label='Remuneraciones', value='tab-remuneraciones'),
        dcc.Tab(label='Empresas', value='tab-empresas'),
        dcc.Tab(label='Flujos', value='tab-flujos'),
        dcc.Tab(label='Genero', value='tab-genero'),
        dcc.Tab(label='Comparaciones', value='tab-comparaciones'),
        dcc.Tab(label='Alertas', value='tab-alertas'),
        dcc.Tab(label='Datos', value='tab-datos'),
        dcc.Tab(label='Metodologia', value='tab-metodologia'),
    ]

    # Tab admin solo para admins
    if is_admin:
        tabs.append(dcc.Tab(label='Admin', value='tab-admin'))

    # User info en header (solo si hay usuario)
    user_info = []
    if user_name:
        user_info = [
            html.Div([
                html.Span(user_name, className="sipa-user-name"),
                html.Span(f" ({role})", style={'fontSize': '0.75rem', 'opacity': '0.7'}),
                html.A("Salir", href="/logout", className="sipa-logout-link"),
            ], className="sipa-user-info")
        ]

    # Componentes que solo van para admin
    admin_components = []
    if is_admin:
        admin_components.append(create_feedback_modal())

    return html.Div([
        # Header institucional
        html.Div([
            html.Div([
                html.Div([
                    html.H1("Panel de Monitoreo de Empleo Registrado"),
                    html.P("SIPA | Republica Argentina", className="sipa-subtitle")
                ]),
                html.Div(user_info)
            ], className="sipa-header-inner")
        ], className="sipa-header"),

        # Controles globales
        html.Div([
            html.Div([
                html.Div([
                    html.Label("Rango de fechas:"),
                    html.Div([
                        dcc.Dropdown(
                            id='dd-fecha-desde',
                            options=period_options,
                            value=value_desde,
                            placeholder="Desde...",
                            style={'width': '180px'}
                        ),
                        html.Span(" - ", className="mx-2"),
                        dcc.Dropdown(
                            id='dd-fecha-hasta',
                            options=period_options,
                            value=value_hasta,
                            placeholder="Hasta...",
                            style={'width': '180px'}
                        )
                    ], className="d-flex align-items-center")
                ], className="col-md-8"),
                html.Div([
                    html.Small(f"Datos hasta: {last_period}",
                               style={'color': '#718096'})
                ], className="col-md-4 d-flex align-items-center justify-content-end")
            ], className="row")
        ], className="sipa-controls"),

        # Tabs
        dcc.Tabs(id='tabs-main', value='tab-resumen', children=tabs, className="custom-tabs"),

        # Contenido con loading state
        dcc.Loading(
            id="loading-tab-content",
            type="default",
            children=html.Div(id='tab-content', className="container-fluid",
                               style={'padding': '1.5rem'})
        ),

        # Store de contexto activo para feedback
        dcc.Store(id="active-context", data={}),

        # Store de info de usuario
        dcc.Store(id="user-info", data={"role": role, "name": user_name}),

        # Modal de feedback (solo admin)
        *admin_components,

        # Footer institucional
        html.Div([
            html.Span(f"Datos hasta: {last_period}"),
            html.Span(" | ", style={'margin': '0 0.5rem'}),
            html.Span("Fuente: SIPA | Ministerio de Capital Humano"),
            html.Span(" | ", style={'margin': '0 0.5rem'}),
            html.Span("Republica Argentina"),
        ], className="sipa-footer")
    ], style={'backgroundColor': '#F7FAFC', 'minHeight': '100vh'})
