#!/usr/bin/env python3
"""Lit une timeline Resolve (EDL CMX ou .drt) et écrit les segments à garder et à retirer, en secondes source.

Usage : coupes_resolve.py <fichier.edl|.drt> [--fps 50] [--out coupes.json] --no-open
Les secondes sont dans la base de temps du clip source (le rendu monté que Lucien a coupé).
"""
import argparse, json, re, sys, zipfile, xml.etree.ElementTree as ET

def tc(s, fps):
    h, m, se, f = map(int, s.split(':'))
    return ((h * 60 + m) * 60 + se) * fps + f

def depuis_edl(path, fps):
    segs, clip = [], None
    for line in open(path, encoding='utf-8', errors='ignore'):
        m = re.match(r'^\d{3}\s+\S+\s+(V|A)\s+C\s+(\S+) (\S+) (\S+) (\S+)', line)
        if m and m.group(1) == 'V':
            segs.append((tc(m.group(4), fps) - tc('01:00:00:00', fps), tc(m.group(2), fps), tc(m.group(3), fps)))
        c = re.search(r'FROM CLIP NAME: (.*)', line)
        if c: clip = c.group(1).strip()
    return sorted(segs), clip

def depuis_drt(path, fps):
    z = zipfile.ZipFile(path)
    seq = [n for n in z.namelist() if n.startswith('SeqContainer/') and n.endswith('.xml')][0]
    root = ET.fromstring(z.read(seq))
    items, clip = set(), None
    for e in root.iter():
        k = {c.tag: (c.text or '') for c in e}
        if 'Start' in k and 'Duration' in k and 'In' in k:  # <In/> vide vaut 0 : ne pas le sauter
            items.add((int(k['Start']), int(k['Duration']), int(k['In'] or 0)))
        if e.tag == 'Name' and (e.text or '').lower().endswith(('.mp4', '.mov')): clip = e.text
    debut = min(s for s, _, _ in items)  # la timeline démarre à 01:00:00:00
    return sorted((s - debut, i, i + d) for s, d, i in items), clip

def main():
    p = argparse.ArgumentParser()
    p.add_argument('fichier'); p.add_argument('--fps', type=int, default=50); p.add_argument('--out')
    p.add_argument('--no-open', action='store_true')
    a = p.parse_args()
    segs, clip = (depuis_drt if a.fichier.endswith('.drt') else depuis_edl)(a.fichier, a.fps)
    garder = [[round(i / a.fps, 2), round(o / a.fps, 2)] for _, i, o in segs]
    retirer = [[garder[k][1], garder[k + 1][0]] for k in range(len(garder) - 1) if garder[k + 1][0] > garder[k][1]]
    trous = [(round((r + o - i) / a.fps, 2), round(r2 / a.fps, 2)) for (r, i, o), (r2, _, _) in zip(segs, segs[1:]) if r + o - i != r2]
    res = {'source': clip, 'fps': a.fps, 'garder_s': garder, 'retire_s': retirer,
           'duree_finale_s': round(sum(o - i for _, i, o in segs) / a.fps, 2), 'trous_timeline': trous}
    out = json.dumps(res, indent=1, ensure_ascii=False)
    open(a.out, 'w').write(out) if a.out else print(out)
    print(f'{len(garder)} segments, {round(sum(b - a_ for a_, b in retirer), 2)} s retirées, trous {trous}', file=sys.stderr)

if __name__ == '__main__':
    main()
