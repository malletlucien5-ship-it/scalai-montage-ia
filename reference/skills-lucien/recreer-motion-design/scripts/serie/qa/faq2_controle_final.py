"""Contrôles de livraison FAQ2 v4 -> work/controles.json (repris dans rapport.json).
Décodage complet, nombre d'images, synchro audio/vidéo, aucune entrée de scène ni coupe dans un mot,
fin du dernier mot audible, sonie."""
import json, re, subprocess, sys
import numpy as np, soundfile as sf

D = '/srv/faq-v4/2-difference/'
MASTER = D + 'FAQ-2-v4.mp4'
APERCU = D + 'FAQ-2-v4-apercu-1080p.mp4'
props = json.load(open(D + 'props.json'))
tr = json.load(open(D + 'work/transcript-sortie.json'))['words']  # temps de sortie
voix = json.load(open(D + 'work/audio/voix-v4.json'))
TOTAL = props['total']
res = {}


def run(*a):
    return subprocess.run(a, capture_output=True, text=True)


def probe(f):
    j = json.loads(run('ffprobe', '-v', 'error', '-count_frames', '-show_entries',
                       'stream=codec_type,codec_name,width,height,r_frame_rate,nb_read_frames,sample_rate,channels,duration:format=duration',
                       '-of', 'json', f).stdout)
    return j


for nom, f in (('master', MASTER), ('apercu', APERCU)):
    j = probe(f)
    v = next(s for s in j['streams'] if s['codec_type'] == 'video')
    a = next(s for s in j['streams'] if s['codec_type'] == 'audio')
    err = run('ffmpeg', '-v', 'error', '-i', f, '-f', 'null', '-').stderr.strip()
    res[nom] = {'video': {k: v.get(k) for k in ('codec_name', 'width', 'height', 'r_frame_rate', 'nb_read_frames', 'duration')},
                'audio': {k: a.get(k) for k in ('codec_name', 'sample_rate', 'channels', 'duration')},
                'images_attendues': int(round(TOTAL * 50)),
                'images_ok': int(v['nb_read_frames']) == int(round(TOTAL * 50)),
                'decodage_complet_erreurs': err.count('\n') + 1 if err else 0,
                'ecart_duree_audio_video_s': round(float(a['duration']) - float(v['duration']), 4)}

# Synchro : la piste du master est-elle calée sur la voix ? (corrélation sur 4 fenêtres)
run('ffmpeg', '-v', 'error', '-y', '-i', MASTER, '-vn', '-ac', '1', '-ar', '48000', '-c:a', 'pcm_f32le', D + 'work/audio/master.wav')
m, sr = sf.read(D + 'work/audio/master.wav')
vv, _ = sf.read(D + 'work/audio/voix-coupee.wav')
dec = []
for t in (20, 80, 160, 230):
    a = m[int(t * sr): int((t + 2) * sr)]
    best = max(range(-2400, 2400, 2), key=lambda d: float(a @ vv[int(t * sr) + d: int((t + 2) * sr) + d]))
    dec.append(round(best / sr * 1000, 2))
res['synchro_voix_master_ms'] = dec

# Image : la vidéo suit-elle la voix ? Comparaison de la dernière image de la plaque et de la 1re de la suite (raccord 306,68)
# -> contrôle visuel dans controles/raccord-image.png ; ici on vérifie qu'aucune image n'est noire en fin de vidéo.
y = run('ffmpeg', '-v', 'error', '-ss', str(TOTAL - 0.5), '-i', MASTER, '-vf', 'signalstats,metadata=print:key=lavfi.signalstats.YAVG', '-f', 'null', '-').stderr
yavg = [float(x) for x in re.findall(r'YAVG=([0-9.]+)', y)]
res['fin_luminance_moyenne_min'] = round(min(yavg), 1) if yavg else None

# Aucune coupe ni entrée de scène dans un mot (temps du montage = temps de sortie, aucune coupe de plaque)
dans_mot = []
bornes = [s['s'] for s in props['scenes'][1:]]
for sc in props['scenes']:
    for p in sc.get('plans') or []:
        bornes.append(p['s'])
for b in bornes:
    for w in tr:
        if w['s'] + 0.02 < b < w['e'] - 0.02:
            dans_mot.append({'t': b, 'mot': w['w'], 'mot_s': w['s'], 'mot_e': w['e']})
res['entrees_de_scene'] = len(bornes)
res['entrees_dans_un_mot'] = dans_mot
res['coupes_plaque'] = props['plateSegs']
# Coupes de Lucien : sous-titre à cheval, clic sur la piste finale (saut d'échantillon au point de coupe ±2 ms)
res['coupes_sortie'] = props['coupes_sortie']
res['sous_titres_a_cheval_coupe'] = [(ph['s'], ph['e']) for ph in props['phrases'] for c in props['coupes_sortie'] if ph['s'] < c - 1e-6 and ph['e'] > c + 1e-6]
dm = np.abs(np.diff(m))
res['clic_aux_coupes'] = [{'t': c, 'saut_max_2ms': round(float(dm[int(c * sr) - 96: int(c * sr) + 96].max()), 4)} for c in props['coupes_sortie']]
res['saut_reference_parole_p999'] = round(float(np.percentile(dm[int(60 * sr): int(70 * sr)], 99.9)), 4)
res['raccord_voix'] = {k: voix[k] for k in ('raccord_s', 'fondu_raccord_ms', 'extinction_s', 'total_s', 'saut_max_autour_raccord', 'saut_max_fin', 'saut_p999_parole_300_306')}
res['raccord_voix']['note'] = ("Le raccord 306,55 s tombe dans « vous » : même prise (montage puis suite brute calée à 4 ms), "
                               "fondu de 20 ms à niveaux égaux, pas une coupe de montage.")

# Fin du dernier mot audible
db = lambda s: 20 * np.log10(np.sqrt((s ** 2).mean()) + 1e-12)
fin = {('%.2f' % t): round(db(m[int(t * sr): int((t + 0.02) * sr)]), 1) for t in np.arange(TOTAL - 0.60, TOTAL - 0.01, 0.04)}
res['fin_master_db_20ms'] = fin
dernier = tr[-1]
ext = voix['extinction_s'] - 306.68 + props['suite']['out']
res['dernier_mot'] = {'mot': dernier['w'], 's': dernier['s'], 'extinction_voix_s': round(ext, 3),
                      'marge_apres_extinction_s': round(TOTAL - ext, 3)}

# Sonie
def lufs(f, extra=()):
    o = run('ffmpeg', '-hide_banner', '-i', f, *extra, '-af', 'ebur128=peak=true', '-f', 'null', '-').stderr
    i = re.findall(r'I:\s+(-?[0-9.]+) LUFS', o)[-1]
    tp = re.findall(r'Peak:\s+(-?[0-9.]+) dBFS', o)[-1]
    return float(i), float(tp)
res['sonie_master_lufs'], res['crete_master_dbtp'] = lufs(MASTER)
# voix seule avec le même gain que la normalisation finale (passe 1 de mix.py)
o = run('ffmpeg', '-hide_banner', '-i', D + 'work/audio/mix-v4.wav', '-af', 'loudnorm=I=-15.76:TP=-1.5:LRA=11:print_format=json', '-f', 'null', '-').stderr
off = float(json.loads(o[o.rindex('{'):o.rindex('}') + 1])['target_offset'])
vo = run('ffmpeg', '-hide_banner', '-i', D + 'work/audio/voix-coupee.wav', '-af', f'aformat=channel_layouts=stereo,volume={off}dB,ebur128', '-f', 'null', '-').stderr
res['sonie_voix_seule_lufs'] = float(re.findall(r'I:\s+(-?[0-9.]+) LUFS', vo)[-1])
json.dump(res, open(D + 'work/controles.json', 'w'), ensure_ascii=False, indent=1)
print(json.dumps({k: v for k, v in res.items() if k not in ('fin_master_db_20ms',)}, ensure_ascii=False, indent=1))
