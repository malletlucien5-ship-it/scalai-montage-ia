#!/usr/bin/python3
"""Bout en bout « Livres Claude » : `pipeline.py assemble --dry` contre la cible de Lucien.

Cible, en temps source OBS :
  v2 (v1 moins les images de l'audit des creux)
  moins les 7 coupes de Lucien (timeline-lucien.edl)
  plus les fins de mots rognées (fins-de-mots/extensions.json, copie en fixture).

On compare la parole gardée : différence symétrique des plages source gardées,
découpée en écarts. Un écart de plus de 0,10 s est rapporté. Il compte comme
écart de parole quand il contient au moins 30 ms de voix (RMS 10 ms brut > −50 dB :
le corps des mots est entre −30 et −45 dB, −50 dB est le bas d'une décroissance).

Par défaut, le test compare la table --dry produite le 09/10/2026 (fixture
dry.sources.json). Avec AUTO_EDIT_E2E=1, il relance l'assemblage --dry sur une
copie légère du dossier de montage dans un dossier temporaire (environ 20 min,
transcriptions mlx, aucun encodage vidéo), puis compare la nouvelle table.

  cd tools && /usr/bin/python3 -m unittest test_livres_bout_en_bout -v
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

from test_coupes_lucien_livres import FIX, FPS, edl_cuts

HERE = Path(__file__).resolve().parent
MONTAGE = Path('/Users/lucienmallet/Desktop/montage-2026-10-08-livres')
TOL = 0.10
MIN_VOICE = 0.03
MAX_SILENCE_GAPS = 8
VOICE_DB = -50.


def union(intervals):
    out = []
    for a, b in sorted(intervals):
        if out and a <= out[-1][1] + 1e-6:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return out


def target_intervals():
    """Plages source OBS gardées par la cible."""
    doc = json.loads((FIX / 'v1.sources.json').read_text())
    removed = [list(r) for r in json.loads((FIX / 'v1_to_v2.json').read_text())['v1_frames_removed']]
    # Coupes de Lucien : temps v2 → images v1.
    def v2_to_v1(t):
        f = round(t * FPS)
        for a, b in sorted(removed):
            if f >= a:
                f += b - a
        return f
    drop = removed + [[v2_to_v1(a), v2_to_v1(b)] for a, b in edl_cuts(FIX / 'timeline-lucien.edl')]
    ext = json.loads((FIX / 'extensions.json').read_text())['cas']
    pieces, pos = [], 0
    for k, c in enumerate(doc['chunks']):
        a0, b0 = pos, pos + c['frames']
        src = c['audio']
        dt = (src['end'] - src['start']) / c['frames']
        keep = [[a0, b0]]
        for x, y in drop:
            keep = [p for q in keep for p in ([[q[0], min(q[1], x)]] if q[0] < x else []) +
                    ([[max(q[0], y), q[1]]] if y < q[1] else [])] if x < b0 and a0 < y else keep
        for x, y in keep:
            s, e = src['start'] + dt * (x - a0), src['start'] + dt * (y - a0)
            for cas in ext:
                if cas['chunk'] != k:
                    continue
                if cas['cote'] == 'fin' and y == b0:
                    e += cas['ajout_s']
                if cas['cote'] == 'debut' and x == a0:
                    s -= cas['ajout_s']
            pieces.append([s, e])
        pos = b0
    return union(pieces)


def table_intervals(doc):
    return union([[c['audio']['start'], c['audio']['end']] for c in doc['chunks']])


def difference(a, b):
    """Plages de `a` absentes de `b` (deux listes triées, disjointes)."""
    out = []
    for s, e in a:
        cur = s
        for x, y in b:
            if y <= cur or x >= e:
                continue
            if x > cur:
                out.append([cur, x])
            cur = max(cur, y)
        if cur < e:
            out.append([cur, e])
    return out


def compare(dry, target, levels):
    """Écarts > TOL : (côté, début, fin, voix_s). côté = « en trop » ou « manquant » dans --dry."""
    rows = []
    for side, regions in (('en trop', difference(dry, target)), ('manquant', difference(target, dry))):
        for s, e in regions:
            if e - s <= TOL:
                continue
            voice = float((levels[int(round(s * 100)):int(round(e * 100))] > VOICE_DB).sum()) / 100
            rows.append((side, round(s, 3), round(e, 3), voice))
    return sorted(rows, key=lambda r: r[1])


def light_copy(src, dst):
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns(
        '*.mp4', '*.wav', '*.m4a', 'clips', 'scrframes', 'audio-chunks', 'sheets'))


class BoutEnBoutLivres(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.levels = np.load(FIX / 'obs.levels.cdb.npy') / 100.
        cls.target = target_intervals()

    def check(self, doc, label):
        rows = compare(table_intervals(doc), self.target, self.levels)
        speech = [r for r in rows if r[3] >= MIN_VOICE]
        print(f'\n  {label} : {len(rows)} écart(s) > {TOL}s, dont {len(speech)} avec de la voix')
        for side, s, e, voice in rows:
            print(f'    {side:8s} source {s:8.3f}-{e:8.3f} ({e - s:.2f}s, voix {voice:.2f}s)')
        self.assertEqual(speech, [], 'parole gardée différente de la cible')
        # Mesure du 09/10/2026 : 8 écarts de silence (6 pauses gardées par Lucien et
        # resserrées par quiet_cleanup, 1 décroissance de 0,107 s, 1 creux de 0,13 s).
        self.assertLessEqual(len(rows), MAX_SILENCE_GAPS)
        return rows

    def test_cible_contient_les_fins_de_mots(self):
        kept = self.target
        inside = lambda t: any(a <= t <= b for a, b in kept)
        self.assertTrue(inside(55.219 + 0.25))          # « entreprise » rallongé
        self.assertFalse(inside(447.5))                 # « Il existe ? » coupé
        self.assertFalse(inside(1346.5))                # « …c'est pas comme » coupé

    def test_table_dry_fixture(self):
        self.check(json.loads((FIX / 'dry.sources.json').read_text()), 'table --dry du 09/10/2026')

    @unittest.skipUnless(os.environ.get('AUTO_EDIT_E2E') and MONTAGE.exists(),
                         'AUTO_EDIT_E2E=1 et le dossier de montage requis')
    def test_assemblage_dry_relance(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'montage'
            light_copy(MONTAGE, out)
            subprocess.run([sys.executable, str(HERE / 'pipeline.py'), 'assemble', '--out', str(out),
                            '--dry', '--no-open'], check=True, capture_output=True)
            doc = json.loads((out / 'work/montage.dry.sources.json').read_text())
        self.check(doc, 'assemblage --dry relancé')


if __name__ == '__main__':
    unittest.main()
