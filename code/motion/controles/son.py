"""Contrôles son.

- niveau : intensité intégrée et crête vraie du master (aperçus saturés à 0 dB le 19/10).
- silences : trous de son (aperçu v2 muet à −91 dB le 19/10).
- musique : niveau de la piste musique sous la voix (musique à 0,085 inaudible le 14/10).
- fichiers : aucun aperçu MP3 parmi les bruitages (lqmp3 posés comme bruitages le 19/10)."""
import os, re, subprocess

from .commun import Resultat, sonde, tc


def ebur128(fichier):
    err = subprocess.run(['ffmpeg', '-nostdin', '-v', 'info', '-i', fichier, '-vn', '-af', 'ebur128=peak=true',
                          '-f', 'null', '-'], capture_output=True, text=True).stderr
    resume = err[err.rfind('Summary:'):]
    i = re.search(r'I:\s+(-?[\d.]+|-inf) LUFS', resume)
    p = re.search(r'Peak:\s+(-?[\d.]+|-inf) dBFS', resume)
    val = lambda m: float('-inf') if not m or m[1] == '-inf' else float(m[1])
    return val(i), val(p)


def niveau(master, lufs_min=-17.0, lufs_max=-11.0, crete_max=-0.5):
    i, p = ebur128(master)
    ok = lufs_min <= i <= lufs_max and p <= crete_max
    return Resultat('niveau sonore', ok, detail=f"{i:.1f} LUFS (plage {lufs_min} à {lufs_max}), crête {p:.1f} dBTP (max {crete_max})")


def silences(master, seuil_db=-50, duree_min=1.5, marge=0.5):
    err = subprocess.run(['ffmpeg', '-nostdin', '-v', 'info', '-i', master, '-vn', '-af',
                          f'silencedetect=noise={seuil_db}dB:d={duree_min}', '-f', 'null', '-'],
                         capture_output=True, text=True).stderr
    debuts = [float(x) for x in re.findall(r'silence_start: (-?[\d.]+)', err)]
    fins = [float(x) for x in re.findall(r'silence_end: (-?[\d.]+)', err)]
    duree = sonde(master)['duree']
    trous = []
    for k, d in enumerate(debuts):
        f = fins[k] if k < len(fins) else duree
        if d > marge and f < duree - marge:
            trous.append((d, f))
        elif f - d > duree * 0.5:
            trous.append((d, f))
    return Resultat('silences', not trous, detail=f"{len(trous)} trou(s) sous {seuil_db} dB de plus de {duree_min} s"
                    + ''.join(f" ; {tc(a)}-{tc(b)}" for a, b in trous[:6]),
                    defauts=[{'debut_s': a, 'fin_s': b} for a, b in trous])


def musique(piste_musique, piste_voix, ecart_min=-20.0, ecart_max=-13.0):
    # 15/11/2026 : 9,3 LU sous la voix jugés « beaucoup trop forts » ; 20 LU acceptés le 10/11 (violon cabinets v3).
    # 26/10/2026 : musique 18 LU sous la voix, Lucien « on n'entend rien ». Plancher relevé de -25 à -15 dB.
    m, _ = ebur128(piste_musique)
    v, _ = ebur128(piste_voix)
    e = m - v
    return Resultat('musique sous la voix', ecart_min <= e <= ecart_max,
                    detail=f"musique {m:.1f} LUFS, voix {v:.1f} LUFS, écart {e:.1f} dB (plage {ecart_min} à {ecart_max})")


def fichiers(dossiers):
    mauvais = []
    for d in dossiers:
        for racine, _, noms in os.walk(d):
            for n in noms:
                if n.lower().endswith('.mp3') or 'lqmp3' in n.lower() or 'preview' in n.lower():
                    mauvais.append(os.path.join(racine, n))
    return Resultat('bruitages en WAV', not mauvais,
                    detail=f"{len(mauvais)} aperçu(s) MP3 parmi les sons" + ''.join(f" ; {os.path.basename(x)}" for x in mauvais[:5]),
                    defauts=mauvais)
