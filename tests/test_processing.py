"""Tests para src/data/processing.py."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import pandas as pd
import numpy as np
from src.data.processing import (
    parse_period_string, process_periods, calculate_variations,
    get_latest_period_data, filter_by_dates
)


class TestParsePeriodString:
    def test_valid_period(self):
        result = parse_period_string("1\u00ba Trim 2024")
        assert result is not None
        assert result.year == 2024
        assert result.month == 2

    def test_fourth_quarter(self):
        result = parse_period_string("4\u00ba Trim 2020")
        assert result is not None
        assert result.year == 2020
        assert result.month == 11

    def test_second_quarter(self):
        result = parse_period_string("2\u00ba Trim 2015")
        assert result is not None
        assert result.year == 2015
        assert result.month == 5

    def test_invalid_period(self):
        result = parse_period_string("invalid")
        assert result is None

    def test_empty_string(self):
        result = parse_period_string("")
        assert result is None


class TestProcessPeriods:
    def test_adds_date_columns(self):
        df = pd.DataFrame({'Per\u00edodo': ['1\u00ba Trim 2024', '2\u00ba Trim 2024']})
        result = process_periods(df)
        assert 'Date' in result.columns
        assert 'Year' in result.columns
        assert 'Quarter' in result.columns
        assert result['Year'].iloc[0] == 2024

    def test_no_periodo_column(self):
        df = pd.DataFrame({'other': [1, 2]})
        result = process_periods(df)
        assert 'Date' not in result.columns

    def test_empty_dataframe(self):
        df = pd.DataFrame({'Per\u00edodo': []})
        result = process_periods(df)
        assert result.empty


class TestCalculateVariations:
    def test_basic_variations(self):
        df = pd.DataFrame({
            'Empleo': [100, 110, 105, 120, 115],
            'Date': pd.date_range('2020-01-01', periods=5, freq='QS')
        })
        result = calculate_variations(df)
        assert 'var_trim' in result.columns
        assert 'var_yoy' in result.columns
        assert 'index_100' in result.columns
        # First var_trim should be NaN
        assert pd.isna(result['var_trim'].iloc[0])
        # Second should be 10%
        assert pytest.approx(result['var_trim'].iloc[1], rel=0.01) == 10.0
        # index_100 first should be 100
        assert result['index_100'].iloc[0] == 100.0

    def test_no_empleo_column(self):
        df = pd.DataFrame({'other': [1, 2], 'Date': pd.date_range('2020-01-01', periods=2)})
        result = calculate_variations(df)
        assert 'var_trim' not in result.columns

    def test_empty_dataframe(self):
        df = pd.DataFrame({'Empleo': [], 'Date': []})
        result = calculate_variations(df)
        assert result.empty

    def test_nan_handling(self):
        df = pd.DataFrame({
            'Empleo': [100, np.nan, 110, 120, 130],
            'Date': pd.date_range('2020-01-01', periods=5, freq='QS')
        })
        result = calculate_variations(df)
        assert 'var_trim' in result.columns


class TestGetLatestPeriodData:
    def test_with_data(self):
        df = pd.DataFrame({
            'Per\u00edodo': ['1\u00ba Trim 2024', '2\u00ba Trim 2024'],
            'Empleo': [1000, 1100],
            'Date': pd.date_range('2024-02-01', periods=2, freq='3MS'),
            'var_trim': [0, 10.0],
            'var_yoy': [0, 5.0]
        })
        result = get_latest_period_data(df)
        assert result['empleo_actual'] == 1100
        assert result['var_trim'] == 10.0

    def test_empty_dataframe(self):
        result = get_latest_period_data(pd.DataFrame())
        assert result['empleo_actual'] == 0
        assert result['periodo'] == 'No disponible'


class TestFilterByDates:
    def test_filter_range(self):
        df = pd.DataFrame({
            'Per\u00edodo': ['1\u00ba Trim 2020', '2\u00ba Trim 2020', '3\u00ba Trim 2020'],
            'Date': [
                pd.Timestamp('2020-02-01'),
                pd.Timestamp('2020-05-01'),
                pd.Timestamp('2020-08-01')
            ],
            'Empleo': [100, 110, 120]
        })
        result = filter_by_dates(df, '2\u00ba Trim 2020', '3\u00ba Trim 2020')
        assert len(result) == 2

    def test_no_filter(self):
        df = pd.DataFrame({
            'Date': [pd.Timestamp('2020-02-01')],
            'Empleo': [100]
        })
        result = filter_by_dates(df, None, None)
        assert len(result) == 1

    def test_empty_df(self):
        result = filter_by_dates(pd.DataFrame(), '1\u00ba Trim 2020', None)
        assert result.empty
