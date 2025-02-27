from contextlib import contextmanager
from os import chdir, getcwd
from pathlib import Path
from re import sub
from subprocess import CalledProcessError, run

from pandas import DataFrame, concat, read_csv, to_datetime


@contextmanager
def directory(dir_path: str | Path):
    original_dir = getcwd()
    try:
        chdir(dir_path)
        yield
    finally:
        chdir(original_dir)


def get_stdout(*tokens) -> str:
    # skip falsy tokens and run the command
    token_list = [str(token) for token in tokens if token]
    try:
        proc = run(token_list, text=True, capture_output=True, check=True)
    except CalledProcessError as e:
        cmd = " ".join(token_list)
        raise RuntimeError(f"Command `{cmd}` failed with returncode {e.returncode}\n"
                           f"  stdout:\n{e.stdout}\n\n"
                           f"  stderr:\n{e.stderr}") from e
    # remove ANSI escape sequences
    escape_sequence_pattern = r"\x1b\[[0-9;]*[a-zA-Z]"
    cleaned_output = sub(escape_sequence_pattern, "", proc.stdout)
    return cleaned_output.strip()


def parse_tab_seperated_gh_output(stdout: str) -> DataFrame:
    lines = stdout.splitlines()
    headers = [header.lower() for header in lines[2].split("\t")]
    data = [line.split("\t") for line in lines[3:]]  # rows
    transpose = zip(*data)  # cols
    df_data: dict[str, list] = {}
    for col_header, col_data in zip(headers, transpose):
        df_data[col_header] = col_data
    return DataFrame(df_data)


def parse_grades_csv(path: str | Path) -> DataFrame:
    data = read_csv(path)
    data.set_index(["assignment_name", "assignment_url", "github_username"], inplace=True)
    data = data[["student_repository_url", "submission_timestamp"]]
    data["submission_timestamp"] = to_datetime(data["submission_timestamp"])
    return data


def parse_grades_csvs(paths: list[str | Path] | None = None) -> DataFrame:
    """
    Parse a list of ``grades.csv`` files.

    :param paths: List of paths to ``grades.csv`` files.
    :return: The relevant data, loaded into a dataframe.
    """
    if paths is None:
        paths = list(Path().glob("*grades*.csv"))
    paths = [Path(p).resolve() for p in paths]

    return concat([parse_grades_csv(path) for path in paths])


def parse_cloned_paths(stdout: str) -> list[Path]:
    """
    Parse output of ``gh classroom`` subcommands of the form ``Cloned into: <path>``.

    :param stdout: The subcommands stdout.
    :return: A list of paths.
    """
    clone_prefix = "Cloning into: "
    cloned_paths = [
        Path(line[len(clone_prefix):])
        for line in stdout.splitlines()
        if line.startswith(clone_prefix)
    ]
    return cloned_paths
