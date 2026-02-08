"""
Tab Flujos de Empleo: KPIs + altas vs bajas + creacion neta + rotacion + sector.
Fuente: nacional_serie_flujos_empleo.xlsx (datasets F1-F3).
"""

from dash import html, dcc, Input, Output
import plotly.graph_objects as go
import pandas as pd

from src.config import COLORS, PLOTLY_TEMPLATE, PLOTLY_COLOR_SEQUENCE, SECTOR_CIIU_LETRA
from src.data.cache import cache
from src.data.processing import filter_by_dates
from src.layout.components import create_kpi_card, create_section_card, empty_state


def _sector_label(code):
    return SECTOR_CIIU_LETRA.get(code, code)


def create_flujos_layout():
    """Layout de la tab Flujos de Empleo."""
    f1 = cache.get_ref('F1')
    if f1.empty:
        return empty_state(
            "Datos de flujos de empleo no disponibles",
            "Ejecute: python scripts/download_oede.py --source flujos_empleo && "
            "python scripts/preprocess/flujos.py"
        )

    if 'Período' in f1.columns and 'Date' in f1.columns:
        sorted_df = f1.sort_values('Date')
        periods = sorted_df['Período'].unique().tolist()
    else:
        periods = []

    period_options = [{'label': p, 'value': p} for p in periods]
    value_hasta = periods[-1] if periods else None
    value_desde = periods[-20] if len(periods) > 20 else periods[0] if periods else None

    # Opciones de sector desde F3
    f3 = cache.get_ref('F3')
    sector_options = []
    if not f3.empty and 'Sector' in f3.columns:
        sectores = sorted(f3['Sector'].dropna().unique().tolist())
        sector_options = [{'label': f"{s} - {_sector_label(s)}", 'value': s} for s in sectores]

    return html.Div([
        # Filtros
        html.Div([
            html.Div([
                html.Div([
                    html.Label("Rango de periodos:", style={'fontWeight': '600', 'fontSize': '0.85rem'}),
                    html.Div([
                        dcc.Dropdown(
                            id='flu-fecha-desde',
                            options=period_options,
                            value=value_desde,
                            placeholder="Desde...",
                            style={'width': '180px'}
                        ),
                        html.Span(" - ", className="mx-2"),
                        dcc.Dropdown(
                            id='flu-fecha-hasta',
                            options=period_options,
                            value=value_hasta,
                            placeholder="Hasta...",
                            style={'width': '180px'}
                        ),
                    ], className="d-flex align-items-center"),
                ], className="col-md-5"),
                html.Div([
                    html.Label("Sector:", style={'fontWeight': '600', 'fontSize': '0.85rem'}),
                    dcc.Dropdown(
                        id='flu-sector-filter',
                        options=sector_options,
                        value=None,
                        placeholder="Todos los sectores",
                        multi=True,
                        style={'minWidth': '250px'}
                    ),
                ], className="col-md-5"),
                html.Div([
                    html.Small(f"Frecuencia: Trimestral | {len(periods)} periodos",
                               style={'color': COLORS['text_muted']})
                ], className="col-md-2 d-flex align-items-center justify-content-end"),
            ], className="row"),
        ], style={'padding': '0.75rem 0', 'marginBottom': '1rem',
                  'borderBottom': f"1px solid {COLORS['border']}"}),

        html.Div(id='flu-kpis', className="row mb-4"),

        html.Div([
            html.Div([
                create_section_card("Altas vs Bajas de Empleo", [
                    dcc.Graph(id='flu-altas-bajas')
                ])
            ], className="col-md-6"),
            html.Div([
                create_section_card("Creacion Neta de Empleo", [
                    dcc.Graph(id='flu-neta')
                ])
            ], className="col-md-6"),
        ], className="row mb-4"),

        html.Div([
            html.Div([
                create_section_card("Tasas de Rotacion", [
                    dcc.Graph(id='flu-rotacion')
                ])
            ], className="col-md-6"),
            html.Div([
                create_section_card("Creacion Neta por Sector (ultimo trimestre)", [
                    dcc.Graph(id='flu-sector')
                ])
            ], className="col-md-6"),
        ], className="row"),
    ])


def register_flujos_callbacks(app):
    @app.callback(
        [Output('flu-kpis', 'children'),
         Output('flu-altas-bajas', 'figure'),
         Output('flu-neta', 'figure'),
         Output('flu-rotacion', 'figure'),
         Output('flu-sector', 'figure')],
        [Input('flu-fecha-desde', 'value'),
         Input('flu-fecha-hasta', 'value'),
         Input('flu-sector-filter', 'value')]
    )
    def update_flujos(fecha_desde, fecha_hasta, sectores_sel):
        import traceback, sys
        try:
            return _update_flujos_inner(fecha_desde, fecha_hasta, sectores_sel)
        except Exception:
            traceback.print_exc(file=sys.stderr)
            empty_fig = go.Figure()
            empty_fig.update_layout(**PLOTLY_TEMPLATE['layout'])
            return [], empty_fig, empty_fig, empty_fig, empty_fig

    def _update_flujos_inner(fecha_desde, fecha_hasta, sectores_sel):
        f1 = cache.get_ref('F1')
        f2 = cache.get_ref('F2')
        f3 = cache.get_ref('F3')

        f1_f = filter_by_dates(f1, fecha_desde, fecha_hasta)
        f2_f = filter_by_dates(f2, fecha_desde, fecha_hasta)
        f3_f = filter_by_dates(f3, fecha_desde, fecha_hasta)

        # KPIs
        kpi_cards = []
        if not f1_f.empty and 'Altas' in f1_f.columns:
            latest = f1_f.nlargest(1, 'Date').iloc[0]
            periodo = latest.get('Período', '')

            neta = latest.get('Creacion_Neta', latest.get('Altas', 0) - latest.get('Bajas', 0))
            trend_neta = 'up' if neta > 0 else 'down' if neta < 0 else None

            kpi_cards = [
                html.Div([
                    create_kpi_card("Altas", latest.get('Altas', 0),
                                    subtitle=f"Puestos creados | {periodo}",
                                    id_prefix="flu-kpi-altas", color="success")
                ], className="col-md-3"),
                html.Div([
                    create_kpi_card("Bajas", latest.get('Bajas', 0),
                                    subtitle=f"Puestos perdidos | {periodo}",
                                    id_prefix="flu-kpi-bajas", color="danger")
                ], className="col-md-3"),
                html.Div([
                    create_kpi_card("Creacion Neta", neta,
                                    subtitle="Altas - Bajas",
                                    id_prefix="flu-kpi-neta", trend=trend_neta)
                ], className="col-md-3"),
                html.Div([
                    create_kpi_card("Periodos", len(f1_f),
                                    subtitle="trimestres con datos",
                                    id_prefix="flu-kpi-periodos", color="info")
                ], className="col-md-3"),
            ]

        # Altas vs Bajas (barras agrupadas)
        fig_ab = go.Figure()
        if not f1_f.empty and 'Date' in f1_f.columns:
            sorted_f1 = f1_f.sort_values('Date')
            if 'Altas' in sorted_f1.columns:
                fig_ab.add_trace(go.Bar(
                    x=sorted_f1['Date'], y=sorted_f1['Altas'],
                    name='Altas', marker_color=COLORS['success']
                ))
            if 'Bajas' in sorted_f1.columns:
                fig_ab.add_trace(go.Bar(
                    x=sorted_f1['Date'], y=sorted_f1['Bajas'],
                    name='Bajas', marker_color=COLORS['danger']
                ))
            fig_ab.update_layout(barmode='group', title='Altas vs Bajas', height=400)
        fig_ab.update_layout(**PLOTLY_TEMPLATE['layout'])

        # Creacion neta (barras coloreadas)
        fig_neta = go.Figure()
        if not f1_f.empty and 'Date' in f1_f.columns:
            sorted_f1 = f1_f.sort_values('Date')
            if 'Creacion_Neta' in sorted_f1.columns:
                neta_col = sorted_f1['Creacion_Neta']
            elif 'Altas' in sorted_f1.columns and 'Bajas' in sorted_f1.columns:
                neta_col = sorted_f1['Altas'] - sorted_f1['Bajas']
            else:
                neta_col = pd.Series(dtype=float)

            if not neta_col.empty:
                colors = [COLORS['success'] if v >= 0 else COLORS['danger'] for v in neta_col]
                fig_neta.add_trace(go.Bar(
                    x=sorted_f1['Date'], y=neta_col,
                    marker_color=colors, name='Creacion Neta'
                ))
            fig_neta.update_layout(title='Creacion neta de empleo', height=400, showlegend=False)
        fig_neta.update_layout(**PLOTLY_TEMPLATE['layout'])

        # Tasas de rotacion
        fig_rot = go.Figure()
        if not f2_f.empty and 'Date' in f2_f.columns:
            sorted_f2 = f2_f.sort_values('Date')
            for col, color, name in [
                ('Tasa_Entrada', COLORS['success'], 'Tasa Entrada'),
                ('Tasa_Salida', COLORS['danger'], 'Tasa Salida'),
                ('Tasa_Rotacion', COLORS['primary_light'], 'Tasa Rotacion'),
            ]:
                if col in sorted_f2.columns:
                    fig_rot.add_trace(go.Scatter(
                        x=sorted_f2['Date'], y=sorted_f2[col],
                        mode='lines', name=name, line=dict(color=color, width=2)
                    ))
            fig_rot.update_layout(title='Tasas de rotacion laboral', yaxis_title='%', height=400)
        fig_rot.update_layout(**PLOTLY_TEMPLATE['layout'])

        # Creacion neta por sector (barras horizontales - ultimo trimestre)
        fig_sector = go.Figure()
        if not f3_f.empty and 'Sector' in f3_f.columns and 'Date' in f3_f.columns:
            latest_date = f3_f['Date'].max()
            latest_f3 = f3_f[f3_f['Date'] == latest_date]
            if sectores_sel:
                latest_f3 = latest_f3[latest_f3['Sector'].isin(sectores_sel)]

            if 'Creacion_Neta' in latest_f3.columns:
                # Agrupar por sector (puede haber duplicados)
                sector_data = latest_f3.groupby('Sector')['Creacion_Neta'].sum().sort_values(ascending=True)
            elif 'Altas' in latest_f3.columns and 'Bajas' in latest_f3.columns:
                agg = latest_f3.groupby('Sector').agg({'Altas': 'sum', 'Bajas': 'sum'})
                sector_data = (agg['Altas'] - agg['Bajas']).sort_values(ascending=True)
            else:
                sector_data = pd.Series(dtype=float)

            if not sector_data.empty:
                labels = [_sector_label(s) for s in sector_data.index]
                colors = [COLORS['success'] if v >= 0 else COLORS['danger'] for v in sector_data.values]
                fig_sector = go.Figure(go.Bar(
                    x=sector_data.values, y=labels, orientation='h',
                    marker_color=colors,
                    text=[f"{v:+,.0f}" for v in sector_data.values],
                    textposition='outside',
                ))
                periodo_f3 = latest_f3['Período'].iloc[0] if 'Período' in latest_f3.columns and len(latest_f3) > 0 else ''
                fig_sector.update_layout(
                    title=f'Creacion neta por sector - {periodo_f3}',
                    height=400, showlegend=False
                )
        fig_sector.update_layout(**PLOTLY_TEMPLATE['layout'])

        return kpi_cards, fig_ab, fig_neta, fig_rot, fig_sector
