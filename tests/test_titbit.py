"""Tests for behaviors that need fixtures (the rest of the suite is doctests)."""

import subprocess

from titbit import git_action_on_projects


def _init_git_repo(path):
    for cmd in (
        ["git", "init", "-q"],
        ["git", "config", "user.email", "test@example.com"],
        ["git", "config", "user.name", "Test"],
        ["git", "commit", "-q", "--allow-empty", "-m", "init"],
    ):
        subprocess.run(cmd, cwd=path, check=True, capture_output=True)


def test_git_action_on_projects_runs_action_per_project(tmp_path):
    repo = tmp_path / "proj"
    repo.mkdir()
    _init_git_repo(repo)

    results = list(git_action_on_projects([str(repo)], action="status"))

    assert len(results) == 1
    assert "branch" in results[0]  # `git status` stdout mentions the branch


def test_git_action_on_projects_reports_errors_without_raising(tmp_path):
    not_a_repo = tmp_path / "empty"
    not_a_repo.mkdir()

    errors = []
    results = list(
        git_action_on_projects(
            [str(not_a_repo)],
            action="status",
            on_error=lambda project, e: errors.append((project, e)),
        )
    )

    # the generator completes; the failed action yields None (error printed)
    assert results == [None]
