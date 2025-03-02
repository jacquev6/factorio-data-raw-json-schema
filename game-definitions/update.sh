#!/bin/bash

set -o errexit
set -o nounset
set -o pipefail
cd "$(dirname "${BASH_SOURCE}")/.."


# This is specific to jacquev6's computer
if [ -d ../Games/Factorio/games ]
then
  for d in ../Games/Factorio/games/for-dump-data--*
  do
    slug=${d#../Games/Factorio/games/for-dump-data--}
    echo "Updating $slug"
    rm -rf game-definitions/$slug
    mkdir -p game-definitions/$slug/{script-output,mods}
    cp $d/mods/mod-list.json game-definitions/$slug/mods
    cp $d/script-output/data-raw-dump.json game-definitions/$slug/script-output
  done
fi
