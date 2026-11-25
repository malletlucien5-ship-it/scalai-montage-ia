#!/usr/bin/python3
"""Contrôle d'un plan multicam (JSON de --preview-out) avant rendu.

  analyze_plan.py PLAN.json [--min-shot 4] [--max-run 10]

Imprime : runs (nombre, moyenne, hors bornes), plans écran qui chevauchent une
plage interdite (doit être vide), portions libres > max_run dans les runs qui
contiennent un verrou, plans face posés sur une plage visuelle (hors verrou),
durée conservée et durée de sortie estimée.
"""
import argparse, json
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("plan"); ap.add_argument("--min-shot", type=float, default=4.0)
    ap.add_argument("--max-run", type=float, default=10.0)
    a = ap.parse_args()
    p = json.loads(Path(a.plan).read_text())
    segs = [(float(s), float(e), l) for s, e, l in p["segments"]]
    speed = float(p.get("speed", 1.0))
    sync = p.get("sync", {})
    anchors = sync.get("anchors") or []
    off = anchors[0][1] if anchors and len(anchors[0]) > 1 else 0.0  # approx cam→écran

    forb = p.get("face_ranges") or []
    vis = p.get("split_ranges") or []

    def ov(s, e, rs):
        return sum(max(0.0, min(e + off, b) - max(s + off, a)) for a, b in rs)

    runs = []
    for i, (s, e, l) in enumerate(segs):
        if runs and runs[-1]["l"] == l:
            runs[-1]["d"] += e - s; runs[-1]["idx"].append(i)
        else:
            runs.append({"l": l, "d": e - s, "s": s, "idx": [i]})
    d = [r["d"] for r in runs]
    print(f"runs : {len(runs)}, moyenne {sum(d)/len(d):.1f}s, > {a.max_run:.0f}s : "
          f"{sum(1 for x in d if x > a.max_run)}, < {a.min_shot:.0f}s : {sum(1 for x in d if x < a.min_shot)}")
    bad = [(round(s), round(e - s, 1)) for s, e, l in segs if l == "split" and ov(s, e, forb) > 0]
    print("ÉCRAN sur plage interdite (doit être vide) :", bad)
    worst = []
    for r in runs:
        acc = mx = 0.0
        for i in r["idx"]:
            s, e, l = segs[i]
            if (l == "face" and ov(s, e, forb) > 0) or (l == "split" and ov(s, e, vis) > 0):
                acc = 0.0
            else:
                acc += e - s; mx = max(mx, acc)
        if mx > a.max_run + 0.5:
            worst.append((r["l"], round(r["s"]), round(mx, 1)))
    print(f"portions libres > {a.max_run:.0f}s :", worst)
    miss = [(round(s), round(e - s, 1)) for s, e, l in segs
            if l == "face" and ov(s, e, vis) >= min(1.0, 0.5 * (e - s)) and ov(s, e, forb) == 0]
    print("FACE sur plage visuelle (hors verrou) :", miss)
    kept = sum(e - s for s, e, _ in segs)
    print(f"gardé {kept:.1f}s → sortie ≈ {kept/speed/60:.1f} min | écran "
          f"{sum(1 for *_, l in segs if l == 'split')} / face {sum(1 for *_, l in segs if l == 'face')}")


if __name__ == "__main__":
    main()
