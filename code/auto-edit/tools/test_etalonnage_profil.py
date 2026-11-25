"""Le look choisi pour une vidéo (Studio A seul) survit à bases() et n'est pas recollé par grades()."""
import json, tempfile, unittest
from pathlib import Path
import etalonnage

LUT = 'lut3d=file=/chemin/Studio_VSL_A.cube'


class TestProfil(unittest.TestCase):
    def test_studio_a_seul_conserve(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'etalonnage.json'
            cam = str(Path(d, 'DJI.MP4').resolve())
            p.write_text(json.dumps({'look_a': 'null', 'bases': {cam: LUT}, 'mesures': {}}))
            etalonnage.bases(d, [cam])  # rush déjà présent : aucune mesure, look conservé
            self.assertEqual(json.loads(p.read_text())['look_a'], 'null')
            self.assertEqual(etalonnage.grades(d), {cam: LUT})

    def test_look_a_par_defaut(self):
        with tempfile.TemporaryDirectory() as d:
            cam = str(Path(d, 'DJI.MP4').resolve())
            Path(d, 'etalonnage.json').write_text(json.dumps({'bases': {cam: 'base'}, 'mesures': {}}))
            self.assertEqual(etalonnage.grades(d), {cam: 'base,' + etalonnage.LOOK_A})


if __name__ == '__main__':
    unittest.main()
