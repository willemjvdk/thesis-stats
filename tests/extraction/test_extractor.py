"""Tests for _parse_response — the JSON parser inside extractor.py.

This is the most critical pure function: it takes the raw API response text
and turns it into a list of arm dicts. We test every parsing path without
making any API calls.
"""

from src.extraction.llm_utils import _parse_response


def test_single_object():
    """Standard case: model returns one JSON object."""
    raw = '{"arm": "treat1", "n": 50}'
    assert _parse_response(raw) == [{"arm": "treat1", "n": 50}]


def test_array_of_objects():
    """Model returns multiple arms as a JSON array."""
    raw = '[{"arm": "treat1", "n": 50}, {"arm": "control", "n": 48}]'
    result = _parse_response(raw)
    assert len(result) == 2
    assert result[0]["arm"] == "treat1"
    assert result[1]["arm"] == "control"


def test_markdown_code_fence():
    """Model wraps JSON in ```json ... ``` — strip the fences."""
    raw = '```json\n{"arm": "treat1", "n": 50}\n```'
    assert _parse_response(raw) == [{"arm": "treat1", "n": 50}]


def test_plain_code_fence():
    """Model uses ``` without a language specifier."""
    raw = '```\n{"arm": "treat1"}\n```'
    assert _parse_response(raw) == [{"arm": "treat1"}]


def test_multiple_loose_objects():
    """Fallback bracket-matching path: two objects without an array wrapper.
    Some models output one object per arm on separate lines.
    """
    raw = '{"arm": "treat1", "n": 50}\n{"arm": "control", "n": 48}'
    result = _parse_response(raw)
    assert len(result) == 2
    assert result[0]["arm"] == "treat1"
    assert result[1]["arm"] == "control"


def test_empty_string():
    assert _parse_response("") == []


def test_not_json():
    assert _parse_response("Sorry, I cannot extract data from this paper.") == []
