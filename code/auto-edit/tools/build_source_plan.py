#!/usr/bin/env python3
"""Construire une timeline originale depuis VAD, mots et synchronisation validée."""
import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from auto_edit import normalize
from multicam import find_filler_intervals, split_long_segments, solve_layouts_dp, decide_layouts_llm, decide_layouts_heuristic, _load_env_fallback
from quiet_cleanup import clean_segments, read_audio


def build(cam,screen,transcript,sync,ranges,fps=50,speed=1.06,no_llm=False,
          force_intro=True,force_outro=True,preserve_full=False):
    words=[{'start':w['start'],'end':w['end'],'raw':w['text'],'word':normalize(w['text'])}
           for w in transcript['words']]
    regions=sync['regions']
    bad=[] if preserve_full else find_filler_intervals(words)
    segs=[]
    if preserve_full:
        dur=transcript['duration']
        bounds={0.,round(dur*fps)/fps}
        for t in range(8,int(dur)+1,8):
            bounds.add(round(t*fps)/fps)
        for r in regions:
            bounds.update((round(r['cam_start']*fps)/fps,round(r['cam_end']*fps)/fps))
            for spans in (ranges.get('face',[]),ranges.get('split',[])):
                for x,y in spans:
                    for screen_t in (x,y):
                        cam_t=(screen_t-r['offset'])/(1+r['drift'])
                        if r['cam_start'] < cam_t < r['cam_end']:
                            bounds.add(round(cam_t*fps)/fps)
        ordered=sorted(t for t in bounds if 0 <= t <= dur)
        segs=[(a,b) for a,b in zip(ordered,ordered[1:]) if b>a]
    else:
        for start,end in transcript['vad']:
            spans=[(start,end)]
            for bs,be,_ in bad:
                bs=max(0,bs-.01); be+=.01
                spans=[part for a,b in spans for part in
                       ([(a,b)] if be<=a or bs>=b else [(a,min(b,bs)),(max(a,be),b)])
                       if part[1]-part[0] >= .1]
            for a,b in spans:
                a,b=round(a*fps)/fps,round(b*fps)/fps
                if b>a:
                    segs.append((a,b))
        audio,sample_rate=read_audio(cam)
        segs=clean_segments(segs,audio,sample_rate,words,fps)
        segs=split_long_segments(segs,words,max_len=8.,min_half=3.,fps=fps)
    # Scinder aux limites prouvées pour empêcher tout plan écran hors couverture.
    bounds=sorted({t for r in regions for t in (r['cam_start'],r['cam_end'])})
    split=[]
    for a,b in segs:
        points=[a]+[round(t*fps)/fps for t in bounds if a+.02<t<b-.02]+[b]
        split.extend((x,y) for x,y in zip(points,points[1:]) if y>x)
    segs=split
    _load_env_fallback()
    key=os.environ.get('OPENROUTER_API_KEY')
    prefs=decide_layouts_llm(segs,words,key) if key and not no_llm else None
    prefs=prefs or decide_layouts_heuristic(segs)
    locked={}
    matched=[]
    dur=transcript['duration']
    for i,(a,b) in enumerate(segs):
        region=next((r for r in regions if a>=r['cam_start']-.011 and b<=r['cam_end']+.011),None)
        matched.append(region)
        if region:
            sa=a+region['offset']+region['drift']*a
            sb=b+region['offset']+region['drift']*b
        else:
            sa=sb=-1
        boundary_face=(force_intro and a<25) or (force_outro and b>dur-25)
        in_face=any(sa<y and sb>x for x,y in ranges.get('face',[]))
        in_split=any(sa<y and sb>x for x,y in ranges.get('split',[]))
        if region is None or boundary_face or in_face or (preserve_full and not in_split):
            locked[i]=0; prefs[i]='face'
        elif in_split:
            locked[i]=1; prefs[i]='split'
    layouts=solve_layouts_dp(prefs,segs,min_shot=4*speed,max_run=10*speed,locked=locked)
    chunks=[]
    input_frames=output_frames=0
    outwords=[]
    for i,((a,b),layout) in enumerate(zip(segs,layouts)):
        n=round(b*fps)-round(a*fps)
        input_frames+=n
        nxt=max(output_frames+1,round(input_frames/speed))
        frames=nxt-output_frames
        c={'frames':frames,'layout':layout,'camera':{'path':str(cam),'start':a,'end':b}}
        if layout=='split':
            r=matched[i]
            c['screen']={'path':str(screen),'start':a+r['offset']+r['drift']*a,
                         'end':b+r['offset']+r['drift']*b}
        chunks.append(c)
        for w in transcript['words']:
            if a <= (w['start']+w['end'])/2 < b:
                outwords.append({'text':w['text'],
                  'start':output_frames/fps+max(0,w['start']-a)/(b-a)*frames/fps,
                  'end':output_frames/fps+min(b-a,w['end']-a)/(b-a)*frames/fps})
        output_frames=nxt
    sources={str(p):{'size':p.stat().st_size,'mtime_ns':p.stat().st_mtime_ns} for p in (cam,screen)}
    doc={'version':1,'kind':'source-timeline','fps':fps,'chunks':chunks,'sources':sources,
         'vertical':{'width':1080,'height':1920,'camera_height':666,'screen_fit':'fit',
                     'reference_status':'provisional-visible-reference'},
         'face_crop':[1050,250,1800,1800], 'speed':speed,
         'sync_report':sync,'ranges':ranges,
         'cut_policy':'aucune coupe temporelle' if preserve_full else 'silences et fillers uniquement',
         'fillers_removed':bad,'source_duration_seconds':transcript['duration'],
         'kept_source_seconds':sum(c['camera']['end']-c['camera']['start'] for c in chunks)}
    return doc,outwords


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cam',required=True,type=Path); p.add_argument('--screen',required=True,type=Path)
    p.add_argument('--transcript',required=True,type=Path); p.add_argument('--sync',required=True,type=Path)
    p.add_argument('--ranges',required=True,type=Path); p.add_argument('--out',required=True,type=Path)
    p.add_argument('--no-llm',action='store_true')
    p.add_argument('--no-force-intro',action='store_true')
    p.add_argument('--no-force-outro',action='store_true')
    p.add_argument('--preserve-full',action='store_true',
                   help='Conserver toute la durée caméra pour les coupes manuelles dans Resolve.')
    p.add_argument('--speed',type=float,default=1.06)
    a=p.parse_args()
    transcript=json.loads(a.transcript.read_text())
    if not transcript.get('complete'):
        raise SystemExit('Transcription incomplète.')
    doc,words=build(a.cam.resolve(),a.screen.resolve(),transcript,json.loads(a.sync.read_text()),
                    json.loads(a.ranges.read_text()),no_llm=a.no_llm,speed=a.speed,
                    force_intro=not a.no_force_intro,force_outro=not a.no_force_outro,
                    preserve_full=a.preserve_full)
    a.out.write_text(json.dumps(doc,ensure_ascii=False,indent=2))
    words_path=a.out.with_name(a.out.name.replace('.sources.json','.words.json'))
    words_path.write_text(json.dumps(words,ensure_ascii=False,indent=2))
    print(f'{len(doc["chunks"])} portions, {sum(c["frames"] for c in doc["chunks"])/doc["fps"]:.2f}s, {len(words)} mots, {len(doc["fillers_removed"])} fillers.')


if __name__=='__main__': main()
