from dataclasses import dataclass
from functools import cache, cached_property
from pathlib import Path
from shutil import move, Error as ShutilError
from subprocess import CompletedProcess, run, CalledProcessError
from typing import ClassVar, Collection, Self
from xml.etree import ElementTree as ET

from pandas import read_csv

from github_classroom_toolkit.model.git import Repository
from github_classroom_toolkit.model.github import Assignment, Classroom
from github_classroom_toolkit.utils import get_stdout, parse_cloned_paths


@dataclass(frozen=True)
class Course:
    """The course to be graded."""

    classroom: Classroom
    """The GitHub classroom for this course."""

    students: tuple["Student", ...]
    """The students in this course."""

    @property
    def student_map(self) -> dict[str, "Student"]:
        """Maps GitHub name to student object."""
        return {student.github_name: student for student in self.students}

    @classmethod
    @cache
    def from_classroom_and_students(cls, classroom_id: int, students_csv: str | Path) -> Self:
        """

        :param classroom_id:
        :param students_csv:
        :return:
        """


@dataclass(frozen=True)
class Student:
    """A student of the course."""

    github_name: str
    """The GitHub account name of this student."""

    first_name: str
    """The first name of this student."""

    last_name: str
    """The last name of this student."""

    email: str
    """The email address of this student."""

    __github_name_map: ClassVar[dict[str, Self]] = {}
    """A dictionary mapping GitHub account names to student objects."""

    def __post_init__(self):
        # add student to lookup table after instantiation
        self.__github_name_map[self.github_name] = self

    @cached_property
    def full_name(self) -> str:
        """The first name, followed by the last name seperated by a space."""
        return f"{self.first_name} {self.last_name}"

    @classmethod
    @cache
    def from_student_data(cls, student_data_csv: str | Path) -> tuple[Self, ...]:
        """
        Parse students from a CSV file.
        The file should have this format:

        +----------------+------------+-----------+------------------------+
        | github_name    | first_name | last_name | email                  |
        +----------------+------------+-----------+------------------------+
        | johndoe123     | John       | Doe       | johndoe@example.com    |
        | janedoe456     | Jane       | Doe       | janedoe@example.com    |
        | devguy789      | Mark       | Smith     | marksmith@example.com  |
        | coderjack99    | Jack       | Turner    | jackturner@example.com |
        | ...            | ...        | ...       | ...                    |
        +----------------+------------+-----------+------------------------+

        :param student_data_csv: Path to a CSV file containing the student data.
        :return: A tuple of students.
        """
        student_data = read_csv(student_data_csv)
        students = student_data.apply(lambda row: cls(*row), axis=1).tolist()
        return tuple(students)

    @classmethod
    @cache
    def from_github_name(cls, github_name: str) -> Self:
        """
        Find a student based on their GitHub account name.

        :param github_name: The GitHub account name of the student.
        :raise KeyError: If name is unknown.
        :return: The student with the specified name.
        """
        return cls.__github_name_map[github_name]


@dataclass(frozen=True)
class Submission:
    assignment: Assignment
    """The :class:`Assignment` that this submission relates to."""

    student: Student
    """The :class:`Student` that submitted this work."""

    repo: Repository
    """The :class:`~github_classroom_toolkit.model.git.Repository` that contains the submitted work."""

    # def __post_init__(self):
    #     # restore tests
    #     self._restore_tests()

    @classmethod
    @cache
    def from_assignment(cls, assignment: Assignment) -> tuple[Self, ...]:
        """
        Download student submissions by cloning repositories.

        :param assignment: The assignment for which to retrieve the submissions.
        :return: A tuple of :class:`Submission` objects for this assignment.
        """

        # clone and rename the submissions
        submission_paths = cls._clone_student_repos(assignment)
        repos = cls._rename_repos(submission_paths)

        # create submissions
        submissions = []
        for repo in repos:
            github_name = repo.path.name
            try:
                student = Student.from_github_name(github_name)
            except KeyError:
                # TODO: replace with log call
                print(f"Couldn't find student: {github_name}")
                continue
            submission = cls(assignment, student, repo)
            submissions.append(submission)
        return tuple(submissions)

    @staticmethod
    def _clone_student_repos(assignment: Assignment) -> tuple[Path, ...]:
        """
        Automatically clone student repositories using the gh classroom command.
        Student repositories are cloned into an assignment directory
        inside the base_dir of the classroom the assignment belongs to.

        :param assignment: The assignment to clone submission repos for.
        :raise CalledProcessError: If the command fails.
        :return: A tuple of paths pointing to the downloaded submissions.
        """
        assignment_dir = assignment.classroom.base_dir / assignment.slug
        assignment_dir.mkdir(parents=True, exist_ok=True)
        submission_paths = []

        # Clone all repositories of one assignment if directory doesn't contain student repos
        only_starter_code = set(assignment_dir.iterdir()) == {assignment_dir / "_starter-code"}
        if only_starter_code:
            # produces directory with `-submission` suffix
            stdout = get_stdout("gh", "classroom", "clone", "student-repos",
                                "-a", assignment.id, "-d", assignment.classroom.base_dir)
            submission_paths = parse_cloned_paths(stdout)
            return tuple(submission_paths)

        # Clone only repositories that don't exist in the assignment-folder
        for (_, _, gh_name), row in assignment.grades.iterrows():
            repo_url = row["student_repository_url"]
            target = assignment_dir / gh_name

            # Skip existing submissions
            if target.is_dir():
                # run(["git", "fetch", "--all"])  # TODO replace with desired git command (slow)
                submission_paths.append(target)
                continue

            # Clone single non existing repository
            try:
                run(["gh", "repo", "clone", repo_url, str(target)], check=True)
                submission_paths.append(target)
            except CalledProcessError as e:
                raise RuntimeError(f"Unexpected error while cloning {gh_name}") from e
        return tuple(submission_paths)

    @staticmethod
    def _rename_repos(submission_paths: Collection[Path]) -> tuple[Repository, ...]:
        """
        Rename the base folder from ``{assignment_slug}-submissions`` to ``{assignment_slug}``
        and each repo from ``{assignment_slug}-{student_name} to ``{student_name}``. Removes empty '-submissions' folder

        :param submission_paths: A collection of paths pointing to the submitted repositories.
        :return: A tuple of :class:`Repository` objects pointing to the renamed submissions.
        """

        repos = []
        moved_parents = set()  # needed later for cleanup
        for submission_path in submission_paths:
            assignment_dir = submission_path.parent
            base_dir = assignment_dir.parent

            if assignment_dir.name.endswith("-submissions"):
                # remove `-submissions` from the end
                assignment_slug = assignment_dir.name.removesuffix("-submissions")
            else:
                assignment_slug = assignment_dir.name

            # skip renaming properly named repos
            if not submission_path.name.startswith(f"{assignment_slug}-"):
                repo = Repository(submission_path)
                repos.append(repo)
                continue

            # remove `<assignment_slug>-` from the start
            github_name = submission_path.name[len(f"{assignment_slug}-"):]
            new_parent = base_dir / assignment_slug
            new_parent.mkdir(parents=True, exist_ok=True)
            new_path = new_parent / github_name

            if not new_path.exists():
                try:
                    move(str(submission_path), str(new_path))
                    moved_parents.add(assignment_dir)
                except (FileExistsError, ShutilError) as e:
                    raise RuntimeError(f"Move failed for {github_name}") from e

            repo = Repository(new_path)
            repos.append(repo)

        # Clean up old '-submissions' directories if empty
        for assignment_dir in moved_parents:
            try:
                assignment_dir.rmdir()
            except OSError as e:
                raise RuntimeError(f"Failed to delete {assignment_dir}") from e

        return tuple(repos)

    def _restore_tests(self) -> None:
        """Restore the contents of ``src/test/`` to the contents of the starter code repository for this assignment."""
        raise NotImplementedError


@dataclass(frozen=True)
class Grade:
    submission: Submission
    points_available: int
    points_received: int

    @cached_property
    def percentage(self) -> float:
        return self.points_received / self.points_available

    @cached_property
    def is_passing_grade(self) -> bool:
        return self.percentage >= 0.5

    @staticmethod
    def test_submissions() -> CompletedProcess:
        return run(["./gradlew", "test", "aggregate", "--info"], check=True)

    @staticmethod
    def find_test_xmls(submissions: Collection[Submission]) -> dict[Submission, tuple[Path, ...]]:
        aggregate_dir = Path("build/reports/aggregate")
        test_results = list(aggregate_dir.glob(f"*/{submissions[0].assignment.slug}_TEST-*.xml"))
        assignment_map = {}
        user_map = {}
        test_file_map = {
            user: {
                assignment: []
                for assignment
                in assignment_map.values()
            }
            for user
            in user_map.values()
        }

        for result in test_results:
            account_name = result.parent.name
            user = user_map.get(account_name)

            assignment_name, _test_name = result.name.split("_TEST-")
            assignment = assignment_map.get(assignment_name)

            test_file_map.get(user, dict()).get(assignment, list()).append(result)

        return {}

    @classmethod
    def from_test_xmls(cls, submission: Submission, test_xmls: Collection[str | Path]) -> Self:
        points_available = 0
        points_received = 0
        for test_xml in test_xmls:
            # retrieve data
            root = ET.parse(test_xml).getroot()
            tests = int(root.attrib["tests"])
            skipped = int(root.attrib["skipped"])
            failures = int(root.attrib["failures"])
            errors = int(root.attrib["errors"])

            # calculate points from this test
            points_available_here = tests - skipped
            points_received_here = points_available_here - failures - errors

            # add to tally
            points_available += points_available_here
            points_received += points_received_here

        return cls(submission, points_available, points_received)
