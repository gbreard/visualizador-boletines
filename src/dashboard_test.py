"""
Dashboard de prueba simplificado para verificar carga de datos
"""
import dash
from dash import dcc, html, dash_table
import pandas as pd
import os

app = dash.Dash(__name__)

# Cargar un archivo de prueba
print("Cargando datos de prueba...")
try:
    # Intentar cargar desde Parquet
    if os.path.exists('../data/optimized/c11.parquet'):
        df = pd.read_parquet('../data/optimized/c11.parquet')
        print(f"Datos cargados desde Parquet: {len(df)} registros")
    else:
        df = pd.read_csv('../data/processed/C1.1.csv')
        print(f"Datos cargados desde CSV: {len(df)} registros")
    
    print(f"Columnas: {list(df.columns)}")
    print(f"Primeras filas:\n{df.head()}")
    
    # Layout simple
    app.layout = html.Div([
        html.H1("Dashboard de Prueba"),
        html.P(f"Datos cargados: {len(df)} registros"),
        html.P(f"Columnas: {', '.join(df.columns)}"),
        html.Hr(),
        html.H3("Primeros 10 registros:"),
        dash_table.DataTable(
            data=df.head(10).to_dict('records'),
            columns=[{"name": i, "id": i} for i in df.columns],
            style_cell={'textAlign': 'left'},
        )
    ])
    
except Exception as e:
    print(f"ERROR: {e}")
    app.layout = html.Div([
        html.H1("Error cargando datos"),
        html.P(f"Error: {str(e)}")
    ])

if __name__ == '__main__':
    app.run(debug=True, port=8051)