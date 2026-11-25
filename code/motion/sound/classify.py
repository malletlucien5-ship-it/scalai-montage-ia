"""Classe les bruitages et la musique de la référence par type, avec CLAP (zéro exemple).

Bruitages : chaque événement de sound_map.json (extrait de 1 s sur la piste sans voix)
reçoit un type parmi TYPES_SFX. « musique » et « silence » servent à écarter les faux événements.
Musique : fenêtres de 10 s, style parmi STYLES_MUSIQUE.
Sorties : sfx_types.json, sfx_types_par_id.md, music_styles.json.
"""
import json
from collections import Counter, defaultdict
from pathlib import Path

import librosa
import numpy as np
import torch
from transformers import ClapModel, ClapProcessor

HERE = Path(__file__).parent
SR = 48000
dev = "mps" if torch.backends.mps.is_available() else "cpu"
model = ClapModel.from_pretrained("laion/larger_clap_general").to(dev).eval()
proc = ClapProcessor.from_pretrained("laion/larger_clap_general")

TYPES_SFX = {
    "clic": "a single mouse click or button click sound",
    "frappe": "fast keyboard typing sound",
    "whoosh": "a fast whoosh swoosh transition sound effect",
    "pop": "a short soft pop or bubble pop user interface sound",
    "impact": "a deep cinematic boom impact hit",
    "grave": "a short low bass thump or sub hit",
    "montée": "a rising riser build up sound effect",
    "nappe": "a low rumbling drone ambience",
    "notification": "a notification chime ding",
    "musique": "background music with drums and melody",
    "silence": "near silence, quiet room tone",
}
STYLES_MUSIQUE = {
    "piano": "calm piano music",
    "ambient": "ambient atmospheric pad music, mysterious",
    "electronic": "electronic music with synth and beat",
    "lofi": "chill lo-fi hip hop beat",
    "cinematic": "cinematic orchestral music with strings",
    "corporate": "upbeat corporate motivational music",
    "tension": "dark suspenseful tension music",
    "guitar": "acoustic guitar music",
}


def text_emb(d):
    inp = proc(text=list(d.values()), return_tensors="pt", padding=True).to(dev)
    with torch.no_grad():
        e = model.get_text_features(**inp)
    e = getattr(e, "pooler_output", e)
    return torch.nn.functional.normalize(e, dim=-1)


def audio_emb(chunks):
    inp = proc(audio=chunks, sampling_rate=SR, return_tensors="pt").to(dev)
    with torch.no_grad():
        e = model.get_audio_features(**inp)
    e = getattr(e, "pooler_output", e)
    return torch.nn.functional.normalize(e, dim=-1)


y, _ = librosa.load(HERE / "stems/htdemucs/ref/no_vocals.wav", sr=SR, mono=True)
T_sfx, T_mus = text_emb(TYPES_SFX), text_emb(STYLES_MUSIQUE)
k_sfx, k_mus = list(TYPES_SFX), list(STYLES_MUSIQUE)

events = json.loads((HERE / "sound_map.json").read_text())
out = []
for i in range(0, len(events), 32):
    batch = events[i:i + 32]
    chunks = [y[int(max(0, e["t"] - 0.05) * SR):int((e["t"] + 1.0) * SR)] for e in batch]
    sims = (audio_emb(chunks) @ T_sfx.T).softmax(dim=-1).cpu().numpy()
    for e, s in zip(batch, sims):
        j = int(s.argmax())
        out.append({**e, "type_son": k_sfx[j], "proba": round(float(s[j]), 2)})
(HERE / "sfx_types.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))

keep = [o for o in out if o["type_son"] not in ("musique", "silence")]
by = defaultdict(Counter)
for o in keep:
    for k in o["ids"]:
        by[k][o["type_son"]] += 1
lines = ["| ID | types de bruitages (nombre) |", "|---|---|"]
for k in sorted(by):
    lines.append(f"| {k} | " + ", ".join(f"{t} {n}" for t, n in by[k].most_common()) + " |")
(HERE / "sfx_types_par_id.md").write_text("\n".join(lines) + "\n")
print("bruitages :", Counter(o["type_son"] for o in out).most_common())

win = 10 * SR
mus = []
for s in range(0, len(y) - win, win):
    sims = (audio_emb([y[s:s + win]]) @ T_mus.T).softmax(dim=-1).cpu().numpy()[0]
    order = np.argsort(-sims)[:2]
    mus.append({"t": s // SR, "style": k_mus[order[0]], "p": round(float(sims[order[0]]), 2),
                "second": k_mus[order[1]]})
(HERE / "music_styles.json").write_text(json.dumps(mus, indent=1, ensure_ascii=False))
print(" ".join(f"{m['t']}:{m['style']}" for m in mus))
