"""Le son caméra n'est jamais retenu en silence quand un OBS est déposé."""
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    import etape1
except ImportError as exc:  # dépendances audio absentes
    etape1 = None
    RAISON = str(exc)


def source(nom, type_):
    return SimpleNamespace(nom=nom, type=type_, s3=f"s3://b/inputs/p/rushs/{nom}")


@unittest.skipIf(etape1 is None, "dépendances de voix/ absentes")
class SonCameraTests(unittest.TestCase):
    def lancer(self, sources, forcer=""):
        with mock.patch.object(etape1, "sources_projet", return_value=sources), \
             mock.patch.object(etape1.av, "sonder", lambda s, _: None):
            return etape1.sources_camera("p", [], forcer)

    def test_obs_present_refuses_camera_audio(self):
        sources = [source("DJI_0001_D.MP4", "camera"), source("2026-09-28 20-32-04.mp4", "maitre")]
        with self.assertRaises(etape1.av.ErreurEntree) as ctx:
            self.lancer(sources)
        self.assertIn("2026-09-28 20-32-04.mp4", str(ctx.exception))

    def test_written_reason_allows_camera_audio(self):
        sources = [source("DJI_0001_D.MP4", "camera"), source("2026-09-28 20-32-04.mp4", "maitre")]
        sortie = self.lancer(sources, "OBS sans micro ce jour-là")
        self.assertEqual(sortie[0], "s3://b/inputs/p/rushs/DJI_0001_D.MP4")

    def test_camera_only_still_works(self):
        sortie = self.lancer([source("DJI_0001_D.MP4", "camera")])
        self.assertEqual(len(sortie), 2)

    def lancer_maitre(self, argv, wavs=None, erreur=None):
        rushs = [source("DJI_0022_D.MP4", "camera"), source("DJI_0023_D.MP4", "camera"),
                 source("2026-09-28 20-32-04.mp4", "maitre")]
        extraire = mock.Mock(return_value=wavs or {}, side_effect=erreur)
        with mock.patch.object(etape1.av, "valider_projet", return_value="p"), \
             mock.patch.object(etape1.av, "sources_projet", return_value=rushs), \
             mock.patch.object(etape1.ex, "main", side_effect=AssertionError("son caméra en voix")), \
             mock.patch.object(etape1.ex, "extraire_projet", extraire), \
             mock.patch.object(etape1.av, "main", return_value=7) as rendre:
            self.assertEqual(etape1.main(["--projet", "p", *argv]), 7)
        return rendre, extraire

    def test_default_audio_is_master(self):
        rendre, _ = self.lancer_maitre([])
        rendre.assert_called_once_with(["rendre", "--projet", "p", "--sans-proxy"])

    def test_master_mode_passes_camera_audio_as_fallback(self):
        wavs = {"s3://b/inputs/p/rushs/DJI_0023_D.MP4": "s3://b/inputs/p/audio-camera/DJI_0023_D.wav"}
        rendre, extraire = self.lancer_maitre(["--exclure", "0022"], wavs)
        # Rushs et ordre inchangés (exclusion comprise), le secours s'ajoute à la fin.
        rendre.assert_called_once_with([
            "rendre", "--projet", "p", "--sans-proxy",
            "s3://b/inputs/p/rushs/DJI_0023_D.MP4", "s3://b/inputs/p/rushs/2026-09-28 20-32-04.mp4",
            "--secours", "s3://b/inputs/p/audio-camera/DJI_0023_D.wav"])
        self.assertEqual(extraire.call_args.args[1], ["DJI_0022_D.MP4"])
        self.assertTrue(extraire.call_args.kwargs["tolerant"])

    def test_fallback_extraction_failure_never_blocks(self):
        rendre, _ = self.lancer_maitre([], erreur=OSError("aws absent"))
        rendre.assert_called_once_with(["rendre", "--projet", "p", "--sans-proxy"])

if __name__ == "__main__":
    unittest.main()
