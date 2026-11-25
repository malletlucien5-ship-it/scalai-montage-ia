#!/usr/bin/env python3
"""Transcrire chaque portion séparément, sur la piste audio maître.

Whisper transcrit un flux continu comme une phrase propre : une amorce ratée
suivie de la bonne prise (« et vous pouvez utiliser… et vous pouvez utiliser
ça ») ressort une seule fois. Transcrire chaque portion isolément empêche
cette fusion : chaque tentative garde son propre texte.

Exécuter avec l'environnement mlx (Apple Silicon) :

  ~/CODE/auto-edit/.venv-mlx/bin/python segment_transcribe.py montage.sources.json \
      --out segments.text.json [--pad 0.15]
"""
import argparse
import json
import subprocess
from pathlib import Path

import numpy as np

MODEL = 'mlx-community/whisper-large-v3-turbo'
SR = 16000


def load(path, start, end):
    r = subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-ss', f'{max(0., start):.6f}',
                        '-t', f'{end - max(0., start):.6f}', '-i', path, '-vn', '-ac', '1',
                        '-ar', str(SR), '-f', 's16le', '-'], capture_output=True, check=True)
    return np.frombuffer(r.stdout, np.int16).astype(np.float32) / 32768


def transcribe(audio):
    import mlx_whisper
    # Sans prompt ni contexte : chaque tentative reste littérale.
    r = mlx_whisper.transcribe(audio, path_or_hf_repo=MODEL, language='fr',
                               word_timestamps=True, condition_on_previous_text=False,
                               temperature=0.0, verbose=None)
    words = [{'word': w['word'].strip(), 'start': float(w['start']), 'end': float(w['end'])}
             for s in r.get('segments', []) for w in s.get('words', []) if w['word'].strip()]
    return r.get('text', '').strip(), words


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('sources', type=Path)
    p.add_argument('--out', required=True, type=Path)
    p.add_argument('--pad', type=float, default=0.15,
                   help='Marge audio autour de chaque portion (s), pour ne pas rogner les mots.')
    p.add_argument('--no-open', action='store_true')
    a = p.parse_args()
    doc = json.loads(a.sources.read_text())
    cache_path = a.out.with_suffix('.cache.json')
    cache = json.loads(cache_path.read_text()) if cache_path.exists() else {}
    out = []
    for i, c in enumerate(doc['chunks']):
        src = c.get('audio') or c['camera']
        key = f"{src['path']}|{src['start']:.3f}|{src['end']:.3f}|{a.pad}"
        if key not in cache:
            text, words = transcribe(load(src['path'], src['start'] - a.pad, src['end'] + a.pad))
            cache[key] = {'text': text, 'words': words}
        out.append({'index': i, 'camera': c['camera'], 'audio': src, 'frames': c['frames'],
                    **cache[key]})
        print(f"{i:4d} {src['start']:8.2f} {cache[key]['text']}", flush=True)
    a.out.write_text(json.dumps(out, ensure_ascii=False, indent=1))
    cache_path.write_text(json.dumps(cache, ensure_ascii=False))


if __name__ == '__main__':
    main()
