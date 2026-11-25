#!/usr/bin/env python3
"""Audit des mots perdus d'une plaque : chaque mot dit au tournage est dans le rendu, ou sa coupe a une raison admise.
--no-open : n'ouvre rien.

Règle du 09/11/2026 (plaque cabinets v2) : la routine avait tranché des phrases gardées (« je [tiens] juste à préciser »)
et laissé la fin d'une prise retirée (« …extrêmement] utile. »). Son audit ne comparait que les phrases du script.
Lucien : « il y a des putains de mots qui sont coupés ».

Entrées :
  --tournage  mots horodatés du tournage (JSON {words:[…]} ou liste ; temps de la piste transcrite)
  --decalage  secondes à ajouter aux temps du tournage pour passer en temps OBS (calage mesuré)
  --portions  portions.json de la plaque (obs_voix de chaque portion gardée)
  --rendu     mots horodatés du rendu, transcrits AVEC LE MÊME MODÈLE que le tournage
  --sortie    préfixe des rapports (.json et .md)

Classes de coupe admises : silence, begaiement (mêmes mots redits aussitôt), prise_refaite (la suite redit au moins
60 % des mots), phrase_inachevee (phrase entière retirée, finie par « … » ou sans fin, reprise ensuite).
Défauts : TROU (mots retirés au milieu d'une phrase gardée), DEBUT_ORPHELIN (une partie gardée commence par la fin
d'une phrase retirée), FIN_ORPHELINE (une partie gardée finit sur une phrase abandonnée), MOT_TRANCHE (mot gardé
dont plus de 60 ms et plus de 10 % manquent : « elle est inst[able] », plaque v3 cabinets, 09/11/2026, passé car
le seuil de présence était 50 %).
Code 1 si au moins un défaut : la plaque ne part pas.
"""
import argparse, difflib, json, re, sys, unicodedata

FIN = re.compile(r'[.?!…]$')


def mots(path):
    d = json.load(open(path))
    return d['words'] if isinstance(d, dict) else d


def toks(s):
    s = unicodedata.normalize('NFD', (s or '').lower()).encode('ascii', 'ignore').decode()
    return [t for t in re.split(r'[^a-z0-9]+', s) if t]


def presents(tournage, rendu, portions, decalage):
    """Un mot est présent s'il est couvert à plus de 50 % par une portion gardée, ou s'il s'aligne sur le rendu
    ET reste couvert à 15 % au moins. Le texte seul ne suffit pas : la transcription du rendu complète un mot
    dont il ne reste qu'un fragment (« je tiens juste » entendu avec 0,1 s de « tiens » sur 1,56 s, plaque v2)."""
    src = [(n, t) for n, w in enumerate(tournage) for t in toks(w['word'])]
    dst = [t for w in rendu for t in toks(w.get('word', w.get('text', '')))]
    sm = difflib.SequenceMatcher(None, [t for _, t in src], dst, autojunk=False)
    vus = set()
    for a, _, size in sm.get_matching_blocks():
        vus.update(src[x][0] for x in range(a, a + size))
    garde = sorted(tuple(p['obs_voix']) for p in portions)
    def couvert(w):
        a, b = w['start'] + decalage, w['end'] + decalage
        if b <= a:
            return 1.0 if any(x <= a <= y for x, y in garde) else 0.0
        return sum(max(0, min(b, y) - max(a, x)) for x, y in garde) / (b - a)
    presents.couverture = [couvert(w) for w in tournage]
    return [couvert(w) > 0.5 or (n in vus and couvert(w) >= 0.15) for n, w in enumerate(tournage)]


def classer(tournage, P):
    rapports, n = [], len(tournage)
    i = 0
    while i < n:
        if P[i]:
            i += 1
            continue
        j = i
        while j < n and not P[j]:
            j += 1
        retire = [t for k in range(i, j) for t in toks(tournage[k]['word'])]
        suite = [t for k in range(j, min(n, j + 3 * (j - i) + 10)) for t in toks(tournage[k]['word'])]
        debut_phrase = i == 0 or bool(FIN.search(tournage[i - 1]['raw'].strip()))
        fin_phrase = bool(FIN.search(tournage[j - 1]['raw'].strip())) or tournage[j - 1]['raw'].rstrip().endswith('...')
        repris = difflib.SequenceMatcher(None, retire, suite, autojunk=False)
        part = sum(b.size for b in repris.get_matching_blocks()) / max(1, len(retire))
        if not retire:
            cl = 'silence'
        elif suite[:len(retire)] == retire:
            cl = 'begaiement'
        elif not debut_phrase and j < n and P[j] and not fin_phrase and part < 0.6:
            cl = 'TROU'
        elif part >= 0.6 and debut_phrase:
            cl = 'prise_refaite'
        elif debut_phrase and fin_phrase:
            cl = 'phrase_inachevee'
        elif debut_phrase:
            cl = 'prise_refaite' if part >= 0.4 else 'phrase_inachevee'
        else:
            cl = 'TROU'
        if cl != 'TROU' and j < n and P[j] and not fin_phrase and tournage[j]['raw'][:1].islower() and len(retire) > 4:
            cl = 'DEBUT_ORPHELIN'
        rapports.append({'debut': i, 'fin': j, 'obs': None, 'classe': cl, 'texte': ' '.join(tournage[k]['raw'] for k in range(i, j)),
                         'part_redite': round(part, 2)})
        i = j
    # FIN_ORPHELINE : partie gardée finie par « ... » et suivie d'une coupe
    i = 0
    while i < n:
        if not P[i]:
            i += 1
            continue
        j = i
        while j < n and P[j]:
            j += 1
        if j < n and tournage[j - 1]['raw'].rstrip().endswith(('...', '…')):
            rapports.append({'debut': max(i, j - 12), 'fin': j, 'classe': 'FIN_ORPHELINE', 'part_redite': None,
                             'texte': ' '.join(tournage[k]['raw'] for k in range(max(i, j - 12), j))})
        i = j
    # MOT_TRANCHE : mot compté présent mais coupé par un bord de portion. Avec --audio, l'énergie de la voix
    # confirme la coupe (les horodatages de la transcription débordent souvent de 0,1 à 0,3 s) ; sans --audio, le défaut reste strict.
    C = getattr(presents, 'couverture', None) or []
    E = getattr(classer, 'energie', None)
    for k, c in enumerate(C):
        w = tournage[k]
        d = max(0.0, w['end'] - w['start'])
        if P[k] and c < 0.9 and (1 - c) * d > 0.06 and (E is None or E(k)):
            rapports.append({'debut': k, 'fin': k + 1, 'classe': 'MOT_TRANCHE', 'part_redite': round(c, 2),
                             'texte': w['raw']})
    return sorted(rapports, key=lambda r: r['debut'])


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--tournage', required=True)
    ap.add_argument('--decalage', type=float, required=True)
    ap.add_argument('--portions', required=True)
    ap.add_argument('--rendu', default=None, help='facultatif : sans lui, seuls les temps des portions comptent (le plus strict)')
    ap.add_argument('--sortie', required=True)
    ap.add_argument('--audio', help="voix OBS en PCM s16le mono 16 kHz (ffmpeg -ac 1 -ar 16000 -f s16le) : confirme MOT_TRANCHE sur l'énergie")
    ap.add_argument('--reference', '--plaque-coupee', dest='reference', help='portions.json de la plaque sur laquelle Lucien a coupé : ses retraits sont admis (coupe_lucien)')
    ap.add_argument('--admis', help="JSON [{obs, raison}] : défauts relus et admis, à 0,1 s près (raison écrite obligatoire)")
    ap.add_argument('--no-open', action='store_true')
    a = ap.parse_args()
    T = mots(a.tournage)
    pj = json.load(open(a.portions))
    portions = pj['portions'] if isinstance(pj, dict) else pj
    P = presents(T, mots(a.rendu) if a.rendu else [], portions, a.decalage)
    if a.audio:
        import numpy as np
        x = np.fromfile(a.audio, dtype='<i2').astype(np.float32) / 32768
        n = len(x) // 160
        db = 10 * np.log10((x[:n * 160].reshape(n, 160) ** 2).mean(1) + 1e-10)
        debuts = [p['obs_voix'][0] for p in portions]; fins = [p['obs_voix'][1] for p in portions]
        # Seuls les vrais sauts comptent : une fin suivie d'un début au même instant est un raccord continu.
        fins_saut = [f for f in fins if not any(abs(f - d) < 0.03 for d in debuts)]
        debuts_saut = [d for d in debuts if not any(abs(f - d) < 0.03 for f in fins)]
        def ener(t):
            i = int(round(t * 100)); return db[i] if 0 <= i < n else -100.0
        def fort(t0, t1):
            return any(ener(t) > -35 for t in np.arange(t0, t1, 0.01))
        def confirme(k):
            ws, we = T[k]['start'] + a.decalage, T[k]['end'] + a.decalage
            if any(ws < b < we and we - b > 0.06 and (ener(b) > -40 or fort(b, min(we, b + 0.15))) for b in fins_saut):
                return True
            return any(ws < b < we and b - ws > 0.06 and (ener(b) > -40 or fort(max(ws, b - 0.15), b)) for b in debuts_saut)
        classer.energie = confirme
    R = classer(T, P)
    if a.reference:
        pr = json.load(open(a.reference)); pr = pr['portions'] if isinstance(pr, dict) else pr
        Pref = presents(T, [], pr, a.decalage)
        bref = [v for p in pr for v in p['obs_voix']]
        for r in R:
            if r['classe'] in ('TROU', 'DEBUT_ORPHELIN', 'FIN_ORPHELINE') and all(Pref[k] for k in range(r['debut'], r['fin'])):
                r['classe'] = 'coupe_lucien'
            elif r['classe'] == 'MOT_TRANCHE':
                ws, we = T[r['debut']]['start'] + a.decalage, T[r['debut']]['end'] + a.decalage
                if not any(ws < b < we for b in bref):
                    r['classe'] = 'tranche_par_lucien'
        presents.couverture = None
    for r in R:
        r['obs'] = round(T[r['debut']]['start'] + a.decalage, 2)
    for r in R:
        r['contexte'] = ' '.join((T[k]['raw'] if P[k] else '[' + T[k]['raw'] + ']')
                                 for k in range(max(0, r['debut'] - 8), min(len(T), r['fin'] + 8)))
    if a.admis:
        for x in json.load(open(a.admis)):
            assert x.get('raison'), 'chaque défaut admis porte sa raison'
            for r in R:
                if r['classe'] in ('TROU', 'DEBUT_ORPHELIN', 'FIN_ORPHELINE', 'MOT_TRANCHE') and abs(r['obs'] - x['obs']) <= 0.1:
                    r['classe'] = 'admis'; r['raison'] = x['raison']
    defauts = [r for r in R if r['classe'] in ('TROU', 'DEBUT_ORPHELIN', 'FIN_ORPHELINE', 'MOT_TRANCHE')]
    json.dump({'mots_tournage': len(T), 'mots_presents': sum(P), 'coupes': R, 'defauts': len(defauts)},
              open(a.sortie + '.json', 'w'), ensure_ascii=False, indent=1)
    with open(a.sortie + '.md', 'w') as f:
        f.write(f"# Mots retirés de la plaque\n\n{sum(P)} mots gardés sur {len(T)}. Défauts : {len(defauts)}.\n\n")
        f.write("Entre crochets : mots absents du rendu. Temps en secondes OBS.\n\n")
        for r in R:
            f.write(f"- {r['obs']:.1f} s · **{r['classe']}** · …{r['contexte']}…\n")
    par = {}
    for r in R:
        par[r['classe']] = par.get(r['classe'], 0) + 1
    print('classes :', ', '.join(f'{k} {v}' for k, v in sorted(par.items())))
    for r in defauts[:40]:
        print(f"  {r['classe']:15s} {r['obs']:7.1f} s  …{r['contexte']}…")
    print(f"défauts : {len(defauts)} ; rapport : {a.sortie}.md")
    return 1 if defauts else 0


if __name__ == '__main__':
    sys.exit(main())
