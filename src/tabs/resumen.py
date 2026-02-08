"""
Tab Resumen: KPIs + barras horizontales + sparkline evolucion.
"""

from dash import html, dcc, Input, Output
import plotly.express as px
import plotly.graph_objects as go

from src.config import COLORS, SECTOR_COLORS, PLOTLY_TEMPLATE
from src.data.cache import cache
from src.data.processing import get_latest_period_data, filter_by_dates, get_latest_period_str
from src.layout.components import create_kpi_card, create_section_card


def create_resumen_layout():
    """Layout de la tab Resumen."""
    return html.Div([
        # Subtitulo con periodo
        html.Div(id='resumen-subtitle', style={'color': '#718096', 'marginBottom': '1rem'}),

        # Fila de KPIs
        html.Div(id='resumen-kpis', className="row mb-4",
                 style={'gap': '0'}),

        # Fila de graficos
        html.Div([
            html.Div([
                create_section_card("Empleo por Sector", [
                    dcc.Graph(id='resumen-bars')
                ])
            ], className="col-md-6"),
            html.Div([
                create_section_card("Evolucion del Empleo Total", [
                    dcc.Graph(id='resumen-sparkline')
                ])
            ], className="col-md-6")
        ], className="row"),
    ])


def register_resumen_callbacks(app):
    @app.callback(
        [Output('resumen-subtitle', 'children'),
         Output('resumen-kpis', 'children'),
         Output('resumen-bars', 'figure'),
         Output('resumen-sparkline', 'figure')],
        [Input('dd-fecha-desde', 'value'),
         Input('dd-fecha-hasta', 'value')]
    )
    def update_resumen(fecha_desde, fecha_hasta):
        c1 = cache.get_ref('C1.1')
        c3 = cache.get_ref('C3')

        c1_filtered = filter_by_dates(c1, fecha_desde, fecha_hasta)

        # KPIs
        kpis = get_latest_period_data(c1_filtered)
        periodo_str = kpis['periodo']

        # Determinar tendencias
        trend_trim = None
        if isinstance(kpis['var_trim'], (int, float)):
            trend_trim = 'up' if kpis['var_trim'] > 0 else 'down' if kpis['var_trim'] < 0 else None
        trend_yoy = None
        if isinstance(kpis['var_yoy'], (int, float)):
            trend_yoy = 'up' if kpis['var_yoy'] > 0 else 'down' if kpis['var_yoy'] < 0 else None

        # Indice base 100 como 4to KPI
        idx_100 = kpis.get('index_100', 'N/D')

        kpi_cards = [
            html.Div([
                create_kpi_card("Empleo Total", kpis['empleo_actual'],
                                subtitle=f"Periodo: {periodo_str}",
                                id_prefix="kpi-total")
            ], className="col-md-3"),
            html.Div([
                create_kpi_card("Var. Trimestral", kpis['var_trim'],
                                subtitle="vs trimestre anterior",
                                id_prefix="kpi-trim", trend=trend_trim)
            ], className="col-md-3"),
            html.Div([
                create_kpi_card("Var. Interanual", kpis['var_yoy'],
                                subtitle="vs mismo trim. ano anterior",
                                id_prefix="kpi-yoy", trend=trend_yoy)
            ], className="col-md-3"),
            html.Div([
                create_kpi_card("Indice Base 100", idx_100,
                                subtitle="Base: 1T 1996 = 100",
                                id_prefix="kpi-idx", color="info")
            ], className="col-md-3"),
        ]

        subtitle = html.Span(f"Datos hasta: {periodo_str}") if periodo_str else ""

        # Barras horizontales
        fig_bars = go.Figure()
        c3_filtered = filter_by_dates(c3, fecha_desde, fecha_hasta)
        if not c3_filtered.empty and 'Sector' in c3_filtered.columns and 'Empleo' in c3_filtered.columns:
            ultimo_periodo = get_latest_period_str(c3_filtered) or c3_filtered['Período'].iloc[-1]
            latest_c3 = c3_filtered[c3_filtered['Período'] == ultimo_periodo].sort_values('Empleo', ascending=True)

            colors = [SECTOR_COLORS.get(s, COLORS['primary_light']) for s in latest_c3['Sector']]
            fig_bars = go.Figure(go.Bar(
                x=latest_c3['Empleo'],
                y=latest_c3['Sector'],
                orientation='h',
                marker_color=colors
            ))
            fig_bars.update_layout(
                title=f'Empleo por sector - {ultimo_periodo}',
                xaxis_title='Empleo (puestos)',
                height=400,
                showlegend=False
            )
        else:
            fig_bars.update_layout(height=400)
        fig_bars.update_layout(**PLOTLY_TEMPLATE['layout'])

        # Sparkline evolucion total
        fig_spark = go.Figure()
        if not c1_filtered.empty and 'Date' in c1_filtered.columns and 'Empleo' in c1_filtered.columns:
            fig_spark.add_trace(go.Scatter(
                x=c1_filtered['Date'],
                y=c1_filtered['Empleo'],
                mode='lines',
                fill='tozeroy',
                line=dict(color=COLORS['primary_light'], width=2),
                fillcolor='rgba(44, 82, 130, 0.12)'
            ))
            fig_spark.update_layout(
                title='Evolucion del empleo total',
                showlegend=False,
                height=400,
            )
        else:
            fig_spark.update_layout(height=400)
        fig_spark.update_layout(**PLOTLY_TEMPLATE['layout'])

        return subtitle, kpi_cards, fig_bars, fig_spark
