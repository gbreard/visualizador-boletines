"""
Tab Empresas: KPIs + evolucion temporal + distribucion por tamano + sector.
Fuente: nacional_serie_empresas_anual.xlsx (datasets E1-E3).
"""

from dash import html, dcc, Input, Output
import plotly.graph_objects as go
import pandas as pd

from src.config import COLORS, PLOTLY_TEMPLATE, PLOTLY_COLOR_SEQUENCE, SECTOR_CIIU_LETRA
from src.data.cache import cache
from src.data.processing import parse_period_string
from src.layout.components import create_kpi_card, create_section_card, empty_state


def _filter_anual(df, anio_desde, anio_hasta):
    """Filtra DataFrame anual por rango de anios."""
    if df.empty or 'Date' not in df.columns:
        return df
    result = df
    if hasattr(result['Date'], 'cat'):
        result = result.copy()
        result['Date'] = pd.to_datetime(result['Date'])
    if anio_desde:
        dt = parse_period_string(str(anio_desde))
        if dt:
            result = result[result['Date'] >= dt]
    if anio_hasta:
        dt = parse_period_string(str(anio_hasta))
        if dt:
            result = result[result['Date'] <= dt]
    return result


def _sector_label(code):
    return SECTOR_CIIU_LETRA.get(code, code)


def create_empresas_layout():
    """Layout de la tab Empresas."""
    e1 = cache.get_ref('E1')
    if e1.empty:
        return empty_state(
            "Datos de empresas no disponibles",
            "Ejecute: python scripts/download_oede.py --source empresas_anual && "
            "python scripts/preprocess/empresas.py"
        )

    if 'Período' in e1.columns and 'Date' in e1.columns:
        sorted_df = e1.sort_values('Date')
        periods = sorted_df['Período'].unique().tolist()
    else:
        periods = []

    period_options = [{'label': p, 'value': p} for p in periods]
    value_hasta = periods[-1] if periods else None
    value_desde = periods[0] if periods else None

    # Opciones de sector desde E2
    e2 = cache.get_ref('E2')
    sector_options = []
    if not e2.empty and 'Sector' in e2.columns:
        sectores = sorted(e2['Sector'].dropna().unique().tolist())
        sector_options = [{'label': f"{s} - {_sector_label(s)}", 'value': s} for s in sectores]

    return html.Div([
        # Filtros
        html.Div([
            html.Div([
                html.Div([
                    html.Label("Rango de anios:", style={'fontWeight': '600', 'fontSize': '0.85rem'}),
                    html.Div([
                        dcc.Dropdown(
                            id='emp-fecha-desde',
                            options=period_options,
                            value=value_desde,
                            placeholder="Desde...",
                            style={'width': '140px'}
                        ),
                        html.Span(" - ", className="mx-2"),
                        dcc.Dropdown(
                            id='emp-fecha-hasta',
                            options=period_options,
                            value=value_hasta,
                            placeholder="Hasta...",
                            style={'width': '140px'}
                        ),
                    ], className="d-flex align-items-center"),
                ], className="col-md-5"),
                html.Div([
                    html.Label("Sector:", style={'fontWeight': '600', 'fontSize': '0.85rem'}),
                    dcc.Dropdown(
                        id='emp-sector-filter',
                        options=sector_options,
                        value=None,
                        placeholder="Todos los sectores",
                        multi=True,
                        style={'minWidth': '250px'}
                    ),
                ], className="col-md-5"),
                html.Div([
                    html.Small(f"Frecuencia: Anual | {len(periods)} periodos",
                               style={'color': COLORS['text_muted']})
                ], className="col-md-2 d-flex align-items-center justify-content-end"),
            ], className="row"),
        ], style={'padding': '0.75rem 0', 'marginBottom': '1rem',
                  'borderBottom': f"1px solid {COLORS['border']}"}),

        html.Div(id='emp-kpis', className="row mb-4"),

        html.Div([
            html.Div([
                create_section_card("Evolucion del Total de Empresas", [
                    dcc.Graph(id='emp-evolution')
                ])
            ], className="col-md-6"),
            html.Div([
                create_section_card("Empresas por Sector (ultimo anio)", [
                    dcc.Graph(id='emp-sector')
                ])
            ], className="col-md-6"),
        ], className="row mb-4"),

        html.Div([
            create_section_card("Evolucion por Sector Seleccionado", [
                dcc.Graph(id='emp-sector-evo')
            ])
        ]),
    ])


def register_empresas_callbacks(app):
    @app.callback(
        [Output('emp-kpis', 'children'),
         Output('emp-evolution', 'figure'),
         Output('emp-sector', 'figure'),
         Output('emp-sector-evo', 'figure')],
        [Input('emp-fecha-desde', 'value'),
         Input('emp-fecha-hasta', 'value'),
         Input('emp-sector-filter', 'value')]
    )
    def update_empresas(fecha_desde, fecha_hasta, sectores_sel):
        import traceback, sys
        try:
            return _update_empresas_inner(fecha_desde, fecha_hasta, sectores_sel)
        except Exception:
            traceback.print_exc(file=sys.stderr)
            empty_fig = go.Figure()
            empty_fig.update_layout(**PLOTLY_TEMPLATE['layout'])
            return [], empty_fig, empty_fig, empty_fig

    def _update_empresas_inner(fecha_desde, fecha_hasta, sectores_sel):
        e1 = cache.get_ref('E1')
        e2 = cache.get_ref('E2')

        e1_f = _filter_anual(e1, fecha_desde, fecha_hasta)
        e2_f = _filter_anual(e2, fecha_desde, fecha_hasta)

        # KPIs
        kpi_cards = []
        if not e1_f.empty and 'Empresas' in e1_f.columns:
            latest = e1_f.nlargest(1, 'Date').iloc[0]
            total = latest['Empresas']
            periodo = latest.get('Período', '')

            sorted_e1 = e1_f.sort_values('Date')
            valid = sorted_e1['Empresas'].dropna()
            var_anual = 0
            if len(valid) >= 2:
                prev = valid.iloc[-2]
                var_anual = ((total - prev) / prev) * 100 if prev != 0 else 0

            trend = 'up' if var_anual > 0 else 'down' if var_anual < 0 else None

            # Cantidad de sectores seleccionados
            n_sectores = len(sectores_sel) if sectores_sel else (
                e2_f['Sector'].nunique() if not e2_f.empty and 'Sector' in e2_f.columns else 0
            )

            kpi_cards = [
                html.Div([
                    create_kpi_card("Total Empresas", total,
                                    subtitle=f"Periodo: {periodo}",
                                    id_prefix="emp-kpi-total")
                ], className="col-md-3"),
                html.Div([
                    create_kpi_card("Var. Anual", var_anual,
                                    subtitle="vs anio anterior",
                                    id_prefix="emp-kpi-var", trend=trend, is_pct=True)
                ], className="col-md-3"),
                html.Div([
                    create_kpi_card("Sectores", n_sectores,
                                    subtitle="sectores con datos",
                                    id_prefix="emp-kpi-sectores", color="info")
                ], className="col-md-3"),
                html.Div([
                    create_kpi_card("Periodos", len(e1_f),
                                    subtitle="anios con datos",
                                    id_prefix="emp-kpi-periodos", color="info")
                ], className="col-md-3"),
            ]

        # Evolucion total
        fig_evo = go.Figure()
        if not e1_f.empty and 'Date' in e1_f.columns:
            sorted_e1 = e1_f.sort_values('Date')
            fig_evo.add_trace(go.Bar(
                x=sorted_e1['Date'],
                y=sorted_e1['Empresas'],
                marker_color=COLORS['primary_light'],
            ))
            fig_evo.update_layout(title='Total de empresas registradas', height=400, showlegend=False)
        fig_evo.update_layout(**PLOTLY_TEMPLATE['layout'])

        # Sector (barras horizontales - ultimo anio)
        fig_sec = go.Figure()
        if not e2_f.empty and 'Sector' in e2_f.columns and 'Date' in e2_f.columns:
            latest_e2 = e2_f[e2_f['Date'] == e2_f['Date'].max()]
            if sectores_sel:
                latest_e2 = latest_e2[latest_e2['Sector'].isin(sectores_sel)]
            latest_e2 = latest_e2.sort_values('Empresas', ascending=True)
            labels = [_sector_label(s) for s in latest_e2['Sector']]
            fig_sec = go.Figure(go.Bar(
                x=latest_e2['Empresas'], y=labels, orientation='h',
                marker_color=PLOTLY_COLOR_SEQUENCE[:len(labels)],
                text=[f"{v:,.0f}" for v in latest_e2['Empresas']],
                textposition='outside',
            ))
            periodo_sec = latest_e2['Período'].iloc[0] if 'Período' in latest_e2.columns and len(latest_e2) > 0 else ''
            fig_sec.update_layout(title=f'Empresas por sector - {periodo_sec}',
                                  height=400, showlegend=False)
        fig_sec.update_layout(**PLOTLY_TEMPLATE['layout'])

        # Evolucion por sector seleccionado (lineas)
        fig_sec_evo = go.Figure()
        if not e2_f.empty and 'Sector' in e2_f.columns and 'Date' in e2_f.columns:
            sel = sectores_sel if sectores_sel else e2_f['Sector'].unique().tolist()[:5]
            for i, sector in enumerate(sel):
                df_s = e2_f[e2_f['Sector'] == sector].sort_values('Date')
                fig_sec_evo.add_trace(go.Scatter(
                    x=df_s['Date'], y=df_s['Empresas'],
                    mode='lines+markers', name=f"{sector} - {_sector_label(sector)}",
                    line=dict(color=PLOTLY_COLOR_SEQUENCE[i % len(PLOTLY_COLOR_SEQUENCE)], width=2)
                ))
            title_suffix = f" ({len(sel)} sectores)" if len(sel) < 14 else " (todos)"
            fig_sec_evo.update_layout(
                title=f'Evolucion de empresas por sector{title_suffix}',
                yaxis_title='Cantidad', height=400
            )
        fig_sec_evo.update_layout(**PLOTLY_TEMPLATE['layout'])

        return kpi_cards, fig_evo, fig_sec, fig_sec_evo
