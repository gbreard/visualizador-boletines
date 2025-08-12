"""
Dashboard V1 - Visualizador de Boletines de Empleo
Implementación completa con todas las vistas y callbacks
Última actualización: 12 de agosto de 2025
"""

import dash
from dash import dcc, html, Input, Output, State, callback_context, dash_table
from dash.exceptions import PreventUpdate
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime
import os
from functools import lru_cache
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =====================================================================
# CONFIGURACIÓN Y CONSTANTES
# =====================================================================

DATA_DIR = 'datos_limpios'
CACHE_SIZE = 128

# Mapeo de trimestres a meses para fechas
TRIMESTRE_MES = {
    '1º Trim': 2,  # Febrero
    '2º Trim': 5,  # Mayo
    '3º Trim': 8,  # Agosto
    '4º Trim': 11  # Noviembre
}

# Colores corporativos
COLORS = {
    'primary': '#1f77b4',
    'secondary': '#ff7f0e',
    'success': '#2ca02c',
    'danger': '#d62728',
    'warning': '#ff9800',
    'info': '#17a2b8',
    'light': '#f8f9fa',
    'dark': '#343a40'
}

# =====================================================================
# FUNCIONES DE CARGA Y PROCESAMIENTO DE DATOS
# =====================================================================

@lru_cache(maxsize=1)
def load_all_data():
    """
    Carga todos los datos desde archivos Parquet optimizados.
    Retorna un diccionario con todos los DataFrames.
    """
    logger.info("Cargando todos los datos...")
    data = {}
    
    # Mapeo de nombres para archivos Parquet
    parquet_mapping = {
        'C1.1': 'c11.parquet',
        'C1.2': 'c12.parquet',
        'C2.1': 'c2_1.parquet',
        'C2.2': 'c2_2.parquet',
        'C3': 'c3.parquet',
        'C4': 'c4.parquet',
        'C5': 'c5.parquet',
        'C6': 'c6.parquet',
        'C7': 'c7.parquet',
        'descriptores_CIIU': 'descriptores.parquet'
    }
    
    # Primero intentar cargar desde Parquet (más rápido)
    parquet_dir = 'datos_rapidos'
    
    for key, parquet_file in parquet_mapping.items():
        parquet_path = os.path.join(parquet_dir, parquet_file)
        csv_path = os.path.join(DATA_DIR, f'{key}.csv')
        
        # Intentar cargar Parquet primero, si no existe usar CSV
        if os.path.exists(parquet_path):
            df = pd.read_parquet(parquet_path)
        elif os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            # Procesar períodos si existe la columna
            if 'Período' in df.columns:
                df = process_periods(df)
        else:
            continue
            
        # Calcular variaciones si es serie temporal
        if key in ['C1.1', 'C1.2', 'C2.1', 'C2.2', 'C3', 'C4', 'C5', 'C6', 'C7']:
            df = calculate_variations(df)
        
        data[key] = df
        logger.info(f"  {key}: {len(df)} registros cargados")
    
    return data

def process_periods(df):
    """
    Convierte la columna Período a formato Date y agrega columnas auxiliares.
    """
    if 'Período' not in df.columns:
        return df
    
    # Parsear período
    def parse_period(period_str):
        try:
            parts = period_str.split(' ')
            trimestre = f"{parts[0]} {parts[1]}"
            year = int(parts[2])
            month = TRIMESTRE_MES.get(trimestre, 2)
            return pd.Timestamp(year=year, month=month, day=1)
        except:
            return pd.NaT
    
    df['Date'] = df['Período'].apply(parse_period)
    df['Year'] = df['Date'].dt.year
    df['Quarter'] = df['Date'].dt.quarter
    
    return df

def parse_period_string(period_str):
    """
    Convierte un string de período (ej: "4º Trim 2004") a pd.Timestamp.
    """
    try:
        parts = period_str.split(' ')
        trimestre = f"{parts[0]} {parts[1]}"
        year = int(parts[2])
        month = TRIMESTRE_MES.get(trimestre, 2)
        return pd.Timestamp(year=year, month=month, day=1)
    except:
        return None

def calculate_variations(df):
    """
    Calcula variaciones trimestrales e interanuales.
    """
    if 'Empleo' in df.columns and 'Date' in df.columns:
        df = df.sort_values('Date')
        df['var_trim'] = df['Empleo'].pct_change() * 100
        df['var_yoy'] = df['Empleo'].pct_change(4) * 100
        
        # Índice base 100
        if len(df) > 0 and df['Empleo'].iloc[0] != 0:
            df['index_100'] = (df['Empleo'] / df['Empleo'].iloc[0]) * 100
    
    return df

def get_latest_period_data(data):
    """
    Obtiene datos del último período disponible para KPIs.
    """
    c11 = data.get('C1.1', pd.DataFrame())
    
    if not c11.empty and 'Date' in c11.columns:
        latest = c11.nlargest(1, 'Date').iloc[0]
        prev = c11.nlargest(2, 'Date').iloc[1] if len(c11) > 1 else latest
        yoy = c11[c11['Date'] == latest['Date'] - pd.DateOffset(years=1)]
        
        return {
            'empleo_actual': latest['Empleo'] if 'Empleo' in latest else 0,
            'var_trim': latest['var_trim'] if 'var_trim' in latest else 0,
            'var_yoy': latest['var_yoy'] if 'var_yoy' in latest else 0,
            'periodo': latest['Período'] if 'Período' in latest else '',
            'fecha': latest['Date'] if 'Date' in latest else None
        }
    
    return {
        'empleo_actual': 0,
        'var_trim': 0,
        'var_yoy': 0,
        'periodo': 'No disponible',
        'fecha': None
    }

# =====================================================================
# FUNCIONES DE UTILIDADES UI
# =====================================================================

def create_kpi_card(title, value, subtitle="", color="primary", id_prefix="kpi"):
    """
    Crea una tarjeta KPI estilizada.
    """
    value_color = COLORS.get(color, COLORS['primary'])
    
    # Determinar color según el valor
    if isinstance(value, (int, float)):
        if value > 0:
            value_color = COLORS['success']
        elif value < 0:
            value_color = COLORS['danger']
    
    return html.Div([
        html.Div([
            html.H6(title, className="text-muted mb-2"),
            html.H3(
                f"{value:,.0f}" if isinstance(value, (int, float)) and abs(value) > 100 else 
                f"{value:.2f}%" if isinstance(value, (int, float)) else value,
                style={'color': value_color, 'fontWeight': 'bold'}
            ),
            html.Small(subtitle, className="text-muted")
        ], className="card-body")
    ], className="card shadow-sm", id=f"{id_prefix}-card")

def format_number(value):
    """
    Formatea números con separadores de miles.
    """
    if pd.isna(value):
        return "N/D"
    if isinstance(value, (int, float)):
        if abs(value) >= 1000000:
            return f"{value/1000000:.1f}M"
        elif abs(value) >= 1000:
            return f"{value/1000:.1f}K"
        else:
            return f"{value:.1f}"
    return str(value)

# =====================================================================
# INICIALIZACIÓN DE LA APLICACIÓN
# =====================================================================

app = dash.Dash(__name__, external_stylesheets=[
    'https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css'
], suppress_callback_exceptions=True)

app.title = "Dashboard V1 - Visualizador de Empleo"

# =====================================================================
# LAYOUT PRINCIPAL
# =====================================================================

app.layout = html.Div([
    # Header
    html.Div([
        html.H1("📊 Visualizador de Boletines de Empleo - Argentina", 
                className="text-white mb-0"),
        html.P("Sistema Integrado Previsional Argentino (SIPA)", 
               className="text-white-50 mb-0")
    ], className="bg-primary p-4 mb-4"),
    
    # Controles globales
    html.Div([
        html.Div([
            html.Div([
                html.Label("📅 Rango de fechas:", className="fw-bold"),
                html.Div([
                    dcc.Dropdown(
                        id='dd-fecha-desde',
                        placeholder="Desde...",
                        style={'width': '150px'}
                    ),
                    html.Span(" - ", className="mx-2"),
                    dcc.Dropdown(
                        id='dd-fecha-hasta',
                        placeholder="Hasta...",
                        style={'width': '150px'}
                    )
                ], className="d-flex align-items-center")
            ], className="col-md-4"),
            
            html.Div([
                html.Label("📈 Métrica:", className="fw-bold"),
                dcc.RadioItems(
                    id='rb-metrica',
                    options=[
                        {'label': 'Niveles', 'value': 'niveles'},
                        {'label': 'Var. Trim %', 'value': 'var_trim'},
                        {'label': 'Var. Anual %', 'value': 'var_yoy'},
                        {'label': 'Índice', 'value': 'index'}
                    ],
                    value='niveles',
                    inline=True,
                    className="mt-1"
                )
            ], className="col-md-4"),
            
            html.Div([
                html.Label("📊 Serie base:", className="fw-bold"),
                dcc.RadioItems(
                    id='rb-serie-base',
                    options=[
                        {'label': 'Con estacionalidad', 'value': 'estacional'},
                        {'label': 'Desestacionalizada', 'value': 'desest'}
                    ],
                    value='estacional',
                    inline=True,
                    className="mt-1"
                )
            ], className="col-md-4")
        ], className="row")
    ], className="container-fluid bg-light p-3 mb-4 border rounded"),
    
    # Tabs para las diferentes vistas
    dcc.Tabs(id='tabs-main', value='tab-overview', children=[
        dcc.Tab(label='📊 Overview', value='tab-overview'),
        dcc.Tab(label='📈 Análisis Temporal', value='tab-temporal'),
        dcc.Tab(label='🏭 Análisis Sectorial', value='tab-sectorial'),
        dcc.Tab(label='📐 Sector × Tamaño', value='tab-tamaño'),
        dcc.Tab(label='⚖️ Comparaciones', value='tab-comparaciones'),
        dcc.Tab(label='🔔 Alertas', value='tab-alertas'),
        dcc.Tab(label='📋 Datos Crudos', value='tab-datos'),
        dcc.Tab(label='📚 Metodología', value='tab-metodologia')
    ], className="mb-4"),
    
    # Contenedor para el contenido de las tabs
    html.Div(id='tab-content', className="container-fluid"),
    
    # Store para datos compartidos
    dcc.Store(id='store-data', storage_type='memory'),
    dcc.Store(id='store-filtered-data', storage_type='memory'),
    
    # Footer
    html.Div([
        html.Hr(),
        html.P([
            "Dashboard V1 | Última actualización: ",
            html.Span(id='last-update', children=datetime.now().strftime('%d/%m/%Y %H:%M')),
            " | Datos: SIPA/MTEySS"
        ], className="text-center text-muted small")
    ], className="mt-5")
])

# =====================================================================
# FUNCIONES DE CREACIÓN DE VISTAS
# =====================================================================

def create_overview_view(data, serie_base, fecha_desde, fecha_hasta):
    """
    Vista 1: Overview - KPIs principales y distribución sectorial.
    """
    # Obtener datos según serie base
    if serie_base == 'desest':
        c1 = data.get('C1.2', pd.DataFrame())
        c2 = data.get('C2.2', pd.DataFrame())
    else:
        c1 = data.get('C1.1', pd.DataFrame())
        c2 = data.get('C2.1', pd.DataFrame())
    
    c3 = data.get('C3', pd.DataFrame())
    
    # Filtrar por fechas si se especifican
    if fecha_desde and 'Date' in c1.columns:
        fecha_desde_dt = parse_period_string(fecha_desde)
        if fecha_desde_dt:
            c1 = c1[c1['Date'] >= fecha_desde_dt]
    
    if fecha_hasta and 'Date' in c1.columns:
        fecha_hasta_dt = parse_period_string(fecha_hasta)
        if fecha_hasta_dt:
            c1 = c1[c1['Date'] <= fecha_hasta_dt]
    
    # Calcular KPIs
    kpis = get_latest_period_data({'C1.1': c1})
    
    # Calcular sectores top
    if not c3.empty and 'Sector' in c3.columns and 'Empleo' in c3.columns:
        latest_c3 = c3.groupby('Sector')['Empleo'].last().reset_index()
        latest_c3 = latest_c3.sort_values('Empleo', ascending=False)
        top_up = latest_c3.iloc[0]['Sector'] if len(latest_c3) > 0 else "N/D"
        top_down = latest_c3.iloc[-1]['Sector'] if len(latest_c3) > 0 else "N/D"
        
        # Gráfico de torta
        fig_torta = px.pie(
            latest_c3.head(8),
            values='Empleo',
            names='Sector',
            title='Distribución sectorial actual',
            color_discrete_sequence=px.colors.sequential.Blues_r
        )
    else:
        top_up = "N/D"
        top_down = "N/D"
        fig_torta = go.Figure()
    
    # Sparkline del total
    if not c1.empty and 'Date' in c1.columns and 'Empleo' in c1.columns:
        fig_spark = go.Figure()
        fig_spark.add_trace(go.Scatter(
            x=c1['Date'],
            y=c1['Empleo'],
            mode='lines',
            fill='tozeroy',
            line=dict(color=COLORS['primary'], width=2),
            fillcolor='rgba(31, 119, 180, 0.2)'
        ))
        fig_spark.update_layout(
            title='Evolución del empleo total',
            showlegend=False,
            height=300,
            margin=dict(l=0, r=0, t=30, b=0),
            xaxis=dict(showgrid=False, zeroline=False),
            yaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.1)')
        )
    else:
        fig_spark = go.Figure()
    
    return html.Div([
        # Fila de KPIs
        html.Div([
            html.Div([
                create_kpi_card(
                    "Empleo Total", 
                    kpis['empleo_actual'],
                    subtitle=f"Período: {kpis['periodo']}",
                    id_prefix="kpi-total"
                )
            ], className="col-md-3"),
            html.Div([
                create_kpi_card(
                    "Var. Trimestral",
                    kpis['var_trim'],
                    subtitle="vs trimestre anterior",
                    id_prefix="kpi-trim"
                )
            ], className="col-md-3"),
            html.Div([
                create_kpi_card(
                    "Var. Interanual",
                    kpis['var_yoy'],
                    subtitle="vs mismo trimestre año anterior",
                    id_prefix="kpi-yoy"
                )
            ], className="col-md-3"),
            html.Div([
                create_kpi_card("Sector ↑", top_up, id_prefix="kpi-top-up")
            ], className="col-md-3")
        ], className="row mb-4"),
        
        # Fila de gráficos
        html.Div([
            html.Div([
                dcc.Graph(id='share-c3-torta', figure=fig_torta)
            ], className="col-md-6"),
            html.Div([
                dcc.Graph(id='spark-total', figure=fig_spark)
            ], className="col-md-6")
        ], className="row"),
        
        # Botón de descarga
        html.Div([
            html.Button("📥 Descargar datos Overview", 
                       id="btn-overview-download",
                       className="btn btn-primary mt-3")
        ])
    ])

def create_temporal_view(data, serie_base, metrica, fecha_desde, fecha_hasta):
    """
    Vista 2: Análisis Temporal - Series de tiempo con métricas configurables.
    """
    return html.Div([
        # Controles específicos
        html.Div([
            html.Div([
                html.Label("Dataset:", className="me-2"),
                dcc.RadioItems(
                    id='rb-dataset-temporal',
                    options=[
                        {'label': 'Total país', 'value': 'total'},
                        {'label': 'Por sector', 'value': 'sectorial'}
                    ],
                    value='total',
                    inline=True,
                    className="me-4"
                )
            ], className="d-inline-flex align-items-center"),
            
            html.Div([
                dcc.Checklist(
                    id='check-promedio-movil',
                    options=[{'label': 'Mostrar promedio móvil (4T)', 'value': 'show'}],
                    value=[],
                    inline=True
                )
            ], className="d-inline-flex align-items-center ms-4")
        ], className="mb-3"),
        
        # Selector de sectores (aparece si se elige "Por sector")
        html.Div(id='div-selector-sectores', children=[
            dcc.Dropdown(
                id='dd-sectores-temporal',
                multi=True,
                placeholder="Seleccione sectores...",
                options=[
                    {'label': 'Agricultura, ganadería y pesca', 'value': 'Agricultura, ganadería y pesca'},
                    {'label': 'Minería y petróleo', 'value': 'Minería y petróleo (3)'},
                    {'label': 'Industria', 'value': 'Industria'},
                    {'label': 'Electricidad, gas y agua', 'value': 'Electricidad, gas y agua (3)'},
                    {'label': 'Construcción', 'value': 'Construcción'},
                    {'label': 'Comercio', 'value': 'Comercio'},
                    {'label': 'Servicios', 'value': 'Servicios'}
                ],
                value=['Industria', 'Comercio', 'Servicios']
            )
        ], style={'display': 'none'}),
        
        # Gráfico principal
        dcc.Graph(id='ts-main', style={'height': '500px'}),
        
        # Tabla de estadísticas
        html.Div(id='div-stats-temporal', className="mt-3")
    ])

def create_sectorial_view(data):
    """
    Vista 3: Análisis Sectorial - Navegación por jerarquía CIIU.
    """
    return html.Div([
        # Controles
        html.Div([
            html.Div([
                html.Label("Nivel CIIU:", className="me-2"),
                dcc.Dropdown(
                    id='dd-nivel-ciiu',
                    options=[
                        {'label': 'C3 - Letra (14 sectores)', 'value': 'C3'},
                        {'label': 'C4 - 2 dígitos (56 ramas)', 'value': 'C4'},
                        {'label': 'C6 - 3 dígitos (147 ramas)', 'value': 'C6'},
                        {'label': 'C7 - 4 dígitos (301 ramas)', 'value': 'C7'}
                    ],
                    value='C4',
                    style={'width': '300px'}
                )
            ], className="col-md-4"),
            
            html.Div([
                html.Label("Códigos:", className="me-2"),
                dcc.Dropdown(
                    id='dd-codigos-sectorial',
                    multi=True,
                    placeholder="Buscar por código o descripción..."
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
        ], className="row mb-3"),
        
        # Panel 2x2
        html.Div([
            html.Div([
                dcc.Graph(id='bars-ultimo', style={'height': '400px'})
            ], className="col-md-6"),
            html.Div([
                dcc.Graph(id='ts-sector', style={'height': '400px'})
            ], className="col-md-6")
        ], className="row mb-3"),
        
        html.Div([
            html.Div(id='tbl-sector-container', className="col-md-12")
        ], className="row")
    ])

def create_tamaño_view(data):
    """
    Vista 4: Sector × Tamaño - Análisis por tamaño de empresa.
    """
    return html.Div([
        # Controles
        html.Div([
            html.Div([
                html.Label("Sector:", className="me-2"),
                dcc.Dropdown(
                    id='dd-sector-c5',
                    options=[
                        {'label': 'Industria', 'value': 'Industria'},
                        {'label': 'Comercio', 'value': 'Comercio'},
                        {'label': 'Servicios', 'value': 'Servicios'},
                        {'label': 'Total', 'value': 'Total'}
                    ],
                    value='Industria',
                    style={'width': '200px'}
                )
            ], className="col-md-4"),
            
            html.Div([
                html.Label("Tamaño:", className="me-2"),
                dcc.Checklist(
                    id='check-tamaño-c5',
                    options=[
                        {'label': 'Grandes', 'value': 'Grandes'},
                        {'label': 'Medianas', 'value': 'Medianas'},
                        {'label': 'Pequeñas', 'value': 'Pequeñas'},
                        {'label': 'Micro', 'value': 'Micro'}
                    ],
                    value=['Grandes', 'Medianas', 'Pequeñas', 'Micro'],
                    inline=True
                )
            ], className="col-md-8")
        ], className="row mb-3"),
        
        # Gráficos
        html.Div([
            html.Div([
                dcc.Graph(id='stack-c5', style={'height': '400px'})
            ], className="col-md-6"),
            html.Div([
                dcc.Graph(id='ts-c5', style={'height': '400px'})
            ], className="col-md-6")
        ], className="row mb-3"),
        
        # Tabla
        html.Div(id='tbl-c5-container', className="mt-3")
    ])

def create_comparaciones_view(data):
    """
    Vista 5: Comparaciones Personalizadas - Análisis A vs B.
    """
    # Obtener períodos disponibles
    periods = []
    c11 = data.get('C1.1', pd.DataFrame())
    if not c11.empty and 'Período' in c11.columns:
        periods = c11['Período'].unique().tolist()
    
    return html.Div([
        # Controles de períodos
        html.Div([
            html.Div([
                html.H5("Período A", className="text-primary"),
                dcc.Dropdown(
                    id='dd-periodo-a',
                    options=[{'label': p, 'value': p} for p in periods],
                    placeholder="Seleccione período A..."
                )
            ], className="col-md-6"),
            html.Div([
                html.H5("Período B", className="text-info"),
                dcc.Dropdown(
                    id='dd-periodo-b',
                    options=[{'label': p, 'value': p} for p in periods],
                    placeholder="Seleccione período B..."
                )
            ], className="col-md-6")
        ], className="row mb-3"),
        
        # Tipo de comparación
        html.Div([
            html.Label("Tipo de comparación:", className="me-2"),
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
        ], className="mb-3"),
        
        # Resultados
        html.Div(id='div-comparacion-results')
    ])

def create_alertas_view(data, fecha_desde=None, fecha_hasta=None):
    """
    Vista 6: Alertas & Hallazgos - Detección de anomalías.
    """
    return html.Div([
        # Configuración de umbrales
        html.Div([
            html.H5("⚙️ Configuración de Alertas", className="mb-3"),
            html.Div([
                html.Div([
                    html.Label("Umbral variación trimestral (%):", className="me-2"),
                    dcc.Input(
                        id='input-umbral-trim',
                        type='number',
                        value=5,
                        min=0,
                        max=50,
                        step=0.5,
                        style={'width': '100px'}
                    )
                ], className="col-md-3"),
                html.Div([
                    html.Label("Umbral variación anual (%):", className="me-2"),
                    dcc.Input(
                        id='input-umbral-yoy',
                        type='number',
                        value=10,
                        min=0,
                        max=50,
                        step=0.5,
                        style={'width': '100px'}
                    )
                ], className="col-md-3"),
                html.Div([
                    html.Label("Activar alertas automáticas:", className="me-2"),
                    dcc.Checklist(
                        id='check-auto-alertas',
                        options=[{'label': ' Sí', 'value': 'auto'}],
                        value=['auto'],
                        inline=True
                    )
                ], className="col-md-3"),
                html.Div([
                    html.Button("🔍 Actualizar análisis", 
                               id="btn-run-alertas",
                               className="btn btn-warning")
                ], className="col-md-3")
            ], className="row mb-4")
        ]),
        
        # Información del período analizado
        html.Div(id='div-periodo-alertas', className="alert alert-light mb-3"),
        
        # Resultados de alertas - se cargan automáticamente
        html.Div(id='div-alertas-results'),
        
        # Store para trigger inicial y fechas
        dcc.Store(id='store-alertas-init', data={'init': True}),
        dcc.Store(id='store-alertas-fechas', data={'desde': fecha_desde, 'hasta': fecha_hasta})
    ])

def create_datos_view(data):
    """
    Vista 7: Datos Crudos - Tabla con filtros y exportación.
    """
    return html.Div([
        # Selector de dataset
        html.Div([
            html.Label("Dataset:", className="me-2"),
            dcc.Dropdown(
                id='dd-dataset-raw',
                options=[
                    {'label': 'C1.1 - Serie temporal con estacionalidad', 'value': 'C1.1'},
                    {'label': 'C1.2 - Serie temporal desestacionalizada', 'value': 'C1.2'},
                    {'label': 'C2.1 - Por sector con estacionalidad', 'value': 'C2.1'},
                    {'label': 'C2.2 - Por sector desestacionalizada', 'value': 'C2.2'},
                    {'label': 'C3 - Por letra CIIU', 'value': 'C3'},
                    {'label': 'C4 - Por 2 dígitos CIIU', 'value': 'C4'},
                    {'label': 'C5 - Por sector y tamaño', 'value': 'C5'},
                    {'label': 'C6 - Por 3 dígitos CIIU', 'value': 'C6'},
                    {'label': 'C7 - Por 4 dígitos CIIU', 'value': 'C7'},
                    {'label': 'Descriptores CIIU', 'value': 'descriptores_CIIU'}
                ],
                value='C1.1',
                style={'width': '400px'}
            )
        ], className="mb-3"),
        
        # Tabla de datos
        html.Div(id='div-raw-table'),
        
        # Botón de exportación
        html.Div([
            html.Button("📥 Exportar a CSV", 
                       id="btn-export-raw",
                       className="btn btn-success mt-3")
        ])
    ])

def create_metodologia_view():
    """
    Vista 8: Metodología - Explicación de indicadores y fórmulas de cálculo.
    """
    return html.Div([
        html.H3("📚 Metodología e Indicadores", className="mb-4"),
        
        # Introducción
        html.Div([
            html.H5("Introducción", className="text-primary mb-3"),
            html.P([
                "Este dashboard utiliza datos del Sistema Integrado Previsional Argentino (SIPA) ",
                "procesados trimestralmente por el Ministerio de Trabajo, Empleo y Seguridad Social. ",
                "Los indicadores se calculan automáticamente a partir de las series de empleo registrado."
            ], className="lead"),
            html.Hr()
        ], className="mb-4"),
        
        # Indicadores Principales
        html.Div([
            html.H5("1. Indicadores Principales", className="text-primary mb-3"),
            
            # Empleo Total
            html.Div([
                html.H6("📊 Empleo Total (Niveles)", className="fw-bold"),
                html.P("Cantidad absoluta de trabajadores registrados en el período."),
                html.Div([
                    html.Code("Empleo Total = Σ(Trabajadores registrados en SIPA)", className="bg-light p-2 d-block")
                ], className="mb-3")
            ], className="card p-3 mb-3"),
            
            # Variación Trimestral
            html.Div([
                html.H6("📈 Variación Trimestral (%)", className="fw-bold"),
                html.P("Cambio porcentual del empleo respecto al trimestre anterior."),
                html.Div([
                    html.Code("Var. Trimestral = ((Empleo(t) - Empleo(t-1)) / Empleo(t-1)) × 100", className="bg-light p-2 d-block"),
                    html.Small("Donde t = trimestre actual, t-1 = trimestre anterior", className="text-muted")
                ], className="mb-3")
            ], className="card p-3 mb-3"),
            
            # Variación Interanual
            html.Div([
                html.H6("📅 Variación Interanual (año a año) (%)", className="fw-bold"),
                html.P("Cambio porcentual del empleo respecto al mismo trimestre del año anterior."),
                html.Div([
                    html.Code("Var. Interanual = ((Empleo(t) - Empleo(t-4)) / Empleo(t-4)) × 100", className="bg-light p-2 d-block"),
                    html.Small("Donde t = trimestre actual, t-4 = mismo trimestre año anterior", className="text-muted")
                ], className="mb-3")
            ], className="card p-3 mb-3"),
            
            # Índice Base 100
            html.Div([
                html.H6("📐 Índice Base 100", className="fw-bold"),
                html.P("Índice que muestra la evolución del empleo tomando un período base como referencia (100)."),
                html.Div([
                    html.Code("Índice = (Empleo(t) / Empleo(base)) × 100", className="bg-light p-2 d-block"),
                    html.Small("Período base: 1º Trimestre 1996", className="text-muted")
                ], className="mb-3")
            ], className="card p-3 mb-3"),
        ], className="mb-4"),
        
        # Series Temporales
        html.Div([
            html.H5("2. Series Temporales", className="text-primary mb-3"),
            
            html.Div([
                html.H6("Series con Estacionalidad (C1.1, C2.1)", className="fw-bold"),
                html.P("Datos originales sin ajuste estacional. Reflejan las fluctuaciones naturales del empleo por temporada."),
                html.Ul([
                    html.Li("C1.1: Serie total país con estacionalidad"),
                    html.Li("C2.1: Serie por sector económico con estacionalidad")
                ])
            ], className="card p-3 mb-3"),
            
            html.Div([
                html.H6("Series Desestacionalizadas (C1.2, C2.2)", className="fw-bold"),
                html.P("Datos ajustados para eliminar efectos estacionales, permitiendo identificar tendencias subyacentes."),
                html.Ul([
                    html.Li("C1.2: Serie total país desestacionalizada"),
                    html.Li("C2.2: Serie por sector económico desestacionalizada")
                ]),
                html.Small("Método: X-13ARIMA-SEATS del US Census Bureau", className="text-muted")
            ], className="card p-3 mb-3"),
        ], className="mb-4"),
        
        # Clasificación CIIU
        html.Div([
            html.H5("3. Clasificación Industrial (CIIU)", className="text-primary mb-3"),
            
            html.P([
                "Los datos sectoriales se organizan según la Clasificación Industrial Internacional Uniforme (CIIU) Rev. 3, ",
                "con diferentes niveles de desagregación:"
            ]),
            
            html.Table([
                html.Thead([
                    html.Tr([
                        html.Th("Nivel", className="text-center"),
                        html.Th("Descripción"),
                        html.Th("Cantidad"),
                        html.Th("Ejemplo")
                    ])
                ]),
                html.Tbody([
                    html.Tr([
                        html.Td("C3 - Letra", className="text-center fw-bold"),
                        html.Td("Secciones principales"),
                        html.Td("14 sectores"),
                        html.Td("A: Agricultura, B: Pesca, C: Minería...")
                    ]),
                    html.Tr([
                        html.Td("C4 - 2 dígitos", className="text-center fw-bold"),
                        html.Td("Divisiones"),
                        html.Td("56 ramas"),
                        html.Td("15: Alimentos, 24: Químicos...")
                    ]),
                    html.Tr([
                        html.Td("C6 - 3 dígitos", className="text-center fw-bold"),
                        html.Td("Grupos"),
                        html.Td("147 ramas"),
                        html.Td("151: Carnes, 241: Químicos básicos...")
                    ]),
                    html.Tr([
                        html.Td("C7 - 4 dígitos", className="text-center fw-bold"),
                        html.Td("Clases"),
                        html.Td("301 ramas"),
                        html.Td("1511: Mataderos, 2411: Gases industriales...")
                    ])
                ])
            ], className="table table-striped table-hover mb-3"),
        ], className="mb-4"),
        
        # Tamaño de Empresas
        html.Div([
            html.H5("4. Clasificación por Tamaño (C5)", className="text-primary mb-3"),
            
            html.P("El empleo se clasifica por tamaño de empresa según cantidad de empleados:"),
            
            html.Table([
                html.Thead([
                    html.Tr([
                        html.Th("Categoría"),
                        html.Th("Rango de Empleados"),
                        html.Th("Sectores Analizados")
                    ])
                ]),
                html.Tbody([
                    html.Tr([
                        html.Td(html.Strong("Microempresas")),
                        html.Td("1 a 5 empleados"),
                        html.Td(rowSpan="4", style={'verticalAlign': 'middle'}, 
                               children="Industria, Comercio, Servicios, Total")
                    ]),
                    html.Tr([
                        html.Td(html.Strong("Pequeñas")),
                        html.Td("6 a 25 empleados")
                    ]),
                    html.Tr([
                        html.Td(html.Strong("Medianas")),
                        html.Td("26 a 100 empleados")
                    ]),
                    html.Tr([
                        html.Td(html.Strong("Grandes")),
                        html.Td("Más de 100 empleados")
                    ])
                ])
            ], className="table table-striped table-hover mb-3"),
        ], className="mb-4"),
        
        # Indicadores Derivados
        html.Div([
            html.H5("5. Indicadores Derivados y Análisis", className="text-primary mb-3"),
            
            html.Div([
                html.H6("🔄 Promedio Móvil 4 Trimestres", className="fw-bold"),
                html.P("Suaviza la serie temporal calculando el promedio de los últimos 4 trimestres."),
                html.Code("PM4T(t) = (Empleo(t) + Empleo(t-1) + Empleo(t-2) + Empleo(t-3)) / 4", 
                         className="bg-light p-2 d-block mb-3")
            ], className="card p-3 mb-3"),
            
            html.Div([
                html.H6("🎯 Participación Sectorial (%)", className="fw-bold"),
                html.P("Porcentaje que representa cada sector sobre el empleo total."),
                html.Code("Participación = (Empleo_Sector / Empleo_Total) × 100", 
                         className="bg-light p-2 d-block mb-3")
            ], className="card p-3 mb-3"),
            
            html.Div([
                html.H6("⚠️ Detección de Anomalías", className="fw-bold"),
                html.P("Identifica valores atípicos usando desviación estándar sobre ventana móvil."),
                html.Code("Anomalía si: |Valor - Media| > (2 × Desv. Estándar)", 
                         className="bg-light p-2 d-block mb-3"),
                html.Small("Ventana móvil: 8 trimestres", className="text-muted")
            ], className="card p-3 mb-3"),
        ], className="mb-4"),
        
        # Sistema de Alertas
        html.Div([
            html.H5("6. Sistema de Alertas Automáticas", className="text-primary mb-3"),
            
            html.P([
                "El sistema de alertas monitorea automáticamente los datos para identificar situaciones que requieren atención. ",
                "Se ejecuta en tiempo real al cargar los datos y genera notificaciones categorizadas por tipo y severidad."
            ]),
            
            # Tipos de Alertas
            html.Div([
                html.H6("📊 Tipos de Alertas", className="fw-bold mb-3"),
                
                html.Div([
                    html.H6("🔴 Alertas Críticas", className="text-danger"),
                    html.P("Variaciones extremas que requieren atención inmediata:"),
                    html.Ul([
                        html.Li("Caída del empleo > 5% trimestral"),
                        html.Li("Caída del empleo > 10% interanual"),
                        html.Li("Pérdida de más de 50,000 empleos en un trimestre"),
                        html.Li("Sector con caída > 15% interanual")
                    ])
                ], className="card p-3 mb-3 border-danger"),
                
                html.Div([
                    html.H6("🟡 Alertas de Advertencia", className="text-warning"),
                    html.P("Cambios significativos que requieren seguimiento:"),
                    html.Ul([
                        html.Li("Variación trimestral entre ±3% y ±5%"),
                        html.Li("Variación interanual entre ±5% y ±10%"),
                        html.Li("Cambio de tendencia (de positiva a negativa o viceversa)"),
                        html.Li("Aceleración o desaceleración marcada en la tasa de crecimiento")
                    ])
                ], className="card p-3 mb-3 border-warning"),
                
                html.Div([
                    html.H6("🟢 Alertas Positivas", className="text-success"),
                    html.P("Mejoras notables en los indicadores:"),
                    html.Ul([
                        html.Li("Crecimiento del empleo > 3% trimestral"),
                        html.Li("Crecimiento del empleo > 5% interanual"),
                        html.Li("Creación de más de 30,000 empleos en un trimestre"),
                        html.Li("Recuperación después de 3+ trimestres negativos")
                    ])
                ], className="card p-3 mb-3 border-success"),
                
                html.Div([
                    html.H6("🔵 Alertas Informativas", className="text-info"),
                    html.P("Información relevante sin implicancias directas:"),
                    html.Ul([
                        html.Li("Nuevo máximo histórico de empleo"),
                        html.Li("Cambios en la composición sectorial > 2 puntos porcentuales"),
                        html.Li("Datos preliminares o sujetos a revisión"),
                        html.Li("Períodos con información incompleta")
                    ])
                ], className="card p-3 mb-3 border-info"),
            ], className="mb-3"),
            
            # Algoritmos de Detección
            html.Div([
                html.H6("🔍 Algoritmos de Detección", className="fw-bold mb-3"),
                
                html.Div([
                    html.P(html.Strong("1. Detección de Valores Atípicos (Outliers)")),
                    html.Code("Outlier = |X - μ| > k × σ", className="bg-light p-2 d-block mb-2"),
                    html.Small([
                        "Donde: X = valor observado, μ = media móvil (8 trimestres), ",
                        "σ = desviación estándar móvil, k = 2 (factor de sensibilidad)"
                    ], className="text-muted")
                ], className="mb-3"),
                
                html.Div([
                    html.P(html.Strong("2. Detección de Cambios de Tendencia")),
                    html.Code("Cambio = sign(Var[t]) ≠ sign(Var[t-1]) por 2+ períodos", className="bg-light p-2 d-block mb-2"),
                    html.Small("Identifica cuando la dirección del cambio se invierte consistentemente", className="text-muted")
                ], className="mb-3"),
                
                html.Div([
                    html.P(html.Strong("3. Detección de Aceleración/Desaceleración")),
                    html.Code("Aceleración = |Var[t] - Var[t-1]| > 1.5 puntos porcentuales", className="bg-light p-2 d-block mb-2"),
                    html.Small("Detecta cambios bruscos en la velocidad de crecimiento", className="text-muted")
                ], className="mb-3"),
                
                html.Div([
                    html.P(html.Strong("4. Análisis Sectorial Comparativo")),
                    html.Code("Alerta Sectorial = Var_Sector < (Var_Total - 5pp)", className="bg-light p-2 d-block mb-2"),
                    html.Small("Identifica sectores con desempeño significativamente inferior al promedio", className="text-muted")
                ], className="mb-3"),
            ]),
            
            # Configuración de Umbrales
            html.Div([
                html.H6("⚙️ Configuración de Umbrales", className="fw-bold mb-3"),
                
                html.Table([
                    html.Thead([
                        html.Tr([
                            html.Th("Parámetro"),
                            html.Th("Valor Por Defecto"),
                            html.Th("Rango Configurable"),
                            html.Th("Descripción")
                        ])
                    ]),
                    html.Tbody([
                        html.Tr([
                            html.Td("Umbral Crítico Trimestral"),
                            html.Td("±5%"),
                            html.Td("3% - 10%"),
                            html.Td("Variación trimestral para alerta crítica")
                        ]),
                        html.Tr([
                            html.Td("Umbral Crítico Interanual"),
                            html.Td("±10%"),
                            html.Td("5% - 15%"),
                            html.Td("Variación interanual para alerta crítica")
                        ]),
                        html.Tr([
                            html.Td("Ventana de Análisis"),
                            html.Td("8 trimestres"),
                            html.Td("4 - 12 trimestres"),
                            html.Td("Períodos para cálculo de estadísticas móviles")
                        ]),
                        html.Tr([
                            html.Td("Factor de Sensibilidad"),
                            html.Td("2σ"),
                            html.Td("1.5σ - 3σ"),
                            html.Td("Desviaciones estándar para outliers")
                        ]),
                        html.Tr([
                            html.Td("Mínimo de Períodos"),
                            html.Td("2"),
                            html.Td("1 - 4"),
                            html.Td("Períodos consecutivos para confirmar tendencia")
                        ])
                    ])
                ], className="table table-striped table-hover mb-3"),
            ]),
            
            # Interpretación y Acciones
            html.Div([
                html.H6("📌 Interpretación y Acciones Sugeridas", className="fw-bold mb-3"),
                
                html.Div([
                    html.P(html.Strong("Para Alertas Críticas:")),
                    html.Ol([
                        html.Li("Verificar la calidad de los datos y posibles errores de carga"),
                        html.Li("Analizar el contexto económico del período"),
                        html.Li("Revisar sectores más afectados"),
                        html.Li("Comparar con indicadores complementarios"),
                        html.Li("Generar reporte detallado para análisis profundo")
                    ])
                ], className="alert alert-danger"),
                
                html.Div([
                    html.P(html.Strong("Para Alertas de Advertencia:")),
                    html.Ol([
                        html.Li("Monitorear evolución en próximos períodos"),
                        html.Li("Identificar factores causales"),
                        html.Li("Evaluar si es un cambio estructural o coyuntural"),
                        html.Li("Preparar análisis de escenarios")
                    ])
                ], className="alert alert-warning"),
            ]),
            
            # Notas sobre el Sistema
            html.Div([
                html.H6("📝 Notas Importantes del Sistema de Alertas", className="fw-bold mb-3"),
                html.Ul([
                    html.Li("Las alertas se generan automáticamente al cargar nuevos datos"),
                    html.Li("Los umbrales pueden ajustarse según el contexto económico"),
                    html.Li("Se priorizan las alertas más recientes (últimos 4 trimestres)"),
                    html.Li("Las alertas sectoriales consideran el peso relativo del sector"),
                    html.Li("El sistema aprende de patrones históricos para mejorar la detección"),
                    html.Li("Se pueden exportar las alertas para seguimiento externo")
                ])
            ], className="alert alert-info"),
        ], className="mb-4"),
        
        # Fuentes de Datos
        html.Div([
            html.H5("7. Fuentes y Actualización", className="text-primary mb-3"),
            
            html.Div([
                html.P([
                    html.Strong("Fuente primaria: "),
                    "Sistema Integrado Previsional Argentino (SIPA)"
                ]),
                html.P([
                    html.Strong("Procesamiento: "),
                    "Ministerio de Trabajo, Empleo y Seguridad Social (MTEySS)"
                ]),
                html.P([
                    html.Strong("Periodicidad: "),
                    "Trimestral con rezago de 2-3 meses"
                ]),
                html.P([
                    html.Strong("Cobertura temporal: "),
                    "Desde 1º Trimestre 1996 hasta la actualidad"
                ]),
                html.P([
                    html.Strong("Última actualización de datos: "),
                    "4º Trimestre 2024"
                ])
            ], className="card p-3"),
        ], className="mb-4"),
        
        # Notas Técnicas
        html.Div([
            html.H5("8. Notas Técnicas", className="text-primary mb-3"),
            
            html.Div([
                html.H6("📝 Consideraciones Importantes:"),
                html.Ul([
                    html.Li("Los datos corresponden únicamente al empleo registrado (formal)"),
                    html.Li("No incluye empleo público provincial ni municipal"),
                    html.Li("Las series pueden tener revisiones retroactivas"),
                    html.Li("Valores faltantes se indican como 's.d.' (sin dato) en archivos fuente"),
                    html.Li("Los cálculos de variaciones requieren al menos 2 períodos (trimestral) o 5 períodos (interanual)")
                ])
            ], className="alert alert-info"),
        ], className="mb-4"),
        
        # Glosario
        html.Div([
            html.H5("9. Glosario", className="text-primary mb-3"),
            
            html.Dl([
                html.Dt("SIPA"),
                html.Dd("Sistema Integrado Previsional Argentino", className="mb-2"),
                
                html.Dt("CIIU"),
                html.Dd("Clasificación Industrial Internacional Uniforme de todas las actividades económicas", className="mb-2"),
                
                html.Dt("MTEySS"),
                html.Dd("Ministerio de Trabajo, Empleo y Seguridad Social", className="mb-2"),
                
                html.Dt("Empleo Registrado"),
                html.Dd("Trabajadores en relación de dependencia con aportes al sistema de seguridad social", className="mb-2"),
                
                html.Dt("Desestacionalización"),
                html.Dd("Proceso estadístico para remover patrones estacionales regulares de una serie temporal", className="mb-2"),
                
                html.Dt("KPI"),
                html.Dd("Key Performance Indicator (Indicador Clave de Desempeño)", className="mb-2"),
            ])
        ], className="mb-4")
    ])

# =====================================================================
# CALLBACKS
# =====================================================================

# Callback para inicializar los datos
@app.callback(
    Output('store-data', 'data'),
    Input('tabs-main', 'value')
)
def load_data_to_store(tab):
    """Carga los datos en el store cuando se inicia la aplicación."""
    data = load_all_data()
    # Convertir DataFrames a dict para almacenar en Store
    data_dict = {}
    for key, df in data.items():
        if isinstance(df, pd.DataFrame):
            data_dict[key] = df.to_dict('records')
    return data_dict

# Callback para actualizar opciones de fechas
@app.callback(
    [Output('dd-fecha-desde', 'options'),
     Output('dd-fecha-hasta', 'options'),
     Output('dd-fecha-desde', 'value'),
     Output('dd-fecha-hasta', 'value')],
    Input('store-data', 'data')
)
def update_date_options(data_dict):
    """Actualiza las opciones de fecha basándose en los datos disponibles."""
    if not data_dict:
        return [], [], None, None
    
    # Reconstruir DataFrame
    c11_data = data_dict.get('C1.1', [])
    if not c11_data:
        return [], [], None, None
    
    c11 = pd.DataFrame(c11_data)
    if 'Período' not in c11.columns:
        return [], [], None, None
    
    periods = sorted(c11['Período'].unique())
    options = [{'label': p, 'value': p} for p in periods]
    
    # Valores por defecto: últimos 5 años
    value_hasta = periods[-1] if periods else None
    value_desde = periods[-20] if len(periods) > 20 else periods[0] if periods else None
    
    return options, options, value_desde, value_hasta

# Callback principal para actualizar contenido de tabs
@app.callback(
    Output('tab-content', 'children'),
    [Input('tabs-main', 'value'),
     Input('store-data', 'data'),
     Input('rb-serie-base', 'value'),
     Input('rb-metrica', 'value'),
     Input('dd-fecha-desde', 'value'),
     Input('dd-fecha-hasta', 'value')]
)
def update_tab_content(active_tab, data_dict, serie_base, metrica, fecha_desde, fecha_hasta):
    """Actualiza el contenido según la tab seleccionada."""
    if not data_dict:
        return html.Div("Cargando datos...", className="text-center p-5")
    
    # Reconstruir DataFrames
    data = {}
    for key, records in data_dict.items():
        data[key] = pd.DataFrame(records)
        # Re-procesar períodos
        if 'Período' in data[key].columns:
            data[key] = process_periods(data[key])
    
    # Renderizar vista según tab
    if active_tab == 'tab-overview':
        return create_overview_view(data, serie_base, fecha_desde, fecha_hasta)
    elif active_tab == 'tab-temporal':
        return create_temporal_view(data, serie_base, metrica, fecha_desde, fecha_hasta)
    elif active_tab == 'tab-sectorial':
        return create_sectorial_view(data)
    elif active_tab == 'tab-tamaño':
        return create_tamaño_view(data)
    elif active_tab == 'tab-comparaciones':
        return create_comparaciones_view(data)
    elif active_tab == 'tab-alertas':
        return create_alertas_view(data, fecha_desde, fecha_hasta)
    elif active_tab == 'tab-datos':
        return create_datos_view(data)
    elif active_tab == 'tab-metodologia':
        return create_metodologia_view()
    else:
        return html.Div("Vista no implementada", className="text-center p-5")

# Callback para mostrar/ocultar selector de sectores
@app.callback(
    Output('div-selector-sectores', 'style'),
    Input('rb-dataset-temporal', 'value')
)
def toggle_sector_selector(dataset):
    """Muestra u oculta el selector de sectores según el dataset elegido."""
    if dataset == 'sectorial':
        return {'display': 'block', 'marginTop': '10px'}
    return {'display': 'none'}

# Callback para actualizar gráfico temporal
@app.callback(
    Output('ts-main', 'figure'),
    [Input('rb-dataset-temporal', 'value'),
     Input('dd-sectores-temporal', 'value'),
     Input('check-promedio-movil', 'value'),
     Input('store-data', 'data'),
     Input('rb-serie-base', 'value'),
     Input('rb-metrica', 'value'),
     Input('dd-fecha-desde', 'value'),
     Input('dd-fecha-hasta', 'value')]
)
def update_temporal_chart(dataset, sectores, promedio_movil, data_dict, serie_base, 
                          metrica, fecha_desde, fecha_hasta):
    """Actualiza el gráfico de análisis temporal."""
    if not data_dict:
        return go.Figure()
    
    fig = go.Figure()
    
    # Seleccionar serie según configuración
    if dataset == 'total':
        if serie_base == 'desest':
            df_key = 'C1.2'
        else:
            df_key = 'C1.1'
        
        df = pd.DataFrame(data_dict.get(df_key, []))
        if not df.empty:
            df = process_periods(df)
            df = calculate_variations(df)
            
            # Filtrar por fechas
            if fecha_desde and 'Date' in df.columns:
                fecha_desde_dt = parse_period_string(fecha_desde)
                if fecha_desde_dt:
                    df = df[df['Date'] >= fecha_desde_dt]
            
            if fecha_hasta and 'Date' in df.columns:
                fecha_hasta_dt = parse_period_string(fecha_hasta)
                if fecha_hasta_dt:
                    df = df[df['Date'] <= fecha_hasta_dt]
            
            # Seleccionar columna según métrica
            if metrica == 'var_trim':
                y_col = 'var_trim'
                y_title = 'Variación trimestral (%)'
            elif metrica == 'var_yoy':
                y_col = 'var_yoy'
                y_title = 'Variación interanual (%)'
            elif metrica == 'index':
                y_col = 'index_100'
                y_title = 'Índice base 100'
            else:
                y_col = 'Empleo'
                y_title = 'Empleo (puestos de trabajo)'
            
            # Línea principal
            fig.add_trace(go.Scatter(
                x=df['Date'],
                y=df[y_col] if y_col in df.columns else df['Empleo'],
                mode='lines+markers',
                name='Empleo total',
                line=dict(color=COLORS['primary'], width=2)
            ))
            
            # Promedio móvil si está activado
            if 'show' in promedio_movil and y_col in df.columns:
                df['MA4'] = df[y_col].rolling(window=4, min_periods=1).mean()
                fig.add_trace(go.Scatter(
                    x=df['Date'],
                    y=df['MA4'],
                    mode='lines',
                    name='Promedio móvil (4T)',
                    line=dict(color=COLORS['secondary'], width=2, dash='dash')
                ))
            
            fig.update_layout(
                title=f'Evolución temporal - {y_title}',
                xaxis_title='Período',
                yaxis_title=y_title,
                hovermode='x unified',
                showlegend=True
            )
    
    else:  # dataset == 'sectorial'
        if serie_base == 'desest':
            df_key = 'C2.2'
        else:
            df_key = 'C2.1'
        
        df = pd.DataFrame(data_dict.get(df_key, []))
        if not df.empty and sectores:
            df = process_periods(df)
            
            # Filtrar por fechas
            if fecha_desde and 'Date' in df.columns:
                fecha_desde_dt = parse_period_string(fecha_desde)
                if fecha_desde_dt:
                    df = df[df['Date'] >= fecha_desde_dt]
            
            if fecha_hasta and 'Date' in df.columns:
                fecha_hasta_dt = parse_period_string(fecha_hasta)
                if fecha_hasta_dt:
                    df = df[df['Date'] <= fecha_hasta_dt]
            
            for sector in sectores:
                if sector in df.columns:
                    # Calcular métrica para cada sector
                    if metrica == 'var_trim':
                        y_col = f'{sector}_var_trim'
                        df[y_col] = df[sector].pct_change() * 100
                    elif metrica == 'var_yoy':
                        y_col = f'{sector}_var_yoy'
                        df[y_col] = df[sector].pct_change(4) * 100
                    elif metrica == 'index':
                        y_col = f'{sector}_index'
                        if df[sector].iloc[0] != 0:
                            df[y_col] = (df[sector] / df[sector].iloc[0]) * 100
                    else:
                        y_col = sector
                    
                    fig.add_trace(go.Scatter(
                        x=df['Date'],
                        y=df[y_col] if y_col in df.columns else df[sector],
                        mode='lines+markers',
                        name=str(sector)
                    ))
            
            y_title = {
                'var_trim': 'Variación trimestral (%)',
                'var_yoy': 'Variación interanual (%)',
                'index': 'Índice base 100',
                'niveles': 'Empleo (puestos de trabajo)'
            }.get(metrica, 'Empleo')
            
            fig.update_layout(
                title=f'Evolución por sector - {y_title}',
                xaxis_title='Período',
                yaxis_title=y_title,
                hovermode='x unified',
                showlegend=True
            )
    
    return fig

# Callback para actualizar opciones de códigos sectoriales
@app.callback(
    Output('dd-codigos-sectorial', 'options'),
    [Input('dd-nivel-ciiu', 'value'),
     Input('store-data', 'data')]
)
def update_codigo_options(nivel_ciiu, data_dict):
    """Actualiza las opciones de códigos según el nivel CIIU seleccionado."""
    if not data_dict or not nivel_ciiu:
        return []
    
    # Obtener descriptores
    desc_data = data_dict.get('descriptores_CIIU', [])
    if not desc_data:
        return []
    
    desc_df = pd.DataFrame(desc_data)
    
    # Filtrar por tabla
    desc_filtered = desc_df[desc_df['Tabla'] == nivel_ciiu]
    
    # Crear opciones
    options = []
    for _, row in desc_filtered.iterrows():
        label = f"{row['Código']} - {row['Descripción'][:50]}..."
        options.append({'label': label, 'value': row['Código']})
    
    return options

# Callback para gráficos sectoriales
@app.callback(
    [Output('bars-ultimo', 'figure'),
     Output('ts-sector', 'figure'),
     Output('tbl-sector-container', 'children')],
    [Input('dd-nivel-ciiu', 'value'),
     Input('dd-codigos-sectorial', 'value'),
     Input('check-top-n', 'value'),
     Input('store-data', 'data')]
)
def update_sectorial_charts(nivel_ciiu, codigos, top_n, data_dict):
    """Actualiza los gráficos y tabla del análisis sectorial."""
    if not data_dict or not nivel_ciiu:
        fig_vacio = go.Figure()
        fig_vacio.add_annotation(
            text="Seleccione un nivel CIIU para visualizar datos",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=14, color="gray")
        )
        return fig_vacio, fig_vacio, html.Div("Seleccione parámetros", className="alert alert-info")
    
    # Obtener datos
    df = pd.DataFrame(data_dict.get(nivel_ciiu, []))
    if df.empty:
        fig_vacio = go.Figure()
        fig_vacio.add_annotation(
            text=f"No hay datos disponibles para {nivel_ciiu}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=14, color="red")
        )
        return fig_vacio, fig_vacio, html.Div(
            f"No se encontraron datos para el nivel {nivel_ciiu}", 
            className="alert alert-warning"
        )
    
    # Procesar períodos
    if 'Período' in df.columns:
        df = process_periods(df)
    
    # Filtrar por códigos si se especifican
    if codigos:
        df_filtrado = df[df['Sector'].isin(codigos)]
        if df_filtrado.empty:
            # Obtener descriptores para mostrar nombres
            desc_data = data_dict.get('descriptores_CIIU', [])
            desc_df = pd.DataFrame(desc_data)
            desc_filtered = desc_df[(desc_df['Tabla'] == nivel_ciiu) & (desc_df['Código'].isin(codigos))]
            
            nombres = ", ".join([f"{row['Código']} ({row['Descripción'][:30]}...)" 
                                for _, row in desc_filtered.iterrows()])
            
            fig_vacio = go.Figure()
            fig_vacio.add_annotation(
                text=f"No hay datos históricos para: {nombres if nombres else ', '.join(codigos)}",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=12, color="orange"),
                wrap=True
            )
            mensaje = html.Div([
                html.H6("⚠️ No hay datos disponibles", className="text-warning"),
                html.P(f"Los códigos seleccionados ({', '.join(codigos)}) no tienen datos históricos en {nivel_ciiu}."),
                html.Small("Esto puede deberse a:"),
                html.Ul([
                    html.Li("Son actividades nuevas sin histórico"),
                    html.Li("No tienen empleo registrado significativo"),
                    html.Li("Están agrupados en otras categorías")
                ])
            ], className="alert alert-warning")
            return fig_vacio, fig_vacio, mensaje
        df = df_filtrado
    elif top_n and 'show' in top_n:
        # Tomar top 10 por último período
        ultimo_periodo = df['Período'].max()
        df_ultimo = df[df['Período'] == ultimo_periodo].nlargest(10, 'Empleo')
        sectores_top = df_ultimo['Sector'].tolist()
        df = df[df['Sector'].isin(sectores_top)]
    
    # Verificar que hay datos después del filtrado
    if df.empty:
        fig_vacio = go.Figure()
        fig_vacio.add_annotation(
            text="No hay datos para mostrar con los filtros seleccionados",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=14, color="gray")
        )
        return fig_vacio, fig_vacio, html.Div(
            "No hay datos con los parámetros seleccionados", 
            className="alert alert-info"
        )
    
    # Gráfico de barras del último período
    ultimo_periodo = df['Período'].max()
    df_ultimo = df[df['Período'] == ultimo_periodo].sort_values('Empleo', ascending=True)
    
    fig_bars = px.bar(
        df_ultimo,
        x='Empleo',
        y='Sector',
        orientation='h',
        title=f'Empleo por sector - {ultimo_periodo}',
        color='Empleo',
        color_continuous_scale='Blues'
    )
    
    # Serie temporal
    fig_ts = go.Figure()
    for sector in df['Sector'].unique()[:10]:  # Máximo 10 series
        df_sector = df[df['Sector'] == sector]
        fig_ts.add_trace(go.Scatter(
            x=df_sector['Date'] if 'Date' in df_sector.columns else df_sector['Período'],
            y=df_sector['Empleo'],
            mode='lines+markers',
            name=str(sector)
        ))
    
    fig_ts.update_layout(
        title='Evolución temporal por sector',
        xaxis_title='Período',
        yaxis_title='Empleo',
        hovermode='x unified'
    )
    
    # Obtener descriptores para la tabla
    desc_data = data_dict.get('descriptores_CIIU', [])
    desc_df = pd.DataFrame(desc_data)
    desc_dict = {}
    if not desc_df.empty:
        desc_filtered = desc_df[desc_df['Tabla'] == nivel_ciiu]
        # Convertir ambos a string para asegurar coincidencia
        desc_dict = {}
        for _, row in desc_filtered.iterrows():
            # Manejar códigos numéricos y string
            codigo_str = str(row['Código']).strip()
            # Para C4, C6, C7 los códigos pueden ser numéricos, convertir a int y luego a string sin decimales
            try:
                if nivel_ciiu in ['C4', 'C6', 'C7']:
                    codigo_str = str(int(float(codigo_str)))
            except:
                pass
            desc_dict[codigo_str] = row['Descripción']
    
    # Enriquecer datos con descripciones
    df_ultimo_enriquecido = df_ultimo.copy()
    df_ultimo_enriquecido['Descripción'] = df_ultimo_enriquecido['Sector'].apply(
        lambda x: (lambda desc: desc[:50] + '...' if len(desc) > 50 else desc)(
            desc_dict.get(str(x).strip(), desc_dict.get(str(int(float(x))) if str(x).replace('.','').isdigit() else x, 'Sin descripción disponible'))
        )
    )
    
    # Tabla resumen
    tabla_container = html.Div([
        html.H5(f"Detalle {nivel_ciiu} - {ultimo_periodo}", className="mb-3"),
        html.Small(f"Mostrando {len(df_ultimo)} sectores", className="text-muted mb-2 d-block"),
        dash_table.DataTable(
            data=df_ultimo_enriquecido.to_dict('records'),
            columns=[
                {'name': 'Código', 'id': 'Sector'},
                {'name': 'Descripción', 'id': 'Descripción'},
                {'name': 'Empleo', 'id': 'Empleo', 'type': 'numeric', 'format': {'specifier': ',.0f'}}
            ],
            style_cell={'textAlign': 'left'},
            style_data_conditional=[
                {
                    'if': {'row_index': 0},
                    'backgroundColor': COLORS['success'],
                    'color': 'white',
                }
            ],
            sort_action="native",
            page_size=15
        ),
        html.Div([
            html.Hr(),
            html.Small([
                html.Strong("Nota: "),
                "Algunos códigos CIIU pueden no tener datos históricos disponibles. ",
                "Esto es normal para actividades económicas nuevas, de baja representatividad, ",
                "o que están agrupadas en categorías más generales."
            ], className="text-muted")
        ], className="mt-3")
    ])
    
    return fig_bars, fig_ts, tabla_container

# Callback para gráficos de tamaño (C5)
@app.callback(
    [Output('stack-c5', 'figure'),
     Output('ts-c5', 'figure'),
     Output('tbl-c5-container', 'children')],
    [Input('dd-sector-c5', 'value'),
     Input('check-tamaño-c5', 'value'),
     Input('store-data', 'data')]
)
def update_tamaño_charts(sector, tamaños, data_dict):
    """Actualiza los gráficos de análisis por tamaño."""
    if not data_dict or not sector or not tamaños:
        return go.Figure(), go.Figure(), html.Div()
    
    # Obtener datos C5
    df = pd.DataFrame(data_dict.get('C5', []))
    if df.empty:
        return go.Figure(), go.Figure(), html.Div()
    
    # Procesar períodos
    if 'Período' in df.columns:
        df = process_periods(df)
    
    # Filtrar por sector y tamaños
    sector_ids = [f"{sector}_{t}" for t in tamaños]
    sector_ids.append(sector)  # Incluir total del sector
    df_filtered = df[df['Sector'].isin(sector_ids)]
    
    # Preparar datos para gráfico apilado
    df_pivot = df_filtered.pivot_table(
        index='Período',
        columns='Sector',
        values='Empleo',
        aggfunc='sum'
    )
    
    # Gráfico de área apilada
    fig_stack = go.Figure()
    for col in df_pivot.columns:
        if col != sector:  # No incluir el total
            fig_stack.add_trace(go.Scatter(
                x=df_pivot.index,
                y=df_pivot[col],
                mode='lines',
                stackgroup='one',
                name=str(col.split('_')[1] if '_' in col else col)
            ))
    
    fig_stack.update_layout(
        title=f'Composición por tamaño - {sector}',
        xaxis_title='Período',
        yaxis_title='Empleo',
        hovermode='x unified'
    )
    
    # Serie temporal por tamaño
    fig_ts = go.Figure()
    for tamaño in tamaños:
        sector_id = f"{sector}_{tamaño}"
        df_tamaño = df_filtered[df_filtered['Sector'] == sector_id]
        if not df_tamaño.empty:
            fig_ts.add_trace(go.Scatter(
                x=df_tamaño['Date'] if 'Date' in df_tamaño.columns else df_tamaño['Período'],
                y=df_tamaño['Empleo'],
                mode='lines+markers',
                name=str(tamaño)
            ))
    
    fig_ts.update_layout(
        title=f'Evolución por tamaño - {sector}',
        xaxis_title='Período',
        yaxis_title='Empleo',
        hovermode='x unified'
    )
    
    # Tabla resumen
    ultimo_periodo = df_filtered['Período'].max()
    df_tabla = df_filtered[df_filtered['Período'] == ultimo_periodo][['Sector', 'Empleo']]
    
    tabla = dash_table.DataTable(
        data=df_tabla.to_dict('records'),
        columns=[
            {'name': 'Categoría', 'id': 'Sector'},
            {'name': 'Empleo', 'id': 'Empleo', 'type': 'numeric', 'format': {'specifier': ',.0f'}}
        ],
        style_cell={'textAlign': 'left'},
        page_size=10
    )
    
    return fig_stack, fig_ts, tabla

# Callback para comparaciones
@app.callback(
    Output('div-comparacion-results', 'children'),
    [Input('dd-periodo-a', 'value'),
     Input('dd-periodo-b', 'value'),
     Input('rb-tipo-comparacion', 'value'),
     Input('store-data', 'data')]
)
def update_comparaciones(periodo_a, periodo_b, tipo, data_dict):
    """Actualiza los resultados de comparación entre períodos."""
    if not data_dict or not periodo_a or not periodo_b:
        return html.Div("Seleccione dos períodos para comparar", className="alert alert-info")
    
    # Obtener datos C3 para comparación sectorial
    df = pd.DataFrame(data_dict.get('C3', []))
    if df.empty:
        return html.Div("No hay datos disponibles", className="alert alert-warning")
    
    # Filtrar por períodos
    df_a = df[df['Período'] == periodo_a]
    df_b = df[df['Período'] == periodo_b]
    
    if df_a.empty or df_b.empty:
        return html.Div("Uno de los períodos no tiene datos", className="alert alert-warning")
    
    # Hacer merge
    df_comp = pd.merge(
        df_a[['Sector', 'Empleo']],
        df_b[['Sector', 'Empleo']],
        on='Sector',
        suffixes=('_A', '_B')
    )
    
    # Calcular diferencias
    if tipo == 'abs':
        df_comp['Diferencia'] = df_comp['Empleo_A'] - df_comp['Empleo_B']
        title = 'Diferencia absoluta'
    elif tipo == 'pct':
        df_comp['Diferencia'] = ((df_comp['Empleo_A'] - df_comp['Empleo_B']) / df_comp['Empleo_B']) * 100
        title = 'Diferencia porcentual'
    else:  # ratio
        df_comp['Diferencia'] = df_comp['Empleo_A'] / df_comp['Empleo_B']
        title = 'Ratio A/B'
    
    # Gráfico de comparación
    fig = px.bar(
        df_comp.sort_values('Diferencia'),
        x='Diferencia',
        y='Sector',
        orientation='h',
        title=f'{title}: {periodo_a} vs {periodo_b}',
        color='Diferencia',
        color_continuous_scale='RdBu_r',
        color_continuous_midpoint=0
    )
    
    # Tabla resumen
    tabla = dash_table.DataTable(
        data=df_comp.to_dict('records'),
        columns=[
            {'name': 'Sector', 'id': 'Sector'},
            {'name': periodo_a, 'id': 'Empleo_A', 'type': 'numeric', 'format': {'specifier': ',.0f'}},
            {'name': periodo_b, 'id': 'Empleo_B', 'type': 'numeric', 'format': {'specifier': ',.0f'}},
            {'name': title, 'id': 'Diferencia', 'type': 'numeric', 
             'format': {'specifier': ',.2f' if tipo == 'pct' else ',.0f'}}
        ],
        style_cell={'textAlign': 'left'},
        style_data_conditional=[
            {
                'if': {
                    'filter_query': '{Diferencia} > 0',
                    'column_id': 'Diferencia'
                },
                'backgroundColor': COLORS['success'],
                'color': 'white',
            },
            {
                'if': {
                    'filter_query': '{Diferencia} < 0',
                    'column_id': 'Diferencia'
                },
                'backgroundColor': COLORS['danger'],
                'color': 'white',
            }
        ],
        page_size=15
    )
    
    return html.Div([
        dcc.Graph(figure=fig),
        html.Hr(),
        html.H5("Tabla de comparación"),
        tabla
    ])

# Callback para alertas
@app.callback(
    [Output('div-alertas-results', 'children'),
     Output('div-periodo-alertas', 'children')],
    [Input('btn-run-alertas', 'n_clicks'),
     Input('store-alertas-init', 'data'),
     Input('check-auto-alertas', 'value'),
     Input('input-umbral-trim', 'value'),
     Input('input-umbral-yoy', 'value'),
     Input('store-data', 'data'),
     Input('dd-fecha-desde', 'value'),
     Input('dd-fecha-hasta', 'value')]
)
def run_alertas(n_clicks, init_data, auto_alertas, umbral_trim, umbral_yoy, data_dict, fecha_desde, fecha_hasta):
    """Ejecuta el análisis de alertas y anomalías."""
    # Ejecutar automáticamente si está activado o si se presiona el botón
    if not data_dict:
        return html.Div("Cargando datos...", className="alert alert-info"), ""
    
    if not auto_alertas and not n_clicks:
        return (html.Div("Active las alertas automáticas o presione 'Actualizar análisis'", 
                       className="alert alert-info"), "")
    
    alertas = []
    
    # Cargar descriptores para obtener nombres de sectores
    descriptores = pd.DataFrame(data_dict.get('descriptores_CIIU', []))
    sector_desc = {}
    if not descriptores.empty:
        desc_c3 = descriptores[descriptores['Tabla'] == 'C3']
        sector_desc = dict(zip(desc_c3['Código'], desc_c3['Descripción']))
    
    # Analizar C1.1 para alertas generales
    df = pd.DataFrame(data_dict.get('C1.1', []))
    if not df.empty:
        df = process_periods(df)
        df = calculate_variations(df)
        
        # Aplicar filtro de fechas si están especificadas
        if fecha_desde and fecha_hasta:
            fecha_desde_ts = parse_period_string(fecha_desde)
            fecha_hasta_ts = parse_period_string(fecha_hasta)
            if fecha_desde_ts and fecha_hasta_ts:
                df = df[(df['Date'] >= fecha_desde_ts) & (df['Date'] <= fecha_hasta_ts)]
        
        # Análisis del período seleccionado (último del rango o último disponible)
        if len(df) > 0:
            ultimo = df.iloc[-1]
            penultimo = df.iloc[-2] if len(df) > 1 else None
            
            # Información del período analizado
            periodo_info = f"Analizando: {ultimo['Período']}" if 'Período' in ultimo else "Período actual"
            
            # ALERTAS CRÍTICAS (Rojas)
            if 'var_trim' in ultimo and pd.notna(ultimo['var_trim']):
                if ultimo['var_trim'] < -5:
                    alertas.append({
                        'tipo': 'danger',
                        'titulo': '🔴 ALERTA CRÍTICA: Caída trimestral severa',
                        'mensaje': f"Caída del empleo de {ultimo['var_trim']:.2f}% en {ultimo['Período']}",
                        'prioridad': 1
                    })
            
            if 'var_yoy' in ultimo and pd.notna(ultimo['var_yoy']):
                if ultimo['var_yoy'] < -10:
                    alertas.append({
                        'tipo': 'danger',
                        'titulo': '🔴 ALERTA CRÍTICA: Caída interanual severa',
                        'mensaje': f"Caída interanual del empleo de {ultimo['var_yoy']:.2f}% en {ultimo['Período']}",
                        'prioridad': 1
                    })
            
            # Pérdida absoluta de empleos
            if penultimo is not None and 'Empleo' in ultimo and 'Empleo' in penultimo:
                perdida = ultimo['Empleo'] - penultimo['Empleo']
                if perdida < -50000:
                    alertas.append({
                        'tipo': 'danger',
                        'titulo': '🔴 ALERTA CRÍTICA: Pérdida masiva de empleos',
                        'mensaje': f"Pérdida de {abs(perdida):,.0f} empleos en {ultimo['Período']}",
                        'prioridad': 1
                    })
            
            # ALERTAS DE ADVERTENCIA (Amarillas)
            if 'var_trim' in ultimo and pd.notna(ultimo['var_trim']):
                if 3 <= abs(ultimo['var_trim']) <= 5:
                    alertas.append({
                        'tipo': 'warning',
                        'titulo': '🟡 Advertencia: Variación trimestral significativa',
                        'mensaje': f"Variación de {ultimo['var_trim']:.2f}% en {ultimo['Período']}",
                        'prioridad': 2
                    })
            
            if 'var_yoy' in ultimo and pd.notna(ultimo['var_yoy']):
                if 5 <= abs(ultimo['var_yoy']) <= 10:
                    alertas.append({
                        'tipo': 'warning',
                        'titulo': '🟡 Advertencia: Variación interanual notable',
                        'mensaje': f"Variación interanual de {ultimo['var_yoy']:.2f}% en {ultimo['Período']}",
                        'prioridad': 2
                    })
            
            # Cambio de tendencia
            if penultimo is not None and 'var_trim' in ultimo and 'var_trim' in penultimo:
                if pd.notna(ultimo['var_trim']) and pd.notna(penultimo['var_trim']):
                    if (ultimo['var_trim'] > 0 and penultimo['var_trim'] < 0) or \
                       (ultimo['var_trim'] < 0 and penultimo['var_trim'] > 0):
                        alertas.append({
                            'tipo': 'warning',
                            'titulo': '🟡 Advertencia: Cambio de tendencia',
                            'mensaje': f"La tendencia cambió de {penultimo['var_trim']:.1f}% a {ultimo['var_trim']:.1f}%",
                            'prioridad': 2
                        })
            
            # ALERTAS POSITIVAS (Verdes)
            if 'var_trim' in ultimo and pd.notna(ultimo['var_trim']):
                if ultimo['var_trim'] > 3:
                    alertas.append({
                        'tipo': 'success',
                        'titulo': '🟢 Crecimiento trimestral robusto',
                        'mensaje': f"Crecimiento del empleo de {ultimo['var_trim']:.2f}% en {ultimo['Período']}",
                        'prioridad': 3
                    })
            
            if 'var_yoy' in ultimo and pd.notna(ultimo['var_yoy']):
                if ultimo['var_yoy'] > 5:
                    alertas.append({
                        'tipo': 'success',
                        'titulo': '🟢 Crecimiento interanual sólido',
                        'mensaje': f"Crecimiento interanual de {ultimo['var_yoy']:.2f}% en {ultimo['Período']}",
                        'prioridad': 3
                    })
            
            # Creación de empleos
            if penultimo is not None and 'Empleo' in ultimo and 'Empleo' in penultimo:
                creacion = ultimo['Empleo'] - penultimo['Empleo']
                if creacion > 30000:
                    alertas.append({
                        'tipo': 'success',
                        'titulo': '🟢 Creación significativa de empleos',
                        'mensaje': f"Creación de {creacion:,.0f} nuevos empleos en {ultimo['Período']}",
                        'prioridad': 3
                    })
            
            # ALERTAS INFORMATIVAS (Azules)
            # Verificar máximo histórico
            if 'Empleo' in df.columns:
                if ultimo['Empleo'] == df['Empleo'].max():
                    alertas.append({
                        'tipo': 'info',
                        'titulo': '🔵 Nuevo máximo histórico',
                        'mensaje': f"El empleo alcanzó un máximo histórico: {ultimo['Empleo']:,.0f} trabajadores",
                        'prioridad': 4
                    })
    
    # Analizar C3 para alertas sectoriales
    df_c3 = pd.DataFrame(data_dict.get('C3', []))
    if not df_c3.empty:
        df_c3 = process_periods(df_c3)
        
        # Aplicar filtro de fechas si están especificadas
        if fecha_desde and fecha_hasta:
            fecha_desde_ts = parse_period_string(fecha_desde)
            fecha_hasta_ts = parse_period_string(fecha_hasta)
            if fecha_desde_ts and fecha_hasta_ts:
                df_c3 = df_c3[(df_c3['Date'] >= fecha_desde_ts) & (df_c3['Date'] <= fecha_hasta_ts)]
        
        # Verificar que hay datos después del filtro
        if df_c3.empty:
            return (html.Div("No hay datos en el período seleccionado", className="alert alert-warning"), 
                   periodo_texto if 'periodo_texto' in locals() else "")
        
        # Obtener último período disponible en el rango filtrado
        ultimo_periodo = df_c3['Date'].max()
        penultimo_periodo = df_c3[df_c3['Date'] < ultimo_periodo]['Date'].max() if len(df_c3['Date'].unique()) > 1 else None
        mismo_periodo_anio_anterior = ultimo_periodo - pd.DateOffset(years=1)
        
        # Calcular variaciones por sector
        sectores_criticos = []
        for sector in df_c3['Sector'].unique():
            df_sector = df_c3[df_c3['Sector'] == sector].sort_values('Date')
            
            if len(df_sector) > 1:
                # Variación trimestral
                ultimo_val = df_sector[df_sector['Date'] == ultimo_periodo]['Empleo'].values
                penultimo_val = df_sector[df_sector['Date'] == penultimo_periodo]['Empleo'].values if penultimo_periodo is not None else []
                
                if len(ultimo_val) > 0 and len(penultimo_val) > 0:
                    var_trim = ((ultimo_val[0] - penultimo_val[0]) / penultimo_val[0]) * 100
                    
                    # Obtener descripción del sector
                    desc_sector = sector_desc.get(sector, f"Sector {sector}")
                    
                    # Variación interanual
                    anio_anterior_val = df_sector[df_sector['Date'] == mismo_periodo_anio_anterior]['Empleo'].values
                    var_yoy = None
                    if len(anio_anterior_val) > 0:
                        var_yoy = ((ultimo_val[0] - anio_anterior_val[0]) / anio_anterior_val[0]) * 100
                    
                    # Obtener el período actual para mostrar en las alertas
                    periodo_actual = df_sector[df_sector['Date'] == ultimo_periodo]['Período'].values
                    periodo_str = periodo_actual[0] if len(periodo_actual) > 0 else "Período actual"
                    
                    # Alertas sectoriales críticas
                    if var_yoy is not None and var_yoy < -15:
                        sectores_criticos.append(desc_sector)
                        alertas.append({
                            'tipo': 'danger',
                            'titulo': f'🔴 Sector en crisis: {sector}',
                            'mensaje': f"{desc_sector}: Caída interanual de {var_yoy:.1f}% en {periodo_str}",
                            'prioridad': 1
                        })
                    elif abs(var_trim) > umbral_trim:
                        # Solo alertar si la variación es significativa y no es un error de datos
                        if pd.notna(var_trim) and ultimo_val[0] > 0 and penultimo_val[0] > 0:
                            tipo = 'warning' if var_trim < 0 else 'info'
                            simbolo = '📉' if var_trim < 0 else '📈'
                            alertas.append({
                                'tipo': tipo,
                                'titulo': f'{simbolo} {sector}: {desc_sector[:30]}...' if len(desc_sector) > 30 else f'{simbolo} {sector}: {desc_sector}',
                                'mensaje': f"Variación trimestral de {var_trim:.2f}% en {periodo_str}",
                                'prioridad': 3 if var_trim > 0 else 2
                            })
        
        # Alerta consolidada si hay múltiples sectores en crisis
        if len(sectores_criticos) > 3:
            alertas.append({
                'tipo': 'danger',
                'titulo': '🔴 ALERTA: Crisis sectorial generalizada',
                'mensaje': f"{len(sectores_criticos)} sectores con caídas superiores al 15% interanual",
                'prioridad': 1
            })
    
    # Ordenar alertas por prioridad
    alertas.sort(key=lambda x: x.get('prioridad', 5))
    
    # Preparar información del período
    if fecha_desde and fecha_hasta:
        periodo_texto = html.Div([
            html.Strong("📅 Período analizado: "),
            f"{fecha_desde} hasta {fecha_hasta}",
            html.Br(),
            html.Small(f"Último período con datos: {periodo_info if 'periodo_info' in locals() else 'N/D'}", 
                      className="text-muted")
        ])
    else:
        periodo_texto = html.Div([
            html.Strong("📅 Analizando todos los períodos disponibles"),
            html.Br(),
            html.Small(f"Último período: {periodo_info if 'periodo_info' in locals() else 'N/D'}", 
                      className="text-muted")
        ])
    
    # Renderizar alertas
    if not alertas:
        return (html.Div([
            html.H4("✅ Estado del Sistema", className="text-success mb-3"),
            html.P("No se detectaron alertas significativas con los umbrales configurados."),
            html.P(f"Umbrales actuales: Trimestral {umbral_trim}% | Interanual {umbral_yoy}%", 
                  className="text-muted small")
        ], className="alert alert-success"), periodo_texto)
    
    # Agrupar alertas por tipo
    alertas_por_tipo = {
        'danger': [],
        'warning': [],
        'success': [],
        'info': []
    }
    
    for alerta in alertas:
        tipo = alerta.get('tipo', 'info')
        if tipo in alertas_por_tipo:
            alertas_por_tipo[tipo].append(alerta)
    
    # Construir la visualización
    cards = []
    
    # Resumen general
    n_criticas = len(alertas_por_tipo['danger'])
    n_advertencias = len(alertas_por_tipo['warning'])
    n_positivas = len(alertas_por_tipo['success'])
    n_info = len(alertas_por_tipo['info'])
    
    resumen = html.Div([
        html.H4("📊 Resumen de Alertas", className="mb-3"),
        html.Div([
            html.Span(f"🔴 Críticas: {n_criticas}", className="badge bg-danger me-2"),
            html.Span(f"🟡 Advertencias: {n_advertencias}", className="badge bg-warning text-dark me-2"),
            html.Span(f"🟢 Positivas: {n_positivas}", className="badge bg-success me-2"),
            html.Span(f"🔵 Informativas: {n_info}", className="badge bg-info me-2"),
        ], className="mb-3")
    ], className="alert alert-light border mb-4")
    
    cards.append(resumen)
    
    # Mostrar alertas por categoría (máximo 15 alertas en total)
    contador = 0
    max_alertas = 15
    
    for tipo in ['danger', 'warning', 'success', 'info']:
        if contador >= max_alertas:
            break
            
        for alerta in alertas_por_tipo[tipo]:
            if contador >= max_alertas:
                break
                
            cards.append(
                html.Div([
                    html.H6(alerta['titulo'], className="mb-2 fw-bold"),
                    html.P(alerta['mensaje'], className="mb-0")
                ], className=f"alert alert-{tipo} mb-2")
            )
            contador += 1
    
    # Agregar nota si hay más alertas
    if len(alertas) > max_alertas:
        cards.append(
            html.Div(
                f"... y {len(alertas) - max_alertas} alertas adicionales",
                className="text-muted text-center mt-2"
            )
        )
    
    return html.Div(cards), periodo_texto

# Callback para tabla de datos crudos
@app.callback(
    Output('div-raw-table', 'children'),
    [Input('dd-dataset-raw', 'value'),
     Input('store-data', 'data')]
)
def update_raw_table(dataset, data_dict):
    """Actualiza la tabla de datos crudos."""
    if not data_dict or not dataset:
        return html.Div("Seleccione un dataset", className="alert alert-info")
    
    df = pd.DataFrame(data_dict.get(dataset, []))
    if df.empty:
        return html.Div("No hay datos disponibles", className="alert alert-warning")
    
    # Limitar a 1000 filas para performance
    if len(df) > 1000:
        df = df.head(1000)
        mensaje = f"Mostrando primeras 1000 filas de {len(data_dict.get(dataset, []))} totales"
    else:
        mensaje = f"Mostrando {len(df)} filas"
    
    # Crear tabla
    columns = []
    for col in df.columns:
        col_config = {'name': col, 'id': col}
        if df[col].dtype in ['float64', 'int64']:
            col_config['type'] = 'numeric'
            col_config['format'] = {'specifier': ',.0f'}
        columns.append(col_config)
    
    tabla = dash_table.DataTable(
        data=df.to_dict('records'),
        columns=columns,
        style_cell={'textAlign': 'left'},
        filter_action="native",
        sort_action="native",
        page_action="native",
        page_current=0,
        page_size=20,
        export_format="csv"
    )
    
    return html.Div([
        html.P(mensaje, className="text-muted"),
        tabla
    ])

# =====================================================================
# EJECUCIÓN
# =====================================================================

# Configurar el servidor para producción
server = app.server

if __name__ == '__main__':
    logger.info("Iniciando Dashboard V1...")
    logger.info(f"Directorio de datos: {DATA_DIR}")
    
    # Verificar que existan los archivos necesarios
    required_files = ['C1.1.csv', 'C1.2.csv', 'descriptores_CIIU.csv']
    missing_files = []
    
    for file in required_files:
        file_path = os.path.join(DATA_DIR, file)
        if not os.path.exists(file_path):
            missing_files.append(file)
    
    if missing_files:
        logger.error(f"Archivos faltantes: {missing_files}")
        logger.error("Ejecute preprocesamiento.py primero")
    else:
        logger.info("Todos los archivos requeridos encontrados")
        # Detectar si estamos en producción o desarrollo
        import sys
        # Por defecto en modo debug para desarrollo local
        debug_mode = True
        # Solo desactivar debug si explícitamente se pide producción
        if '--production' in sys.argv:
            debug_mode = False
        
        port = int(os.environ.get('PORT', 8050))
        host = '127.0.0.1' if debug_mode else '0.0.0.0'
        
        logger.info(f"Dashboard disponible en: http://{host}:{port}")
        app.run(debug=debug_mode, host=host, port=port)