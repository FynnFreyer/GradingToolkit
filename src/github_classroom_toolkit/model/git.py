"""
Module that deals with git related matters.
"""
from dataclasses import dataclass
from datetime import date, datetime
from functools import cached_property
from pathlib import Path
from re import search
from shutil import move
from subprocess import run, CompletedProcess
from typing import Self

from github_classroom_toolkit.utils import directory, get_stdout


class InconsistentRemoteURLError(ValueError):
    """Is raised when a git repository has different fetch and push URLs."""


class RemoteURLNotFoundError(ValueError):
    """Is raised when a remote URL cannot be parsed from the output of ``git remote show <remote>``."""


@dataclass
class Repository:
    """A git repository that was cloned to the local file system."""
    path: Path
    """The directory path of the repository."""

    def __post_init__(self):
        # ensure that paths are resolved and point to a directory
        self.path = self.path.resolve(strict=True)
        if not self.path.is_dir():
            raise ValueError("Path is not a directory.")

    @cached_property
    def origin(self) -> str:
        """The origin remote."""
        return self.get_remote("origin")

    def get_remote(self, remote: str, query: bool = False) -> str:
        """
        Get the fetch and push URL of a specified remote.

        :param remote: The remote to get the URL.
        :param query: Whether to query the remote. (uses the ``-n`` flag)
        :raise InconsistentRemoteURLError: If fetch and push URL are not identical.
        :raise RemoteURLNotFound: If the remote URL can't be determined from the output of ``git remote show <remote>``.
        :return: The remote URL.
        """
        with directory(self.path):
            stdout = get_stdout("git", "remote", "show", "-n" if query else None, remote)

        try:
            fetch_url = search(r"Fetch URL: (\S+)$", stdout).group(1)
            push_url = search(r"Push URL: (\S+)$", stdout).group(1)
        except AttributeError as e:
            raise RemoteURLNotFoundError("Remote URL can't be determined.") from e

        if fetch_url != push_url:
            raise InconsistentRemoteURLError("Fetch and push URL are not identical.")

        return fetch_url

    def move(self, new_path: str | Path) -> Self:
        """
        Move the repository to a new path.

        :param new_path: The path that the repository should be moved to.
        :raise FileExistsError: If the path exists.
        :return: The object itself.
        """
        new_path = Path(new_path).resolve()
        if new_path.exists():
            raise FileExistsError("Path exists.")
        else:
            new_path.parent.mkdir(parents=True, exist_ok=True)

        move(self.path, new_path)
        self.path = new_path
        return self

    def get_latest_commit_hash(self, deadline: date | datetime | None = None, branch: str | None = None) -> str:
        """
        Get the hash of the last commit on the specified branch before the specified date.

        :param deadline: Optionally, a cutoff date or datetime. Will take the latest commit overall if left ``None``.
        :param branch: Optionally, a branch name. Will take the latest commit overall if left ``None``.
        :return: The hash of the latest commit fulfilling the specified criteria.
        """
        if deadline is not None:
            deadline = f"--before='{deadline.isoformat()}'"

        with directory(self.path):
            return get_stdout("git", "log", branch, deadline, "-n", 1, "--format='%H'")

    def checkout(self, branch_or_commit: str = "main") -> CompletedProcess:
        """
        Check out a commit by its hash.

        :param branch_or_commit: The branch or commit (hash) to check out. Defaults to "main".
        :return: Nothing.
        """
        with directory(self.path):
            return run(["git", "checkout", branch_or_commit], check=True)
