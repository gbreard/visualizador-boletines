import dash
from dash import dcc, html, callback, Input, Output, State
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import os
import re
from datetime import datetime

# Inicializar la aplicación Dash
app = dash.Dash(__name__)
server = app.server

# Función para verificar archivos CSV
def verificar_csv(ruta):
    if os.path.exists(ruta):
        try:
            # Leer solo las primeras filas para diagnóstico
            df = pd.read_csv(ruta, nrows=5)
            print(f"\nContenido de {ruta} (primeras 5 filas):")
            print(df.head())
            print(f"Columnas: {df.columns.tolist()}")
            return True
        except Exception as e:
            print(f"Error al leer {ruta}: {e}")
            return False
    else:
        print(f"Archivo no encontrado: {ruta}")
        return False

# Verificar archivos CSV al inicio
print("\n===== VERIFICACIÓN DE ARCHIVOS CSV =====")
verificar_csv("datos_procesados/series_temporales.csv")
verificar_csv("datos_procesados/datos_sectoriales.csv")


# ------------------------------------------------------------------------------
# 1) Funciones de preprocesamiento y carga de datos
# ------------------------------------------------------------------------------

def unify_period_string(period_str):
    """Unifica formatos de período"""
    if pd.isna(period_str):
        return ""
    
    p = str(period_str).strip()
    
    # Reemplazos comunes para números ordinales
    p = re.sub(r"1er\s+trim", "1º Trim", p, flags=re.IGNORECASE)
    p = re.sub(r"2do\s+trim", "2º Trim", p, flags=re.IGNORECASE)
    p = re.sub(r"3er\s+trim", "3º Trim", p, flags=re.IGNORECASE)
    p = re.sub(r"4to\s+trim", "4º Trim", p, flags=re.IGNORECASE)
    
    # Manejar variantes con grado (°)
    p = re.sub(r"1°\s+trim", "1º Trim", p, flags=re.IGNORECASE)
    p = re.sub(r"2°\s+trim", "2º Trim", p, flags=re.IGNORECASE)
    p = re.sub(r"3°\s+trim", "3º Trim", p, flags=re.IGNORECASE)
    p = re.sub(r"4°\s+trim", "4º Trim", p, flags=re.IGNORECASE)
    
    # Uniformar "trim" (asegurarse que sea "Trim" con T mayúscula)
    p = re.sub(r"\btrim\b", "Trim", p, flags=re.IGNORECASE)
    
    # Eliminar espacios dobles
    p = re.sub(r"\s+", " ", p)
    
    return p

def find_header_row(file_path, sheet_name):
    """Busca fila de encabezados"""
    try:
        import openpyxl
        wb = openpyxl.load_workbook(file_path, read_only=True)
        ws = wb[sheet_name]
        
        for i, row in enumerate(ws.iter_rows(max_row=15)):
            for cell in row:
                if cell.value and "Período" in str(cell.value):
                    return i
        return 2
    except Exception as e:
        print(f"Error buscando encabezados: {e}")
        return 2

def preprocesar_datos(file_path):
    """Función principal de preprocesamiento"""
    print(f"Preprocesando datos desde: {file_path}")
    
    # Crear directorio de salida
    output_dir = "datos_procesados"
    os.makedirs(output_dir, exist_ok=True)
    
    # Cargar datos de series temporales (C1.1 y C1.2)
    try:
        # Leer C1.2 (desestacionalizada)
        header_row = find_header_row(file_path, "C1.2")
        df_c12 = pd.read_excel(file_path, sheet_name="C1.2", header=header_row)
        df_c12["Fuente"] = "C1.2"
        print(f"C1.2 leído: {len(df_c12)} filas")
        
        # Leer C1.1 (con estacionalidad)
        header_row = find_header_row(file_path, "C1.1")
        df_c11 = pd.read_excel(file_path, sheet_name="C1.1", header=header_row)
        df_c11["Fuente"] = "C1.1"
        print(f"C1.1 leído: {len(df_c11)} filas")
        
        # Combinar
        df_series = pd.concat([df_c11, df_c12], ignore_index=True)
        
        # Limpiar períodos
        if "Período" in df_series.columns:
            df_series["Período"] = df_series["Período"].apply(unify_period_string)
        
        # Guardar
        output_path = os.path.join(output_dir, "series_temporales.csv")
        df_series.to_csv(output_path, index=False)
        print(f"Series temporales guardadas: {output_path}")
    except Exception as e:
        print(f"Error procesando series temporales: {e}")
        df_series = pd.DataFrame()
    
    # Cargar datos sectoriales (C2.x a C7)
    try:
        sector_sheets = ["C2.1", "C2.2", "C3", "C4", "C5", "C6", "C7"]
        df_sector_list = []
        
        for sheet in sector_sheets:
            try:
                header_row = find_header_row(file_path, sheet)
                df = pd.read_excel(file_path, sheet_name=sheet, header=header_row)
                df["Fuente"] = sheet
                df_sector_list.append(df)
                print(f"{sheet} leído: {len(df)} filas")
            except Exception as e:
                print(f"Error leyendo {sheet}: {e}")
        
        # Combinar datos sectoriales
        if df_sector_list:
            df_sectorial = pd.concat(df_sector_list, ignore_index=True)
            
            # Guardar
            output_path = os.path.join(output_dir, "datos_sectoriales.csv")
            df_sectorial.to_csv(output_path, index=False)
            print(f"Datos sectoriales guardados: {output_path}")
        else:
            df_sectorial = pd.DataFrame()
            print("No se pudieron cargar datos sectoriales")
    except Exception as e:
        print(f"Error procesando datos sectoriales: {e}")
        df_sectorial = pd.DataFrame()
    
    # Crear un archivo de metadatos básico
    try:
        metadata = []
        for sheet in ["C1.1", "C1.2", "C2.1", "C2.2", "C3", "C4", "C5", "C6", "C7"]:
            try:
                metadata.append({
                    "Sheet": sheet,
                    "Titulo": f"Datos de {sheet}",
                    "TipoSerie": "Desestacionalizada" if ".2" in sheet else "Con estacionalidad"
                })
            except Exception:
                pass
        
        df_metadata = pd.DataFrame(metadata)
        output_path = os.path.join(output_dir, "metadatos.csv")
        df_metadata.to_csv(output_path, index=False)
        print(f"Metadatos guardados: {output_path}")
    except Exception as e:
        print(f"Error creando metadatos: {e}")
    
    # Crear un archivo de descriptores vacío para compatibilidad
    try:
        pd.DataFrame(columns=["Codigo", "Descripcion"]).to_csv(
            os.path.join(output_dir, "descriptores_actividad.csv"), index=False
        )
        print("Archivo de descriptores creado para compatibilidad")
    except Exception as e:
        print(f"Error creando descriptores: {e}")
    
    return {
        "series_temporales": os.path.join(output_dir, "series_temporales.csv"),
        "datos_sectoriales": os.path.join(output_dir, "datos_sectoriales.csv")
    }

def cargar_datos(directorio="datos_procesados"):
    """Carga los datos procesados"""
    datos = {}
    
    # Rutas de archivos
    rutas = {
        "series_temporales": os.path.join(directorio, "series_temporales.csv"),
        "datos_sectoriales": os.path.join(directorio, "datos_sectoriales.csv"),
        "descriptores": os.path.join(directorio, "descriptores_actividad.csv"),
        "metadatos": os.path.join(directorio, "metadatos.csv")
    }
    
    # Cargar cada archivo si existe
    for nombre, ruta in rutas.items():
        if os.path.exists(ruta):
            try:
                datos[nombre] = pd.read_csv(ruta)
                print(f"Cargado: {ruta} ({len(datos[nombre])} filas)")
            except Exception as e:
                print(f"Error al cargar {ruta}: {e}")
                datos[nombre] = pd.DataFrame()
        else:
            print(f"Archivo no encontrado: {ruta}")
            datos[nombre] = pd.DataFrame()
    
    return datos





def preparar_series(df):
    """Prepara los datos de series temporales"""
    if df.empty or 'Período' not in df.columns or 'Empleo' not in df.columns:
        return df
    
    # Copiar para evitar modificar el original
    df = df.copy()
    
    # Asegurarse de que Empleo es numérico
    df['Empleo'] = pd.to_numeric(df['Empleo'], errors='coerce')
    
    # Extraer año y trimestre
    df['Año'] = pd.to_numeric(
        df['Período'].str.extract(r'(\d{4})')[0], errors='coerce'
    ).astype('Int64')
    df['Trimestre'] = pd.to_numeric(
        df['Período'].str.extract(r'([1-4])')[0], errors='coerce'
    ).astype('Int64')
    
    # Ordenar cronológicamente
    df = df.sort_values(['Año', 'Trimestre'])
    
    # Intentar calcular variaciones seguras
    try:
        # Variación interanual (segura)
        df['varInteranual'] = df.groupby('Trimestre')['Empleo'].pct_change(4, fill_method=None) * 100
        # Variación trimestral (segura)
        df['varTrimestral'] = df['Empleo'].pct_change(fill_method=None) * 100
    except Exception as e:
        print(f"Advertencia: Error al calcular variaciones: {e}")
    
    return df


    # Después de cargar los datos
    print("\n----- DIAGNÓSTICO DE DATOS -----")
    print(f"Series temporales: {df_series.shape}")
    print(f"Series con estacionalidad: {df_estacional.shape if not df_estacional.empty else 'Vacío'}")
    print(f"Series desestacionalizadas: {df_desestacionalizada.shape if not df_desestacionalizada.empty else 'Vacío'}")
    print(f"Columnas en series temporales: {df_series.columns.tolist()}")
    print("----- MUESTRAS DE DATOS -----")
    if not df_series.empty:
        print("\nPrimeras 3 filas de series temporales:")
        print(df_series.head(3))


# ------------------------------------------------------------------------------
# 2) Verificación y preparación inicial
# ------------------------------------------------------------------------------

# Verificar o crear el directorio de datos procesados
output_dir = "datos_procesados"
os.makedirs(output_dir, exist_ok=True)

# Verificar si existen archivos procesados
series_path = os.path.join(output_dir, "series_temporales.csv")
sectorial_path = os.path.join(output_dir, "datos_sectoriales.csv")

# Verificar si es necesario preprocesar
if not os.path.exists(series_path) or not os.path.exists(sectorial_path):
    # Buscar el archivo Excel
    excel_file = "nacional_serie_empleo_trimestral_actualizado241312.xlsx"
    if os.path.exists(excel_file):
        print(f"Archivo Excel encontrado: {excel_file}")
        # Preprocesar datos
        preprocesar_datos(excel_file)
    else:
        print(f"¡ADVERTENCIA! Archivo Excel no encontrado: {excel_file}")
        print("El dashboard podría no mostrar datos correctamente.")

# Cargar datos
datos = cargar_datos()

# Preparar series temporales
df_series = datos.get("series_temporales", pd.DataFrame())
df_series_procesadas = preparar_series(df_series)

# Filtrar series
df_estacional = df_series_procesadas[df_series_procesadas['Fuente'] == 'C1.1'] if not df_series_procesadas.empty else pd.DataFrame()
df_desestacionalizada = df_series_procesadas[df_series_procesadas['Fuente'] == 'C1.2'] if not df_series_procesadas.empty else pd.DataFrame()

# Si no hay datos específicos, usar todos
if df_desestacionalizada.empty:
    df_desestacionalizada = df_series_procesadas

# Obtener períodos disponibles
periodos_disponibles = []
if not df_series_procesadas.empty and 'Período' in df_series_procesadas.columns:
    periodos = df_series_procesadas['Período'].unique().tolist()
    
    # Ordenar períodos
    def orden_periodo(p):
        match_year = re.search(r'(\d{4})', str(p))
        match_trim = re.search(r'([1-4])', str(p))
        if match_year and match_trim:
            return int(match_year.group(1)) * 10 + int(match_trim.group(1))
        return 0
    
    periodos_disponibles = sorted(periodos, key=orden_periodo)

# Obtener período más reciente
ultimo_periodo = periodos_disponibles[-1] if periodos_disponibles else None
periodo_anterior = periodos_disponibles[-5] if len(periodos_disponibles) >= 5 else periodos_disponibles[0] if periodos_disponibles else None

# ------------------------------------------------------------------------------
# 3) Inicialización de la aplicación Dash
# ------------------------------------------------------------------------------

# Colores
colors = {
    'primary': '#2c3e50',
    'secondary': '#3498db',
    'success': '#2ecc71',
    'danger': '#e74c3c',
    'warning': '#f39c12',
    'info': '#1abc9c',
    'light': '#ecf0f1',
    'bg': '#f5f7fa',
    'text': '#333333'
}

# ------------------------------------------------------------------------------
# 4) Layout de la aplicación
# ------------------------------------------------------------------------------

app.layout = html.Div([
    # ENCABEZADO
    html.Div([
        html.H1("Dashboard de Empleo Registrado en Argentina", 
                style={'textAlign': 'center', 'color': 'white', 'padding': '20px 0'})
    ], style={'backgroundColor': colors['primary'], 'marginBottom': '20px'}),
    
    # CONTENEDOR PRINCIPAL
    html.Div([
        # SECCIÓN DE INDICADORES
        html.Div([
            # Empleo actual
            html.Div([
                html.H4("Empleo Actual", style={'fontSize': '14px', 'color': '#777'}),
                html.Div(id="indicador-empleo", style={'fontSize': '24px', 'fontWeight': 'bold'}),
                html.Div(id="indicador-periodo", style={'fontSize': '12px', 'color': '#999'})
            ], style={
                'flex': '1',
                'backgroundColor': 'white',
                'padding': '15px',
                'borderRadius': '5px',
                'boxShadow': '0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24)',
                'minWidth': '200px'
            }),
            
            # Variación interanual
            html.Div([
                html.H4("Variación Interanual", style={'fontSize': '14px', 'color': '#777'}),
                html.Div(id="indicador-var-interanual", style={'fontSize': '24px', 'fontWeight': 'bold'}),
                html.Div("vs. mismo trimestre año anterior", style={'fontSize': '12px', 'color': '#999'})
            ], style={
                'flex': '1',
                'backgroundColor': 'white',
                'padding': '15px',
                'borderRadius': '5px',
                'boxShadow': '0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24)',
                'minWidth': '200px'
            }),
            
            # Variación trimestral
            html.Div([
                html.H4("Variación Trimestral", style={'fontSize': '14px', 'color': '#777'}),
                html.Div(id="indicador-var-trimestral", style={'fontSize': '24px', 'fontWeight': 'bold'}),
                html.Div("vs. trimestre anterior", style={'fontSize': '12px', 'color': '#999'})
            ], style={
                'flex': '1',
                'backgroundColor': 'white',
                'padding': '15px',
                'borderRadius': '5px',
                'boxShadow': '0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24)',
                'minWidth': '200px'
            })
        ], style={
            'display': 'flex',
            'flexWrap': 'wrap',
            'gap': '15px',
            'marginBottom': '20px'
        }),
        
        # CONTROLES Y EVOLUCIÓN HISTÓRICA
        html.Div([
            # Panel de control
            html.Div([
                html.H3("Controles", style={'borderBottom': '1px solid #eee', 'paddingBottom': '10px', 'marginBottom': '15px'}),
                
                # Selector de período
                html.Div([
                    html.Label("Período de análisis:", style={'display': 'block', 'marginBottom': '5px'}),
                    dcc.Dropdown(
                        id="dropdown-periodo",
                        options=[{"label": p, "value": p} for p in periodos_disponibles],
                        value=ultimo_periodo,
                        clearable=False,
                        style={'width': '100%'}
                    )
                ], style={'marginBottom': '15px'}),
                
                # Selector de tipo de serie
                html.Div([
                    html.Label("Tipo de serie:", style={'display': 'block', 'marginBottom': '5px'}),
                    dcc.RadioItems(
                        id="radio-tipo-serie",
                        options=[
                            {"label": "Con estacionalidad", "value": "estacional"},
                            {"label": "Desestacionalizada", "value": "desestacionalizada"}
                        ],
                        value="desestacionalizada"
                    )
                ], style={'marginBottom': '15px'}),
                
                # Selector de nivel de detalle
                html.Div([
                    html.Label("Nivel de detalle sectorial:", style={'display': 'block', 'marginBottom': '5px'}),
                    dcc.Dropdown(
                        id="dropdown-nivel-detalle",
                        options=[
                            {"label": "Grandes divisiones", "value": "grandes_divisiones"},
                            {"label": "Letra CIIU", "value": "letra_ciiu"},
                            {"label": "2 dígitos CIIU", "value": "ciiu_2d"}
                        ],
                        value="grandes_divisiones",
                        clearable=False,
                        style={'width': '100%'}
                    )
                ], style={'marginBottom': '15px'})
            ], style={
                'flex': '1',
                'backgroundColor': 'white',
                'padding': '20px',
                'borderRadius': '5px',
                'boxShadow': '0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24)',
                'minWidth': '250px'
            }),
            
            # Gráfico de evolución
            html.Div([
                html.H3("Evolución del Empleo Registrado", 
                        style={'borderBottom': '1px solid #eee', 'paddingBottom': '10px', 'marginBottom': '15px'}),
                dcc.Graph(id="grafico-evolucion")
            ], style={
                'flex': '3',
                'backgroundColor': 'white',
                'padding': '20px',
                'borderRadius': '5px',
                'boxShadow': '0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24)',
                'minWidth': '400px'
            })
        ], style={
            'display': 'flex',
            'flexWrap': 'wrap',
            'gap': '20px',
            'marginBottom': '20px'
        }),
        
        # COMPOSICIÓN SECTORIAL Y EVOLUCIÓN RECIENTE
        html.Div([
            # Composición sectorial
            html.Div([
                html.H3("Composición Sectorial", 
                        style={'borderBottom': '1px solid #eee', 'paddingBottom': '10px', 'marginBottom': '15px'}),
                dcc.Graph(id="grafico-sectorial")
            ], style={
                'flex': '1',
                'backgroundColor': 'white',
                'padding': '20px',
                'borderRadius': '5px',
                'boxShadow': '0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24)',
                'minWidth': '350px'
            }),
            
            # Evolución reciente
            html.Div([
                html.H3("Evolución Reciente", 
                        style={'borderBottom': '1px solid #eee', 'paddingBottom': '10px', 'marginBottom': '15px'}),
                dcc.Graph(id="grafico-evolucion-reciente")
            ], style={
                'flex': '1',
                'backgroundColor': 'white',
                'padding': '20px',
                'borderRadius': '5px',
                'boxShadow': '0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24)',
                'minWidth': '350px'
            })
        ], style={
            'display': 'flex',
            'flexWrap': 'wrap',
            'gap': '20px',
            'marginBottom': '20px'
        }),
        
        # TABLA DE DATOS
        html.Div([
            html.H3("Datos Detallados", 
                    style={'borderBottom': '1px solid #eee', 'paddingBottom': '10px', 'marginBottom': '15px'}),
            html.Div(id="tabla-datos", style={'overflowX': 'auto'})
        ], style={
            'backgroundColor': 'white',
            'padding': '20px',
            'borderRadius': '5px',
            'boxShadow': '0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24)'
        })
    ], style={
        'maxWidth': '1200px',
        'margin': '0 auto',
        'padding': '0 20px'
    }),
    
    # PIE DE PÁGINA
    html.Footer([
        html.P("Fuente: Ministerio de Trabajo, Empleo y Seguridad Social de Argentina", 
              style={'margin': '5px 0', 'color': 'white', 'opacity': '0.8'}),
        html.P("Dashboard desarrollado con Dash y Plotly", 
              style={'margin': '5px 0', 'color': 'white', 'opacity': '0.8'}),
        html.P(f"Última actualización: {datetime.now().strftime('%d/%m/%Y')}", 
              style={'margin': '5px 0', 'color': 'white', 'opacity': '0.8'})
    ], style={
        'backgroundColor': colors['primary'],
        'textAlign': 'center',
        'padding': '20px 0',
        'marginTop': '40px'
    })
])

# ------------------------------------------------------------------------------
# 5) Callbacks para interactividad
# ------------------------------------------------------------------------------

# Callback para actualizar indicadores
@callback(
    [Output("indicador-empleo", "children"),
     Output("indicador-periodo", "children"),
     Output("indicador-var-interanual", "children"),
     Output("indicador-var-interanual", "style"),
     Output("indicador-var-trimestral", "children"),
     Output("indicador-var-trimestral", "style")],
    [Input("dropdown-periodo", "value"),
     Input("radio-tipo-serie", "value")]
)
def actualizar_indicadores(periodo, tipo_serie):
    # Seleccionar dataframe según tipo de serie
    df = df_estacional if tipo_serie == "estacional" else df_desestacionalizada
    
    if df.empty or not periodo:
        return "No disponible", "No disponible", "No disponible", {}, "No disponible", {}
    
    # Filtrar por período
    df_periodo = df[df['Período'] == periodo]
    
    if df_periodo.empty:
        return "No disponible", "No disponible", "No disponible", {}, "No disponible", {}
    
    # Extraer valores
    empleo = df_periodo['Empleo'].values[0]
    
    # Variación interanual
    var_interanual = df_periodo['varInteranual'].values[0] if 'varInteranual' in df_periodo.columns else None
    if var_interanual is None or pd.isna(var_interanual):
        var_interanual_str = "No disponible"
        var_interanual_style = {}
    else:
        var_interanual_str = f"{var_interanual:.2f}%"
        var_interanual_style = {"color": "#2ecc71" if var_interanual >= 0 else "#e74c3c"}
    
    # Variación trimestral
    var_trimestral = df_periodo['varTrimestral'].values[0] if 'varTrimestral' in df_periodo.columns else None
    if var_trimestral is None or pd.isna(var_trimestral):
        var_trimestral_str = "No disponible"
        var_trimestral_style = {}
    else:
        var_trimestral_str = f"{var_trimestral:.2f}%"
        var_trimestral_style = {"color": "#2ecc71" if var_trimestral >= 0 else "#e74c3c"}
    
    # Formatear valores
    empleo_str = f"{empleo:,.0f}"
    periodo_str = f"{periodo}"
    
    return empleo_str, periodo_str, var_interanual_str, var_interanual_style, var_trimestral_str, var_trimestral_style


@callback(
    Output("grafico-evolucion", "figure"),
    [Input("radio-tipo-serie", "value")]
)
def actualizar_grafico_evolucion(tipo_serie):
    # Seleccionar dataframe según tipo de serie
    df = df_estacional if tipo_serie == "estacional" else df_desestacionalizada

    print(f"DEBUG - actualizar_grafico_evolucion - tipo_serie: {tipo_serie}")
    print(f"DEBUG - actualizar_grafico_evolucion - df shape: {df.shape if not df.empty else 'DataFrame vacío'}")
    
    if df.empty:
        print("DEBUG - DataFrame vacío en actualizar_grafico_evolucion")
        return go.Figure().update_layout(title="No hay datos disponibles")
    
    # Imprimir las primeras filas para verificar
    print("DEBUG - Primeras 5 filas del DataFrame:")
    print(df.head())
    
    # Crear gráfico - IMPORTANTE: Usar solo una forma de crear el gráfico
    fig = px.line(
        df, 
        x='Período', 
        y='Empleo',
        title=f'Evolución del empleo registrado en el sector privado',
        labels={'Empleo': 'Empleos registrados', 'Período': 'Período'}
    )
    
    # Añadir marcas para crisis económicas
    crisis = [
        {"periodo": "4º Trim 2001", "nombre": "Crisis 2001"},
        {"periodo": "3º Trim 2008", "nombre": "Crisis 2008"},
        {"periodo": "3º Trim 2018", "nombre": "Crisis 2018"},
        {"periodo": "1º Trim 2020", "nombre": "COVID-19"}
    ]
    
    for c in crisis:
        if c["periodo"] in df["Período"].values:
            idx = df[df["Período"] == c["periodo"]].index
            if len(idx) > 0:  # Verificar que haya resultados
                fig.add_vline(
                    x=idx[0],
                    line_width=1,
                    line_dash="dash",
                    line_color="gray",
                    annotation_text=c["nombre"],
                    annotation_position="top right"
                )
    
    # Personalizar
    fig.update_layout(
        xaxis={'title': 'Período'},
        yaxis={'title': 'Empleos registrados'},
        template='plotly_white',
        height=400
    )
    
    return fig



@callback(
    Output("grafico-sectorial", "figure"),
    [Input("dropdown-periodo", "value"),
     Input("dropdown-nivel-detalle", "value")]
)
def actualizar_grafico_sectorial(periodo, nivel_detalle):
    # Datos sectoriales
    df_sectorial = datos.get("datos_sectoriales", pd.DataFrame())
    
    if df_sectorial.empty or not periodo:
        return go.Figure().update_layout(title="No hay datos sectoriales disponibles")
    
    # Filtrar por período
    df_filtrado = df_sectorial[df_sectorial['Período'].astype(str) == str(periodo)]
    
    # Mapear nivel de detalle a fuentes
    if nivel_detalle == "grandes_divisiones":
        fuentes = ["C2.1", "C2.2"]
    elif nivel_detalle == "letra_ciiu":
        fuentes = ["C3"]
    elif nivel_detalle == "ciiu_2d":
        fuentes = ["C4"]
    else:
        fuentes = ["C2.1", "C2.2"]
    
    # Filtrar por fuentes
    if 'Fuente' in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado['Fuente'].isin(fuentes)]
    
    if df_filtrado.empty:
        return go.Figure().update_layout(title=f"No hay datos para {periodo} con el nivel de detalle seleccionado")
    
    # Determinar columna de categoría
    columna_categoria = None
    for posible_col in ['Categoría', 'Sector']:
        if posible_col in df_filtrado.columns:
            columna_categoria = posible_col
            break
    
    if not columna_categoria:
        return go.Figure().update_layout(title="No se pudo determinar la columna de categoría")
    
    # Convertir valores a numéricos
    df_filtrado['Valor'] = pd.to_numeric(df_filtrado['Valor'], errors='coerce')
    df_filtrado = df_filtrado.dropna(subset=['Valor'])
    
    # Ordenar por valor y tomar los primeros 8 sectores
    df_filtrado = df_filtrado.sort_values('Valor', ascending=False).head(8)
    
    # Crear gráfico
    fig = px.bar(
        df_filtrado,
        y=columna_categoria,
        x='Valor',
        orientation='h',
        title=f'Distribución sectorial del empleo - {periodo}',
        labels={columna_categoria: 'Sector', 'Valor': 'Empleos registrados'}
    )
    
    # Personalizar
    fig.update_layout(
        yaxis={'title': ''},
        xaxis={'title': 'Número de empleos'},
        height=400
    )
    
    return fig


# Callback para gráfico de evolución reciente
@callback(
    Output("grafico-evolucion-reciente", "figure"),
    [Input("radio-tipo-serie", "value")]
)
def actualizar_grafico_reciente(tipo_serie):
    # Seleccionar dataframe según tipo de serie
    df = df_estacional if tipo_serie == "estacional" else df_desestacionalizada
    
    if df.empty:
        return go.Figure().update_layout(title="No hay datos disponibles")
    
    # Tomar los últimos 20 trimestres
    df_reciente = df.iloc[-20:] if len(df) > 20 else df
    
    if df_reciente.empty:
        return go.Figure().update_layout(title="No hay datos recientes disponibles")
    
    # Crear gráfico combinado (línea + barras)
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Añadir línea para empleo
    fig.add_trace(
        go.Scatter(
            x=df_reciente['Período'],
            y=df_reciente['Empleo'],
            mode='lines+markers',
            name='Empleo Registrado',
            line=dict(color=colors['secondary'], width=3),
            marker=dict(size=6)
        ),
        secondary_y=False
    )
    
    # Añadir barras para variación interanual
    if 'varInteranual' in df_reciente.columns:
        fig.add_trace(
            go.Bar(
                x=df_reciente['Período'],
                y=df_reciente['varInteranual'],
                name='Var. Interanual (%)',
                marker_color=[colors['success'] if v >= 0 else colors['danger'] 
                             for v in df_reciente['varInteranual']]
            ),
            secondary_y=True
        )
    
    # Configurar ejes
    fig.update_layout(
        title="Evolución reciente del empleo registrado",
        template="plotly_white",
        xaxis_title="Período",
        legend_title="",
        hovermode="x unified",
        height=400
    )
    
    fig.update_yaxes(title_text="Empleos registrados", secondary_y=False)
    fig.update_yaxes(title_text="Variación interanual (%)", secondary_y=True)
    
    return fig

# Callback para tabla de datos
@callback(
    Output("tabla-datos", "children"),
    [Input("dropdown-periodo", "value"),
     Input("dropdown-nivel-detalle", "value")]
)
def actualizar_tabla_datos(periodo, nivel_detalle):
    # Datos sectoriales
    df_sectorial = datos.get("datos_sectoriales", pd.DataFrame())
    
    if df_sectorial.empty or not periodo:
        return html.P("No hay datos sectoriales disponibles")
    
    # Filtrar por período
    df_filtrado = df_sectorial[df_sectorial['Período'] == periodo]
    
    # Mapear nivel de detalle a fuentes
    if nivel_detalle == "grandes_divisiones":
        fuentes = ["C2.1", "C2.2"]
    elif nivel_detalle == "letra_ciiu":
        fuentes = ["C3"]
    elif nivel_detalle == "ciiu_2d":
        fuentes = ["C4"]
    else:
        fuentes = ["C2.1", "C2.2"]
    
    # Filtrar por fuentes
    if 'Fuente' in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado['Fuente'].isin(fuentes)]
    
    if df_filtrado.empty:
        return html.P(f"No hay datos para {periodo} con el nivel de detalle seleccionado")
    
    # Determinar columna de categoría
    columna_categoria = None
    for posible_col in ['Categoría', 'Sector']:
        if posible_col in df_filtrado.columns:
            columna_categoria = posible_col
            break
    
    if not columna_categoria:
        return html.P("No se pudo determinar la columna de categoría")
    
    # Limpiar y ordenar datos
    df_filtrado['Valor'] = pd.to_numeric(df_filtrado['Valor'], errors='coerce')
    df_filtrado = df_filtrado.dropna(subset=['Valor'])
    df_filtrado = df_filtrado.sort_values('Valor', ascending=False)
    
    # Calcular porcentajes
    total = df_filtrado['Valor'].sum()
    df_filtrado['Porcentaje'] = (df_filtrado['Valor'] / total) * 100
    
    # Crear tabla HTML
    tabla = html.Table([
        # Encabezado
        html.Thead(
            html.Tr([
                html.Th("Sector", style={'textAlign': 'left', 'padding': '8px', 'borderBottom': '2px solid #ddd'}),
                html.Th("Empleos", style={'textAlign': 'right', 'padding': '8px', 'borderBottom': '2px solid #ddd'}),
                html.Th("Porcentaje", style={'textAlign': 'right', 'padding': '8px', 'borderBottom': '2px solid #ddd'})
            ])
        ),
        # Cuerpo
        html.Tbody([
            html.Tr([
                html.Td(row[columna_categoria], style={'padding': '8px', 'borderBottom': '1px solid #ddd'}),
                html.Td(f"{row['Valor']:,.0f}", style={'textAlign': 'right', 'padding': '8px', 'borderBottom': '1px solid #ddd'}),
                html.Td(f"{row['Porcentaje']:.2f}%", style={'textAlign': 'right', 'padding': '8px', 'borderBottom': '1px solid #ddd'})
            ]) for _, row in df_filtrado.iterrows()
        ])
    ], style={'width': '100%', 'borderCollapse': 'collapse'})
    
    return tabla

# ------------------------------------------------------------------------------
# 6) Ejecución del servidor
# ------------------------------------------------------------------------------

if __name__ == '__main__':
    app.run_server(debug=True)
