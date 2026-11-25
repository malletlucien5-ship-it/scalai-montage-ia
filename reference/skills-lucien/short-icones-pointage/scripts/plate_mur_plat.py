"""Remplace le coin du mur (droite de l'image) par le prolongement du mur plat.

Le pan x 700-800 du fond est recopié en miroir alterné jusqu'au bord droit.
Sous y = 1700, les prises électriques occupent ce pan : on prend alors x 780-880.
"""
import subprocess
from pathlib import Path

import numpy as np

here = Path(__file__).parent
W, H = 1080, 1920
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(here / "plate_raw.png"), "-f", "rawvideo",
                      "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
a = np.frombuffer(raw, np.uint8).reshape(H, W, 3).copy()


def fill(rows: slice, src0: int, start: int) -> None:
    strip = a[rows, src0:src0 + 100]
    x, k = start, 0
    while x < W:
        tile = strip[:, ::-1] if k % 2 == 0 else strip
        n = min(100, W - x)
        a[rows, x:x + n] = tile[:, :n]
        x += n
        k += 1


fill(slice(0, 1700), 700, 800)
fill(slice(1700, H), 780, 880)
out = here / "plate_miroir.png"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                "-i", "-", str(out)], input=a.tobytes(), check=True)
print(out)
