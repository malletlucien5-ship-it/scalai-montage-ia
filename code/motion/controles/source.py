"""Contrôles du code de rendu (Remotion), avant ou après le rendu.

- polices : chaque fontFamily appartient aux polices du chantier et son fichier existe
  (Inter au lieu d'Helvetica le 15/10, Liberation Sans faute de fichier le 19/10, DejaVu le 10/10).
- modeles : aucun nom de modèle périmé à l'écran (Opus 4.7 le 15/10). Liste : modeles-actuels.json.
- liens : aucun lien symbolique dans public/ (bundle Remotion en 404 les 13 et 15/10)."""
import json, os, re, subprocess

from .commun import Resultat

ICI = os.path.dirname(os.path.abspath(__file__))
EXT_CODE = ('.ts', '.tsx', '.js', '.jsx', '.json', '.css')
IGNORE = {'node_modules', '.git', 'build', 'dist', 'out', '.remotion'}


def _fichiers(racine, ext):
    for r, ds, fs in os.walk(racine):
        ds[:] = [d for d in ds if d not in IGNORE]
        for f in fs:
            if f.endswith(ext):
                yield os.path.join(r, f)


def polices(racine, autorisees):
    vues = {}
    rx = re.compile(r"""fontFamily\s*[:=]\s*[`'"]([^`'"]+)[`'"]|font-family\s*:\s*([^;}{]+)""")
    for f in _fichiers(racine, EXT_CODE):
        with open(f, errors='ignore') as fh:
            texte = fh.read()
        for m in rx.finditer(texte):
            premiere = (m[1] or m[2]).split(',')[0].strip().strip('"\'')
            if premiere and not premiere.startswith(('var(', '${', 'inherit', 'system-ui')):
                vues.setdefault(premiere, os.path.relpath(f, racine))
    norm = lambda s: re.sub(r'[\s_-]', '', s.lower())
    hors = {p: f for p, f in vues.items() if not any(norm(p).startswith(norm(a)) for a in autorisees)}
    fichiers_polices = [os.path.basename(f) for f in _fichiers(racine, ('.ttf', '.otf', '.woff', '.woff2'))]
    # 31/10/2026 : Roboto servie par @fontsource vit dans node_modules, ignoré par _fichiers (master viral X refusé à tort).
    for r, ds, _ in os.walk(racine):
        fs = os.path.join(r, 'node_modules', '@fontsource')
        if os.path.isdir(fs):
            fichiers_polices += os.listdir(fs)
        ds[:] = [d for d in ds if d not in IGNORE]
    try:
        fc = subprocess.run(['fc-list', ':', 'family'], capture_output=True, text=True).stdout
    except OSError:
        fc = ''
    absentes = [a for a in autorisees
                if not any(norm(a) in norm(x) for x in fichiers_polices) and norm(a) not in norm(fc)]
    ok = not hors and not absentes
    detail = f"{len(vues)} police(s) citée(s)"
    if hors:
        detail += ' ; hors chantier : ' + ', '.join(f"{p} ({f})" for p, f in list(hors.items())[:5])
    if absentes:
        detail += ' ; fichier introuvable : ' + ', '.join(absentes)
    return Resultat('polices', ok, detail=detail, defauts={'hors': hors, 'absentes': absentes})


def modeles(racine, liste=None, acceptes=()):
    """acceptes : noms gardés par décision écrite de Lucien (chantier.json, valides.modeles)."""
    with open(liste or os.path.join(ICI, 'modeles-actuels.json')) as fh:
        d = json.load(fh)
    rx = re.compile(d['perimes'], re.I)
    trouves = []
    for f in _fichiers(racine, EXT_CODE + ('.md', '.txt', '.srt', '.vtt')):
        if 'modeles-actuels' in f:
            continue
        with open(f, errors='ignore') as fh:
            for n, l in enumerate(fh, 1):
                m = rx.search(l)
                if m and m[0] not in acceptes:
                    trouves.append(f"{os.path.relpath(f, racine)}:{n} « {m[0]} »")
    return Resultat('modèles périmés', not trouves, detail=f"{len(trouves)} mention(s)" + ''.join(f" ; {t}" for t in trouves[:5]),
                    defauts=trouves)


def liens(racine):
    pub = os.path.join(racine, 'public')
    trouves = [os.path.relpath(os.path.join(r, x), racine) for r, ds, fs in os.walk(pub) for x in ds + fs
               if os.path.islink(os.path.join(r, x))] if os.path.isdir(pub) else []
    return Resultat('liens symboliques', not trouves, detail=f"{len(trouves)} lien(s) dans public/" + ''.join(f" ; {t}" for t in trouves[:5]),
                    defauts=trouves)
