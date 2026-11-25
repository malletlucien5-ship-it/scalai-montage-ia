#!/usr/bin/env bash
# Image fixe locale : tools/still.sh COMPOSITION FRAME SORTIE.png [props-json]
set -euo pipefail
cd "$(dirname "$0")/.."
extra=()
[[ $# -ge 4 ]] && extra+=("--props=$4")
LOCAL_PREVIEW=1 npx --no-install remotion still src/index.ts "$1" "$3" --frame="$2" \
  --browser-executable=/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell \
  --log=error "${extra[@]}"
