.PHONY: check test lint typecheck file-length eval-dev eval-test eval-adversarial eval-generation eval-judge reindex bench gen-api smoke

check: file-length lint typecheck test

file-length:
	python3 scripts/check_file_length.py

lint:
	cd apps/api && uv run ruff check . ../../eval && uv run ruff format --check . ../../eval
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

RETRIEVAL_REPORT ?= eval/reports/m2-dense-dev.json

eval-generation:
	cd apps/api && PYTHONPATH=. uv run --no-sync python ../../eval/generation.py --retrieval-report "$(abspath $(RETRIEVAL_REPORT))"

eval-judge:
	cd apps/api && PYTHONPATH=. uv run --no-sync python ../../eval/judge.py --cases ../../eval/reports/m2-qa40.cases.jsonl --compare ../../eval/reports/m2-qa40.agent.jsonl

bench:
	@echo "bench: Python vs Rust measurements start in M3."

gen-api:
	bash scripts/gen_api_client.sh
