#!/usr/bin/env python3
import unittest

from tools.refine_resolve_cuts import refine


class RefineResolveCutsTests(unittest.TestCase):
    def test_clamps_resolve_tail_and_trims_word_gap(self):
        words=[
            {'text':'a','start':0.0,'end':1.0},
            {'text':'b','start':2.0,'end':3.0},
        ]
        kept=[[0,40],[45,101]]
        refined,report=refine(kept,words,total=100,fps=10,gap=.6,speech_pad=.1)
        self.assertEqual(refined[-1][1],100)
        self.assertIn([11,19],report['silence_removed'])
        self.assertEqual(report['manual_removed'],[[40,45]])

    def test_preserves_word_touched_by_cut_end(self):
        words=[
            {'text':'a','start':0.0,'end':1.0},
            {'text':'b','start':2.0,'end':2.5},
        ]
        kept=[[0,12],[21,30]]
        _,report=refine(kept,words,total=30,fps=10,gap=9.)
        self.assertEqual(report['manual_adjusted'],[[12,19]])


if __name__=='__main__':
    unittest.main()
