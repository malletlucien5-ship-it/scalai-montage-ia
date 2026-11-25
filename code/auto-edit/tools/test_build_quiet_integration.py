import tempfile
import unittest
import wave
from pathlib import Path
from unittest.mock import patch
import numpy as np
import build_source_plan


class BuildQuietIntegrationTests(unittest.TestCase):
    def test_normal_plan_cleans_quiet_and_preserve_full_keeps_every_frame(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'camera.wav'
            data=np.full(32000,3277,dtype='<i2')
            data[8000:11200]=0
            with wave.open(str(path),'wb') as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(16000)
                wav.writeframes(data.tobytes())
            transcript={'duration':2,'vad':[[0,2]],'words':[
                {'start':.1,'end':.3,'text':'bonjour'},
                {'start':1.2,'end':1.4,'text':'Lucien'}]}
            sync={'regions':[{'cam_start':0,'cam_end':2,'offset':0,'drift':0}]}
            with patch.object(build_source_plan,'_load_env_fallback'):
                doc,words=build_source_plan.build(path,path,transcript,sync,{},speed=1,no_llm=True)
                full,_=build_source_plan.build(path,path,transcript,sync,{},speed=1,no_llm=True,preserve_full=True)
            self.assertEqual(sum(c['frames'] for c in doc['chunks']),92)
            self.assertEqual(sum(c['frames'] for c in full['chunks']),100)
            self.assertEqual([w['text'] for w in words],['bonjour','Lucien'])
            self.assertEqual(doc['chunks'][0]['camera']['end'],.52)
            self.assertEqual(doc['chunks'][1]['camera']['start'],.68)


if __name__=='__main__':
    unittest.main()
