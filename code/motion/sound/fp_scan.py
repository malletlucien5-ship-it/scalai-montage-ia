"""Retrouve dans la référence chaque bruitage Epidemic utilisé, par empreinte.

1. Élargit le pool de candidats (recherche publique Epidemic, aperçus MP3).
2. Indexe une seule fois les empreintes de toute la piste sans voix de la référence.
3. Pour chaque candidat, vote par décalage temporel. Un candidat utilisé donne un pic net
   de votes à l'instant où il est posé. Chaque pic retenu est une utilisation.
Sortie : sfx_used.json (son, instant, votes, page Epidemic) et sfx_used.md.
Usage : python fp_scan.py [--pages 3] [--min-votes 12]
"""
import argparse
import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import librosa
import numpy as np

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from match_epidemic import CAND, UA, search  # noqa: E402

src = (HERE / "fingerprint_match.py").read_text().split("cands = {}")[0]
exec(src)  # landmarks(), index(), SR, HOP

TERMS = [
    "low short", "whoosh low short", "swooshes whoosh low", "low long", "whoosh low long", "low medium",
    "mouse click mac", "trackpad click", "keyboard typing mac", "laptop typing", "ui pop soft", "soft pop",
    "bubble", "blip ui", "select", "hover", "toggle switch", "send message", "whoosh fast short", "whoosh short",
    "designed boom low hit", "boom low", "kick hit", "sub hit", "low hit", "thump", "tom hit", "soft hit",
    "text appear", "typewriter", "digital", "data", "computer", "beep", "scroll", "page turn", "paper",
    "phone vibrate", "phone tap", "iphone", "keyboard iphone", "subscribe", "like button",

    "whoosh", "swoosh", "swish", "low long", "low short", "whoosh low", "sub whoosh", "air whoosh",
    "boom", "sub boom", "impact", "cinematic hit", "hit", "braam", "bass dive", "sub drop", "drop",
    "riser", "reverse", "shimmer", "sparkle", "glitch", "transition", "stinger",
    "pop", "bubble pop", "click", "ui click", "mouse click", "button", "tap", "tick", "ding", "notification",
    "user interface", "interface beep", "swipe", "slide", "typing", "keyboard", "type writer", "camera shutter",
    "cash register", "success", "error", "message send", "message received", "chime", "bell", "blip",
]


def fetch_pool(pages):
    pool = {}
    for term in TERMS:
        for p in range(1, pages + 1):
            try:
                for c in search(term, p):
                    pool.setdefault(str(c["id"]), c)
            except Exception as e:
                print("recherche en échec", term, p, e)
            time.sleep(0.3)
    import urllib.request
    for cid, c in pool.items():
        f = CAND / f"{cid}.mp3"
        if not f.exists():
            try:
                f.write_bytes(urllib.request.urlopen(urllib.request.Request(c["mp3"], headers=UA), timeout=30).read())
                time.sleep(0.1)
            except Exception:
                pass
    return pool


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", type=int, default=3)
    ap.add_argument("--min-votes", type=int, default=12)
    a = ap.parse_args()

    pool = fetch_pool(a.pages)
    meta_f = HERE / "candidats_meta.json"
    meta = json.loads(meta_f.read_text()) if meta_f.exists() else {}
    meta.update({k: {"title": v["title"], "slug": v["slug"], "ms": v["ms"]} for k, v in pool.items()})
    meta_f.write_text(json.dumps(meta, ensure_ascii=False))
    print(len(meta), "candidats connus")

    ref, _ = librosa.load(HERE / "stems/htdemucs/ref/no_vocals.wav", sr=SR, mono=True)
    ridx = index(landmarks(ref))
    fps = SR / HOP

    used = []
    files = sorted(CAND.glob("*.mp3"))
    for i, f in enumerate(files):
        try:
            y, _ = librosa.load(f, sr=SR, mono=True, duration=10)
        except Exception:
            continue
        votes = Counter()
        for h, tc in landmarks(y):
            for tr in ridx.get(h, ()):
                votes[(tr - tc) // 4] += 1  # tolérance de 4 trames (~46 ms)
        if not votes:
            continue
        med = np.median(list(votes.values()))
        for off, v in votes.most_common(12):
            if v >= a.min_votes and v >= 4 * max(med, 1):
                m = meta.get(f.stem, {})
                used.append({"t": round(off * 4 / fps, 2), "votes": v, "id": f.stem,
                             "titre": m.get("title", "?"),
                             "page": f"https://www.epidemicsound.com/sound-effects/tracks/{m.get('slug')}/"})
        if i % 300 == 0:
            print(i, "/", len(files))

    # un instant ne garde que le candidat le plus voté
    used.sort(key=lambda u: (u["t"], -u["votes"]))
    kept = []
    for u in used:
        if kept and abs(kept[-1]["t"] - u["t"]) < 0.3:
            if u["votes"] > kept[-1]["votes"]:
                kept[-1] = u
            continue
        kept.append(u)
    (HERE / "sfx_used.json").write_text(json.dumps(kept, indent=1, ensure_ascii=False))
    by = defaultdict(list)
    for u in kept:
        by[(u["id"], u["titre"], u["page"])].append(u["t"])
    lines = ["| Son Epidemic | Utilisations | Instants (s) |", "|---|---|---|"]
    for (cid, titre, page), ts in sorted(by.items(), key=lambda x: -len(x[1])):
        lines.append(f"| [{titre}]({page}) | {len(ts)} | {', '.join(str(t) for t in ts)} |")
    (HERE / "sfx_used.md").write_text("\n".join(lines) + "\n")
    print(len(kept), "utilisations,", len(by), "sons distincts")


if __name__ == "__main__":
    main()
