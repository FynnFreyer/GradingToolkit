from dataclasses import dataclass
from datetime import datetime, date
from functools import cached_property
from pathlib import Path
from subprocess import run
from typing import Self
from xml.etree import ElementTree as ET

from pandas import to_datetime, to_numeric, DataFrame, read_csv

from github_classroom_toolkit.utils import get_stdout, parse_tab_seperated_gh_output, directory
from github_classroom_toolkit.utils import parse_grades_csv
import re
import shutil


@dataclass
class Classroom:
    """A GitHub classroom, containing exercises."""
    id: int
    name: str
    url: str

    @classmethod
    def get_classrooms(cls) -> list[Self]:
        stdout = get_stdout("gh", "classroom", "ls")  # ls output is not tab separated
        rooms = []
        for line in stdout.splitlines()[3:]:
            parts = line.split()
            room_id = int(parts[0])
            room_name = " ".join(parts[1: -1])
            room_url = parts[-1]
            rooms.append(cls(int(room_id), room_name, room_url))
        return rooms

    @property
    def assignments(self) -> list["Assignment"]:
        return Assignment.from_classroom(self)


@dataclass
class Assignment:
    classroom: Classroom
    id: int
    title: str
    deadline: datetime
    invite: str
    base_dir: Path

    # TODO: add properties
    # starter_code: Repo
    #slug : str

    @classmethod
    def from_classroom(cls, classroom: Classroom) -> list[Self]:
        stdout = get_stdout("gh", "classroom", "assignments", "-c", classroom.id)
        assignment_data = parse_tab_seperated_gh_output(stdout)
        # wrangle data
        assignment_data["id"] = to_numeric(assignment_data["id"])
        assignment_data["deadline"] = to_datetime(assignment_data["deadline"])
        # throw away useless bits
        assignment_data = assignment_data[["id", "title", "deadline", "invitation link"]]
        # cast to assignment objects
        assignments = assignment_data.apply(lambda row: cls(classroom, *row), axis=1).tolist()
        return assignments

    def rename_folder_and_repos(self):
        """
        Rename the base folder from 'hausaufgabe-{n}-submissions' to 'hausaufgabe-{n}' and each repo from '
        hausaufgabe-{n}-[student_name] to '[student-name]'
        """
        target_dir = None
        for subdir in self.base_dir.iterdir():
            if subdir.is_dir() and re.match(r"hausaufgabe-\d+-submissions", subdir.name):
                target_dir = subdir
                break

        if target_dir is None:
            raise FileExistsError

        match = re.match(r"(hausaufgabe-(\d+))-submissions", target_dir.name)
        if not match:
            raise ValueError

        assignment_base_name = match.group(1)
        new_folder_path = self.base_dir / assignment_base_name

        shutil.move(target_dir, new_folder_path)

        print(f"Renamed base folder to '{assignment_base_name}'.")

        for repo_dir in new_folder_path.iterdir():
            if repo_dir.is_dir():
                repo_match = re.match(rf"{assignment_base_name}-(.+)", repo_dir.name)
                if repo_match:
                    student_name = repo_match.group(1)
                    new_repo_path = new_folder_path / student_name
                    repo_dir.rename(new_repo_path)
                    print(f"Renamed repo folder to {new_repo_path}.")

    @property
    def grades(self) -> DataFrame:
        grades_csv = Path(f"{self.id}_grades.csv")
        if not grades_csv.exists():
            cmd = ["gh", "classroom", "assignment-grades", "-a", str(self.id), "-f", str(grades_csv)]
            run(cmd, check=True)
        return parse_grades_csv(grades_csv)

    @property
    def submissions(self) -> list["Submission"]:
        return Submission.from_assignment(self)


@dataclass
class Student:
    """A student of the course."""

    github_name: str
    first_name: str
    last_name: str
    email: str

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @classmethod
    def from_student_data(cls, student_data_csv: str | Path) -> list[Self]:
        student_data = read_csv(student_data_csv)
        return student_data.apply(lambda row: cls(*row), axis=1).tolist()


@dataclass
class Submission:
    assignment: Assignment
    # TODO:
    # student: Student
    username: str
    repo_url: str
    timestamp: datetime

    @classmethod
    def from_assignment(cls, assignment: Assignment) -> list[Self]:
        grades_data = assignment.grades
        # move gh account name out of index and throw away useless bits
        grades_data = grades_data.reset_index(level="github_username")
        grades_data = grades_data[["github_username", "student_repository_url", "submission_timestamp"]]
        # cast to submissions objects
        submissions = grades_data.apply(lambda row: cls(assignment, *row), axis=1).tolist()
        return submissions


@dataclass
class Repo:
    """A repository containing an exercise submission."""


@dataclass
class RepoManager:
    base_dir: Path
    classroom: Classroom

    def download_submissions(self) -> dict[Submission, Path]:
        """
        Download student submissions by cloning repositories.
        :return:
        """
        self.clone_student_repos()
        submission_map = {}
        for assignment in self.classroom.assignments:
            for submission in assignment.submissions:
                path = self.base_dir / submission.username / assignment.title
                if path.exists():  # clone
                    path.mkdir(parents=True)
                    run(["git", "pull"], check=True)
                    submission_map[submission] = path
                else:  # update
                    with directory(path):
                        run(["git", "pull"], check=True)
        return submission_map

    def clone_student_repos(self):
        """
        Automatically clone student repositories using the gh classroom command.
        """
        run(["gh", "classroom", "clone", "student-repos", "-a", str(self.classroom.id), "-d", str(self.base_dir)], check=True)

    @cached_property
    def assignment_map(self) -> dict[str, Assignment]:
        return {assignment.title: assignment for assignment in self.classroom.assignments}

    def get_latest_commit_hash(self, deadline: date | datetime | None = None, branch: str | None = None) -> str:
        """
        Get the hash of the last commit on the specified branch before the specified date.

        :param deadline: Optionally, a cutoff date or datetime. Will take the latest commit overall if left ``None``.
        :param branch: Optionally, a branch name. Will take the latest commit overall if left ``None``.
        :return: The hash of the latest commit fulfilling the specified criteria.
        """
        if deadline is not None:
            deadline = f"--before='{deadline.isoformat()}'"
        return get_stdout("git", "log", branch, deadline, "-n", 1, "--format='%H'")

    def restore_tests(self):
        ...

    # def test_repos(self) -> ():
    #     ...

    def find_test_xmls(self, user_map: dict[str, Student]) -> dict[Student, dict[Assignment, "Grade"]]:
        run(["./gradlew", "test", "aggregate", "--info"], check=True)

        aggregate_dir = Path("build/reports/aggregate")
        test_results = list(aggregate_dir.glob("*/*_TEST-*.xml"))
        test_file_map = {user: {assignment: [] for assignment in self.assignment_map.values()} for user in
                         user_map.values()}

        for result in test_results:
            account_name = result.parent.name
            user = user_map.get(account_name)

            assignment_name, _test_name = result.name.split("_TEST-")
            assignment = self.assignment_map.get(assignment_name)

            test_file_map.get(user, dict()).get(assignment, list()).append(result)

        return {user: {assignment: Grade.from_test_xmls(user, submission, )} for user, assignment_dict in
                test_file_map.items()}


@dataclass
class Grade:
    user: Student
    submission: Submission
    points_available: int
    points_received: int

    @property
    def percentage(self) -> float:
        return self.points_received / self.points_available

    @property
    def is_passing_grade(self) -> bool:
        return self.percentage >= 0.5

    @classmethod
    def from_test_xmls(cls, user: Student, submission: Submission, test_xmls: list[str | Path]) -> Self:
        points_available = 0
        points_received = 0
        for test_xml in test_xmls:
            # retrieve data
            root = ET.parse(test_xml).getroot()
            tests = int(root.attrib['tests'])
            skipped = int(root.attrib['skipped'])
            failures = int(root.attrib['failures'])
            errors = int(root.attrib['errors'])

            # calculate points from this test
            points_available_here = tests - skipped
            points_received_here = points_available_here - failures - errors

            # add to tally
            points_available += points_available_here
            points_received += points_received_here

        return cls(user, submission, points_available, points_received)

# Test cloning and renaming
# if __name__ == "__main__":
#     base_dir = Path("../../test")
#     classroom_id = 622847
#     classroom = Classroom(id=classroom_id, name="Test Classroom", url="https://classroom.github.com/a/xITCpvlP")
#     repo_manager = RepoManager(base_dir=base_dir, classroom=classroom)
#     repo_manager.clone_student_repos()
#     assignment = Assignment(classroom, classroom_id, "Hausaufgabe 5", datetime.now(), "https://classroom.github.com/a/xITCpvlP", base_dir)
#     assignment.rename_folder_and_repos()