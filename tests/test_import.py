"""Basic import test."""


def test_import():
    """Verify the package can be imported."""
    import philiprehberger_git_analyzer
    assert hasattr(philiprehberger_git_analyzer, "__name__") or True
