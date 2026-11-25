#!/usr/bin/python3
"""Rallonger les portions qui rognent un mot, à la fin comme au début.

La détection de silence tourne sur le micro caméra. Une syllabe faible passe
sous son seuil et la portion coupe le mot : « entrepri|se », « Schwar|tz »,
« pi|tch » après la fermeture du t, « |Ce que » au début. On relit la piste
audio maître autour de chaque coupe, par trames de 10 ms.

La mesure passe un passe-haut à 80 Hz, comme la chaîne vocale finale (65 Hz).
Sans lui, le grondement grave du micro OBS ressemble à de la voix.

Seuils, mesurés sur chaque fichier : fond = 10e centile, parole = 95e centile
des niveaux 50 ms.
- voix : parole - 24 dB (fond + 15 dB au minimum) ;
- silence : parole - 36 dB (fond + 6 dB au minimum) ;
- voyelle : parole - 10 dB.

Une coupe se corrige quand elle tombe dans un son (niveau au-dessus du silence
à ± 30 ms) : en pleine voix, ou avec au moins 30 ms de voix perdue derrière.
Le mot se termine après 150 ms sans voix : une occlusion de plosive
(« pi-tch », « éta-pe ») dure moins.
Une voyelle qui revient après 50 ms sans voix ouvre un autre mot : on s'arrête
avant, pour ne jamais faire entendre le début d'une reprise coupée.
On prolonge jusqu'au retour au silence (80 ms au plus après la dernière voix),
plus 40 ms de marge. Une voix qui continue au-delà de 0,4 s (fin) ou 0,3 s
(début) signale une phrase coupée volontairement : on n'y touche pas.
"""
import subprocess

import numpy as np

SR = 16000
WIN = 0.01
HIGHPASS = 'highpass=f=80,highpass=f=80'
VOICE_DB = 24
SILENCE_DB = 36
VOWEL_DB = 10
GAP = 0.15
NEW_WORD_GAP = 0.05
MAX_EXT = 0.4
MAX_LEAD = 0.3
MIN_LOST = 0.03
DECAY = 0.08
MARGIN = 0.04
EDGE = 0.05
_stats = {}


def _pcm(path, start, dur):
    r = subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-ss', f'{max(0., start):.4f}',
                        '-t', f'{dur:.4f}', '-i', path, '-vn', '-ac', '1', '-ar', str(SR),
                        '-af', HIGHPASS, '-f', 's16le', '-'], capture_output=True, check=True)
    return np.frombuffer(r.stdout, np.int16).astype(float) / 32768


def _levels(x, win=0.05):
    n = int(win * SR)
    return [20 * np.log10(np.sqrt(np.mean(x[i:i + n] ** 2)) + 1e-9)
            for i in range(0, len(x) - n + 1, n)]


def levels_db(path):
    """(fond, parole) du fichier : 10e et 95e centiles des niveaux 50 ms.

    Trois minutes échantillonnées. Un fichier court (extrait, test) est mesuré en entier.
    """
    if path not in _stats:
        levels = []
        for t in (30, 90, 150, 210, 270, 330):
            levels += _levels(_pcm(path, t, 30))
        if len(levels) < 200:
            levels = _levels(_pcm(path, 0, 600))
        _stats[path] = ((float(np.percentile(levels, 10)), float(np.percentile(levels, 95)))
                        if levels else (-70., -30.))
    return _stats[path]


def floor_db(path):
    return levels_db(path)[0]


def _thresholds(path):
    floor, speech = levels_db(path)
    return (max(floor + 15, speech - VOICE_DB), max(floor + 6, speech - SILENCE_DB),
            speech - VOWEL_DB)


def _profile(path, start, dur):
    """Niveaux en dB par trame de 10 ms."""
    x = _pcm(path, start, dur)
    n = int(WIN * SR)
    count = len(x) // n
    return 10 * np.log10((x[:count * n].reshape(count, n) ** 2).mean(1) + 1e-18)


def _cut_voice(levels, cut, step, limits, longest):
    """Secondes de voix coupée à partir de la trame `cut`, dans le sens `step`."""
    voice, silence, vowel = limits
    near = levels[max(0, cut - 3):cut + 3]
    if not len(near) or 10 * np.log10(np.mean(10 ** (near / 10))) <= silence:
        return 0.
    gap, new_word = round(GAP / WIN), round(NEW_WORD_GAP / WIN)
    last, lost, quiet = None, 0, 0
    span = round(longest / WIN)
    for j in range(span + gap):
        i = cut + j if step > 0 else cut - 1 - j
        if not 0 <= i < len(levels):
            return 0.
        if levels[i] > voice:
            # Voyelle après un vrai blanc : un autre mot commence.
            if quiet >= new_word and levels[i] > vowel:
                break
            last, lost, quiet = j, lost + 1, 0
        else:
            quiet += 1
            if quiet >= gap:
                break
    else:
        return 0.
    if last is None or (last + 1) * WIN > longest + 1e-9:
        return 0.
    # Coupe en pleine voix : on la termine. Sinon, au moins 30 ms de voix perdue (pas un clic).
    first = levels[cut] if step > 0 else levels[cut - 1]
    if first <= voice and lost * WIN < MIN_LOST - 1e-9:
        return 0.
    end = last + 1
    while end - last - 1 < round(DECAY / WIN):
        i = cut + end if step > 0 else cut - 1 - end
        if not 0 <= i < len(levels) or levels[i] <= silence:
            break
        end += 1
    return end * WIN


def extension(path, end):
    """Secondes de voix restantes après `end`, 0 si rien à rallonger."""
    look = MAX_EXT + GAP + DECAY + 2 * EDGE
    levels = _profile(path, end - EDGE, look)
    return _cut_voice(levels, round(EDGE / WIN), 1, _thresholds(path), MAX_EXT)


def lead(path, start):
    """Secondes de voix coupées avant `start`, 0 si rien à avancer."""
    look = MAX_LEAD + GAP + DECAY + 2 * EDGE
    begin = max(0., start - look + EDGE)
    levels = _profile(path, begin, start + EDGE - begin)
    return _cut_voice(levels, round((start - begin) / WIN), -1, _thresholds(path), MAX_LEAD)


def _src(c):
    return c.get('audio') or c['camera']


def _grow(c, add, real, side):
    for key in ('camera', 'audio', 'screen'):
        if c.get(key):
            if side == 'fin':
                c[key]['end'] += real
            else:
                c[key]['start'] -= real
    c['frames'] += add
    key = 'tail_guard_frames' if side == 'fin' else 'head_guard_frames'
    c[key] = c.get(key, 0) + add


def extend_tails(doc, speed, eligible=None):
    """Rallonger en place les fins et les débuts rognés.

    `eligible(chunk)` filtre les fins à examiner (reprise Resolve). Avec un filtre,
    les débuts restent intacts : seuls les raccords automatiques sont corrigés.
    """
    fps = doc['fps']
    chunks = doc['chunks']
    fixed = []

    def contiguous(a, b):
        return b['path'] == a['path'] and abs(b['start'] - a['end']) < 0.02

    for k, c in enumerate(chunks):
        a = _src(c)
        nxt = chunks[k + 1] if k + 1 < len(chunks) else None
        b = _src(nxt) if nxt else None
        if b and contiguous(a, b):
            continue
        if eligible and not eligible(c):
            continue
        ext = extension(a['path'], a['end'])
        if not ext:
            continue
        # Ne jamais rejouer l'audio de la portion suivante dans le même fichier.
        if b and b['path'] == a['path'] and b['start'] > a['end']:
            ext = min(ext + MARGIN, b['start'] - a['end'] - 0.02)
        else:
            ext += MARGIN
        add = round(ext * fps / speed)
        if add <= 0:
            continue
        real = add * speed / fps
        _grow(c, add, real, 'fin')
        fixed.append({'side': 'fin', 'path': a['path'], 'end': round(a['end'] - real, 3),
                      'added': round(real, 3)})

    for k, c in enumerate(chunks):
        if eligible:
            break
        a = _src(c)
        prev = _src(chunks[k - 1]) if k else None
        if prev and contiguous(prev, a):
            continue
        ext = lead(a['path'], a['start'])
        if not ext:
            continue
        ext += MARGIN
        # Ni rejouer la fin de la portion précédente, ni sortir du fichier.
        if prev and prev['path'] == a['path'] and prev['end'] < a['start']:
            ext = min(ext, a['start'] - prev['end'] - 0.02)
        ext = min([ext] + [c[key]['start'] for key in ('camera', 'audio', 'screen') if c.get(key)])
        add = int(ext * fps / speed + 1e-9)
        if add <= 0:
            continue
        real = add * speed / fps
        _grow(c, add, real, 'debut')
        fixed.append({'side': 'debut', 'path': a['path'], 'start': round(a['start'] + real, 3),
                      'added': round(real, 3)})
    if 'total_frames' in doc:
        doc['total_frames'] = sum(c['frames'] for c in chunks)
    return fixed


def _span_words(start, end):
    """Faux mots de 40 ms bout à bout : l'audit des creux protège le centre de chaque mot ± 25 ms,
    donc toute la portion rallongée reste intacte (occlusion de plosive comprise)."""
    out, t = [], start
    while t < end - 1e-9:
        out.append({'word': '', 'start': t, 'end': min(end, t + 0.04)})
        t += 0.04
    return out


def protected_words(doc):
    """Faux mots sur les bords rallongés : l'audit des creux ne doit pas les retirer.

    La marque des débuts (`head_guard_frames`) est consommée ici et ne reste pas dans la table.
    """
    out, pos = [], 0
    fps = doc['fps']
    for c in doc['chunks']:
        head = c.pop('head_guard_frames', None)
        if head:
            out += _span_words(pos / fps, (pos + head) / fps)
        pos += c['frames']
        add = c.get('tail_guard_frames')
        if add:
            out += _span_words((pos - add) / fps, pos / fps)
    return out
