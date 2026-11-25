#!/usr/bin/env bash
# Vérifie le poste de montage sans rien ouvrir ni afficher de secret.
cd "$(dirname "$0")/.." || exit 1
ok=0; ko=0
PY=python3; [ -x .venv/bin/python3 ] && PY=.venv/bin/python3
check() { if eval "$2" >/dev/null 2>&1; then echo "OK    $1"; ok=$((ok+1)); else echo "MANQUE $1 : $3"; ko=$((ko+1)); fi; }

check "ffmpeg"        "command -v ffmpeg"  "brew install ffmpeg (Mac) ou apt-get install ffmpeg"
check "ffprobe"       "command -v ffprobe" "livré avec ffmpeg"
check "python3"       "python3 -c 'import sys; assert sys.version_info>=(3,9)'" "Python 3.9 ou plus"
check "node 18+"      "node -e 'process.exit(+process.versions.node.split(\".\")[0]<18)'" "https://nodejs.org"
check "numpy/scipy"   "$PY -c 'import numpy, scipy, soundfile'" "bash scripts/installer.sh"
check "opencv"        "$PY -c 'import cv2'" "bash scripts/installer.sh"
check "remotion"      "test -d code/motion/remotion/node_modules" "cd code/motion/remotion && npm ci"
check "claude"        "command -v claude" "npm install -g @anthropic-ai/claude-code"

if [ -f .env ]; then set -a; . ./.env; set +a; fi
echo
for k in ELEVENLABS_API_KEY FAL_KEY OPENROUTER_API_KEY EPIDEMIC_API_KEY; do
  if [ -n "${!k}" ]; then echo "CLÉ   $k présente"; else echo "CLÉ   $k absente"; fi
done
if [ -n "$ANTHROPIC_API_KEY" ]; then echo "ALERTE ANTHROPIC_API_KEY est définie : retire-la, Claude doit tourner sur ton abonnement Max."; ko=$((ko+1)); fi
echo
echo "$ok contrôles OK, $ko à corriger."
[ "$ko" -eq 0 ]
