"""Vérifier que le bypass retire tous les traitements de réduction de bruit."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import auto_edit


class DenoiseBypassTests(unittest.TestCase):
    def test_no_denoise_skips_ml_gate_and_spectral_reduction(self):
        with patch.object(auto_edit, 'run'), \
             patch.object(auto_edit, '_deepfilternet_denoise') as deep, \
             patch.object(auto_edit, '_vad_speech_gate') as gate, \
             patch.object(auto_edit, '_measure_chain_latency', return_value=0) as latency, \
             patch.object(auto_edit, '_measure_loudness', return_value=None), \
             patch.object(auto_edit, 'get_stream_duration', return_value=2), \
             patch.object(auto_edit.subprocess, 'run') as run, \
             patch.object(auto_edit, 'warn_av_sync'), \
             patch.object(auto_edit, 'USE_DEEPFILTERNET', True), \
             patch.object(auto_edit, 'USE_SPEECH_GATE', True):
            run.return_value.returncode = 0
            auto_edit.polish_audio('in.mp4', 'out.mp4', denoise=False)
            deep.assert_not_called()
            gate.assert_not_called()
            self.assertNotIn('afftdn', latency.call_args[0][0])
            self.assertIn('acompressor', latency.call_args[0][0])


if __name__ == '__main__':
    unittest.main()
