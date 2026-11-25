#!/usr/bin/python3
"""Plan multicam → table source-timeline avec la piste OBS comme audio maître.

Chaque portion reçoit un champ `audio` qui pointe vers l'enregistrement OBS,
recalé par la synchronisation GCC-PHAT du plan (même carte que l'écran).
La caméra ne fournit plus que l'image.

  obs_master.py DIR/prise1/montage.json --out DIR/prise1/montage.sources.json
"""
import argparse
import copy
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from pipeline import source_module
from resolve_cuts import probe_dur, probe_fps


def to_obs_master(plan):
    module = source_module()
    durations = [probe_dur(x) for x in plan['cam_parts']]
    fps = probe_fps(plan['cam_parts'][0])
    # Toutes les portions en split pour obtenir les bornes OBS, sans changer les frames.
    probe = copy.deepcopy(plan)
    probe['segments'] = [[s, e, 'split'] for s, e, _ in plan['segments']]
    mapped = module.from_multicam(probe, durations, fps)
    doc = module.from_multicam(plan, durations, fps)
    if len(mapped['chunks']) != len(doc['chunks']):
        raise RuntimeError('Découpage incohérent entre plan et carte OBS.')
    for chunk, ref in zip(doc['chunks'], mapped['chunks']):
        if chunk['frames'] != ref['frames']:
            raise RuntimeError('Frames incohérentes entre plan et carte OBS.')
        chunk['audio'] = dict(ref['screen'])
    doc['audio_master'] = plan['screen']
    doc['audio_channels'] = 2
    doc['source_duration_seconds'] = sum(durations)
    doc['sync_report'] = plan.get('sync')
    return module.validate(doc)


def output_words(doc, words, av_cam):
    """Recaler les mots de la transcription caméra sur la timeline rendue."""
    out, pos = [], 0.
    for chunk in doc['chunks']:
        cam = chunk['camera']
        dur = chunk['frames'] / doc['fps']
        rate = (cam['end'] - cam['start']) / dur
        for w in words:
            mid = (w['start'] + w['end']) / 2 + av_cam
            if cam['start'] <= mid < cam['end']:
                a = max(0., (w['start'] + av_cam - cam['start']) / rate)
                b = min(dur, (w['end'] + av_cam - cam['start']) / rate)
                out.append({**w, 'start': pos + a, 'end': pos + b})
        pos += dur
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('plan', type=Path)
    p.add_argument('--out', required=True, type=Path)
    p.add_argument('--transcache', type=Path, help='multicam.transcache.json de la prise')
    p.add_argument('--no-open', action='store_true')
    a = p.parse_args()
    plan = json.loads(a.plan.read_text())
    if len(plan['cam_parts']) != 1:
        raise SystemExit('Une partie caméra par prise attendue pour le recalage des mots.')
    doc = to_obs_master(plan)
    a.out.write_text(json.dumps(doc, ensure_ascii=False, indent=2))
    if a.transcache:
        words = json.loads(a.transcache.read_text())['words']
        mapped = output_words(doc, words, plan['sync'].get('av_cam', 0.))
        target = a.out.with_name(a.out.name.replace('.sources.json', '.words.json'))
        target.write_text(json.dumps(mapped, ensure_ascii=False, indent=2))
        print(f'{len(mapped)} mots recalés sur {len(words)}.')
    n = sum(c['frames'] for c in doc['chunks'])
    print(f"{len(doc['chunks'])} portions, {n} images, {n/doc['fps']:.2f}s, audio maître OBS.")


if __name__ == '__main__':
    main()
