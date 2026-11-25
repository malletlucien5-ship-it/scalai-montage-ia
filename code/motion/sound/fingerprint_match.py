"""Test d'identité des bruitages par empreinte de pics spectraux (principe de Shazam).

On repère les pics du spectrogramme, on forme des paires (f1, f2, écart de temps)
et on compte les paires communes entre un étalon et un candidat avec un décalage
temporel constant. Un fichier identique donne un pic net de votes, même sous la
musique. Un son simplement ressemblant n'en donne presque pas.
Candidats : candidats/*.mp3 (aperçus Epidemic). Sortie : fingerprint.json.
"""
import json
from collections import Counter
from pathlib import Path

import librosa
import numpy as np
from scipy.ndimage import maximum_filter

HERE = Path(__file__).parent
SR = 22050
N_FFT, HOP = 2048, 256
FAN = 8


def landmarks(y):
    S = np.abs(librosa.stft(y, n_fft=N_FFT, hop_length=HOP))
    D = librosa.amplitude_to_db(S, ref=np.max)
    loc = (maximum_filter(D, size=(15, 9)) == D) & (D > -45)
    f_idx, t_idx = np.nonzero(loc)
    order = np.argsort(t_idx)
    pts = list(zip(t_idx[order], f_idx[order]))
    hashes = []
    for i, (t1, f1) in enumerate(pts):
        for t2, f2 in pts[i + 1:i + 1 + FAN]:
            dt = t2 - t1
            if 0 < dt <= 60:
                hashes.append(((f1 // 2, f2 // 2, dt), t1))
    return hashes


def index(hashes):
    idx = {}
    for h, t in hashes:
        idx.setdefault(h, []).append(t)
    return idx


cands = {}
for f in sorted((HERE / "candidats").glob("*.mp3")):
    try:
        y, _ = librosa.load(f, sr=SR, mono=True, duration=10)
        cands[f.stem] = index(landmarks(y))
    except Exception:
        pass
print(len(cands), "candidats indexés")

meta = {}
for v in json.loads((HERE / "matches.json").read_text()).values():
    for c in v:
        meta[str(c["id"])] = c["title"]

out = {}
for et in sorted((HERE / "etalons").glob("*.wav")):
    y, _ = librosa.load(et, sr=SR, mono=True)
    lm = landmarks(y)
    res = []
    for cid, idx in cands.items():
        votes = Counter()
        for h, t in lm:
            for tc in idx.get(h, ()):
                votes[t - tc] += 1
        best = votes.most_common(1)[0][1] if votes else 0
        res.append((best, cid))
    res.sort(reverse=True)
    top = res[:5]
    second = res[1][0] if len(res) > 1 else 0
    out[et.stem] = [{"votes": v, "id": c, "titre": meta.get(c, "?")} for v, c in top]
    print(f"{et.stem:26s} votes {top[0][0]:3d} (2e : {second:3d}, médiane : {int(np.median([r[0] for r in res]))})  {meta.get(top[0][1], top[0][1])}")
(HERE / "fingerprint.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
