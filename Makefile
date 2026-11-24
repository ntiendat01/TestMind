.PHONY: check test lint typecheck file-length eval-dev eval-test eval-adversarial reindex bench gen-api smoke

check: file-length lint typecheck test

file-length:
	python3 scripts/check_file_length.py

lint:
	cd apps/api && uv run ruff check . ../../eval/cli.py && uv run ruff format --check . ../../eval/cli.py
	cd apps/web && pnpm exec eslint .

typecheck:
	cd apps/api && uv run mypy app
	cd apps/web && pnpm exec tsc --noEmit

test:
	cd apps/api && uv run pytest
	cd apps/api && uv run pytest --override-ini="testpaths=" ../../scripts/test_check_file_length.py
	cd apps/web && pnpm test

CONFIG ?= config/exp/baseline.yaml

smoke:
	cd apps/api && PYTHONPATH=. uv run python ../../eval/cli.py smoke --config "$(CONFIG)"

eval-dev eval-test eval-adversarial:
	cd apps/api && PYTHONPATH=. uv run --no-sync python ../../eval/cli.py $(@:eval-%=%) --config "$(CONFIG)"

reindex:
	python3 scripts/reindex.py

bench:
	@echo "bench: Python vs Rust measurements start in M3."

gen-api:
	bash scripts/gen_api_client.sh
