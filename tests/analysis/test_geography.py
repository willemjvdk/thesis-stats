"""Tests for src/geography.py — country-to-continent mapping."""

import math

from src.analysis.geography import get_continent


class TestGetContinent:
    def test_single_country_usa(self):
        assert get_continent("USA") == "North America"

    def test_single_country_netherlands(self):
        assert get_continent("Netherlands") == "Europe"

    def test_single_country_japan(self):
        assert get_continent("Japan") == "Asia"

    def test_single_country_brazil(self):
        assert get_continent("Brazil") == "South America"

    def test_single_country_australia(self):
        assert get_continent("Australia") == "Oceania"

    def test_single_country_south_africa(self):
        assert get_continent("South Africa") == "Africa"

    def test_none_returns_unknown(self):
        assert get_continent(None) == "Unknown"

    def test_unknown_country(self):
        assert get_continent("Atlantis") == "Other"

    def test_multi_country_same_continent(self):
        assert get_continent("Belgium and Spain") == "Europe"

    def test_multi_country_multi_continent(self):
        result = get_continent("USA and Japan")
        assert result == "Multi-continent"

    def test_europe_wrapper(self):
        result = get_continent("Europe (Belgium, Greece, UK)")
        assert result == "Europe"

    def test_empty_string(self):
        assert get_continent("") == "Other"

    def test_korea_alias(self):
        assert get_continent("Korea") == "Asia"

    def test_mexico_in_south_america(self):
        assert get_continent("Mexico") == "South America"
