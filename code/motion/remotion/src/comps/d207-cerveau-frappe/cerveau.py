# Cerveau filaire procédural (vue latérale, front à gauche), coordonnées plein cadre 1920x1080.
import numpy as np
from scipy.spatial import Voronoi
rng = np.random.default_rng(7)

def catmull(pts, n=12, closed=True):
    P = np.array(pts, float)
    if closed: P = np.vstack([P[-1], P, P[0], P[1]])
    else: P = np.vstack([P[0], P, P[-1]])
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i-1], P[i], P[i+1], P[i+2]
        for t in np.linspace(0, 1, n, endpoint=False):
            t2, t3 = t*t, t*t*t
            out.append(0.5*((2*p1) + (-p0+p2)*t + (2*p0-5*p1+4*p2-p3)*t2 + (-p0+3*p1-3*p2+p3)*t3))
    if not closed: out.append(P[-2])
    return np.array(out)

def inside(poly, pts):
    x, y = pts[:, 0], pts[:, 1]
    res = np.zeros(len(pts), bool)
    xs, ys = poly[:, 0], poly[:, 1]
    j = len(poly) - 1
    for i in range(len(poly)):
        c = ((ys[i] > y) != (ys[j] > y)) & (x < (xs[j]-xs[i])*(y-ys[i])/(ys[j]-ys[i]+1e-9)+xs[i])
        res ^= c; j = i
    return res

def path(pts, closed=False):
    s = 'M' + ' L'.join(f'{p[0]:.1f},{p[1]:.1f}' for p in pts)
    return s + ('Z' if closed else '')

# Contour du cerveau (cortex)
cortex_ctrl = [(398,470),(412,360),(455,262),(530,178),(640,108),(780,58),(930,38),(1080,48),(1215,88),(1335,158),(1432,258),(1492,370),(1506,470),(1488,560),(1440,618),(1360,648),(1250,646),(1150,660),(1060,700),(960,712),(860,706),(770,672),(716,628),(640,640),(548,634),(470,600),(420,545)]
cortex = catmull(cortex_ctrl, 10)
# Cervelet
cereb_ctrl = [(1040,690),(1120,650),(1250,648),(1360,660),(1410,720),(1390,800),(1320,860),(1210,880),(1110,850),(1050,790)]
cereb = catmull(cereb_ctrl, 10)
# Tronc cérébral
stem_l = catmull([(1062,700),(1072,800),(1092,900),(1108,1000),(1116,1090)], 10, False)
stem_r = catmull([(1146,860),(1150,930),(1158,1000),(1166,1090)], 10, False)

paths = []
paths.append(('outline', path(cortex, True)))
cb = np.vstack([cereb, cereb[:1]])
cm = ~inside(cortex, cb)
st = None
for i, v in enumerate(list(cm) + [False]):
    if v and st is None: st = i
    if not v and st is not None:
        if i - st > 2: paths.append(('outline', path(cb[st:i])))
        st = None
for st in (stem_l, stem_r):
    st = catmull(st[::3], 4, False)
    st = st[~inside(cereb, st) & ~inside(cortex, st)]
    if len(st) > 2: paths.append(('outline', path(st)))
# Scissure latérale + sillon central (plus marqués)
paths.append(('fiss', path(catmull([(730,630),(820,610),(930,585),(1040,560),(1140,520),(1200,470)], 10, False))))
paths.append(('fiss', path(catmull([(1010,45),(990,140),(1005,240),(960,340),(940,430),(905,540)], 10, False))))

# Gyri : lignes de niveau zéro d'un bruit passe-bande (motif labyrinthe des circonvolutions)
from scipy.ndimage import gaussian_filter
from skimage import measure
G = 3  # pas de la grille en px
gw, gh = 1920 // G, 1100 // G
noise = rng.standard_normal((gh, gw))
field = gaussian_filter(noise, 15 / G) - gaussian_filter(noise, 34 / G)
shrink = cortex.mean(0) + (cortex - cortex.mean(0)) * 0.975
for lvl in [0.0]:
    for cont in measure.find_contours(field, lvl):
        pts = cont[:, ::-1] * G  # (x, y)
        ok = inside(shrink, pts) & ~inside(cereb, pts)
        # découpe en segments à l'intérieur du cortex
        start = None
        for i, v in enumerate(list(ok) + [False]):
            if v and start is None: start = i
            if not v and start is not None:
                seg = pts[start:i]
                if len(seg) > 6:
                    seg = seg[::2]
                    paths.append(('gyr', path(seg)))
                start = None

# Double contour intérieur (bord des gyri)
inner = cortex.mean(0) + (cortex - cortex.mean(0)) * 0.955
seg = len(inner)
i = 0
while i < seg:
    L = rng.integers(8, 22)
    if rng.random() < 0.65:
        paths.append(('gyr', path(inner[i:min(seg, i+L)])))
    i += L + rng.integers(2, 8)

# Lamelles du cervelet : courbes quasi horizontales empilées
for k, yy in enumerate(np.arange(672, 880, 15)):
    xs = np.linspace(1030, 1420, 80)
    ys = yy + 0.00045*(xs-1225)**2*(-1 if yy < 760 else 1)*0.6 + (xs-1225)*0.12
    arc = np.stack([xs, ys], 1)
    arc = arc[inside(cereb, arc) & ~inside(cortex, arc)]
    if len(arc) > 3: paths.append(('cer', path(arc)))
W = {'outline': 4.2, 'fiss': 3.6, 'gyr': 3.4, 'cer': 2.6}
svg = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1920 1080" width="1920" height="1080" fill="none" stroke="#C9D3EA" stroke-linecap="round" stroke-linejoin="round">']
for kind, d in paths:
    svg.append(f'<path d="{d}" stroke-width="{W[kind]}"/>')
svg.append('</svg>')
open('/home/user/martell-motion-cloud/remotion/public/d207/cerveau.svg', 'w').write('\n'.join(svg))
print(len(paths), 'paths')
