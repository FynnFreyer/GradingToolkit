from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import Sequence

from github_classroom_toolkit.model.course import Student, Submission
from github_classroom_toolkit.model.github import Classroom


def parse_args(args: Sequence[str] | None = None) -> Namespace:
    parser = ArgumentParser()

    parser.add_argument("-c", "--classroom", type=int, required=True,
                        help="the ID of the GitHub classroom to grade")

    parser.add_argument("-s", "--students", type=Path, required=True,
                        help="path to a CSV with names and GitHub accounts of students")

    return parser.parse_args(args)


def main(args: Namespace | None = None):
    args = args or parse_args()

    students = Student.from_student_data(args.students)
    classroom = Classroom.from_id(args.classroom)

    submission_lists = {
        assignment: Submission.from_assignment(assignment)
        for assignment in classroom.assignments
    }

    print(submission_lists, students)


if __name__ == "__main__":
    main()
