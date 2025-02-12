from contextlib import contextmanager
from os import getcwd, chdir
from pandas import DataFrame, concat, read_csv, to_datetime
from pathlib import Path
from subprocess import run


@contextmanager
def directory(dir_path: str | Path):
    original_dir = getcwd()
    try:
        chdir(dir_path)
        yield
    finally:
        chdir(original_dir)


def get_stdout(*tokens) -> str:
    proc = run([str(token) for token in tokens if token is not None], text=True, capture_output=True, check=True)
    return proc.stdout


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
    if paths is not None:
        paths = [Path(p) for p in paths]
    else:
        paths = list(Path().glob("*grades*.csv"))
    paths = [p.resolve() for p in paths]

    return concat([parse_grades_csv(path) for path in paths])
