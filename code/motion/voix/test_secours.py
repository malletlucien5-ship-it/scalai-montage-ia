"""Son caméra de secours : il ne remplit que ce que l'OBS ne couvre pas.

Incidents I5 et I6 (03/10, video-gpt-new) : faux départs 0023 et 0024 sans OBS,
fin de 0026 et 0027 après l'OBS. Sans réseau, sans S3, sans média : seule numpy est requise.

  python -m pytest -q voix/test_secours.py
  python -m unittest discover -s voix -p test_secours.py
"""
import sys
import tempfile
import unittest
from fractions import Fraction
from pathlib import Path
from unittest import mock

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ameliorer_voix as av  # noqa: E402
import synchro  # noqa: E402

OBS = "2026-10-03 10-00-00.mkv"


def paire_obs(camera, a, confiance, maitre=OBS):
    return {"camera": camera, "maitre": maitre, "accepte": True, "a": a, "d": 0.0,
            "confiance": confiance, "confiance_grossiere": confiance,
            "derive_source": "mesuree", "span_s": 600.0,
            "residu_ms": 0.1, "points": [{"u": 0.0, "offset": a}]}


class CouvertureTests(unittest.TestCase):
    def test_obs_prioritaire_meme_si_secours_plus_confiant(self):
        # OBS de 50 s qui démarre avec le rush ; secours artificiellement très confiant.
        secours = {**av.paire_secours("DJI_0026.MP4", "DJI_0026.wav"), "confiance": 1e6}
        segments, trous = av.couvrir_rush(
            100.0, 0.0, [secours, paire_obs("DJI_0026.MP4", 0.0, 8.0)],
            {OBS: 50.0, "DJI_0026.wav": 100.0})
        self.assertEqual([(s["maitre"], s["tau_debut"], s["tau_fin"]) for s in segments],
                         [(OBS, 0.0, 50.0), ("DJI_0026.wav", 50.0, 100.0)])
        self.assertFalse(segments[0]["secours"])
        self.assertTrue(segments[1]["secours"])
        self.assertEqual(trous, [])

    def test_trou_de_fin_rempli_par_le_secours(self):
        # Le rush commence 30 s dans l'OBS, l'OBS s'arrête 40 s avant la fin du rush.
        segments, trous = av.couvrir_rush(
            100.0, 0.0, [paire_obs("DJI_0027.MP4", 30.0, 12.0),
                         av.paire_secours("DJI_0027.MP4", "DJI_0027.wav")],
            {OBS: 90.0, "DJI_0027.wav": 100.0})
        self.assertEqual([(s["maitre"], s["tau_debut"], s["tau_fin"]) for s in segments],
                         [(OBS, 0.0, 60.0), ("DJI_0027.wav", 60.0, 100.0)])
        self.assertEqual(trous, [])

    def test_sans_secours_le_trou_reste(self):
        segments, trous = av.couvrir_rush(100.0, 0.0, [paire_obs("C.MP4", 30.0, 12.0)],
                                          {OBS: 90.0})
        self.assertEqual(trous, [(60.0, 100.0)])

    def test_principaux_entre_eux_par_confiance(self):
        segments, _ = av.couvrir_rush(
            100.0, 0.0, [paire_obs("C.MP4", 0.0, 5.0, "a.wav"), paire_obs("C.MP4", 0.0, 9.0, "b.wav"),
                         av.paire_secours("C.MP4", "C.wav")],
            {"a.wav": 100.0, "b.wav": 100.0, "C.wav": 100.0})
        self.assertEqual([s["maitre"] for s in segments], ["b.wav"])


class AudioRushTests(unittest.TestCase):
    def test_aucun_silence_de_remplissage_avec_secours(self):
        cam = {"frames": 100 * 50, "av_ms": 0.0, "segments": []}
        cam["segments"], trous = av.couvrir_rush(
            100.0, 0.0, [paire_obs("C.MP4", 30.0, 12.0), av.paire_secours("C.MP4", "C.wav")],
            {OBS: 90.0, "C.wav": 100.0})
        self.assertEqual(trous, [])
        lus = []

        def lire(chemin, t, d, n):
            lus.append((chemin.name, round(t, 3), n))
            return np.ones(n, dtype=np.float32)

        with mock.patch.object(av, "_lire_master", lire):
            x = av.audio_rush(cam, {OBS: Path(OBS), "C.wav": Path("C.wav")})
        self.assertEqual(len(x), 100 * av.AUDIO_SR)
        self.assertEqual(lus, [(OBS, 30.0, 60 * av.AUDIO_SR), ("C.wav", 60.0, 40 * av.AUDIO_SR)])
        # Seul le raccord de 10 ms entre OBS et secours passe par zéro (fondu croisé).
        self.assertLessEqual(int(np.count_nonzero(x == 0)), 2)
        self.assertGreater(float(np.mean(np.abs(x[-av.AUDIO_SR:]))), 0.99)


def source(nom):
    return av.Source(nom=nom, entree=f"/rushs/{nom}", ident=nom, taille=1, s3=f"s3://b/p/{nom}")


class AnalyseTests(unittest.TestCase):
    """analyser() de bout en bout, sondes et mesures simulées."""

    DUREES = {OBS: 300.0, "DJI_0023.MP4": 20.0, "DJI_0026.MP4": 120.0,
              "DJI_0023.wav": 20.0, "DJI_0026.wav": 120.0}

    def sonder(self, src, _forces):
        if src.nom.endswith(".MP4"):
            src.type, src.origine = "camera", "camera"
        else:
            src.type, src.origine = "maitre", "obs" if src.nom == OBS else "audio"

    def info(self, src):
        frames = int(self.DUREES[src.nom] * 50)
        return av.InfoCamera(codec="h264", profil=None, largeur=3840, hauteur=2160, pix_fmt=None,
                             fps=Fraction(50), fps_moyen=Fraction(50), frames=frames, av=0.0,
                             creation=None, debit=None)

    def piste(self, src, _cache):
        return np.zeros(int(self.DUREES[src.nom] * synchro.XCORR_SR), dtype=np.float32)

    def mesurer(self, cam, wav):
        # 0026 commence à 240 s dans l'OBS (300 s) : ses 60 dernières secondes sont hors OBS.
        # 0023 est un faux départ que l'OBS n'a pas enregistré.
        if cam.nom == "DJI_0026.MP4" and wav.nom == OBS:
            return paire_obs(cam.nom, 240.0, 10.0)
        return {"camera": cam.nom, "maitre": wav.nom, "accepte": False,
                "confiance_grossiere": 3.0, "raison": "aucune sonde fiable"}

    def analyser(self, sources, secours):
        with tempfile.TemporaryDirectory() as tmp, \
             mock.patch.object(av, "sonder", self.sonder), \
             mock.patch.object(av, "info_camera", self.info), \
             mock.patch.object(av, "extraire_16k_maitre", self.piste), \
             mock.patch.object(av, "extraire_16k_camera", self.piste), \
             mock.patch.object(av.synchro, "mesurer_paire", self.mesurer):
            return av.analyser([source(n) for n in sources], Path(tmp), set(),
                               [source(n) for n in secours])

    def test_rush_sans_obs_couvert_par_son_secours(self):
        analyse = self.analyser([OBS, "DJI_0023.MP4", "DJI_0026.MP4"],
                                ["DJI_0023.wav", "DJI_0026.wav"])
        cams = {c["nom"]: c for c in analyse["cameras"]}
        c23 = cams["DJI_0023.MP4"]
        self.assertEqual(c23["couverture_obs_pct"], 0.0)
        self.assertEqual(c23["couverture_secours_pct"], 100.0)
        self.assertEqual(c23["plages_secours"], [[0.0, 20.0]])
        self.assertEqual(c23["trous"], [])
        self.assertTrue(any("DJI_0023.MP4" in a and "aucun maître principal" in a
                            for a in analyse["avertissements"]))
        c26 = cams["DJI_0026.MP4"]
        self.assertEqual([(s["maitre"], s["tau_debut"], s["tau_fin"]) for s in c26["segments"]],
                         [(OBS, 0.0, 60.0), ("DJI_0026.wav", 60.0, 120.0)])
        self.assertEqual((c26["couverture_obs_pct"], c26["couverture_secours_pct"]), (50.0, 50.0))
        self.assertEqual(c26["trous"], [])
        # Le rapport distingue l'OBS des secours (garde_fous.py voix lit origine « obs »).
        maitres = {m["nom"]: m for m in analyse["maitres"]}
        self.assertEqual(maitres[OBS]["origine"], "obs")
        self.assertTrue(maitres[OBS]["utilise"])
        self.assertEqual(maitres["DJI_0023.wav"]["origine"], "secours")
        # L'ordre des rushs ne dépend pas du secours.
        self.assertEqual([c["nom"] for c in analyse["cameras"]], ["DJI_0023.MP4", "DJI_0026.MP4"])

    def test_secours_jamais_croise_avec_un_autre_rush(self):
        analyse = self.analyser([OBS, "DJI_0023.MP4", "DJI_0026.MP4"],
                                ["DJI_0023.wav", "DJI_0026.wav"])
        for c in analyse["cameras"]:
            for s in c["segments"]:
                if s["secours"]:
                    self.assertEqual(Path(s["maitre"]).stem, Path(c["nom"]).stem)
        self.assertFalse(any(p.get("secours") and p["maitre"] == OBS for p in analyse["paires"]))

    def test_refus_si_ni_obs_ni_secours(self):
        with self.assertRaises(av.ErreurEntree) as ctx:
            self.analyser([OBS, "DJI_0023.MP4", "DJI_0026.MP4"], ["DJI_0026.wav"])
        self.assertIn("Appairage refusé", str(ctx.exception))
        self.assertIn("DJI_0023.MP4", str(ctx.exception))
        self.assertNotIn("DJI_0026.MP4", str(ctx.exception))

    def test_secours_de_duree_differente_ecarte(self):
        self.DUREES = {**self.DUREES, "DJI_0023.wav": 5.0}
        with self.assertRaises(av.ErreurEntree):
            self.analyser([OBS, "DJI_0023.MP4"], ["DJI_0023.wav"])


class CacheS3Tests(unittest.TestCase):
    """Le WAV déjà extrait est réutilisé seulement s'il vient du même rush."""

    def test_reutilise_si_meme_rush(self):
        import extraire_audio_camera as ex
        rush = source("DJI_0026.MP4")
        rush.type = "camera"
        head = '{"Metadata": {"rush-ident": "DJI_0026.MP4"}}'
        with mock.patch.object(ex.av, "sources_projet", return_value=[rush]), \
             mock.patch.object(ex.av, "sonder", lambda s, _: None), \
             mock.patch.object(ex.av, "run_aws", return_value=head) as aws, \
             mock.patch.object(ex, "extraire", side_effect=AssertionError("réextrait")), \
             tempfile.TemporaryDirectory() as tmp:
            wavs = ex.extraire_projet("p", travail=Path(tmp))
        self.assertEqual(wavs, {rush.s3: f"s3://{av.BUCKET}/inputs/p/audio-camera/DJI_0026.wav"})
        self.assertEqual(aws.call_count, 1)

    def test_rush_remplace_reextrait_et_echec_tolere(self):
        import extraire_audio_camera as ex
        rush = source("DJI_0026.MP4")
        rush.type = "camera"
        head = '{"Metadata": {"rush-ident": "ancien"}}'
        with mock.patch.object(ex.av, "sources_projet", return_value=[rush]), \
             mock.patch.object(ex.av, "sonder", lambda s, _: None), \
             mock.patch.object(ex.av, "run_aws", return_value=head), \
             mock.patch.object(ex, "extraire", side_effect=OSError("lecture")) as extraire, \
             tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(ex.extraire_projet("p", travail=Path(tmp), tolerant=True), {})
            with self.assertRaises(OSError):
                ex.extraire_projet("p", travail=Path(tmp))
        self.assertTrue(extraire.called)


if __name__ == "__main__":
    unittest.main()
