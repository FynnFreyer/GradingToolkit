from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import Sequence

from github_classroom_toolkit.model.course import Course, Grade, Student, Submission
from github_classroom_toolkit.model.github import Classroom


def parse_args(args: Sequence[str] | None = None) -> Namespace:
    parser = ArgumentParser()

    # mutex group classroom/assignment
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-c", "--classroom", type=int,
                        help="the ID of the GitHub classroom to grade")
    group.add_argument("-a", "--assignment", type=int,
                        help="the ID of the GitHub assignment to grade")

    parser.add_argument("-s", "--students", type=Path, required=True,
                        help="path to a CSV with names and GitHub accounts of students")

    return parser.parse_args(args)


def main(args: Namespace | None = None):
    args = args or parse_args()

    if args.classroom:
        course = Course.from_classroom_and_students(args.classroom, args.students)
        course.grade_course("all_grades.csv")
    elif args.assignment:
        raise NotImplementedError("Grading individual assignments is not supported yet")


if __name__ == "__main__":
    main()
