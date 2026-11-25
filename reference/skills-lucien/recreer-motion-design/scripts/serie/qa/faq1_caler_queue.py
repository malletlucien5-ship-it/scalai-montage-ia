"""Calage de la suite des rushs (in/queue/queue-1-temps.mov) sur la fin de la plaque, par corrélation audio.

Usage : python3 caler_queue.py → affiche le décalage, le gain et la décroissance de la voix ; écrit work/queue-calage.json.
"""
import json, soundfile as sf, numpy as np

v, sr = sf.read('work/voix48.wav'); q, _ = sf.read('work/queue48.wav')
end = len(v) / sr
a, b = int(185.00 * sr), int(185.44 * sr); ref = v[a:b]
N = 1 << int(np.ceil(np.log2(len(q) + len(ref))))
cc = np.fft.irfft(np.fft.rfft(q, N) * np.conj(np.fft.rfft(ref, N)), N)[:len(q) - len(ref)]
cs = np.concatenate([[0], np.cumsum(q ** 2)]); en = np.sqrt(cs[len(ref):] - cs[:-len(ref)])[:len(cc)]
r = cc / (en * np.sqrt(np.dot(ref, ref)) + 1e-12)
lag = int(np.argmax(r[:int(0.4 * sr)]))
off = 185.00 - lag / sr
seg = q[lag:lag + len(ref)]
gain = 20 * np.log10(np.sqrt(np.mean(ref ** 2)) / np.sqrt(np.mean(seg ** 2)))
print('début de la suite (temps plaque)', round(off, 5), 'corrélation', round(float(r[lag]), 3), 'recouvrement', round(end - off, 4), 's')
print('gain plaque/suite', round(gain, 2), 'dB')
w = int(0.02 * sr)
for t in np.arange(185.2, off + len(q) / sr - 0.02, 0.04):
    i = int((t - off) * sr); x = q[i:i + w]
    print(f'{t:.2f} {20*np.log10(np.sqrt(np.mean(x**2))+1e-9):6.1f}', end=' | ')
print()
json.dump({"debut_suite_temps_plaque": off, "correlation": float(r[lag]), "gain_db": gain}, open('work/queue-calage.json', 'w'), indent=1)
