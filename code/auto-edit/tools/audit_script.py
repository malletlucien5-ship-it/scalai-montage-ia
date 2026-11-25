#!/usr/bin/env python3
"""Audit de complétude d'un montage lu sur script.

Chaque phrase du script dite au tournage doit figurer dans le montage. Le texte du montage
vient d'une retranscription de son audio réel (défaut, `--mots` pour l'ancien mode) : les mots
déduits des horodatages du tournage inventent des trous après le nettoyage des creux
(8 faux trous sur AI Advantage, 10/10/2026). Sortie non nulle
si une phrase dite (score tournage ≥ 0,6) manque au montage (score < 0,6). Les phrases
reformulées sortent parfois en faux positif : les relire sur le texte, jamais les ignorer.

  python3 audit_script.py --out DIR --script script.txt [--takes DIR/prise1 DIR/prise2]
"""
import argparse, difflib, json, re, sys, unicodedata
from pathlib import Path


def toks(t):
    t = unicodedata.normalize('NFKD', t.lower()); t = ''.join(c for c in t if not unicodedata.combining(c))
    return re.findall(r'[a-z0-9%]+', t.replace("'", ' ').replace('’', ' '))


def words_of(path):
    w = json.loads(Path(path).read_text())
    w = w['words'] if isinstance(w, dict) else w
    return [x for t in w for x in toks(t.get('word') or t.get('text') or '')]


def score(sent, hay):
    n = len(sent)
    if not n or not hay: return 0.
    win, best = max(n + 4, int(n * 1.6)), 0.
    for i in range(0, max(1, len(hay) - n // 2), 2):
        m = sum(b.size for b in difflib.SequenceMatcher(None, sent, hay[i:i + win], autojunk=False).get_matching_blocks())
        best = max(best, m / n)
    return best


def retranscrire(media):
    """Transcription de l'audio réellement rendu (faster-whisper large-v3-turbo, CPU)."""
    import os, subprocess, tempfile
    from faster_whisper import WhisperModel
    cache = media.with_name(media.stem + '.reel.words.json')
    if cache.exists() and cache.stat().st_mtime > media.stat().st_mtime:
        return words_of(cache)
    with tempfile.TemporaryDirectory() as d:
        wav = Path(d) / 'a.wav'
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(media), '-vn', '-ac', '1', '-ar', '16000', str(wav)], check=True)
        m = WhisperModel('large-v3-turbo', device='cpu', compute_type='int8', cpu_threads=os.cpu_count() or 8)
        segs, _ = m.transcribe(str(wav), language='fr', word_timestamps=True, beam_size=5, condition_on_previous_text=False)
        w = [{'word': x.word.strip(), 'start': x.start, 'end': x.end} for s in segs for x in (s.words or [])]
    cache.write_text(json.dumps(w, ensure_ascii=False))
    return words_of(cache)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--out', type=Path, required=True); p.add_argument('--script', type=Path, required=True)
    p.add_argument('--takes', type=Path, nargs='*'); p.add_argument('--name', default='montage')
    p.add_argument('--mots', action='store_true', help='Utiliser NAME.words.json au lieu de retranscrire.')
    p.add_argument('--no-open', action='store_true')
    a = p.parse_args()
    takes = a.takes or [a.out]
    phrases = [s.strip() for s in re.split(r'(?<=[.!?…:])\s+', a.script.read_text()) if len(toks(s)) >= 4]
    raw = [w for t in takes for w in words_of(t / 'work/multicam.transcache.json')]
    final = words_of(a.out / f'{a.name}.words.json') if a.mots else retranscrire(a.out / f'{a.name}.mp4')
    lost, absent = [], []
    for s in phrases:
        r, f = score(toks(s), raw), score(toks(s), final)
        if r >= 0.6 and f < 0.6: lost.append((s, r, f))
        elif r < 0.6: absent.append((s, r))
    report = {'phrases': len(phrases), 'perdues': [{'phrase': s, 'tournage': round(r, 2), 'montage': round(f, 2)} for s, r, f in lost],
              'non_dites': [{'phrase': s, 'tournage': round(r, 2)} for s, r in absent]}
    (a.out / f'{a.name}.audit-script.json').write_text(json.dumps(report, ensure_ascii=False, indent=1))
    print(f'Phrases du script : {len(phrases)} | dites mais absentes du montage : {len(lost)} | non dites : {len(absent)}')
    for s, r, f in lost: print(f'  [tournage {r:.2f} | montage {f:.2f}] {s}')
    sys.exit(1 if lost else 0)


if __name__ == '__main__':
    main()
