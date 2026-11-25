import sys, wave, json, numpy as np
from faster_whisper import WhisperModel
wf = wave.open(sys.argv[1]); a = np.frombuffer(wf.readframes(wf.getnframes()), np.int16).astype(np.float32)/32768
m = WhisperModel("large-v3-turbo", device="cpu", compute_type="int8", cpu_threads=8)
for j in json.loads(sys.argv[2]):
    s, e = max(0, j - 2.2), j + 2.2
    segs, _ = m.transcribe(a[int(s*16000):int(e*16000)], language="fr", beam_size=5, word_timestamps=True, condition_on_previous_text=False)
    print(f"jonction {j:.2f} :", ' '.join(f"{w.word.strip()}" + ('|' if abs(w.end + s - j) < 0.12 or (w.start + s < j < w.end + s) else '') for sg in segs for w in sg.words), flush=True)
