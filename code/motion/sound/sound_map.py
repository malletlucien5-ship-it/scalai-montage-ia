"""Carte des bruitages par bande de fréquence, rattachée aux motion designs.

Trois détecteurs sur la piste sans voix (Demucs) :
  grave  : 30-160 Hz, les « thumps » d'apparition et les impacts ;
  aigu   : 3-16 kHz, les clics, frappes et whooshes ;
  large  : pic simultané grave + aigu, les impacts de transition.
Chaque événement est rattaché à l'ID du catalogue dont la plage le contient.
Sortie : sound_map.json et sound_map.md.
"""
import json
import re
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf

HERE = Path(__file__).parent
SR = 22050
HOP = 256
y, _ = librosa.load(HERE / "stems/htdemucs/ref/no_vocals.wav", sr=SR, mono=True)
S = np.abs(librosa.stft(y, n_fft=2048, hop_length=HOP)) ** 2
freqs = librosa.fft_frequencies(sr=SR, n_fft=2048)
times = librosa.frames_to_time(np.arange(S.shape[1]), sr=SR, hop_length=HOP)


def band_db(lo, hi):
    return 10 * np.log10(S[(freqs >= lo) & (freqs < hi)].sum(axis=0) + 1e-12)


def rolling_median(x, sec):
    w = int(sec * SR / HOP)
    p = np.pad(x, (w // 2, w // 2), mode="edge")
    return np.array([np.median(p[i:i + w]) for i in range(0, len(x))])


def peaks(db, bed, over, min_gap):
    ex = db - bed
    out, last = [], -1e9
    for i in range(1, len(ex) - 1):
        if ex[i] > over and ex[i] >= ex[i - 1] and ex[i] >= ex[i + 1] and times[i] - last > min_gap:
            # début : remonte tant que l'énergie décroît
            j = i
            while j > 0 and ex[j - 1] < ex[j] and ex[j - 1] > over / 3:
                j -= 1
            out.append((float(times[j]), float(times[i]), float(ex[i])))
            last = times[i]
    return out


low = band_db(30, 160)
high = band_db(3000, 16000)
low_ev = peaks(low, rolling_median(low, 6), 12, 0.35)
high_ev = peaks(high, rolling_median(high, 6), 12, 0.08)

# Plages du catalogue
cat = {}
for line in (HERE.parent / "CATALOGUE.md").read_text().splitlines():
    m = re.match(r"\| (\d\d) \| ([\w-]+) \| ([^|]+) \|", line)
    if not m:
        continue
    ranges = []
    for r in re.findall(r"(\d+)(?:-(\d+))?", m.group(3)):
        a = int(r[0]); b = int(r[1]) if r[1] else a + 1
        ranges.append((a - 0.6, b + 0.6))
    cat[f"{m.group(1)}-{m.group(2)}"] = ranges


def owner(t):
    hits = [k for k, rs in cat.items() for a, b in rs if a <= t <= b]
    return hits or ["(hors catalogue)"]


events = []
for kind, evs in (("grave", low_ev), ("aigu", high_ev)):
    for start, peak, over in evs:
        events.append({"type": kind, "t": round(start, 2), "pic": round(peak, 2),
                       "au_dessus_du_fond_db": round(over, 1), "ids": owner(start)})
events.sort(key=lambda e: e["t"])

# « large » : grave et aigu à moins de 80 ms
for e in events:
    if e["type"] == "grave" and any(o["type"] == "aigu" and abs(o["t"] - e["t"]) < 0.08 for o in events):
        e["type"] = "impact"

clips = HERE / "clips_map"
clips.mkdir(exist_ok=True)
for i, e in enumerate(events):
    s0 = int(max(0, e["t"] - 0.08) * SR)
    s1 = int((e["t"] + 0.9) * SR)
    sf.write(clips / f"{e['t']:07.2f}_{e['type']}.wav", y[s0:s1], SR)

(HERE / "sound_map.json").write_text(json.dumps(events, indent=1, ensure_ascii=False))
by_id = {}
for e in events:
    for k in e["ids"]:
        by_id.setdefault(k, []).append(e)
lines = ["| ID | graves | aigus | impacts | premiers instants |", "|---|---|---|---|---|"]
for k in sorted(by_id):
    ev = by_id[k]
    c = {t: sum(1 for e in ev if e["type"] == t) for t in ("grave", "aigu", "impact")}
    lines.append(f"| {k} | {c['grave']} | {c['aigu']} | {c['impact']} | "
                 + ", ".join(f"{e['t']}" for e in ev[:6]) + " |")
(HERE / "sound_map.md").write_text("\n".join(lines) + "\n")
print(len(events), "événements :", {t: sum(1 for e in events if e["type"] == t) for t in ("grave", "aigu", "impact")})
