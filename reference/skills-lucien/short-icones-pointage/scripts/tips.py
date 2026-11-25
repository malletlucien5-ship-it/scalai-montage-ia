"""Repère le bout du doigt (pixel de peau le plus à droite) sur le montage 1080x1920."""
import json, subprocess, sys
import numpy as np
V = sys.argv[1]
reveals = {"S1": [6, 42, 78], "S2": [111, 145, 187], "S3": [241, 294, 337]}
W, H = 1080, 1920
def frame(n):
    b = subprocess.run(["ffmpeg", "-v", "error", "-i", V, "-vf", f"select=eq(n\\,{n})", "-frames:v", "1",
                        "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    return np.frombuffer(b, np.uint8).reshape(H, W, 3).astype(int)
out = {}
for sec, rs in reveals.items():
    out[sec] = []
    for r in rs:
        pts = []
        for n in range(r, r + 13, 3):
            a = frame(n)
            R, G, B = a[..., 0], a[..., 1], a[..., 2]
            skin = (R > 110) & (R - B > 45) & (R > G) & (G > B)
            skin[:, :430] = False; skin[:700] = False; skin[1500:] = False
            cols = np.where(skin.sum(0) >= 3)[0]
            if len(cols) == 0: continue
            x = cols.max()
            ys = np.where(skin[:, x - 4:x + 1].any(1))[0]
            pts.append((int(x), int(np.median(ys))))
        xs, ys = zip(*pts)
        out[sec].append({"reveal": r, "x": int(np.median(xs)), "y": int(np.median(ys)), "samples": pts})
        print(sec, r, out[sec][-1]["x"], out[sec][-1]["y"], pts)
json.dump(out, open(sys.argv[2], "w"), indent=1)
