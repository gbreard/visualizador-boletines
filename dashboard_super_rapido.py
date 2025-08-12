"""
Dashboard SUPER RÁPIDO - Carga desde Parquet en < 0.1 segundos
"""
import dash
from dash import dcc, html, Input, Output, dash_table
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import time
import os

# ========================================
# CARGA INSTANTÁNEA DE DATOS
# ========================================

print("Cargando datos...")
inicio = time.time()

# Verificar que existan los archivos Parquet
if not os.path.exists('datos_rapidos/c11.parquet'):
    print("ERROR: Primero ejecuta 'python preprocesar_excel.py'")
    exit(1)

# Cargar datos (esto es INSTANTÁNEO con Parquet)
df_c11 = pd.read_parquet('datos_rapidos/c11.parquet')
df_descriptores = pd.read_parquet('datos_rapidos/descriptores.parquet')

# Intentar cargar C3 si existe
try:
    df_c3 = pd.read_parquet('datos_rapidos/c3.parquet')
except:
    df_c3 = pd.DataFrame()

tiempo_carga = time.time() - inicio
print(f"Datos cargados en {tiempo_carga:.3f} segundos!")
print(f"  - C1.1: {len(df_c11)} registros")
print(f"  - C3: {len(df_c3)} registros")
print(f"  - Descriptores: {len(df_descriptores)} códigos")

# Crear diccionario de descriptores para búsqueda rápida
desc_dict = dict(zip(df_descriptores['codigo'], df_descriptores['descripcion']))

# ========================================
# INICIALIZACIÓN DE DASH
# ========================================

app = dash.Dash(__name__, 
    external_stylesheets=['https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css'],
    suppress_callback_exceptions=True
)

server = app.server

# ========================================
# LAYOUT
# ========================================

# Obtener rango de fechas
fecha_min = df_c11['fecha'].min() if not df_c11.empty else pd.Timestamp('1996-01-01')
fecha_max = df_c11['fecha'].max() if not df_c11.empty else pd.Timestamp('2024-01-01')

app.layout = html.Div([
    # Header
    html.Div([
        html.H1("Dashboard de Empleo - SUPER RÁPIDO", className="text-white mb-0"),
        html.P(f"Cargado en {tiempo_carga:.3f} segundos | {len(df_c11)} trimestres", 
               className="text-white-50 mb-0")
    ], style={'background': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', 
              'padding': '30px', 'marginBottom': '20px'}),
    
    # Controles
    html.Div([
        html.Label("Seleccionar período:", className="fw-bold"),
        dcc.RangeSlider(
            id='periodo-slider',
            min=fecha_min.year,
            max=fecha_max.year,
            value=[max(fecha_min.year, fecha_max.year - 10), fecha_max.year],
            marks={y: str(y) for y in range(fecha_min.year, fecha_max.year + 1, 5)},
            tooltip={"placement": "bottom", "always_visible": False}
        )
    ], className="container mb-4"),
    
    # Tabs
    dcc.Tabs(id="tabs", value='general', children=[
        dcc.Tab(label='Vista General', value='general'),
        dcc.Tab(label='Análisis Sectorial', value='sectorial'),
        dcc.Tab(label='Tendencias', value='tendencias'),
    ], className="container"),
    
    # Contenido
    html.Div(id='contenido', className="container mt-3"),
    
    # Medidor de rendimiento
    html.Div(id='rendimiento', className="text-center text-muted small mt-3")
])

# ========================================
# CALLBACKS ULTRA-RÁPIDOS
# ========================================

@app.callback(
    [Output('contenido', 'children'),
     Output('rendimiento', 'children')],
    [Input('tabs', 'value'),
     Input('periodo-slider', 'value')]
)
def actualizar_contenido(tab, periodo):
    """Actualización instantánea del contenido"""
    inicio_render = time.time()
    
    # Filtrar datos por período (operación vectorizada rápida)
    mask = (df_c11['año'] >= periodo[0]) & (df_c11['año'] <= periodo[1])
    df_filtrado = df_c11[mask].copy()
    
    if tab == 'general':
        contenido = vista_general(df_filtrado)
    elif tab == 'sectorial':
        contenido = vista_sectorial(df_filtrado, periodo)
    elif tab == 'tendencias':
        contenido = vista_tendencias(df_filtrado)
    else:
        contenido = html.Div("Seleccione una pestaña")
    
    tiempo_render = time.time() - inicio_render
    rendimiento = f"Renderizado en {tiempo_render*1000:.0f} ms"
    
    return contenido, rendimiento

def vista_general(df):
    """Vista general optimizada"""
    if df.empty:
        return html.Div("No hay datos para el período seleccionado")
    
    # Gráfico principal
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['fecha'],
        y=df['Total'],
        mode='lines+markers',
        name='Empleo Total',
        line=dict(color='#667eea', width=3),
        marker=dict(size=8)
    ))
    
    # Agregar línea de tendencia
    z = np.polyfit(range(len(df)), df['Total'].values, 1)
    p = np.poly1d(z)
    fig.add_trace(go.Scatter(
        x=df['fecha'],
        y=p(range(len(df))),
        mode='lines',
        name='Tendencia',
        line=dict(color='red', width=2, dash='dash')
    ))
    
    fig.update_layout(
        title="Evolución del Empleo Registrado",
        xaxis_title="Fecha",
        yaxis_title="Cantidad de Empleos",
        hovermode='x unified',
        height=500,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )
    
    # Estadísticas rápidas
    ultimo = df.iloc[-1]['Total']
    primero = df.iloc[0]['Total']
    cambio = ((ultimo - primero) / primero) * 100
    promedio = df['Total'].mean()
    maximo = df['Total'].max()
    minimo = df['Total'].min()
    
    # Calcular cambio trimestral
    if len(df) > 1:
        cambio_trim = ((df.iloc[-1]['Total'] - df.iloc[-2]['Total']) / df.iloc[-2]['Total']) * 100
    else:
        cambio_trim = 0
    
    return html.Div([
        # KPIs
        html.Div([
            html.Div([
                html.Div([
                    html.H2(f"{ultimo:,.0f}", className="mb-0 text-primary"),
                    html.P("Último Valor", className="text-muted mb-0")
                ], className="card-body text-center")
            ], className="card"),
            html.Div([
                html.Div([
                    html.H2(f"{cambio:+.1f}%", 
                           className=f"mb-0 text-{'success' if cambio > 0 else 'danger'}"),
                    html.P("Cambio Total", className="text-muted mb-0")
                ], className="card-body text-center")
            ], className="card"),
            html.Div([
                html.Div([
                    html.H2(f"{cambio_trim:+.1f}%",
                           className=f"mb-0 text-{'success' if cambio_trim > 0 else 'danger'}"),
                    html.P("Cambio Trimestral", className="text-muted mb-0")
                ], className="card-body text-center")
            ], className="card"),
            html.Div([
                html.Div([
                    html.H2(f"{promedio:,.0f}", className="mb-0 text-info"),
                    html.P("Promedio", className="text-muted mb-0")
                ], className="card-body text-center")
            ], className="card")
        ], className="row row-cols-1 row-cols-md-4 g-3 mb-4"),
        
        # Gráfico
        dcc.Graph(figure=fig, config={'displayModeBar': False}),
        
        # Mini tabla resumen
        html.Div([
            html.H5("Resumen Estadístico", className="mt-4"),
            html.Table([
                html.Tr([
                    html.Td("Período:"),
                    html.Td(f"{df.iloc[0]['periodo_str']} - {df.iloc[-1]['periodo_str']}")
                ]),
                html.Tr([
                    html.Td("Máximo:"),
                    html.Td(f"{maximo:,.0f}")
                ]),
                html.Tr([
                    html.Td("Mínimo:"),
                    html.Td(f"{minimo:,.0f}")
                ]),
                html.Tr([
                    html.Td("Rango:"),
                    html.Td(f"{maximo - minimo:,.0f}")
                ])
            ], className="table table-sm w-50")
        ])
    ])

def vista_sectorial(df_general, periodo):
    """Vista sectorial optimizada"""
    if df_c3.empty:
        return html.Div([
            html.Alert("No hay datos sectoriales disponibles. Los datos de C3 no se pudieron procesar.", 
                      className="alert-warning")
        ])
    
    # Filtrar datos sectoriales
    mask = (df_c3['año'] >= periodo[0]) & (df_c3['año'] <= periodo[1])
    df_sect = df_c3[mask].copy()
    
    if df_sect.empty:
        return html.Div("No hay datos sectoriales para este período")
    
    # Top sectores
    sector_totals = df_sect.groupby('sector')['valor'].sum().sort_values(ascending=False).head(10)
    
    # Gráfico de barras
    fig_barras = go.Figure()
    fig_barras.add_trace(go.Bar(
        x=sector_totals.values,
        y=[f"Sector {s}" for s in sector_totals.index],
        orientation='h',
        marker_color='#764ba2',
        text=sector_totals.values.round(0),
        textposition='auto',
    ))
    
    fig_barras.update_layout(
        title="Top 10 Sectores por Empleo",
        xaxis_title="Cantidad de Empleos",
        height=400
    )
    
    # Evolución de top 5
    top5 = sector_totals.index[:5]
    fig_lineas = go.Figure()
    
    for sector in top5:
        df_s = df_sect[df_sect['sector'] == sector].sort_values('fecha')
        fig_lineas.add_trace(go.Scatter(
            x=df_s['fecha'],
            y=df_s['valor'],
            mode='lines+markers',
            name=f"Sector {sector}"
        ))
    
    fig_lineas.update_layout(
        title="Evolución Top 5 Sectores",
        xaxis_title="Fecha",
        yaxis_title="Empleos",
        height=400
    )
    
    return html.Div([
        html.Div([
            html.Div([dcc.Graph(figure=fig_barras)], className="col-md-6"),
            html.Div([dcc.Graph(figure=fig_lineas)], className="col-md-6")
        ], className="row")
    ])

def vista_tendencias(df):
    """Vista de tendencias y análisis"""
    if df.empty:
        return html.Div("No hay datos para analizar")
    
    # Calcular cambios porcentuales
    df['cambio_pct'] = df['Total'].pct_change() * 100
    
    # Gráfico de cambios
    fig_cambios = go.Figure()
    fig_cambios.add_trace(go.Bar(
        x=df['fecha'],
        y=df['cambio_pct'],
        marker_color=['green' if x > 0 else 'red' for x in df['cambio_pct']],
        text=df['cambio_pct'].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else ""),
        textposition='auto',
    ))
    
    fig_cambios.update_layout(
        title="Cambios Porcentuales Trimestrales",
        xaxis_title="Trimestre",
        yaxis_title="Cambio %",
        height=400
    )
    
    # Análisis por año
    df_anual = df.groupby('año').agg({
        'Total': ['mean', 'std', 'min', 'max']
    }).round(0)
    
    # Gráfico anual
    fig_anual = go.Figure()
    años = df_anual.index
    promedios = df_anual[('Total', 'mean')]
    
    fig_anual.add_trace(go.Bar(
        x=años,
        y=promedios,
        marker_color='#667eea',
        text=promedios.round(0),
        textposition='auto',
    ))
    
    fig_anual.update_layout(
        title="Promedio Anual de Empleo",
        xaxis_title="Año",
        yaxis_title="Empleo Promedio",
        height=400
    )
    
    return html.Div([
        html.Div([
            html.Div([dcc.Graph(figure=fig_cambios)], className="col-md-6"),
            html.Div([dcc.Graph(figure=fig_anual)], className="col-md-6")
        ], className="row"),
        
        html.Hr(),
        html.H5("Estadísticas Anuales"),
        dash_table.DataTable(
            data=df_anual.reset_index().to_dict('records'),
            columns=[
                {"name": "Año", "id": "año"},
                {"name": "Promedio", "id": ("Total", "mean"), "type": "numeric", "format": {"specifier": ",.0f"}},
                {"name": "Desv. Est.", "id": ("Total", "std"), "type": "numeric", "format": {"specifier": ",.0f"}},
                {"name": "Mínimo", "id": ("Total", "min"), "type": "numeric", "format": {"specifier": ",.0f"}},
                {"name": "Máximo", "id": ("Total", "max"), "type": "numeric", "format": {"specifier": ",.0f"}}
            ],
            style_cell={'textAlign': 'center'},
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': 'rgb(248, 248, 248)'
                }
            ]
        )
    ])

# Importar numpy para la línea de tendencia
import numpy as np

# ========================================
# EJECUCIÓN
# ========================================

if __name__ == '__main__':
    print("\n" + "="*60)
    print("DASHBOARD SUPER RÁPIDO INICIADO")
    print("="*60)
    print(f"Tiempo de carga inicial: {tiempo_carga:.3f} segundos")
    print(f"URL: http://localhost:8050")
    print("="*60 + "\n")
    
    app.run(debug=True, host='127.0.0.1', port=8050)