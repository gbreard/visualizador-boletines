"""
Dashboard con DEBUG para producción - Versión simplificada
"""
import dash
from dash import dcc, html, Input, Output, dash_table
import pandas as pd
import plotly.graph_objects as go
import os
import logging
from datetime import datetime

# Configurar logging detallado
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =====================================================================
# VERIFICACIÓN INICIAL
# =====================================================================
logger.info("="*60)
logger.info("INICIANDO DASHBOARD - DEBUG MODE")
logger.info("="*60)
logger.info(f"Directorio actual: {os.getcwd()}")
logger.info(f"Archivos en raíz: {os.listdir('.')}")

# Verificar directorios de datos
if os.path.exists('datos_limpios'):
    csv_files = os.listdir('datos_limpios')
    logger.info(f"Archivos CSV encontrados: {len(csv_files)}")
else:
    logger.error("NO EXISTE datos_limpios")

if os.path.exists('datos_rapidos'):
    parquet_files = os.listdir('datos_rapidos')
    logger.info(f"Archivos Parquet encontrados: {len(parquet_files)}")
else:
    logger.error("NO EXISTE datos_rapidos")

# =====================================================================
# CARGA DE DATOS SIMPLIFICADA
# =====================================================================
data_loaded = False
df_test = None
error_message = ""

try:
    logger.info("Intentando cargar datos...")
    
    # Intentar Parquet primero
    if os.path.exists('datos_rapidos/c11.parquet'):
        logger.info("Cargando desde Parquet...")
        df_test = pd.read_parquet('datos_rapidos/c11.parquet')
        data_loaded = True
        logger.info(f"✓ Parquet cargado: {len(df_test)} registros")
    elif os.path.exists('datos_limpios/C1.1.csv'):
        logger.info("Cargando desde CSV...")
        df_test = pd.read_csv('datos_limpios/C1.1.csv')
        data_loaded = True
        logger.info(f"✓ CSV cargado: {len(df_test)} registros")
    else:
        error_message = "No se encontraron archivos de datos"
        logger.error(error_message)
        
    if data_loaded:
        logger.info(f"Columnas: {list(df_test.columns)}")
        logger.info(f"Shape: {df_test.shape}")
        
except Exception as e:
    error_message = f"Error cargando datos: {str(e)}"
    logger.error(error_message)
    import traceback
    logger.error(traceback.format_exc())

# =====================================================================
# APLICACIÓN DASH
# =====================================================================
app = dash.Dash(__name__)
server = app.server  # Importante para Gunicorn

# Layout simple con información de debug
if data_loaded and df_test is not None:
    # Crear gráfico simple
    fig = go.Figure()
    
    # Si hay columna Período y Empleo
    if 'Período' in df_test.columns and 'Empleo' in df_test.columns:
        fig.add_trace(go.Scatter(
            x=df_test['Período'],
            y=df_test['Empleo'],
            mode='lines+markers',
            name='Empleo'
        ))
        fig.update_layout(title='Serie de Empleo', height=400)
    else:
        # Gráfico genérico con las primeras dos columnas
        cols = df_test.columns
        if len(cols) >= 2:
            fig.add_trace(go.Scatter(
                x=df_test.iloc[:, 0],
                y=df_test.iloc[:, 1],
                mode='lines+markers'
            ))
        fig.update_layout(title='Datos Disponibles', height=400)
    
    app.layout = html.Div([
        html.H1("🟢 Dashboard Debug - DATOS CARGADOS", style={'color': 'green'}),
        html.Hr(),
        
        html.Div([
            html.H3("Información del Sistema:"),
            html.P(f"📁 Directorio: {os.getcwd()}"),
            html.P(f"📊 Registros cargados: {len(df_test)}"),
            html.P(f"📋 Columnas: {', '.join(df_test.columns)}"),
            html.P(f"⏰ Hora servidor: {datetime.now()}"),
        ], style={'backgroundColor': '#f0f0f0', 'padding': '20px', 'borderRadius': '10px'}),
        
        html.Hr(),
        html.H3("Gráfico de Prueba:"),
        dcc.Graph(figure=fig),
        
        html.Hr(),
        html.H3("Primeros 10 Registros:"),
        dash_table.DataTable(
            data=df_test.head(10).to_dict('records'),
            columns=[{"name": i, "id": i} for i in df_test.columns],
            style_cell={'textAlign': 'left'},
            style_data={'whiteSpace': 'normal', 'height': 'auto'}
        ),
        
        html.Hr(),
        html.H3("Estadísticas:"),
        html.Pre(df_test.describe().to_string())
    ])
    
else:
    # Layout de error
    app.layout = html.Div([
        html.H1("🔴 Dashboard Debug - ERROR", style={'color': 'red'}),
        html.Hr(),
        
        html.Div([
            html.H3("ERROR: No se pudieron cargar los datos"),
            html.P(f"Mensaje: {error_message}"),
            html.Hr(),
            html.H4("Información de Debug:"),
            html.P(f"📁 Directorio actual: {os.getcwd()}"),
            html.P(f"📂 Archivos en raíz: {', '.join(os.listdir('.')[:10])}..."),
            html.P(f"⏰ Hora servidor: {datetime.now()}"),
            
            html.Hr(),
            html.H4("Directorios esperados:"),
            html.P(f"datos_limpios existe: {os.path.exists('datos_limpios')}"),
            html.P(f"datos_rapidos existe: {os.path.exists('datos_rapidos')}"),
            
            html.Hr(),
            html.H4("Archivos CSV disponibles:"),
            html.Pre(str(os.listdir('datos_limpios')[:5]) if os.path.exists('datos_limpios') else "No existe"),
            
            html.H4("Archivos Parquet disponibles:"),
            html.Pre(str(os.listdir('datos_rapidos')[:5]) if os.path.exists('datos_rapidos') else "No existe"),
        ], style={'backgroundColor': '#ffe0e0', 'padding': '20px', 'borderRadius': '10px'})
    ])

# Callback simple para verificar que funciona
@app.callback(
    Output('dummy-output', 'children'),
    Input('dummy-input', 'value'),
    prevent_initial_call=True
)
def dummy_callback(value):
    return value

# Agregar componentes dummy ocultos
app.layout.children.extend([
    html.Div(id='dummy-output', style={'display': 'none'}),
    dcc.Input(id='dummy-input', style={'display': 'none'})
])

logger.info("="*60)
logger.info("DASHBOARD LISTO")
logger.info(f"Datos cargados: {data_loaded}")
logger.info("="*60)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8050)