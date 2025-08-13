"""
Dashboard Mínimo - Solo para verificar que Render funciona
"""
import dash
from dash import dcc, html
import os
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("="*60)
logger.info("DASHBOARD MINIMAL - SIN PANDAS")
logger.info(f"Directorio: {os.getcwd()}")
logger.info(f"Archivos: {os.listdir('.')}")
logger.info("="*60)

# Crear aplicación Dash
app = dash.Dash(__name__)
server = app.server  # IMPORTANTE para Gunicorn

# Verificar estructura
datos_info = {}
if os.path.exists('datos_rapidos'):
    datos_info['datos_rapidos'] = os.listdir('datos_rapidos')
    logger.info(f"datos_rapidos contiene: {len(datos_info['datos_rapidos'])} archivos")
else:
    datos_info['datos_rapidos'] = 'NO EXISTE'
    logger.error("datos_rapidos NO EXISTE")

# Layout simple
app.layout = html.Div([
    html.H1("🔍 Dashboard Minimal - Verificación de Render"),
    html.Hr(),
    
    html.Div([
        html.H3("Estado del Sistema:"),
        html.P(f"✅ Dash funcionando"),
        html.P(f"📁 Directorio: {os.getcwd()}"),
        html.P(f"🐍 Python: {os.sys.version}"),
    ], style={'backgroundColor': '#e8f4f8', 'padding': '20px', 'borderRadius': '10px'}),
    
    html.Hr(),
    html.H3("Verificación de Archivos:"),
    html.P(f"datos_rapidos existe: {'✅ SÍ' if os.path.exists('datos_rapidos') else '❌ NO'}"),
    
    html.Div([
        html.H4("Contenido de datos_rapidos:"),
        html.Pre(
            str(datos_info['datos_rapidos'][:10]) if isinstance(datos_info.get('datos_rapidos'), list) 
            else datos_info.get('datos_rapidos', 'Error')
        )
    ], style={'backgroundColor': '#f5f5f5', 'padding': '10px'}),
    
    html.Hr(),
    html.H3("Archivos en raíz:"),
    html.Pre(', '.join(os.listdir('.')[:20])),
    
    html.Hr(),
    html.P("Este es un dashboard mínimo sin pandas para verificar que Render funciona."),
    html.P("Si ves esto, el problema es con las dependencias de datos (pandas/numpy).")
])

logger.info("Dashboard minimal configurado exitosamente")

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8050)