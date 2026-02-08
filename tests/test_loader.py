"""Tests para src/data/loader.py."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from src.data.loader import load_from_files


@pytest.fixture(scope="module")
def loaded_data():
    """Carga datos una vez para todos los tests del modulo."""
    return load_from_files()


class TestLoadFromFiles:
    def test_returns_dict(self, loaded_data):
        assert isinstance(loaded_data, dict)

    def test_has_expected_keys(self, loaded_data):
        expected_keys = ['C1.1', 'C1.2', 'C2.1', 'C2.2', 'C3', 'C4', 'C5', 'C6', 'C7', 'descriptores_CIIU']
        for key in expected_keys:
            assert key in loaded_data, f"Missing key: {key}"

    def test_c11_has_expected_columns(self, loaded_data):
        df = loaded_data['C1.1']
        assert 'Per\u00edodo' in df.columns
        assert 'Empleo' in df.columns
        assert 'Date' in df.columns
        assert 'var_trim' in df.columns
        assert 'var_yoy' in df.columns

    def test_c3_has_expected_columns(self, loaded_data):
        df = loaded_data['C3']
        assert 'Sector' in df.columns
        assert 'Per\u00edodo' in df.columns
        assert 'Empleo' in df.columns

    def test_c11_row_count(self, loaded_data):
        df = loaded_data['C1.1']
        assert len(df) > 50, f"C1.1 tiene solo {len(df)} filas, se esperan >50"

    def test_c3_row_count(self, loaded_data):
        df = loaded_data['C3']
        assert len(df) > 100, f"C3 tiene solo {len(df)} filas, se esperan >100"

    def test_descriptores_has_columns(self, loaded_data):
        df = loaded_data['descriptores_CIIU']
        assert 'C\u00f3digo' in df.columns
        assert 'Descripci\u00f3n' in df.columns

    def test_dataframes_not_empty(self, loaded_data):
        for key, df in loaded_data.items():
            assert len(df) > 0, f"DataFrame {key} esta vacio"
