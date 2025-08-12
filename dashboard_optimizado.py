"""
Dashboard Optimizado con Caché y Pre-carga de Datos
Versión de alto rendimiento del visualizador
"""
import dash
from dash import dcc, html, Input, Output, State, callback_context, dash_table
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from functools import lru_cache
import time
import warnings
warnings.filterwarnings('ignore')

# ========================
# CONFIGURACIÓN Y CACHÉ
# ========================

# Cache global para datos
CACHE = {}
LAST_LOAD_TIME = None
CACHE_DURATION = 3600  # 1 hora en segundos

# Pre-cargar todos los datos al inicio
def cargar_datos_inicial():
    """Carga inicial de todos los datos en memoria"""
    global CACHE, LAST_LOAD_TIME
    
    print("Cargando datos en memoria...")
    inicio = time.time()
    
    try:
        # Intentar cargar desde Parquet (más rápido)
        CACHE['datos'] = pd.read_parquet('datos_empleo.parquet')
        print(f"  Datos cargados desde Parquet en {time.time()-inicio:.2f}s")
    except:
        # Si no existe Parquet, procesar desde Excel
        print("  Parquet no encontrado, procesando desde Excel...")
        CACHE['datos'] = procesar_datos_excel()
        # Guardar en Parquet para próximas veces
        CACHE['datos'].to_parquet('datos_empleo.parquet', engine='pyarrow', compression='snappy')
    
    # Pre-calcular agregaciones comunes
    pre_calcular_agregaciones()
    
    LAST_LOAD_TIME = time.time()
    print(f"Datos cargados en {time.time()-inicio:.2f} segundos")
    print(f"Total registros en memoria: {len(CACHE['datos']):,}")

def procesar_datos_excel():
    """Procesa el archivo Excel y retorna DataFrame"""
    # Cargar todas las hojas necesarias
    excel_file = 'nacional_serie_empleo_trimestral_actualizado241312.xlsx'
    
    # Leer C1.1
    df_c11 = pd.read_excel(excel_file, sheet_name='C1.1', header=None)
    
    # Procesar estructura horizontal
    records = []
    
    # Encontrar fila con fechas
    fecha_row = 5  # Basado en tu estructura actual
    
    # Extraer fechas desde las columnas
    fechas = []
    for col in range(1, df_c11.shape[1]):
        cell_val = str(df_c11.iloc[fecha_row, col])
        if 'Trim' in cell_val:
            parts = cell_val.split()
            quarter = int(parts[0][0])
            year = int(parts[-1])
            fecha = pd.Timestamp(year=year, month=(quarter-1)*3 + 1, day=1)
            fechas.append(fecha)
    
    # Procesar datos
    for row_idx in range(fecha_row + 1, len(df_c11)):
        codigo = df_c11.iloc[row_idx, 0]
        if pd.isna(codigo):
            continue
            
        codigo = str(codigo).strip()
        
        for col_idx, fecha in enumerate(fechas, start=1):
            if col_idx < df_c11.shape[1]:
                valor = df_c11.iloc[row_idx, col_idx]
                if pd.notna(valor):
                    try:
                        records.append({
                            'fecha': fecha,
                            'trimestre': f"{fecha.year}-T{fecha.quarter}",
                            'año': fecha.year,
                            'codigo': codigo,
                            'valor': float(valor)
                        })
                    except:
                        pass
    
    # Leer descriptores
    df_desc = pd.read_excel(excel_file, sheet_name='Descriptores de actividad', header=None)
    desc_dict = {}
    for idx in range(1, len(df_desc)):
        if pd.notna(df_desc.iloc[idx, 0]):
            desc_dict[str(df_desc.iloc[idx, 0]).strip()] = str(df_desc.iloc[idx, 1])
    
    # Crear DataFrame y agregar descripciones
    df = pd.DataFrame(records)
    df['descripcion'] = df['codigo'].map(desc_dict).fillna('')
    df['nivel'] = df['codigo'].apply(lambda x: len(str(x)))
    
    return df

def pre_calcular_agregaciones():
    """Pre-calcula agregaciones comunes para acelerar consultas"""
    global CACHE
    
    df = CACHE['datos']
    
    # Total nacional por fecha
    CACHE['total_nacional'] = df[df['codigo'] == 'Total'].groupby('fecha')['valor'].sum().to_dict()
    
    # Sectores únicos
    CACHE['sectores'] = df[df['nivel'] == 1]['codigo'].unique().tolist()
    
    # Estadísticas por código
    CACHE['stats_codigo'] = df.groupby('codigo').agg({
        'valor': ['mean', 'std', 'min', 'max'],
        'descripcion': 'first'
    }).to_dict()
    
    # Serie temporal por sector (nivel 1)
    sectores_df = df[df['nivel'] == 1]
    CACHE['serie_sectores'] = sectores_df.pivot_table(
        index='fecha', 
        columns='codigo', 
        values='valor', 
        aggfunc='sum'
    ).to_dict()
    
    # Últimos valores para alertas
    ultima_fecha = df['fecha'].max()
    CACHE['ultimos_valores'] = df[df['fecha'] == ultima_fecha].set_index('codigo')['valor'].to_dict()
    
    # Cambios porcentuales pre-calculados
    calcular_cambios_porcentuales()

def calcular_cambios_porcentuales():
    """Pre-calcula cambios porcentuales para alertas"""
    global CACHE
    df = CACHE['datos']
    
    cambios = {}
    for codigo in df['codigo'].unique():
        serie = df[df['codigo'] == codigo].sort_values('fecha')
        if len(serie) >= 2:
            ultimo = serie.iloc[-1]['valor']
            anterior = serie.iloc[-2]['valor']
            if anterior != 0:
                cambio = ((ultimo - anterior) / anterior) * 100
                cambios[codigo] = cambio
    
    CACHE['cambios_porcentuales'] = cambios

@lru_cache(maxsize=128)
def obtener_datos_filtrados(fecha_inicio, fecha_fin, codigos=None):
    """Obtiene datos filtrados con caché LRU"""
    df = CACHE['datos']
    
    # Convertir fechas
    fecha_inicio = pd.to_datetime(fecha_inicio)
    fecha_fin = pd.to_datetime(fecha_fin)
    
    # Filtrar por fechas
    mask = (df['fecha'] >= fecha_inicio) & (df['fecha'] <= fecha_fin)
    df_filtrado = df[mask]
    
    # Filtrar por códigos si se especifican
    if codigos:
        df_filtrado = df_filtrado[df_filtrado['codigo'].isin(codigos)]
    
    return df_filtrado

# ========================
# INICIALIZACIÓN DE DASH
# ========================

app = dash.Dash(__name__, 
    external_stylesheets=['https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css'],
    suppress_callback_exceptions=True
)

# Para producción
server = app.server

# Cargar datos al inicio
cargar_datos_inicial()

# ========================
# LAYOUT
# ========================

def crear_layout():
    """Crea el layout del dashboard"""
    
    # Obtener rango de fechas
    fecha_min = CACHE['datos']['fecha'].min()
    fecha_max = CACHE['datos']['fecha'].max()
    
    return html.Div([
        # Header
        html.Div([
            html.H1("📊 Visualizador de Empleo - Argentina (Optimizado)", 
                   className="text-center text-white mb-0"),
            html.P(f"Datos: {fecha_min.strftime('%Y')} - {fecha_max.strftime('%Y')} | "
                  f"{len(CACHE['datos']):,} registros en memoria", 
                  className="text-center text-white-50")
        ], className="bg-primary py-3"),
        
        # Controles globales
        html.Div([
            html.Div([
                html.Label("Período de análisis:", className="fw-bold"),
                dcc.RangeSlider(
                    id='rango-fechas',
                    min=fecha_min.year,
                    max=fecha_max.year,
                    value=[fecha_max.year - 5, fecha_max.year],
                    marks={year: str(year) for year in range(fecha_min.year, fecha_max.year + 1, 5)},
                    tooltip={"placement": "bottom", "always_visible": False}
                )
            ], className="col-12")
        ], className="container mt-3"),
        
        # Tabs
        dcc.Tabs(id="tabs-main", value='vista-general', children=[
            dcc.Tab(label='Vista General', value='vista-general'),
            dcc.Tab(label='Análisis Sectorial', value='analisis-sectorial'),
            dcc.Tab(label='Comparaciones', value='comparaciones'),
            dcc.Tab(label='Alertas', value='alertas'),
        ], className="mt-3"),
        
        # Contenido
        html.Div(id='tabs-content', className="container-fluid mt-3"),
        
        # Footer con métricas de rendimiento
        html.Div([
            html.P(id='metricas-rendimiento', className="text-center text-muted small")
        ], className="mt-5")
    ])

app.layout = crear_layout()

# ========================
# CALLBACKS OPTIMIZADOS
# ========================

@app.callback(
    Output('tabs-content', 'children'),
    Output('metricas-rendimiento', 'children'),
    [Input('tabs-main', 'value'),
     Input('rango-fechas', 'value')]
)
def render_content(active_tab, rango_fechas):
    """Renderiza contenido según tab activa - OPTIMIZADO"""
    inicio_render = time.time()
    
    # Filtrar datos una sola vez
    fecha_inicio = pd.Timestamp(year=rango_fechas[0], month=1, day=1)
    fecha_fin = pd.Timestamp(year=rango_fechas[1], month=12, day=31)
    
    if active_tab == 'vista-general':
        content = crear_vista_general(fecha_inicio, fecha_fin)
    elif active_tab == 'analisis-sectorial':
        content = crear_analisis_sectorial(fecha_inicio, fecha_fin)
    elif active_tab == 'comparaciones':
        content = crear_comparaciones(fecha_inicio, fecha_fin)
    elif active_tab == 'alertas':
        content = crear_alertas(fecha_inicio, fecha_fin)
    else:
        content = html.Div("Seleccione una pestaña")
    
    tiempo_render = time.time() - inicio_render
    metricas = f"Renderizado en {tiempo_render:.3f}s | Cache activo | Datos en memoria"
    
    return content, metricas

def crear_vista_general(fecha_inicio, fecha_fin):
    """Vista general optimizada"""
    # Usar datos pre-calculados
    df = CACHE['datos']
    mask = (df['fecha'] >= fecha_inicio) & (df['fecha'] <= fecha_fin)
    df_periodo = df[mask]
    
    # Total nacional
    total_nacional = df_periodo[df_periodo['codigo'] == 'Total'].groupby('fecha')['valor'].sum()
    
    # Gráfico de línea
    fig_linea = go.Figure()
    fig_linea.add_trace(go.Scatter(
        x=total_nacional.index,
        y=total_nacional.values,
        mode='lines+markers',
        name='Empleo Total',
        line=dict(width=3)
    ))
    fig_linea.update_layout(
        title="Evolución del Empleo Total",
        xaxis_title="Fecha",
        yaxis_title="Empleos",
        height=400
    )
    
    # Top sectores (usar pre-calculado)
    sectores_sum = df_periodo[df_periodo['nivel'] == 1].groupby('codigo')['valor'].sum().nlargest(10)
    
    fig_barras = go.Figure()
    fig_barras.add_trace(go.Bar(
        x=sectores_sum.values,
        y=sectores_sum.index,
        orientation='h',
        text=sectores_sum.values.round(0),
        textposition='auto'
    ))
    fig_barras.update_layout(
        title="Top 10 Sectores por Empleo",
        xaxis_title="Empleos",
        height=400
    )
    
    return html.Div([
        html.Div([
            html.Div([dcc.Graph(figure=fig_linea)], className="col-md-6"),
            html.Div([dcc.Graph(figure=fig_barras)], className="col-md-6")
        ], className="row")
    ])

def crear_analisis_sectorial(fecha_inicio, fecha_fin):
    """Análisis sectorial optimizado"""
    df = CACHE['datos']
    mask = (df['fecha'] >= fecha_inicio) & (df['fecha'] <= fecha_fin)
    df_periodo = df[mask]
    
    # Selector de sector
    sectores = sorted(df_periodo[df_periodo['nivel'] == 1]['codigo'].unique())
    
    return html.Div([
        html.Div([
            html.Label("Seleccione sector:"),
            dcc.Dropdown(
                id='selector-sector',
                options=[{'label': s, 'value': s} for s in sectores],
                value=sectores[0] if sectores else None
            )
        ], className="mb-3"),
        html.Div(id='analisis-sector-content')
    ])

def crear_comparaciones(fecha_inicio, fecha_fin):
    """Comparaciones optimizadas"""
    df = CACHE['datos']
    mask = (df['fecha'] >= fecha_inicio) & (df['fecha'] <= fecha_fin)
    df_periodo = df[mask]
    
    # Cambios porcentuales
    cambios = []
    for codigo in df_periodo[df_periodo['nivel'] == 1]['codigo'].unique():
        serie = df_periodo[df_periodo['codigo'] == codigo].sort_values('fecha')
        if len(serie) >= 2:
            inicial = serie.iloc[0]['valor']
            final = serie.iloc[-1]['valor']
            if inicial > 0:
                cambio = ((final - inicial) / inicial) * 100
                cambios.append({
                    'Sector': codigo,
                    'Cambio %': round(cambio, 2),
                    'Inicial': round(inicial, 0),
                    'Final': round(final, 0)
                })
    
    df_cambios = pd.DataFrame(cambios).sort_values('Cambio %', ascending=False)
    
    # Gráfico de barras
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df_cambios['Sector'],
        y=df_cambios['Cambio %'],
        text=df_cambios['Cambio %'].apply(lambda x: f"{x:+.1f}%"),
        textposition='auto',
        marker_color=['green' if x > 0 else 'red' for x in df_cambios['Cambio %']]
    ))
    fig.update_layout(
        title=f"Cambios por Sector ({fecha_inicio.year}-{fecha_fin.year})",
        xaxis_title="Sector",
        yaxis_title="Cambio %",
        height=500
    )
    
    return html.Div([
        dcc.Graph(figure=fig),
        html.Hr(),
        html.H5("Tabla de Cambios"),
        dash_table.DataTable(
            data=df_cambios.to_dict('records'),
            columns=[{"name": i, "id": i} for i in df_cambios.columns],
            sort_action="native",
            style_cell={'textAlign': 'center'},
            style_data_conditional=[
                {
                    'if': {'column_id': 'Cambio %', 'filter_query': '{Cambio %} > 0'},
                    'color': 'green',
                    'fontWeight': 'bold'
                },
                {
                    'if': {'column_id': 'Cambio %', 'filter_query': '{Cambio %} < 0'},
                    'color': 'red',
                    'fontWeight': 'bold'
                }
            ]
        )
    ])

def crear_alertas(fecha_inicio, fecha_fin):
    """Sistema de alertas optimizado"""
    # Usar cambios pre-calculados
    cambios = CACHE.get('cambios_porcentuales', {})
    
    alertas = []
    for codigo, cambio in cambios.items():
        if abs(cambio) > 10:  # Umbral de alerta
            tipo = '🔴 Crítico' if abs(cambio) > 15 else '🟡 Advertencia'
            direccion = '📈 Aumento' if cambio > 0 else '📉 Disminución'
            alertas.append({
                'Tipo': tipo,
                'Sector': codigo,
                'Cambio': f"{cambio:+.1f}%",
                'Dirección': direccion
            })
    
    if alertas:
        df_alertas = pd.DataFrame(alertas)
        return html.Div([
            html.H4("⚠️ Alertas Detectadas"),
            dash_table.DataTable(
                data=df_alertas.to_dict('records'),
                columns=[{"name": i, "id": i} for i in df_alertas.columns],
                style_cell={'textAlign': 'center'},
                style_data_conditional=[
                    {
                        'if': {'column_id': 'Tipo', 'filter_query': '{Tipo} contains "Crítico"'},
                        'backgroundColor': '#ffcccc'
                    },
                    {
                        'if': {'column_id': 'Tipo', 'filter_query': '{Tipo} contains "Advertencia"'},
                        'backgroundColor': '#fff3cd'
                    }
                ]
            )
        ])
    else:
        return html.Div([
            html.H4("✅ Sin Alertas"),
            html.P("No se detectaron cambios significativos en el período seleccionado.")
        ])

@app.callback(
    Output('analisis-sector-content', 'children'),
    [Input('selector-sector', 'value'),
     Input('rango-fechas', 'value')]
)
def actualizar_analisis_sector(sector, rango_fechas):
    """Callback para análisis de sector específico"""
    if not sector:
        return html.Div("Seleccione un sector")
    
    fecha_inicio = pd.Timestamp(year=rango_fechas[0], month=1, day=1)
    fecha_fin = pd.Timestamp(year=rango_fechas[1], month=12, day=31)
    
    df = CACHE['datos']
    mask = (df['fecha'] >= fecha_inicio) & (df['fecha'] <= fecha_fin) & (df['codigo'] == sector)
    df_sector = df[mask].sort_values('fecha')
    
    if df_sector.empty:
        return html.Div("No hay datos para este sector en el período seleccionado")
    
    # Gráfico de evolución
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_sector['fecha'],
        y=df_sector['valor'],
        mode='lines+markers',
        name=sector,
        line=dict(width=3)
    ))
    fig.update_layout(
        title=f"Evolución del Sector {sector}",
        xaxis_title="Fecha",
        yaxis_title="Empleos",
        height=400
    )
    
    # Estadísticas
    stats = df_sector['valor'].describe()
    
    return html.Div([
        dcc.Graph(figure=fig),
        html.Hr(),
        html.H5("Estadísticas del Período"),
        html.Div([
            html.Div([
                html.P(f"Promedio: {stats['mean']:,.0f}", className="mb-1"),
                html.P(f"Mínimo: {stats['min']:,.0f}", className="mb-1"),
            ], className="col-md-6"),
            html.Div([
                html.P(f"Máximo: {stats['max']:,.0f}", className="mb-1"),
                html.P(f"Desv. Est.: {stats['std']:,.0f}", className="mb-1"),
            ], className="col-md-6")
        ], className="row")
    ])

# ========================
# EJECUCIÓN
# ========================

if __name__ == '__main__':
    import sys
    
    if '--production' in sys.argv:
        # Modo producción
        print("Iniciando en modo PRODUCCIÓN...")
        app.run_server(debug=False, host='0.0.0.0', port=8080)
    else:
        # Modo desarrollo
        print("Iniciando en modo DESARROLLO...")
        print("Dashboard disponible en: http://localhost:8050")
        app.run_server(debug=True, host='127.0.0.1', port=8050)