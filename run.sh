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
    factorio_prototypes_schema \
    --strict

  black \
    factorio_prototypes_schema \
    --skip-magic-trailing-comma \
    --line-length 120

  python -m factorio_prototypes_schema.extract $FACTORIO_LOCATION >factorio_prototypes_schema.pure.json
  python -m factorio_prototypes_schema.patch <factorio_prototypes_schema.pure.json >factorio_prototypes_schema.json
  check-jsonschema --verbose --schemafile factorio_prototypes_schema.json game-definitions/*/script-output/data-raw-dump.json
)
