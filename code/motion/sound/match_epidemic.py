"""Cherche dans la banque Epidemic Sound les bruitages de la référence.

1. Interroge la recherche publique Epidemic (aperçus MP3 basse qualité) avec des mots-clés.
2. Calcule le spectrogramme mel de chaque candidat.
3. Compare chaque étalon (etalons/*.wav) à chaque candidat : corrélation maximale
   du spectrogramme mel, candidat glissé sur l'étalon. Un même fichier donne un score
   proche de 1 malgré les restes de musique ; un son voisin reste plus bas.
Sortie : matches.json (top 8 par étalon) et candidats/ (aperçus téléchargés).
Usage : python match_epidemic.py [--pages 2]
"""
import argparse
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

import librosa
import numpy as np

HERE = Path(__file__).parent
CAND = HERE / "candidats"
CAND.mkdir(exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (Macintosh) sound-match"}
SR = 22050
HOP = 256

TERMS = [
    "sub whoosh", "low whoosh", "bass swell", "soft impact", "whoosh transition", "swoosh",
    "cinematic boom", "sub drop", "deep impact", "braam", "bass dive",
    "riser", "whoosh riser", "shimmer", "reverse", "cinematic transition",
    "ui click", "mouse click", "button click", "interface", "keyboard typing", "typing",
    "drone low", "atmosphere swell", "ui pop", "notification", "pop", "thud",
]


def search(term, page):
    url = ("https://www.epidemicsound.com/json/search/sfx/?"
           + urllib.parse.urlencode({"term": term, "page": page}))
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
        d = json.load(r)
    out = []
    for t in d["entities"]["tracks"].values():
        u = t.get("stems", {}).get("full", {}).get("lqMp3Url")
        if u and t.get("durationMs", 0) <= 15000:
            out.append({"id": t["id"], "title": t["title"], "slug": t.get("publicSlug"),
                        "ms": t["durationMs"], "mp3": u})
    return out


def logmel(y):
    m = librosa.feature.melspectrogram(y=y, sr=SR, hop_length=HOP, n_mels=64, fmin=30, fmax=11000)
    return librosa.power_to_db(m + 1e-10)


def best_corr(ref, cand):
    """Corrélation de Pearson maximale d'un motif sur l'autre, décalage en temps seulement."""
    a, b = (ref, cand) if ref.shape[1] >= cand.shape[1] else (cand, ref)
    L = b.shape[1]
    if L < 8:
        return 0.0
    bz = (b - b.mean()) / (b.std() + 1e-9)
    best = -1.0
    for off in range(0, a.shape[1] - L + 1, 2):
        w = a[:, off:off + L]
        wz = (w - w.mean()) / (w.std() + 1e-9)
        c = float((wz * bz).mean())
        best = max(best, c)
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", type=int, default=2)
    args = ap.parse_args()

    pool = {}
    for term in TERMS:
        for p in range(1, args.pages + 1):
            try:
                for c in search(term, p):
                    pool.setdefault(c["id"], c)
            except Exception as e:
                print("recherche en échec", term, p, e)
            time.sleep(0.4)
    print(len(pool), "candidats")

    feats = {}
    for i, (cid, c) in enumerate(pool.items()):
        f = CAND / f"{cid}.mp3"
        if not f.exists():
            try:
                req = urllib.request.Request(c["mp3"], headers=UA)
                f.write_bytes(urllib.request.urlopen(req, timeout=30).read())
                time.sleep(0.15)
            except Exception as e:
                print("téléchargement en échec", cid, e)
                continue
        try:
            y, _ = librosa.load(f, sr=SR, mono=True, duration=6)
            y, _ = librosa.effects.trim(y, top_db=40)
            feats[cid] = logmel(y[: int(3 * SR)])
        except Exception:
            continue
        if i % 200 == 0:
            print(i, "/", len(pool))

    results = {}
    for et in sorted((HERE / "etalons").glob("*.wav")):
        y, _ = librosa.load(et, sr=SR, mono=True)
        ref = logmel(y)
        scores = sorted(((best_corr(ref, m), cid) for cid, m in feats.items()), reverse=True)[:8]
        results[et.stem] = [{"score": round(s, 3), **pool[cid],
                             "page": f"https://www.epidemicsound.com/sound-effects/tracks/{pool[cid]['slug']}/"}
                            for s, cid in scores]
        top = results[et.stem][0]
        print(f"{et.stem:26s} {top['score']:.3f}  {top['title']}")
    (HERE / "matches.json").write_text(json.dumps(results, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
