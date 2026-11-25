"""Repère l'arrivée du doigt levé, à gauche et à droite, sur le montage 1080x1920."""
import json, subprocess, sys
from pathlib import Path
import numpy as np
V = sys.argv[1]
W, H = 1080, 1920
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", V, "-vf", "scale=270:480", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                     capture_output=True, check=True).stdout
fr = np.frombuffer(raw, np.uint8).reshape(-1, 480, 270, 3).astype(int)
fps = 30000 / 1001
def top(f, x0, x1):
    R, G, B = f[..., 0], f[..., 1], f[..., 2]
    skin = (R > 100) & (R - B > 40) & (R > G) & (G > B)
    skin[:, :x0] = False; skin[:, x1:] = False; skin[300:] = False
    rows = np.where(skin.sum(1) >= 2)[0]
    return rows.min() if len(rows) else 480
Ly = np.array([top(f, 0, 85) for f in fr]); Ry = np.array([top(f, 185, 270) for f in fr])
Path("gestes_y.json").write_text(json.dumps({"L": Ly.tolist(), "R": Ry.tolist()}))
for name, y in (("G", Ly), ("D", Ry)):
    ev = []
    i = 0
    while i < len(y):
        if y[i] < 140:  # doigt au-dessus des épaules
            j = i
            while j < len(y) and y[j] < 140: j += 1
            seg = y[i:j]; m = seg.min()
            arr = i + int(np.argmax(seg <= m + 4))
            if j - i >= 6: ev.append((arr, j))
            i = j
        else:
            i += 1
    print(name, " ".join(f"{a}({a/fps:.2f}s→{b/fps:.2f})" for a, b in ev))
