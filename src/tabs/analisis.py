"""
Tab Analisis: unifica Temporal + Sectorial + Por Tamano con toggle.
"""

from dash import html, dcc, Input, Output, dash_table, callback_context
from dash.exceptions import PreventUpdate
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from src.config import COLORS, SECTOR_COLORS, PLOTLY_TEMPLATE
from src.data.cache import cache
from src.data.processing import filter_by_dates, process_periods, calculate_variations, get_latest_period_str
from src.layout.components import empty_state, create_section_card


def create_analisis_layout():
    """Layout de la tab Analisis con toggle de sub-vista."""
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

        # Controles locales de metrica y serie base
        html.Div([
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
            ], className="col-md-6"),
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
            ], className="col-md-6")
        ], className="sipa-controls row", id='analisis-controles-metrica',
           style={'margin': '0 0 1rem 0'}),

        # Contenido dinamico
        html.Div(id='analisis-content')
    ])


def register_analisis_callbacks(app):
    # Mostrar/ocultar controles de metrica segun sub-vista
    @app.callback(
        Output('analisis-controles-metrica', 'style'),
        Input('analisis-toggle', 'value')
    )
    def toggle_metrica_controls(vista):
        if vista == 'temporal':
            return {'display': 'flex', 'margin': '0 0 1rem 0'}
        return {'display': 'none'}

    # Contenido principal de analisis
    @app.callback(
        Output('analisis-content', 'children'),
        [Input('analisis-toggle', 'value'),
         Input('analisis-metrica', 'value'),
         Input('analisis-serie-base', 'value'),
         Input('dd-fecha-desde', 'value'),
         Input('dd-fecha-hasta', 'value')]
    )
    def update_analisis(vista, metrica, serie_base, fecha_desde, fecha_hasta):
        if vista == 'temporal':
            return _render_temporal(metrica, serie_base, fecha_desde, fecha_hasta)
        elif vista == 'sectorial':
            return _render_sectorial(fecha_desde, fecha_hasta)
        elif vista == 'tamaño':
            return _render_tamaño(fecha_desde, fecha_hasta)
        return empty_state("Vista no disponible")


def _render_temporal(metrica, serie_base, fecha_desde, fecha_hasta):
    """Sub-vista temporal."""
    if serie_base == 'desest':
        c1 = cache.get('C1.2')
    else:
        c1 = cache.get('C1.1')

    c1 = filter_by_dates(c1, fecha_desde, fecha_hasta)

    if c1.empty:
        return empty_state("No hay datos disponibles",
                           "Verifique el rango de fechas seleccionado")

    # Seleccionar columna segun metrica
    y_col_map = {
        'var_trim': ('var_trim', 'Variacion trimestral (%)'),
        'var_yoy': ('var_yoy', 'Variacion interanual (%)'),
        'index': ('index_100', 'Indice base 100'),
        'niveles': ('Empleo', 'Empleo (puestos de trabajo)')
    }
    y_col, y_title = y_col_map.get(metrica, ('Empleo', 'Empleo'))

    fig = go.Figure()
    if y_col in c1.columns:
        fig.add_trace(go.Scatter(
            x=c1['Date'], y=c1[y_col],
            mode='lines+markers',
            name='Empleo total',
            line=dict(color=COLORS['primary_light'], width=2),
            marker=dict(size=4)
        ))

        # Promedio movil
        c1['MA4'] = c1[y_col].rolling(window=4, min_periods=1).mean()
        fig.add_trace(go.Scatter(
            x=c1['Date'], y=c1['MA4'],
            mode='lines',
            name='Promedio movil (4T)',
            line=dict(color=COLORS['warning'], width=2, dash='dash')
        ))

    fig.update_layout(
        title=f'Evolucion temporal - {y_title}',
        xaxis_title='Periodo',
        yaxis_title=y_title,
        hovermode='x unified',
        showlegend=True,
        height=500
    )
    fig.update_layout(**PLOTLY_TEMPLATE['layout'])

    # Estadisticas resumen
    stats_children = []
    if y_col in c1.columns and not c1[y_col].dropna().empty:
        stats = c1[y_col].describe()
        stats_children = [
            html.Div([
                html.H6("Estadisticas del periodo seleccionado",
                         style={'marginBottom': '0.5rem', 'fontWeight': '600'}),
                html.Div([
                    html.Span(f"Min: {stats['min']:,.1f}", className="sipa-badge sipa-badge-info me-2"),
                    html.Span(f"Max: {stats['max']:,.1f}", className="sipa-badge sipa-badge-info me-2"),
                    html.Span(f"Media: {stats['mean']:,.1f}", className="sipa-badge sipa-badge-info me-2"),
                    html.Span(f"Obs: {int(stats['count'])}", className="sipa-badge sipa-badge-info"),
                ])
            ], className="sipa-controls", style={'marginTop': '1rem'})
        ]

    return html.Div([
        create_section_card(f"Serie Temporal - {y_title}", [
            dcc.Graph(id='analisis-temporal-chart', figure=fig),
        ]),
        html.Div(stats_children)
    ])


def _render_sectorial(fecha_desde, fecha_hasta):
    """Sub-vista sectorial (CIIU)."""
    return html.Div([
        html.Div([
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
            ], className="col-md-4"),
            html.Div([
                html.Label("Codigos:", className="me-2"),
                dcc.Dropdown(
                    id='dd-codigos-sectorial',
                    multi=True,
                    placeholder="Buscar por codigo o descripcion..."
                )
            ], className="col-md-6"),
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
                create_section_card("Empleo por Sector (ultimo periodo)", [
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


def register_sectorial_callbacks(app):
    """Callbacks para la sub-vista sectorial."""

    @app.callback(
        Output('dd-codigos-sectorial', 'options'),
        Input('dd-nivel-ciiu', 'value')
    )
    def update_codigo_options(nivel_ciiu):
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

    @app.callback(
        [Output('bars-ultimo', 'figure'),
         Output('ts-sector', 'figure'),
         Output('tbl-sector-container', 'children')],
        [Input('dd-nivel-ciiu', 'value'),
         Input('dd-codigos-sectorial', 'value'),
         Input('check-top-n', 'value'),
         Input('dd-fecha-desde', 'value'),
         Input('dd-fecha-hasta', 'value')]
    )
    def update_sectorial_charts(nivel_ciiu, codigos, top_n, fecha_desde, fecha_hasta):
        if not nivel_ciiu:
            fig_empty = go.Figure()
            fig_empty.add_annotation(text="Seleccione un nivel CIIU",
                                     xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
            fig_empty.update_layout(**PLOTLY_TEMPLATE['layout'])
            return fig_empty, fig_empty, empty_state("Seleccione parametros")

        df = cache.get(nivel_ciiu)
        df = filter_by_dates(df, fecha_desde, fecha_hasta)
        if df.empty:
            fig_empty = go.Figure()
            fig_empty.add_annotation(text=f"No hay datos para {nivel_ciiu}",
                                     xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
            fig_empty.update_layout(**PLOTLY_TEMPLATE['layout'])
            return fig_empty, fig_empty, empty_state(f"No hay datos para {nivel_ciiu}")

        # Filtrar por codigos
        if codigos:
            df = df[df['Sector'].isin(codigos)]
            if df.empty:
                fig_empty = go.Figure()
                fig_empty.add_annotation(text="Los codigos seleccionados no tienen datos",
                                         xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
                fig_empty.update_layout(**PLOTLY_TEMPLATE['layout'])
                return fig_empty, fig_empty, empty_state(
                    "No hay datos historicos",
                    "Los codigos seleccionados pueden ser actividades nuevas o de baja representatividad")
        elif top_n and 'show' in top_n:
            ultimo_periodo = get_latest_period_str(df) or df['Período'].iloc[-1]
            df_ultimo = df[df['Período'] == ultimo_periodo].nlargest(10, 'Empleo')
            sectores_top = df_ultimo['Sector'].tolist()
            df = df[df['Sector'].isin(sectores_top)]

        if df.empty:
            fig_empty = go.Figure()
            fig_empty.update_layout(**PLOTLY_TEMPLATE['layout'])
            return fig_empty, fig_empty, empty_state("No hay datos con los filtros seleccionados")

        # Barras del ultimo periodo
        ultimo_periodo = get_latest_period_str(df) or df['Período'].iloc[-1]
        df_ultimo = df[df['Período'] == ultimo_periodo].sort_values('Empleo', ascending=True)

        fig_bars = px.bar(
            df_ultimo, x='Empleo', y='Sector', orientation='h',
            title=f'Empleo por sector - {ultimo_periodo}',
            color='Empleo', color_continuous_scale='Blues'
        )
        fig_bars.update_layout(**PLOTLY_TEMPLATE['layout'])

        # Serie temporal
        fig_ts = go.Figure()
        for sector in df['Sector'].unique()[:10]:
            df_sector = df[df['Sector'] == sector]
            fig_ts.add_trace(go.Scatter(
                x=df_sector['Date'] if 'Date' in df_sector.columns else df_sector['Período'],
                y=df_sector['Empleo'],
                mode='lines+markers', name=str(sector),
                marker=dict(size=4)
            ))
        fig_ts.update_layout(title='Evolucion temporal por sector',
                             xaxis_title='Periodo', yaxis_title='Empleo',
                             hovermode='x unified')
        fig_ts.update_layout(**PLOTLY_TEMPLATE['layout'])

        # Tabla con descriptores
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

        df_ultimo_e = df_ultimo.copy()
        df_ultimo_e['Descripción'] = df_ultimo_e['Sector'].apply(
            lambda x: str(desc_dict.get(str(x).strip(),
                          desc_dict.get(str(int(float(x))) if str(x).replace('.', '').isdigit() else x,
                                        'Sin descripcion')))[:50]
        )

        tabla_container = create_section_card(f"Detalle {nivel_ciiu} - {ultimo_periodo}", [
            html.Small(f"Mostrando {len(df_ultimo)} sectores",
                       style={'color': '#718096', 'display': 'block', 'marginBottom': '0.5rem'}),
            dash_table.DataTable(
                data=df_ultimo_e.to_dict('records'),
                columns=[
                    {'name': 'Codigo', 'id': 'Sector'},
                    {'name': 'Descripcion', 'id': 'Descripción'},
                    {'name': 'Empleo', 'id': 'Empleo', 'type': 'numeric', 'format': {'specifier': ',.0f'}}
                ],
                style_cell={'textAlign': 'left', 'padding': '8px', 'fontSize': '0.85rem'},
                style_header={
                    'backgroundColor': '#1B2A4A',
                    'color': 'white',
                    'fontWeight': '600',
                    'padding': '10px 8px'
                },
                style_data_conditional=[
                    {'if': {'row_index': 'odd'}, 'backgroundColor': '#F7FAFC'}
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
                {'name': 'Empleo', 'id': 'Empleo', 'type': 'numeric', 'format': {'specifier': ',.0f'}}
            ],
            style_cell={'textAlign': 'left', 'padding': '8px', 'fontSize': '0.85rem'},
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
