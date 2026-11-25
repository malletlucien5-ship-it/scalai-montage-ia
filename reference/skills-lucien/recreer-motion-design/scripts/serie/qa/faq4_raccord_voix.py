# Voix complète : plaque jusqu'à 107,35 s, puis suite OBS passée dans la chaîne estimée (FIR 256), fondu enchaîné de 10 ms.
import numpy as np, subprocess, json, wave
def lire(f, ss=None):
    cmd = ['ffmpeg', '-v', 'error'] + (['-ss', str(ss)] if ss is not None else []) + ['-i', f, '-f', 'f32le', '-ac', '1', '-ar', '48000', '-']
    return np.frombuffer(subprocess.run(cmd, capture_output=True).stdout, np.float32).astype(np.float64)
sr = 48000; Q0 = 106.95177; RAC = 107.36; XF = 0.010
pl = lire('voix48k.wav'); q = lire('queueL.wav')
h = np.load('fir256.npy'); D = json.load(open('fir256.json'))['D']
qf = np.convolve(q, h)[D:D + len(q)]  # même convention que l'estimation (np.roll k-D)
db = lambda s: 20 * np.log10(np.sqrt((s ** 2).mean()) + 1e-12)
# extinction de la voix dans la suite filtrée : dernier instant > fond + 6 dB
F = 480
env = np.array([db(qf[i:i + F]) for i in range(0, len(qf) - F, F)])
fond = np.percentile(env[-60:], 50)
t_q = np.arange(len(env)) * F / sr + Q0
voix = [t for t, e in zip(t_q, env) if e > fond + 6 and t > 107.0]
ext = max(voix) + F / sr
# détection automatique perturbée par des bruits de mouvement (108,1 et 108,3 s) : extinction lue sur l'enveloppe du brut (+25 dB)
ext = 107.40
print('fond suite filtrée %.1f dB (plaque : -42,3) ; extinction voix %.3f s' % (fond, ext))
for t, e in zip(t_q, env):
    if 107.28 < t < 107.6: print('  %.2f %.1f' % (t, e))
total = round(np.ceil((ext + 0.4) * 50 - 1e-6) / 50, 2)
n = int(round(total * sr))
out = np.zeros(n)
r = int(round(RAC * sr)); x = int(XF * sr)
out[:r - x // 2] = pl[:r - x // 2]
w = np.linspace(0, 1, x)
iq = lambda t_idx: t_idx - int(round(Q0 * sr))
seg_p = pl[r - x // 2:r - x // 2 + x]; seg_q = qf[iq(r - x // 2):iq(r - x // 2) + x]
out[r - x // 2:r - x // 2 + x] = seg_p * (1 - w) + seg_q * w
reste = qf[iq(r - x // 2 + x):]
m = min(len(reste), n - (r - x // 2 + x))
out[r - x // 2 + x:r - x // 2 + x + m] = reste[:m]
# saut au raccord (clic) : différence d'échantillons max autour du raccord vs dans la plaque
d = np.abs(np.diff(out[r - 2400:r + 2400])); dref = np.abs(np.diff(pl[r - 48000:r - 2400]))
print('pente max au raccord %.4f, pente max 1 s avant %.4f' % (d.max(), dref.max()))
print('total sortie %.2f s (%d images à 50 i/s), suite utilisée jusqu\'à %.3f s de la suite' % (total, round(total * 50), (n - int(Q0 * sr)) / sr))
with wave.open('voix-complete.wav', 'wb') as wf:
    wf.setnchannels(1); wf.setsampwidth(3); wf.setframerate(sr)
    s = np.clip(out, -1, 1 - 2 ** -23); i = (s * 2 ** 23).astype(np.int32)
    wf.writeframes(b''.join(int(v).to_bytes(3, 'little', signed=True) for v in i))
json.dump({'q0_plaque': Q0, 'raccord': RAC, 'fondu_ms': XF * 1000, 'extinction': round(ext, 3), 'total': total,
           'images': int(round(total * 50)), 'fond_suite_db': round(fond, 1)}, open('raccord.json', 'w'), indent=1)
