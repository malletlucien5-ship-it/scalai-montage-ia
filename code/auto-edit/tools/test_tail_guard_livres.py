"""Non-régression tail_guard sur les mots coupés du montage « Livres Claude » (08/10/2026).

Extraits OBS réels de 3 s, coupe à 1,5 s. Le fond et le niveau de parole viennent
du fichier OBS complet (fixtures/tail_guard_livres/cases.json).
"""
import json
import unittest
from pathlib import Path

import numpy as np

import tail_guard
from quiet_cleanup import find_quiet_cuts

HERE = Path(__file__).resolve().parent
FIX = HERE / 'fixtures' / 'tail_guard_livres'
SPEC = json.loads((FIX / 'cases.json').read_text())
CUT = 1.5


def path(case):
    p = str(FIX / case['fichier'])
    stats = SPEC['stats_source']
    if hasattr(tail_guard, '_stats'):
        tail_guard._stats[p] = (stats['fond_db'], stats['parole_db'])
    else:
        # Version d'avant le 09/10/2026 : fond brut seul, pour rejouer son comportement.
        tail_guard._floors[p] = stats['fond_brut_ancien_db']
    return p


def measure(case):
    if case['cote'] == 'fin':
        return tail_guard.extension(path(case), CUT)
    return tail_guard.lead(path(case), CUT)


class TailGuardLivresTests(unittest.TestCase):
    def test_mots_coupes_retrouves(self):
        for case in SPEC['cas']:
            if not case['doit_atteindre']:
                continue
            with self.subTest(mot=case['mot'], cote=case['cote']):
                limit = tail_guard.MAX_EXT if case['cote'] == 'fin' else getattr(tail_guard, 'MAX_LEAD', 0)
                got = measure(case)
                self.assertGreaterEqual(got, case['doit_atteindre'] - 1e-9, case['note'])
                self.assertLessEqual(got, limit + 1e-9)

    def test_aucun_faux_positif(self):
        for case in SPEC['cas']:
            if case['doit_atteindre']:
                continue
            with self.subTest(mot=case['mot'], cote=case['cote']):
                self.assertEqual(measure(case), 0., case['note'])

    def chunk(self, name, start, end, speed=1.06, fps=50.):
        p = path({'fichier': name})
        frames = round((end - start) * fps / speed)
        return {'layout': 'face', 'frames': frames,
                'audio': {'path': p, 'start': start, 'end': end},
                'camera': {'path': '/cam.mp4', 'start': start + 10, 'end': end + 10}}

    def test_table_rallonge_fin_et_debut(self):
        speed, fps = 1.06, 50.
        doc = {'fps': fps, 'chunks': [self.chunk('entreprise.wav', .2, CUT),
                                      self.chunk('ce-que.wav', CUT, 2.8)]}
        before = [dict(c, audio=dict(c['audio']), camera=dict(c['camera'])) for c in doc['chunks']]
        fixed = tail_guard.extend_tails(doc, speed)
        self.assertEqual(sorted(f['side'] for f in fixed), ['debut', 'fin'])
        fin, debut = doc['chunks']
        self.assertGreaterEqual(fin['audio']['end'] - CUT, .18)
        self.assertGreaterEqual(CUT - debut['audio']['start'], .07)
        for c, old in zip(doc['chunks'], before):
            grown = (c['audio']['end'] - c['audio']['start']) - (old['audio']['end'] - old['audio']['start'])
            self.assertAlmostEqual(grown, (c['frames'] - old['frames']) * speed / fps, places=6)
            self.assertAlmostEqual(c['camera']['start'] - c['audio']['start'],
                                   old['camera']['start'] - old['audio']['start'], places=6)
        tail, head = fin['tail_guard_frames'], debut['head_guard_frames']
        words = tail_guard.protected_words(doc)
        self.assertNotIn('head_guard_frames', debut)

        def covered(a, b):
            return all(any(w['start'] <= t <= w['end'] for w in words) for t in np.arange(a, b, .01))
        self.assertTrue(covered((fin['frames'] - tail) / fps, fin['frames'] / fps))
        self.assertTrue(covered(fin['frames'] / fps, (fin['frames'] + head) / fps))

    def test_creux_ne_retire_rien_dans_une_rallonge(self):
        # Rallonge de 0,4 s en fin de portion : l'occlusion de 140 ms à son début reste.
        doc = {'fps': 50., 'chunks': [{'frames': 100, 'tail_guard_frames': 20}]}
        words = tail_guard.protected_words(doc)
        audio = np.full(40000, .1)
        audio[round(1.60 * 16000):round(1.74 * 16000)] = 0
        self.assertTrue(find_quiet_cuts(audio, 16000, [], fps=50))
        self.assertEqual(find_quiet_cuts(audio, 16000, words, fps=50), [])


if __name__ == '__main__':
    unittest.main()
