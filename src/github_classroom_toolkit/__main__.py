from argparse import ArgumentParser, Namespace
from pathlib import Path

from github_classroom_toolkit.autograde import clone_repos
from github_classroom_toolkit.utils import parse_grades_csvs


def parse_args(args: list[str] | None = None) -> Namespace:
    parser = ArgumentParser()

    parser.add_argument("csvs", nargs="+", type=Path, help="the GitHub classroom grade CSV files")

    return parser.parse_args(args)


def main(args: Namespace | None = None):
    args = args or parse_args()
    assignments = parse_grades_csvs(args.csv)
    clone_repos(assignments)

    lines = ["user,percentage\n"]
    for assignment in assignments:
        lines.append(f"{assignment.user},{assignment.percentage or 0}\n")
    with open("results/summary.csv", "w") as file:
        file.writelines(lines)


if __name__ == '__main__':
    args = parse_args()
    main(args)