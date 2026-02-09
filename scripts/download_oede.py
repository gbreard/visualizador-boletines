"""
Descarga archivos Excel del OEDE (Observatorio de Empleo y Dinamica Empresarial).

Uso:
    python scripts/download_oede.py --all
    python scripts/download_oede.py --source empleo_trimestral
    python scripts/download_oede.py --source remuneraciones_mensual --source genero
    python scripts/download_oede.py --list
"""

import argparse
import logging
import os
import sys
import time
import urllib.request
import urllib.error

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Directorio de destino
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, 'data', 'raw')

# Fuentes OEDE
# URLs actualizadas Feb 2026 - Los sufijos numericos cambian con cada revision.
# Si una URL falla, verificar en:
# https://www.argentina.gob.ar/trabajo/estadisticas/oede-estadisticas-nacionales
OEDE_FILES = {
    'empleo_trimestral': {
        'url': 'https://www.argentina.gob.ar/sites/default/files/nacional_serie_empleo_trimestral_5.xlsx',
        'filename': 'empleo_trimestral.xlsx',
        'description': 'Empleo registrado trimestral (C1-C7)',
        'frequency': 'quarterly',
    },
    'empleo_anual': {
        'url': 'https://www.argentina.gob.ar/sites/default/files/nacional_serie_empleo_anual_1.xlsx',
        'filename': 'empleo_anual.xlsx',
        'description': 'Empleo registrado anual',
        'frequency': 'annual',
    },
    'remuneraciones_mensual': {
        'url': 'https://www.argentina.gob.ar/sites/default/files/nacional_serie_remuneraciones_mensual_6.xlsx',
        'filename': 'remuneraciones_mensual.xlsx',
        'description': 'Remuneraciones por sector (mensual)',
        'frequency': 'monthly',
    },
    'remuneraciones_anual': {
        'url': 'https://www.argentina.gob.ar/sites/default/files/nacional_serie_remuneraciones_anual_1.xlsx',
        'filename': 'remuneraciones_anual.xlsx',
        'description': 'Remuneraciones anuales',
        'frequency': 'annual',
    },
    'empresas_anual': {
        'url': 'https://www.argentina.gob.ar/sites/default/files/nacional_serie_empresas_1.xlsx',
        'filename': 'empresas_anual.xlsx',
        'description': 'Cantidad de empresas (anual)',
        'frequency': 'annual',
    },
    'flujos_empleo': {
        'url': 'https://www.argentina.gob.ar/sites/default/files/flujos_de_creacion_y_destruccion_de_empleo_0.xlsx',
        'filename': 'flujos_empleo.xlsx',
        'description': 'Flujos de empleo: altas, bajas, rotacion',
        'frequency': 'quarterly',
    },
    'genero': {
        'url': 'https://www.argentina.gob.ar/sites/default/files/boletin_estadisticas_laborales_segun_sexo_al_ii_trim_2025.xlsx',
        'filename': 'genero.xlsx',
        'description': 'Empleo por genero',
        'frequency': 'quarterly',
    },
    'ipc': {
        'url': 'https://raw.githubusercontent.com/matuteiglesias/IPC-Argentina/main/data/info/indice_precios_M.csv',
        'filename': 'ipc_mensual.csv',
        'description': 'IPC mensual empalmado (base Ene 2016=100)',
        'frequency': 'monthly',
    },
}


def download_file(source_key, force=False):
    """Descarga un archivo Excel del OEDE a data/raw/."""
    if source_key not in OEDE_FILES:
        logger.error(f"Fuente desconocida: {source_key}")
        logger.info(f"Fuentes disponibles: {', '.join(OEDE_FILES.keys())}")
        return False

    info = OEDE_FILES[source_key]
    url = info['url']
    dest_path = os.path.join(RAW_DIR, info['filename'])

    # Verificar si ya existe
    if os.path.exists(dest_path) and not force:
        size_kb = os.path.getsize(dest_path) / 1024
        logger.info(f"  {source_key}: Ya existe ({size_kb:.0f} KB). Use --force para re-descargar.")
        return True

    logger.info(f"  Descargando {source_key}: {info['description']}...")
    logger.info(f"    URL: {url}")

    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        start = time.time()
        with urllib.request.urlopen(req, timeout=60) as response:
            data = response.read()
        elapsed = time.time() - start

        # Verificar integridad
        if len(data) < 1000:
            logger.error(f"  {source_key}: Archivo demasiado pequeno ({len(data)} bytes). Posible error.")
            return False

        # Guardar
        os.makedirs(RAW_DIR, exist_ok=True)
        with open(dest_path, 'wb') as f:
            f.write(data)

        size_kb = len(data) / 1024
        logger.info(f"  {source_key}: OK ({size_kb:.0f} KB, {elapsed:.1f}s) -> {dest_path}")
        return True

    except urllib.error.HTTPError as e:
        logger.error(f"  {source_key}: Error HTTP {e.code} - {e.reason}")
        return False
    except urllib.error.URLError as e:
        logger.error(f"  {source_key}: Error de conexion - {e.reason}")
        return False
    except Exception as e:
        logger.error(f"  {source_key}: Error inesperado - {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Descargar archivos Excel del OEDE')
    parser.add_argument('--all', action='store_true', help='Descargar todos los archivos')
    parser.add_argument('--source', action='append', help='Fuente(s) a descargar (puede repetirse)')
    parser.add_argument('--force', action='store_true', help='Re-descargar aunque ya exista')
    parser.add_argument('--list', action='store_true', help='Listar fuentes disponibles')
    args = parser.parse_args()

    if args.list:
        print("\nFuentes OEDE disponibles:")
        print("-" * 70)
        for key, info in OEDE_FILES.items():
            status = "EXISTE" if os.path.exists(os.path.join(RAW_DIR, info['filename'])) else "NO DESCARGADO"
            print(f"  {key:<25} {info['frequency']:<12} [{status}]")
            print(f"    {info['description']}")
        return

    if not args.all and not args.source:
        parser.error("Especifique --all o --source <nombre>")

    sources = list(OEDE_FILES.keys()) if args.all else args.source

    logger.info(f"Descargando {len(sources)} archivo(s)...")
    results = {}
    for source in sources:
        results[source] = download_file(source, force=args.force)

    # Resumen
    ok = sum(1 for v in results.values() if v)
    fail = sum(1 for v in results.values() if not v)
    logger.info(f"\nResumen: {ok} exitosos, {fail} fallidos de {len(results)} total")

    if fail > 0:
        sys.exit(1)


if __name__ == '__main__':
    main()
