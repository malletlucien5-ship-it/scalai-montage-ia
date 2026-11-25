"""Choisit, pour chaque type de bruitage, les sons Epidemic les plus proches de ceux de Dan.

Pour chaque type (clic, pop, grave, whoosh, notification, frappe) :
1. prend les 20 événements de la référence les plus sûrs de ce type (sfx_types.json) ;
2. calcule leur empreinte CLAP moyenne ;
3. classe les aperçus Epidemic de candidats/ par similarité cosinus.
Les sons confirmés identiques (fp_scan) sont imposés pour « nappe » et « impact chapitre ».
Sortie : sfx_choix.json et sfx_choix.md (3 propositions par type).
"""
import json
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


def emb(chunks):
    out = []
    for i in range(0, len(chunks), 32):
        inp = proc(audio=chunks[i:i + 32], sampling_rate=SR, return_tensors="pt").to(dev)
        with torch.no_grad():
            e = model.get_audio_features(**inp)
        e = getattr(e, "pooler_output", e)
        out.append(torch.nn.functional.normalize(e, dim=-1).cpu().numpy())
    return np.concatenate(out)


meta = json.loads((HERE / "candidats_meta.json").read_text())
cache = HERE / "cand_emb.npz"
if cache.exists():
    z = np.load(cache, allow_pickle=True)
    ids, E = list(z["ids"]), z["E"]
else:
    ids, chunks = [], []
    for f in sorted((HERE / "candidats").glob("*.mp3")):
        try:
            y, _ = librosa.load(f, sr=SR, mono=True, duration=4)
            y, _ = librosa.effects.trim(y, top_db=40)
        except Exception:
            continue
        if len(y) < SR // 20:
            continue
        ids.append(f.stem)
        chunks.append(y[: int(2 * SR)])
    E = emb(chunks)
    np.savez(cache, ids=np.array(ids), E=E)
print(len(ids), "candidats")

ref, _ = librosa.load(HERE / "stems/htdemucs/ref/no_vocals.wav", sr=SR, mono=True)
events = json.loads((HERE / "sfx_types.json").read_text())

choix = {}
for typ in ("clic", "pop", "grave", "whoosh", "notification"):
    ev = sorted((e for e in events if e["type_son"] == typ), key=lambda e: -e["proba"])[:20]
    if not ev:
        continue
    chunks = [ref[int(max(0, e["t"] - 0.03) * SR):int((e["t"] + 0.8) * SR)] for e in ev]
    q = emb(chunks).mean(axis=0)
    q /= np.linalg.norm(q)
    s = E @ q
    top = np.argsort(-s)[:3]
    choix[typ] = [{"id": ids[i], "score": round(float(s[i]), 3), **meta.get(ids[i], {}),
                   "exemples_ref": [e["t"] for e in ev[:5]]} for i in top]

# sons confirmés identiques par empreinte
choix["nappe (écran titre)"] = [{"id": "197891", "score": 1.0, "title": "Low, Long 03", "slug": "PP2iNsmWDD",
                                 "exemples_ref": [44.81, 296.05, 426.09, 614.68, 762.13]}]
choix["impact (carte chapitre)"] = [{"id": "?", "score": 1.0, "title": "Designed, Boom, Low Hit", "slug": "pmCzzPFo22",
                                     "exemples_ref": [25.59, 82.48, 264.71, 403.56, 576.6, 734.96]}]

(HERE / "sfx_choix.json").write_text(json.dumps(choix, indent=1, ensure_ascii=False))
lines = ["| Type | Proposition | Similarité | Exemples chez Dan (s) |", "|---|---|---|---|"]
for typ, lst in choix.items():
    for k, c in enumerate(lst):
        url = f"https://www.epidemicsound.com/sound-effects/tracks/{c.get('slug')}/"
        lines.append(f"| {typ if k == 0 else ''} | [{c.get('title', c['id'])}]({url}) | {c['score']} | "
                     f"{', '.join(str(t) for t in c['exemples_ref']) if k == 0 else ''} |")
(HERE / "sfx_choix.md").write_text("\n".join(lines) + "\n")
print("\n".join(lines))
