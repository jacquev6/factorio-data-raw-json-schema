#!/bin/bash

set -o errexit
set -o nounset
set -o pipefail


if ! diff .venv/requirements.txt requirements.txt 2>/dev/null >/dev/null
then
  rm -rf .venv
  python3 -m venv .venv
  (
    . .venv/bin/activate
    pip install -r requirements.txt
  )
  cp requirements.txt .venv/requirements.txt
fi

(
  . .venv/bin/activate

  mypy \
    factorio_data_raw_json_schema \
    --strict

  black \
    factorio_data_raw_json_schema \
    --skip-magic-trailing-comma \
    --line-length 120

  python -m factorio_data_raw_json_schema extract \
    --doc-root https://lua-api.factorio.com/2.0.28/ \
    factorio-data-raw-json-schema.json

  if ! git diff --stat --exit-code factorio-data-raw-json-schema.json
  then
    check-jsonschema --verbose --schemafile factorio-data-raw-json-schema.json game-definitions/*/script-output/data-raw-dump.json
  fi
)
