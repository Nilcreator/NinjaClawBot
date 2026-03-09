# Suggested Commands
- `python -m compileall .`
- `ruff check .`
- `ruff format --check .`
- `pytest -q`
- `mypy .` (only when typing is already part of the project)
- Use `rg` / `rg --files` for fast search.
- Some subprojects in `NinjaRobotV5_bak/` use `uv run ruff check ...` and `uv run pytest ...` based workflows.