"""
Layout principal del dashboard: 6 tabs + header institucional + footer.
"""

from dash import html, dcc
from src.data.cache import cache


def create_main_layout():
    """Construye el layout principal de la aplicacion."""
    periods = cache.periods
    period_options = [{'label': p, 'value': p} for p in periods]

    # Valores por defecto: ultimos 5 anos
    value_hasta = periods[-1] if periods else None
    value_desde = periods[-20] if len(periods) > 20 else periods[0] if periods else None

    last_period = cache.last_period

    return html.Div([
        # Header institucional
        html.Div([
            html.H1("Panel de Monitoreo de Empleo Registrado"),
            html.P("SIPA | Republica Argentina", className="sipa-subtitle")
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

        # Tabs: 6 tabs
        dcc.Tabs(id='tabs-main', value='tab-resumen', children=[
            dcc.Tab(label='Resumen', value='tab-resumen'),
            dcc.Tab(label='Analisis', value='tab-analisis'),
            dcc.Tab(label='Comparaciones', value='tab-comparaciones'),
            dcc.Tab(label='Alertas', value='tab-alertas'),
            dcc.Tab(label='Datos', value='tab-datos'),
            dcc.Tab(label='Metodologia', value='tab-metodologia'),
        ], className="custom-tabs"),

        # Contenido con loading state
        dcc.Loading(
            id="loading-tab-content",
            type="default",
            children=html.Div(id='tab-content', className="container-fluid",
                               style={'padding': '1.5rem'})
        ),

        # Footer institucional
        html.Div([
            html.Span(f"Datos hasta: {last_period}"),
            html.Span(" | ", style={'margin': '0 0.5rem'}),
            html.Span("Fuente: SIPA / MTEySS"),
            html.Span(" | ", style={'margin': '0 0.5rem'}),
            html.Span("Republica Argentina"),
        ], className="sipa-footer")
    ], style={'backgroundColor': '#F7FAFC', 'minHeight': '100vh'})
