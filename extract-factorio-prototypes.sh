#!/bin/bash

set -o errexit
set -o nounset
set -o pipefail


# Generate a JSON schema for the Factorio prototypes
if ! diff .venv/requirements.txt factorio_prototypes_schema/requirements.txt 2>/dev/null >/dev/null
then
  rm -rf .venv
  python3 -m venv .venv
  (
    . .venv/bin/activate
    pip install -r factorio_prototypes_schema/requirements.txt
  )
  cp factorio_prototypes_schema/requirements.txt .venv/requirements.txt
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

  python -m factorio_prototypes_schema $FACTORIO_LOCATION >src/factorio_prototypes_schema.tmp.json
)
npx prettier --write src/factorio_prototypes_schema.tmp.json
mv src/factorio_prototypes_schema.tmp.json src/factorio_prototypes_schema.json
(
  . .venv/bin/activate

  check-jsonschema --verbose --schemafile src/factorio_prototypes_schema.json game-definitions/*/script-output/data-raw-dump.json
)


# Generate Typescript types from the JSON schema
# https://www.npmjs.com/package/json-schema-to-typescript
npx json2ts --no-format --unreachableDefinitions --no-additionalProperties src/factorio_prototypes_schema.json src/factorio_prototypes_schema.tmp.ts
npx prettier --write src/factorio_prototypes_schema.tmp.ts
mv src/factorio_prototypes_schema.tmp.ts src/factorio_prototypes_schema.ts
