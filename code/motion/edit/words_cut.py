"""Horodate chaque mot de Lucien dans la timeline de montage-cut.mp4.

montage.words.json donne les mots dans la timeline de montage.mp4.
Chaque timeline est une suite de portions (frames de sortie + plage source audio).
On passe : temps montage -> temps source audio -> temps montage-cut.
Un mot retiré par les coupes Resolve disparaît.
Sortie : edit/words_cut.json et edit/transcript_cut.txt (une ligne par phrase).
"""
import bisect
import json
from pathlib import Path

D = Path.home() / "Desktop/montage-2026-09-17"
OUT = Path(__file__).parent


def spans(doc):
    fps, t, out = doc["fps"], 0.0, []
    for c in doc["chunks"]:
        d = c["frames"] / fps
        a = c["audio"]
        out.append((t, t + d, a["path"], a["start"], a["end"]))
        t += d
    return out


A = spans(json.loads((D / "montage.sources.json").read_text()))
B = spans(json.loads((D / "montage-cut.sources.json").read_text()))
starts_a = [s[0] for s in A]


def to_source(t):
    i = max(0, bisect.bisect_right(starts_a, t) - 1)
    t0, t1, path, s0, s1 = A[i]
    r = (s1 - s0) / max(t1 - t0, 1e-9)
    return path, s0 + (t - t0) * r


def to_cut(path, s):
    for t0, t1, p, s0, s1 in B:
        if p == path and s0 - 0.02 <= s <= s1 + 0.02:
            r = (t1 - t0) / max(s1 - s0, 1e-9)
            return t0 + (s - s0) * r
    return None


words = json.loads((D / "montage.words.json").read_text())
out = []
for w in words:
    p, s = to_source(w["start"])
    p2, e = to_source(w["end"])
    cs, ce = to_cut(p, s), to_cut(p2, e)
    if cs is None:
        continue
    out.append({"w": w["raw"], "s": round(cs, 3), "e": round(ce if ce is not None else cs + 0.2, 3)})

(OUT / "words_cut.json").write_text(json.dumps(out, ensure_ascii=False, indent=0))
lines, cur = [], []
for w in out:
    cur.append(w)
    if w["w"].endswith((".", "?", "!")) or len(cur) > 28:
        lines.append(f"[{cur[0]['s']:7.2f}] " + " ".join(x["w"] for x in cur))
        cur = []
if cur:
    lines.append(f"[{cur[0]['s']:7.2f}] " + " ".join(x["w"] for x in cur))
(OUT / "transcript_cut.txt").write_text("\n".join(lines) + "\n")
print(len(words), "mots dans montage.mp4 ;", len(out), "gardés dans montage-cut ; dernier à", out[-1]["e"], "s")
