#!/usr/bin/env python3
import unittest

from tools.merge_source_plans import merge


def plan(camera, frames, source_duration):
    return {
        'version':1,
        'kind':'source-timeline',
        'fps':50,
        'chunks':[{
            'frames':frames,
            'layout':'face',
            'camera':{'path':camera,'start':1.0,'end':1.0+frames/50},
        }],
        'sources':{camera:{}},
        'source_duration_seconds':source_duration,
    }


class MergeSourcePlansTests(unittest.TestCase):
    def test_merges_every_camera_and_shifts_words(self):
        doc,words=merge(
            [plan('/a.mp4',100,10),plan('/b.mp4',150,20)],
            [[{'text':'a','start':.2,'end':.4}],[{'text':'b','start':.1,'end':.3}]],
            ['/a.mp4','/b.mp4'],
        )
        self.assertEqual(doc['camera_paths'],['/a.mp4','/b.mp4'])
        self.assertEqual(doc['camera_count'],2)
        self.assertEqual(doc['part_count'],2)
        self.assertEqual(doc['total_frames'],250)
        self.assertEqual(doc['source_duration_seconds'],30)
        self.assertAlmostEqual(words[1]['start'],2.1)

    def test_rejects_partial_project(self):
        with self.assertRaisesRegex(ValueError,'incomplets'):
            merge([plan('/a.mp4',100,10)],[[]],['/a.mp4','/b.mp4'])


if __name__=='__main__':
    unittest.main()
