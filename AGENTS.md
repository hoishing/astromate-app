# Python Rules

## Code Style

- use python 3.12
- all function must be type hinted
- use `pathlib.Path` instead of `os.path` for path operation
- use latest type hints syntax, eg.
  - `list[int]` instead of `List[int]`
  - `dict[str, int]` instead of `Dict[str, int]`
  - `tuple[int, ...]` instead of `Tuple[int, ...]`
  - `A | B` instead of `Union[A, B]`
  - use `typing.Self` instead of forward reference string "ClassName"
- remove unused imports

## Docstrings Styles

- always use single line concise docstring
- DO NOT include params and type hint in docstring

## Virtual Environment And Package Management

- only use `uv` for managing virtual environment and package dependencies
- use `uv init --python 3.12 && uv venv` to inititialize and create virtual environment
- use `uv add` instead of `uv pip install` for installing packages
- activate the environment with `source .venv/bin/activate` before running cli command installed by `uv add`
- you can install and remove any packages if necessary
- only use `uv` for managing virtual environment and package dependencies
- use `uv init --python 3.12 && uv venv` to initialize and create virtual environment
- use `uv add` and `uv remove` to add/remove packages
- DO NOT use `uv pip install` and `uv pip uninstall` to add/remove packages
- activate the environment with `source .venv/bin/activate` before running cli command installed by `uv add`
- you can install and remove any packages if necessary
