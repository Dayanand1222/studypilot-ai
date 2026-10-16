from pathlib import Path
import ast

APP = Path(__file__).resolve().parents[1] / "app.py"


def test_app_file_exists():
    assert APP.is_file()


def test_app_has_valid_python_syntax():
    ast.parse(APP.read_text(encoding="utf-8"))


def test_expected_features_are_present():
    source = APP.read_text(encoding="utf-8")
    for feature in ("AI Plan Bot", "Video Tutor", "Analytics", "make_plan", "sqlite3"):
        assert feature in source
