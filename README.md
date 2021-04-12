# philiprehberger-git-analyzer

[![Tests](https://github.com/philiprehberger/py-git-analyzer/actions/workflows/publish.yml/badge.svg)](https://github.com/philiprehberger/py-git-analyzer/actions/workflows/publish.yml)
[![PyPI version](https://img.shields.io/pypi/v/philiprehberger-git-analyzer.svg)](https://pypi.org/project/philiprehberger-git-analyzer/)
[![License](https://img.shields.io/github/license/philiprehberger/py-git-analyzer)](LICENSE)

Git repository statistics and commit analysis.

## Install

```bash
pip install philiprehberger-git-analyzer
```

## Usage

```python
from philiprehberger_git_analyzer import analyze

report = analyze(".")

print(f"Total commits: {report.total_commits}")
print(f"Contributors: {report.contributor_count}")
print(f"Most active file: {report.most_changed_file}")
print(f"Commits/week: {report.commits_per_week}")

# Per-author stats
for author in report.authors:
    print(f"{author.name}: {author.commits} commits")

# File hotspots (most changed files)
for file in report.hotspots(limit=10):
    print(f"{file.path}: {file.change_count} changes")

# Language breakdown
for ext, count in report.file_extensions.items():
    print(f"{ext}: {count} files")

# Activity patterns
print(report.commits_by_hour)      # {9: 42, 10: 38, ...}
print(report.commits_by_weekday)   # {0: 120, 1: 115, ...} (0=Mon)
print(report.activity_heatmap())   # {weekday: {hour: count}}
```

## API

### `analyze(repo_path, branch?, max_commits?) -> RepoReport`

| Field | Description |
|-------|-------------|
| `total_commits` | Total number of commits |
| `contributor_count` | Number of unique authors |
| `first_commit_date` | Date of earliest commit |
| `last_commit_date` | Date of latest commit |
| `commits_per_week` | Average commits per week |
| `most_changed_file` | File with most changes |
| `authors` | List of AuthorStats |
| `file_extensions` | Extension → file count |
| `commits_by_day` | Date → commit count |
| `commits_by_hour` | Hour → commit count |
| `commits_by_weekday` | Weekday → commit count |
| `hotspots(limit)` | Most frequently changed files |
| `activity_heatmap()` | Weekday × hour activity matrix |


## Development

```bash
pip install -e .
python -m pytest tests/ -v
```

## License

MIT
