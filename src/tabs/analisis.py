"""
Tab Analisis: unifica Temporal + Sectorial + Por Tamano con toggle.
Soporta multiples fuentes de datos (empleo, remuneraciones, empresas, flujos, genero).
"""

from dash import html, dcc, Input, Output, State, dash_table, callback_context, no_update
from dash.exceptions import PreventUpdate
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from src.config import COLORS, SECTOR_COLORS, PLOTLY_TEMPLATE, SECTOR_CIIU_LETRA
from src.data.cache import cache
from src.data.processing import filter_by_dates, process_periods, calculate_variations, get_latest_period_str
from src.layout.components import empty_state, create_section_card

# ---------------------------------------------------------------------------
# Config: Temporal variables
# ---------------------------------------------------------------------------
# Each entry: dataset, y_col, y_label, unit, has_serie_base, multi_series, group_col
TEMPORAL_VARIABLES = {
    'empleo': {
        'label': 'Empleo',
        'dataset': {'estacional': 'C1.1', 'desest': 'C1.2'},
        'y_col': 'Empleo', 'y_label': 'Empleo (puestos de trabajo)',
        'unit': 'puestos', 'has_serie_base': True, 'has_metrica': True,
    },
    'remuneracion_promedio': {
        'label': 'Remuneracion Promedio',
        'dataset': 'R1',
        'y_col': 'Remuneracion', 'y_label': 'Remuneracion promedio ($)',
        'unit': '$', 'has_serie_base': False, 'has_metrica': False,
    },
    'remuneracion_mediana': {
        'label': 'Remuneracion Mediana',
        'dataset': 'R2',
        'y_col': 'Remuneracion', 'y_label': 'Remuneracion mediana ($)',
        'unit': '$', 'has_serie_base': False, 'has_metrica': False,
    },
    'total_empresas': {
        'label': 'Total Empresas',
        'dataset': 'E1',
        'y_col': 'Empresas', 'y_label': 'Cantidad de empresas',
        'unit': 'empresas', 'has_serie_base': False, 'has_metrica': False,
    },
    'flujos_altas': {
        'label': 'Altas de Empleo',
        'dataset': 'F1',
        'y_col': 'Altas', 'y_label': 'Altas de empleo',
        'unit': 'puestos', 'has_serie_base': False, 'has_metrica': False,
    },
    'flujos_bajas': {
        'label': 'Bajas de Empleo',
        'dataset': 'F1',
        'y_col': 'Bajas', 'y_label': 'Bajas de empleo',
        'unit': 'puestos', 'has_serie_base': False, 'has_metrica': False,
    },
    'flujos_creacion': {
        'label': 'Creacion Neta',
        'dataset': 'F1',
        'y_col': 'Creacion_Neta', 'y_label': 'Creacion neta de empleo',
        'unit': 'puestos', 'has_serie_base': False, 'has_metrica': False,
    },
    'tasas_rotacion': {
        'label': 'Tasas de Rotacion',
        'dataset': 'F2',
        'y_col': ['Tasa_Entrada', 'Tasa_Salida', 'Tasa_Rotacion'],
        'y_label': 'Tasa (%)',
        'series_names': ['Tasa Entrada', 'Tasa Salida', 'Tasa Rotacion'],
        'unit': '%', 'has_serie_base': False, 'has_metrica': False,
        'multi_series': True,
    },
    'empleo_genero': {
        'label': 'Empleo por Genero',
        'dataset': 'G1',
        'y_col': 'Empleo', 'y_label': 'Empleo (miles)',
        'unit': 'miles', 'has_serie_base': False, 'has_metrica': False,
        'group_col': 'Sexo',
    },
    'brecha_salarial': {
        'label': 'Brecha Salarial',
        'dataset': 'G2',
        'y_col': 'Brecha', 'y_label': 'Brecha salarial (%)',
        'unit': '%', 'has_serie_base': False, 'has_metrica': False,
    },
}

# ---------------------------------------------------------------------------
# Config: Sectorial sources
# ---------------------------------------------------------------------------
SECTORIAL_SOURCES = {
    'empleo': {
        'label': 'Empleo',
        'has_nivel': True,
        'datasets': {'C3': 'C3', 'C4': 'C4', 'C6': 'C6', 'C7': 'C7'},
        'y_col': 'Empleo', 'y_label': 'Empleo',
    },
    'remuneracion': {
        'label': 'Remuneracion',
        'has_nivel': False,
        'dataset': 'R3',
        'y_col': 'Remuneracion', 'y_label': 'Remuneracion promedio ($)',
    },
    'empresas': {
        'label': 'Empresas',
        'has_nivel': False,
        'dataset': 'E2',
        'y_col': 'Empresas', 'y_label': 'Cantidad de empresas',
    },
    'flujos': {
        'label': 'Flujos (Creacion Neta)',
        'has_nivel': False,
        'dataset': 'F3',
        'y_col': 'Creacion_Neta', 'y_label': 'Creacion neta de empleo',
    },
}


def create_analisis_layout():
    """Layout de la tab Analisis con toggle de sub-vista."""
    variable_options = [{'label': v['label'], 'value': k}
                        for k, v in TEMPORAL_VARIABLES.items()]
    fuente_options = [{'label': v['label'], 'value': k}
                      for k, v in SECTORIAL_SOURCES.items()]

    return html.Div([
        # Toggle superior
        html.Div([
            dcc.RadioItems(
                id='analisis-toggle',
                options=[
                    {'label': 'Temporal', 'value': 'temporal'},
                    {'label': 'Sectorial', 'value': 'sectorial'},
                    {'label': 'Por Tamano', 'value': 'tamaño'}
                ],
                value='temporal',
                inline=True,
                className="mb-0",
                inputClassName="btn-check",
                labelClassName="btn btn-outline-primary"
            )
        ], className="mb-3 text-center"),

        # Controles temporales: Variable + Metrica + Serie base
        html.Div([
            html.Div([
                html.Label("Variable:", className="fw-bold me-2"),
                dcc.Dropdown(
                    id='analisis-variable',
                    options=variable_options,
                    value='empleo',
                    clearable=False,
                    style={'width': '220px'}
                )
            ], className="col-md-3"),
            html.Div([
                html.Label("Metrica:", className="fw-bold me-2"),
                dcc.RadioItems(
                    id='analisis-metrica',
                    options=[
                        {'label': 'Niveles', 'value': 'niveles'},
                        {'label': 'Var. Trim %', 'value': 'var_trim'},
                        {'label': 'Var. Anual %', 'value': 'var_yoy'},
                        {'label': 'Indice', 'value': 'index'}
                    ],
                    value='niveles',
                    inline=True,
                    className="mt-1"
                )
            ], className="col-md-5", id='analisis-metrica-wrapper'),
            html.Div([
                html.Label("Serie base:", className="fw-bold me-2"),
                dcc.RadioItems(
                    id='analisis-serie-base',
                    options=[
                        {'label': 'Con estacionalidad', 'value': 'estacional'},
                        {'label': 'Desestacionalizada', 'value': 'desest'}
                    ],
                    value='estacional',
                    inline=True,
                    className="mt-1"
                )
            ], className="col-md-4", id='analisis-serie-base-wrapper')
        ], className="sipa-controls row", id='analisis-controles-metrica',
           style={'margin': '0 0 1rem 0'}),

        # Contenido dinamico
        html.Div(id='analisis-content')
    ])


def register_analisis_callbacks(app):
    # Mostrar/ocultar controles de metrica segun sub-vista y variable
    @app.callback(
        [Output('analisis-controles-metrica', 'style'),
         Output('analisis-metrica-wrapper', 'style'),
         Output('analisis-serie-base-wrapper', 'style')],
        [Input('analisis-toggle', 'value'),
         Input('analisis-variable', 'value')]
    )
    def toggle_metrica_controls(vista, variable):
        if vista != 'temporal':
            hidden = {'display': 'none'}
            return hidden, hidden, hidden

        show_row = {'display': 'flex', 'margin': '0 0 1rem 0'}
        show = {}
        hidden = {'display': 'none'}

        cfg = TEMPORAL_VARIABLES.get(variable, {})
        metrica_style = show if cfg.get('has_metrica', False) else hidden
        serie_style = show if cfg.get('has_serie_base', False) else hidden
        return show_row, metrica_style, serie_style

    # Contenido principal de analisis
    @app.callback(
        Output('analisis-content', 'children'),
        [Input('analisis-toggle', 'value'),
         Input('analisis-metrica', 'value'),
         Input('analisis-serie-base', 'value'),
         Input('analisis-variable', 'value'),
         Input('dd-fecha-desde', 'value'),
         Input('dd-fecha-hasta', 'value')]
    )
    def update_analisis(vista, metrica, serie_base, variable, fecha_desde, fecha_hasta):
        if vista == 'temporal':
            return _render_temporal(variable or 'empleo', metrica, serie_base,
                                    fecha_desde, fecha_hasta)
        elif vista == 'sectorial':
            return _render_sectorial(fecha_desde, fecha_hasta)
        elif vista == 'tamaño':
            return _render_tamaño(fecha_desde, fecha_hasta)
        return empty_state("Vista no disponible")


def _render_temporal(variable, metrica, serie_base, fecha_desde, fecha_hasta):
    """Sub-vista temporal con selector de variable multi-fuente."""
    cfg = TEMPORAL_VARIABLES.get(variable)
    if not cfg:
        return empty_state("Variable no reconocida")

    # Load dataset
    ds = cfg['dataset']
    if isinstance(ds, dict):
        # Empleo: pick estacional/desest
        df = cache.get(ds.get(serie_base, ds.get('estacional')))
    else:
        df = cache.get(ds)

    df = filter_by_dates(df, fecha_desde, fecha_hasta)

    if df.empty:
        return empty_state("No hay datos disponibles",
                           "Verifique el rango de fechas seleccionado")

    # Determine y columns and title
    multi_series = cfg.get('multi_series', False)
    group_col = cfg.get('group_col')
    y_label = cfg['y_label']

    # For empleo with metrica
    if cfg.get('has_metrica') and metrica != 'niveles':
        y_col_map = {
            'var_trim': ('var_trim', 'Variacion trimestral (%)'),
            'var_yoy': ('var_yoy', 'Variacion interanual (%)'),
            'index': ('index_100', 'Indice base 100'),
        }
        y_col, y_label = y_col_map.get(metrica, (cfg['y_col'], y_label))
    else:
        y_col = cfg['y_col']

    fig = go.Figure()
    colors = PLOTLY_TEMPLATE['layout']['colorway']

    if multi_series:
        # Multiple columns on same dataset (e.g. Tasas)
        series_names = cfg.get('series_names', y_col)
        for i, (col, name) in enumerate(zip(y_col, series_names)):
            if col in df.columns:
                fig.add_trace(go.Scatter(
                    x=df['Date'], y=df[col],
                    mode='lines+markers', name=name,
                    line=dict(color=colors[i % len(colors)], width=2),
                    marker=dict(size=4)
                ))
    elif group_col:
        # Grouped data (e.g. Genero)
        groups = df[group_col].unique()
        for i, grp in enumerate(groups):
            df_g = df[df[group_col] == grp]
            fig.add_trace(go.Scatter(
                x=df_g['Date'], y=df_g[y_col],
                mode='lines+markers', name=str(grp),
                line=dict(color=colors[i % len(colors)], width=2),
                marker=dict(size=4)
            ))
    else:
        # Single series
        if isinstance(y_col, str) and y_col in df.columns:
            fig.add_trace(go.Scatter(
                x=df['Date'], y=df[y_col],
                mode='lines+markers',
                name=cfg['label'],
                line=dict(color=COLORS['primary_light'], width=2),
                marker=dict(size=4)
            ))

            # Moving average (adapt window to frequency)
            ma_window = 4 if cfg.get('unit') != '$' else 6
            df['_MA'] = df[y_col].rolling(window=ma_window, min_periods=1).mean()
            ma_label = f'Promedio movil ({ma_window})'
            fig.add_trace(go.Scatter(
                x=df['Date'], y=df['_MA'],
                mode='lines', name=ma_label,
                line=dict(color=COLORS['warning'], width=2, dash='dash')
            ))

    fig.update_layout(
        title=f'Evolucion temporal - {y_label}',
        xaxis_title='Periodo',
        yaxis_title=y_label,
        hovermode='x unified',
        showlegend=True,
        height=500
    )
    fig.update_layout(**PLOTLY_TEMPLATE['layout'])

    # Summary stats
    stats_children = []
    if not multi_series and not group_col:
        stat_col = y_col if isinstance(y_col, str) else y_col[0]
        if stat_col in df.columns and not df[stat_col].dropna().empty:
            stats = df[stat_col].describe()
            stats_children = [
                html.Div([
                    html.H6("Estadisticas del periodo seleccionado",
                             style={'marginBottom': '0.5rem', 'fontWeight': '600'}),
                    html.Div([
                        html.Span(f"Min: {stats['min']:,.1f}",
                                  className="sipa-badge sipa-badge-info me-2"),
                        html.Span(f"Max: {stats['max']:,.1f}",
                                  className="sipa-badge sipa-badge-info me-2"),
                        html.Span(f"Media: {stats['mean']:,.1f}",
                                  className="sipa-badge sipa-badge-info me-2"),
                        html.Span(f"Obs: {int(stats['count'])}",
                                  className="sipa-badge sipa-badge-info"),
                    ])
                ], className="sipa-controls", style={'marginTop': '1rem'})
            ]

    return html.Div([
        create_section_card(f"Serie Temporal - {y_label}", [
            dcc.Graph(id='analisis-temporal-chart', figure=fig),
        ]),
        html.Div(stats_children)
    ])


def _render_sectorial(fecha_desde, fecha_hasta):
    """Sub-vista sectorial (CIIU) con selector de fuente."""
    fuente_options = [{'label': v['label'], 'value': k}
                      for k, v in SECTORIAL_SOURCES.items()]

    return html.Div([
        html.Div([
            html.Div([
                html.Label("Fuente:", className="me-2"),
                dcc.Dropdown(
                    id='analisis-fuente-sectorial',
                    options=fuente_options,
                    value='empleo',
                    clearable=False,
                    style={'width': '250px'}
                )
            ], className="col-md-3"),
            html.Div([
                html.Label("Nivel CIIU:", className="me-2"),
                dcc.Dropdown(
                    id='dd-nivel-ciiu',
                    options=[
                        {'label': 'C3 - Letra (14 sectores)', 'value': 'C3'},
                        {'label': 'C4 - 2 digitos (56 ramas)', 'value': 'C4'},
                        {'label': 'C6 - 3 digitos (147 ramas)', 'value': 'C6'},
                        {'label': 'C7 - 4 digitos (301 ramas)', 'value': 'C7'}
                    ],
                    value='C4',
                    style={'width': '300px'}
                )
            ], className="col-md-3", id='dd-nivel-ciiu-wrapper'),
            html.Div([
                html.Label("Codigos:", className="me-2"),
                dcc.Dropdown(
                    id='dd-codigos-sectorial',
                    multi=True,
                    placeholder="Buscar por codigo o descripcion..."
                )
            ], className="col-md-4"),
            html.Div([
                dcc.Checklist(
                    id='check-top-n',
                    options=[{'label': 'Top 10', 'value': 'show'}],
                    value=['show'],
                    inline=True
                )
            ], className="col-md-2")
        ], className="sipa-controls row", style={'margin': '0 0 1rem 0'}),

        html.Div([
            html.Div([
                create_section_card("Dato por Sector (ultimo periodo)", [
                    dcc.Graph(id='bars-ultimo', style={'height': '400px'})
                ])
            ], className="col-md-6"),
            html.Div([
                create_section_card("Evolucion Temporal", [
                    dcc.Graph(id='ts-sector', style={'height': '400px'})
                ])
            ], className="col-md-6")
        ], className="row mb-3"),

        html.Div(id='tbl-sector-container', className="col-md-12")
    ])


def _render_tamaño(fecha_desde, fecha_hasta):
    """Sub-vista por tamano de empresa (C5)."""
    return html.Div([
        html.Div([
            html.Div([
                html.Label("Sector:", className="me-2"),
                dcc.Dropdown(
                    id='dd-sector-c5',
                    options=[
                        {'label': 'Industria', 'value': 'Industria'},
                        {'label': 'Comercio', 'value': 'Comercio'},
                        {'label': 'Servicios', 'value': 'Servicios'},
                        {'label': 'Total', 'value': 'Total Industria, Comercio Y Servicios'}
                    ],
                    value='Industria',
                    style={'width': '200px'}
                )
            ], className="col-md-4"),
            html.Div([
                html.Label("Tamano:", className="me-2"),
                dcc.Checklist(
                    id='check-tamaño-c5',
                    options=[
                        {'label': 'Grandes', 'value': 'Grandes'},
                        {'label': 'Medianas', 'value': 'Medianas'},
                        {'label': 'Pequenas', 'value': 'Pequeñas'},
                        {'label': 'Micro', 'value': 'Micro'}
                    ],
                    value=['Grandes', 'Medianas', 'Pequeñas', 'Micro'],
                    inline=True
                )
            ], className="col-md-8")
        ], className="sipa-controls row", style={'margin': '0 0 1rem 0'}),

        html.Div([
            html.Div([
                create_section_card("Composicion por Tamano", [
                    dcc.Graph(id='stack-c5', style={'height': '400px'})
                ])
            ], className="col-md-6"),
            html.Div([
                create_section_card("Evolucion por Tamano", [
                    dcc.Graph(id='ts-c5', style={'height': '400px'})
                ])
            ], className="col-md-6")
        ], className="row mb-3"),

        html.Div(id='tbl-c5-container', className="mt-3")
    ])


def _get_sector_label(sector_code):
    """Map sector CIIU letter code to human-readable label."""
    return SECTOR_CIIU_LETRA.get(str(sector_code), str(sector_code))


def register_sectorial_callbacks(app):
    """Callbacks para la sub-vista sectorial."""

    # Show/hide nivel CIIU based on fuente
    @app.callback(
        Output('dd-nivel-ciiu-wrapper', 'style'),
        Input('analisis-fuente-sectorial', 'value')
    )
    def toggle_nivel_ciiu(fuente):
        cfg = SECTORIAL_SOURCES.get(fuente, {})
        if cfg.get('has_nivel', False):
            return {}
        return {'display': 'none'}

    @app.callback(
        Output('dd-codigos-sectorial', 'options'),
        [Input('dd-nivel-ciiu', 'value'),
         Input('analisis-fuente-sectorial', 'value')]
    )
    def update_codigo_options(nivel_ciiu, fuente):
        cfg = SECTORIAL_SOURCES.get(fuente, {})
        if cfg.get('has_nivel', False):
            # Empleo: use descriptores for selected CIIU level
            if not nivel_ciiu:
                return []
            desc_df = cache.get_ref('descriptores_CIIU')
            if desc_df.empty:
                return []
            desc_filtered = desc_df[desc_df['Tabla'] == nivel_ciiu]
            options = []
            for _, row in desc_filtered.iterrows():
                label = f"{row['Código']} - {str(row['Descripción'])[:50]}..."
                options.append({'label': label, 'value': row['Código']})
            return options
        else:
            # Non-empleo sources: CIIU letter sectors
            return [{'label': f"{k} - {v}", 'value': k}
                    for k, v in SECTOR_CIIU_LETRA.items()]

    @app.callback(
        [Output('bars-ultimo', 'figure'),
         Output('ts-sector', 'figure'),
         Output('tbl-sector-container', 'children')],
        [Input('dd-nivel-ciiu', 'value'),
         Input('dd-codigos-sectorial', 'value'),
         Input('check-top-n', 'value'),
         Input('analisis-fuente-sectorial', 'value'),
         Input('dd-fecha-desde', 'value'),
         Input('dd-fecha-hasta', 'value')]
    )
    def update_sectorial_charts(nivel_ciiu, codigos, top_n, fuente,
                                fecha_desde, fecha_hasta):
        cfg = SECTORIAL_SOURCES.get(fuente or 'empleo', SECTORIAL_SOURCES['empleo'])
        y_col = cfg['y_col']
        y_label = cfg['y_label']

        # Determine which dataset to load
        if cfg.get('has_nivel', False):
            # Empleo: use selected CIIU level
            if not nivel_ciiu:
                fig_empty = go.Figure()
                fig_empty.add_annotation(text="Seleccione un nivel CIIU",
                                         xref="paper", yref="paper",
                                         x=0.5, y=0.5, showarrow=False)
                fig_empty.update_layout(**PLOTLY_TEMPLATE['layout'])
                return fig_empty, fig_empty, empty_state("Seleccione parametros")
            dataset_key = cfg['datasets'].get(nivel_ciiu, 'C3')
            source_label = nivel_ciiu
        else:
            dataset_key = cfg['dataset']
            nivel_ciiu = None  # no level selector for non-empleo
            source_label = cfg['label']

        df = cache.get(dataset_key)
        df = filter_by_dates(df, fecha_desde, fecha_hasta)
        if df.empty:
            fig_empty = go.Figure()
            fig_empty.add_annotation(text=f"No hay datos para {source_label}",
                                     xref="paper", yref="paper",
                                     x=0.5, y=0.5, showarrow=False)
            fig_empty.update_layout(**PLOTLY_TEMPLATE['layout'])
            return fig_empty, fig_empty, empty_state(f"No hay datos para {source_label}")

        # Check that y_col exists
        if y_col not in df.columns:
            fig_empty = go.Figure()
            fig_empty.add_annotation(
                text=f"Columna '{y_col}' no encontrada en {dataset_key}",
                xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
            fig_empty.update_layout(**PLOTLY_TEMPLATE['layout'])
            return fig_empty, fig_empty, empty_state(
                f"Datos no disponibles",
                f"El dataset {dataset_key} no contiene la columna esperada")

        # Filter by selected codes
        if codigos:
            df = df[df['Sector'].isin(codigos)]
            if df.empty:
                fig_empty = go.Figure()
                fig_empty.add_annotation(
                    text="Los codigos seleccionados no tienen datos",
                    xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
                fig_empty.update_layout(**PLOTLY_TEMPLATE['layout'])
                return fig_empty, fig_empty, empty_state(
                    "No hay datos historicos",
                    "Los codigos seleccionados pueden ser actividades nuevas o de baja representatividad")
        elif top_n and 'show' in top_n:
            ultimo_periodo = get_latest_period_str(df) or df['Período'].iloc[-1]
            df_ultimo = df[df['Período'] == ultimo_periodo].nlargest(10, y_col)
            sectores_top = df_ultimo['Sector'].tolist()
            df = df[df['Sector'].isin(sectores_top)]

        if df.empty:
            fig_empty = go.Figure()
            fig_empty.update_layout(**PLOTLY_TEMPLATE['layout'])
            return fig_empty, fig_empty, empty_state(
                "No hay datos con los filtros seleccionados")

        # Bar chart - last period
        ultimo_periodo = get_latest_period_str(df) or df['Período'].iloc[-1]
        df_ultimo = df[df['Período'] == ultimo_periodo].sort_values(
            y_col, ascending=True)

        # Add readable labels for CIIU letter codes in non-empleo sources
        use_sector_labels = not cfg.get('has_nivel', False)
        if use_sector_labels:
            df_ultimo = df_ultimo.copy()
            df_ultimo['Sector_Label'] = df_ultimo['Sector'].apply(_get_sector_label)
            bar_y = 'Sector_Label'
        else:
            bar_y = 'Sector'

        fig_bars = px.bar(
            df_ultimo, x=y_col, y=bar_y, orientation='h',
            title=f'{y_label} por sector - {ultimo_periodo}',
            color=y_col, color_continuous_scale='Blues'
        )
        fig_bars.update_layout(**PLOTLY_TEMPLATE['layout'])

        # Time series
        fig_ts = go.Figure()
        for sector in df['Sector'].unique()[:10]:
            df_sector = df[df['Sector'] == sector]
            x_vals = df_sector['Date'] if 'Date' in df_sector.columns else df_sector['Período']
            label = _get_sector_label(sector) if use_sector_labels else str(sector)
            fig_ts.add_trace(go.Scatter(
                x=x_vals, y=df_sector[y_col],
                mode='lines+markers', name=label,
                marker=dict(size=4)
            ))
        fig_ts.update_layout(title=f'Evolucion temporal - {y_label}',
                             xaxis_title='Periodo', yaxis_title=y_label,
                             hovermode='x unified')
        fig_ts.update_layout(**PLOTLY_TEMPLATE['layout'])

        # Detail table
        df_ultimo_e = df_ultimo.copy()
        desc_col_name = 'Descripción'

        if cfg.get('has_nivel', False) and nivel_ciiu:
            # Empleo: use descriptores_CIIU
            desc_df = cache.get_ref('descriptores_CIIU')
            desc_dict = {}
            if not desc_df.empty:
                desc_filtered = desc_df[desc_df['Tabla'] == nivel_ciiu]
                for _, row in desc_filtered.iterrows():
                    codigo_str = str(row['Código']).strip()
                    try:
                        if nivel_ciiu in ['C4', 'C6', 'C7']:
                            codigo_str = str(int(float(codigo_str)))
                    except Exception:
                        pass
                    desc_dict[codigo_str] = row['Descripción']

            df_ultimo_e[desc_col_name] = df_ultimo_e['Sector'].apply(
                lambda x: str(desc_dict.get(
                    str(x).strip(),
                    desc_dict.get(
                        str(int(float(x))) if str(x).replace('.', '').isdigit() else x,
                        'Sin descripcion')))[:50]
            )
        else:
            # Non-empleo: CIIU letter -> description
            df_ultimo_e[desc_col_name] = df_ultimo_e['Sector'].apply(
                lambda x: SECTOR_CIIU_LETRA.get(str(x), str(x))
            )

        tabla_columns = [
            {'name': 'Codigo', 'id': 'Sector'},
            {'name': 'Descripcion', 'id': desc_col_name},
            {'name': y_label, 'id': y_col, 'type': 'numeric',
             'format': {'specifier': ',.0f'}}
        ]

        tabla_container = create_section_card(
            f"Detalle {source_label} - {ultimo_periodo}", [
                html.Small(f"Mostrando {len(df_ultimo)} sectores",
                           style={'color': '#718096', 'display': 'block',
                                  'marginBottom': '0.5rem'}),
                dash_table.DataTable(
                    data=df_ultimo_e.to_dict('records'),
                    columns=tabla_columns,
                    style_cell={'textAlign': 'left', 'padding': '8px',
                                'fontSize': '0.85rem'},
                    style_header={
                        'backgroundColor': '#1B2A4A',
                        'color': 'white',
                        'fontWeight': '600',
                        'padding': '10px 8px'
                    },
                    style_data_conditional=[
                        {'if': {'row_index': 'odd'},
                         'backgroundColor': '#F7FAFC'}
                    ],
                    sort_action="native",
                    page_size=15
                )
            ])

        return fig_bars, fig_ts, tabla_container


def register_tamaño_callbacks(app):
    """Callbacks para la sub-vista por tamano."""

    @app.callback(
        [Output('stack-c5', 'figure'),
         Output('ts-c5', 'figure'),
         Output('tbl-c5-container', 'children')],
        [Input('dd-sector-c5', 'value'),
         Input('check-tamaño-c5', 'value'),
         Input('dd-fecha-desde', 'value'),
         Input('dd-fecha-hasta', 'value')]
    )
    def update_tamaño_charts(sector, tamaños, fecha_desde, fecha_hasta):
        if not sector or not tamaños:
            return go.Figure(), go.Figure(), empty_state(
                "Seleccione un sector y tamanos",
                "Use los controles para filtrar los datos")

        df = cache.get('C5')
        df = filter_by_dates(df, fecha_desde, fecha_hasta)
        if df.empty:
            return go.Figure(), go.Figure(), empty_state("No hay datos para C5")

        sector_ids = [f"{sector}_{t}" for t in tamaños]
        sector_ids.append(sector)
        df_filtered = df[df['Sector'].isin(sector_ids)]

        if df_filtered.empty:
            return go.Figure(), go.Figure(), empty_state(
                f"No hay datos para {sector}",
                "Intente con otro sector o rango de fechas")

        # Area apilada
        df_pivot = df_filtered.pivot_table(index='Período', columns='Sector',
                                            values='Empleo', aggfunc='sum')
        fig_stack = go.Figure()
        for col in df_pivot.columns:
            if col != sector:
                fig_stack.add_trace(go.Scatter(
                    x=df_pivot.index, y=df_pivot[col],
                    mode='lines', stackgroup='one',
                    name=str(col.split('_')[1] if '_' in col else col)
                ))
        fig_stack.update_layout(title=f'Composicion por tamano - {sector}',
                                xaxis_title='Periodo', yaxis_title='Empleo',
                                hovermode='x unified')
        fig_stack.update_layout(**PLOTLY_TEMPLATE['layout'])

        # Serie temporal
        fig_ts = go.Figure()
        for tamaño in tamaños:
            sector_id = f"{sector}_{tamaño}"
            df_t = df_filtered[df_filtered['Sector'] == sector_id]
            if not df_t.empty:
                fig_ts.add_trace(go.Scatter(
                    x=df_t['Date'] if 'Date' in df_t.columns else df_t['Período'],
                    y=df_t['Empleo'],
                    mode='lines+markers', name=str(tamaño),
                    marker=dict(size=4)
                ))
        fig_ts.update_layout(title=f'Evolucion por tamano - {sector}',
                             xaxis_title='Periodo', yaxis_title='Empleo',
                             hovermode='x unified')
        fig_ts.update_layout(**PLOTLY_TEMPLATE['layout'])

        # Tabla
        ultimo_periodo = get_latest_period_str(df_filtered) or df_filtered['Período'].iloc[-1]
        df_tabla = df_filtered[df_filtered['Período'] == ultimo_periodo][['Sector', 'Empleo']]
        tabla = dash_table.DataTable(
            data=df_tabla.to_dict('records'),
            columns=[
                {'name': 'Categoria', 'id': 'Sector'},
                {'name': 'Empleo', 'id': 'Empleo', 'type': 'numeric',
                 'format': {'specifier': ',.0f'}}
            ],
            style_cell={'textAlign': 'left', 'padding': '8px',
                        'fontSize': '0.85rem'},
            style_header={
                'backgroundColor': '#1B2A4A',
                'color': 'white',
                'fontWeight': '600',
                'padding': '10px 8px'
            },
            style_data_conditional=[
                {'if': {'row_index': 'odd'}, 'backgroundColor': '#F7FAFC'}
            ],
            page_size=10
        )

        return fig_stack, fig_ts, tabla
