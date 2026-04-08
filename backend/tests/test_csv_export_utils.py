from backend.app.api.routes import _safe_filename_fragment, _sanitize_csv_cell


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
