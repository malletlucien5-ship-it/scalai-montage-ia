#!/usr/bin/env python3
"""Transcription et VAD ONNX sur serveur CPU, sans interface graphique."""
import argparse
import json
from pathlib import Path
from faster_whisper import WhisperModel
from faster_whisper.audio import decode_audio
from faster_whisper.vad import VadOptions, get_speech_timestamps


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('audio'); p.add_argument('--out',required=True)
    p.add_argument('--model',default='small'); p.add_argument('--threads',type=int,default=2)
    a=p.parse_args()
    audio=decode_audio(a.audio,sampling_rate=16000)
    vad=get_speech_timestamps(audio,VadOptions(threshold=.4,min_silence_duration_ms=220,speech_pad_ms=140))
    out={'model':a.model,'vad':[[x['start']/16000,x['end']/16000] for x in vad],
         'duration':len(audio)/16000,'words':[],'segments':[]}
    Path(a.out).write_text(json.dumps(out,ensure_ascii=False,indent=2))
    model=WhisperModel(a.model,device='cpu',compute_type='int8',cpu_threads=a.threads)
    segments,info=model.transcribe(audio,language='fr',word_timestamps=True,beam_size=1,
                                  vad_filter=True,condition_on_previous_text=False)
    for s in segments:
        out['segments'].append({'start':s.start,'end':s.end,'text':s.text})
        out['words'].extend({'start':w.start,'end':w.end,'text':w.word.strip()} for w in s.words or [])
        Path(a.out).write_text(json.dumps(out,ensure_ascii=False,indent=2))
        print(f'{s.start:.1f}-{s.end:.1f} {s.text}',flush=True)
    out['complete']=True
    Path(a.out).write_text(json.dumps(out,ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
