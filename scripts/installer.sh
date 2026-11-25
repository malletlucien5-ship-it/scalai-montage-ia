#!/usr/bin/env bash
# Installe les dépendances du montage. N'ouvre rien à l'écran (--no-open accepté et implicite).
set -euo pipefail
cd "$(dirname "$0")/.."

if ! command -v ffmpeg >/dev/null; then
  if command -v brew >/dev/null; then brew install ffmpeg
  elif command -v apt-get >/dev/null; then (sudo apt-get update && sudo apt-get install -y ffmpeg) || (apt-get update && apt-get install -y ffmpeg)
  else echo "Installe ffmpeg à la main."; exit 1; fi
fi

python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install --no-deps deepfilternet==0.5.6 DeepFilterLib==0.5.6 || echo "DeepFilterNet non installé : la voix sera traitée sans ce débruiteur."

(cd code/motion/remotion && npm ci --no-audit --no-fund)

echo "Installation terminée. Active l'environnement avec : . .venv/bin/activate"
