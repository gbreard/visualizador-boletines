"""
Tab Datos: Explorador de datos multi-fuente con filtro por origen, metadata y descarga.
"""

from dash import html, dcc, Input, Output, dash_table

from src.config import (
    DATASET_LABELS, DATASET_DESCRIPTIONS, COLORS,
    EMPLEO_KEYS, REMUNERACIONES_KEYS, EMPRESAS_KEYS, FLUJOS_KEYS, GENERO_KEYS
)
from src.data.cache import cache
from src.data.processing import filter_by_dates
from src.layout.components import empty_state, create_section_card

# Categorias de fuentes
SOURCE_CATEGORIES = {
    'todas': {'label': 'Todas las fuentes', 'keys': None},
    'empleo': {'label': 'Empleo Trimestral', 'keys': EMPLEO_KEYS, 'freq': 'Trimestral'},
    'remuneraciones': {'label': 'Remuneraciones', 'keys': REMUNERACIONES_KEYS, 'freq': 'Mensual'},
    'empresas': {'label': 'Empresas', 'keys': EMPRESAS_KEYS, 'freq': 'Anual'},
    'flujos': {'label': 'Flujos de Empleo', 'keys': FLUJOS_KEYS, 'freq': 'Trimestral'},
    'genero': {'label': 'Genero', 'keys': GENERO_KEYS, 'freq': 'Trimestral'},
}


def _get_available_options(source_key):
    """Retorna opciones de dropdown para la fuente seleccionada, excluyendo datasets vacios."""
    if source_key == 'todas' or source_key is None:
        keys = list(DATASET_LABELS.keys())
    else:
        cat = SOURCE_CATEGORIES.get(source_key, {})
        keys = cat.get('keys', list(DATASET_LABELS.keys())) or list(DATASET_LABELS.keys())

    options = []
    for k in keys:
        if k in DATASET_LABELS:
            df = cache.get_ref(k)
            if not df.empty:
                options.append({'label': DATASET_LABELS[k], 'value': k})
    return options


def create_datos_layout():
    """Layout de la tab Datos."""
    source_options = [{'label': v['label'], 'value': k} for k, v in SOURCE_CATEGORIES.items()]
    dataset_options = _get_available_options('todas')

    # Contar datasets disponibles
    total_available = sum(1 for k in DATASET_LABELS if not cache.get_ref(k).empty)

    return html.Div([
        html.Div([
            html.H5("Explorador de Datos",
                     style={'color': COLORS['primary'], 'fontWeight': '600',
                            'marginBottom': '0.25rem', 'display': 'inline-block'}),
            html.Span(f"  {total_available} datasets disponibles",
                      style={'fontSize': '0.85rem', 'color': COLORS['text_muted'],
                             'marginLeft': '0.75rem'}),
        ], style={'marginBottom': '1rem'}),

        # Fila de filtros
        html.Div([
            html.Div([
                html.Label("Fuente:", style={'fontWeight': '600', 'fontSize': '0.85rem'}),
                dcc.Dropdown(
                    id='dd-datos-source',
                    options=source_options,
                    value='todas',
                    clearable=False,
                    style={'width': '220px'}
                )
            ], className="col-md-3"),
            html.Div([
                html.Label("Dataset:", style={'fontWeight': '600', 'fontSize': '0.85rem'}),
                dcc.Dropdown(
                    id='dd-dataset-raw',
                    options=dataset_options,
                    value='C1.1',
                    style={'width': '100%'}
                )
            ], className="col-md-7"),
            html.Div([
                html.Div(id='datos-stats-badge',
                         style={'paddingTop': '1.5rem', 'textAlign': 'right'})
            ], className="col-md-2"),
        ], className="row mb-3"),

        # Metadata del dataset
        html.Div(id='datos-metadata', className="mb-3"),

        # Tabla
        html.Div(id='div-raw-table')
    ])


def register_datos_callbacks(app):
    # Callback 1: Actualizar opciones del dropdown de dataset segun fuente
    @app.callback(
        [Output('dd-dataset-raw', 'options'),
         Output('dd-dataset-raw', 'value')],
        [Input('dd-datos-source', 'value')]
    )
    def update_dataset_options(source):
        options = _get_available_options(source)
        # Seleccionar el primer dataset disponible
        value = options[0]['value'] if options else None
        return options, value

    # Callback 2: Actualizar metadata, stats y tabla
    @app.callback(
        [Output('datos-metadata', 'children'),
         Output('datos-stats-badge', 'children'),
         Output('div-raw-table', 'children')],
        [Input('dd-dataset-raw', 'value'),
         Input('dd-fecha-desde', 'value'),
         Input('dd-fecha-hasta', 'value')]
    )
    def update_raw_table(dataset, fecha_desde, fecha_hasta):
        if not dataset:
            return "", "", empty_state("Seleccione un dataset")

        df = cache.get(dataset)
        if df.empty:
            return "", "", empty_state("No hay datos disponibles")

        # Contar total antes de filtrar
        total_sin_filtro = len(df)

        # Aplicar filtro de fechas
        df = filter_by_dates(df, fecha_desde, fecha_hasta)

        total_rows = len(df)
        total_cols = len(df.columns)

        # Metadata
        desc_info = DATASET_DESCRIPTIONS.get(dataset, {})
        desc_title = desc_info.get('title', dataset)
        desc_text = desc_info.get('description', '')
        desc_freq = desc_info.get('frequency', 'N/D')

        # Rango de fechas
        date_range = ""
        if 'Período' in df.columns and not df.empty:
            if 'Date' in df.columns:
                sorted_df = df.sort_values('Date')
                date_range = f"{sorted_df['Período'].iloc[0]} - {sorted_df['Período'].iloc[-1]}"
            else:
                date_range = f"{df['Período'].iloc[0]} - {df['Período'].iloc[-1]}"

        # Columnas del dataset (sin las auxiliares)
        display_cols = [c for c in df.columns if c not in ('Date', 'Year', 'Quarter')]

        # Indicador de filtro activo
        filtro_activo = total_rows < total_sin_filtro

        metadata = html.Div([
            html.Div([
                html.H6(desc_title, style={'fontWeight': '600', 'marginBottom': '0.5rem',
                                            'color': COLORS['primary']}),
                html.P(desc_text, style={'fontSize': '0.85rem', 'color': COLORS['text_muted'],
                                          'marginBottom': '0.75rem'}),
                html.Div([
                    html.Span(f"{total_rows:,} filas", className="sipa-badge sipa-badge-info me-2"),
                    html.Span(f"{len(display_cols)} columnas", className="sipa-badge sipa-badge-info me-2"),
                    html.Span(f"Frecuencia: {desc_freq}", className="sipa-badge sipa-badge-info me-2"),
                    html.Span(f"Rango: {date_range}", className="sipa-badge sipa-badge-info me-2") if date_range else None,
                    html.Span(
                        f"Filtrado ({total_rows:,} de {total_sin_filtro:,})",
                        style={
                            'display': 'inline-block',
                            'padding': '2px 8px',
                            'borderRadius': '4px',
                            'fontSize': '0.75rem',
                            'backgroundColor': '#FED7D7',
                            'color': COLORS['danger'],
                        }
                    ) if filtro_activo else None,
                ])
            ])
        ], className="sipa-card", style={'padding': '1rem'})

        # Stats badge
        stats = html.Span(f"{desc_freq}", style={
            'fontSize': '0.8rem', 'color': COLORS['text_muted'],
            'padding': '4px 8px',
            'border': f"1px solid {COLORS['border']}",
            'borderRadius': '4px',
        })

        # Columnas para la tabla (excluir columnas auxiliares)
        columns = []
        for col in display_cols:
            col_config = {'name': col, 'id': col}
            if df[col].dtype in ['float64', 'int64']:
                col_config['type'] = 'numeric'
                col_config['format'] = {'specifier': ',.0f'}
            columns.append(col_config)

        # Preparar datos sin columnas auxiliares
        display_df = df[display_cols]

        # Tabla con estilo institucional
        tabla = dash_table.DataTable(
            data=display_df.to_dict('records'),
            columns=columns,
            style_cell={
                'textAlign': 'left',
                'padding': '8px 10px',
                'fontSize': '0.8rem',
                'border': '1px solid #E2E8F0',
            },
            style_header={
                'backgroundColor': '#1B2A4A',
                'color': 'white',
                'fontWeight': '600',
                'padding': '10px 10px',
                'border': '1px solid #1B2A4A',
            },
            style_data_conditional=[
                {'if': {'row_index': 'odd'}, 'backgroundColor': '#F7FAFC'}
            ],
            filter_action="native",
            sort_action="native",
            page_action="native",
            page_current=0,
            page_size=20,
            export_format="csv",
            export_headers="display"
        )

        return metadata, stats, create_section_card(
            f"Datos: {DATASET_LABELS.get(dataset, dataset)}", [
                html.Div([
                    html.Small("Utilice los filtros de columna para buscar. "
                               "Haga clic en el encabezado para ordenar. "
                               "Boton 'Export' para descargar CSV.",
                               style={'color': COLORS['text_muted'], 'display': 'block',
                                      'marginBottom': '0.75rem'})
                ]),
                tabla
            ]
        )
