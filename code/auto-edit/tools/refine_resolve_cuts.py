#!/usr/bin/env python3
"""Resserrer les coupes Resolve sur les silences entre les mots."""
import argparse
import json
from pathlib import Path


def merge_intervals(rows):
    merged=[]
    for start,end in sorted(rows):
        if end<=start:
            continue
        if merged and start<=merged[-1][1]:
            merged[-1][1]=max(merged[-1][1],end)
        else:
            merged.append([start,end])
    return merged


def complement(rows,total):
    kept=[]
    cursor=0
    for start,end in rows:
        if start>cursor:
            kept.append([cursor,start])
        cursor=max(cursor,end)
    if cursor<total:
        kept.append([cursor,total])
    return kept


def refine(kept,words,total,fps,gap=.60,speech_pad=.10):
    manual=[]
    cursor=0
    for start,end in kept:
        start=max(0,min(total,start)); end=max(start,min(total,end))
        if start>cursor:
            manual.append([cursor,start])
        cursor=end
    if cursor<total:
        manual.append([cursor,total])

    adjusted=[]
    for start,end in manual:
        start_s,end_s=start/fps,end/fps
        start_word=next((w for w in words if w['start']<start_s<w['end']),None)
        end_word=next((w for w in words if w['start']<end_s<w['end']),None)
        if end_word and not start_word and end_s-end_word['start']<=.15:
            end=max(start+1,round((end_word['start']-.06)*fps))
        if start_word and not end_word and start_word['end']-start_s<=.15:
            start=min(end-1,round((start_word['end']+.06)*fps))
        adjusted.append([start,end])

    silence=[]
    for previous,next_word in zip(words,words[1:]):
        gap_start=previous['end']; gap_end=next_word['start']
        if gap_end-gap_start<gap:
            continue
        start=round((gap_start+speech_pad)*fps)
        end=round((gap_end-speech_pad)*fps)
        if end>start:
            silence.append([start,end])

    removed=merge_intervals(adjusted+silence)
    refined=complement(removed,total)
    report={
        'fps':fps,'total_frames':total,'manual_cuts':len(manual),
        'silence_cuts':len(silence),
        'removed_frames':sum(end-start for start,end in removed),
        'kept_frames':sum(end-start for start,end in refined),
        'gap_threshold_seconds':gap,'speech_pad_seconds':speech_pad,
        'manual_removed':manual,'manual_adjusted':adjusted,
        'silence_removed':silence,
    }
    return refined,report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--kept',required=True,type=Path)
    p.add_argument('--words',required=True,type=Path)
    p.add_argument('--manifest',required=True,type=Path)
    p.add_argument('--out',required=True,type=Path)
    p.add_argument('--gap',type=float,default=.60)
    p.add_argument('--speech-pad',type=float,default=.10)
    p.add_argument('--no-open',action='store_true')
    a=p.parse_args()
    manifest=json.loads(a.manifest.read_text())
    words=json.loads(a.words.read_text())
    fps=manifest['fps']; total=sum(c['frames'] for c in manifest['chunks'])
    kept=json.loads(a.kept.read_text())
    refined,report=refine(kept,words,total,fps,a.gap,a.speech_pad)
    a.out.write_text(json.dumps(refined,indent=2))
    a.out.with_suffix('.report.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({
        'manual_cuts':report['manual_cuts'],
        'silence_cuts':report['silence_cuts'],
        'removed_seconds':report['removed_frames']/fps,
        'output_seconds':report['kept_frames']/fps,
    }))


if __name__=='__main__':
    main()
