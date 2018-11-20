"""Code quality tests for KAOS."""

def test_code_quality():
    """Pylint test."""
    from pylint import epylint as lint
    assert not lint.py_run("kaos")
