"""Mesure la taille réelle de chaque sous-titre sur un rendu : une image au milieu de chaque phrase, hauteur des capitales.

Usage : python3 mesurer_sous_titres.py <rendu.mp4> → work/mesure-sous-titres.json et liste des phrases sous 92 % de la taille de base.
Hauteur des capitales mesurée sur les lignes de pixels quasi blancs (≥ 235) de la bande du sous-titre ; la référence est la
médiane des phrases de même position (bas, centre, dessous), qui sont à leur taille de base.
"""
import json, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image

ICI = Path(__file__).resolve().parent.parent
f = sys.argv[1]
props = json.loads((ICI / "props.json").read_text())
sc = props["scenes"]
out = ICI / "work" / "mesure-st"; out.mkdir(exist_ok=True)


def position(t):
    s = next((x for x in sc if x["s"] <= t < x["e"]), sc[-1])
    force = next((g["pos"] for g in s.get("legende") or [] if g["s"] <= t < g["e"]), None)
    if s["kind"] == "split" or force == "off":
        return None
    en_bas = s["kind"] in ("speaker", "puces", "broll")
    return force or ("bottom" if en_bas else "center" if s["kind"] == "fs" else "below")


res = []
for i, p in enumerate(props["phrases"]):
    t = (p["s"] + p["e"]) / 2
    pos = position(t)
    if not pos:
        continue
    img = out / f"p{i:03d}.png"
    if not img.exists():
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.3f}", "-i", f, "-frames:v", "1", str(img)], check=True)
    a = np.asarray(Image.open(img).convert("RGB")).astype(int)
    H, W, _ = a.shape
    # bande du sous-titre : centre 0,83 H (bas), 0,47 H (centre), 0,80 H (dessous)
    c = {"bottom": 0.83, "center": 0.47, "below": 0.80}[pos]
    y0, y1 = int((c - 0.15) * H), min(H, int((c + 0.15) * H))
    band = a[y0:y1]
    # pixels de texte : blancs (≥ 235) ou bleu de marque (b > 200, r < 90)
    txt = ((band.min(axis=2) >= 235) | ((band[..., 2] > 200) & (band[..., 0] < 90) & (band[..., 1] < 140)))
    rows = txt.sum(1) > W * 0.01
    # suites de lignes de texte (une par ligne de sous-titre)
    runs, debut = [], None
    for y, v in enumerate(list(rows) + [False]):
        if v and debut is None:
            debut = y
        elif not v and debut is not None:
            if y - debut > 8:
                runs.append(y - debut)
            debut = None
    nlignes = len(p["lines"])
    hcap = float(np.median(sorted(runs, reverse=True)[:nlignes])) if runs else 0.0
    res.append({"i": i, "t": round(t, 2), "pos": pos, "texte": " / ".join(" ".join(m["t"] for m in l) for l in p["lines"]),
                "hauteur_capitales_px": hcap, "lignes_detectees": len(runs)})

ref = {pos: float(np.median([r["hauteur_capitales_px"] for r in res if r["pos"] == pos and r["hauteur_capitales_px"] > 0]))
       for pos in {r["pos"] for r in res}}
for r in res:
    r["echelle"] = round(r["hauteur_capitales_px"] / ref[r["pos"]], 3) if ref[r["pos"]] else None
petits = [r for r in res if r["echelle"] is not None and r["echelle"] < 0.92]
json.dump({"reference_px": ref, "phrases": res, "sous_92_pourcent": petits}, open(ICI / "work" / "mesure-sous-titres.json", "w"), ensure_ascii=False, indent=1)
print("référence (médiane par position) :", ref)
print(len(res), "phrases mesurées ;", len(petits), "sous 92 % :")
for r in petits:
    print(f"  {r['t']:7.2f} {r['pos']:6s} échelle {r['echelle']:.2f}  {r['texte']}")
