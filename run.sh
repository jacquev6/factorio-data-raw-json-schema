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

  python -m factorio_data_raw_json_schema extract $FACTORIO_LOCATION \
  | python -m factorio_data_raw_json_schema patch \
  >factorio-data-raw-json-schema.json

  check-jsonschema --verbose --schemafile factorio-data-raw-json-schema.json game-definitions/*/script-output/data-raw-dump.json
)
