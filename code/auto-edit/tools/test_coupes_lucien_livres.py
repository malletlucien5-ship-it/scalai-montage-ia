#!/usr/bin/python3
"""Non-régression : les 7 coupes manuelles de Lucien sur le montage « Livres Claude ».

Entrées réelles du montage du 08/10/2026 (fixtures/coupes_lucien_livres) :
- v1.sources.json : table source de montage.mp4 (v1), 204 portions ;
- v1.protect.ancien-tail-guard.json : fins rallongées par l'ancien tail_guard (faux mots protégés) ;
- v1.protect.nouveau-tail-guard.json : mêmes fins rallongées par le tail_guard du 09/10/2026 ;
- obs.levels.cdb.npy : niveaux 10 ms de la voix OBS, en centièmes de dB ;
- phrases.mlx-turbo.json : transcription mlx-whisper de chaque phrase acoustique ;
- assemble.segments.json : transcription portion par portion utilisée au montage ;
- timeline-lucien.edl : timeline corrigée par Lucien sur la v2 (8 plages gardées) ;
- coupeN.flac : extraits audio courts autour de chaque coupe.

La v2 est la v1 moins les images de v1_to_v2.json. Les 7 trous de l'EDL sont les
coupes de Lucien. 3 sont des amorces : la relecture fine doit les proposer (±0,10 s
sur les bornes), sans aucune autre proposition sur la vidéo. 4 sont des pauses
laissées par les fausses rallonges de l'ancien tail_guard : le nouveau ne les
protège plus et quiet_cleanup les retire (test_livres_bout_en_bout.py).

  cd tools && /usr/bin/python3 -m unittest test_coupes_lucien_livres -v
  AUTO_EDIT_MLX_TESTS=1 … : retranscrit aussi les extraits audio avec mlx-whisper.
"""
import json
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

import numpy as np

import restart_detect as R

HERE = Path(__file__).resolve().parent
FIX = HERE / 'fixtures/coupes_lucien_livres'
MLX_PY = HERE.parent / '.venv-mlx/bin/python'
TOL = 0.10
FPS = 50
AMORCES = {1, 4, 6}       # coupes 2, 5 et 7 de l'EDL
PAUSES = (0, 2, 3, 5)     # coupes 1, 3, 4 et 6
QUIET_MIN = 0.13          # creux minimal retiré par quiet_cleanup


def edl_cuts(path, fps=FPS):
    """Trous entre les plages gardées de l'EDL (temps source v2, fin exclusive)."""
    def tc(s):
        h, m, sec, f = map(int, s.split(':'))
        return ((h * 60 + m) * 60 + sec) * fps + f
    kept = sorted({(tc(a), tc(b)) for a, b in re.findall(
        r'^\d+\s+\S+\s+V\s+C\s+(\S+)\s+(\S+)\s+\S+\s+\S+', path.read_text(), re.M)})
    return [(kept[i][1] / fps, kept[i + 1][0] / fps) for i in range(len(kept) - 1)]


def v1_to_v2(t):
    removed = json.loads((FIX / 'v1_to_v2.json').read_text())['v1_frames_removed']
    f = t * FPS
    return (f - sum(min(max(f - a, 0), b - a) for a, b in removed)) / FPS


def load_phrases():
    doc = json.loads((FIX / 'v1.sources.json').read_text())
    levels = np.load(FIX / 'obs.levels.cdb.npy') / 100.
    phrases = R.split_phrases(doc, lambda path: levels)
    rows = json.loads((FIX / 'phrases.mlx-turbo.json').read_text())
    segs = []
    for p in phrases:
        match = [r for r in rows if abs(r['clip'][0] - p['clip'][0]) < .02 and abs(r['clip'][1] - p['clip'][1]) < .02]
        if not match:
            raise AssertionError(f"Phrase {p['clip']} absente de la fixture : régénérer phrases.mlx-turbo.json")
        segs.append(match[0])
    return R.attach_text(phrases, segs)


def score(cuts, truth):
    """(coupes de Lucien trouvées, propositions hors coupes de Lucien, détail)."""
    found, false_pos, rows = set(), [], []
    for c in cuts:
        a, b = v1_to_v2(c['range'][0]), v1_to_v2(c['range'][1])
        hit = [k for k, (x, y) in enumerate(truth) if x < b and a < y]
        if not hit:
            false_pos.append((a, b, c['why'], c['text']))
            continue
        x, y = truth[hit[0]]
        if abs(a - x) <= TOL and abs(b - y) <= TOL:
            found.add(hit[0])
        rows.append((hit[0], a, b, c['why']))
    return found, false_pos, rows


class CoupesLucienLivres(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.truth = edl_cuts(FIX / 'timeline-lucien.edl')
        cls.phrases = load_phrases()
        cls.old_protect = json.loads((FIX / 'v1.protect.ancien-tail-guard.json').read_text())
        cls.new_protect = json.loads((FIX / 'v1.protect.nouveau-tail-guard.json').read_text())

    def test_edl_contient_sept_coupes(self):
        self.assertEqual(len(self.truth), 7)
        self.assertAlmostEqual(self.truth[0][0], 69.02)
        self.assertAlmostEqual(self.truth[-1][1], 506.20)

    def test_amorces_detectees_sans_faux_positif(self):
        cuts = R.fine_cuts(self.phrases)
        found, false_pos, rows = score(cuts, self.truth)
        print(f'\n  Amorces de Lucien détectées : {len(found)}/3 | faux positifs : {len(false_pos)}')
        for a, b, why, text in false_pos:
            print(f'    FP v2 {a:7.2f}-{b:7.2f} {why} | {text[:70]}')
        self.assertEqual(found, AMORCES, f'coupes manquées ou bornes hors ±{TOL}s : {rows}')
        self.assertEqual(false_pos, [])

    def test_cause_portion_entiere_fusionne_les_tentatives(self):
        """Transcrite en entier, la portion ne garde qu'une tentative : detect() ne voit rien."""
        segs = json.loads((FIX / 'assemble.segments.json').read_text())
        for src, start in ((447.6, 'il existe'), (1245.2, 'et tout le livre presente'),
                           (1346.5, 'parce que la ce n est pas')):
            seg = next(s for s in segs if s['audio']['start'] <= src <= s['audio']['end'])
            text = ' '.join(R.tokens(seg['text']))
            self.assertEqual(text.count(start), 1, seg['text'])
            self.assertNotIn(seg['index'], R.detect(segs))

    def test_cause_pause_protegee_par_tail_guard(self):
        """Les quatre coupes de pause tombent dans une fausse rallonge de l'ancien tail_guard."""
        spans = [(v1_to_v2(p['start']), v1_to_v2(p['end'])) for p in self.old_protect]
        for k in PAUSES:
            x, y = self.truth[k]
            self.assertTrue(any(a - TOL <= x and y <= b + TOL for a, b in spans), self.truth[k])

    def test_nouveau_tail_guard_libere_les_pauses(self):
        """Le nouveau tail_guard laisse au moins QUIET_MIN de silence non protégé dans chaque pause."""
        levels = np.load(FIX / 'obs.levels.cdb.npy') / 100.
        for k in PAUSES:
            x, y = self.truth[k]
            prot = [(v1_to_v2(p['start']), v1_to_v2(p['end'])) for p in self.new_protect
                    if v1_to_v2(p['start']) < y and x < v1_to_v2(p['end'])]
            free = (y - x) - sum(min(b, y) - max(a, x) for a, b in prot)
            self.assertGreaterEqual(free, QUIET_MIN - 0.02, (self.truth[k], prot))

    @unittest.skipUnless(os.environ.get('AUTO_EDIT_MLX_TESTS') and MLX_PY.exists(),
                         'AUTO_EDIT_MLX_TESTS=1 et .venv-mlx requis')
    def test_extraits_audio_retranscrits(self):
        """Retranscrire les phrases des extraits avec mlx-whisper : les amorces restent visibles."""
        extracts = json.loads((FIX / 'extraits.json').read_text())
        chunks, index = [], []
        for e in extracts:
            for i in range(e['phrases'][0], e['phrases'][1] + 1):
                p = self.phrases[i]
                src = {'path': str(FIX / e['file']), 'start': p['clip'][0] - e['start'],
                       'end': p['clip'][1] - e['start']}
                chunks.append({'audio': src, 'camera': dict(src), 'frames': 1})
                index.append(i)
        with tempfile.TemporaryDirectory() as tmp:
            table, out = Path(tmp) / 't.json', Path(tmp) / 'o.json'
            table.write_text(json.dumps({'fps': FPS, 'chunks': chunks}))
            subprocess.run([str(MLX_PY), str(HERE / 'segment_transcribe.py'), str(table), '--out', str(out),
                            '--pad', '0', '--no-open'], check=True, capture_output=True)
            segs = json.loads(out.read_text())
        # Les mots sont relatifs au début de chaque extrait : attach_text les replace en temps source.
        phrases = R.attach_text([dict(self.phrases[i]) for i in index], segs)
        found, false_pos, _ = score(R.fine_cuts(phrases), self.truth)
        self.assertEqual(found, AMORCES)
        self.assertEqual(false_pos, [])


class ReglesSynthetiques(unittest.TestCase):
    def phrase(self, out, text, words=None):
        run = {'pieces': [(0., 100., 0., 100.)]}
        return {'start': out[0], 'end': out[1], 'out': list(out), 'run': run, 'text': text,
                'words': words or [], 'clip': list(out)}

    def test_amorce_interne_coupee_jusqu_a_la_reprise(self):
        ph = [self.phrase((0, 2), 'au moment du besoin.', [{'word': 'besoin', 'start': 1.6, 'end': 1.9}]),
              self.phrase((2.3, 2.8), 'Il existe ?'),
              self.phrase((3.1, 5), 'Il existe même un skill gratuit.')]
        [c] = R.false_starts(ph)
        self.assertEqual(c['range'], [1.9, 3.08])

    def test_phrases_differentes_non_coupees(self):
        ph = [self.phrase((0, 1), 'Il existe un skill.'), self.phrase((1.3, 3), 'Il va tout lire.')]
        self.assertEqual(R.false_starts(ph), [])

if __name__ == '__main__':
    unittest.main()
