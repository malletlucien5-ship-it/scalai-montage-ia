#!/bin/bash
# Rendu lourd FAQ v4 : machine libre parmi atelier (local) et martell-atelier-v4-rendu (distant).
# Usage : /srv/faq-v4/rendre.sh <commande...>   (lancé depuis un dossier sous /srv/faq-v4/<video>/)
# Tout ce que la commande lit ou écrit doit être sous /srv/faq-v4/<video>/. Variables : en ligne (env A=b cmd).
set -uo pipefail
R=<serveur-de-lucien>
CWD=$(pwd); V=$(echo "$CWD" | cut -d/ -f1-4)
case "$V" in /srv/faq-v4/*-*) ;; *) echo "lancer depuis /srv/faq-v4/<video>/..." >&2; exit 2;; esac
CMD=$(printf "%q " "$@")
distant() {
  echo "[rendre] machine distante (CCX33) pour $V" >&2
  rsync -aH --delete --exclude ".git" --exclude manifeste.json --exclude "*.log" "$V/" "$R:$V/" || return 90
  ssh -o ServerAliveInterval=30 "$R" "cd $(printf %q "$CWD") && $CMD"; rc=$?
  rsync -aH --update --exclude node_modules --exclude ".git" --exclude manifeste.json "$R:$V/" "$V/"
  return $rc
}
local_() { echo "[rendre] machine locale (CPX62) pour $V" >&2; bash -c "$CMD"; }
while true; do
  exec 8>/srv/faq-v4/render.lock
  if flock -n 8; then local_; rc=$?; flock -u 8; exit $rc; fi
  if [ -f /srv/faq-v4/rendu2.pret ]; then
    exec 9>/srv/faq-v4/render2.lock
    if flock -n 9; then distant; rc=$?; flock -u 9; exit $rc; fi
  fi
  sleep 20
done
