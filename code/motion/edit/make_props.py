"""Écrit les props de 01b (sous-titres) et 05b (badge) pour la vidéo de Lucien.

Sous-titres : captions_lucien.json (alignement sur ses mots).
Badge : un chapitre par niveau, du début de la carte de niveau (+ sa durée) au niveau suivant,
retiré pendant les plein écran pour rester sur le speaker comme chez Dan.
"""
import json
import subprocess
from pathlib import Path

H = Path(__file__).parent
SRC = Path.home() / "Desktop/montage-2026-09-17/montage-cut.mp4"
FPS = 30
total = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                              str(SRC)], capture_output=True, text=True, check=True).stdout)
n = int(total * FPS)

caps = json.loads((H / "captions_lucien.json").read_text())
(H / "props-01b-sous-titres-lucien.json").write_text(json.dumps({"durationInFrames": n, "occs": caps["occs"]},
                                                                 ensure_ascii=False))

places = json.loads((H / "placements.json").read_text())
chap = json.loads((H / "chapitres.json").read_text())
cards = {p["at"]: p["at"] + p["dur"] / FPS for p in places if p["id"] == "04-podiums-6-niveaux"}
pleins = sorted((p["at"], p["at"] + p["dur"] / FPS) for p in places if p["mode"] == "plein")
out = []
for i, c in enumerate(chap):
    start = cards.get(c["start"], c["start"] + 3.5)
    end = chap[i + 1]["start"] if i + 1 < len(chap) else total - 1
    # découpe la plage autour des plein écran : le badge vit sur le speaker
    t = start
    for a, b in pleins:
        if b <= t or a >= end:
            continue
        if a - t > 1.0:
            out.append({"niveau": c["niveau"], "start": round(t, 2), "end": round(a, 2)})
        t = max(t, b)
    if end - t > 1.0:
        out.append({"niveau": c["niveau"], "start": round(t, 2), "end": round(end, 2)})
(H / "props-05b-badge-chapitres.json").write_text(json.dumps({"durationInFrames": n, "chapitres": out}))
print(len(caps["occs"]), "sous-titres ;", len(out), "plages de badge ;", n, "images")
