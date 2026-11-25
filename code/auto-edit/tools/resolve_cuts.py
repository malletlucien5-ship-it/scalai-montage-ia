#!/usr/bin/python3
"""Coupes DaVinci Resolve (version App Store, base SQLite) → plan multicam coupé.

  resolve_cuts.py extract PROJET --media montage.mp4 --out kept.json
      Lit Project.db (copie, jamais l'original ouvert par Resolve), garde les
      clips vidéo dont MediaFilePath se termine par --media, imprime les coupes
      et écrit les plages GARDÉES en frames de sortie [[f0,f1],...].
  resolve_cuts.py apply PLAN.json kept.json PLAN_OUT.json
      Intersecte chaque segment source du plan avec les plages gardées (mapping
      frames sortie → temps source via le plan cumulatif x vitesse). Le raccord
      entre parties caméra est lu par ffprobe sur cam_parts.

Prérequis : toutes les versions rendues d'un même plan partagent les mêmes
frames de sortie (même liste de segments), sinon les coupes ne se reportent pas.
"""
import argparse, json, shutil, sqlite3, subprocess, sys, tempfile
from pathlib import Path

LIB = (Path.home() / "Library/Containers/com.blackmagic-design.DaVinciResolveLite/Data/"
       "Library/Application Support/Resolve Project Library/Resolve Projects/Users/guest/Projects")


def probe_dur(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", path], capture_output=True, text=True)
    return float(r.stdout.strip().splitlines()[0])


def probe_fps(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                        "stream=r_frame_rate", "-of", "csv=p=0", path], capture_output=True, text=True)
    n, d = r.stdout.strip().splitlines()[0].split("/"); return int(n) / int(d)


def probe_frames(path):
    r = subprocess.run([
        "ffprobe", "-v", "error", "-count_packets", "-select_streams", "v:0",
        "-show_entries", "stream=nb_read_packets", "-of", "csv=p=0", path,
    ], capture_output=True, text=True)
    value=r.stdout.strip().splitlines()
    return int(value[0]) if r.returncode==0 and value and value[0].isdigit() else None


def extract(a):
    db = LIB / a.project / "Project.db"
    if not db.exists():
        sys.exit(f"projet introuvable : {db}")
    tmp = Path(tempfile.mkdtemp()) / "Project.db"
    shutil.copy(db, tmp)
    con = sqlite3.connect(tmp)
    rows = con.execute("select Start, Duration, cast(coalesce(nullif([In],''),0) as integer), MediaFilePath from Sm2TiItem "
                       "where DbType='Sm2TiVideoClip' order by Start").fetchall()
    rows = [r for r in rows if r[3] and r[3].endswith(a.media)]
    if not rows:
        sys.exit("aucun clip vidéo de ce média dans la timeline")
    fps = a.fps
    raw_kept = [[int(i or 0), int(i or 0) + int(d)] for s, d, i, _ in rows]
    if Path(rows[0][3]).exists():
        total = probe_frames(rows[0][3]) or int(round(probe_dur(rows[0][3]) * fps))
    else:
        total = raw_kept[-1][1]
    kept = [[max(0,x),min(total,y)] for x,y in raw_kept if min(total,y)>max(0,x)]
    removed, prev = [], 0
    for x, y in kept:
        if x > prev:
            removed.append((prev, x))
        prev = y
    if prev < total:
        removed.append((prev, total))
    tc = lambda f: f"{int(f/fps//60)}:{(f/fps)%60:05.2f}"
    print(f"{len(kept)} clips, gardé {sum(y-x for x,y in kept)/fps/60:.2f} min, média {rows[0][3]}")
    for x, y in removed:
        print(f"  coupe {tc(x)} → {tc(y)}  ({(y-x)/fps:.1f}s)")
    Path(a.out).write_text(json.dumps(kept))
    print(f"→ {a.out}")


def apply(a):
    p = json.loads(Path(a.plan).read_text())
    kept = json.loads(Path(a.kept).read_text())
    speed = float(p.get("speed", 1.0))
    fps = probe_fps(p["cam_parts"][0])
    bounds, acc = [], 0.0
    for part in p["cam_parts"][:-1]:
        acc += probe_dur(part); bounds.append(acc)
    segs = [(float(s), float(e), l) for s, e, l in p["segments"]]
    for b in bounds:   # scission au raccord comme au rendu
        out = []
        for s, e, l in segs:
            out += [(s, b, l), (b, e, l)] if s < b < e else [(s, e, l)]
        segs = out
    t2f = lambda t: int(round(t * fps))
    cum_in = cum_out = 0; rows = []
    for s, e, l in segs:
        inp = max(1, t2f(e) - t2f(s)); cum_in += inp
        nxt = max(cum_out + 1, int(round(cum_in / speed)))
        rows.append((s, e, l, cum_out, nxt - cum_out, inp)); cum_out = nxt
    print(f"plan : {len(segs)} segments, {cum_out} frames sortie")
    out = []
    for s, e, l, o0, nf, inp in rows:
        o1 = o0 + nf; eff = inp / nf
        for k0, k1 in kept:
            x, y = max(o0, k0), min(o1, k1)
            if y - x <= 0:
                continue
            sa = s if x == o0 else round((s + (x - o0) * eff / fps) * fps) / fps
            sb = e if y == o1 else round((s + (y - o0) * eff / fps) * fps) / fps
            if sb - sa >= 1.0 / fps:
                out.append([sa, sb, l])
    merged = []
    for s, e, l in out:
        if merged and merged[-1][2] == l and abs(merged[-1][1] - s) < 1e-6:
            merged[-1][1] = e
        else:
            merged.append([s, e, l])
    p["segments"] = merged; p["kept"] = sum(e - s for s, e, _ in merged)
    Path(a.plan_out).write_text(json.dumps(p, ensure_ascii=False, indent=1))
    ci = co = 0
    for s, e, _ in merged:
        ci += max(1, t2f(e) - t2f(s)); co = max(co + 1, int(round(ci / speed)))
    exp = sum(y - x for x, y in kept)
    print(f"après coupes : {len(merged)} segments → {co} frames (attendu {exp}, écart {co-exp})")
    print(f"→ {a.plan_out}")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("extract"); e.add_argument("project"); e.add_argument("--media", required=True)
    e.add_argument("--out", required=True); e.add_argument("--fps", type=float, default=50.0)
    x = sub.add_parser("apply"); x.add_argument("plan"); x.add_argument("kept"); x.add_argument("plan_out")
    a = ap.parse_args()
    (extract if a.cmd == "extract" else apply)(a)


if __name__ == "__main__":
    main()
