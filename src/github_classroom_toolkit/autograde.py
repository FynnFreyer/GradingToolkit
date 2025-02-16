#!/usr/bin/env python
"""
Quick and dirty auto-grading script, in case no free minutes are available for running GitHub actions.
"""

from datetime import date
from os import chdir, getcwd
from pathlib import Path
from shutil import copytree, rmtree
from subprocess import run

from github_classroom_toolkit.model.github import Assignment


def clone_repos(
        assignments: list[Assignment], directory: str | Path | None = None
) -> None:
    if directory is None:
        today = date.today()
        directory = Path.home() / f"tmp/{today}_assignments"
        directory.mkdir(exist_ok=True)
    else:
        directory = Path(directory).resolve()

    cwd = getcwd()
    chdir(directory)
    for assignment in assignments:
        run(["git", "clone", assignment.ssh_url], check=True)
        assignment.base_dir = directory
    chdir(cwd)

