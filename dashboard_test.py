"""
Dashboard Test - El más simple posible
"""
import dash
from dash import html
import os

app = dash.Dash(__name__)
server = app.server

# Verificar archivos
files_exist = os.path.exists('datos_rapidos')
file_list = []
if files_exist:
    file_list = os.listdir('datos_rapidos')

app.layout = html.Div([
    html.H1("Dashboard Test"),
    html.P(f"Directorio: {os.getcwd()}"),
    html.P(f"datos_rapidos existe: {files_exist}"),
    html.P(f"Archivos: {len(file_list)}"),
    html.Ul([html.Li(f) for f in file_list[:5]])
])

if __name__ == '__main__':
    app.run_server(debug=True)