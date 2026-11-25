"""Master livré contre rendus frais (remotion still) aux mêmes images : écart moyen absolu (0-255)
sur l'image entière, le panneau (x < 935 à 1080p) et la moitié de Lucien, et part de pixels très différents (> 40)."""
import json, numpy as np
from PIL import Image
D = '/srv/faq-v4/2-difference/'
T = open(D + 'work/temps-compare.txt').read().split()
props = json.load(open(D + 'props.json'))
def kind(t): return next(s['kind'] for s in props['scenes'] if s['s'] <= t < s['e'])
res = []
for t in T:
    a = np.asarray(Image.open(f'{D}work/stills/masterfr/t{t}.jpg').convert('RGB')).astype(float)
    b = np.asarray(Image.open(f'{D}work/stills/frais/t{t}.jpg').convert('RGB')).astype(float)
    d = np.abs(a - b).mean(2)
    res.append({'t': float(t), 'kind': kind(float(t)), 'ecart_image': round(float(d.mean()), 2), 'ecart_panneau': round(float(d[:, :935].mean()), 2),
                'ecart_lucien': round(float(d[:, 935:].mean()), 2), 'pixels_tres_differents_pct': round(float((d > 40).mean() * 100), 3)})
sp = [r for r in res if r['kind'] == 'slide']
out = {'images': len(res), 'ecran_partage': len(sp),
       'panneau_moyenne': round(float(np.mean([r['ecart_panneau'] for r in sp])), 2), 'panneau_max': max(r['ecart_panneau'] for r in sp),
       'image_moyenne': round(float(np.mean([r['ecart_image'] for r in res])), 2), 'image_max': max(r['ecart_image'] for r in res),
       'pixels_tres_differents_max_pct': max(r['pixels_tres_differents_pct'] for r in res), 'detail': res}
json.dump(out, open(D + 'work/compare-master.json', 'w'), indent=1)
print(json.dumps({k: v for k, v in out.items() if k != 'detail'}, indent=1))
for r in sorted(res, key=lambda r: -r['ecart_image'])[:5]: print(r)
