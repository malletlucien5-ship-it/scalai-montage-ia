"""Compare les départs de bips d'un rendu avec ceux de la référence (première note, 1600 Hz)."""
import json
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

here = Path(__file__).parent


def onsets(path: str, approx: list[float]) -> list[float]:
    w = wave.open(path)
    sr = w.getframerate()
    x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(float) / 32768
    n, hop = 1024, 96
    win = np.hanning(n)
    f = np.fft.rfftfreq(n, 1 / sr)
    band = (f > 1500) & (f < 1700)
    ref = (f > 1200) & (f < 1400)
    res = []
    for a in approx:
        ts = np.arange(a - 0.25, a + 0.25, hop / sr)
        e = []
        for t in ts:
            i = max(0, int(t * sr))
            S = np.abs(np.fft.rfft(x[i:i + n] * win))
            e.append(20 * np.log10(S[band].max() + 1e-9) - 20 * np.log10(S[ref].mean() + 1e-9))
        e = np.array(e)
        res.append(float(ts[int(np.argmax(e > e.max() - 6))] + n / 2 / sr))
    return res


video = sys.argv[1]
wav = str(Path(video).with_suffix(".wav"))
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", video, "-vn", "-ac", "1", "-ar", "48000", wav], check=True)
cfg = json.loads((here / "cuts3.json").read_text())
ref = cfg["bips_ref"]
mine = onsets(wav, ref)
print("écarts rendu - référence :", " ".join(f"{(m - r) * 1000:+.0f}" for m, r in zip(mine, ref)), "ms")
