import sys
from datetime import date
from pathlib import Path

docs_root = Path(__file__).parent.resolve()
repo_root = docs_root.parent

# add src/ to python path
sys.path.append(str(repo_root / "src"))

# import project data
from github_classroom_toolkit.__about__ import __authors__, __project_name__, __version__

# format author information
author_names = [author["name"] for author in __authors__]
authors_plain = "; ".join(author_names)
authors_latex = r" \and ".join(author_names)

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = __project_name__
author = authors_plain
copyright = f"Copyright {date.today().year} {authors_plain}"
version = __version__

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.doctest",
    "sphinx.ext.mathjax",
    "sphinxcontrib.mermaid",
    "sphinxcontrib.plantuml",
    "sphinxcontrib.relativeinclude",
]

templates_path = ["templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- Options for output ------------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-latex-output

html_theme = "classic"
html_static_path = ["static"]

# export these variables for usage in rst files
rst_epilog = f"""
.. |project| replace:: {project}
.. |version| replace:: {version}
.. |author| replace:: {author}
.. |copyright| replace:: {copyright}
"""

author_latex = r" \and ".join(author_names)
# latex_engine = "xelatex"
latex_documents = [
    ("index", f"{project}.tex", "", author_latex, "manual"),
]

latex_elements = {
    "extraclassoptions": "openany,oneside",
    "papersize": "a4paper",
    "pointsize": "12pt",
    "figure_align": "H",
    "preamble": r"""
        % One line per author on title page
        % cf. https://github.com/jfbu/matplotlib/commit/da0f35a535183d3cf5611063abfe254f0c2be975
        \DeclareRobustCommand{\and}%
          {\end{tabular}\kern-\tabcolsep\\\begin{tabular}[t]{c}}%
    """,
}

# -- Autodoc configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html
# https://www.sphinx-doc.org/en/master/usage/extensions/autosummary.html

add_module_names = False

autodoc_mock_imports = []
autodoc_member_order = "bysource"

autosummary_context = {
    "project": project,
    "version": version,
}

# -- Diagram options ---------------------------------------------------------
# https://pypi.org/project/sphinxcontrib-mermaid/
# https://pypi.org/project/sphinxcontrib-plantuml/

mermaid_cmd = "npx --yes -p @mermaid-js/mermaid-cli mmdc"

plantuml = f"java -jar {docs_root / 'plantuml/plantuml-mit.jar'}"
plantuml_latex_output_format = "eps"
