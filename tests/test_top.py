"""Tests for RepoReport.top_authors and RepoReport.top_hotspots."""

from philiprehberger_git_analyzer import AuthorStats, RepoReport


def _build_authors_report() -> RepoReport:
    report = RepoReport()
    report.authors = [
        AuthorStats(name="Alice", email="alice@example.com", commits=5),
        AuthorStats(name="Bob", email="bob@example.com", commits=20),
        AuthorStats(name="Carol", email="carol@example.com", commits=10),
    ]
    return report


def _build_hotspots_report() -> RepoReport:
    report = RepoReport()
    report._file_changes = {
        "src/a.py": 5,
        "src/b.py": 20,
        "src/c.py": 10,
    }
    return report


def test_top_authors_returns_top_n_descending():
    report = _build_authors_report()
    top = report.top_authors(2)
    assert len(top) == 2
    assert top[0].name == "Bob"
    assert top[0].commits == 20
    assert top[1].name == "Carol"
    assert top[1].commits == 10


def test_top_authors_n_larger_than_count_returns_all():
    report = _build_authors_report()
    top = report.top_authors(100)
    assert len(top) == 3
    assert [a.commits for a in top] == [20, 10, 5]


def test_top_authors_zero_returns_empty():
    report = _build_authors_report()
    assert report.top_authors(0) == []


def test_top_hotspots_returns_top_n_descending():
    report = _build_hotspots_report()
    top = report.top_hotspots(2)
    assert len(top) == 2
    assert top[0].path == "src/b.py"
    assert top[0].change_count == 20
    assert top[1].path == "src/c.py"
    assert top[1].change_count == 10


def test_top_hotspots_n_larger_than_count_returns_all():
    report = _build_hotspots_report()
    top = report.top_hotspots(100)
    assert len(top) == 3
    assert [h.change_count for h in top] == [20, 10, 5]


def test_top_hotspots_zero_returns_empty():
    report = _build_hotspots_report()
    assert report.top_hotspots(0) == []
