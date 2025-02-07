#!/bin/bash

set -o errexit
set -o nounset
set -o pipefail


# Generate a JSON schema for the Factorio prototypes
if ! diff .venv/requirements.txt factorio_prototypes_schema/requirements.txt 2>/dev/null >/dev/null
then
  python3 -m venv .venv
  (
    . .venv/bin/activate
    pip install -r factorio_prototypes_schema/requirements.txt
  )
  cp factorio_prototypes_schema/requirements.txt .venv/requirements.txt
fi

(
  . .venv/bin/activate
  python -m factorio_prototypes_schema >src/factorio_prototypes_schema.tmp.json
)


# Generate Typescript types from the JSON schema
# https://www.npmjs.com/package/json-schema-to-typescript
npx json2ts --no-format --no-additionalProperties src/factorio_prototypes_schema.tmp.json src/factorio_prototypes_schema.tmp.ts


# Format generated files
npx prettier --write src/factorio_prototypes_schema.tmp.json src/factorio_prototypes_schema.tmp.ts

# Finalize
mv src/factorio_prototypes_schema.tmp.json src/factorio_prototypes_schema.json
mv src/factorio_prototypes_schema.tmp.ts src/factorio_prototypes_schema.ts
