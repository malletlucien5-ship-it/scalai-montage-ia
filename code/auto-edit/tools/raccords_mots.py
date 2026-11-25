#!/usr/bin/env python3
"""Garde-fou des raccords : aucun mot coupé en deux par un raccord automatique.

Le silence d'une consonne (« ré|ponse », « ré|flexion ») passait pour une fin de mot :
la détection de silence et tail_guard coupaient en plein mot (AI Advantage, 10/10/2026).
Ce contrôle mesure l'audio maître autour de chaque raccord. Si la voix est présente
juste avant et juste après la frontière, le raccord tombe dans un mot : la portion
s'allonge jusqu'au premier silence de 100 ms (0,6 s au plus), ou la suivante recule. Les raccords protégés (coupes de Lucien)
ne bougent jamais : ils sont seulement listés.

  python3 raccords_mots.py TABLE.sources.json [--out corrige.json] [--protege coupes.json] [--dry]
"""
import argparse
import json
import os
import subprocess
from pathlib import Path

import numpy as np

SR = 16000
AVANT, APRES = 1.4, 0.9      # fenêtre retranscrite autour d'une frontière (s)
MARGE = 0.08                # un mot doit dépasser la frontière d'au moins 80 ms de chaque côté
CREUX_MAX = 0.35            # micro-creux retiré refermé s'il contient de la voix
RALLONGE_MAX = 0.6          # au-delà, ce n'est plus une fin de mot : listé, jamais restauré
QUEUE = 0.06                # marge ajoutée après la fin du mot restauré


def src(c):
    return c.get('audio') or c['camera']


def charger(path, start, end):
    r = subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-ss', f'{max(0., start):.6f}', '-t',
                        f'{end - max(0., start):.6f}', '-i', path, '-vn', '-ac', '1', '-ar', str(SR),
                        '-f', 's16le', '-'], capture_output=True, check=True)
    return np.frombuffer(r.stdout, np.int16).astype(np.float32) / 32768


SEPARATEUR = 0.8            # silence entre deux fenêtres d'un même lot (s)
LOT = 27.0                  # Whisper lit 30 s par passe : un lot tient dans une passe


def mots(item):
    """Mots horodatés (secondes source) d'une fenêtre audio."""
    return mots_lot([item])[0]


def mots_lot(items):
    """Plusieurs fenêtres collées avec un silence entre elles : une seule passe Whisper.
    Une fenêtre isolée coûtait une passe entière de 30 s (70 s par raccord sous charge)."""
    from segment_transcribe import transcribe
    blocs, places, pos = [], [], 0.
    for path, a, b in items:
        x = charger(path, a, b)
        blocs += [x, np.zeros(int(SEPARATEUR * SR), np.float32)]
        places.append((pos, pos + len(x) / SR, a)); pos += len(x) / SR + SEPARATEUR
    _, words = transcribe(np.concatenate(blocs))
    out = [[] for _ in items]
    for w in words:
        mid = (w['start'] + w['end']) / 2
        for k, (d, f, a) in enumerate(places):
            if d <= mid < f:
                out[k].append((w['word'], a + max(w['start'], d) - d, a + min(w['end'], f) - d)); break
    return out


def lots(fenetres):
    groupe, duree = [], 0.
    for f in fenetres:
        n = f[2] - f[1] + SEPARATEUR
        if groupe and duree + n > LOT:
            yield groupe; groupe, duree = [], 0.
        groupe.append(f); duree += n
    if groupe:
        yield groupe


def voix_proche(path, t, sens):
    """Vrai si la voix est présente dans les 100 ms après (sens=+1) ou avant (sens=-1) l'instant t.
    Seuil de tail_guard : voix = niveau de parole local - 24 dB. Une vraie fin de mot laisse
    au moins 150 ms sans voix ; le silence d'une consonne dure moins de 100 ms."""
    x = charger(path, t - 2.0, t + 2.0)
    if len(x) < 6400:
        return False
    n = len(x) // 320
    db = 20 * np.log10(np.sqrt((x[:n * 320].reshape(n, 320) ** 2).mean(1)) + 1e-9)
    seuil = np.percentile(db, 90) - 24
    i = int(2.0 * SR / 320)
    zone = db[i:i + 5] if sens > 0 else db[max(0, i - 5):i]
    return bool((zone > seuil).sum() >= 2)


def frontieres(doc):
    """(indice du morceau, côté) pour chaque fin et chaque début qui touche un raccord."""
    out = []
    ch = doc['chunks']
    for i in range(len(ch) - 1):
        a, b = src(ch[i]), src(ch[i + 1])
        contigu = a['path'] == b['path'] and abs(b['start'] - a['end']) < 0.01
        if not contigu:
            out.append((i, i + 1))
    return out


def profil(path, t):
    """dB par tranche de 20 ms sur [t-2, t+2] et seuil de voix (niveau de parole local - 24 dB)."""
    x = charger(path, t - 2.0, t + 2.0)
    n = len(x) // 320
    db = 20 * np.log10(np.sqrt((x[:n * 320].reshape(n, 320) ** 2).mean(1)) + 1e-9)
    return db, np.percentile(db, 90) - 24, int(2.0 * SR / 320)


def voisee(db, seuil, i0, i1):
    zone = db[max(0, i0):max(0, i1)]
    return len(zone) > 0 and (zone > seuil).sum() >= 2


def jusqu_au_silence(db, seuil, i, sens):
    """Nombre de tranches de 20 ms jusqu'au premier silence de 100 ms, dans le sens donné."""
    run, k = 0, 0
    while 0 <= i + sens * k < len(db) and k < int(RALLONGE_MAX / 0.02):
        run = run + 1 if db[i + sens * k] <= seuil else 0
        if run >= 5:
            return k - 4
        k += 1
    return None


def auditer(doc, workers=None):
    """Raccord fautif : la voix est présente dans les 60 ms avant et dans les 60 ms après la frontière.
    Une vraie fin de mot laisse un silence après ; le silence d'une consonne dure moins de 60 ms
    de part et d'autre. Détection acoustique déterministe, sans Whisper (horodatages trop flous)."""
    ch = doc['chunks']
    defauts = []
    for i, j in frontieres(doc):
        a, b = src(ch[i]), src(ch[j])
        ecart = b['start'] - a['end']
        if a['path'] == b['path'] and 0 < ecart <= CREUX_MAX:
            # Micro-creux retiré sur la même prise : s'il contient de la voix, il était dans un mot.
            db, seuil, c = profil(a['path'], a['end'])
            if voisee(db, seuil, c, c + max(2, int(ecart / 0.02))):
                defauts.append({'joint': [i, j], 'cote': 'creux', 'mot': '', 'source': a['path'],
                                'frontiere': round(a['end'], 3), 'mot_debut': round(a['end'], 3),
                                'mot_fin': round(b['start'], 3), 'restaurable': True})
                continue
        for cote, s, t, sens in (('fin', a, a['end'], +1), ('debut', b, b['start'], -1)):
            db, seuil, c = profil(s['path'], t)
            if not (voisee(db, seuil, c - 3, c) and voisee(db, seuil, c, c + 3)):
                continue
            k = jusqu_au_silence(db, seuil, c if sens > 0 else c - 1, sens)
            d = {'joint': [i, j], 'cote': cote, 'mot': '', 'source': s['path'], 'frontiere': round(t, 3),
                 'restaurable': k is not None}
            if k is not None:
                if sens > 0:
                    d['mot_debut'], d['mot_fin'] = round(t, 3), round(t + k * 0.02, 3)
                else:
                    d['mot_debut'], d['mot_fin'] = round(t - k * 0.02, 3), round(t, 3)
            defauts.append(d)
    return defauts


def decaler(c, cote, delta):
    for key in ('camera', 'audio'):
        if key in c:
            c[key][cote] += delta


def corriger(doc, defauts, speed, proteges=()):
    """Restaure les mots tranchés sur les raccords non protégés. Retourne (corrigés, listés)."""
    ch, fps = doc['chunks'], doc['fps']
    faits, listes = [], []
    for d in sorted(defauts, key=lambda d: d['joint']):
        i, j = d['joint']
        if tuple(d['joint']) in proteges or not d.get('restaurable', True):
            listes.append(d); continue
        if d['cote'] == 'creux':
            decaler(ch[i], 'end', src(ch[j])['start'] - src(ch[i])['end'])
        elif d['cote'] == 'fin':
            delta = d['mot_fin'] + 0.02 - src(ch[i])['end']
            if delta > 0:
                decaler(ch[i], 'end', delta)
                nxt = src(ch[j])
                if nxt['path'] == src(ch[i])['path'] and nxt['start'] < src(ch[i])['end'] < nxt['end']:
                    decaler(ch[j], 'start', src(ch[i])['end'] - nxt['start'])
        else:
            delta = src(ch[j])['start'] - (d['mot_debut'] - 0.02)
            if delta > 0:
                decaler(ch[j], 'start', -delta)
                prv = src(ch[i])
                if prv['path'] == src(ch[j])['path'] and prv['start'] < src(ch[j])['start'] < prv['end']:
                    decaler(ch[i], 'end', src(ch[j])['start'] - prv['end'])
        faits.append(d)
    for c in ch:
        s = src(c)
        c['frames'] = max(1, round((s['end'] - s['start']) * fps / speed))
    doc['total_frames'] = sum(c['frames'] for c in ch)
    return faits, listes


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('table', type=Path)
    p.add_argument('--out', type=Path)
    p.add_argument('--protege', type=Path, help='JSON : liste de joints [i, j] à ne jamais modifier.')
    p.add_argument('--speed', type=float, default=1.06)
    p.add_argument('--dry', action='store_true')
    p.add_argument('--no-open', action='store_true')
    a = p.parse_args()
    doc = json.loads(a.table.read_text())
    proteges = {tuple(x) for x in json.loads(a.protege.read_text())} if a.protege else set()
    defauts = auditer(doc)
    for d in defauts:
        print(f"  {d['cote']:5s} joint {d['joint']} frontière {d['frontiere']:.2f} -> "
              f"{d.get('mot_debut', '?')}-{d.get('mot_fin', '?')}{' (protégé)' if tuple(d['joint']) in proteges else ''}")
    print(f'Mots tranchés : {len(defauts)}')
    if a.dry or not defauts:
        return
    faits, listes = corriger(doc, defauts, a.speed, proteges)
    (a.out or a.table).write_text(json.dumps(doc, ensure_ascii=False, indent=2))
    print(f'Restaurés : {len(faits)} | listés (coupes de Lucien) : {len(listes)}')


if __name__ == '__main__':
    main()
