# Usage : python3 controle_fantomes.py MASTER.mp4 DOSSIER_RENDUS_FRAIS SORTIE.json [FPS=50] [SEUIL=5]
# Entrées : master (ou master muet) et images fixes fraîches t<instant>.png rendues à part (node tools/stills-faq3v4.mjs PROPS DOSSIER t1 t2 …).
# Sortie : JSON de l'écart moyen master / rendu frais par instant (image entière et panneau gauche) ; code 1 si un écart dépasse le seuil.
"""Contrôle « aucune_image_fantome » : un rendu enchaîné (onglets qui rendent les images à la suite) peut garder des éléments
d'images précédentes (clés React dupliquées), invisibles sur des images fixes isolées. On compare donc le master à des rendus
frais du même instant. Écart attendu : la compression seule (2 à 3 niveaux sur 255 en 960x540)."""
import glob, json, os, subprocess, sys
import numpy as np
from PIL import Image

MASTER, DOSSIER, OUT = sys.argv[1:4]
FPS = float(sys.argv[4]) if len(sys.argv) > 4 else 50
SEUIL = float(sys.argv[5]) if len(sys.argv) > 5 else 5.0
res = []
for f in sorted(glob.glob(os.path.join(DOSSIER, "t*.png"))):
    t = float(os.path.basename(f)[1:-4]); n = round(t * FPS)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", MASTER, "-vf", f"select=eq(n\\,{n}),scale=960:540", "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         capture_output=True, check=True).stdout
    m = np.frombuffer(raw, np.uint8).reshape(540, 960, 3).astype(float)
    l = np.asarray(Image.open(f).convert("RGB").resize((960, 540))).astype(float)
    res.append({"t": t, "ecart_image": round(float(np.abs(m - l).mean()), 2), "ecart_panneau": round(float(np.abs(m[:, :440] - l[:, :440]).mean()), 2)})
ok = bool(res) and max(r["ecart_image"] for r in res) < SEUIL
json.dump({"ok": ok, "seuil": SEUIL, "images": len(res), "ecart_max": max((r["ecart_image"] for r in res), default=None), "mesures": res}, open(OUT, "w"), ensure_ascii=False, indent=1)
print(("OK" if ok else "ÉCART"), "images", len(res), "écart max", max((r["ecart_image"] for r in res), default=None))
sys.exit(0 if ok else 1)
