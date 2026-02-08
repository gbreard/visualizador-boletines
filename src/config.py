"""
Configuracion y constantes del dashboard.
"""

import os

# Directorios de datos (relativos a src/)
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'processed')
OPTIMIZED_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'optimized')

CACHE_SIZE = 128

TRIMESTRE_MES = {
    '1º Trim': 2,
    '2º Trim': 5,
    '3º Trim': 8,
    '4º Trim': 11
}

# Paleta institucional
COLORS = {
    'primary': '#1B2A4A',
    'primary_light': '#2C5282',
    'success': '#276749',
    'danger': '#9B2C2C',
    'warning': '#975A16',
    'info': '#2B6CB0',
    'bg': '#F7FAFC',
    'bg_secondary': '#EDF2F7',
    'border': '#E2E8F0',
    'text': '#1A202C',
    'text_muted': '#718096',
    'white': '#FFFFFF',
}

# Colores consistentes por sector (mismo sector = mismo color en todos los graficos)
SECTOR_COLORS = {
    'Agricultura, ganadería y pesca': '#276749',
    'Minería y petróleo (3)': '#744210',
    'Industria': '#2C5282',
    'Electricidad, gas y agua (3)': '#975A16',
    'Construcción': '#9B2C2C',
    'Comercio': '#553C9A',
    'Servicios': '#2B6CB0',
    'Total': '#4A5568',
}

# Secuencia de colores institucionales para Plotly
PLOTLY_COLOR_SEQUENCE = [
    '#2C5282', '#276749', '#9B2C2C', '#975A16', '#553C9A',
    '#2B6CB0', '#744210', '#285E61', '#702459', '#4A5568'
]

# Template Plotly institucional
PLOTLY_TEMPLATE = {
    'layout': {
        'paper_bgcolor': '#FFFFFF',
        'plot_bgcolor': '#FFFFFF',
        'font': {
            'family': '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
            'color': '#1A202C',
            'size': 12
        },
        'title': {
            'font': {'size': 14, 'color': '#1B2A4A'},
            'x': 0.02,
            'xanchor': 'left'
        },
        'xaxis': {
            'showgrid': True,
            'gridcolor': 'rgba(226, 232, 240, 0.6)',
            'zeroline': False,
            'linecolor': '#E2E8F0',
        },
        'yaxis': {
            'showgrid': True,
            'gridcolor': 'rgba(226, 232, 240, 0.6)',
            'zeroline': False,
            'linecolor': '#E2E8F0',
        },
        'hoverlabel': {
            'bgcolor': '#1B2A4A',
            'font': {'color': '#FFFFFF', 'size': 12}
        },
        'margin': {'l': 50, 'r': 20, 't': 50, 'b': 40},
        'colorway': [
            '#2C5282', '#276749', '#9B2C2C', '#975A16', '#553C9A',
            '#2B6CB0', '#744210', '#285E61', '#702459', '#4A5568'
        ],
        'legend': {
            'font': {'size': 11},
            'bgcolor': 'rgba(255,255,255,0.8)',
            'bordercolor': '#E2E8F0',
            'borderwidth': 1,
        }
    }
}

PARQUET_MAPPING = {
    'C1.1': 'c11.parquet',
    'C1.2': 'c12.parquet',
    'C2.1': 'c2_1.parquet',
    'C2.2': 'c2_2.parquet',
    'C3': 'c3.parquet',
    'C4': 'c4.parquet',
    'C5': 'c5.parquet',
    'C6': 'c6.parquet',
    'C7': 'c7.parquet',
    'descriptores_CIIU': 'descriptores.parquet',
    # Remuneraciones
    'R1': 'r1.parquet',
    'R2': 'r2.parquet',
    'R3': 'r3.parquet',
    'R4': 'r4.parquet',
    'descriptores_remuneraciones': 'descriptores_remuneraciones.parquet',
    # Empresas
    'E1': 'e1.parquet',
    'E2': 'e2.parquet',
    'E3': 'e3.parquet',
    # Flujos
    'F1': 'f1.parquet',
    'F2': 'f2.parquet',
    'F3': 'f3.parquet',
    # Genero
    'G1': 'g1.parquet',
    'G2': 'g2.parquet',
    'G3': 'g3.parquet',
}

# Datasets de empleo trimestral (fuente original)
EMPLEO_KEYS = ['C1.1', 'C1.2', 'C2.1', 'C2.2', 'C3', 'C4', 'C5', 'C6', 'C7', 'descriptores_CIIU']

# Datasets de remuneraciones
REMUNERACIONES_KEYS = ['R1', 'R2', 'R3', 'R4', 'descriptores_remuneraciones']

# Datasets de empresas
EMPRESAS_KEYS = ['E1', 'E2', 'E3']

# Datasets de flujos de empleo
FLUJOS_KEYS = ['F1', 'F2', 'F3']

# Datasets de genero
GENERO_KEYS = ['G1', 'G2', 'G3']

ALL_DATASET_KEYS = EMPLEO_KEYS + REMUNERACIONES_KEYS + EMPRESAS_KEYS + FLUJOS_KEYS + GENERO_KEYS

DATASET_LABELS = {
    'C1.1': 'C1.1 - Serie temporal con estacionalidad',
    'C1.2': 'C1.2 - Serie temporal desestacionalizada',
    'C2.1': 'C2.1 - Por sector con estacionalidad',
    'C2.2': 'C2.2 - Por sector desestacionalizada',
    'C3': 'C3 - Por letra CIIU',
    'C4': 'C4 - Por 2 digitos CIIU',
    'C5': 'C5 - Por sector y tamano',
    'C6': 'C6 - Por 3 digitos CIIU',
    'C7': 'C7 - Por 4 digitos CIIU',
    'descriptores_CIIU': 'Descriptores CIIU',
    'R1': 'R1 - Remuneracion promedio total',
    'R2': 'R2 - Remuneracion mediana total',
    'R3': 'R3 - Remuneracion promedio por sector',
    'R4': 'R4 - Remuneracion mediana por sector',
    'descriptores_remuneraciones': 'Descriptores CIIU (Remuneraciones)',
    'E1': 'E1 - Total empresas',
    'E2': 'E2 - Empresas por sector',
    'E3': 'E3 - Empresas por tamano',
    'F1': 'F1 - Flujos totales (altas/bajas)',
    'F2': 'F2 - Tasas de rotacion',
    'F3': 'F3 - Flujos por sector',
    'G1': 'G1 - Empleo por genero total',
    'G2': 'G2 - Brecha salarial por genero',
    'G3': 'G3 - Empleo por genero y sector',
}

# Mapeo de sector CIIU letra a descripcion (para remuneraciones)
SECTOR_CIIU_LETRA = {
    'A': 'Agricultura, ganaderia y pesca',
    'B': 'Mineria y petroleo',
    'C': 'Industria',
    'D': 'Electricidad, gas y agua',
    'E': 'Construccion',
    'F': 'Comercio',
    'G': 'Hoteleria y restaurantes',
    'H': 'Transporte y comunicaciones',
    'I': 'Serv. financieros',
    'J': 'Serv. inmobiliarios',
    'K': 'Adm. publica y defensa',
    'M': 'Ensenanza',
    'N': 'Serv. sociales y de salud',
    'O': 'Otros servicios',
}

# Descripciones expandidas para tab Datos
DATASET_DESCRIPTIONS = {
    'C1.1': {
        'title': 'Serie Temporal con Estacionalidad',
        'description': 'Serie de empleo total del pais sin ajuste estacional. Incluye niveles absolutos, variaciones trimestrales e interanuales, e indice base 100.',
        'columns': 'Periodo, Empleo, var_trim, var_yoy, index_100',
        'frequency': 'Trimestral',
    },
    'C1.2': {
        'title': 'Serie Temporal Desestacionalizada',
        'description': 'Serie de empleo total con ajuste estacional (X-13ARIMA-SEATS). Elimina patrones estacionales para reflejar la tendencia subyacente.',
        'columns': 'Periodo, Empleo, var_trim, var_yoy, index_100',
        'frequency': 'Trimestral',
    },
    'C2.1': {
        'title': 'Empleo por Sector con Estacionalidad',
        'description': 'Empleo desagregado por grandes sectores economicos (Industria, Comercio, Servicios, etc.) sin ajuste estacional.',
        'columns': 'Periodo, Sector, Empleo',
        'frequency': 'Trimestral',
    },
    'C2.2': {
        'title': 'Empleo por Sector Desestacionalizada',
        'description': 'Empleo por sector economico con ajuste estacional.',
        'columns': 'Periodo, Sector, Empleo',
        'frequency': 'Trimestral',
    },
    'C3': {
        'title': 'Empleo por Letra CIIU',
        'description': 'Empleo registrado desagregado en 14 secciones de la CIIU Rev. 3 (nivel de letra). Incluye sectores como Agricultura, Industria, Construccion, Comercio, Servicios.',
        'columns': 'Periodo, Sector, Empleo',
        'frequency': 'Trimestral',
    },
    'C4': {
        'title': 'Empleo por 2 Digitos CIIU',
        'description': 'Empleo desagregado en 56 divisiones industriales (2 digitos CIIU). Mayor detalle sectorial: Alimentos, Textiles, Quimicos, etc.',
        'columns': 'Periodo, Sector, Empleo',
        'frequency': 'Trimestral',
    },
    'C5': {
        'title': 'Empleo por Sector y Tamano de Empresa',
        'description': 'Empleo cruzado por sector economico y tamano de empresa (Micro, Pequena, Mediana, Grande).',
        'columns': 'Periodo, Sector, Empleo',
        'frequency': 'Trimestral',
    },
    'C6': {
        'title': 'Empleo por 3 Digitos CIIU',
        'description': 'Empleo desagregado en 147 grupos industriales (3 digitos CIIU). Permite analisis a nivel de subrama economica.',
        'columns': 'Periodo, Sector, Empleo',
        'frequency': 'Trimestral',
    },
    'C7': {
        'title': 'Empleo por 4 Digitos CIIU',
        'description': 'Maximo nivel de desagregacion: 301 clases industriales (4 digitos CIIU). Detalle por actividad economica especifica.',
        'columns': 'Periodo, Sector, Empleo',
        'frequency': 'Trimestral',
    },
    'descriptores_CIIU': {
        'title': 'Descriptores CIIU',
        'description': 'Tabla maestra de codigos y descripciones de la Clasificacion Industrial Internacional Uniforme. Vincula codigos numericos con nombres de actividades.',
        'columns': 'Tabla, Codigo, Descripcion',
        'frequency': 'Referencia estatica',
    },
    'R1': {
        'title': 'Remuneracion Promedio Total',
        'description': 'Remuneracion promedio por todo concepto de los trabajadores registrados del sector privado. Serie original a valores corrientes.',
        'columns': 'Periodo, Remuneracion',
        'frequency': 'Mensual',
    },
    'R2': {
        'title': 'Remuneracion Mediana Total',
        'description': 'Remuneracion mediana por todo concepto de los trabajadores registrados del sector privado.',
        'columns': 'Periodo, Remuneracion',
        'frequency': 'Mensual',
    },
    'R3': {
        'title': 'Remuneracion Promedio por Sector',
        'description': 'Remuneracion promedio por sector de actividad economica (nivel letra CIIU). Serie original a valores corrientes.',
        'columns': 'Periodo, Sector, Remuneracion',
        'frequency': 'Mensual',
    },
    'R4': {
        'title': 'Remuneracion Mediana por Sector',
        'description': 'Remuneracion mediana por sector de actividad economica (nivel letra CIIU).',
        'columns': 'Periodo, Sector, Remuneracion',
        'frequency': 'Mensual',
    },
    'descriptores_remuneraciones': {
        'title': 'Descriptores CIIU (Remuneraciones)',
        'description': 'Tabla de codigos CIIU para las tablas de remuneraciones (2, 3 y 4 digitos).',
        'columns': 'Codigo, Descripcion',
        'frequency': 'Referencia estatica',
    },
    'E1': {
        'title': 'Total de Empresas',
        'description': 'Cantidad total de empresas registradas del sector privado.',
        'columns': 'Periodo, Empresas',
        'frequency': 'Anual',
    },
    'E2': {
        'title': 'Empresas por Sector',
        'description': 'Cantidad de empresas por sector de actividad economica.',
        'columns': 'Periodo, Sector, Empresas',
        'frequency': 'Anual',
    },
    'E3': {
        'title': 'Empresas por Tamano',
        'description': 'Cantidad de empresas por tamano (micro, pequena, mediana, grande).',
        'columns': 'Periodo, Tamano, Empresas',
        'frequency': 'Anual',
    },
    'F1': {
        'title': 'Flujos de Empleo Total',
        'description': 'Altas, bajas y creacion neta de puestos de trabajo del sector privado.',
        'columns': 'Periodo, Altas, Bajas, Creacion_Neta',
        'frequency': 'Trimestral',
    },
    'F2': {
        'title': 'Tasas de Rotacion',
        'description': 'Tasas de entrada, salida y rotacion laboral del sector privado.',
        'columns': 'Periodo, Tasa_Entrada, Tasa_Salida, Tasa_Rotacion',
        'frequency': 'Trimestral',
    },
    'F3': {
        'title': 'Flujos por Sector',
        'description': 'Flujos de empleo por sector de actividad economica.',
        'columns': 'Periodo, Sector, Altas, Bajas',
        'frequency': 'Trimestral',
    },
    'G1': {
        'title': 'Empleo por Genero',
        'description': 'Empleo registrado del sector privado desagregado por sexo.',
        'columns': 'Periodo, Sexo, Empleo',
        'frequency': 'Trimestral',
    },
    'G2': {
        'title': 'Brecha Salarial por Genero',
        'description': 'Remuneraciones por sexo y brecha salarial de genero.',
        'columns': 'Periodo, Sexo, Remuneracion, Brecha',
        'frequency': 'Trimestral',
    },
    'G3': {
        'title': 'Empleo por Genero y Sector',
        'description': 'Empleo por sexo desagregado por sector de actividad economica.',
        'columns': 'Periodo, Sexo, Sector, Empleo',
        'frequency': 'Trimestral',
    },
}
