"""Détecte les bruitages dans la piste sans voix de la référence.

Entrée : stems/htdemucs/ref/no_vocals.wav (sortie Demucs).
Sortie :
  sfx_events.json : un événement par bruitage (début, fin, énergie, timbre).
  clips/NNN_<t>.wav : extrait audio de chaque événement.
  bed.json : niveau du fond musical par seconde.
"""
import json
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf

HERE = Path(__file__).parent
SR = 44100
y, _ = librosa.load(HERE / "stems/htdemucs/ref/no_vocals.wav", sr=SR, mono=True)

hop = 512
rms = librosa.feature.rms(y=y, hop_length=hop)[0]
db = librosa.amplitude_to_db(rms, ref=1.0)
t = librosa.frames_to_time(np.arange(len(db)), sr=SR, hop_length=hop)

# Fond musical : médiane glissante sur 4 s. Un bruitage dépasse ce fond.
win = int(4 * SR / hop)
pad = np.pad(db, (win // 2, win // 2), mode="edge")
bed = np.array([np.median(pad[i:i + win]) for i in range(len(db))])

onset_env = librosa.onset.onset_strength(y=y, sr=SR, hop_length=hop)
onsets = librosa.onset.onset_detect(onset_envelope=onset_env, sr=SR, hop_length=hop,
                                    backtrack=True, delta=0.25, wait=4)

events = []
for f in onsets:
    peak_zone = db[f:f + int(0.4 * SR / hop)]
    if len(peak_zone) == 0:
        continue
    peak = float(peak_zone.max())
    over = peak - bed[f]
    if over < 6 or peak < -45:
        continue
    # fin : retour à 3 dB du fond, max 3 s
    end = f
    while end < len(db) - 1 and end - f < int(3 * SR / hop) and db[end] > bed[end] + 3:
        end += 1
    s0, s1 = int(t[f] * SR), int(t[end] * SR) + int(0.05 * SR)
    seg = y[s0:s1]
    if len(seg) < 512:
        continue
    cent = float(np.mean(librosa.feature.spectral_centroid(y=seg, sr=SR)))
    flat = float(np.mean(librosa.feature.spectral_flatness(y=seg)))
    events.append({
        "t": round(float(t[f]), 2), "dur": round(float(t[end] - t[f]), 2),
        "peak_db": round(peak, 1), "over_bed_db": round(float(over), 1),
        "centroid_hz": round(cent), "flatness": round(flat, 3),
    })

clips = HERE / "clips"
clips.mkdir(exist_ok=True)
for i, e in enumerate(events):
    s0 = int(max(0, e["t"] - 0.05) * SR)
    s1 = int((e["t"] + max(e["dur"], 0.3) + 0.15) * SR)
    sf.write(clips / f"{i:03d}_{e['t']:07.2f}.wav", y[s0:s1], SR)

(HERE / "sfx_events.json").write_text(json.dumps(events, indent=1))
per_sec = [round(float(np.median(bed[(t >= s) & (t < s + 1)])), 1) for s in range(int(t[-1]))]
(HERE / "bed.json").write_text(json.dumps(per_sec))
print(len(events), "événements ; fond médian", round(float(np.median(bed)), 1), "dB")
