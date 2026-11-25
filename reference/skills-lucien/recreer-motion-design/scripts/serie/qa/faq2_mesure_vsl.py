import sys, numpy as np
from PIL import Image
im = np.asarray(Image.open(sys.argv[1]).convert('RGB')).astype(int)
H, W, _ = im.shape
r, g, b = im[..., 0], im[..., 1], im[..., 2]
blue = (b > 200) & (r < 90) & (g > 50) & (g < 140) & (b - r > 150)
white = (r > 235) & (g > 235) & (b > 235)
ys, xs = np.nonzero(blue)
print('frame', W, H)
if len(ys):
    core = im[blue]
    print('bleu: n=%d median RGB=%s  #%02X%02X%02X' % (len(ys), np.median(core, 0), *np.median(core, 0).astype(int)))
    print('bleu bbox x %d-%d y %d-%d' % (xs.min(), xs.max(), ys.min(), ys.max()))
# white text rows in bottom half
rows = white[H // 2:].sum(1)
on = np.nonzero(rows > 15)[0] + H // 2
if len(on):
    grp = np.split(on, np.nonzero(np.diff(on) > 3)[0] + 1)
    for gp in grp:
        if len(gp) > 10:
            cols = np.nonzero(white[gp[0]:gp[-1] + 1].sum(0) > 2)[0]
            print('ligne blanche y %d-%d (h=%d, centre %.1f = %.3f H) x %d-%d' % (gp[0], gp[-1], gp[-1] - gp[0] + 1, (gp[0] + gp[-1]) / 2, (gp[0] + gp[-1]) / 2 / H, cols.min(), cols.max()))
