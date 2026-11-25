import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest

spec=importlib.util.spec_from_file_location('continuous_pipeline',Path(__file__).with_name('continuous_pipeline.py'))
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)


class PipelineTests(unittest.TestCase):
    def test_arrivals_start_independently_and_cache_invalidation_is_local(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); a=root/'a'; b=root/'b'; a.write_text('un')
            script='from pathlib import Path; import sys; Path(sys.argv[2]).write_text(Path(sys.argv[1]).read_text()+" traité")'
            tasks=[{'id':n,'command':[sys.executable,'-c',script,str(root/n),str(root/(n+'.out'))],
                    'inputs':[str(root/n)],'outputs':[str(root/(n+'.out'))]} for n in ('a','b')]
            observed=[]
            def deliver():
                time.sleep(.5); observed.append((root/'a.out').exists()); b.write_text('deux')
            thread=threading.Thread(target=deliver); thread.start()
            report=m.run({'tasks':tasks},root/'state',stable_seconds=.01,timeout=5)
            thread.join(); self.assertEqual(observed,[True]); self.assertEqual(report['status'],'complete')
            again=m.run({'tasks':tasks},root/'state',stable_seconds=0,timeout=5)
            self.assertTrue(all(t['status']=='cached' for t in again['tasks'].values()))
            a.write_text('trois')
            changed=m.run({'tasks':tasks},root/'state',stable_seconds=0,timeout=5)
            self.assertEqual(changed['tasks']['a']['status'],'complete')
            self.assertEqual(changed['tasks']['b']['status'],'cached')
            (root/'b.out').write_text('altération')
            changed=m.run({'tasks':tasks},root/'state',stable_seconds=0,timeout=5)
            self.assertEqual(changed['tasks']['b']['status'],'complete')

    def test_failure_prevents_dependents_and_is_reported(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            tasks=[{'id':'a','command':[sys.executable,'-c','raise SystemExit(2)'],
                'outputs':[str(root/'a')]},
                {'id':'b','depends':['a'],'command':[sys.executable,'-c','raise SystemExit(99)'],
                 'outputs':[str(root/'b')]}]
            with self.assertRaises(Exception): m.run({'tasks':tasks},root,stable_seconds=0)
            report=json.loads((root/'status.json').read_text())
            self.assertEqual(report['status'],'failed'); self.assertFalse((root/'b.log').exists())

    def test_rejects_cycles_and_duplicate_outputs(self):
        for tasks in ([{'id':'a','depends':['a'],'outputs':['x']}],
                      [{'id':'a','outputs':['x']},{'id':'b','outputs':['x']}]):
            with self.assertRaises(ValueError): m.validate_graph(tasks)


if __name__=='__main__': unittest.main()
