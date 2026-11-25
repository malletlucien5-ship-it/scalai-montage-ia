# Usage : python3 caler_coupes.py COUPES.json VOIX.wav TRANSCRIPT.json FIN_TOTALE_S SORTIE.json
# Entrées : coupes DaVinci de Lucien (retire_s), voix complète 48 kHz, transcript mot à mot, fin de la timeline (s).
# Sortie : JSON des coupes calées sur le silence le plus proche (grille 50 i/s, ±80 ms puis ±200 ms), segments gardés, journal.
"""Cale chaque point de coupe de Lucien sur le minimum d'énergie de la voix le plus proche, sur la grille des images (±80 ms, ±200 ms si aucun silence, fenêtre 10 ms).
Usage : python3 caler_coupes.py COUPES.json VOIX.wav TRANSCRIPT.json FIN_TOTALE SORTIE.json"""
import json, subprocess, sys
import numpy as np
C, VOIX, TR, FIN, OUT = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4]), sys.argv[5]
c = json.load(open(C)); mots = json.load(open(TR))["mots"]
SR = 48000
v = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", VOIX, "-f", "f32le", "-"], capture_output=True).stdout, np.float32).astype(float)
e2 = np.convolve(v ** 2, np.ones(480) / 480, "same")
db = lambda t: 10 * np.log10(e2[int(t * SR)] + 1e-12)
FEN = 0.08
journal = []
def caler(t, fen=FEN):
    # candidats sur la grille des images (50 i/s) pour que l'image et la voix coupent au même instant
    cands = [round(t / 0.02) * 0.02 + k * 0.02 for k in range(-10, 11)]
    cands = [x for x in cands if abs(x - t) <= fen + 1e-9]
    m = min(db(x) for x in cands)
    if m > -30 and fen < 0.2:
        return caler(t, 0.2)  # aucun silence à ±80 ms : recherche élargie à ±200 ms
    return round(min((x for x in cands if db(x) <= m + 1.5), key=lambda x: abs(x - t)), 2)
retire = []
for a, b in c["retire_s"]:
    a2, b2 = caler(a), caler(b)
    retire.append([a2, b2])
    for x, y in ((a, a2), (b, b2)):
        dans = [m["word"] for m in mots if m["start"] + 0.02 < y < m["end"] - 0.02]
        journal.append({"lucien_s": x, "cale_s": y, "decalage_ms": round((y - x) * 1000, 1), "energie_avant_db": round(db(x), 1), "energie_apres_db": round(db(y), 1)})
garder = []
t = 0.0
for a, b in retire:
    garder.append([round(t, 4), a]); t = b
garder.append([round(t, 4), FIN])
json.dump({"source": "in/coupes/coupes-lucien.json, points calés sur le minimum d'énergie (±80 ms)", "retire_s": retire, "garder_s": garder,
           "duree_s": round(sum(b - a for a, b in garder), 4), "journal": journal}, open(OUT, "w"), ensure_ascii=False, indent=1)
for j in journal:
    print(f"{j['lucien_s']:8.2f} -> {j['cale_s']:9.4f} ({j['decalage_ms']:+6.1f} ms)  {j['energie_avant_db']:6.1f} -> {j['energie_apres_db']:6.1f} dB")
print("durée", round(sum(b - a for a, b in garder), 4))
