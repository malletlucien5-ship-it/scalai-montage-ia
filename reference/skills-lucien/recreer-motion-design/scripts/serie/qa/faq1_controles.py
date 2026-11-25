"""Contrôles FAQ1 v4 sur un rendu (master ou aperçu). Usage : python3 controles.py <fichier.mp4> [w h] → JSON sur la sortie standard.

Décodage complet, nombre d'images, format, synchro audio/vidéo, voix identique au montage (aucune coupe, donc aucun mot coupé),
fin du dernier mot audible, sonie voix et mix, crête vraie, couverture des mots par les sous-titres.
"""
import json, subprocess, sys
from pathlib import Path
import numpy as np, soundfile as sf

ICI = Path(__file__).resolve().parent.parent
f = Path(sys.argv[1]); W, H = (int(sys.argv[2]), int(sys.argv[3])) if len(sys.argv) > 3 else (2560, 1440)
props = json.loads((ICI / "props.json").read_text())
T = json.loads((ICI / "transcript.json").read_text())
ATTENDU = round(props["total"] * 50)
res = {"fichier": f.name, "controles": []}


def ok(id_, cond, detail, valeur=None):
    res["controles"].append({"id": id_, "ok": bool(cond), "detail": detail, **({"valeur": valeur} if valeur is not None else {})})


def sh(*a):
    return subprocess.run(a, capture_output=True, text=True)


# 1. Décodage complet
r = sh("ffmpeg", "-v", "error", "-i", str(f), "-f", "null", "-")
ok("decodage_complet", r.returncode == 0 and not r.stderr.strip(), "ffmpeg -f null : aucune erreur" if not r.stderr.strip() else r.stderr[:300])

# 2. Format et nombre d'images (décompte réel des paquets)
v = json.loads(sh("ffprobe", "-v", "error", "-select_streams", "v:0", "-count_packets", "-show_entries",
                  "stream=codec_name,width,height,r_frame_rate,nb_read_packets,duration,start_time,pix_fmt", "-of", "json", str(f)).stdout)["streams"][0]
a = json.loads(sh("ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=codec_name,sample_rate,channels,duration,start_time",
                  "-of", "json", str(f)).stdout)["streams"][0]
n = int(v["nb_read_packets"])
ok("nombre_images", n == ATTENDU, f"{n} images pour {ATTENDU} attendues ({props['total']} s à 50 i/s)", n)
ok("format_video", (v["width"], v["height"], v["r_frame_rate"]) == (W, H, "50/1"), f"{v['codec_name']} {v['width']}x{v['height']} {v['r_frame_rate']} {v['pix_fmt']}")
ok("format_audio", a["codec_name"] == "aac" and a["sample_rate"] == "48000", f"{a['codec_name']} {a['sample_rate']} Hz {a['channels']} canaux")
dv, da = float(v["duration"]), float(a["duration"])
ecart = abs(float(v.get("start_time", 0)) - float(a.get("start_time", 0))) * 1000
ok("synchro_debut", ecart <= 5, f"écart de départ audio/vidéo {ecart:.1f} ms", round(ecart, 2))
ok("durees", abs(dv - da) <= 0.03, f"vidéo {dv:.3f} s, audio {da:.3f} s", [dv, da])

# 3. Voix : l'audio du rendu suit la voix du montage sans décalage ni coupe (corrélation par fenêtres de 2 s)
tmp = ICI / "work" / f"ctrl-{f.stem}.wav"
sh("ffmpeg", "-v", "error", "-y", "-i", str(f), "-vn", "-ac", "1", "-ar", "48000", "-c:a", "pcm_f32le", str(tmp))
m, sr = sf.read(tmp); vsrc, _ = sf.read(ICI / "work" / "voix48.wav")
# voix de référence : segments gardés par Lucien, mis bout à bout (temps de sortie)
segs = props["plateSegs"]
vo = np.concatenate([vsrc[int(round(g["src"] * sr)):int(round(g["src"] * sr)) + int(round(g["dur"] * sr))] for g in segs])
lags = []
for t0 in np.arange(1.0, props["total"] - 2.5, 5.0):
    i = int(t0 * sr); w = int(2 * sr); P = int(0.05 * sr)
    x = vo[i:i + w]; y = m[i - P:i + w + P]
    N = 1 << int(np.ceil(np.log2(len(y) + len(x))))
    cc = np.fft.irfft(np.fft.rfft(y, N) * np.conj(np.fft.rfft(x, N)), N)[:len(y) - len(x) + 1]
    lags.append((int(np.argmax(cc)) - P) / sr * 1000)
lmax = max(abs(l) for l in lags)
ok("voix_calee", lmax <= 2.0, f"décalage voix rendu/montage sur {len(lags)} fenêtres : max {lmax:.2f} ms (tolérance 2 ms ; AAC)", round(lmax, 2))
# Coupes de Lucien : niveau de la voix source à chaque borne (fenêtre de 10 ms) et mot éventuellement entamé
bornes = []
for i, g in enumerate(segs):
    for t, cote in ([(g["src"], "entrée")] if i else []) + ([(g["src"] + g["dur"], "sortie")] if i < len(segs) - 1 else []):
        j = int(t * sr); x = vsrc[j - int(0.005 * sr):j + int(0.005 * sr)]
        bornes.append({"t_src": round(t, 2), "cote": cote, "niveau_db": round(float(20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12)), 1)})
res["bornes_coupes"] = bornes
fortes = [b for b in bornes if b["niveau_db"] > -30]
ok("aucune_coupe_dans_un_mot", lmax <= 2.0 and all(b["t_src"] in (17.72, 64.24, 68.44) for b in fortes),
   f"{len(bornes)} bornes : {len(bornes) - len(fortes)} sous −30 dB ; au-dessus : {[(b['t_src'], b['niveau_db']) for b in fortes]} "
   "(17,72 : parole liée « mais | de », retrait choisi par Lucien ; 64,24 → 68,44 : raccord voulu entre deux « et »)")
# Clics : saut d'échantillon au raccord comparé aux sauts des 200 ms autour
clics = []
for g in segs[1:]:
    j = int(round(g["out"] * sr)); d = np.abs(np.diff(m[j - int(0.1 * sr):j + int(0.1 * sr)]))
    c0 = int(0.1 * sr); pic = float(d[c0 - 240:c0 + 240].max()); ref_ = float(np.percentile(d, 99))
    clics.append({"t": g["out"], "rapport": round(pic / (ref_ + 1e-12), 2)})
res["clics"] = clics
ok("aucun_clic_aux_coupes", all(c["rapport"] < 2.0 for c in clics), f"saut maximal au raccord / 99e centile local : {[c['rapport'] for c in clics]} (seuil 2,0)")

# 4. Fin du dernier mot audible
dern = T["words"][-1]
def db(s, e):
    x = m[int(s * sr):int(e * sr)]
    return 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12)
# dernier mot : « informations » (source 185,00 → 185,48), dans le dernier segment
g = segs[-1]; ds = g["out"] + dern["s"] - g["src"]; de = g["out"] + 185.48 - g["src"]
fin_mot = db(ds, de); apres = db(g["out"] + 185.52 - g["src"], g["out"] + g["dur"])
ok("dernier_mot_audible", fin_mot > -40, f"« {dern['w']} » ({ds:.2f} → {de:.2f} s) à {fin_mot:.1f} dB RMS ; ensuite {apres:.1f} dB jusqu'à la fin de la plaque", round(fin_mot, 1))

# 5. Sonie
def lufs(path, extra=()):
    r = sh("ffmpeg", "-hide_banner", "-i", str(path), *extra, "-af", "ebur128=peak=true", "-f", "null", "-").stderr
    tail = r[r.rindex("Summary:"):]
    I = float(tail.split("I:")[1].split("LUFS")[0]); P = float(tail.split("Peak:")[1].split("dBFS")[0])
    return I, P
Iv, _ = lufs(ICI / "work" / "voix48.wav")
Im, Pm = lufs(f)
ok("lufs_voix", abs(Iv + 16) <= 0.5, f"voix seule {Iv:.1f} LUFS (cible ≈ −16)", Iv)
ok("lufs_mix", abs(Im + 15.76) <= 0.5, f"mix final {Im:.1f} LUFS (cible −15,76 ± 0,5)", Im)
ok("crete_vraie", Pm <= -1.5, f"crête vraie {Pm:.1f} dBTP (guide ≤ −1,5) ; la voix livrée plafonne à −1,2 dBFS, aucun limiteur ajouté", Pm)

# 6. Sous-titres : part des mots couverts par un sous-titre ou un texte de panneau
ph = props["phrases"]; sc = props["scenes"]
def couvert(t):
    s = next((x for x in sc if x["s"] <= t < x["e"]), None)
    if s and s["kind"] == "split":
        return True
    if s and any(g["s"] <= t < g["e"] and g["pos"] == "off" for g in s.get("legende") or []):
        return s["kind"] == "question"  # la question tient lieu de texte pendant 2 s
    return any(p["s"] <= t < p["e"] for p in ph)
def vers_sortie(t):
    for g in props["plateSegs"]:
        if g["src"] <= t <= g["src"] + g["dur"]:
            return g["out"] + t - g["src"]
    return None
mid = [x for x in (vers_sortie((w["s"] + w["e"]) / 2) for w in T["words"]) if x is not None]
c = sum(couvert(t) for t in mid) / len(mid)
ok("texte_sur_les_mots", c >= 0.95, f"{100 * c:.1f} % des mots ont un texte à l'écran", round(c, 4))
sans_st = [round(t, 2) for t in mid if not any(p["s"] <= t < p["e"] for p in ph)]
res["mots_sans_sous_titre"] = sans_st
print(json.dumps(res, ensure_ascii=False, indent=1))
