#!/usr/bin/env python3
"""Préparer un seul rush complet dès sa disponibilité, sans attendre les autres."""
import argparse
import json
from pathlib import Path
import subprocess
import sys


def duration(path):
    return float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration',
                                         '-of','default=nw=1:nk=1',str(path)]))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',required=True,type=Path)
    parser.add_argument('--out',required=True,type=Path)
    parser.add_argument('--kind',choices=['audio','transcript'],default='audio')
    parser.add_argument('--reuse-verified',action='store_true')
    parser.add_argument('--verified-stats',help='Signatures source et sortie relevées après leur validation initiale.')
    parser.add_argument('--no-open',action='store_true')
    args=parser.parse_args(); args.out.parent.mkdir(parents=True,exist_ok=True)
    if args.reuse_verified:
        expected=json.loads(args.verified_stats) if args.verified_stats else None
        actual=[]
        for path in (args.source,args.out):
            actual.append([path.stat().st_size,path.stat().st_mtime_ns] if path.exists() else None)
        args.reuse_verified=expected==actual
    if args.kind=='audio':
        source_duration=duration(args.source)
        if args.reuse_verified and args.out.exists() and abs(duration(args.out)-source_duration)<.1:
            print('Audio existant vérifié.'); return
        before=args.source.stat()
        tmp=args.out.with_suffix('.partial.wav')
        subprocess.run(['ffmpeg','-nostdin','-v','error','-y','-i',str(args.source),'-map','0:a:0',
                        '-vn','-ac','1','-ar','16000',str(tmp)],check=True)
        after=args.source.stat()
        if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):
            raise RuntimeError('Source encore en transfert.')
        if abs(duration(tmp)-source_duration)>.1: raise RuntimeError('Extraction audio incomplète.')
        tmp.replace(args.out)
    else:
        if args.reuse_verified and args.out.exists():
            data=json.loads(args.out.read_text())
            if data.get('complete') and data.get('model')=='small' and abs(data['duration']-duration(args.source))<.1:
                print('Transcription existante vérifiée.'); return
        subprocess.run([sys.executable,str(Path(__file__).with_name('transcribe_cpu.py')),str(args.source),
                        '--out',str(args.out),'--model','small','--threads','2'],check=True)


if __name__=='__main__': main()
