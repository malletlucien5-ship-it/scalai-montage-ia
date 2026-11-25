#!/usr/bin/env python3
"""Fusionner plusieurs prises auto-éditées en une timeline Resolve unique."""
import argparse
import json
from pathlib import Path


def camera_paths(plan):
    paths=[]
    for chunk in plan['chunks']:
        path=chunk['camera']['path']
        if path not in paths:
            paths.append(path)
    return paths


def merge(plans, word_files, expected_cameras=None):
    if len(plans) != len(word_files) or not plans:
        raise ValueError('Une table de mots est requise pour chaque plan.')
    fps=plans[0]['fps']
    if any(p.get('kind')!='source-timeline' or p.get('version')!=1 for p in plans):
        raise ValueError('Plans source-timeline version 1 requis.')
    if any(p['fps']!=fps for p in plans):
        raise ValueError('Les cadences des plans diffèrent.')
    actual_cameras=[path for plan in plans for path in camera_paths(plan)]
    if expected_cameras is not None and actual_cameras != expected_cameras:
        raise ValueError(f'Rushs caméra incomplets ou désordonnés. Attendu : {expected_cameras}. Reçu : {actual_cameras}.')
    merged=dict(plans[0])
    merged['chunks']=[]
    merged['sources']={}
    merged['parts']=[]
    merged_words=[]
    frames=0
    for index,(plan,words) in enumerate(zip(plans,word_files),1):
        start=frames
        count=sum(c['frames'] for c in plan['chunks'])
        merged['chunks'].extend(plan['chunks'])
        merged['sources'].update(plan.get('sources',{}))
        merged_words.extend({**w,'start':w['start']+start/fps,'end':w['end']+start/fps} for w in words)
        frames += count
        kept_seconds=sum(c['camera']['end']-c['camera']['start'] for c in plan['chunks'])
        source_seconds=plan.get('source_duration_seconds',
                                max(c['camera']['end'] for c in plan['chunks']))
        merged['parts'].append({'index':index,'start_frame':start,'end_frame':frames,
                                'source_duration_seconds':source_seconds,
                                'kept_source_seconds':kept_seconds,
                                'kept_input_frames':round(kept_seconds*fps),
                                'output_frames':count,
                                'cameras':camera_paths(plan)})
    merged['total_frames']=frames
    merged['part_count']=len(plans)
    merged['camera_count']=len(actual_cameras)
    merged['camera_paths']=actual_cameras
    merged['source_duration_seconds']=sum(p['source_duration_seconds'] for p in merged['parts'])
    merged['kept_source_seconds']=sum(p['kept_source_seconds'] for p in merged['parts'])
    merged['sync_reports']=[p.get('sync_report') for p in plans]
    merged['fillers_removed_by_part']=[p.get('fillers_removed',[]) for p in plans]
    masters=[]
    for plan in plans:
        for path in plan.get('audio_master_sources') or ([plan['audio_master']] if plan.get('audio_master') else []):
            if path not in masters:
                masters.append(path)
    merged.pop('audio_master',None)
    if masters:
        merged['audio_master_sources']=masters
    merged.pop('sync_report',None)
    merged.pop('fillers_removed',None)
    return merged,merged_words


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--plans',nargs='+',required=True,type=Path)
    p.add_argument('--words',nargs='+',required=True,type=Path)
    p.add_argument('--out',required=True,type=Path)
    p.add_argument('--expect-cameras',nargs='+',type=Path,
                   help='Liste complète des rushs caméra attendus dans leur ordre final.')
    p.add_argument('--no-open',action='store_true')
    a=p.parse_args()
    expected=[str(x.resolve()) for x in a.expect_cameras] if a.expect_cameras else None
    doc,words=merge([json.loads(x.read_text()) for x in a.plans],
                    [json.loads(x.read_text()) for x in a.words],expected)
    a.out.write_text(json.dumps(doc,ensure_ascii=False,indent=2))
    words_out=a.out.with_name(a.out.name.replace('.sources.json','.words.json'))
    words_out.write_text(json.dumps(words,ensure_ascii=False,indent=2))
    print(f'{doc["part_count"]} prises, {doc["total_frames"]} images, '
          f'{doc["total_frames"]/doc["fps"]:.2f}s, {len(words)} mots.')


if __name__=='__main__':
    main()
