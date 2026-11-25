"""Pose les bips à la milliseconde, aux instants de la référence, sur la vidéo rendue par Remotion.

Les départs de la référence sont mesurés avec compare_bips.py. Cette mesure ajoute 12,7 ms
à un bip seul : on les retire pour obtenir le vrai départ.
"""
import json
import subprocess
import sys
from pathlib import Path

here = Path(__file__).parent
video, out = sys.argv[1], sys.argv[2]
gain = float(sys.argv[3]) if len(sys.argv) > 3 else 0.5
cfg = json.loads((here / "cuts3.json").read_text())
starts = [round((t - 0.0127) * 1000) for t in cfg["bips_ref"]]
bip = here.parent / "remotion" / "public" / "sfx" / "bip.wav"
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", video],
                           capture_output=True, text=True, check=True).stdout.split()[0])
args = ["ffmpeg", "-v", "error", "-y", "-i", video]
for _ in starts:
    args += ["-i", str(bip)]
parts = [f"[{k + 1}]adelay={ms}:all=1,volume={gain}[b{k}]" for k, ms in enumerate(starts)]
mix = "".join(f"[b{k}]" for k in range(len(starts))) + f"amix=inputs={len(starts)}:normalize=0,apad,atrim=0:{dur:.3f}[a]"
args += ["-filter_complex", ";".join(parts + [mix]), "-map", "0:v", "-map", "[a]", "-c:v", "copy",
         "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-movflags", "+faststart", out]
subprocess.run(args, check=True)
print(out)
