#!/bin/bash
# intermediaire_flux.sh URL_GET SORTIE.mov : intermédiaire 2560x1440 50 i/s H.264 CRF 14 + PCM 48 kHz depuis un rush 4K lu en flux HTTP.
# Le rush n'est jamais écrit sur le disque : 17 Go de 4K plus l'intermédiaire ont rempli les 30 Go du conteneur le 14/11/2026 (plaque claude-cabinets-guide).
# Une seule connexion (passerelle à 6 connexions). Reprise complète en cas de coupure, 3 essais. Rien ne s'ouvre à l'écran.
url="$1"; out="$2"
[ -n "$url" ] && [ -n "$out" ] || { echo "usage : intermediaire_flux.sh URL_GET SORTIE.mov"; exit 2; }
for essai in 1 2 3; do
  nice -n 19 ffmpeg -nostdin -v error -stats -y -reconnect 1 -reconnect_streamed 1 -reconnect_on_network_error 1 -reconnect_delay_max 30 \
    -i "$url" -map 0:v:0 -map 0:a:0 -vf "scale=2560:1440:flags=lanczos" -r 50 -c:v libx264 -preset veryfast -crf 14 -pix_fmt yuv420p \
    -c:a pcm_s16le -ar 48000 "$out.partial.mov" && mv "$out.partial.mov" "$out" && { echo "INTERMEDIAIRE_OK $out"; exit 0; }
  echo "reprise $essai"; rm -f "$out.partial.mov"; sleep 20
done
echo "INTERMEDIAIRE_ECHEC $out"; exit 1
