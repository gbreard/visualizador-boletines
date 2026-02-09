"""
Tab Metodologia: referencia completa de calculo, fuentes e indicadores.
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
                "Este panel integra datos del ",
                html.Strong("Observatorio de Empleo y Dinamica Empresarial (OEDE)"),
                " del Ministerio de Trabajo, Empleo y Seguridad Social (MTEySS), "
                "basados en registros administrativos del ",
                html.Strong("Sistema Integrado Previsional Argentino (SIPA)"),
                ". Se procesan automaticamente 7 archivos Excel del OEDE y una serie de IPC, "
                "generando 26 datasets que cubren empleo, remuneraciones (nominales y reales), "
                "empresas, flujos laborales y genero."
            ]),
            html.P(
                "Los datos comprenden empleo registrado del sector privado declarado al SIPA. "
                "El procesamiento incluye descarga automatica, limpieza, estandarizacion de formatos "
                "y calculo de indicadores derivados."
            ),
        ], className="sipa-metodo-section"),

        # 2. Fuentes de Datos
        html.Div([
            html.H5("2. Fuentes de Datos OEDE"),
            html.P("El sistema descarga y procesa 7 archivos Excel del OEDE mas una serie de IPC:"),
            html.Table([
                html.Thead([
                    html.Tr([
                        html.Th("Fuente"), html.Th("Frecuencia"),
                        html.Th("Datasets"), html.Th("Contenido")
                    ])
                ]),
                html.Tbody([
                    html.Tr([
                        html.Td("Empleo Trimestral"), html.Td("Trimestral"),
                        html.Td("C1.1 a C7"), html.Td("Empleo registrado total, por sector CIIU y tamano")
                    ]),
                    html.Tr([
                        html.Td("Remuneraciones Mensual"), html.Td("Mensual"),
                        html.Td("R1 a R4"), html.Td("Remuneracion promedio y mediana, total y por sector")
                    ]),
                    html.Tr([
                        html.Td("Empresas Anual"), html.Td("Anual"),
                        html.Td("E1, E2"), html.Td("Cantidad de empresas registradas, total y por sector")
                    ]),
                    html.Tr([
                        html.Td("Flujos de Empleo"), html.Td("Trimestral"),
                        html.Td("F1 a F3"), html.Td("Altas, bajas, creacion neta y tasas de rotacion")
                    ]),
                    html.Tr([
                        html.Td("Genero"), html.Td("Trimestral"),
                        html.Td("G1, G2"), html.Td("Empleo y remuneracion por sexo, brecha salarial")
                    ]),
                    html.Tr([
                        html.Td("IPC Empalmado"), html.Td("Mensual"),
                        html.Td("IPC"), html.Td("Indice de precios al consumidor (base Ene 2016=100)")
                    ]),
                ])
            ], className="table table-striped",
               style={'fontSize': '0.85rem'}),
            html.Small(
                "Fuentes: OEDE (argentina.gob.ar/trabajo/estadisticas/oede) | "
                "IPC empalmado (github.com/matuteiglesias/IPC-Argentina)",
                style={'color': '#718096'}
            ),
        ], className="sipa-metodo-section"),

        # 3. Indicadores de Empleo
        html.Div([
            html.H5("3. Indicadores de Empleo (C1-C7)"),

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
            ], style={'marginBottom': '1rem'}),

            html.Div([
                html.H6("Variacion Interanual (%)", style={'fontWeight': '600'}),
                html.P("Cambio porcentual respecto al mismo trimestre del ano anterior."),
                html.Code("var_yoy = ((Empleo(t) - Empleo(t-4)) / Empleo(t-4)) x 100",
                           className="sipa-formula"),
            ], style={'marginBottom': '1rem'}),

            html.Div([
                html.H6("Indice Base 100", style={'fontWeight': '600'}),
                html.P("Evolucion tomando el periodo base (1er Trim 1996) como referencia."),
                html.Code("index_100 = (Empleo(t) / Empleo(base)) x 100",
                           className="sipa-formula"),
                html.Small("Periodo base: 1er Trimestre 1996", style={'color': '#718096'}),
            ]),
        ], className="sipa-metodo-section"),

        # 4. Indicadores de Remuneraciones
        html.Div([
            html.H5("4. Indicadores de Remuneraciones (R1-R4)"),

            html.Div([
                html.H6("Remuneracion Promedio (R1, R3)", style={'fontWeight': '600'}),
                html.P("Remuneracion bruta promedio por todo concepto del total de trabajadores "
                       "registrados del sector privado. R1 es el total nacional, R3 desagrega por "
                       "los 14 sectores CIIU."),
                html.Code("Rem_promedio = Sum(Remuneraciones) / N(trabajadores)",
                           className="sipa-formula"),
                html.Small("Valores a pesos corrientes (nominales)", style={'color': '#718096'}),
            ], style={'marginBottom': '1rem'}),

            html.Div([
                html.H6("Remuneracion Mediana (R2, R4)", style={'fontWeight': '600'}),
                html.P("Valor que divide la distribucion de remuneraciones en dos mitades iguales. "
                       "Menos sensible a valores extremos que el promedio."),
                html.Code("Rem_mediana = P50(distribucion de remuneraciones)",
                           className="sipa-formula"),
            ], style={'marginBottom': '1rem'}),

            html.Div([
                html.H6("Variacion Mensual y Anual", style={'fontWeight': '600'}),
                html.P("Cambio porcentual de la remuneracion respecto al mes anterior y al mismo mes del ano anterior."),
                html.Code("var_periodo = ((Rem(t) - Rem(t-1)) / Rem(t-1)) x 100",
                           className="sipa-formula"),
                html.Code("var_yoy = ((Rem(t) - Rem(t-12)) / Rem(t-12)) x 100",
                           className="sipa-formula"),
            ], style={'marginBottom': '1rem'}),

            html.Div([
                html.H6("Efecto Aguinaldo (SAC)", style={'fontWeight': '600'}),
                html.P("La remuneracion por todo concepto incluye el Sueldo Anual Complementario, "
                       "que se paga en junio y diciembre. Esto genera picos pronunciados en esos meses. "
                       "El panel ofrece la opcion de suavizar las series con un promedio movil de 12 meses "
                       "para eliminar este efecto estacional."),
                html.Code("Rem_suavizada(t) = Promedio(Rem(t-11) ... Rem(t))",
                           className="sipa-formula"),
            ]),
        ], className="sipa-metodo-section"),

        # 4b. Salario Real e IPC
        html.Div([
            html.H5("5. Salario Real e IPC"),

            html.Div([
                html.H6("Indice de Precios al Consumidor (IPC)", style={'fontWeight': '600'}),
                html.P([
                    "Serie mensual empalmada de IPC con base Enero 2016 = 100, que cubre el periodo "
                    "2000-2025. El empalme utiliza series provinciales (CABA, Cordoba, San Luis) para "
                    "cubrir el periodo 2007-2016 donde el IPC nacional (INDEC) no fue confiable. "
                    "Fuente: ",
                    html.A("matuteiglesias/IPC-Argentina",
                           href="https://github.com/matuteiglesias/IPC-Argentina",
                           target="_blank"),
                    "."
                ]),
            ], style={'marginBottom': '1rem'}),

            html.Div([
                html.H6("Remuneracion Real (deflactada)", style={'fontWeight': '600'}),
                html.P("La remuneracion real mide el poder adquisitivo del salario, descontando "
                       "el efecto de la inflacion. Se calcula deflactando la remuneracion nominal "
                       "por el IPC del mismo mes."),
                html.Code("Rem_real(t) = (Rem_nominal(t) / IPC(t)) x 100",
                           className="sipa-formula"),
                html.Small("Unidad: pesos constantes de Enero 2016", style={'color': '#718096'}),
            ], style={'marginBottom': '1rem'}),

            html.Div([
                html.H6("Datasets derivados", style={'fontWeight': '600'}),
                html.Ul([
                    html.Li([html.Strong("R1_real: "), "Remuneracion real promedio total (309 meses)"]),
                    html.Li([html.Strong("R2_real: "), "Remuneracion real mediana total (309 meses)"]),
                    html.Li([html.Strong("R3_real: "), "Remuneracion real promedio por sector CIIU (14 sectores x ~309 meses)"]),
                ]),
                html.Small("La cobertura temporal es la interseccion entre las series de remuneraciones "
                           "(desde Ene 1995) y el IPC disponible (desde Ene 2000).",
                           style={'color': '#718096'}),
            ], style={'marginBottom': '1rem'}),

            html.Div([
                html.H6("Visualizacion", style={'fontWeight': '600'}),
                html.Ul([
                    html.Li([html.Strong("Temporal: "),
                             "Al seleccionar Remuneracion Promedio o Mediana se muestran "
                             "ambas series (nominal y real) en el mismo grafico. En niveles se usa "
                             "eje dual (izq: nominal, der: real). En variaciones e indice comparten eje."]),
                    html.Li([html.Strong("Sectorial: "),
                             "La fuente 'Remuneracion Real' muestra el salario real por sector, "
                             "permitiendo identificar que sectores ganan o pierden poder adquisitivo "
                             "en sus negociaciones salariales."]),
                ]),
            ]),
        ], className="sipa-metodo-section"),

        # 5. Indicadores de Empresas
        html.Div([
            html.H5("6. Indicadores de Empresas (E1-E2)"),

            html.Div([
                html.H6("Total de Empresas (E1)", style={'fontWeight': '600'}),
                html.P("Cantidad total de empresas del sector privado con al menos un trabajador "
                       "registrado en el SIPA durante el periodo."),
            ], style={'marginBottom': '1rem'}),

            html.Div([
                html.H6("Empresas por Sector (E2)", style={'fontWeight': '600'}),
                html.P("Desagregacion por los 14 sectores de actividad economica (letra CIIU)."),
            ], style={'marginBottom': '1rem'}),

            html.Div([
                html.H6("Variacion Anual", style={'fontWeight': '600'}),
                html.Code("var_anual = ((Empresas(t) - Empresas(t-1)) / Empresas(t-1)) x 100",
                           className="sipa-formula"),
                html.Small("Frecuencia anual, un dato por ano", style={'color': '#718096'}),
            ]),
        ], className="sipa-metodo-section"),

        # 6. Indicadores de Flujos
        html.Div([
            html.H5("7. Indicadores de Flujos de Empleo (F1-F3)"),

            html.Div([
                html.H6("Altas y Bajas (F1)", style={'fontWeight': '600'}),
                html.P("Cantidad de puestos de trabajo creados (altas) y destruidos (bajas) "
                       "en el trimestre."),
                html.Ul([
                    html.Li([html.Strong("Altas: "), "Nuevos puestos registrados en el periodo"]),
                    html.Li([html.Strong("Bajas: "), "Puestos dados de baja en el periodo"]),
                ]),
            ], style={'marginBottom': '1rem'}),

            html.Div([
                html.H6("Creacion Neta", style={'fontWeight': '600'}),
                html.Code("Creacion_Neta = Altas - Bajas", className="sipa-formula"),
                html.P("Valor positivo indica creacion neta; negativo indica destruccion neta de empleo.",
                       style={'fontSize': '0.85rem', 'color': '#718096'}),
            ], style={'marginBottom': '1rem'}),

            html.Div([
                html.H6("Tasas de Rotacion (F2)", style={'fontWeight': '600'}),
                html.Code("Tasa_Entrada = (Altas / Stock_Empleo) x 100", className="sipa-formula"),
                html.Code("Tasa_Salida = (Bajas / Stock_Empleo) x 100", className="sipa-formula"),
                html.Code("Tasa_Rotacion = Tasa_Entrada + Tasa_Salida", className="sipa-formula"),
                html.Small("Tasas expresadas como porcentaje del stock de empleo",
                           style={'color': '#718096'}),
            ], style={'marginBottom': '1rem'}),

            html.Div([
                html.H6("Flujos por Sector (F3)", style={'fontWeight': '600'}),
                html.P("Altas, bajas y creacion neta desagregadas por los 14 sectores CIIU."),
            ]),
        ], className="sipa-metodo-section"),

        # 7. Indicadores de Genero
        html.Div([
            html.H5("8. Indicadores de Genero (G1-G2)"),

            html.Div([
                html.H6("Empleo por Genero (G1)", style={'fontWeight': '600'}),
                html.P("Cantidad de trabajadores registrados desagregada por sexo (Mujeres y Varones)."),
                html.Code("Participacion_Fem = Empleo_Mujeres / (Empleo_Mujeres + Empleo_Varones) x 100",
                           className="sipa-formula"),
            ], style={'marginBottom': '1rem'}),

            html.Div([
                html.H6("Brecha Salarial (G2)", style={'fontWeight': '600'}),
                html.P("Diferencia porcentual entre la remuneracion de varones y mujeres."),
                html.Code("Brecha = ((Rem_Varones - Rem_Mujeres) / Rem_Varones) x 100",
                           className="sipa-formula"),
                html.Small("Un valor de 40% indica que las mujeres perciben en promedio "
                           "40% menos que los varones", style={'color': '#718096'}),
            ]),
        ], className="sipa-metodo-section"),

        # 8. Series Temporales
        html.Div([
            html.H5("9. Series Temporales y Estacionalidad"),

            html.Div([
                html.H6("Series con Estacionalidad (C1.1, C2.1)", style={'fontWeight': '600'}),
                html.P("Datos originales sin ajuste estacional. Reflejan patrones ciclicos propios de "
                       "cada periodo del ano (ej: mayor empleo en trimestres de cosecha)."),
            ], style={'marginBottom': '1rem'}),

            html.Div([
                html.H6("Series Desestacionalizadas (C1.2, C2.2)", style={'fontWeight': '600'}),
                html.P("Datos ajustados para eliminar efectos estacionales, permitiendo observar "
                       "la tendencia subyacente del empleo."),
                html.Small("Metodo de ajuste: X-13ARIMA-SEATS del US Census Bureau",
                           style={'color': '#718096'}),
            ]),
        ], className="sipa-metodo-section"),

        # 9. Clasificacion CIIU
        html.Div([
            html.H5("10. Clasificacion Industrial (CIIU)"),
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
                             html.Td("14 sectores"), html.Td("A: Agricultura, C: Industria")]),
                    html.Tr([html.Td("C4"), html.Td("2 digitos (Divisiones)"),
                             html.Td("56 ramas"), html.Td("15: Alimentos, 24: Quimicos")]),
                    html.Tr([html.Td("C6"), html.Td("3 digitos (Grupos)"),
                             html.Td("147 ramas"), html.Td("151: Carnes, 241: Quimicos basicos")]),
                    html.Tr([html.Td("C7"), html.Td("4 digitos (Clases)"),
                             html.Td("301 ramas"), html.Td("1511: Mataderos, 2411: Quimicos basicos")])
                ])
            ], className="table table-striped",
               style={'fontSize': '0.85rem'}),
            html.P("Los sectores por letra CIIU aplican tambien a remuneraciones (R3, R4), "
                   "empresas (E2) y flujos (F3).",
                   style={'color': '#718096', 'fontSize': '0.85rem'}),
        ], className="sipa-metodo-section"),

        # 10. Sistema de Alertas
        html.Div([
            html.H5("11. Sistema de Alertas Multi-Fuente"),
            html.P("El sistema monitorea automaticamente 5 fuentes de datos y genera alertas "
                   "en cuatro categorias:"),

            html.Div([
                html.Div([
                    html.Span("CRITICA", className="sipa-badge sipa-badge-danger"),
                    html.Span(" - Caidas severas, destruccion masiva de empleo, "
                              "aumentos significativos de brecha salarial",
                              style={'fontSize': '0.85rem'}),
                ], style={'marginBottom': '0.5rem'}),
                html.Div([
                    html.Span("ADVERTENCIA", className="sipa-badge sipa-badge-warning"),
                    html.Span(" - Variaciones moderadas, cambios de tendencia, "
                              "rotacion elevada, creacion neta negativa",
                              style={'fontSize': '0.85rem'}),
                ], style={'marginBottom': '0.5rem'}),
                html.Div([
                    html.Span("POSITIVA", className="sipa-badge sipa-badge-success"),
                    html.Span(" - Crecimiento robusto, creacion neta significativa, "
                              "reduccion de brecha salarial",
                              style={'fontSize': '0.85rem'}),
                ], style={'marginBottom': '0.5rem'}),
                html.Div([
                    html.Span("INFORMATIVA", className="sipa-badge sipa-badge-info"),
                    html.Span(" - Maximos historicos, niveles de brecha actuales, "
                              "estancamiento empresarial",
                              style={'fontSize': '0.85rem'}),
                ], style={'marginBottom': '1rem'}),
            ]),

            html.H6("Fuentes analizadas", style={'fontWeight': '600'}),
            html.Table([
                html.Thead([
                    html.Tr([html.Th("Fuente"), html.Th("Indicadores monitoreados")])
                ]),
                html.Tbody([
                    html.Tr([html.Td("Empleo (C1.1)"),
                             html.Td("Var. trimestral/interanual, perdida absoluta, cambio de tendencia")]),
                    html.Tr([html.Td("Empleo Sectorial (C3)"),
                             html.Td("Caidas por sector, crisis generalizada (>3 sectores)")]),
                    html.Tr([html.Td("Remuneraciones (R1)"),
                             html.Td("Var. mensual, maximo historico, 3 meses consecutivos de caida")]),
                    html.Tr([html.Td("Empresas (E1)"),
                             html.Td("Var. anual, estancamiento")]),
                    html.Tr([html.Td("Flujos (F1, F2)"),
                             html.Td("Creacion neta, destruccion sostenida, tasa salida > entrada, rotacion")]),
                    html.Tr([html.Td("Genero (G2)"),
                             html.Td("Cambio de brecha salarial, tendencia sostenida (3+ periodos)")]),
                ])
            ], className="table table-striped",
               style={'fontSize': '0.85rem'}),

            html.H6("Alerta cruzada", style={'fontWeight': '600', 'marginTop': '1rem'}),
            html.P("Cuando 3 o mas fuentes presentan senales negativas simultaneas, se genera una "
                   "alerta cruzada de maxima prioridad indicando deterioro en multiples dimensiones.",
                   style={'fontSize': '0.85rem'}),

            html.H6("Umbrales configurables", style={'fontWeight': '600', 'marginTop': '1rem'}),
            html.Ul([
                html.Li("Umbral de variacion trimestral (default: 5%)"),
                html.Li("Umbral de variacion interanual (default: 10%)"),
            ]),
        ], className="sipa-metodo-section"),

        # 11. Pipeline de Datos
        html.Div([
            html.H5("12. Pipeline de Datos"),
            html.P("El sistema cuenta con un pipeline automatizado para mantener los datos actualizados:"),

            html.Div([
                html.H6("1. Descarga", style={'fontWeight': '600'}),
                html.Code("python scripts/download_oede.py --all", className="sipa-formula"),
                html.P("Descarga los 7 archivos Excel del OEDE desde argentina.gob.ar y el CSV de IPC "
                       "desde GitHub a data/raw/",
                       style={'fontSize': '0.85rem'}),
            ], style={'marginBottom': '0.75rem'}),

            html.Div([
                html.H6("2. Preprocesamiento", style={'fontWeight': '600'}),
                html.Code("python scripts/preprocess/remuneraciones_mes.py", className="sipa-formula"),
                html.P("Cada fuente tiene su procesador que extrae hojas, limpia datos y genera CSV + Parquet. "
                       "Disponibles: empleo_trimestral, remuneraciones_mes, empresas, flujos, genero, ipc.",
                       style={'fontSize': '0.85rem'}),
            ], style={'marginBottom': '0.75rem'}),

            html.Div([
                html.H6("3. Carga", style={'fontWeight': '600'}),
                html.P("El dashboard carga automaticamente desde Parquet (data/optimized/) con fallback a CSV "
                       "(data/processed/). Tambien soporta carga desde PostgreSQL.",
                       style={'fontSize': '0.85rem'}),
            ]),
        ], className="sipa-metodo-section"),

        # 12. Fuentes y Actualizacion
        html.Div([
            html.H5("13. Fuentes y Actualizacion"),
            html.Div([
                html.Div([
                    html.Strong("Fuente primaria: "),
                    html.Span("Sistema Integrado Previsional Argentino (SIPA)")
                ], style={'marginBottom': '0.5rem'}),
                html.Div([
                    html.Strong("Procesamiento: "),
                    html.Span("Observatorio de Empleo y Dinamica Empresarial (OEDE) - MTEySS")
                ], style={'marginBottom': '0.5rem'}),
                html.Div([
                    html.Strong("Periodicidad: "),
                    html.Span("Mensual (remuneraciones), Trimestral (empleo, flujos, genero), "
                              "Anual (empresas)")
                ], style={'marginBottom': '0.5rem'}),
                html.Div([
                    html.Strong("Cobertura temporal: "),
                    html.Span("Empleo desde 1T 1996 | Remuneraciones desde Ene 1995 | "
                              "Empresas desde 1996 | Flujos desde 2T 1996 | Genero desde 3T 2003 | "
                              "IPC desde Ene 2000")
                ], style={'marginBottom': '0.5rem'}),
                html.Div([
                    html.Strong("Formatos: "),
                    html.Span("Parquet (optimizado), CSV (compatible), Excel (fuente original)")
                ]),
            ]),
        ], className="sipa-metodo-section"),

        # 14. Notas Tecnicas y Glosario
        html.Div([
            html.H5("14. Notas Tecnicas y Glosario"),

            html.H6("Notas Tecnicas", style={'fontWeight': '600', 'marginBottom': '0.5rem'}),
            html.Ul([
                html.Li("Los datos corresponden unicamente al empleo registrado (formal) del sector privado"),
                html.Li("No incluye empleo publico provincial ni municipal"),
                html.Li("Las series pueden tener revisiones retroactivas por parte del organismo fuente"),
                html.Li("Valores faltantes se indican como 's.d.' en archivos fuente y se tratan como nulos"),
                html.Li("El ajuste estacional es realizado por el organismo fuente, no por este panel"),
                html.Li("Las remuneraciones nominales son en pesos corrientes. El panel tambien ofrece "
                        "series reales deflactadas por IPC (ver seccion 5)"),
                html.Li("La brecha salarial se calcula como diferencia porcentual sobre la remuneracion masculina"),
            ]),

            html.H6("Glosario", style={'fontWeight': '600', 'marginTop': '1rem', 'marginBottom': '0.5rem'}),
            html.Dl([
                html.Dt("SIPA"), html.Dd("Sistema Integrado Previsional Argentino"),
                html.Dt("OEDE"), html.Dd("Observatorio de Empleo y Dinamica Empresarial"),
                html.Dt("CIIU"), html.Dd("Clasificacion Industrial Internacional Uniforme (Rev. 3)"),
                html.Dt("MTEySS"), html.Dd("Ministerio de Trabajo, Empleo y Seguridad Social"),
                html.Dt("Empleo Registrado"),
                html.Dd("Trabajadores con aportes declarados al sistema de seguridad social"),
                html.Dt("Creacion Neta"),
                html.Dd("Diferencia entre altas y bajas de puestos de trabajo en un periodo"),
                html.Dt("Tasa de Rotacion"),
                html.Dd("Suma de tasas de entrada y salida; mide la dinamica del mercado laboral"),
                html.Dt("Brecha Salarial"),
                html.Dd("Diferencia porcentual de remuneracion entre varones y mujeres"),
                html.Dt("IPC"),
                html.Dd("Indice de Precios al Consumidor - mide la variacion de precios de bienes y servicios"),
                html.Dt("Salario Real"),
                html.Dd("Remuneracion ajustada por inflacion (deflactada por IPC), mide poder adquisitivo"),
                html.Dt("SAC (Aguinaldo)"),
                html.Dd("Sueldo Anual Complementario - pago obligatorio en junio y diciembre equivalente "
                         "al 50% del mejor salario mensual del semestre"),
                html.Dt("Deflactacion"),
                html.Dd("Proceso de ajustar valores nominales por un indice de precios para obtener "
                         "valores reales (a precios constantes)"),
                html.Dt("Desestacionalizacion"),
                html.Dd("Proceso estadistico para remover patrones estacionales recurrentes"),
                html.Dt("X-13ARIMA-SEATS"),
                html.Dd("Metodo de ajuste estacional desarrollado por el US Census Bureau"),
            ]),
        ], className="sipa-metodo-section"),

    ], style={'maxWidth': '900px', 'margin': '0 auto'})
