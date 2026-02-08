"""
Tab Datos: Explorador de datos con metadata, tabla institucional y descarga.
"""

from dash import html, dcc, Input, Output, dash_table

from src.config import DATASET_LABELS, DATASET_DESCRIPTIONS, COLORS
from src.data.cache import cache
from src.data.processing import filter_by_dates
from src.layout.components import empty_state, create_section_card


def create_datos_layout():
    """Layout de la tab Datos."""
    options = [{'label': v, 'value': k} for k, v in DATASET_LABELS.items()]

    return html.Div([
        html.H5("Explorador de Datos",
                 style={'color': COLORS['primary'], 'fontWeight': '600', 'marginBottom': '1rem'}),

        # Selector de dataset
        html.Div([
            html.Div([
                html.Label("Dataset:", style={'fontWeight': '600', 'marginRight': '0.5rem'}),
                dcc.Dropdown(
                    id='dd-dataset-raw',
                    options=options,
                    value='C1.1',
                    style={'width': '400px'}
                )
            ], className="col-md-6"),
        ], className="row mb-3"),

        # Metadata del dataset
        html.Div(id='datos-metadata', className="mb-3"),

        # Tabla
        html.Div(id='div-raw-table')
    ])


def register_datos_callbacks(app):
    @app.callback(
        [Output('datos-metadata', 'children'),
         Output('div-raw-table', 'children')],
        [Input('dd-dataset-raw', 'value'),
         Input('dd-fecha-desde', 'value'),
         Input('dd-fecha-hasta', 'value')]
    )
    def update_raw_table(dataset, fecha_desde, fecha_hasta):
        if not dataset:
            return "", empty_state("Seleccione un dataset")

        df = cache.get(dataset)
        if df.empty:
            return "", empty_state("No hay datos disponibles")

        # Aplicar filtro de fechas si aplica
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
            date_range = f"{df['Período'].iloc[0]} - {df['Período'].iloc[-1]}"

        metadata = html.Div([
            html.Div([
                html.H6(desc_title, style={'fontWeight': '600', 'marginBottom': '0.5rem',
                                            'color': COLORS['primary']}),
                html.P(desc_text, style={'fontSize': '0.85rem', 'color': COLORS['text_muted'],
                                          'marginBottom': '0.75rem'}),
                html.Div([
                    html.Span(f"{total_rows:,} filas", className="sipa-badge sipa-badge-info me-2"),
                    html.Span(f"{total_cols} columnas", className="sipa-badge sipa-badge-info me-2"),
                    html.Span(f"Frecuencia: {desc_freq}", className="sipa-badge sipa-badge-info me-2"),
                    html.Span(f"Rango: {date_range}", className="sipa-badge sipa-badge-info") if date_range else None,
                ])
            ])
        ], className="sipa-card", style={'padding': '1rem'})

        # Columnas
        columns = []
        for col in df.columns:
            col_config = {'name': col, 'id': col}
            if df[col].dtype in ['float64', 'int64']:
                col_config['type'] = 'numeric'
                col_config['format'] = {'specifier': ',.0f'}
            columns.append(col_config)

        # Tabla con estilo institucional
        tabla = dash_table.DataTable(
            data=df.to_dict('records'),
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

        return metadata, create_section_card(
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
