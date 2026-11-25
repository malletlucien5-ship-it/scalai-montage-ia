import unittest
import numpy as np
from quiet_cleanup import find_quiet_cuts, subtract_cuts, refine_kept


class QuietCleanupTests(unittest.TestCase):
    def audio(self):
        x = np.full(32000, 0.1)
        x[8000:11200] = 0
        return x

    def test_removes_quiet_200ms_with_speech_margins(self):
        self.assertEqual(find_quiet_cuts(self.audio(), 16000, [], fps=50), [[26, 34]])

    def test_preserves_short_spoken_word(self):
        x = self.audio()
        x[8700:10300] = 0.03
        self.assertEqual(find_quiet_cuts(x, 16000, [], fps=50), [])

    def test_preserves_word_center_even_when_whisper_and_audio_disagree(self):
        words = [{'start': .55, 'end': .65, 'text': 'oui'}]
        self.assertEqual(find_quiet_cuts(self.audio(), 16000, words, fps=50), [])

    def test_preserves_subthreshold_pause(self):
        x = np.full(32000, .1)
        x[8000:9600] = 0
        self.assertEqual(find_quiet_cuts(x, 16000, [], fps=50), [])

    def test_never_restores_manual_cuts_and_keeps_repetitions(self):
        kept = [[0, 20], [40, 60], [0, 20]]
        self.assertEqual(subtract_cuts(kept, [[10, 50]]), [[0, 10], [50, 60], [0, 10]])

    def test_inward_rounding_keeps_margins(self):
        x = np.full(32000, .1)
        x[8160:11520] = 0
        self.assertEqual(find_quiet_cuts(x, 16000, [], fps=50), [[27, 35]])

    def test_cleanup_checks_new_manual_join_and_preserves_source_mapping(self):
        x = np.full(32000, .1)
        x[6400:8000] = 0
        x[16000:17600] = 0
        kept, report = refine_kept([[0,25],[50,100]],x,16000,[],fps=50)
        self.assertEqual(kept, [[0,21],[54,100]])
        self.assertEqual(report['remaining'],0)
        self.assertEqual(report['removed_frames'],8)


if __name__ == '__main__':
    unittest.main()
