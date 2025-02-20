from dataclasses import dataclass
from datetime import datetime
from functools import cache, cached_property
from pathlib import Path
from re import MULTILINE, search
from shutil import move
from subprocess import CalledProcessError, run
from tempfile import TemporaryDirectory
from typing import Self

from pandas import DataFrame, to_datetime, to_numeric

from github_classroom_toolkit.model.git import Repository
from github_classroom_toolkit.utils import (get_stdout, parse_cloned_paths, parse_grades_csv,
                                            parse_tab_seperated_gh_output)


@dataclass(frozen=True)
class Classroom:
    """A GitHub classroom for a specific course. It contains assignments."""

    id: int
    """The ID of this classroom."""

    name: str
    """The name of this classroom."""

    url: str
    """The URL of this classroom."""

    base_dir: Path = None
    """The directory to use for storing starter code and submissions for assigned work."""

    def __post_init__(self):
        # TODO: doing this here seems super clumsy and like a bad idea in general
        # ensure that the classroom has a base directory to clone assignment data into
        object.__setattr__(self, "base_dir", Path("repos").resolve())
        self.base_dir.mkdir(exist_ok=True)

    @property
    def slug(self) -> str:
        """The slug from the url."""
        return self.url.split("/")[-1]

    @classmethod
    @cache
    def from_id(cls, classroom_id: int) -> Self:
        """
        Retrieve a classroom based on its ID.

        :param classroom_id: The ID of the classroom.
        :raise ValueError: On failure to retrieve classroom data or parse it.
        :return: The classroom with the passed ID.
        """
        try:
            stdout = get_stdout("gh", "classroom", "view", "-c", classroom_id)
            id = int(search(r"ID: (\d+)$", stdout, MULTILINE).group(1))
            name = search(r"Name: (.+)$", stdout, MULTILINE).group(1)
            url = search(r"Classroom URL: (.+)$", stdout, MULTILINE).group(1)
            return cls(id, name, url)
        except CalledProcessError as e:
            raise ValueError("Failed to retrieve classroom data.") from e
        except AttributeError as e:
            raise ValueError("Failed to parse output of `gh classroom view`.") from e

    @classmethod
    @cache
    def get_classrooms(cls) -> tuple[Self, ...]:
        """
        Get a tuple of all classrooms you have access to.

        :return: A tuple of all classrooms that one has access to.
        """
        stdout = get_stdout("gh", "classroom", "ls")  # ls output is not tab separated
        rooms = []
        for line in stdout.splitlines()[3:]:
            parts = line.split()
            room_id = int(parts[0])
            room_name = " ".join(parts[1: -1])
            room_url = parts[-1]
            rooms.append(cls(int(room_id), room_name, room_url))
        return tuple(rooms)

    @cached_property
    def assignments(self) -> tuple["Assignment", ...]:
        """A tuple of assignments for this classroom."""
        return Assignment.from_classroom(self)


@dataclass(frozen=True)
class Assignment:
    """Assigned work."""

    classroom: Classroom
    """The classroom this assignment belongs to."""

    id: int
    """The ID of this assignment."""

    title: str
    """The title of this assignment."""

    deadline: datetime | None
    """The deadline by which a solution for this assignment needs to be submitted."""

    invite_url: str
    """The URL under which this assignment may be accepted."""

    starter_code: Repository = None
    """A :class:`~github_classroom_toolkit.model.git.Repository` containing the starter code for this assignment."""

    def __post_init__(self):
        # download the starter code repository
        object.__setattr__(self, "starter_code", self._clone_starter_code())

    @property
    def slug(self) -> str:
        """The slug that is used as prefix in the student repo URLs."""
        return self.starter_code.path.parent.name

    @classmethod
    @cache
    def from_classroom(cls, classroom: Classroom) -> tuple[Self, ...]:
        """
        Find all assignments for a given class.

        :param classroom: The classroom of which to get the assignments.
        :return: A tuple of assignments.
        """
        # get assignments for classroom
        stdout = get_stdout("gh", "classroom", "assignments", "-c", classroom.id)
        assignment_data = parse_tab_seperated_gh_output(stdout)

        # wrangle assignment data and throw away useless bits
        assignment_data["id"] = to_numeric(assignment_data["id"])
        assignment_data["deadline"] = to_datetime(assignment_data["deadline"])
        assignment_data = assignment_data[["id", "title", "deadline", "invitation link"]]

        # cast to assignment objects
        assignments = assignment_data.apply(lambda row: cls(classroom, *row), axis=1).tolist()
        return tuple(assignments)

    @cached_property
    def grades(self) -> DataFrame:
        """Downloads the ``grades.csv`` file for this assignment and loads it into a DataFrame."""
        grades_csv = Path(f"{self.id}_grades.csv")
        if not grades_csv.exists():
            cmd = ["gh", "classroom", "assignment-grades", "-a", str(self.id), "-f", str(grades_csv)]
            run(cmd, check=True)
        return parse_grades_csv(grades_csv)

    @cache
    def _clone_starter_code(self) -> Repository:
        """
        Clone the starter code into the base directory.

        :raise CalledProcessError: If the ``gh clone`` command fails.
        :return: A :class:`~github_classroom_toolkit.model.git.Repository` containing the assignments starter code.
        """

        with TemporaryDirectory() as tmp:
            # clone the starter code repo to a temp dir
            stdout = get_stdout("gh", "classroom", "clone", "starter-repo", "-a", self.id, "-d", tmp)

            # parse the cloned path and ensure it's exactly one path
            starter_code_paths = parse_cloned_paths(stdout)
            if not len(starter_code_paths) == 1:
                raise ValueError("Unexpected number of starter code repositories.")
            starter_code_path = starter_code_paths[0]

            # construct the assignment_dir path and ensure it exists
            assignment_dir = self.classroom.base_dir / starter_code_path.name
            assignment_dir.mkdir(parents=True, exist_ok=True)

            # construct the destination path and move the repo
            dest_path = assignment_dir / "_starter-code"
            if not dest_path.is_dir():
                move(starter_code_path, dest_path)

            return Repository(dest_path)
