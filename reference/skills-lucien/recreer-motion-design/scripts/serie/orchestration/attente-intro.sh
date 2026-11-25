#!/bin/bash
# Sort dès qu'une FAQ (non déjà vue) passe en attente-feu-vert ou livre. Lit etat.json sur atelier. --no-open.
VUS="$HOME/.local/share/martell-faq-v4-20261007/vus.txt"; touch "$VUS"
for i in $(seq 1 240); do
  out=$(ssh -o ConnectTimeout=10 atelier 'for v in 1-temps 2-difference 3-metier 4-risque; do f=$(find /srv/faq-v4/$v -maxdepth 3 -name etat.json -newer /srv/faq-v4/$v/CONSIGNE.txt -not -path "*/in/*" | head -1); [ -n "$f" ] && echo "$v $(python3 -c "import json;print(json.load(open(\"$f\")).get(\"phase\",\"?\"))" 2>/dev/null) $(stat -c %Y $f)"; done')
  while read -r v ph mt; do
    [ -z "$v" ] && continue
    case "$ph" in attente-feu-vert|livre) grep -qx "$v $ph $mt" "$VUS" || { echo "$v $ph $mt" >> "$VUS"; echo "NOUVEAU $v $ph"; echo "$out"; exit 0; } ;; esac
  done <<< "$out"
  sleep 120
done
echo "timeout 8h"; echo "$out"
