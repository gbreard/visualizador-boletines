"""
Tab Remuneraciones: KPIs + evolucion temporal + sector barras + tabla detalle.
Fuente: nacional_serie_remuneraciones_mensual.xlsx (datasets R1-R4).
"""

from dash import html, dcc, Input, Output, dash_table
import plotly.graph_objects as go
import pandas as pd

from src.config import COLORS, PLOTLY_TEMPLATE, PLOTLY_COLOR_SEQUENCE, SECTOR_CIIU_LETRA
from src.data.cache import cache
from src.data.processing import parse_period_string
from src.layout.components import create_kpi_card, create_section_card, empty_state


def _filter_remuneraciones(df, meses_desde, meses_hasta):
    """Filtra DataFrame de remuneraciones por rango de meses."""
    if df.empty or 'Date' not in df.columns:
        return df
    result = df
    if hasattr(result['Date'], 'cat'):
        result = result.copy()
        result['Date'] = pd.to_datetime(result['Date'])
    if meses_desde:
        dt = parse_period_string(meses_desde)
        if dt:
            result = result[result['Date'] >= dt]
    if meses_hasta:
        dt = parse_period_string(meses_hasta)
        if dt:
            result = result[result['Date'] <= dt]
    return result


def _sector_label(code):
    return SECTOR_CIIU_LETRA.get(code, code)


def create_remuneraciones_layout():
    """Layout de la tab Remuneraciones."""
    r1 = cache.get_ref('R1')
    if r1.empty:
        return empty_state(
            "Datos de remuneraciones no disponibles",
            "Ejecute: python scripts/download_oede.py --source remuneraciones_mensual && "
            "python scripts/preprocess/remuneraciones_mes.py"
        )

    if 'Período' in r1.columns and 'Date' in r1.columns:
        sorted_df = r1.sort_values('Date')
        periods = sorted_df['Período'].unique().tolist()
    else:
        periods = []

    period_options = [{'label': p, 'value': p} for p in periods]
    value_hasta = periods[-1] if periods else None
    value_desde = periods[-60] if len(periods) > 60 else periods[0] if periods else None

    # Opciones de sector desde R3
    r3 = cache.get_ref('R3')
    sector_options = []
    if not r3.empty and 'Sector' in r3.columns:
        sectores = sorted(r3['Sector'].dropna().unique().tolist())
        sector_options = [{'label': f"{s} - {_sector_label(s)}", 'value': s} for s in sectores]

    return html.Div([
        # Controles locales de fecha + sector
        html.Div([
            html.Div([
                html.Div([
                    html.Label("Rango de meses:", style={'fontWeight': '600', 'fontSize': '0.85rem'}),
                    html.Div([
                        dcc.Dropdown(
                            id='rem-fecha-desde',
                            options=period_options,
                            value=value_desde,
                            placeholder="Desde...",
                            style={'width': '180px'}
                        ),
                        html.Span(" - ", className="mx-2"),
                        dcc.Dropdown(
                            id='rem-fecha-hasta',
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
                        id='rem-sector-filter',
                        options=sector_options,
                        value=None,
                        placeholder="Todos los sectores",
                        multi=True,
                        style={'minWidth': '250px'}
                    ),
                ], className="col-md-5"),
                html.Div([
                    html.Small(f"Frecuencia: Mensual | {len(periods)} periodos",
                               style={'color': COLORS['text_muted']})
                ], className="col-md-2 d-flex align-items-center justify-content-end"),
            ], className="row"),
        ], style={'padding': '0.75rem 0', 'marginBottom': '1rem',
                  'borderBottom': f"1px solid {COLORS['border']}"}),

        html.Div(id='rem-kpis', className="row mb-4"),

        html.Div([
            html.Div([
                create_section_card("Evolucion de la Remuneracion", [
                    dcc.Graph(id='rem-evolution')
                ])
            ], className="col-md-7"),
            html.Div([
                create_section_card("Remuneracion por Sector (ultimo mes)", [
                    dcc.Graph(id='rem-sector-bars')
                ])
            ], className="col-md-5"),
        ], className="row mb-4"),

        html.Div([
            create_section_card("Detalle por Sector", [
                html.Div(id='rem-table-container')
            ])
        ]),
    ])


def register_remuneraciones_callbacks(app):
    @app.callback(
        [Output('rem-kpis', 'children'),
         Output('rem-evolution', 'figure'),
         Output('rem-sector-bars', 'figure'),
         Output('rem-table-container', 'children')],
        [Input('rem-fecha-desde', 'value'),
         Input('rem-fecha-hasta', 'value'),
         Input('rem-sector-filter', 'value')]
    )
    def update_remuneraciones(fecha_desde, fecha_hasta, sectores_sel):
        import traceback, sys
        try:
            return _update_rem_inner(fecha_desde, fecha_hasta, sectores_sel)
        except Exception:
            traceback.print_exc(file=sys.stderr)
            empty_fig = go.Figure()
            empty_fig.update_layout(**PLOTLY_TEMPLATE['layout'])
            return [], empty_fig, empty_fig, html.Div()

    def _update_rem_inner(fecha_desde, fecha_hasta, sectores_sel):
        r1 = cache.get_ref('R1')
        r3 = cache.get_ref('R3')

        r1_f = _filter_remuneraciones(r1, fecha_desde, fecha_hasta)
        r3_f = _filter_remuneraciones(r3, fecha_desde, fecha_hasta)

        # === KPIs ===
        kpi_cards = []
        if not r1_f.empty and 'Remuneracion' in r1_f.columns:
            latest = r1_f.nlargest(1, 'Date').iloc[0]
            rem_actual = latest['Remuneracion']
            periodo = latest.get('Período', '')

            sorted_r1 = r1_f.sort_values('Date')
            valid = sorted_r1['Remuneracion'].dropna()
            var_mes = 0
            if len(valid) >= 2:
                prev = valid.iloc[-2]
                var_mes = ((rem_actual - prev) / prev) * 100 if prev != 0 else 0

            var_yoy = 0
            if len(valid) > 12:
                prev_12 = valid.iloc[-13]
                var_yoy = ((rem_actual - prev_12) / prev_12) * 100 if prev_12 != 0 else 0

            trend_mes = 'up' if var_mes > 0 else 'down' if var_mes < 0 else None
            trend_yoy = 'up' if var_yoy > 0 else 'down' if var_yoy < 0 else None

            kpi_cards = [
                html.Div([
                    create_kpi_card("Remuneracion Promedio", rem_actual,
                                    subtitle=f"$ | {periodo}",
                                    id_prefix="rem-kpi-total")
                ], className="col-md-3"),
                html.Div([
                    create_kpi_card("Var. Mensual", var_mes,
                                    subtitle="vs mes anterior",
                                    id_prefix="rem-kpi-mes", trend=trend_mes, is_pct=True)
                ], className="col-md-3"),
                html.Div([
                    create_kpi_card("Var. Interanual", var_yoy,
                                    subtitle="vs mismo mes ano anterior",
                                    id_prefix="rem-kpi-yoy", trend=trend_yoy, is_pct=True)
                ], className="col-md-3"),
                html.Div([
                    create_kpi_card("Periodos", len(r1_f),
                                    subtitle="meses con datos",
                                    id_prefix="rem-kpi-periodos", color="info")
                ], className="col-md-3"),
            ]

        # === Grafico: Evolucion temporal ===
        fig_evo = go.Figure()
        if sectores_sel and not r3_f.empty and 'Sector' in r3_f.columns:
            # Mostrar evolucion por sector seleccionado
            for i, sector in enumerate(sectores_sel):
                df_s = r3_f[r3_f['Sector'] == sector].sort_values('Date')
                if not df_s.empty:
                    fig_evo.add_trace(go.Scatter(
                        x=df_s['Date'], y=df_s['Remuneracion'],
                        mode='lines', name=f"{sector} - {_sector_label(sector)}",
                        line=dict(color=PLOTLY_COLOR_SEQUENCE[i % len(PLOTLY_COLOR_SEQUENCE)], width=2)
                    ))
            fig_evo.update_layout(
                title='Remuneracion promedio por sector ($ corrientes)',
                yaxis_title='Pesos ($)', showlegend=True, height=400
            )
        elif not r1_f.empty and 'Date' in r1_f.columns:
            # Sin filtro de sector: promedio vs mediana
            sorted_r1 = r1_f.sort_values('Date')
            fig_evo.add_trace(go.Scatter(
                x=sorted_r1['Date'], y=sorted_r1['Remuneracion'],
                mode='lines', fill='tozeroy',
                line=dict(color=COLORS['primary_light'], width=2),
                fillcolor='rgba(44, 82, 130, 0.12)',
                name='Promedio'
            ))
            r2 = cache.get_ref('R2')
            r2_f = _filter_remuneraciones(r2, fecha_desde, fecha_hasta)
            if not r2_f.empty:
                sorted_r2 = r2_f.sort_values('Date')
                fig_evo.add_trace(go.Scatter(
                    x=sorted_r2['Date'], y=sorted_r2['Remuneracion'],
                    mode='lines',
                    line=dict(color=COLORS['success'], width=1.5, dash='dash'),
                    name='Mediana'
                ))
            fig_evo.update_layout(
                title='Remuneracion promedio vs mediana ($ corrientes)',
                yaxis_title='Pesos ($)', showlegend=True, height=400
            )
        fig_evo.update_layout(**PLOTLY_TEMPLATE['layout'])

        # === Grafico: Barras por sector ===
        fig_bars = go.Figure()
        if not r3_f.empty and 'Sector' in r3_f.columns:
            ultimo_periodo = r3_f.loc[r3_f['Date'].idxmax(), 'Período'] if 'Date' in r3_f.columns else r3_f['Período'].iloc[-1]
            latest_r3 = r3_f[r3_f['Período'] == ultimo_periodo].dropna(subset=['Remuneracion'])
            if sectores_sel:
                latest_r3 = latest_r3[latest_r3['Sector'].isin(sectores_sel)]
            latest_r3 = latest_r3.sort_values('Remuneracion', ascending=True)

            labels = [_sector_label(s) for s in latest_r3['Sector']]
            fig_bars = go.Figure(go.Bar(
                x=latest_r3['Remuneracion'],
                y=labels,
                orientation='h',
                marker_color=PLOTLY_COLOR_SEQUENCE[:len(labels)],
                text=[f"${v:,.0f}" for v in latest_r3['Remuneracion']],
                textposition='outside',
            ))
            fig_bars.update_layout(
                title=f'Remuneracion promedio por sector - {ultimo_periodo}',
                xaxis_title='Pesos ($)', height=400, showlegend=False,
            )
        fig_bars.update_layout(**PLOTLY_TEMPLATE['layout'])

        # === Tabla detalle ===
        table = html.Div()
        if not r3_f.empty and 'Sector' in r3_f.columns and 'Date' in r3_f.columns:
            ultimo_periodo = r3_f.loc[r3_f['Date'].idxmax(), 'Período']
            latest_r3 = r3_f[r3_f['Período'] == ultimo_periodo].dropna(subset=['Remuneracion']).copy()
            if sectores_sel:
                latest_r3 = latest_r3[latest_r3['Sector'].isin(sectores_sel)]

            sorted_r3 = r3_f.sort_values('Date')
            periodos_unicos = sorted_r3['Date'].unique()
            if len(periodos_unicos) >= 2:
                prev_date = sorted(periodos_unicos)[-2]
                prev_data = r3_f[r3_f['Date'] == prev_date].set_index('Sector')['Remuneracion']
                latest_r3['Var_Mensual'] = latest_r3.apply(
                    lambda row: ((row['Remuneracion'] - prev_data.get(row['Sector'], 0)) /
                                 prev_data.get(row['Sector'], 1) * 100)
                    if row['Sector'] in prev_data.index and prev_data.get(row['Sector'], 0) != 0
                    else None, axis=1
                )
            else:
                latest_r3['Var_Mensual'] = None

            latest_r3['Sector_Desc'] = latest_r3['Sector'].map(_sector_label)
            latest_r3 = latest_r3.sort_values('Remuneracion', ascending=False)

            table_df = latest_r3[['Sector', 'Sector_Desc', 'Remuneracion', 'Var_Mensual']].copy()
            table_df.columns = ['Codigo', 'Sector', 'Remuneracion ($)', 'Var. Mensual (%)']

            table = dash_table.DataTable(
                data=table_df.to_dict('records'),
                columns=[
                    {'name': 'Codigo', 'id': 'Codigo'},
                    {'name': 'Sector', 'id': 'Sector'},
                    {'name': 'Remuneracion ($)', 'id': 'Remuneracion ($)', 'type': 'numeric',
                     'format': {'specifier': ',.0f'}},
                    {'name': 'Var. Mensual (%)', 'id': 'Var. Mensual (%)', 'type': 'numeric',
                     'format': {'specifier': '.2f'}},
                ],
                style_table={'overflowX': 'auto'},
                style_cell={'textAlign': 'left', 'padding': '8px', 'fontSize': '0.85rem'},
                style_header={
                    'backgroundColor': COLORS['primary'],
                    'color': COLORS['white'],
                    'fontWeight': 'bold'
                },
                style_data_conditional=[
                    {'if': {'row_index': 'odd'}, 'backgroundColor': '#F7FAFC'},
                    {'if': {'column_id': 'Var. Mensual (%)', 'filter_query': '{Var. Mensual (%)} > 0'},
                     'color': COLORS['success']},
                    {'if': {'column_id': 'Var. Mensual (%)', 'filter_query': '{Var. Mensual (%)} < 0'},
                     'color': COLORS['danger']},
                ],
                sort_action='native',
                page_size=15,
            )

        return kpi_cards, fig_evo, fig_bars, table
