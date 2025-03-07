from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import Sequence

from github_classroom_toolkit.model.course import Student, Submission, Grade, Course
from github_classroom_toolkit.model.github import Classroom


def parse_args(args: Sequence[str] | None = None) -> Namespace:
    parser = ArgumentParser()

    # mutex group classroom/assignment
    parser.add_argument("-c", "--classroom", type=int, required=True,
                        help="the ID of the GitHub classroom to grade")

    # mutex arg -a/--assignment...

    parser.add_argument("-s", "--students", type=Path, required=True,
                        help="path to a CSV with names and GitHub accounts of students")

    return parser.parse_args(args)


def main(args: Namespace | None = None):
    args = args or parse_args()

    course = Course.from_classroom_and_students(args.classroom, args.students)

    grades = course.grade_submissions()



if __name__ == "__main__":
    main()
