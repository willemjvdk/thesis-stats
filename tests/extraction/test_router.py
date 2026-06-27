"""Tests for get_disease — pure path-to-disease-name mapping."""

from pathlib import Path

import pytest

from src.extraction.router import get_disease


def test_returns_disease_from_parent_directory():
    for disease in ("copd", "cvd", "dm"):
        path = Path(f"data/sample/{disease}/some_paper.md")
        assert get_disease(path) == disease


def test_unknown_disease_raises_value_error():
    with pytest.raises(ValueError, match="Unknown disease"):
        get_disease(Path("data/sample/asthma/paper.md"))
