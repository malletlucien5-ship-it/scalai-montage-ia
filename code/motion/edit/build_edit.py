"""Construit la liste des placements des motion designs sur montage-cut.mp4.

Entrées :
  anchors.json      alignement script de Dan (ref) -> vidéo de Lucien (cut), par segments et mots clés
  occurrences.json  registre des occurrences de chaque composition (tools/occurrences.mjs)
Sortie :
  placements.json   une ligne par occurrence posée : id, from, dur (images 30 i/s), at (s dans la vidéo), mode
  chapitres.json    début de chaque chapitre dans la vidéo (pour la musique et le badge)
Règles :
  - une occurrence dont le passage a été coupé chez Lucien n'est pas posée ;
  - un mot clé proche (moins de 2 s dans la référence) prime sur l'interpolation par segment ;
  - deux plein écran qui se chevauchent : le premier est raccourci au début du suivant ;
  - 01 et 05 sont remplacés par 01b et 05b (sous-titres et badge calés sur Lucien).
"""
import bisect
import json
from pathlib import Path

H = Path(__file__).parent
anch = json.loads((H / "anchors.json").read_text())
occ = json.loads((H / "occurrences.json").read_text())
FPS = 30
# Retirés : passage coupé chez Lucien (Apex) ou contenu contraire à sa phrase (DM au lieu du lien en description).
RETIRES = {"44-apex-cta", "22-telephone-dm"}
SKIP = {"01-sous-titres-cinetiques", "05-badge-niveau", "01b-sous-titres-lucien", "05b-badge-chapitres"}

segs = sorted(anch["segments"], key=lambda s: s["ref_s"])
kept = [s for s in segs if not s.get("absent")]
keys = sorted((k for k in anch.get("mots_cles", []) if k.get("cut_t") is not None and k.get("ref_t") is not None), key=lambda k: k["ref_t"])
key_t = [k["ref_t"] for k in keys]


def absent_at(t):
    for s in segs:
        if s["ref_s"] - 0.05 <= t <= s["ref_e"] + 0.05:
            return bool(s.get("absent"))
    return False


def map_ref(t):
    """Temps de la référence -> temps dans la vidéo de Lucien, ou None si le passage est coupé."""
    i = bisect.bisect_left(key_t, t)
    near = [keys[j] for j in (i - 1, i) if 0 <= j < len(keys) and abs(keys[j]["ref_t"] - t) < 2.0]
    if near:
        k = min(near, key=lambda k: abs(k["ref_t"] - t))
        return k["cut_t"] + (t - k["ref_t"])
    if absent_at(t):
        return None
    pts = []
    for s in kept:
        pts += [(s["ref_s"], s["cut_s"]), (s["ref_e"], s["cut_e"])]
    pts.sort()
    xs = [p[0] for p in pts]
    j = bisect.bisect_right(xs, t)
    if j == 0:
        return pts[0][1] - (pts[0][0] - t)
    if j >= len(pts):
        return pts[-1][1] + (t - pts[-1][0])
    (x0, y0), (x1, y1) = pts[j - 1], pts[j]
    return y0 if x1 == x0 else y0 + (t - x0) * (y1 - y0) / (x1 - x0)


places, skipped = [], []
for cid, v in occ.items():
    if cid in SKIP or cid in RETIRES or not v.get("occurrences"):
        continue
    for k, o in enumerate(v["occurrences"]):
        at = map_ref(o["ref"][0])
        if at is None:
            skipped.append(f"{cid}#{k} (ref {o['ref'][0]:.1f} s coupé chez Lucien)")
            continue
        places.append({"id": cid, "occ": k, "from": o["from"], "dur": o["durationInFrames"],
                       "at": round(at, 3), "mode": o["mode"], "ref": o["ref"]})

places.sort(key=lambda p: p["at"])
plein = [p for p in places if p["mode"] == "plein"]
for a, b in zip(plein, plein[1:]):
    end = a["at"] + a["dur"] / FPS
    if end > b["at"]:
        a["dur"] = max(1, int((b["at"] - a["at"]) * FPS))
        a["raccourci"] = True

# Chapitres : arrivée de chaque niveau d'après les occurrences 1 à 6 de la carte podiums (04).
chap = [p for p in places if p["id"] == "04-podiums-6-niveaux" and p["occ"] >= 1]
chapitres = [{"niveau": i + 1, "start": p["at"]} for i, p in enumerate(sorted(chap, key=lambda p: p["at"]))]

(H / "placements.json").write_text(json.dumps(places, indent=1, ensure_ascii=False))
(H / "chapitres.json").write_text(json.dumps(chapitres, indent=1))
print(len(places), "placements ;", sum(p.get("raccourci", False) for p in places), "raccourcis ;", len(skipped), "non posés")
for s in skipped:
    print("  non posé :", s)
print("chapitres :", [(c["niveau"], round(c["start"], 1)) for c in chapitres])
