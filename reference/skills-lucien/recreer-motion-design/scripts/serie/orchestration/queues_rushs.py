#!/usr/bin/env python3
"""Extrait la suite brute d'un montage depuis ses rushs (DJI + OBS), pour rendre un dernier mot coupé.

Usage : queues_rushs.py <montage.sources.json> <sortie.mov> [--vitesse 1.06] [--avant 0.5] [--duree 2.0] --no-open
Entrée : le montage.sources.json de l'assemblage multicam (dernier chunk : camera et audio, début et fin source).
Sortie : .mov 2560x1440 50 i/s + .json. Les `avant/vitesse` premières secondes recouvrent la fin de la plaque :
le monteur cale par corrélation audio, applique la chaîne voix et le look de la plaque, puis raccorde.
"""
import argparse, json, subprocess

p = argparse.ArgumentParser()
p.add_argument('sources'); p.add_argument('sortie')
p.add_argument('--vitesse', type=float, default=1.06); p.add_argument('--avant', type=float, default=0.5)
p.add_argument('--duree', type=float, default=2.0); p.add_argument('--no-open', action='store_true')
a = p.parse_args()
c = json.load(open(a.sources))['chunks'][-1]
cam, aud = c['camera'], c['audio']
subprocess.run(['ffmpeg', '-v', 'error', '-y',
    '-ss', str(cam['end'] - a.avant), '-t', str(a.duree), '-i', cam['path'],
    '-ss', str(aud['end'] - a.avant), '-t', str(a.duree), '-i', aud['path'],
    '-map', '0:v:0', '-map', '1:a:0',
    '-filter:v', f'setpts=PTS/{a.vitesse},scale=2560:-2,fps=50', '-filter:a', f'atempo={a.vitesse}',
    '-c:v', 'libx264', '-crf', '14', '-preset', 'fast', '-c:a', 'pcm_s24le', a.sortie], check=True)
json.dump({'recouvrement_s_plaque': round(a.avant / a.vitesse, 4), 'camera': cam, 'audio': aud,
           'note': 'Suite brute (OBS non traité, DJI non étalonné). Caler par corrélation audio sur le recouvrement.'},
          open(a.sortie.rsplit('.', 1)[0] + '.json', 'w'), indent=1)
print('ok', a.sortie)
