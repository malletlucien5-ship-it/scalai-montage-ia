import subprocess, numpy as np
from faster_whisper import WhisperModel
raw=subprocess.run(["ffmpeg","-v","error","-i","fin16k.wav","-f","s16le","-"],capture_output=True).stdout
a=np.frombuffer(raw,np.int16).astype(np.float32)/32768
m=WhisperModel("large-v3-turbo",device="cpu",compute_type="int8",cpu_threads=8)
s,_=m.transcribe(a,language="fr",word_timestamps=True)
for x in s:
    for w in x.words: print(f"{281.8+w.start:.3f}-{281.8+w.end:.3f} {w.word} p={w.probability:.2f}")
