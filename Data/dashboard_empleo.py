import dash
from dash import dcc, html, callback, Input, Output, State
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import os
import re

# ------------------------------------------------------------------------------
# 1) Funciones de carga y procesamiento de datos
# ------------------------------------------------------------------------------

def cargar_datos(directorio="datos_procesados"):
    """
    Carga los archivos CSV generados por el script de preprocesamiento.
    Retorna un diccionario con los DataFrames correspondientes.
    """
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

def preparar_series_temporales(df):
    """
    Prepara los datos de series temporales para la visualización.
    """
    if df.empty:
        return df
    
    # Asegurarse de que tenemos las columnas necesarias
    if not all(col in df.columns for col in ["Período", "Empleo"]):
        return df
    
    # Convertir "Período" a datetime (esto puede requerir preprocesamiento adicional)
    try:
        # Extraer año y trimestre
        df['Año'] = df['Período'].str.extract(r'(\d{4})').astype(int)
        df['Trimestre'] = df['Período'].str.extract(r'([1-4])').astype(int)
        
        # Crear fecha representativa para cada trimestre (primer día del trimestre)
        df['Fecha'] = pd.to_datetime(df['Año'].astype(str) + '-' + 
                                     ((df['Trimestre'] * 3) - 2).astype(str) + '-01')
        
        # Ordenar por fecha
        df = df.sort_values('Fecha')
    except Exception as e:
        print(f"Error al procesar fechas: {e}")
    
    return df

def preparar_datos_sectoriales(df):
    """
    Prepara los datos sectoriales para la visualización.
    """
    if df.empty:
        return df
    
    # Asegurarse de que tenemos las columnas necesarias
    required_cols = ["Período", "Categoría", "Valor"]
    if not all(col in df.columns for col in required_cols):
        return df
    
    # Convertir "Valor" a numérico
    df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce")
    
    # Filtrar valores nulos
    df = df.dropna(subset=["Valor"])
    
    return df

def extraer_periodos_disponibles(df):
    """
    Extrae la lista de períodos únicos ordenados cronológicamente.
    """
    if df.empty or "Período" not in df.columns:
        return []
    
    # Extraer períodos únicos
    periodos = df["Período"].unique().tolist()
    
    # Función para ordenar períodos
    def orden_periodo(periodo):
        # Extraer año y trimestre
        match_year = re.search(r'(\d{4})', periodo)
        match_trim = re.search(r'([1-4])', periodo)
        
        if match_year and match_trim:
            year = int(match_year.group(1))
            trim = int(match_trim.group(1))
            return year * 10 + trim
        return 0
    
    # Ordenar períodos cronológicamente
    periodos_ordenados = sorted(periodos, key=orden_periodo)
    return periodos_ordenados

def extraer_sectores_disponibles(df):
    """
    Extrae la lista de sectores/categorías únicos.
    """
    if df.empty:
        return []
    
    # Determinar la columna que contiene los sectores
    columna_sector = next((col for col in ["Categoría", "Sector"] if col in df.columns), None)
    
    if columna_sector is None:
        return []
    
    # Extraer sectores únicos y ordenarlos alfabéticamente
    sectores = sorted(df[columna_sector].unique().tolist())
    return sectores

# ------------------------------------------------------------------------------
# 2) Configuración de la aplicación Dash
# ------------------------------------------------------------------------------

# Inicializar la aplicación Dash
app = dash.Dash(__name__, 
                title="Dashboard de Empleo Registrado en Argentina",
                meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}])

# Cargar datos
datos = cargar_datos()

# Preparar datos para visualización
df_series = preparar_series_temporales(datos.get("series_temporales", pd.DataFrame()))
df_sectores = preparar_datos_sectoriales(datos.get("datos_sectoriales", pd.DataFrame()))

# Extraer períodos y sectores disponibles
periodos_disponibles = extraer_periodos_disponibles(df_series)
sectores_disponibles = extraer_sectores_disponibles(df_sectores)

# ------------------------------------------------------------------------------
# 3) Diseño del layout de la aplicación
# ------------------------------------------------------------------------------

app.layout = html.Div([
    # Encabezado
    html.Div([
        html.H1("Dashboard de Empleo Registrado en Argentina (1996-2024)", 
                className="header-title"),
        html.P("Análisis de datos del Ministerio de Trabajo, Empleo y Seguridad Social",
               className="header-description")
    ], className="header"),
    
    # Contenedor principal
    html.Div([
        # Sección 1: Evolución temporal del empleo total
        html.Div([
            html.H2("Evolución del Empleo Registrado", className="section-title"),
            
            # Controles de filtrado
            html.Div([
                html.Label("Seleccionar serie:"),
                dcc.Dropdown(
                    id="dropdown-serie",
                    options=[
                        {"label": "Serie con estacionalidad", "value": "estacional"},
                        {"label": "Serie desestacionalizada", "value": "desestacionalizada"}
                    ],
                    value="desestacionalizada",
                    clearable=False
                )
            ], className="control-group"),
            
            # Gráfico de evolución temporal
            dcc.Graph(id="grafico-evolucion"),
            
            # Indicadores clave
            html.Div([
                html.Div([
                    html.H4("Empleos actuales"),
                    html.P(id="indicador-empleo-actual", className="indicator-value")
                ], className="indicator"),
                html.Div([
                    html.H4("Variación interanual"),
                    html.P(id="indicador-var-interanual", className="indicator-value")
                ], className="indicator"),
                html.Div([
                    html.H4("Máximo histórico"),
                    html.P(id="indicador-maximo", className="indicator-value")
                ], className="indicator")
            ], className="indicators-container")
        ], className="card"),
        
        # Sección 2: Composición sectorial
        html.Div([
            html.H2("Composición Sectorial", className="section-title"),
            
            # Controles de filtrado
            html.Div([
                html.Label("Seleccionar período:"),
                dcc.Dropdown(
                    id="dropdown-periodo",
                    options=[{"label": p, "value": p} for p in periodos_disponibles[-20:]], # Últimos 20 períodos
                    value=periodos_disponibles[-1] if periodos_disponibles else None,
                    clearable=False
                ),
                html.Label("Nivel de detalle:"),
                dcc.Dropdown(
                    id="dropdown-detalle",
                    options=[
                        {"label": "Grandes divisiones", "value": "grandes_divisiones"},
                        {"label": "Letra CIIU", "value": "letra_ciiu"},
                        {"label": "2 dígitos CIIU", "value": "ciiu_2d"}
                    ],
                    value="grandes_divisiones",
                    clearable=False
                )
            ], className="control-group"),
            
            # Gráfico de composición sectorial
            dcc.Graph(id="grafico-sectorial"),
            
            # Tabla de distribución sectorial
            html.Div(id="tabla-sectorial", className="data-table")
        ], className="card"),
        
        # Sección 3: Evolución sectorial
        html.Div([
            html.H2("Evolución por Sector", className="section-title"),
            
            # Controles de filtrado
            html.Div([
                html.Label("Seleccionar sectores:"),
                dcc.Dropdown(
                    id="dropdown-sectores",
                    options=[{"label": s, "value": s} for s in sectores_disponibles[:10]], # Primeros 10 sectores
                    value=sectores_disponibles[:3] if len(sectores_disponibles) >= 3 else sectores_disponibles,
                    multi=True
                ),
                html.Label("Rango de años:"),
                dcc.RangeSlider(
                    id="slider-anios",
                    min=1996,
                    max=2024,
                    step=1,
                    marks={i: str(i) for i in range(1996, 2025, 4)},
                    value=[2015, 2024]
                )
            ], className="control-group"),
            
            # Gráfico de evolución sectorial
            dcc.Graph(id="grafico-evolucion-sectorial"),
        ], className="card"),
        
        # Sección 4: Variación interanual
        html.Div([
            html.H2("Variación Interanual", className="section-title"),
            
            # Controles de filtrado
            html.Div([
                html.Label("Seleccionar períodos de comparación:"),
                dcc.Dropdown(
                    id="dropdown-periodo-actual",
                    options=[{"label": p, "value": p} for p in periodos_disponibles[-8:]], # Últimos 8 períodos
                    value=periodos_disponibles[-1] if periodos_disponibles else None,
                    placeholder="Período actual",
                    clearable=False
                ),
                dcc.Dropdown(
                    id="dropdown-periodo-anterior",
                    options=[{"label": p, "value": p} for p in periodos_disponibles[-12:-4]], # Períodos anteriores
                    value=periodos_disponibles[-5] if len(periodos_disponibles) >= 5 else None,
                    placeholder="Período de comparación",
                    clearable=False
                )
            ], className="control-group"),
            
            # Gráfico de variación interanual
            dcc.Graph(id="grafico-variacion-interanual"),
        ], className="card"),
    ], className="main-container"),
    
    # Pie de página
    html.Footer([
        html.P("Fuente: Ministerio de Trabajo, Empleo y Seguridad Social de Argentina"),
        html.P("Dashboard desarrollado con Dash y Plotly")
    ], className="footer")
])

# ------------------------------------------------------------------------------
# 4) Callbacks para la interactividad
# ------------------------------------------------------------------------------

@callback(
    Output("grafico-evolucion", "figure"),
    [Input("dropdown-serie", "value")]
)
def actualizar_grafico_evolucion(tipo_serie):
    """
    Actualiza el gráfico de evolución temporal según la serie seleccionada.
    """
    if df_series.empty:
        return go.Figure().update_layout(title="No hay datos disponibles")
    
    # Filtrar por tipo de serie (con estacionalidad o desestacionalizada)
    filtro_serie = "Con estacionalidad" if tipo_serie == "estacional" else "Desestacionalizada"
    fuentes_filtradas = datos["metadatos"][datos["metadatos"]["TipoSerie"] == filtro_serie]["Sheet"].tolist()
    
    # Si no hay datos específicos, usar todos los datos
    if not fuentes_filtradas:
        df_filtrado = df_series
    else:
        df_filtrado = df_series[df_series["Fuente"].isin(fuentes_filtradas)]
    
    # Si aún así no hay datos, usar el DataFrame completo
    if df_filtrado.empty:
        df_filtrado = df_series
    
    # Crear gráfico
    fig = px.line(
        df_filtrado, 
        x="Fecha" if "Fecha" in df_filtrado.columns else "Período", 
        y="Empleo",
        title=f"Evolución del empleo registrado en el sector privado - Serie {filtro_serie.lower()}",
        labels={"Empleo": "Cantidad de empleos", "Fecha": "Período"}
    )
    
    # Personalizar diseño
    fig.update_layout(
        template="plotly_white",
        hovermode="x unified",
        xaxis_title="Período",
        yaxis_title="Empleos registrados",
        legend_title="",
        margin=dict(l=40, r=40, t=60, b=40),
    )
    
    # Añadir marcas para crisis económicas
    crisis = [
        {"año": "2001-12-01", "nombre": "Crisis 2001"},
        {"año": "2008-09-01", "nombre": "Crisis 2008"},
        {"año": "2018-08-01", "nombre": "Crisis 2018"},
        {"año": "2020-03-01", "nombre": "COVID-19"}
    ]
    
    for c in crisis:
        fig.add_vline(
            x=c["año"], 
            line_width=1, 
            line_dash="dash", 
            line_color="gray",
            annotation_text=c["nombre"],
            annotation_position="top right"
        )
    
    return fig

@callback(
    [Output("indicador-empleo-actual", "children"),
     Output("indicador-var-interanual", "children"),
     Output("indicador-maximo", "children")],
    [Input("dropdown-serie", "value")]
)
def actualizar_indicadores(tipo_serie):
    """
    Actualiza los indicadores clave según la serie seleccionada.
    """
    if df_series.empty:
        return "No disponible", "No disponible", "No disponible"
    
    # Filtrar por tipo de serie
    filtro_serie = "Con estacionalidad" if tipo_serie == "estacional" else "Desestacionalizada"
    fuentes_filtradas = datos["metadatos"][datos["metadatos"]["TipoSerie"] == filtro_serie]["Sheet"].tolist()
    
    if not fuentes_filtradas:
        df_filtrado = df_series
    else:
        df_filtrado = df_series[df_series["Fuente"].isin(fuentes_filtradas)]
    
    if df_filtrado.empty:
        df_filtrado = df_series
    
    # Ordenar por fecha o período
    if "Fecha" in df_filtrado.columns:
        df_filtrado = df_filtrado.sort_values("Fecha")
    else:
        # Ordenar por período si no hay columna de fecha
        def extraer_anio_trim(periodo):
            match_year = re.search(r'(\d{4})', str(periodo))
            match_trim = re.search(r'([1-4])', str(periodo))
            if match_year and match_trim:
                return int(match_year.group(1)) * 10 + int(match_trim.group(1))
            return 0
        
        df_filtrado["orden"] = df_filtrado["Período"].apply(extraer_anio_trim)
        df_filtrado = df_filtrado.sort_values("orden")
    
    # Obtener último valor
    ultimo_periodo = df_filtrado.iloc[-1]
    empleo_actual = ultimo_periodo["Empleo"]
    
    # Obtener variación interanual (si está disponible)
    if "varInteranual" in ultimo_periodo and pd.notna(ultimo_periodo["varInteranual"]):
        var_interanual = ultimo_periodo["varInteranual"] * 100  # Convertir a porcentaje
    else:
        # Calcular manualmente si es posible
        try:
            # Buscar el mismo trimestre del año anterior
            periodo_actual = ultimo_periodo["Período"]
            match_actual = re.search(r'([1-4]).*?(\d{4})', str(periodo_actual))
            
            if match_actual:
                trim_actual = match_actual.group(1)
                anio_actual = int(match_actual.group(2))
                anio_anterior = anio_actual - 1
                
                # Buscar el mismo trimestre del año anterior
                patron_anterior = f"{trim_actual}.*?{anio_anterior}"
                periodos_anteriores = df_filtrado[df_filtrado["Período"].str.contains(patron_anterior, regex=True)]
                
                if not periodos_anteriores.empty:
                    empleo_anterior = periodos_anteriores.iloc[-1]["Empleo"]
                    var_interanual = ((empleo_actual / empleo_anterior) - 1) * 100
                else:
                    var_interanual = None
            else:
                var_interanual = None
        except Exception:
            var_interanual = None
    
    # Obtener máximo histórico
    maximo = df_filtrado["Empleo"].max()
    periodo_maximo = df_filtrado[df_filtrado["Empleo"] == maximo].iloc[0]["Período"]
    
    # Formatear valores
    empleo_actual_str = f"{empleo_actual:,.0f}"
    
    if var_interanual is not None:
        var_interanual_str = f"{var_interanual:.2f}%"
        # Añadir color según el valor
        var_interanual_str = f'<span style="color:{"green" if var_interanual >= 0 else "red"}">{var_interanual_str}</span>'
    else:
        var_interanual_str = "No disponible"
    
    maximo_str = f"{maximo:,.0f} ({periodo_maximo})"
    
    return empleo_actual_str, html.Span([var_interanual_str], dangerously_set_inner_html=True), maximo_str

@callback(
    Output("grafico-sectorial", "figure"),
    [Input("dropdown-periodo", "value"),
     Input("dropdown-detalle", "value")]
)
def actualizar_grafico_sectorial(periodo, nivel_detalle):
    """
    Actualiza el gráfico de composición sectorial según el período y nivel de detalle.
    """
    if df_sectores.empty or not periodo:
        return go.Figure().update_layout(title="No hay datos disponibles")
    
    # Filtrar por período
    df_filtrado = df_sectores[df_sectores["Período"] == periodo]
    
    # Filtrar por nivel de detalle
    if nivel_detalle == "grandes_divisiones":
        # Usar datos de hojas C2.1 o C2.2
        fuentes_objetivo = ["C2.1", "C2.2"]
        df_filtrado = df_filtrado[df_filtrado["Fuente"].isin(fuentes_objetivo)]
    elif nivel_detalle == "letra_ciiu":
        # Usar datos de hoja C3
        df_filtrado = df_filtrado[df_filtrado["Fuente"] == "C3"]
    elif nivel_detalle == "ciiu_2d":
        # Usar datos de hoja C4
        df_filtrado = df_filtrado[df_filtrado["Fuente"] == "C4"]
    
    if df_filtrado.empty:
        return go.Figure().update_layout(title=f"No hay datos para {periodo} con el nivel de detalle seleccionado")
    
    # Columna para categoría/sector
    col_categoria = next((c for c in ["Categoría", "Sector"] if c in df_filtrado.columns), None)
    
    if not col_categoria:
        return go.Figure().update_layout(title="No se pudo identificar la columna de categoría")
    
    # Ordenar por valor descendente y tomar los 10 primeros
    df_filtrado = df_filtrado.sort_values("Valor", ascending=False).head(10)
    
    # Calcular porcentajes
    total = df_filtrado["Valor"].sum()
    df_filtrado["Porcentaje"] = df_filtrado["Valor"] / total * 100
    
    # Crear gráfico de barras
    fig = px.bar(
        df_filtrado,
        y=col_categoria,
        x="Valor",
        title=f"Distribución sectorial del empleo - {periodo}",
        labels={col_categoria: "Sector", "Valor": "Empleos registrados"},
        text="Porcentaje",
        orientation="h"
    )
    
    # Personalizar diseño
    fig.update_layout(
        template="plotly_white",
        xaxis_title="Cantidad de empleos",
        yaxis_title="",
        yaxis=dict(autorange="reversed"),  # Invertir eje Y para mostrar mayor valor arriba
        margin=dict(l=40, r=40, t=60, b=40),
    )
    
    # Personalizar formato de texto
    fig.update_traces(
        texttemplate="%{text:.1f}%",
        textposition="outside",
    )
    
    return fig

@callback(
    Output("tabla-sectorial", "children"),
    [Input("dropdown-periodo", "value"),
     Input("dropdown-detalle", "value")]
)
def actualizar_tabla_sectorial(periodo, nivel_detalle):
    """
    Actualiza la tabla de distribución sectorial según el período y nivel de detalle.
    """
    if df_sectores.empty or not periodo:
        return html.P("No hay datos disponibles")
    
    # Filtrar por período y nivel
    df_filtrado = df_sectores[df_sectores["Período"] == periodo]
    
    if nivel_detalle == "grandes_divisiones":
        fuentes_objetivo = ["C2.1", "C2.2"]
        df_filtrado = df_filtrado[df_filtrado["Fuente"].isin(fuentes_objetivo)]
    elif nivel_detalle == "letra_ciiu":
        df_filtrado = df_filtrado[df_filtrado["Fuente"] == "C3"]
    elif nivel_detalle == "ciiu_2d":
        df_filtrado = df_filtrado[df_filtrado["Fuente"] == "C4"]
    
    if df_filtrado.empty:
        return html.P(f"No hay datos para {periodo} con el nivel de detalle seleccionado")
    
    # Columna para categoría/sector
    col_categoria = next((c for c in ["Categoría", "Sector"] if c in df_filtrado.columns), None)
    
    if not col_categoria:
        return html.P("No se pudo identificar la columna de categoría")
    
    # Ordenar por valor descendente
    df_filtrado = df_filtrado.sort_values("Valor", ascending=False)
    
    # Calcular porcentajes
    total = df_filtrado["Valor"].sum()
    df_filtrado["Porcentaje"] = df_filtrado["Valor"] / total * 100
    
    # Crear tabla HTML
    tabla = html.Table([
        html.Thead(
            html.Tr([
                html.Th("Sector"),
                html.Th("Empleos"),
                html.Th("Porcentaje")
            ])
        ),
        html.Tbody([
            html.Tr([
                html.Td(row[col_categoria]),
                html.Td(f"{row['Valor']:,.0f}"),
                html.Td(f"{row['Porcentaje']:.2f}%")
            ]) for _, row in df_filtrado.iterrows()
        ])
    ], className="table")
    
    return tabla

@callback(
    Output("grafico-evolucion-sectorial", "figure"),
    [Input("dropdown-sectores", "value"),
     Input("slider-anios", "value")]
)
def actualizar_grafico_evolucion_sectorial(sectores, rango_anios):
    """
    Actualiza el gráfico de evolución sectorial según los sectores seleccionados y rango de años.
    """
    if df_sectores.empty or not sectores:
        return go.Figure().update_layout(title="No hay datos disponibles")
    
    # Columna para categoría/sector
    col_categoria = next((c for c in ["Categoría", "Sector"] if c in df_sectores.columns), None)
    
    if not col_categoria:
        return go.Figure().update_layout(title="No se pudo identificar la columna de categoría")
    
    # Filtrar por sectores seleccionados
    df_filtrado = df_sectores[df_sectores[col_categoria].isin(sectores)]
    
    # Filtrar por rango de años
    if "Año" in df_filtrado.columns:
        df_filtrado = df_filtrado[(df_filtrado["Año"] >= rango_anios[0]) & (df_filtrado["Año"] <= rango_anios[1])]
    else:
        # Filtrar por año en el campo período
        df_filtrado = df_filtrado[df_filtrado["Período"].str.contains(f'({"|".join(str(year) for year in range(rango_anios[0], rango_anios[1]+1))})')]
    
    if df_filtrado.empty:
        return go.Figure().update_layout(title="No hay datos para los filtros seleccionados")
    
    # Crear gráfico de líneas
    fig = px.line(
        df_filtrado,
        x="Período",
        y="Valor",
        color=col_categoria,
        title=f"Evolución del empleo por sector ({rango_anios[0]}-{rango_anios[1]})",
        labels={"Valor": "Empleos registrados", "Período": "Período"}
    )
    
    # Personalizar diseño
    fig.update_layout(
        template="plotly_white",
        hovermode="x unified",
        xaxis_title="Período",
        yaxis_title="Empleos registrados",
        legend_title="Sector",
        margin=dict(l=40, r=40, t=60, b=40)
    )
    
    return fig

@callback(
    Output("grafico-variacion-interanual", "figure"),
    [Input("dropdown-periodo-actual", "value"),
     Input("dropdown-periodo-anterior", "value")]
)
def actualizar_grafico_variacion_interanual(periodo_actual, periodo_anterior):
    """
    Actualiza el gráfico de variación interanual entre períodos seleccionados.
    """
    if df_sectores.empty or not periodo_actual or not periodo_anterior:
        return go.Figure().update_layout(title="No hay datos disponibles")
    
    # Columna para categoría/sector
    col_categoria = next((c for c in ["Categoría", "Sector"] if c in df_sectores.columns), None)
    
    if not col_categoria:
        return go.Figure().update_layout(title="No se pudo identificar la columna de categoría")
    
    # Filtrar por los períodos seleccionados y nivel (grandes divisiones)
    fuentes_objetivo = ["C2.1", "C2.2"]
    df_actual = df_sectores[(df_sectores["Período"] == periodo_actual) & 
                          (df_sectores["Fuente"].isin(fuentes_objetivo))]
    
    df_anterior = df_sectores[(df_sectores["Período"] == periodo_anterior) & 
                           (df_sectores["Fuente"].isin(fuentes_objetivo))]
    
    if df_actual.empty or df_anterior.empty:
        return go.Figure().update_layout(title="No hay datos suficientes para la comparación")
    
    # Combinar datos actuales y anteriores
    df_combo = pd.merge(
        df_actual[[col_categoria, "Valor"]],
        df_anterior[[col_categoria, "Valor"]],
        on=col_categoria,
        suffixes=("_actual", "_anterior"),
        how="inner"
    )
    
    # Calcular variación
    df_combo["variacion"] = ((df_combo["Valor_actual"] / df_combo["Valor_anterior"]) - 1) * 100
    
    # Ordenar por variación
    df_combo = df_combo.sort_values("variacion")
    
    # Crear gráfico de barras horizontales
    fig = px.bar(
        df_combo,
        y=col_categoria,
        x="variacion",
        title=f"Variación interanual del empleo por sector ({periodo_anterior} vs {periodo_actual})",
        labels={col_categoria: "Sector", "variacion": "Variación (%)"},
        orientation="h"
    )
    
    # Personalizar diseño
    fig.update_layout(
        template="plotly_white",
        xaxis_title="Variación porcentual (%)",
        yaxis_title="",
        xaxis=dict(tickformat=".1f"),
        margin=dict(l=40, r=40, t=60, b=40)
    )
    
    # Añadir colores según valor (positivo o negativo)
    fig.update_traces(
        marker_color=["green" if x >= 0 else "red" for x in df_combo["variacion"]],
        texttemplate="%{x:.1f}%",
        textposition="outside"
    )
    
    # Añadir línea vertical en cero
    fig.add_vline(x=0, line_width=1, line_dash="solid", line_color="gray")
    
    return fig

# ------------------------------------------------------------------------------
# 5) Estilos CSS y Ejecutar la aplicación
# ------------------------------------------------------------------------------

# Definir estilos CSS
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            /* Estilos generales */
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 0;
                background-color: #f5f5f5;
                color: #333;
            }
            
            /* Encabezado */
            .header {
                background-color: #2c3e50;
                color: white;
                padding: 20px;
                text-align: center;
                margin-bottom: 20px;
            }
            
            .header-title {
                margin: 0;
                font-size: 24px;
                font-weight: 600;
            }
            
            .header-description {
                margin: 10px 0 0 0;
                font-size: 16px;
                opacity: 0.9;
            }
            
            /* Contenedor principal */
            .main-container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 0 20px;
                display: grid;
                grid-template-columns: 1fr;
                gap: 20px;
            }
            
            /* Tarjetas */
            .card {
                background-color: white;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                padding: 20px;
                margin-bottom: 20px;
            }
            
            .section-title {
                margin-top: 0;
                margin-bottom: 20px;
                font-size: 20px;
                color: #2c3e50;
                border-bottom: 1px solid #eee;
                padding-bottom: 10px;
            }
            
            /* Controles */
            .control-group {
                margin-bottom: 20px;
                display: flex;
                flex-wrap: wrap;
                gap: 15px;
                align-items: center;
            }
            
            .control-group label {
                font-weight: 600;
                margin-right: 10px;
                width: 150px;
            }
            
            /* Indicadores */
            .indicators-container {
                display: flex;
                justify-content: space-between;
                flex-wrap: wrap;
                margin-top: 20px;
            }
            
            .indicator {
                flex: 1;
                min-width: 150px;
                padding: 15px;
                text-align: center;
                border-right: 1px solid #eee;
            }
            
            .indicator:last-child {
                border-right: none;
            }
            
            .indicator h4 {
                margin: 0;
                font-size: 14px;
                color: #7f8c8d;
            }
            
            .indicator-value {
                margin: 10px 0 0 0;
                font-size: 20px;
                font-weight: 600;
                color: #2980b9;
            }
            
            /* Tabla de datos */
            .data-table {
                margin-top: 20px;
                overflow-x: auto;
            }
            
            .table {
                width: 100%;
                border-collapse: collapse;
            }
            
            .table th,
            .table td {
                padding: 10px;
                text-align: left;
                border-bottom: 1px solid #eee;
            }
            
            .table th {
                background-color: #f9f9f9;
                font-weight: 600;
            }
            
            /* Pie de página */
            .footer {
                text-align: center;
                padding: 20px;
                margin-top: 40px;
                background-color: #34495e;
                color: white;
            }
            
            .footer p {
                margin: 5px 0;
                font-size: 14px;
            }
            
            /* Responsive */
            @media screen and (max-width: 768px) {
                .main-container {
                    padding: 0 10px;
                }
                
                .card {
                    padding: 15px;
                }
                
                .indicators-container {
                    flex-direction: column;
                }
                
                .indicator {
                    border-right: none;
                    border-bottom: 1px solid #eee;
                    padding: 10px;
                }
                
                .indicator:last-child {
                    border-bottom: none;
                }
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# ------------------------------------------------------------------------------
# 6) Ejecutar la aplicación
# ------------------------------------------------------------------------------

if __name__ == '__main__':
    app.run_server(debug=True)