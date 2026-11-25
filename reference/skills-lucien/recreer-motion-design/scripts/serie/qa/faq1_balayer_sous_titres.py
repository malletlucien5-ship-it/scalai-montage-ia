"""Balayage à 5 i/s : hauteur des capitales du sous-titre à chaque image, comparée à la référence de sa position.
Usage : python3 balayer_sous_titres.py → liste des instants où le sous-titre est sous 92 % (hors 0,12 s d'entrée pop)."""
import json
from pathlib import Path
import numpy as np
from PIL import Image
ICI = Path(__file__).resolve().parent.parent
props = json.loads((ICI / "props.json").read_text()); sc = props["scenes"]; ph = props["phrases"]
ref = json.loads((ICI / "work" / "mesure-sous-titres.json").read_text())["reference_px"]
def position(t):
    s = next((x for x in sc if x["s"] <= t < x["e"]), sc[-1])
    force = next((g["pos"] for g in s.get("legende") or [] if g["s"] <= t < g["e"]), None)
    if s["kind"] == "split" or force == "off": return None, s
    return force or ("bottom" if s["kind"] in ("speaker", "puces", "broll") else "center" if s["kind"] == "fs" else "below"), s
alertes = []; toutes = []
for k, img in enumerate(sorted((ICI / "work" / "balayage").glob("f*.png"))):
    t = k / 5 + 0.1  # fps=5 : image k centrée sur k/5 + 0,1 s
    p = next((x for x in ph if x["s"] <= t < x["e"]), None)
    pos, s = position(t)
    if not p or not pos or t - p["s"] < 0.12: continue
    a = np.asarray(Image.open(img).convert("RGB")).astype(int); H, W, _ = a.shape
    c = {"bottom": 0.83, "center": 0.47, "below": 0.80}[pos]
    band = a[int((c - 0.15) * H):min(H, int((c + 0.15) * H))]
    txt = (band.min(axis=2) >= 235) | ((band[..., 2] > 200) & (band[..., 0] < 90) & (band[..., 1] < 140))
    rows = list(txt.sum(1) > W * 0.01) + [False]
    runs, d = [], None
    for y, v in enumerate(rows):
        if v and d is None: d = y
        elif not v and d is not None:
            if y - d > 4: runs.append(y - d)
            d = None
    if not runs: continue
    h = float(np.median(sorted(runs, reverse=True)[:len(p["lines"])])) * 2  # 960 → 1920 : même échelle que la référence ? non, référence en 2560
    e = h / (ref[pos] * 1920 / 2560 * 0.5 * 2)
    toutes.append(e)
    if e > 1.3: print("haut", round(t, 2), pos, s["kind"], round(e, 2))
    if e < 0.92:
        alertes.append({"t": round(t, 2), "pos": pos, "scene": s["kind"], "echelle": round(e, 2), "texte": " / ".join(" ".join(m["t"] for m in l) for l in p["lines"])})
print(len(alertes), "images sous 92 %")
for x in alertes: print(x)
print("échelles mesurées :", len(toutes), "images, min", round(min(toutes),3), "p5", round(float(np.percentile(toutes,5)),3), "médiane", round(float(np.median(toutes)),3), "max", round(max(toutes),3))
json.dump({"images": len(toutes), "min": round(min(toutes), 3), "p5": round(float(np.percentile(toutes, 5)), 3), "mediane": round(float(np.median(toutes)), 3),
           "max": round(max(toutes), 3), "alertes": alertes}, open(ICI / "work" / "balayage-sous-titres.json", "w"), ensure_ascii=False, indent=1)
