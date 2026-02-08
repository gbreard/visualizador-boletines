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
    'descriptores_CIIU': 'descriptores.parquet'
}

ALL_DATASET_KEYS = ['C1.1', 'C1.2', 'C2.1', 'C2.2', 'C3', 'C4', 'C5', 'C6', 'C7', 'descriptores_CIIU']

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
    'descriptores_CIIU': 'Descriptores CIIU'
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
}
