"""Retrouve où chaque morceau Epidemic est placé dans la référence.

Pour chaque morceau : télécharge l'aperçu public, calcule le chroma, puis cherche
par corrélation glissante quel passage du morceau correspond à chaque fenêtre
de 8 s de la piste sans voix. Sortie : music_map.json, une ligne par fenêtre reconnue
(temps dans la référence, temps dans le morceau, score).
"""
import json
import urllib.request
from pathlib import Path

import librosa
import numpy as np

HERE = Path(__file__).parent
SR = 22050
HOP = 2048
UA = {"User-Agent": "Mozilla/5.0 (Macintosh) sound-match"}
TRACKS = {
    "Apparent Solution - Brendon Moeller": "Apparent Solution",
    "Steall Waters - Luba Hilman": "Steall Waters",
    "Shadowed - John B. Lund": "Shadowed",
    "The Farmhouse - Silver Maple": "The Farmhouse",
    "Pink Pulsar - ELFL": "Pink Pulsar",
}


def preview_url(term, title):
    import urllib.parse
    u = "https://www.epidemicsound.com/json/search/tracks/?" + urllib.parse.urlencode({"term": term})
    d = json.load(urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=30))
    for t in d["entities"]["tracks"].values():
        if t["title"].lower() == title.lower():
            return t["stems"]["full"]["lqMp3Url"], t.get("publicSlug")
    return None, None


def chroma(y):
    c = librosa.feature.chroma_cqt(y=y, sr=SR, hop_length=HOP)
    return c / (np.linalg.norm(c, axis=0, keepdims=True) + 1e-9)


ref, _ = librosa.load(HERE / "stems/htdemucs/ref/no_vocals.wav", sr=SR, mono=True)
cref = chroma(ref)
fps = SR / HOP
win = int(8 * fps)
out = []
(HERE / "music").mkdir(exist_ok=True)
for name, title in TRACKS.items():
    url, slug = preview_url(name, title)
    if not url:
        print("introuvable", name)
        continue
    f = HERE / "music" / f"{title}.mp3"
    if not f.exists():
        f.write_bytes(urllib.request.urlopen(urllib.request.Request(url, headers=UA)).read())
    y, _ = librosa.load(f, sr=SR, mono=True)
    ct = chroma(y)
    for s in range(0, cref.shape[1] - win, int(4 * fps)):
        w = cref[:, s:s + win]
        best, off = 0.0, 0
        for o in range(0, ct.shape[1] - win):
            c = float((w * ct[:, o:o + win]).sum() / win)
            if c > best:
                best, off = c, o
        if best > 0.80:
            out.append({"morceau": name, "slug": slug, "t_ref": round(s / fps, 1),
                        "t_morceau": round(off / fps, 1), "score": round(best, 3)})
    print(name, sum(1 for o in out if o["morceau"] == name), "fenêtres")

out.sort(key=lambda o: (o["t_ref"], -o["score"]))
(HERE / "music_map.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
