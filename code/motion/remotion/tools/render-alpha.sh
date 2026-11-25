#!/bin/bash
# Usage : tools/render-alpha.sh <id>
# Rend out/alpha/<id>.mov en ProRes 4444 avec canal alpha, sans speaker.
# La composition doit accepter la prop showPlate et laisser un fond transparent quand elle vaut false.
set -e
cd "$(dirname "$0")/.."
mkdir -p out/alpha
npx remotion render src/index.ts "$1" "out/alpha/$1.mov" --codec=prores --prores-profile=4444 \
  --pixel-format=yuva444p10le --image-format=png --props='{"showPlate":false}' --log=error
echo "ok: out/alpha/$1.mov"
