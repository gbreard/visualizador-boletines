"""
Tab Comparaciones: Periodo A vs B multi-fuente con presets rapidos.
Soporta: Empleo (C3), Remuneraciones (R3), Empresas (E2), Flujos (F3).
"""

from dash import html, dcc, Input, Output, State, dash_table
import plotly.express as px
import pandas as pd

from src.config import COLORS, PLOTLY_TEMPLATE, SECTOR_CIIU_LETRA
from src.data.cache import cache
from src.data.processing import parse_period_string
from src.layout.components import empty_state, create_section_card

# Configuracion de variables comparables
VARIABLES = {
    'empleo': {
        'label': 'Empleo por Sector (C3)',
        'dataset': 'C3', 'col': 'Empleo',
        'freq': 'Trimestral', 'unit': 'puestos',
        'preset_offset': {'trim': -1, 'yoy': -4},
    },
    'remuneracion': {
        'label': 'Remuneracion por Sector (R3)',
        'dataset': 'R3', 'col': 'Remuneracion',
        'freq': 'Mensual', 'unit': '$',
        'preset_offset': {'trim': -1, 'yoy': -12},
    },
    'empresas': {
        'label': 'Empresas por Sector (E2)',
        'dataset': 'E2', 'col': 'Empresas',
        'freq': 'Anual', 'unit': 'empresas',
        'preset_offset': {'trim': -1, 'yoy': -1},
    },
    'flujos': {
        'label': 'Creacion Neta por Sector (F3)',
        'dataset': 'F3', 'col': 'Creacion_Neta',
        'freq': 'Trimestral', 'unit': 'puestos netos',
        'preset_offset': {'trim': -1, 'yoy': -4},
    },
}


def _get_periods_for(dataset_key):
    """Obtiene periodos disponibles para un dataset."""
    df = cache.get_ref(dataset_key)
    if df.empty or 'Date' not in df.columns or 'Período' not in df.columns:
        return []
    return df.sort_values('Date')['Período'].unique().tolist()


def _sector_label(code):
    return SECTOR_CIIU_LETRA.get(code, code)


def _get_sector_descriptions():
    """Obtiene mapeo de codigo de sector a descripcion desde descriptores_CIIU."""
    desc_df = cache.get_ref('descriptores_CIIU')
    if desc_df.empty or 'Tabla' not in desc_df.columns:
        return {}
    desc_c3 = desc_df[desc_df['Tabla'] == 'C3']
    return dict(zip(desc_c3['Código'], desc_c3['Descripción']))


def _find_nearest_period(period_str, target_periods):
    """Busca el periodo mas cercano en fecha a period_str dentro de target_periods.
    Retorna el string del periodo mas cercano, o None."""
    if not period_str or not target_periods:
        return None
    dt = parse_period_string(period_str)
    if dt is None:
        return None

    df = cache.get_ref(VARIABLES['empleo']['dataset'])  # solo para tener parse
    best = None
    best_diff = None
    for p in target_periods:
        p_dt = parse_period_string(p)
        if p_dt is None:
            continue
        diff = abs((p_dt - dt).days)
        if best_diff is None or diff < best_diff:
            best_diff = diff
            best = p
    return best


def create_comparaciones_layout():
    """Layout de la tab Comparaciones."""
    var_options = [{'label': v['label'], 'value': k} for k, v in VARIABLES.items()]

    # Periodos iniciales (empleo C3)
    periods = _get_periods_for('C3')
    period_options = [{'label': p, 'value': p} for p in periods]

    return html.Div([
        # Selector de variable + presets
        html.Div([
            html.Div([
                html.Div([
                    html.Label("Variable:", style={'fontWeight': '600', 'fontSize': '0.85rem'}),
                    dcc.Dropdown(
                        id='comp-variable',
                        options=var_options,
                        value='empleo',
                        clearable=False,
                        style={'width': '280px'}
                    ),
                ], className="col-md-5"),
                html.Div([
                    html.Label("Presets:", style={'fontWeight': '600', 'fontSize': '0.85rem'}),
                    html.Div([
                        html.Button("vs Periodo anterior", id='btn-preset-trim-ant',
                                    className="sipa-btn-outline me-2"),
                        html.Button("vs Mismo periodo ano ant.", id='btn-preset-yoy',
                                    className="sipa-btn-outline"),
                    ]),
                ], className="col-md-5"),
                html.Div([
                    html.Div(id='comp-freq-badge',
                             style={'paddingTop': '1.5rem', 'textAlign': 'right'})
                ], className="col-md-2"),
            ], className="row"),
        ], style={'padding': '0.75rem 0', 'marginBottom': '1rem',
                  'borderBottom': f"1px solid {COLORS['border']}"}),

        # Selectores de periodo
        html.Div([
            html.Div([
                html.H6("Periodo A", style={'color': COLORS['primary_light'], 'fontWeight': '600'}),
                dcc.Dropdown(id='dd-periodo-a', options=period_options,
                             placeholder="Seleccione periodo A...")
            ], className="col-md-5"),
            html.Div([
                html.H6("Periodo B", style={'color': COLORS['info'], 'fontWeight': '600'}),
                dcc.Dropdown(id='dd-periodo-b', options=period_options,
                             placeholder="Seleccione periodo B...")
            ], className="col-md-5"),
            html.Div([
                html.Label("Tipo:", style={'fontWeight': '600', 'fontSize': '0.85rem'}),
                dcc.RadioItems(
                    id='rb-tipo-comparacion',
                    options=[
                        {'label': ' Dif. %', 'value': 'pct'},
                        {'label': ' Dif. abs.', 'value': 'abs'},
                        {'label': ' Ratio', 'value': 'ratio'}
                    ],
                    value='pct',
                    inline=False,
                    style={'fontSize': '0.85rem'}
                )
            ], className="col-md-2"),
        ], className="row mb-3"),

        # Validacion
        html.Div(id='comp-validation-msg'),

        # Resultados
        html.Div(id='div-comparacion-results')
    ])


def register_comparaciones_callbacks(app):
    # Callback 1: Actualizar opciones de periodos cuando cambia la variable,
    # preservando la seleccion actual buscando el periodo mas cercano en fecha
    @app.callback(
        [Output('dd-periodo-a', 'options'),
         Output('dd-periodo-b', 'options'),
         Output('dd-periodo-a', 'value'),
         Output('dd-periodo-b', 'value'),
         Output('comp-freq-badge', 'children')],
        [Input('comp-variable', 'value')],
        [State('dd-periodo-a', 'value'),
         State('dd-periodo-b', 'value')]
    )
    def update_period_options(variable, current_a, current_b):
        var_cfg = VARIABLES.get(variable, VARIABLES['empleo'])
        periods = _get_periods_for(var_cfg['dataset'])
        options = [{'label': p, 'value': p} for p in periods]

        # Intentar preservar la seleccion buscando el periodo mas cercano
        if current_a:
            val_a = _find_nearest_period(current_a, periods)
        else:
            val_a = None
        if current_b:
            val_b = _find_nearest_period(current_b, periods)
        else:
            val_b = None

        # Fallback si no se pudo mapear
        if not val_a:
            val_a = periods[-1] if periods else None
        if not val_b:
            offset = var_cfg['preset_offset']['trim']
            val_b = periods[offset] if len(periods) > abs(offset) else (periods[0] if periods else None)

        # Evitar que ambos queden iguales
        if val_a and val_b and val_a == val_b and len(periods) >= 2:
            idx = periods.index(val_a)
            val_b = periods[idx - 1] if idx > 0 else periods[1]

        badge = html.Span(var_cfg['freq'], style={
            'fontSize': '0.8rem', 'color': COLORS['text_muted'],
            'padding': '4px 8px',
            'border': f"1px solid {COLORS['border']}",
            'borderRadius': '4px',
        })

        return options, options, val_a, val_b, badge

    # Callback 2: Presets (solo botones)
    @app.callback(
        [Output('dd-periodo-a', 'value', allow_duplicate=True),
         Output('dd-periodo-b', 'value', allow_duplicate=True)],
        [Input('btn-preset-trim-ant', 'n_clicks'),
         Input('btn-preset-yoy', 'n_clicks')],
        [State('comp-variable', 'value')],
        prevent_initial_call=True
    )
    def apply_preset(n_trim, n_yoy, variable):
        from dash import callback_context
        from dash.exceptions import PreventUpdate
        ctx = callback_context
        if not ctx.triggered:
            raise PreventUpdate

        var_cfg = VARIABLES.get(variable, VARIABLES['empleo'])
        periods = _get_periods_for(var_cfg['dataset'])
        if len(periods) < 2:
            raise PreventUpdate

        trigger = ctx.triggered[0]['prop_id'].split('.')[0]
        if trigger == 'btn-preset-trim-ant':
            offset = var_cfg['preset_offset']['trim']
        elif trigger == 'btn-preset-yoy':
            offset = var_cfg['preset_offset']['yoy']
        else:
            raise PreventUpdate

        val_a = periods[-1]
        val_b = periods[offset] if len(periods) > abs(offset) else periods[0]
        return val_a, val_b

    # Callback 3: Comparacion
    @app.callback(
        [Output('comp-validation-msg', 'children'),
         Output('div-comparacion-results', 'children')],
        [Input('dd-periodo-a', 'value'),
         Input('dd-periodo-b', 'value'),
         Input('rb-tipo-comparacion', 'value'),
         Input('comp-variable', 'value')]
    )
    def update_comparaciones(periodo_a, periodo_b, tipo, variable):
        if not periodo_a or not periodo_b:
            return "", empty_state("Seleccione dos periodos para comparar")

        if periodo_a == periodo_b:
            return (html.Div("Los periodos A y B deben ser diferentes.",
                             className="sipa-alert sipa-alert-warning"),
                    empty_state("Seleccione periodos distintos"))

        var_cfg = VARIABLES.get(variable, VARIABLES['empleo'])
        dataset_key = var_cfg['dataset']
        value_col = var_cfg['col']
        unit = var_cfg['unit']

        df = cache.get(dataset_key)
        if df.empty:
            return "", empty_state(f"No hay datos disponibles para {var_cfg['label']}")

        # Ordenar cronologicamente
        date_a = parse_period_string(periodo_a)
        date_b = parse_period_string(periodo_b)

        if date_a and date_b and date_a < date_b:
            p_anterior, p_posterior = periodo_a, periodo_b
        else:
            p_anterior, p_posterior = periodo_b, periodo_a

        df_ant = df[df['Período'] == p_anterior]
        df_post = df[df['Período'] == p_posterior]

        if df_ant.empty or df_post.empty:
            return "", empty_state(f"Uno de los periodos no tiene datos en {dataset_key}")

        if 'Sector' not in df.columns or value_col not in df.columns:
            return "", empty_state(f"Columnas requeridas no encontradas en {dataset_key}")

        # Descripciones de sector
        if dataset_key == 'C3':
            sector_desc = _get_sector_descriptions()
        else:
            sector_desc = {s: _sector_label(s) for s in df['Sector'].unique()}

        df_comp = pd.merge(
            df_post[['Sector', value_col]].rename(columns={value_col: 'Val_post'}),
            df_ant[['Sector', value_col]].rename(columns={value_col: 'Val_ant'}),
            on='Sector'
        )

        df_comp['Descripcion'] = df_comp['Sector'].map(
            lambda s: sector_desc.get(s, s)
        )

        # Calcular diferencia (siempre posterior - anterior)
        if tipo == 'abs':
            df_comp['Diferencia'] = df_comp['Val_post'] - df_comp['Val_ant']
            title = 'Diferencia absoluta'
            fmt = ',.0f'
        elif tipo == 'pct':
            df_comp['Diferencia'] = df_comp.apply(
                lambda r: ((r['Val_post'] - r['Val_ant']) / r['Val_ant'] * 100)
                if r['Val_ant'] != 0 else 0, axis=1
            )
            title = 'Diferencia porcentual'
            fmt = ',.2f'
        else:
            df_comp['Diferencia'] = df_comp.apply(
                lambda r: r['Val_post'] / r['Val_ant'] if r['Val_ant'] != 0 else 0,
                axis=1
            )
            title = 'Ratio'
            fmt = ',.3f'

        # Grafico de barras horizontales
        df_sorted = df_comp.sort_values('Diferencia')
        fig = px.bar(
            df_sorted,
            x='Diferencia', y='Descripcion', orientation='h',
            title=f'{var_cfg["label"]}: {p_posterior} vs {p_anterior}',
            color='Diferencia',
            color_continuous_scale='RdBu_r',
            color_continuous_midpoint=0 if tipo != 'ratio' else 1
        )
        fig.update_layout(**PLOTLY_TEMPLATE['layout'])
        fig.update_layout(yaxis_title='', height=450)

        # Formato de la columna valor segun tipo de dato
        if value_col == 'Remuneracion':
            val_fmt = ',.0f'
        elif value_col == 'Creacion_Neta':
            val_fmt = '+,.0f'
        else:
            val_fmt = ',.0f'

        # Tabla
        tabla = dash_table.DataTable(
            data=df_comp.to_dict('records'),
            columns=[
                {'name': 'Sector', 'id': 'Descripcion'},
                {'name': f'{p_anterior}', 'id': 'Val_ant', 'type': 'numeric',
                 'format': {'specifier': val_fmt}},
                {'name': f'{p_posterior}', 'id': 'Val_post', 'type': 'numeric',
                 'format': {'specifier': val_fmt}},
                {'name': f'{title} ({"%"  if tipo == "pct" else unit})',
                 'id': 'Diferencia', 'type': 'numeric',
                 'format': {'specifier': fmt}},
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
            sort_action="native",
            page_size=15
        )

        # Resumen
        ganadores = (df_comp['Diferencia'] > 0).sum()
        perdedores = (df_comp['Diferencia'] < 0).sum()
        sin_cambio = (df_comp['Diferencia'] == 0).sum()

        resumen = html.Div([
            html.Span(f"Mejoran: {ganadores}", className="sipa-badge sipa-badge-success me-2"),
            html.Span(f"Empeoran: {perdedores}", className="sipa-badge sipa-badge-danger me-2"),
            html.Span(f"Sin cambio: {sin_cambio}", className="sipa-badge sipa-badge-info me-2") if sin_cambio else None,
            html.Span(f" | {len(df_comp)} sectores comparados",
                      style={'fontSize': '0.8rem', 'color': COLORS['text_muted']}),
        ], style={'marginBottom': '1rem'})

        return "", html.Div([
            resumen,
            create_section_card(f"{title}: {p_posterior} vs {p_anterior}", [
                dcc.Graph(figure=fig),
            ]),
            create_section_card("Tabla de Comparacion", [tabla])
        ])
