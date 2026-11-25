"""Assemble la vidéo finale : montage-cut.mp4 + motion designs + bruitages + musique.

Lit placements.json et chapitres.json (build_edit.py). Écrit la commande ffmpeg dans compose.sh.
Ne lance rien sans --run (rendu lourd : encodeur matériel h264_videotoolbox, 2560x1440 à 50 i/s).

Couches :
  vidéo  : montage-cut.mp4, puis chaque occurrence posée à son instant (plein écran ou transparente),
           puis les sous-titres et le badge calés sur Lucien (01b, 05b, webm transparents).
  son    : voix de montage-cut.mp4, bruitages de chaque occurrence, musique par chapitre à -23 dB.
Sortie : ~/Desktop/montage-2026-09-17/montage-motion.mp4
"""
import argparse
import json
import shlex
import subprocess
from pathlib import Path

H = Path(__file__).parent
R = H.parent / "remotion/out"
SRC = Path.home() / "Desktop/montage-2026-09-17/montage-cut.mp4"
OUT = Path.home() / "Desktop/montage-2026-09-17/montage-motion.mp4"
MUS = H / "musique"
W, HGT, FPS_OUT = 2560, 1440, 50
MUSIC_GAIN = 0.07  # environ -23 dB : la musique reste 21 à 27 LU sous la voix, comme chez Dan
FADE = 1.5

MUSIQUE = [  # (niveau de départ, fichier, décalage dans le morceau)
    (0, "00-intro-Unseen-Elin-Piel.mp3", 0),
    (1, "01-amateur-Apparent-Solution-Brendon-Moeller.mp3", 0),
    (2, "02-habitue-Steall-Waters-Luba-Hilman.mp3", 0),
    (3, "03-integrateur-The-Shape-of-Memory-Luba-Hilman.mp3", 0),
    (4, "04-operateur-Shadowed-John-B-Lund.mp3", 0),
    (5, "05-batisseur-Fallout-Lennon-Hutton.mp3", 0),
    (6, "06-orchestrateur-The-Farmhouse-Silver-Maple.mp3", 0),
]
OUTRO = ("07-outro-Pink-Pulsar-ELFL.mp3", 44.0, 35.0)  # fichier, décalage, durée finale


def duration(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                       capture_output=True, text=True, check=True)
    return float(r.stdout.strip())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()

    places = json.loads((H / "placements.json").read_text())
    chap = json.loads((H / "chapitres.json").read_text())
    total = duration(SRC)

    args = ["ffmpeg", "-y", "-hide_banner", "-i", str(SRC)]
    vf, af, amix = [], [], ["[0:a]"]
    base = "[0:v]"
    n = 1

    def add_clip(path, start, dur, at, alpha, tag):
        nonlocal n, base
        args.extend(["-ss", f"{start:.3f}", "-t", f"{dur:.3f}"])
        if alpha and str(path).endswith(".webm"):
            args.extend(["-c:v", "libvpx-vp9"])
        args.extend(["-i", str(path)])
        fmt = "yuva420p" if alpha else "yuv420p"
        vf.append(f"[{n}:v]fps={FPS_OUT},scale={W}:{HGT},format={fmt},setpts=PTS-STARTPTS+{at:.3f}/TB[v{n}]")
        vf.append(f"{base}[v{n}]overlay=eof_action=pass:format=auto[b{n}]")
        base = f"[b{n}]"
        ms = int(at * 1000)
        af.append(f"[{n}:a]asetpts=PTS-STARTPTS,aresample=48000,adelay={ms}|{ms}[a{n}]")
        amix.append(f"[a{n}]")
        n += 1

    for p in places:
        path = R / (f"alpha/{p['id']}.mov" if p["mode"] == "overlay" else f"{p['id']}.mp4")
        add_clip(path, p["from"] / 30, p["dur"] / 30, p["at"], p["mode"] == "overlay", p["id"])

    for special in ("01b-sous-titres-lucien", "05b-badge-chapitres"):
        add_clip(R / f"alpha/{special}.webm", 0, total, 0, True, special)

    # musique : un morceau par chapitre, du début du chapitre au suivant, fondu de sortie
    starts = {0: 0.0, **{c["niveau"]: c["start"] for c in chap}}
    outro_at = total - OUTRO[2]
    bounds = sorted(starts.items())
    for idx, (lvl, t0) in enumerate(bounds):
        t1 = bounds[idx + 1][1] if idx + 1 < len(bounds) else outro_at
        f, off = next(((m[1], m[2]) for m in MUSIQUE if m[0] == lvl), (None, 0))
        if not f or t1 <= t0:
            continue
        d = t1 - t0
        args.extend(["-ss", f"{off:.3f}", "-t", f"{d:.3f}", "-i", str(MUS / f)])
        ms = int(t0 * 1000)
        af.append(f"[{n}:a]aresample=48000,volume={MUSIC_GAIN},afade=t=in:d=0.3,"
                  f"afade=t=out:st={max(0, d - FADE):.3f}:d={FADE},adelay={ms}|{ms}[m{n}]")
        amix.append(f"[m{n}]")
        n += 1
    args.extend(["-ss", f"{OUTRO[1]:.3f}", "-t", f"{OUTRO[2]:.3f}", "-i", str(MUS / OUTRO[0])])
    ms = int(outro_at * 1000)
    af.append(f"[{n}:a]aresample=48000,volume={MUSIC_GAIN},afade=t=in:d=1,afade=t=out:st={OUTRO[2] - 3}:d=3,"
              f"adelay={ms}|{ms}[m{n}]")
    amix.append(f"[m{n}]")

    af.append("".join(amix) + f"amix=inputs={len(amix)}:normalize=0:duration=first,alimiter=limit=0.95[aout]")
    graph = ";\n".join(vf + af)
    (H / "compose.filter").write_text(graph)
    args.extend(["-filter_complex_script", str(H / "compose.filter"), "-map", base, "-map", "[aout]",
                 "-c:v", "h264_videotoolbox", "-b:v", "35M", "-profile:v", "high", "-pix_fmt", "yuv420p",
                 "-c:a", "aac", "-b:a", "320k", "-movflags", "+faststart", str(OUT)])
    (H / "compose.sh").write_text("#!/bin/bash\n" + " ".join(shlex.quote(x) for x in args) + "\n")
    print(f"{len(places)} occurrences + sous-titres + badge + {len([x for x in amix if x.startswith('[m')])} pistes musique")
    print("commande écrite dans", H / "compose.sh")
    if a.run:
        subprocess.run(args, check=True)


if __name__ == "__main__":
    main()
