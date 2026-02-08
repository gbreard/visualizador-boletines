"""
Tab Comparaciones: Periodo A vs B con presets rapidos.
"""

from dash import html, dcc, Input, Output, dash_table
import plotly.express as px
import pandas as pd

from src.config import COLORS, PLOTLY_TEMPLATE
from src.data.cache import cache
from src.data.processing import filter_by_dates
from src.layout.components import empty_state, create_section_card


def create_comparaciones_layout():
    """Layout de la tab Comparaciones."""
    periods = cache.periods
    period_options = [{'label': p, 'value': p} for p in periods]

    return html.Div([
        # Presets rapidos
        html.Div([
            html.Label("Presets rapidos:", className="fw-bold me-2"),
            html.Button("vs Trim. anterior", id='btn-preset-trim-ant',
                        className="sipa-btn-outline me-2"),
            html.Button("vs Mismo trim. ano anterior", id='btn-preset-yoy',
                        className="sipa-btn-outline"),
        ], className="mb-3"),

        # Selectores de periodo
        html.Div([
            html.Div([
                html.H6("Periodo A", style={'color': COLORS['primary_light'], 'fontWeight': '600'}),
                dcc.Dropdown(id='dd-periodo-a', options=period_options,
                             placeholder="Seleccione periodo A...")
            ], className="col-md-6"),
            html.Div([
                html.H6("Periodo B", style={'color': COLORS['info'], 'fontWeight': '600'}),
                dcc.Dropdown(id='dd-periodo-b', options=period_options,
                             placeholder="Seleccione periodo B...")
            ], className="col-md-6")
        ], className="row mb-3"),

        # Validacion
        html.Div(id='comp-validation-msg'),

        # Tipo de comparacion
        html.Div([
            html.Label("Tipo de comparacion:", className="me-2"),
            dcc.RadioItems(
                id='rb-tipo-comparacion',
                options=[
                    {'label': 'Diferencia absoluta', 'value': 'abs'},
                    {'label': 'Diferencia %', 'value': 'pct'},
                    {'label': 'Ratio A/B', 'value': 'ratio'}
                ],
                value='pct',
                inline=True
            )
        ], className="sipa-controls", style={'marginBottom': '1rem'}),

        html.Div(id='div-comparacion-results')
    ])


def register_comparaciones_callbacks(app):
    @app.callback(
        [Output('dd-periodo-a', 'value'),
         Output('dd-periodo-b', 'value')],
        [Input('btn-preset-trim-ant', 'n_clicks'),
         Input('btn-preset-yoy', 'n_clicks')],
        prevent_initial_call=True
    )
    def apply_preset(n_trim, n_yoy):
        from dash import callback_context
        ctx = callback_context
        if not ctx.triggered:
            from dash.exceptions import PreventUpdate
            raise PreventUpdate

        periods = cache.periods
        if len(periods) < 2:
            from dash.exceptions import PreventUpdate
            raise PreventUpdate

        trigger = ctx.triggered[0]['prop_id'].split('.')[0]
        if trigger == 'btn-preset-trim-ant':
            return periods[-1], periods[-2]
        elif trigger == 'btn-preset-yoy':
            if len(periods) >= 5:
                return periods[-1], periods[-5]
            return periods[-1], periods[0]
        from dash.exceptions import PreventUpdate
        raise PreventUpdate

    @app.callback(
        [Output('comp-validation-msg', 'children'),
         Output('div-comparacion-results', 'children')],
        [Input('dd-periodo-a', 'value'),
         Input('dd-periodo-b', 'value'),
         Input('rb-tipo-comparacion', 'value'),
         Input('dd-fecha-desde', 'value'),
         Input('dd-fecha-hasta', 'value')]
    )
    def update_comparaciones(periodo_a, periodo_b, tipo, fecha_desde, fecha_hasta):
        if not periodo_a or not periodo_b:
            return "", empty_state("Seleccione dos periodos para comparar")

        # Validar que no sean iguales
        if periodo_a == periodo_b:
            return (html.Div("Los periodos A y B deben ser diferentes.",
                             className="sipa-alert sipa-alert-warning"),
                    empty_state("Seleccione periodos distintos"))

        df = cache.get('C3')
        if df.empty:
            return "", empty_state("No hay datos disponibles")

        df_a = df[df['Período'] == periodo_a]
        df_b = df[df['Período'] == periodo_b]

        if df_a.empty or df_b.empty:
            return "", empty_state("Uno de los periodos no tiene datos")

        df_comp = pd.merge(
            df_a[['Sector', 'Empleo']],
            df_b[['Sector', 'Empleo']],
            on='Sector', suffixes=('_A', '_B')
        )

        if tipo == 'abs':
            df_comp['Diferencia'] = df_comp['Empleo_A'] - df_comp['Empleo_B']
            title = 'Diferencia absoluta'
        elif tipo == 'pct':
            df_comp['Diferencia'] = ((df_comp['Empleo_A'] - df_comp['Empleo_B']) / df_comp['Empleo_B']) * 100
            title = 'Diferencia porcentual'
        else:
            df_comp['Diferencia'] = df_comp['Empleo_A'] / df_comp['Empleo_B']
            title = 'Ratio A/B'

        fig = px.bar(
            df_comp.sort_values('Diferencia'),
            x='Diferencia', y='Sector', orientation='h',
            title=f'{title}: {periodo_a} vs {periodo_b}',
            color='Diferencia',
            color_continuous_scale='RdBu_r',
            color_continuous_midpoint=0
        )
        fig.update_layout(**PLOTLY_TEMPLATE['layout'])

        tabla = dash_table.DataTable(
            data=df_comp.to_dict('records'),
            columns=[
                {'name': 'Sector', 'id': 'Sector'},
                {'name': periodo_a, 'id': 'Empleo_A', 'type': 'numeric', 'format': {'specifier': ',.0f'}},
                {'name': periodo_b, 'id': 'Empleo_B', 'type': 'numeric', 'format': {'specifier': ',.0f'}},
                {'name': title, 'id': 'Diferencia', 'type': 'numeric',
                 'format': {'specifier': ',.2f' if tipo == 'pct' else ',.0f'}}
            ],
            style_cell={'textAlign': 'left', 'padding': '8px', 'fontSize': '0.85rem'},
            style_header={
                'backgroundColor': '#1B2A4A',
                'color': 'white',
                'fontWeight': '600',
                'padding': '10px 8px'
            },
            style_data_conditional=[
                {'if': {'filter_query': '{Diferencia} > 0', 'column_id': 'Diferencia'},
                 'backgroundColor': '#F0FFF4', 'color': '#276749'},
                {'if': {'filter_query': '{Diferencia} < 0', 'column_id': 'Diferencia'},
                 'backgroundColor': '#FFF5F5', 'color': '#9B2C2C'}
            ],
            page_size=15
        )

        return "", html.Div([
            create_section_card(f"{title}: {periodo_a} vs {periodo_b}", [
                dcc.Graph(figure=fig),
            ]),
            create_section_card("Tabla de Comparacion", [tabla])
        ])
