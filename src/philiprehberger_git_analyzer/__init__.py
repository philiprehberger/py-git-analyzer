"""Git repository statistics and commit analysis."""

from __future__ import annotations

import subprocess
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

__all__ = ["analyze", "RepoReport", "AuthorStats", "FileHotspot"]


def _git(args: list[str], repo_path: str = ".") -> str:
    result = subprocess.run(
        ["git"] + args,
        cwd=repo_path,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


@dataclass
class AuthorStats:
    """Statistics for a single author."""

    name: str
    email: str
    commits: int = 0
    additions: int = 0
    deletions: int = 0
    first_commit: datetime | None = None
    last_commit: datetime | None = None

    @property
    def lines_changed(self) -> int:
        return self.additions + self.deletions


@dataclass
class FileHotspot:
    """A file that changes frequently."""

    path: str
    change_count: int
    last_changed: str | None = None


@dataclass
class RepoReport:
    """Complete repository analysis report."""

    total_commits: int = 0
    contributor_count: int = 0
    first_commit_date: str | None = None
    last_commit_date: str | None = None
    authors: list[AuthorStats] = field(default_factory=list)
    commits_by_day: dict[str, int] = field(default_factory=dict)
    commits_by_hour: dict[int, int] = field(default_factory=dict)
    commits_by_weekday: dict[int, int] = field(default_factory=dict)
    file_extensions: dict[str, int] = field(default_factory=dict)
    _file_changes: dict[str, int] = field(default_factory=dict)
    _file_last_changed: dict[str, str] = field(default_factory=dict)

    @property
    def most_changed_file(self) -> str | None:
        if not self._file_changes:
            return None
        return max(self._file_changes, key=self._file_changes.get)

    @property
    def commits_per_week(self) -> float:
        if not self.first_commit_date or not self.last_commit_date:
            return 0.0
        first = datetime.strptime(self.first_commit_date, "%Y-%m-%d")
        last = datetime.strptime(self.last_commit_date, "%Y-%m-%d")
        weeks = max((last - first).days / 7, 1)
        return round(self.total_commits / weeks, 1)

    def hotspots(self, limit: int = 10) -> list[FileHotspot]:
        """Get the most frequently changed files."""
        sorted_files = sorted(
            self._file_changes.items(),
            key=lambda x: x[1],
            reverse=True,
        )[:limit]
        return [
            FileHotspot(
                path=path,
                change_count=count,
                last_changed=self._file_last_changed.get(path),
            )
            for path, count in sorted_files
        ]

    def activity_heatmap(self) -> dict[int, dict[int, int]]:
        """Returns activity by weekday (0=Mon) and hour."""
        return dict(self._heatmap)

    _heatmap: dict[int, dict[int, int]] = field(default_factory=lambda: defaultdict(lambda: defaultdict(int)))


def analyze(
    repo_path: str = ".",
    branch: str | None = None,
    max_commits: int | None = None,
) -> RepoReport:
    """Analyze a git repository.

    Args:
        repo_path: Path to the git repository.
        branch: Branch to analyze (default: current branch).
        max_commits: Limit number of commits to analyze.

    Returns:
        RepoReport with all statistics.
    """
    report = RepoReport()

    # Get commit log
    log_args = ["log", "--pretty=format:%H|%ad|%an|%ae", "--date=iso"]
    if branch:
        log_args.append(branch)
    if max_commits:
        log_args.extend(["-n", str(max_commits)])

    raw_log = _git(log_args, repo_path)
    if not raw_log:
        return report

    # Parse commits
    author_map: dict[str, AuthorStats] = {}
    day_counter: Counter[str] = Counter()
    hour_counter: Counter[int] = Counter()
    weekday_counter: Counter[int] = Counter()
    heatmap: dict[int, dict[int, int]] = defaultdict(lambda: defaultdict(int))

    lines = raw_log.splitlines()
    report.total_commits = len(lines)

    dates: list[datetime] = []

    for line in lines:
        parts = line.split("|", 3)
        if len(parts) < 4:
            continue
        commit_hash, date_str, name, email = parts

        try:
            dt = datetime.fromisoformat(date_str.strip())
        except ValueError:
            continue

        dates.append(dt)
        day_str = dt.strftime("%Y-%m-%d")
        day_counter[day_str] += 1
        hour_counter[dt.hour] += 1
        weekday_counter[dt.weekday()] += 1
        heatmap[dt.weekday()][dt.hour] += 1

        key = f"{name}|{email}"
        if key not in author_map:
            author_map[key] = AuthorStats(name=name, email=email)
        author = author_map[key]
        author.commits += 1
        if author.first_commit is None or dt < author.first_commit:
            author.first_commit = dt
        if author.last_commit is None or dt > author.last_commit:
            author.last_commit = dt

    if dates:
        dates.sort()
        report.first_commit_date = dates[0].strftime("%Y-%m-%d")
        report.last_commit_date = dates[-1].strftime("%Y-%m-%d")

    # Get per-author stats (additions/deletions)
    try:
        shortlog = _git(["shortlog", "-sne", "HEAD"], repo_path)
    except RuntimeError:
        pass

    # Get file change counts
    try:
        log_args = ["log", "--pretty=format:", "--name-only", "--diff-filter=ACDMR"]
        if branch:
            log_args.append(branch)
        if max_commits:
            log_args.extend(["-n", str(max_commits)])
        file_log = _git(log_args, repo_path)
        file_counter: Counter[str] = Counter()
        for fname in file_log.splitlines():
            fname = fname.strip()
            if fname:
                file_counter[fname] += 1
        report._file_changes = dict(file_counter)
    except RuntimeError:
        pass

    # Language breakdown by extension
    try:
        tracked = _git(["ls-files"], repo_path)
        ext_counter: Counter[str] = Counter()
        for f in tracked.splitlines():
            f = f.strip()
            if f:
                ext = Path(f).suffix.lower()
                if ext:
                    ext_counter[ext] += 1
        report.file_extensions = dict(ext_counter.most_common())
    except RuntimeError:
        pass

    report.authors = sorted(author_map.values(), key=lambda a: a.commits, reverse=True)
    report.contributor_count = len(report.authors)
    report.commits_by_day = dict(day_counter)
    report.commits_by_hour = dict(hour_counter)
    report.commits_by_weekday = dict(weekday_counter)
    report._heatmap = {k: dict(v) for k, v in heatmap.items()}

    return report
