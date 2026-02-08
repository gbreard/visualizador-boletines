"""
Tab Genero: KPIs + evolucion por genero + brecha salarial + composicion.
Fuente: boletin_sexo_serie.xlsx (datasets G1-G2).
"""

from dash import html, dcc, Input, Output
import plotly.graph_objects as go
import pandas as pd

from src.config import COLORS, PLOTLY_TEMPLATE, PLOTLY_COLOR_SEQUENCE
from src.data.cache import cache
from src.data.processing import filter_by_dates
from src.layout.components import create_kpi_card, create_section_card, empty_state


def create_genero_layout():
    """Layout de la tab Genero."""
    g1 = cache.get_ref('G1')
    if g1.empty:
        return empty_state(
            "Datos de empleo por genero no disponibles",
            "Ejecute: python scripts/download_oede.py --source genero && "
            "python scripts/preprocess/genero.py"
        )

    if 'Período' in g1.columns and 'Date' in g1.columns:
        sorted_df = g1.sort_values('Date')
        periods = sorted_df['Período'].unique().tolist()
    else:
        periods = []

    period_options = [{'label': p, 'value': p} for p in periods]
    value_hasta = periods[-1] if periods else None
    value_desde = periods[0] if periods else None

    # Indicador de variable
    var_options = [
        {'label': 'Empleo (miles de personas)', 'value': 'empleo'},
        {'label': 'Remuneracion (% composicion)', 'value': 'remuneracion'},
    ]

    return html.Div([
        # Filtros
        html.Div([
            html.Div([
                html.Div([
                    html.Label("Rango de periodos:", style={'fontWeight': '600', 'fontSize': '0.85rem'}),
                    html.Div([
                        dcc.Dropdown(
                            id='gen-fecha-desde',
                            options=period_options,
                            value=value_desde,
                            placeholder="Desde...",
                            style={'width': '180px'}
                        ),
                        html.Span(" - ", className="mx-2"),
                        dcc.Dropdown(
                            id='gen-fecha-hasta',
                            options=period_options,
                            value=value_hasta,
                            placeholder="Hasta...",
                            style={'width': '180px'}
                        ),
                    ], className="d-flex align-items-center"),
                ], className="col-md-5"),
                html.Div([
                    html.Label("Variable:", style={'fontWeight': '600', 'fontSize': '0.85rem'}),
                    dcc.Dropdown(
                        id='gen-variable',
                        options=var_options,
                        value='empleo',
                        clearable=False,
                        style={'width': '250px'}
                    ),
                ], className="col-md-5"),
                html.Div([
                    html.Small(f"Frecuencia: Trimestral | {len(periods)} periodos",
                               style={'color': COLORS['text_muted']})
                ], className="col-md-2 d-flex align-items-center justify-content-end"),
            ], className="row"),
        ], style={'padding': '0.75rem 0', 'marginBottom': '1rem',
                  'borderBottom': f"1px solid {COLORS['border']}"}),

        html.Div(id='gen-kpis', className="row mb-4"),

        html.Div([
            html.Div([
                create_section_card("Evolucion por Genero", [
                    dcc.Graph(id='gen-evolution')
                ])
            ], className="col-md-6"),
            html.Div([
                create_section_card("Composicion por Genero", [
                    dcc.Graph(id='gen-participacion')
                ])
            ], className="col-md-6"),
        ], className="row mb-4"),

        html.Div([
            create_section_card("Brecha Salarial de Genero", [
                dcc.Graph(id='gen-brecha')
            ])
        ]),
    ])


def register_genero_callbacks(app):
    @app.callback(
        [Output('gen-kpis', 'children'),
         Output('gen-evolution', 'figure'),
         Output('gen-participacion', 'figure'),
         Output('gen-brecha', 'figure')],
        [Input('gen-fecha-desde', 'value'),
         Input('gen-fecha-hasta', 'value'),
         Input('gen-variable', 'value')]
    )
    def update_genero(fecha_desde, fecha_hasta, variable):
        import traceback, sys
        try:
            return _update_genero_inner(fecha_desde, fecha_hasta, variable)
        except Exception:
            traceback.print_exc(file=sys.stderr)
            empty_fig = go.Figure()
            empty_fig.update_layout(**PLOTLY_TEMPLATE['layout'])
            return [], empty_fig, empty_fig, empty_fig

    def _update_genero_inner(fecha_desde, fecha_hasta, variable):
        g1 = cache.get_ref('G1')
        g2 = cache.get_ref('G2')

        g1_f = filter_by_dates(g1, fecha_desde, fecha_hasta)
        g2_f = filter_by_dates(g2, fecha_desde, fecha_hasta)

        # KPIs
        kpi_cards = []
        if not g1_f.empty and 'Sexo' in g1_f.columns and 'Empleo' in g1_f.columns:
            latest_date = g1_f['Date'].max()
            latest = g1_f[g1_f['Date'] == latest_date]
            periodo = latest['Período'].iloc[0] if 'Período' in latest.columns else ''

            fem = latest[latest['Sexo'].str.lower().str.contains('fem|mujer')]['Empleo'].sum()
            masc = latest[latest['Sexo'].str.lower().str.contains('masc|varon|hombre')]['Empleo'].sum()
            total = fem + masc
            pct_fem = (fem / total * 100) if total > 0 else 0

            # Brecha del ultimo periodo
            brecha_val = None
            if not g2_f.empty and 'Brecha' in g2_f.columns:
                latest_g2 = g2_f.nlargest(1, 'Date')
                if not latest_g2.empty:
                    brecha_val = latest_g2['Brecha'].iloc[0]

            kpi_cards = [
                html.Div([
                    create_kpi_card("Empleo Femenino", fem,
                                    subtitle=f"Miles | {periodo}",
                                    id_prefix="gen-kpi-fem")
                ], className="col-md-3"),
                html.Div([
                    create_kpi_card("Empleo Masculino", masc,
                                    subtitle=f"Miles | {periodo}",
                                    id_prefix="gen-kpi-masc")
                ], className="col-md-3"),
                html.Div([
                    create_kpi_card("Participacion Fem.", pct_fem,
                                    subtitle="% del total",
                                    id_prefix="gen-kpi-pct", color="info", is_pct=True)
                ], className="col-md-3"),
                html.Div([
                    create_kpi_card("Brecha Salarial",
                                    brecha_val if brecha_val is not None else 0,
                                    subtitle="% diferencia M/V",
                                    id_prefix="gen-kpi-brecha", color="warning", is_pct=True)
                ], className="col-md-3"),
            ]

        # Evolucion por genero
        fig_evo = go.Figure()
        color_map = {'Mujeres': '#E53E3E', 'Varones': '#3182CE',
                     'Femenino': '#E53E3E', 'Masculino': '#3182CE'}

        if variable == 'empleo' and not g1_f.empty and 'Date' in g1_f.columns and 'Sexo' in g1_f.columns:
            for sexo in g1_f['Sexo'].unique():
                df_sexo = g1_f[g1_f['Sexo'] == sexo].sort_values('Date')
                fig_evo.add_trace(go.Scatter(
                    x=df_sexo['Date'], y=df_sexo['Empleo'],
                    mode='lines', name=sexo,
                    line=dict(color=color_map.get(sexo, COLORS['primary_light']), width=2)
                ))
            fig_evo.update_layout(title='Empleo por genero (miles)', yaxis_title='Miles', height=400)
        elif variable == 'remuneracion' and not g2_f.empty and 'Sexo' in g2_f.columns:
            for sexo in g2_f['Sexo'].unique():
                df_sexo = g2_f[g2_f['Sexo'] == sexo].sort_values('Date')
                fig_evo.add_trace(go.Scatter(
                    x=df_sexo['Date'], y=df_sexo['Remuneracion'],
                    mode='lines', name=sexo,
                    line=dict(color=color_map.get(sexo, COLORS['primary_light']), width=2)
                ))
            fig_evo.update_layout(title='Composicion salarial por genero (%)', yaxis_title='%', height=400)
        fig_evo.update_layout(**PLOTLY_TEMPLATE['layout'])

        # Composicion (area apilada - participacion femenina en el tiempo)
        fig_part = go.Figure()
        if not g1_f.empty and 'Sexo' in g1_f.columns:
            # Calcular % por periodo
            pivot = g1_f.pivot_table(index='Date', columns='Sexo', values='Empleo', aggfunc='sum')
            if not pivot.empty:
                total_by_date = pivot.sum(axis=1)
                for col in pivot.columns:
                    pct = pivot[col] / total_by_date * 100
                    fig_part.add_trace(go.Scatter(
                        x=pct.index, y=pct.values,
                        mode='lines', name=col, stackgroup='one',
                        line=dict(color=color_map.get(col, COLORS['primary_light']))
                    ))
            fig_part.update_layout(
                title='Participacion por genero (%)', yaxis_title='%',
                height=400, yaxis=dict(range=[0, 100])
            )
        fig_part.update_layout(**PLOTLY_TEMPLATE['layout'])

        # Brecha salarial
        fig_brecha = go.Figure()
        if not g2_f.empty and 'Date' in g2_f.columns and 'Brecha' in g2_f.columns:
            sorted_g2 = g2_f.drop_duplicates(subset=['Date']).sort_values('Date')
            fig_brecha.add_trace(go.Scatter(
                x=sorted_g2['Date'], y=sorted_g2['Brecha'],
                mode='lines+markers', name='Brecha Salarial',
                line=dict(color=COLORS['danger'], width=2),
                fill='tozeroy', fillcolor='rgba(155, 44, 44, 0.1)'
            ))
            fig_brecha.update_layout(
                title='Brecha salarial de genero (% diferencia)',
                yaxis_title='%', height=400
            )
        fig_brecha.update_layout(**PLOTLY_TEMPLATE['layout'])

        return kpi_cards, fig_evo, fig_part, fig_brecha
