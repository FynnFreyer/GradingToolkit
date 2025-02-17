##---------------------------------
## Simple rules to automate chores.
##---------------------------------
##

ifeq (${VIRTUAL_ENV},)
 	$(info No venv is active, but this Makefile can only safely be used inside one.)
 	$(info You can usually create and activate a venv with `python3 -m venv venv && source venv/bin/activate`.)
 	$(error Please activate a venv before proceeding)
endif

help:  ## Show this help.
	@sed -ne '/@sed/!s/[^:]*[#][#]//p' $(MAKEFILE_LIST)

##
##
## Dependency Management
##
##   Requirements Files
##

# there are two different targets for each dependency file:
# requirements(-dev) always regenerates the requirements files,
# requirements(-dev).txt only generates them, when they're not found

DEFAULT_COMPILE_ARGS = --generate-hashes --strip-extras --no-annotate

requirements-min: ## (Re-)generate and update requirements.txt.
	uv pip compile $(DEFAULT_COMPILE_ARGS) --upgrade  -o requirements.txt pyproject.toml

# define a variable to check if requirements.txt exists
REQUIREMENTS_EXIST := $(shell if [ -e requirements.txt ]; then echo 1; else echo 0; fi)
requirements.txt: ## Generate requirements.txt, if it doesn't exist yet.
ifeq ($(REQUIREMENTS_EXIST),0)
	uv pip compile $(DEFAULT_COMPILE_ARGS) -o requirements.txt pyproject.toml
endif

requirements-dev: ## (Re-)generate and update requirements-dev.txt.
	uv pip compile  $(DEFAULT_COMPILE_ARGS) --upgrade --extra dev -o requirements-dev.txt pyproject.toml

# define a variable to check if requirements-dev.txt exists
REQUIREMENTS_DEV_EXIST := $(shell if [ -e requirements.txt ]; then echo 1; else echo 0; fi)
requirements-dev.txt: ## Generate requirements-dev.txt, if it doesn't exist yet.
ifeq ($(REQUIREMENTS_DEV_EXIST),0)
	uv pip compile  $(DEFAULT_COMPILE_ARGS) --extra dev -o requirements-dev.txt pyproject.toml
endif

requirements: requirements-min requirements-dev ## (Re-)generate and update both requirements.txt and requirements-dev.txt.

##
##   Installing Dependencies
##

install-min: requirements.txt ## Synchronise contents of venv and requirements.txt.
	uv pip sync requirements.txt

install-dev: requirements-dev.txt ## Synchronise contents of venv and requirements-dev.txt.
	uv pip sync requirements-dev.txt

install: install-dev ## Synonymous with install-dev

##
##   Updating Dependencies
##

update-min: requirements-min install-min ## Regenerate requirements.txt and synchronise the venv.

update-dev: requirements-dev install-dev ## Regenerate requirements-dev.txt and synchronise the venv.

update: requirements-min update-dev ## Regenerate both requirements.txt and requirements-dev.txt and synchronise the venv.

##
##
## Chores
##

logs:
	mkdir -p logs

.PHONY: format lint test type-check chores
format: logs  ## Do code formatting with isort and autopep8.
	python3 -m isort src/ tst/ | tee logs/isort.log
	python3 -m autopep8 -v src/ tst/ | tee logs/autopep8.log

lint: logs  ## Lint the project with ruff.
	python3 -m ruff check --fix src/ tst/ | tee logs/ruff.log

test: logs  ## Run tests with coverage.
	python3 -m pytest --cov src/ | tee logs/pytest.log

type-check: logs  ## Run static type checking with mypy.
	python3 -m mypy src/ tst/ | tee logs/mypy.log

chores: format lint test type-check  ## Format, lint, test and type check the repository.
	@echo Looks good to me!

##
##
## Generating Artifacts
##

.PHONY: docs
docs: logs ## Generate PDF documentation.
	@rm -r docs/_build || true
	@rm -r docs/_generated || true
	# sphinx-build -M latexpdf -a docs _build | tee logs/docs.log
	$(MAKE) -C docs latexpdf 2>&1 | tee logs/docs.log
	mv docs/_build/latex/*.pdf .
