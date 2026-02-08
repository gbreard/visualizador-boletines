"""
Tab Metodologia: referencia completa de calculo e indicadores (9 secciones).
"""

from dash import html


def create_metodologia_layout():
    """Layout completo de la tab Metodologia."""
    return html.Div([
        html.H4("Metodologia e Indicadores",
                 style={'color': '#1B2A4A', 'fontWeight': '600', 'marginBottom': '1.5rem'}),

        # 1. Introduccion
        html.Div([
            html.H5("1. Introduccion"),
            html.P([
                "Este panel utiliza datos del ",
                html.Strong("Sistema Integrado Previsional Argentino (SIPA)"),
                ", procesados trimestralmente por el Ministerio de Trabajo, Empleo y Seguridad Social (MTEySS). "
                "Los indicadores se calculan automaticamente a partir de las series de empleo registrado publicadas "
                "en los Boletines de Estadisticas Laborales."
            ]),
            html.P(
                "Los datos comprenden empleo registrado del sector privado declarado al SIPA, "
                "abarcando desde el 1er Trimestre de 1996 hasta el ultimo periodo disponible. "
                "El procesamiento incluye limpieza, estandarizacion de formatos y calculo de indicadores derivados."
            ),
        ], className="sipa-metodo-section"),

        # 2. Indicadores Principales
        html.Div([
            html.H5("2. Indicadores Principales"),

            html.Div([
                html.H6("Empleo Total (Niveles)", style={'fontWeight': '600'}),
                html.P("Cantidad absoluta de trabajadores registrados en el periodo."),
                html.Code("Empleo Total = Sum(Trabajadores registrados en SIPA)",
                           className="sipa-formula"),
            ], style={'marginBottom': '1rem'}),

            html.Div([
                html.H6("Variacion Trimestral (%)", style={'fontWeight': '600'}),
                html.P("Cambio porcentual del empleo respecto al trimestre inmediato anterior."),
                html.Code("var_trim = ((Empleo(t) - Empleo(t-1)) / Empleo(t-1)) x 100",
                           className="sipa-formula"),
                html.Small("Donde t = trimestre actual, t-1 = trimestre anterior",
                           style={'color': '#718096'}),
            ], style={'marginBottom': '1rem'}),

            html.Div([
                html.H6("Variacion Interanual (%)", style={'fontWeight': '600'}),
                html.P("Cambio porcentual respecto al mismo trimestre del ano anterior."),
                html.Code("var_yoy = ((Empleo(t) - Empleo(t-4)) / Empleo(t-4)) x 100",
                           className="sipa-formula"),
                html.Small("Donde t = trimestre actual, t-4 = mismo trimestre ano anterior",
                           style={'color': '#718096'}),
            ], style={'marginBottom': '1rem'}),

            html.Div([
                html.H6("Indice Base 100", style={'fontWeight': '600'}),
                html.P("Indice que muestra la evolucion tomando el periodo base (1er Trim 1996) como referencia."),
                html.Code("index_100 = (Empleo(t) / Empleo(base)) x 100",
                           className="sipa-formula"),
                html.Small("Periodo base: 1er Trimestre 1996",
                           style={'color': '#718096'}),
            ]),
        ], className="sipa-metodo-section"),

        # 3. Series Temporales
        html.Div([
            html.H5("3. Series Temporales"),

            html.Div([
                html.H6("Series con Estacionalidad (C1.1, C2.1)", style={'fontWeight': '600'}),
                html.P("Datos originales sin ajuste estacional. Reflejan patrones ciclicos propios de "
                       "cada periodo del ano (ej: mayor empleo en trimestres de cosecha)."),
                html.Ul([
                    html.Li("C1.1: Serie total pais con estacionalidad"),
                    html.Li("C2.1: Serie por sector economico con estacionalidad")
                ])
            ], style={'marginBottom': '1rem'}),

            html.Div([
                html.H6("Series Desestacionalizadas (C1.2, C2.2)", style={'fontWeight': '600'}),
                html.P("Datos ajustados para eliminar efectos estacionales, permitiendo observar "
                       "la tendencia subyacente del empleo."),
                html.Ul([
                    html.Li("C1.2: Serie total pais desestacionalizada"),
                    html.Li("C2.2: Serie por sector economico desestacionalizada")
                ]),
                html.Small("Metodo de ajuste: X-13ARIMA-SEATS del US Census Bureau",
                           style={'color': '#718096'})
            ]),
        ], className="sipa-metodo-section"),

        # 4. Clasificacion CIIU
        html.Div([
            html.H5("4. Clasificacion Industrial (CIIU)"),
            html.P("Los datos sectoriales se organizan segun la Clasificacion Industrial "
                   "Internacional Uniforme (CIIU Rev. 3):"),
            html.Table([
                html.Thead([
                    html.Tr([
                        html.Th("Tabla"), html.Th("Nivel"),
                        html.Th("Cantidad"), html.Th("Ejemplo")
                    ])
                ]),
                html.Tbody([
                    html.Tr([html.Td("C3"), html.Td("Letra (Secciones)"),
                             html.Td("14 sectores"), html.Td("A: Agricultura, D: Industria")]),
                    html.Tr([html.Td("C4"), html.Td("2 digitos (Divisiones)"),
                             html.Td("56 ramas"), html.Td("15: Alimentos, 24: Quimicos")]),
                    html.Tr([html.Td("C6"), html.Td("3 digitos (Grupos)"),
                             html.Td("147 ramas"), html.Td("151: Carnes, 241: Quimicos basicos")]),
                    html.Tr([html.Td("C7"), html.Td("4 digitos (Clases)"),
                             html.Td("301 ramas"), html.Td("1511: Mataderos, 2411: Quimicos basicos")])
                ])
            ], className="table table-striped",
               style={'fontSize': '0.85rem'}),
        ], className="sipa-metodo-section"),

        # 5. Clasificacion por Tamano
        html.Div([
            html.H5("5. Clasificacion por Tamano de Empresa (C5)"),
            html.P("El empleo se clasifica segun el tamano de la empresa empleadora. "
                   "Los datos se desagregan por sector economico y tamano:"),
            html.Table([
                html.Thead([html.Tr([html.Th("Categoria"), html.Th("Rango de Empleados")])]),
                html.Tbody([
                    html.Tr([html.Td(html.Strong("Microempresas")), html.Td("1 a 5 empleados")]),
                    html.Tr([html.Td(html.Strong("Pequenas")), html.Td("6 a 25 empleados")]),
                    html.Tr([html.Td(html.Strong("Medianas")), html.Td("26 a 100 empleados")]),
                    html.Tr([html.Td(html.Strong("Grandes")), html.Td("Mas de 100 empleados")])
                ])
            ], className="table table-striped",
               style={'fontSize': '0.85rem'}),
            html.P("Los sectores disponibles son: Industria, Comercio, Servicios y Total.",
                   style={'color': '#718096', 'fontSize': '0.85rem'}),
        ], className="sipa-metodo-section"),

        # 6. Indicadores Derivados
        html.Div([
            html.H5("6. Indicadores Derivados"),

            html.Div([
                html.H6("Promedio Movil 4 Trimestres (PM4T)", style={'fontWeight': '600'}),
                html.P("Suaviza fluctuaciones de corto plazo promediando los ultimos 4 trimestres."),
                html.Code("PM4T(t) = (X(t) + X(t-1) + X(t-2) + X(t-3)) / 4",
                           className="sipa-formula"),
            ], style={'marginBottom': '1rem'}),

            html.Div([
                html.H6("Participacion Sectorial", style={'fontWeight': '600'}),
                html.P("Peso relativo de cada sector en el empleo total del periodo."),
                html.Code("Participacion(s,t) = Empleo(s,t) / Empleo(total,t) x 100",
                           className="sipa-formula"),
            ], style={'marginBottom': '1rem'}),

            html.Div([
                html.H6("Deteccion de Anomalias", style={'fontWeight': '600'}),
                html.P("Valores atipicos identificados por desviacion respecto a la media movil."),
                html.Code("Outlier = |X(t) - media_movil(8T)| > k x sigma_movil(8T)",
                           className="sipa-formula"),
                html.Small("Donde k = 2 (factor de desviacion estandar)",
                           style={'color': '#718096'}),
            ]),
        ], className="sipa-metodo-section"),

        # 7. Sistema de Alertas
        html.Div([
            html.H5("7. Sistema de Alertas"),
            html.P("El sistema monitorea automaticamente los datos y genera alertas "
                   "en cuatro categorias:"),

            html.Div([
                html.Div([
                    html.Span("CRITICA", className="sipa-badge sipa-badge-danger"),
                    html.Span(" - Variacion trimestral > umbral o caida interanual severa",
                              style={'fontSize': '0.85rem'}),
                ], style={'marginBottom': '0.5rem'}),
                html.Div([
                    html.Span("ADVERTENCIA", className="sipa-badge sipa-badge-warning"),
                    html.Span(" - Variacion moderada o cambio de tendencia detectado",
                              style={'fontSize': '0.85rem'}),
                ], style={'marginBottom': '0.5rem'}),
                html.Div([
                    html.Span("POSITIVA", className="sipa-badge sipa-badge-success"),
                    html.Span(" - Crecimiento robusto o creacion significativa de empleos",
                              style={'fontSize': '0.85rem'}),
                ], style={'marginBottom': '0.5rem'}),
                html.Div([
                    html.Span("INFORMATIVA", className="sipa-badge sipa-badge-info"),
                    html.Span(" - Maximos historicos, variaciones sectoriales notables",
                              style={'fontSize': '0.85rem'}),
                ], style={'marginBottom': '1rem'}),
            ]),

            html.H6("Umbrales configurables", style={'fontWeight': '600'}),
            html.P("En la tab Alertas se pueden ajustar:"),
            html.Ul([
                html.Li("Umbral de variacion trimestral (default: 5%)"),
                html.Li("Umbral de variacion interanual (default: 10%)"),
            ]),
            html.P("Las alertas sectoriales utilizan multiplicadores sobre estos umbrales: "
                   "crisis sectorial cuando la caida supera 1.5x el umbral interanual.",
                   style={'color': '#718096', 'fontSize': '0.85rem'}),
        ], className="sipa-metodo-section"),

        # 8. Fuentes y Actualizacion
        html.Div([
            html.H5("8. Fuentes y Actualizacion"),
            html.Div([
                html.Div([
                    html.Strong("Fuente primaria: "),
                    html.Span("Sistema Integrado Previsional Argentino (SIPA)")
                ], style={'marginBottom': '0.5rem'}),
                html.Div([
                    html.Strong("Procesamiento: "),
                    html.Span("Ministerio de Trabajo, Empleo y Seguridad Social (MTEySS)")
                ], style={'marginBottom': '0.5rem'}),
                html.Div([
                    html.Strong("Periodicidad: "),
                    html.Span("Trimestral (con rezago de 2-3 meses respecto al cierre del trimestre)")
                ], style={'marginBottom': '0.5rem'}),
                html.Div([
                    html.Strong("Cobertura temporal: "),
                    html.Span("Desde 1er Trimestre 1996 hasta ultimo boletin publicado")
                ], style={'marginBottom': '0.5rem'}),
                html.Div([
                    html.Strong("Formatos disponibles: "),
                    html.Span("Parquet (optimizado), CSV (compatible), Excel (fuente original)")
                ]),
            ]),
        ], className="sipa-metodo-section"),

        # 9. Notas Tecnicas y Glosario
        html.Div([
            html.H5("9. Notas Tecnicas y Glosario"),

            html.H6("Notas Tecnicas", style={'fontWeight': '600', 'marginBottom': '0.5rem'}),
            html.Ul([
                html.Li("Los datos corresponden unicamente al empleo registrado (formal) del sector privado"),
                html.Li("No incluye empleo publico provincial ni municipal"),
                html.Li("Las series pueden tener revisiones retroactivas por parte del organismo fuente"),
                html.Li("Valores faltantes se indican como 's.d.' en archivos fuente y se tratan como nulos"),
                html.Li("El ajuste estacional es realizado por el organismo fuente, no por este panel"),
            ]),

            html.H6("Glosario", style={'fontWeight': '600', 'marginTop': '1rem', 'marginBottom': '0.5rem'}),
            html.Dl([
                html.Dt("SIPA"), html.Dd("Sistema Integrado Previsional Argentino"),
                html.Dt("CIIU"), html.Dd("Clasificacion Industrial Internacional Uniforme (Rev. 3)"),
                html.Dt("MTEySS"), html.Dd("Ministerio de Trabajo, Empleo y Seguridad Social"),
                html.Dt("Empleo Registrado"),
                html.Dd("Trabajadores con aportes declarados al sistema de seguridad social"),
                html.Dt("Desestacionalizacion"),
                html.Dd("Proceso estadistico para remover patrones estacionales recurrentes de una serie temporal"),
                html.Dt("X-13ARIMA-SEATS"),
                html.Dd("Metodo de ajuste estacional desarrollado por el US Census Bureau, estandar internacional"),
            ]),
        ], className="sipa-metodo-section"),

    ], style={'maxWidth': '900px', 'margin': '0 auto'})
