"""Voix coupée selon props.json (plateSegs) : segments de work/audio/voix-v4.wav mis bout à bout,
fondu de 15 ms (demi-cosinus) en sortie et en entrée de chaque coupe : aucune durée changée, aucun clic.
Écrit work/audio/voix-coupee.wav et work/audio/voix-coupee.json (sauts d'échantillon aux coupes)."""
import json, numpy as np, soundfile as sf
D = '/srv/faq-v4/2-difference/'
p = json.load(open(D + 'props.json'))
v, sr = sf.read(D + 'work/audio/voix-v4.wav')
F = int(0.015 * sr)
ramp = np.sin(np.linspace(0, np.pi / 2, F)) ** 2
parts = []
segs = p['plateSegs']
for k, sg in enumerate(segs):
    a = int(round(sg['src'] * sr)); n = int(round(sg['dur'] * sr))
    x = v[a:a + n].copy()
    if len(x) < n: x = np.concatenate([x, np.zeros(n - len(x))])
    if k > 0: x[:F] *= ramp
    if k < len(segs) - 1: x[-F:] *= ramp[::-1]
    parts.append(x)
out = np.concatenate(parts)
n_tot = int(round(p['total'] * sr))
out = out[:n_tot] if len(out) >= n_tot else np.concatenate([out, np.zeros(n_tot - len(out))])
sf.write(D + 'work/audio/voix-coupee.wav', out.astype(np.float32), sr, subtype='FLOAT')
d = np.abs(np.diff(out))
res = {'duree': len(out) / sr, 'coupes': []}
for c in p['coupes_sortie']:
    i = int(round(c * sr))
    res['coupes'].append({'t': c, 'saut_max_10ms': round(float(d[i - 480:i + 480].max()), 4),
                          'niveau_avant_db': round(float(20 * np.log10(np.sqrt((out[i - 960:i - 480] ** 2).mean()) + 1e-12)), 1),
                          'niveau_apres_db': round(float(20 * np.log10(np.sqrt((out[i + 480:i + 960] ** 2).mean()) + 1e-12)), 1)})
res['saut_p999_parole'] = round(float(np.percentile(d[int(100 * sr):int(110 * sr)], 99.9)), 4)
json.dump(res, open(D + 'work/audio/voix-coupee.json', 'w'), indent=1)
print(json.dumps(res, indent=1))
