default: check fmt

check:
	- ruff check --fix

fmt: fmt-py
fmt: fmt-toml\:pyproject.toml
fmt: fmt-toml\:ruff.toml

fmt-py:
	ruff format

fmt-toml\:%:
	toml-sort --in-place --all "$*"
	taplo format "$*"
