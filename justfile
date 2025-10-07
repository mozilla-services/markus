# Relative to docs/ directory
sphinxbuild := "../.venv/bin/sphinx-build"

@_default:
    just --list

# Build a development environment
devenv:
    uv sync --extra dev --extra datadog --extra statsd --refresh --upgrade

# Run tests and linting
test *args: devenv
    uv run tox {{args}}

# Format files
format: devenv
    uv run tox exec -e py310-lint -- ruff format

# Lint files
lint: devenv
    uv run tox -e py310-lint

# Build docs
docs: devenv
    SPHINXBUILD={{sphinxbuild}} make -e -C docs/ clean
    SPHINXBUILD={{sphinxbuild}} make -e -C docs/ doctest
    SPHINXBUILD={{sphinxbuild}} make -e -C docs/ html

# Wipe dev environment and build artifacts
clean:
    rm -rf .venv uv.lock
    rm -rf build dist src/markus.egg-info .tox
    rm -rf docs/_build/*
    find src/markus/ tests/ -name __pycache__ | xargs rm -rf
    find src/markus/ tests/ -name '*.pyc' | xargs rm -rf

# Build files for relase
build: devenv
    rm -rf build/ dist/
    uv run python -m build
    uv run twine check dist/*
