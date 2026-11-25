#!/usr/bin/python3
"""Repérer les amorces ratées à partir d'une transcription portion par portion.

Règle apprise sur les coupes Resolve de Lucien (montage du 17/09/2026) :
une portion est une amorce ratée quand une des portions suivantes recommence
par les mêmes mots. On coupe alors l'amorce et tout ce qui la sépare de la
reprise. On garde toujours la dernière tentative.
Une portion sans aucun mot (souffle, bruit transcrit « ... ») est coupée aussi.

Relecture fine (coupes de Lucien, montage « Livres Claude », 09/10/2026) :
split_phrases découpe chaque portion en phrases acoustiques, transcrites une à une.
false_starts coupe une amorce reprise dans la même portion.
pipeline.py l'applique à l'assemblage (fine_review) et aux reprises du plan.
Les pauses coupées par Lucien venaient des fausses rallonges de l'ancien tail_guard :
le tail_guard du 09/10/2026 ne les crée plus et quiet_cleanup retire le silence.

  restart_detect.py segments.text.json --out restarts.json [--labels labels.json]
"""
import argparse
import difflib
import json
import re
import unicodedata
from pathlib import Path

LOOKAHEAD = 6          # portions examinées après l'amorce
MAX_GAP = 30.0         # secondes source maximum entre amorce et reprise
CONNECTORS = {'donc', 'et', 'alors', 'mais', 'bon', 'ok', 'okay', 'puis', 'hey', 'euh'}
# Apartés de tournage : « Ok, là, je reprends », « autant pour moi », « je continue ».
ASIDES = re.compile(r'\b(je reprends|on reprends?|autant pour moi|je recommence|on recommence|'
                    r'je (la |le )?refais|je continue|on continue|c est pas bon|attends)\b')


def tokens(text):
    t = unicodedata.normalize('NFKD', text.lower())
    t = ''.join(c for c in t if not unicodedata.combining(c))
    t = t.replace("'", ' ').replace('’', ' ').replace('-', ' ')
    return re.findall(r'[a-z0-9%]+', t)


def same(a, b):
    """Deux mots identiques, ou un mot coupé en cours de route (« agis » / « agir »)."""
    if a == b:
        return True
    n = min(len(a), len(b))
    return n >= 4 and a[:n - 1] == b[:n - 1]


def prefix_len(a, b):
    n = 0
    for x, y in zip(a, b):
        if not same(x, y):
            break
        n += 1
    return n


def strip(t):
    while len(t) > 1 and t[0] in CONNECTORS:
        t = t[1:]
    return t


def is_restart(a, b, text_a):
    """a : mots de l'amorce, b : mots de la tentative suivante."""
    if not a or not b:
        return False, ''
    a, b = strip(a), strip(b)
    p = prefix_len(a, b)
    frac = p / len(a)
    unfinished = text_a.rstrip().endswith(('...', '…'))
    if p == len(a) and len(a) < len(b) + 1:
        return True, f'amorce reprise en entier ({p} mots)'
    if frac >= 0.8:
        return True, f'début identique {p}/{len(a)}'
    if len(a) <= 4 and p >= 2:
        return True, f'fragment court {p}/{len(a)}'
    if unfinished and p >= 2:
        return True, f'phrase inachevée, début identique {p}/{len(a)}'
    # Même fin de phrase, début mal entendu : « ces skills sont comme… » / « c'est ce qu'ils sont… ».
    suffix = 0
    for x, y in zip(reversed(a), reversed(b)):
        if not same(x, y):
            break
        suffix += 1
    common = sum(m.size for m in difflib.SequenceMatcher(None, a, b, autojunk=False).get_matching_blocks())
    if suffix >= 3 and common / len(a) >= 0.6 and len(b) <= len(a) + 6:
        return True, f'même fin de phrase ({suffix} mots), reprise'
    ratio = difflib.SequenceMatcher(None, a, b[:len(a) + 2]).ratio()
    if ratio >= 0.7 and len(a) >= 4:
        return True, f'même phrase transcrite autrement ({ratio:.2f})'
    return False, ''


def detect(segs):
    toks = [tokens(s['text']) for s in segs]
    cut = {}
    for i, s in enumerate(segs):
        if not toks[i]:
            cut[i] = 'aucun mot (souffle ou bruit)'
            continue
        if len(toks[i]) <= 6 and ASIDES.search(' '.join(toks[i])):
            cut[i] = 'aparté de tournage'
            continue
        for j in range(i + 1, min(len(segs), i + 1 + LOOKAHEAD)):
            same_take = segs[j]['camera']['path'] == s['camera']['path']
            gap = segs[j]['camera']['start'] - s['camera']['end'] if same_take else 0.
            if gap > MAX_GAP:
                break
            ok, why = is_restart(toks[i], toks[j], s['text'])
            if ok:
                cut.setdefault(i, why)
                # Une portion intermédiaire ne part que si elle est redite après la reprise.
                # Sans ce contrôle, une phrase dite une seule fois disparaissait (AI Advantage,
                # 09/10/2026 : « Vous pouvez gagner plus d'argent, agrandir votre équipe »).
                after = [w for m in range(j, min(len(segs), j + 1 + LOOKAHEAD)) for w in toks[m]]
                for k in range(i + 1, j):
                    if superseded(toks[k], after) or len(toks[k]) <= 2:
                        cut.setdefault(k, f'entre l’amorce {i} et sa reprise {j}')
                break
    return cut


def superseded(words, after, share=0.6):
    """Les mots de la portion reviennent, dans l'ordre, dans ce qui suit la reprise."""
    if not words:
        return True
    common = sum(m.size for m in difflib.SequenceMatcher(None, words, after, autojunk=False).get_matching_blocks())
    return common / len(words) >= share


def phrase_repeats(words, n=5, window=30):
    """Répétitions dans un même passage : n mots identiques repris dans les `window` mots suivants.

    Retourne des plages [début de la 1re tentative, début de la dernière] en secondes.
    """
    toks = [(tokens(w['word']) or [''])[0] for w in words]
    out = []
    i = 0
    while i + n <= len(toks):
        gram = toks[i:i + n]
        if '' in gram:
            i += 1
            continue
        last = None
        for j in range(i + 1, min(len(toks) - n + 1, i + window)):
            if toks[j:j + n] == gram:
                last = j
        if last is not None and words[last]['start'] - words[i]['start'] < 20:
            out.append([words[i]['start'], words[last]['start']])
            i = last
        else:
            i += 1
    return out


# ─── Relecture fine par phrase acoustique ─────────────────────────────────────
# Règles apprises sur les coupes de Lucien du montage « Livres Claude » (09/10/2026).
# Une portion peut contenir deux tentatives séparées par un court silence
# (« Il existe… / Il existe même un skill »). Whisper les fusionne quand il
# transcrit la portion entière. On découpe donc chaque portion en phrases
# acoustiques et on transcrit chaque phrase seule.
QUIET_DB = -55.0      # seuil de silence de quiet_cleanup (RMS sur 10 ms)
PHRASE_PAUSE = 0.12   # s de sortie : un creux plus long sépare deux phrases
MIN_ISLAND = 0.06     # s source : un îlot de voix plus court est un clic
PHRASE_PAD = 0.06     # s de marge de transcription, bornée au milieu du creux voisin
RESTART_GAP = 1.5     # s de sortie au plus entre l'amorce et sa reprise
EDGE = 0.02           # s gardées avant la reprise ou la phrase suivante


def levels_db(pcm, sample_rate=16000):
    """Niveau RMS en dB par bloc de 10 ms."""
    import numpy as np
    block = sample_rate // 100
    n = len(pcm) // block
    x = np.asarray(pcm[:n * block], dtype=np.float64).reshape(n, block)
    return 20 * np.log10(np.sqrt((x * x).mean(axis=1)) + 1e-9)


_LEVELS = {}


def source_levels(path):
    """Niveaux 10 ms du fichier audio maître entier (mono 16 kHz), mis en cache."""
    import subprocess
    import numpy as np
    if path not in _LEVELS:
        raw = subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-i', str(path), '-vn', '-ac', '1',
                              '-ar', '16000', '-f', 's16le', '-'], capture_output=True, check=True).stdout
        _LEVELS[path] = levels_db(np.frombuffer(raw, np.int16).astype(np.float64) / 32768)
    return _LEVELS[path]


def source_runs(doc):
    """Portions consécutives et continues dans la source, avec leur position de sortie."""
    fps, runs, pos = doc['fps'], [], 0
    for c in doc['chunks']:
        src = c.get('audio') or c['camera']
        piece = (pos / fps, (pos + c['frames']) / fps, src['start'], src['end'])
        last = runs[-1] if runs else None
        if last and last['path'] == src['path'] and abs(src['start'] - last['pieces'][-1][3]) < .02:
            last['pieces'].append(piece)
        else:
            runs.append({'path': src['path'], 'pieces': [piece]})
        pos += c['frames']
    return runs


def to_output(run, t):
    """Temps source → temps de sortie (s), borné à la portion."""
    for o0, o1, s0, s1 in run['pieces']:
        if t <= s1 + 1e-6 or (o0, o1, s0, s1) == run['pieces'][-1]:
            t = min(max(t, s0), s1)
            return o0 + (o1 - o0) * (t - s0) / max(s1 - s0, 1e-9)


def split_phrases(doc, level=source_levels):
    """Phrases acoustiques dans l'ordre de sortie.

    Une phrase est un passage de voix (> QUIET_DB) sans creux de plus de
    PHRASE_PAUSE secondes de sortie. Chaque phrase porte ses bornes source
    (`start`, `end`), l'extrait à transcrire (`clip`) et ses bornes de sortie (`out`).
    """
    import numpy as np
    phrases = []
    for run in source_runs(doc):
        db = level(run['path'])
        first, last = run['pieces'][0], run['pieces'][-1]
        s0, s1 = first[2], last[3]
        speed = (s1 - s0) / max(last[1] - first[0], 1e-9)
        i0 = int(round(s0 * 100))
        voiced = db[i0:int(round(s1 * 100))] > QUIET_DB
        edges = np.flatnonzero(np.diff(np.r_[False, voiced, False])).reshape(-1, 2)
        islands = []
        for a, b in edges:
            if (b - a) / 100 < MIN_ISLAND:
                continue
            if islands and (a - islands[-1][1]) / 100 < PHRASE_PAUSE * speed:
                islands[-1][1] = b
            else:
                islands.append([a, b])
        for k, (a, b) in enumerate(islands):
            start, end = (i0 + a) / 100, (i0 + b) / 100
            lo = s0 if k == 0 else (end_prev + start) / 2
            hi = s1 if k == len(islands) - 1 else (end + (i0 + islands[k + 1][0]) / 100) / 2
            end_prev = end
            phrases.append({'path': run['path'], 'start': start, 'end': end,
                            'clip': [max(lo, start - PHRASE_PAD), min(hi, end + PHRASE_PAD)],
                            'out': [to_output(run, start), to_output(run, end)], 'run': run})
    return phrases


def output_to_source(doc, t, key='camera'):
    """Temps de sortie (s) → (chemin, temps source) pour la piste `key` d'une table source."""
    fps, pos = doc['fps'], 0
    for c in doc['chunks']:
        a, b = pos / fps, (pos + c['frames']) / fps
        if t < b or c is doc['chunks'][-1]:
            src = c.get(key) or c['camera']
            x = min(max(t, a), b)
            return src['path'], src['start'] + (src['end'] - src['start']) * (x - a) / max(b - a, 1e-9)
        pos += c['frames']


def phrase_table(phrases, fps=50):
    """Table source minimale pour segment_transcribe.py (un extrait par phrase, --pad 0)."""
    chunks = []
    for p in phrases:
        src = {'path': p['path'], 'start': p['clip'][0], 'end': p['clip'][1]}
        chunks.append({'audio': src, 'camera': dict(src), 'frames': 1})
    return {'fps': fps, 'chunks': chunks}


def attach_text(phrases, segs):
    """Ajouter texte et mots (temps source absolus) de la transcription des extraits."""
    for p, s in zip(phrases, segs):
        p['text'] = s.get('text', '')
        p['words'] = [{**w, 'start': p['clip'][0] + w['start'], 'end': p['clip'][0] + w['end']}
                      for w in s.get('words', []) if tokens(w['word'])]
    return phrases


def speech_end(p):
    """Fin de la voix utile d'une phrase, en temps de sortie.

    Whisper place la fin du dernier mot là où l'oreille l'entend finir. Le souffle
    ou la résonance qui suit dépasse souvent le seuil de silence. On retient donc
    la fin du dernier mot quand elle tombe dans la phrase, sinon la fin acoustique.
    """
    end = p['end']
    if p.get('words'):
        w = p['words'][-1]['end']
        if p['start'] < w < end:
            end = w
    return to_output(p['run'], end)


def false_starts(phrases):
    """Amorces ratées à l'intérieur d'une portion ou entre deux portions voisines.

    A est une amorce quand la phrase suivante B la reprend (is_restart).
    On coupe de la fin de la voix de la phrase qui précède A jusqu'au début de B :
    l'amorce part avec sa pause. On garde toujours la dernière tentative.
    """
    toks = [tokens(p.get('text', '')) for p in phrases]
    cuts = []
    for i in range(len(phrases) - 1):
        a, b = phrases[i], phrases[i + 1]
        if not toks[i] or not toks[i + 1] or b['out'][0] - a['out'][1] > RESTART_GAP:
            continue
        ok, why = is_restart(toks[i], toks[i + 1], a['text'])
        if not ok:
            continue
        prev = phrases[i - 1] if i else None
        start = a['out'][0] - EDGE
        if prev and a['out'][0] - prev['out'][1] <= RESTART_GAP:
            start = speech_end(prev)
        cuts.append({'range': [start, b['out'][0] - EDGE], 'why': f'amorce dans la phrase, {why}',
                     'text': f"{a['text']} → {b['text']}"})
    return cuts


def fine_cuts(phrases):
    """Coupes de la relecture fine, fusionnées, en secondes de sortie."""
    return merge_cuts(false_starts(phrases))


def merge_cuts(cuts, join=.05):
    """Fusionner les coupes qui se touchent (pause + amorce qui suit, par exemple)."""
    out = []
    for c in sorted(cuts, key=lambda c: c['range'][0]):
        if out and c['range'][0] <= out[-1]['range'][1] + join:
            last = out[-1]
            last['range'][1] = max(last['range'][1], c['range'][1])
            last['why'] += ' + ' + c['why']
            last['text'] += ' | ' + c['text']
        else:
            out.append({**c, 'range': list(c['range'])})
    return out


def kept_frames(total, cuts, fps):
    """Intervalles d'images gardés une fois les coupes (secondes de sortie) retirées."""
    kept, cursor = [], 0
    for c in merge_cuts(cuts):
        a, b = max(0, round(c['range'][0] * fps)), min(total, round(c['range'][1] * fps))
        if b - a < 2:
            continue
        if a > cursor:
            kept.append([cursor, a])
        cursor = max(cursor, b)
    if cursor < total:
        kept.append([cursor, total])
    return kept


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('segments', type=Path)
    p.add_argument('--out', required=True, type=Path)
    p.add_argument('--labels', type=Path, help='[[index, part_coupée, ...]] pour mesurer')
    p.add_argument('--no-open', action='store_true')
    a = p.parse_args()
    segs = json.loads(a.segments.read_text())
    cut = detect(segs)
    rows = [{'index': i, 'why': w, 'text': segs[i]['text'], 'camera': segs[i]['camera'],
             'audio': segs[i]['audio']} for i, w in sorted(cut.items())]
    a.out.write_text(json.dumps(rows, ensure_ascii=False, indent=1))
    print(f'{len(rows)} portions à couper.')
    if a.labels:
        labels = {r[0]: r[1] for r in json.loads(a.labels.read_text())}
        truth = {i for i, r in labels.items() if r > .7}
        pred = set(cut)
        tp, fp, fn = truth & pred, pred - truth, truth - pred
        print(f'Coupes Lucien : {len(truth)} | détectées : {len(tp)} | '
              f'en trop : {len(fp)} | manquées : {len(fn)}')
        for tag, ids in (('EN TROP', fp), ('MANQUÉE', fn)):
            for i in sorted(ids):
                print(f'  {tag:8s} {i:3d} {cut.get(i, ""):45s} {segs[i]["text"][:80]}'
                      f'  →  {segs[i + 1]["text"][:60] if i + 1 < len(segs) else ""}')


if __name__ == '__main__':
    main()
