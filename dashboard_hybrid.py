"""
Dashboard Híbrido - Funciona con o sin pandas
"""
import dash
from dash import dcc, html
import os
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("="*60)
logger.info("DASHBOARD HYBRID")
logger.info(f"Directorio: {os.getcwd()}")
logger.info("="*60)

# Intentar importar pandas
pandas_available = False
df = None
try:
    import pandas as pd
    pandas_available = True
    logger.info("✅ Pandas disponible")
except ImportError:
    logger.warning("⚠️ Pandas no disponible - modo básico")

# Crear aplicación Dash
app = dash.Dash(__name__)
server = app.server

# Verificar archivos
archivos_info = {
    'datos_rapidos_exists': os.path.exists('datos_rapidos'),
    'archivos': []
}

if os.path.exists('datos_rapidos'):
    archivos_info['archivos'] = os.listdir('datos_rapidos')
    logger.info(f"Archivos encontrados: {len(archivos_info['archivos'])}")

# Intentar cargar datos si pandas está disponible
data_loaded = False
error_msg = ""

if pandas_available and os.path.exists('datos_rapidos/c11.parquet'):
    try:
        logger.info("Intentando cargar c11.parquet...")
        df = pd.read_parquet('datos_rapidos/c11.parquet')
        data_loaded = True
        logger.info(f"✅ Datos cargados: {len(df)} registros")
    except Exception as e:
        error_msg = f"Error cargando: {str(e)}"
        logger.error(error_msg)
elif not pandas_available:
    error_msg = "Pandas no disponible"
else:
    error_msg = "Archivo c11.parquet no encontrado"

# Layout adaptativo
if data_loaded and df is not None:
    # Layout con datos
    import plotly.express as px
    
    # Crear gráfico simple
    fig = px.line(title="Datos Cargados Exitosamente")
    if len(df.columns) >= 2:
        x_col = df.columns[0]
        y_col = df.columns[1]
        fig = px.line(df, x=x_col, y=y_col, title=f"{y_col} vs {x_col}")
    
    app.layout = html.Div([
        html.H1("✅ Dashboard Funcionando con Datos"),
        html.P(f"Registros: {len(df)}"),
        html.P(f"Columnas: {', '.join(df.columns[:5])}"),
        dcc.Graph(figure=fig),
        html.Hr(),
        html.Pre(df.head().to_string())
    ])
else:
    # Layout sin datos pero funcional
    app.layout = html.Div([
        html.H1("🔍 Dashboard Hybrid"),
        html.Hr(),
        
        html.Div([
            html.H3("Estado:"),
            html.P(f"Pandas: {'✅ Disponible' if pandas_available else '❌ No disponible'}"),
            html.P(f"Datos: {'✅ Cargados' if data_loaded else '❌ No cargados'}"),
            html.P(f"Error: {error_msg}" if error_msg else ""),
        ], style={'backgroundColor': '#f0f0f0', 'padding': '20px'}),
        
        html.Hr(),
        html.H3("Archivos Disponibles:"),
        html.P(f"datos_rapidos existe: {'✅' if archivos_info['datos_rapidos_exists'] else '❌'}"),
        
        html.Div([
            html.H4("Archivos Parquet encontrados:"),
            html.Ul([
                html.Li(f) for f in archivos_info['archivos'][:10]
            ]) if archivos_info['archivos'] else html.P("No hay archivos")
        ]),
        
        html.Hr(),
        html.H3("Información del Sistema:"),
        html.P(f"Python: {os.sys.version}"),
        html.P(f"Directorio: {os.getcwd()}"),
        html.P(f"Archivos en raíz: {', '.join(os.listdir('.')[:15])}")
    ])

logger.info(f"Dashboard configurado - Pandas: {pandas_available}, Datos: {data_loaded}")

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8050)