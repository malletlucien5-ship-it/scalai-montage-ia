import copy
import unittest
from tools.intro import validate_spec


class IntroTests(unittest.TestCase):
    def setUp(self):
        self.spec = {'version':1, 'authorized':True, 'duration':21.72,
            'source_seconds':[0,30], 'crop_switch_seconds':3.962,
            'reference_crops':[[0,0,1600,900],[0,0,1450,816]],
            'face_seconds':[[3.96,7.54],[16.94,17.86],[29.4,30]]}

    def test_reference_end_lands_on_exact_last_intro_frame(self):
        frames,ratio,face=validate_spec(self.spec,50,78878)
        self.assertEqual(frames,1086)
        self.assertEqual(face,[(143,273),(613,647),(1064,1086)])
        self.assertAlmostEqual(ratio*30,frames/50)

    def test_offset_source_preserves_face_positions(self):
        shifted=copy.deepcopy(self.spec)
        shifted['source_seconds']=[10,40]
        shifted['crop_switch_seconds']+=10
        shifted['face_seconds']=[[a+10,b+10] for a,b in shifted['face_seconds']]
        self.assertEqual(validate_spec(shifted,50,78878)[2],validate_spec(self.spec,50,78878)[2])

    def test_rejects_intro_beyond_timeline(self):
        with self.assertRaises(ValueError):validate_spec(self.spec,50,100)

    def test_rejects_face_or_crop_switch_outside_reference(self):
        for field,value in [('face_seconds',[[29,31]]),('crop_switch_seconds',31)]:
            bad=self.spec|{field:value}
            with self.assertRaises(ValueError):validate_spec(bad,50,78878)

    def test_rejects_unauthorized_reference(self):
        with self.assertRaises(ValueError):validate_spec(self.spec|{'authorized':False},50,78878)


if __name__=='__main__':unittest.main()
