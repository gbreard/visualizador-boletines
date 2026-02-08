"""Tests para src/data/cache.py."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import pandas as pd
from src.data.cache import DataCache


@pytest.fixture
def test_cache():
    """Crea un cache fresco para cada test."""
    c = DataCache()
    c.load(lambda: {
        'C1.1': pd.DataFrame({
            'Per\u00edodo': ['1\u00ba Trim 2024', '2\u00ba Trim 2024'],
            'Empleo': [1000, 1100],
            'Date': pd.to_datetime(['2024-02-01', '2024-05-01'])
        }),
        'C3': pd.DataFrame({
            'Sector': ['A', 'B'],
            'Empleo': [500, 600]
        })
    })
    return c


class TestDataCache:
    def test_get_ref_returns_reference(self, test_cache):
        ref1 = test_cache.get_ref('C1.1')
        ref2 = test_cache.get_ref('C1.1')
        # Same object
        assert ref1 is ref2

    def test_get_returns_copy(self, test_cache):
        copy1 = test_cache.get('C1.1')
        copy2 = test_cache.get('C1.1')
        # Different objects
        assert copy1 is not copy2

    def test_mutating_copy_doesnt_affect_cache(self, test_cache):
        copy = test_cache.get('C1.1')
        copy['Empleo'] = [9999, 8888]
        original = test_cache.get_ref('C1.1')
        assert original['Empleo'].iloc[0] == 1000

    def test_get_missing_key(self, test_cache):
        result = test_cache.get_ref('nonexistent')
        assert result.empty

    def test_periods(self, test_cache):
        periods = test_cache.periods
        assert isinstance(periods, list)
        assert len(periods) == 2
        assert periods == sorted(periods)

    def test_last_period(self, test_cache):
        assert test_cache.last_period == '2\u00ba Trim 2024'

    def test_data_keys(self, test_cache):
        keys = test_cache.data_keys
        assert 'C1.1' in keys
        assert 'C3' in keys

    def test_singleton(self):
        instance1 = DataCache.get_instance()
        instance2 = DataCache.get_instance()
        assert instance1 is instance2
