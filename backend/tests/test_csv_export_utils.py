import pytest
from fastapi import HTTPException

from backend.app.api.routes import _parse_csv_columns, _safe_filename_fragment, _sanitize_csv_cell


def test_sanitize_csv_cell_handles_none():
    assert _sanitize_csv_cell(None) == ""


def test_sanitize_csv_cell_prefixes_formula_like_values():
    assert _sanitize_csv_cell("=SUM(A1:A2)") == "'=SUM(A1:A2)"
    assert _sanitize_csv_cell("+1+2") == "'+1+2"
    assert _sanitize_csv_cell("-42") == "'-42"
    assert _sanitize_csv_cell("@username") == "'@username"


def test_sanitize_csv_cell_keeps_normal_text():
    assert _sanitize_csv_cell("u/naive-user") == "u/naive-user"


def test_safe_filename_fragment_normalizes_input():
    assert _safe_filename_fragment("AI & Ethics / 2026") == "AI-Ethics-2026"


def test_safe_filename_fragment_fallback_when_empty():
    assert _safe_filename_fragment("   ") == "search"


def test_parse_csv_columns_returns_default_order_when_not_provided():
    columns = _parse_csv_columns(None)
    assert columns == [
        "source_post_id",
        "author",
        "subreddit",
        "title",
        "body",
        "permalink",
        "posted_at",
        "neg_score",
        "neu_score",
        "pos_score",
        "compound_score",
        "sentiment_label",
    ]


def test_parse_csv_columns_supports_comma_separated_and_repeated_params():
    columns = _parse_csv_columns(["title, sentiment_label", "author", "title"])
    assert columns == ["author", "title", "sentiment_label"]


def test_parse_csv_columns_rejects_invalid_values():
    with pytest.raises(HTTPException) as exc:
        _parse_csv_columns(["title", "not_a_column"])

    assert exc.value.status_code == 400
    assert "Invalid CSV columns" in str(exc.value.detail)


def test_parse_csv_columns_rejects_empty_input_values():
    with pytest.raises(HTTPException) as exc:
        _parse_csv_columns([" ,  ", ""])

    assert exc.value.status_code == 400
    assert "At least one valid CSV column" in str(exc.value.detail)
