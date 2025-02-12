from webbrowser import open_new_tab

from github_classroom_toolkit.model import Assignment


def check_access_settings(assignments: list[Assignment]) -> None:
    for assignment in assignments:
        url = assignment.https_url + "/settings/access"
        open_new_tab(url)
