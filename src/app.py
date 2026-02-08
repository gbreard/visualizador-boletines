"""
Entry point del Dashboard V2 - Visualizador de Boletines de Empleo.
"""

import sys
import os
import logging

# Asegurar que el directorio padre este en el path para imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dash import Dash

from src.data.cache import cache
from src.data.loader import load_all_data
from src.layout.main import create_main_layout
from src.callbacks.register import register_all_callbacks

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Directorio base (src/)
base_dir = os.path.dirname(os.path.abspath(__file__))

# Crear app
app = Dash(
    __name__,
    assets_folder=os.path.join(base_dir, '..', 'assets'),
    external_stylesheets=[
        'https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css'
    ],
    suppress_callback_exceptions=True
)
app.title = "SIPA - Panel de Monitoreo de Empleo Registrado"

# Cargar datos una vez al inicio
logger.info("Cargando datos...")
cache.load(load_all_data)
logger.info(f"Datos cargados: {cache.data_keys}")
logger.info(f"Periodos: {len(cache.periods)} ({cache.periods[0] if cache.periods else 'N/A'} - {cache.last_period})")

# Layout
app.layout = create_main_layout()

# Registrar todos los callbacks
register_all_callbacks(app)

# Para gunicorn
server = app.server

if __name__ == '__main__':
    debug_mode = '--production' not in sys.argv
    port = int(os.environ.get('PORT', 8050))
    host = '127.0.0.1' if debug_mode else '0.0.0.0'

    logger.info(f"Dashboard disponible en: http://{host}:{port}")
    app.run(debug=debug_mode, host=host, port=port)
