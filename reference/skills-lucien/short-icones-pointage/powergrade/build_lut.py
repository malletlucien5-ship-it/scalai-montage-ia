"""Reproduit le nœud « Look » du PowerGrade « P&F colo rapide » pour une source Rec.709.

Nœud Look (décodé du .drx) : CST Rec.709 gamma 2.4 → Rec.709 Cineon, puis LUT
« Film Looks/Rec709 Kodak 2383 D55.cube », le tout mélangé à 50 % avec l'image d'entrée.
Les CST S-Log3 du PowerGrade sont ignorées : la DJI filme en Rec.709, pas en S-Log3.
Sortie : une LUT 3D 65³ au format .cube, utilisable avec ffmpeg lut3d.
"""
import sys
from pathlib import Path

import numpy as np

KODAK = Path("/Applications/DaVinci Resolve.app/Contents/Resources/LUT/Film Looks/Rec709 Kodak 2383 D55.cube")
MIX = float(sys.argv[2]) if len(sys.argv) > 2 else 0.5
N = 65


def read_cube(p: Path):
    size, rows, dmin, dmax = None, [], [0, 0, 0], [1, 1, 1]
    for line in p.read_text().splitlines():
        t = line.strip()
        if not t or t.startswith("#") or t.startswith("TITLE"):
            continue
        if t.startswith("LUT_3D_SIZE"):
            size = int(t.split()[1])
        elif t.startswith("DOMAIN_MIN"):
            dmin = [float(v) for v in t.split()[1:]]
        elif t.startswith("DOMAIN_MAX"):
            dmax = [float(v) for v in t.split()[1:]]
        elif t[0].isdigit() or t[0] in "-.":
            rows.append([float(v) for v in t.split()[:3]])
    lut = np.array(rows).reshape(size, size, size, 3)  # index [b][g][r], r varie le plus vite
    return lut, size, np.array(dmin), np.array(dmax)


def sample(lut, size, rgb):
    x = np.clip(rgb, 0, 1) * (size - 1)
    i0 = np.floor(x).astype(int)
    i0 = np.clip(i0, 0, size - 2)
    f = x - i0
    out = 0
    for db in (0, 1):
        for dg in (0, 1):
            for dr in (0, 1):
                w = ((f[..., 0] if dr else 1 - f[..., 0]) * (f[..., 1] if dg else 1 - f[..., 1])
                     * (f[..., 2] if db else 1 - f[..., 2]))
                out = out + w[..., None] * lut[i0[..., 2] + db, i0[..., 1] + dg, i0[..., 0] + dr]
    return out


def rec709_g24_to_cineon(v):
    lin = np.clip(v, 0, 1) ** 2.4
    b = 10 ** ((95 - 685) / 300)
    return (685 + 300 * np.log10(lin * (1 - b) + b)) / 1023


lut, size, dmin, dmax = read_cube(KODAK)
g = np.linspace(0, 1, N)
b_, g_, r_ = np.meshgrid(g, g, g, indexing="ij")
rgb = np.stack([r_, g_, b_], axis=-1)
cin = (rec709_g24_to_cineon(rgb) - dmin) / (dmax - dmin)
look = sample(lut, size, cin)
res = np.clip((1 - MIX) * rgb + MIX * look, 0, 1)
lines = [f"TITLE \"P&F colo rapide - Look {int(MIX * 100)}% sur Rec709\"", f"LUT_3D_SIZE {N}"]
lines += [f"{v[0]:.6f} {v[1]:.6f} {v[2]:.6f}" for v in res.reshape(-1, 3)]
Path(sys.argv[1]).write_text("\n".join(lines) + "\n")
print(sys.argv[1], "domaine Kodak", dmin, dmax, "taille", size)
