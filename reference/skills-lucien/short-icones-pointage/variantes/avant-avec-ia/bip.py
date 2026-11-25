"""Synthétise le bip de révélation, recopié du spectre de la référence (aucun échantillon extrait).

Spectre mesuré sur le Short jkSJqLsjcQ4 :
- 0 ms : note à 1600 Hz (+ octave 3200), brève ;
- 65 ms : 2100 Hz (+ 4200), et 4800 Hz qui tient ~250 ms ;
- 130 ms : accord 1900 / 2550 / 2850 / 3800 Hz tenu ~350 ms ;
- 130 ms : scintillement qui glisse de 7650 à 7800 Hz pendant ~400 ms.
"""
import wave
from pathlib import Path

import numpy as np

SR = 48000
DUR = 0.75
t = np.arange(int(SR * DUR)) / SR
out = np.zeros_like(t)


def tone(start, freq, amp, tau, length, glide_to=None):
    n0 = int(start * SR)
    n = int(length * SR)
    tt = np.arange(n) / SR
    f = np.full(n, float(freq)) if glide_to is None else freq + (glide_to - freq) * np.clip(tt / length, 0, 1)
    phase = 2 * np.pi * np.cumsum(f) / SR
    env = np.minimum(1, tt / 0.003) * np.exp(-tt / tau)
    env *= np.minimum(1, (length - tt) / 0.02)  # fin douce, sans clic
    seg = amp * env * np.sin(phase)
    end = min(len(out), n0 + n)
    out[n0:end] += seg[: end - n0]


tone(0.000, 1600, 0.50, 0.035, 0.12)
tone(0.000, 3200, 0.18, 0.030, 0.10)
tone(0.065, 2100, 0.50, 0.040, 0.14)
tone(0.065, 4200, 0.18, 0.035, 0.12)
tone(0.065, 4800, 0.28, 0.120, 0.40)
for f, a in ((1900, 0.45), (2550, 0.55), (2850, 0.55), (3800, 0.30)):
    tone(0.130, f, a, 0.150, 0.60)
tone(0.130, 7650, 0.16, 0.200, 0.55, glide_to=7800)

out = out / np.abs(out).max() * 10 ** (-3 / 20)
pcm = (out * 32767).astype(np.int16)
dest = Path(__file__).parent.parent / "remotion" / "public" / "sfx" / "bip.wav"
dest.parent.mkdir(parents=True, exist_ok=True)
with wave.open(str(dest), "wb") as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print(dest)
