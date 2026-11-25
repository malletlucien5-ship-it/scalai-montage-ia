"""Étalonnages proposés, appliqués par-dessus le montage actuel. Sortie : planche comparée."""
import subprocess
import sys
from pathlib import Path

FIX = "colorchannelmixer=rr=1.0:gg=0.972:bb=0.99"  # retire la dominante verte du mur
S_SOFT = "curves=all=0/0 0.25/0.22 0.75/0.80 1/1"
S_CINE = "curves=all=0/0 0.25/0.20 0.75/0.82 1/1"
LOOKS = {
    "A Lumineux naturel": f"{FIX},eq=brightness=0.03:contrast=1.06:saturation=1.12,unsharp=5:5:0.5",
    "B Chaud premium": f"{FIX},colorbalance=rm=0.03:bm=-0.03:rh=0.02:bh=-0.02,"
                       f"eq=brightness=0.02:contrast=1.10:saturation=1.2,{S_SOFT},unsharp=5:5:0.5",
    "C Ciné teal-orange": f"{FIX},colorbalance=rs=-0.05:gs=0.01:bs=0.07:rh=0.05:bh=-0.05,"
                          f"eq=brightness=0.01:contrast=1.10:saturation=1.1,{S_CINE},unsharp=5:5:0.5",
    "D Pub éclatante": f"{FIX},eq=brightness=0.05:contrast=1.14:saturation=1.28,vibrance=intensity=0.2,unsharp=5:5:0.8",
}

if __name__ == "__main__":
    src, out = sys.argv[1], sys.argv[2]
    names = ["Actuel", *LOOKS]
    parts = [f"[0]split={len(names)}" + "".join(f"[i{k}]" for k in range(len(names)))]
    parts.append("[i0]null[o0]")
    for k, (name, f) in enumerate(LOOKS.items(), start=1):
        parts.append(f"[i{k}]{f}[o{k}]")
    labels = []
    for k, name in enumerate(names):
        labels.append(f"[o{k}]drawtext=text='{name}':x=24:y=24:fontsize=60:fontcolor=white:box=1:boxcolor=black@0.6[t{k}]")
    parts += labels
    parts.append("".join(f"[t{k}]" for k in range(len(names))) + f"hstack={len(names)},scale=3000:-1")
    graph = Path(out).with_suffix(".filter")
    graph.write_text(";".join(parts))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-/filter_complex", str(graph), out], check=True)
