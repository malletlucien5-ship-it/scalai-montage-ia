#!/usr/bin/env python3
"""Génère les manifestes privés v4 (GET/PUT signés 72 h) pour l'Asus. --no-open : n'ouvre jamais rien."""
import json, sys, os, datetime
sys.path.insert(0, os.path.expanduser('~/CODE/martell-motion-cloud/cloud'))
from storage_gateway import signed_url
T = 259200
B = 'backups/faq-precall'
V3 = 'outputs/faq-precall/2026-10-06-v3'
OUT = 'outputs/faq-precall/2026-10-07-v4'
JOB = 'jobs/faq-v4-20261007'
FAQ = {'1-temps': 1, '2-difference': 2, '3-metier': 3, '4-risque': 4}
commun_get = {
  'brief/BRIEF-V4.md': f'{JOB}/BRIEF-V4.md',
  'brief/GUIDE-MONTAGE-v2.md': f'{B}/GUIDE-MONTAGE.md',
  'brief/script.md': f'{B}/script.md',
  'refs/references-locales.tgz': 'jobs/faq-v3-20261006/references-locales.tgz',
  'refs/skill-recreer-motion-design.tgz': 'jobs/faq-v3-20261006/skill-recreer-motion-design.tgz',
  'sound/musique/trace_lennon-hutton.wav': f'{B}/sound/musique/trace_lennon-hutton.wav',
  'commun/controle.py': f'{B}/commun/controle.py', 'commun/mix.py': f'{B}/commun/mix.py',
  'commun/plan.py': f'{B}/commun/plan.py', 'commun/completer_mots.py': f'{B}/commun/completer_mots.py',
  'commun/rendre.sh': f'{B}/commun/rendre.sh',
}
for s in 'clic frappe-clavier impact-alt impact notification pop scintillement tictac whoosh zoom'.split():
    commun_get[f'sound/sfx/{s}.wav'] = f'{B}/sound/sfx/{s}.wav'
exp = (datetime.datetime.utcnow() + datetime.timedelta(seconds=T)).strftime('%Y-%m-%dT%H:%M:%SZ')
index = {}
for v, n in FAQ.items():
    get = dict(commun_get)
    for f in ['montage.mp4', 'FAQ.mp4', 'props.json', 'build_props.py', 'mix.wav', 'words.json', 'words-complet.json', 'brolls.json', 'RAPPORT-PLAN.md']:
        get[f'faq/{f}'] = f'{B}/{v}/{f}'
    get['faq/bundle-v2.tgz'] = f'jobs/anthropic-cloud-20261005/{v}/bundle.tgz'
    get['faq/v2-rapport.json'] = f'outputs/faq-precall/2026-10-05-anthropic-cloud/{v}/rapport.json'
    d = f'{V3}/{v}/design/faq{n}'
    for f in ['design.tgz', 'plan.md', 'plan.json', 'extraits.mp4', 'planche-etats.jpg']:
        get[f'v3/{f}'] = f'{d}/{f}'
    get['v3/props-v3.json'] = f'{V3}/{v}/props-v3.json'
    get['v3/essai-10s.mp4'] = f'{V3}/{v}/essai-10s.mp4'
    put = {}
    for f in [f'FAQ-{n}-v4.mp4', f'FAQ-{n}-v4-apercu-1080p.mp4', 'intro-extrait.mp4', 'planche.jpg', 'rapport.json', 'etat.json', 'sources-v4.tgz', 'transcript.json', 'plan.md', 'intro-extrait-v2.mp4', 'planche-v2.jpg']:
        put[f] = f'{OUT}/{v}/{f}'
    m = {'version': 'faq-v4', 'faq': n, 'video': v, 'expire_utc': exp, 'prefixe_ecriture': f'{OUT}/{v}/',
         'get': {k: {'cle': c, 'url': signed_url(c, 'GET', T)} for k, c in get.items()},
         'put': {k: {'cle': c, 'url': signed_url(c, 'PUT', T)} for k, c in put.items()},
         'note': 'Liens privés. Ne jamais les écrire dans Git, un log ou un rapport. Certaines clés v3 peuvent manquer (404) : ignorer.'}
    p = f'manifestes/faq-{v}.json'
    json.dump(m, open(p, 'w'), indent=1, ensure_ascii=False)
    index[v] = signed_url(f'{JOB}/manifestes/faq-{v}.json', 'GET', T)
json.dump(index, open('manifestes/index-prive.json', 'w'), indent=1)
print('ok', exp)
