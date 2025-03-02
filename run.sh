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
    $extract_options \
    factorio-data-raw-json-schema.full.json

  python -m factorio_data_raw_json_schema extract \
    --strict-numbers \
    factorio-data-raw-json-schema.full-strict.json

  python -m factorio_data_raw_json_schema extract \
    --limit-to Recipe --limit-to Entity --limit-to Item \
    --forbid SoundDefinition --forbid SpriteSource \
    factorio-data-raw-json-schema.recipes-entities-items.json

  for schema in factorio-data-raw-json-schema.*.json
  do
    schema_slug=${schema%.json}
    schema_slug=${schema_slug#factorio-data-raw-json-schema.}
    for data in game-definitions/*/script-output/data-raw-dump.json
    do
      data_slug=${data%/script-output/data-raw-dump.json}
      data_slug=${data_slug#game-definitions/}
      if md5sum --status --check game-definitions/last-check-of-$data_slug-with-$schema_slug.txt 2>/dev/null
      then
        echo "The $data_slug game definition has already been checked with this version of the $schema_slug schema" >&2
      else
        echo "Checking the $data_slug game definition with the $schema_slug schema" >&2
        echo "check-jsonschema --verbose --schemafile $schema $data && md5sum $schema $data >game-definitions/last-check-of-$data_slug-with-$schema_slug.txt"
      fi
    done \
  done \
  | parallel
)
