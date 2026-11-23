#!/usr/bin/env bash
# Generate the web API types from the FastAPI OpenAPI schema.
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
schema="$(mktemp)"
out="$root/apps/web/lib/api/schema.ts"
trap 'rm -f "$schema"' EXIT

(
  cd "$root/apps/api"
  uv run python -c 'import json; from app.main import app; print(json.dumps(app.openapi()))'
) > "$schema"

(
  cd "$root/apps/web"
  pnpm exec openapi-typescript "$schema" --output "$out"
)

tmp="$(mktemp)"
{
  printf '%s\n' '/* AUTO-GENERATED. Do not edit. */'
  cat "$out"
} > "$tmp"
mv "$tmp" "$out"
echo "wrote $out"
