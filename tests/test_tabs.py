"""Tests de smoke para las tabs: verifican que renderizan sin error."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from src.data.cache import cache
from src.data.loader import load_from_files


@pytest.fixture(scope="module", autouse=True)
def setup_cache():
    """Carga datos en el cache antes de los tests."""
    cache.load(load_from_files)
    yield


class TestTabLayouts:
    def test_resumen_layout(self):
        from src.tabs.resumen import create_resumen_layout
        layout = create_resumen_layout()
        assert layout is not None

    def test_analisis_layout(self):
        from src.tabs.analisis import create_analisis_layout
        layout = create_analisis_layout()
        assert layout is not None

    def test_comparaciones_layout(self):
        from src.tabs.comparaciones import create_comparaciones_layout
        layout = create_comparaciones_layout()
        assert layout is not None

    def test_alertas_layout(self):
        from src.tabs.alertas import create_alertas_layout
        layout = create_alertas_layout()
        assert layout is not None

    def test_datos_layout(self):
        from src.tabs.datos import create_datos_layout
        layout = create_datos_layout()
        assert layout is not None

    def test_metodologia_content(self):
        from src.tabs.metodologia import create_metodologia_layout
        content = create_metodologia_layout()
        assert content is not None

    def test_main_layout(self):
        from src.layout.main import create_main_layout
        layout = create_main_layout()
        assert layout is not None
