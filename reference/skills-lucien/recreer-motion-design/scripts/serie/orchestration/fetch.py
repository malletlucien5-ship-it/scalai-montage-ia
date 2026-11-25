#!/usr/bin/env python3
# Télécharge les GET d'un manifeste dans DIR/in/<clé>. Aucune URL dans la sortie. --no-open.
import json, sys, os, subprocess
d = sys.argv[1]; m = json.load(open(f'{d}/manifeste.json'))
for k, x in m['get'].items():
    p = f'{d}/in/{k}'; os.makedirs(os.path.dirname(p), exist_ok=True)
    if os.path.exists(p) and os.path.getsize(p) > 0: continue
    r = subprocess.run(['curl', '-sf', '--retry', '3', '-o', p, x['url']])
    print(k, 'ok' if r.returncode == 0 else f'ECHEC {r.returncode}', flush=True)
