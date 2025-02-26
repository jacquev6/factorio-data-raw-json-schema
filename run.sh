#!/bin/bash

set -o errexit
set -o nounset
set -o pipefail


runner=""
extract_options=""
while [ $# -gt 0 ]
do
  case "$1" in
    --py-spy)
      runner="py-spy record -o py-spy.svg --subprocesses --"
      extract_options="--workers 1"
      shift
      ;;
    *)
      break
      ;;
  esac
done


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

  $runner python -m factorio_data_raw_json_schema extract \
    --doc-root https://lua-api.factorio.com/2.0.28/ \
    $extract_options \
    factorio-data-raw-json-schema.full.json

  python -m factorio_data_raw_json_schema extract \
    --doc-root https://lua-api.factorio.com/2.0.28/ \
    --limit-to Recipe --limit-to Entity --limit-to Item \
    --forbid SoundDefinition --forbid SpriteSource \
    factorio-data-raw-json-schema.recipes-entities-items.json

  for schema in factorio-data-raw-json-schema.*.json
  do
    if ! git diff --stat --exit-code $schema 1>&2
    then
      for data in game-definitions/*/script-output/data-raw-dump.json
      do
        echo check-jsonschema --verbose --schemafile $schema $data
      done \
    fi
  done \
  | parallel
)
