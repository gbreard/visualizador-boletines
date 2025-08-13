"""
Dashboard Simple para verificar funcionamiento básico en Render
"""
import dash
from dash import dcc, html
import pandas as pd
import plotly.express as px
import os
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("="*60)
logger.info("INICIANDO DASHBOARD SIMPLE")
logger.info(f"Directorio: {os.getcwd()}")
logger.info(f"Archivos: {os.listdir('.')}")
logger.info("="*60)

# Crear aplicación Dash
app = dash.Dash(__name__)
server = app.server  # IMPORTANTE para Gunicorn

# Intentar cargar datos
data_loaded = False
df = None
error_msg = ""

try:
    # Intentar cargar un archivo Parquet simple
    if os.path.exists('datos_rapidos/c11.parquet'):
        logger.info("Cargando c11.parquet...")
        df = pd.read_parquet('datos_rapidos/c11.parquet')
        data_loaded = True
        logger.info(f"Datos cargados: {len(df)} registros")
        logger.info(f"Columnas: {list(df.columns)}")
    else:
        error_msg = "No se encontró datos_rapidos/c11.parquet"
        logger.error(error_msg)
except Exception as e:
    error_msg = f"Error cargando datos: {str(e)}"
    logger.error(error_msg)

# Layout de la aplicación
if data_loaded and df is not None:
    # Crear un gráfico simple
    fig = px.line(title="Dashboard Funcionando")
    
    # Si hay columnas apropiadas, hacer un gráfico real
    if len(df.columns) >= 2:
        x_col = df.columns[0]
        y_col = df.columns[1]
        fig = px.line(df, x=x_col, y=y_col, title=f"{y_col} vs {x_col}")
    
    app.layout = html.Div([
        html.H1("✅ Dashboard Simple - FUNCIONANDO"),
        html.P(f"Datos cargados: {len(df)} registros"),
        html.P(f"Columnas: {', '.join(df.columns[:5])}"),
        dcc.Graph(figure=fig),
        html.Hr(),
        html.H3("Primeros 5 registros:"),
        html.Pre(df.head().to_string())
    ])
else:
    # Layout de error
    app.layout = html.Div([
        html.H1("❌ Dashboard Simple - ERROR"),
        html.P(f"Error: {error_msg}"),
        html.Hr(),
        html.H3("Información de Debug:"),
        html.P(f"Directorio: {os.getcwd()}"),
        html.P(f"Existe datos_rapidos?: {os.path.exists('datos_rapidos')}"),
        html.P(f"Archivos en raíz: {', '.join(os.listdir('.')[:10])}")
    ])

logger.info("Dashboard simple configurado")

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8050)