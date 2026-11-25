# Usage : python3 centres_vides.py VIDEO_1080p.mp4 PROPS.json SORTIE.json [PAS_S=0.1]
# Entrées : aperçu 1080p livré (variante B) et props de la composition faq3-v4 (scènes « split »).
# Sortie : JSON des plages où le centre des diapositives reste vide plus de 0,4 s (vide = moins de 0,5 % de pixels hors fond).
"""Panneaux à centre vide sur une vidéo 1080p livrée (variante B).
Usage : python3 centres_vides.py VIDEO_1080p.mp4 PROPS.json SORTIE.json [PAS_S]
Centre = zone du visuel de la diapositive (x 40 à 895, y 330 à 805). Une image est « vide » si moins de 0,5 % des pixels
s'écartent du fond négatoscope (pixels sombres, colorés ou annotations). Signale toute plage vide de plus de 0,4 s dans un écran partagé.
"""
import json, subprocess, sys
import numpy as np

VID, PROPS, OUT = sys.argv[1:4]
PAS = float(sys.argv[4]) if len(sys.argv) > 4 else 0.1
p = json.load(open(PROPS))
W, H = 1920, 1080
X0, X1, Y0, Y1 = 40, 894, 330, 806  # dimensions paires (ffmpeg arrondit le recadrage)
# décodage continu à PAS secondes (fps = 1/PAS), centre seulement, en niveaux de gris
fps = round(1 / PAS)
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", VID, "-vf", f"fps={fps},crop={X1 - X0}:{Y1 - Y0}:{X0}:{Y0},format=rgb24", "-f", "rawvideo", "-"],
                     capture_output=True, check=True).stdout
n = len(raw) // ((X1 - X0) * (Y1 - Y0) * 3)
im = np.frombuffer(raw, np.uint8)[: n * (X1 - X0) * (Y1 - Y0) * 3].reshape(n, Y1 - Y0, X1 - X0, 3).astype(np.int16)
r, g, b = im[..., 0], im[..., 1], im[..., 2]
lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
contenu = ((lum < 170) | (np.abs(r - b) > 40) | (np.abs(g - b) > 45)).mean(axis=(1, 2))
splits = [s for s in p["scenes"] if s["kind"] == "split"]
def dans_split(t):
    return any(s["s"] + 0.05 <= t < s["e"] - 0.05 for s in splits)
vides, cur = [], None
for k in range(n):
    t = (k + 0.5) / fps
    v = dans_split(t) and contenu[k] < 0.005
    if v and cur is None:
        cur = t
    if not v and cur is not None:
        if t - cur > 0.4:
            vides.append([round(cur, 2), round(t, 2)])
        cur = None
json.dump({"pas_s": PAS, "images": n, "plages_vides_plus_de_0_4_s": vides, "contenu_min_split": round(float(min(contenu[k] for k in range(n) if dans_split((k + 0.5) / fps))), 4)},
          open(OUT, "w"), ensure_ascii=False, indent=1)
print("plages vides > 0,4 s :", vides)
