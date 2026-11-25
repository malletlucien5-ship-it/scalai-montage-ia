#!/bin/bash
# Usage : tools/render.sh <id> [ref_start_s ref_duree_s]
# Rend out/<id>.mp4. Avec un segment de référence, produit aussi
# out/compare/<id>.mp4 (référence à gauche, recréation à droite)
# et out/compare/<id>.jpg (planche de 8 paires d'images). N'ouvre rien.
set -e
cd "$(dirname "$0")/.."
ID="$1"; S="$2"; D="$3"
npx remotion render src/index.ts "$ID" "out/$ID.mp4" --log=error
if [ -n "$S" ]; then
  mkdir -p out/compare
  REF=../ref/ref.mp4
  ffmpeg -hide_banner -loglevel error -y -ss "$S" -t "$D" -i "$REF" -i "out/$ID.mp4" \
    -filter_complex "[0:v]scale=960:540,setpts=PTS-STARTPTS,fps=30[a];[1:v]scale=960:540,fps=30[b];[a][b]hstack=shortest=0[v]" \
    -map "[v]" -an -c:v libx264 -crf 20 "out/compare/$ID.mp4"
  DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "out/compare/$ID.mp4")
  ffmpeg -hide_banner -loglevel error -y -i "out/compare/$ID.mp4" \
    -vf "fps=8/$DUR,scale=960:270,tile=2x4" -frames:v 1 "out/compare/$ID.jpg"
  echo "compare: out/compare/$ID.mp4 out/compare/$ID.jpg"
fi
echo "ok: out/$ID.mp4"
