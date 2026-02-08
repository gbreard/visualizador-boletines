"""Tests para scripts/cargar_datos.py."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from scripts.cargar_datos import load_csv_data, parse_period_to_date


class TestParsePeriodToDate:
    def test_first_quarter(self):
        anio, trim, fecha = parse_period_to_date("1\u00ba Trim 2024")
        assert anio == 2024
        assert trim == 1
        assert fecha.month == 2

    def test_fourth_quarter(self):
        anio, trim, fecha = parse_period_to_date("4\u00ba Trim 2020")
        assert anio == 2020
        assert trim == 4
        assert fecha.month == 11


class TestLoadCsvData:
    def test_loads_data(self):
        data = load_csv_data()
        assert isinstance(data, dict)
        assert len(data) > 0

    def test_has_main_datasets(self):
        data = load_csv_data()
        assert 'C1.1' in data
        assert 'C3' in data


class TestDryRun:
    def test_dry_run_from_csv(self):
        """Simula dry-run cargando desde CSV."""
        from scripts.cargar_datos import ingest_to_db
        data = load_csv_data()
        result = ingest_to_db(data, engine=None, dry_run=True)
        assert result is True
