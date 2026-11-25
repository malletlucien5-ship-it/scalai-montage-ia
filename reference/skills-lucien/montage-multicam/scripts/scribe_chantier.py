#!/usr/bin/env python3
"""Mots horodatés ElevenLabs Scribe v3 pour une routine de montage, produits sur le Mac et déposés sur la Storage Box.
--no-open : n'ouvre rien. Aucun calcul de montage sur le Mac : extraction audio puis appel au service.

Décision du 14/11/2026 (Intelligence/decisions/2026-11-14-transcription-elevenlabs-scribe) : 18 min en 24 s,
0,20 $/h, contre plus d'une heure de modèle local sur CPU dans le cloud.

Usage :
  scribe_chantier.py --chantier NOM --cam DJI_1.LRF [DJI_2.LRF ...] --obs OBS.mp4 [--obs-nom obs.mp4] [--sans-envoi]

Sorties dans ~/.local/share/montage-NOM/scribe/ puis sur la Storage Box martell/inputs/NOM/scribe/ :
  mots-camera.json : {"words": [...]} sur la piste caméra concaténée, rushs dans l'ordre donné.
                     La routine le passe à `pipeline.py plan` par AE_WORDS_FILE.
  mots-portions.json : {"obs.mp4": [...]} sur la piste OBS. La routine le passe par AE_SEG_WORDS ;
                     la clé doit être le nom de fichier de l'OBS dans la routine (--obs-nom).
La clé vient de ~/.config/scalai/credentials.env et n'est jamais affichée ni écrite ailleurs.
"""
import argparse, json, os, subprocess, sys, tempfile, time, urllib.request, uuid
from concurrent.futures import ThreadPoolExecutor

MODELE = 'scribe_v3'


def cle():
    for l in open(os.path.expanduser('~/.config/scalai/credentials.env')):
        if l.startswith('ELEVENLABS_API_KEY='):
            return l.split('=', 1)[1].strip().strip('"').strip("'")
    sys.exit('ELEVENLABS_API_KEY absente de credentials.env')


def duree(f):
    return float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', f],
                                capture_output=True, text=True, check=True).stdout)


def scribe(src):
    with tempfile.TemporaryDirectory() as d:
        a = os.path.join(d, 'a.mp3')
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-vn', '-ac', '1', '-ar', '16000', '-b:a', '64k', a], check=True)
        b = uuid.uuid4().hex
        champs = {'model_id': MODELE, 'language_code': 'fra', 'tag_audio_events': 'false', 'timestamps_granularity': 'word'}
        corps = b''.join(f'--{b}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode() for k, v in champs.items())
        corps += f'--{b}\r\nContent-Disposition: form-data; name="file"; filename="a.mp3"\r\nContent-Type: audio/mpeg\r\n\r\n'.encode()
        corps += open(a, 'rb').read() + f'\r\n--{b}--\r\n'.encode()
        for essai in range(1, 4):
            try:
                r = urllib.request.Request('https://api.elevenlabs.io/v1/speech-to-text', data=corps, method='POST',
                                           headers={'xi-api-key': cle(), 'Content-Type': f'multipart/form-data; boundary={b}'})
                rep = json.load(urllib.request.urlopen(r, timeout=900))
                break
            except Exception as e:
                if essai == 3:
                    sys.exit(f'Scribe en échec sur {os.path.basename(src)} : {type(e).__name__} {e}')
                time.sleep(10 * essai)
    return [{'word': w['text'], 'start': float(w['start']), 'end': float(w['end'])}
            for w in rep['words'] if w.get('type') == 'word' and w.get('start') is not None]


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--chantier', required=True)
    p.add_argument('--cam', nargs='+', required=True, help='Rushs caméra dans l ordre (LRF de préférence, même audio que la 4K)')
    p.add_argument('--obs', required=True)
    p.add_argument('--obs-nom', default='obs.mp4', help='Nom de fichier de l OBS dans la routine')
    p.add_argument('--sans-envoi', action='store_true')
    p.add_argument('--no-open', action='store_true')
    a = p.parse_args()
    out = os.path.expanduser(f'~/.local/share/montage-{a.chantier}/scribe')
    os.makedirs(out, exist_ok=True)
    t0 = time.time()
    with ThreadPoolExecutor(4) as ex:
        res = list(ex.map(scribe, a.cam + [a.obs]))
    cam, decal = [], 0.
    for f, mots in zip(a.cam, res[:-1]):
        cam += [{**w, 'start': w['start'] + decal, 'end': w['end'] + decal} for w in mots]
        decal += duree(f)
    json.dump({'modele': MODELE, 'sources': [os.path.basename(f) for f in a.cam], 'words': cam},
              open(f'{out}/mots-camera.json', 'w'), ensure_ascii=False)
    json.dump({a.obs_nom: res[-1]}, open(f'{out}/mots-portions.json', 'w'), ensure_ascii=False)
    print(f'Scribe {MODELE} : caméra {len(cam)} mots, OBS {len(res[-1])} mots, {time.time() - t0:.0f} s')
    if len(res[-1]) < 0.8 * len(cam) or len(cam) < 0.8 * len(res[-1]):
        print('ALERTE : nombres de mots caméra et OBS trop différents, vérifier le calage des sources.')
    if a.sans_envoi:
        return
    env = dict(l.strip().split('=', 1) for l in open(os.path.expanduser('~/.config/scalai/credentials.env')) if l.startswith('MARTELL_STORAGEBOX_'))
    r = f"{env['MARTELL_STORAGEBOX_USER'].strip()}@{env['MARTELL_STORAGEBOX_HOST'].strip()}"
    ssh = f"ssh -i {os.path.expanduser('<cle-ssh-de-lucien>')} -p 23 -o BatchMode=yes -o ConnectTimeout=20"
    dst = f'martell/inputs/{a.chantier}/scribe'
    subprocess.run(ssh.split() + ['-n', r, f'mkdir -p {dst}'], check=True)
    subprocess.run(['/opt/homebrew/bin/rsync', '-t', '-e', ssh, f'{out}/mots-camera.json', f'{out}/mots-portions.json', f'{r}:{dst}/'],
                   check=True, stdin=subprocess.DEVNULL)
    print(f'Déposé sur la Storage Box : {dst}/mots-camera.json et mots-portions.json')


if __name__ == '__main__':
    main()
