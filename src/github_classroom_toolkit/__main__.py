from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import Sequence

from github_classroom_toolkit.model.course import Course, Grade, Student
from github_classroom_toolkit.model.github import Classroom, Assignment


def parse_args(args: Sequence[str] | None = None) -> Namespace:
    parser = ArgumentParser()

    # mutex group classroom/assignment
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-c", "--classroom", type=Classroom.from_id,
                        help="the ID of the GitHub classroom to grade")
    group.add_argument("-a", "--assignment", type=Assignment.from_id,
                        help="the ID of the GitHub assignment to grade")

    parser.add_argument("-s", "--students", type=Student.from_student_data, required=True,
                        help="path to a CSV with names and GitHub accounts of students")

    return parser.parse_args(args)


def main(args: Namespace | None = None):
    args = args or parse_args()

    if args.classroom:
        course = Course(args.classroom, args.students)
        results = Grade.grade_course(course)
        out = f"grades_classroom_{course.classroom.id}.csv"
    elif args.assignment:
        assignment: Assignment = args.assignment
        out = f"grades_assignment_{assignment.id}.csv"
        results = Grade.grade_assignment(args.assignment)
    else:
        # should never happen bc of mutex group, but keeps the IDE happy
        raise NotImplementedError("Only grading classrooms and assignments is supported")

    grades = Grade.tabulate_results(results)
    grades.reset_index().to_csv(out, index=False)


if __name__ == "__main__":
    main()
