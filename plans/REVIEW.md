## Standards findings — checkpoint after prd-05

- `pyproject.toml` uses Ruff `select` instead of the required `extend-select = ["S"]`, which replaces Ruff's default rules and omits the security rules.
- The new-project baseline also requires `ty`, `pytest-cov`, and `pip-audit`; `[tool.coverage.run] branch = true`; and the `tests/**` `S101` ignore. These settings are missing. `exclude-newer = "7 days"` is present.
