# Commands

## Build/Lint/Test
- `uv run ruff check . --config pyproject.toml` - lint code
- `uv run ruff format . --config pyproject.toml` - format code
- `uv run pytest` - run all tests
- `uv run pytest tests/test_birth.py::test_default_name -v` - run single test
- `uv run streamlit run main.py` - run the app locally

## Code Style

### Python Version & Types
- use python 3.12
- all functions must be type hinted
- use latest type hints syntax: `list[int]`, `dict[str, int]`, `A | B`, `typing.Self`
- use `pathlib.Path` instead of `os.path` for path operations

### Imports & Formatting
- remove unused imports
- use ruff for linting (line-length=100, no-sections for isort)
- imports: standard library, third-party, local (separated by blank lines)

### Naming Conventions
- functions: snake_case
- variables: snake_case
- constants: UPPER_CASE
- classes: PascalCase

### Docstrings & Documentation
- single line concise docstrings
- DO NOT include params and type hints in docstring

### Error Handling
- use specific exceptions over generic Exception
- prefer early returns over nested if statements
- validate inputs at function boundaries

## Virtual Environment & Package Management

- only use `uv` for managing virtual environment and package dependencies
- `uv init --python 3.12 && uv venv` - initialize and create virtual environment
- `uv add` / `uv remove` - add/remove packages (not `uv pip install`)
- activate with `source .venv/bin/activate` before running CLI tools
