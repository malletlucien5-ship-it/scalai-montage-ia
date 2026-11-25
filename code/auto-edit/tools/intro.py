"""Introduction depuis une référence muette et les rushs caméra originaux."""
import argparse
import concurrent.futures
import hashlib
import json
import subprocess
from pathlib import Path


def run(args):
    result = subprocess.run(args, capture_output=True)
    if result.returncode:
        raise RuntimeError(result.stderr.decode(errors='replace')[-5000:])
    return result.stdout


def probe(path):
    return json.loads(run(['ffprobe', '-v', 'error', '-count_packets',
        '-show_entries', 'stream=codec_type,nb_read_packets,duration,width,height,avg_frame_rate',
        '-of', 'json', str(path)]))


def validate_spec(spec, fps, total):
    if spec.get('version') != 1 or spec.get('authorized') is not True:
        raise ValueError('Référence autorisée et spécification version 1 requises.')
    frames = round(spec['duration'] * fps)
    if not 0 < frames <= total:
        raise ValueError('Introduction hors de la timeline.')
    start, end = spec['source_seconds']
    if not 0 <= start < end:
        raise ValueError('Intervalle de référence invalide.')
    if not start < spec['crop_switch_seconds'] < end:
        raise ValueError('Changement de cadrage hors de la référence.')
    for crop in spec['reference_crops'] + [spec.get('camera_crop',[1050,100,1800,1800])]:
        if len(crop) != 4 or any(not isinstance(x,int) for x in crop):
            raise ValueError('Crop entier de quatre coordonnées requis.')
        if crop[0] < 0 or crop[1] < 0 or crop[2] <= 0 or crop[3] <= 0:
            raise ValueError('Crop hors des bornes.')
    spans = spec.get('face_seconds', [])
    if any(not start <= a < b <= end for a, b in spans):
        raise ValueError('Plan visage hors de la référence.')
    ratio = frames / fps / (end - start)
    face = [(round((a-start)*ratio*fps), round((b-start)*ratio*fps)) for a,b in spans]
    return frames, ratio, face


def file_stamp(path):
    path = Path(path).resolve()
    st = path.stat()
    return [str(path), st.st_size, st.st_mtime_ns]


def render_camera_tracks(doc, work, crop, size, width, height, hardware):
    """Deux pistes vidéo originales avec un cache propre à chaque portion."""
    fps = doc['fps']
    cache = work / 'camera-cache'
    cache.mkdir(parents=True, exist_ok=True)

    def render(pair):
        chunk, square = pair
        src = chunk['camera']
        n = chunk['frames']
        duration = n / fps
        rate = (src['end']-src['start']) / duration
        dims = [size, size] if square else [width, height]
        payload = [chunk, crop if square else None, dims, hardware, file_stamp(src['path']), 'intro-1']
        key = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:20]
        target = cache / (key + '.mkv')
        if target.exists():
            count = int(probe(target)['streams'][0]['nb_read_packets'])
            if count == n:
                return target
        graph = f'setpts=(PTS-STARTPTS)/{rate:.12f},tpad=stop_mode=clone:stop_duration=1,'
        if square:
            x,y,w,h = crop
            graph += f'crop={w}:{h}:{x}:{y},scale={size}:{size}:flags=lanczos,'
        else:
            graph += (f'scale={width}:{height}:force_original_aspect_ratio=increase:flags=lanczos,'
                f'crop={width}:{height},')
        graph += f'fps={fps},trim=end_frame={n},setpts=N/({fps}*TB),setsar=1,format=yuv420p'
        temp = target.with_suffix('.partial.mkv')
        cmd = ['ffmpeg','-v','error','-nostdin','-y']
        if hardware:
            cmd += ['-hwaccel','videotoolbox']
        cmd += ['-ss',str(src['start']),'-t',str(src['end']-src['start']),'-i',src['path'],
            '-vf',graph,'-an']
        cmd += (['-c:v','h264_videotoolbox','-b:v','6M' if square else '32M','-allow_sw','0']
            if hardware else ['-c:v','libx264','-threads','2','-preset','veryfast','-crf','18'])
        cmd += ['-bf','0','-frames:v',str(n),'-t',str(max(duration,.12)),str(temp)]
        run(cmd)
        if int(probe(temp)['streams'][0]['nb_read_packets']) != n:
            raise RuntimeError('Piste caméra incomplète.')
        temp.replace(target)
        return target

    pairs = [(c,square) for square in (False, True) for c in doc['chunks']]
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        files = list(pool.map(render, pairs))
    n = len(doc['chunks'])
    lists = []
    for tag, selected in [('face',files[:n]),('square',files[n:])]:
        listing = work / (tag+'.concat.txt')
        listing.write_text(''.join("file '"+str(p).replace("'","'\\''")+"'\n" for p in selected))
        lists.append(listing)
    return lists


def build(media, target, spec_path, work, preview=False, hardware=False):
    from pipeline import source_module
    module = source_module()
    media, target, spec_path, work = map(Path, (media,target,spec_path,work))
    if media.resolve() == target.resolve():
        raise ValueError('La sortie doit conserver le média initial.')
    work.mkdir(parents=True, exist_ok=True)
    doc = module.validate(json.loads(media.with_suffix('.sources.json').read_text()))
    spec = json.loads(spec_path.read_text())
    fps, total = doc['fps'], module.frame_count(doc)
    frames, ratio, face = validate_spec(spec,fps,total)
    base_probe = probe(media)
    v = next(s for s in base_probe['streams'] if s['codec_type']=='video')
    if int(v['nb_read_packets']) != total:
        raise ValueError('Le média et sa table des sources divergent.')
    width,height = v['width'],v['height']
    if not preview and doc.get('face_crop') != spec.get('camera_crop',[1050,100,1800,1800]):
        raise ValueError('Rendre le montage avec le nouveau cadrage avant son introduction.')
    output_frames = frames if preview else total
    reference = Path(spec['reference_path'])
    if not reference.is_absolute():
        reference = spec_path.parent/reference
    signature = hashlib.sha256(json.dumps([spec,file_stamp(media),file_stamp(reference),
        doc,preview,hardware,'intro-1'],sort_keys=True).encode()).hexdigest()
    receipt = target.with_suffix('.finish.json')
    if target.exists():
        old = json.loads(receipt.read_text()) if receipt.exists() else {}
        if old.get('signature') == signature and old.get('output_stamp') == file_stamp(target):
            print('Introduction déjà vérifiée :',target,flush=True)
            return target
        raise FileExistsError('Une sortie différente existe déjà : '+str(target))
    work = work / signature[:16]
    work.mkdir(parents=True, exist_ok=True)
    prefix = module.slice_frames(doc,[[0,frames]])
    crop = spec.get('camera_crop',[1050,100,1800,1800])
    size = round(height*.4/2)*2
    margin = 40
    face_list,square_list = render_camera_tracks(prefix,work,crop,size,width,height,hardware)
    mask = work/'rounded-mask.pgm'
    radius = round(size*.08)
    if not mask.exists():
        run(['ffmpeg','-v','error','-nostdin','-y','-f','lavfi','-i',
            f"color=c=white:s={size}x{size},format=gray,geq=lum='255*lte(hypot(X-clip(X,{radius},W-1-{radius}),Y-clip(Y,{radius},H-1-{radius})),{radius})'",
            '-frames:v','1',str(mask)])
    prepared = work/'reference.mp4'
    if not prepared.exists():
        start,end = spec['source_seconds']
        split = spec['crop_switch_seconds']
        crops = spec['reference_crops']
        parts=[]
        for index,(a,b) in enumerate([(start,split),(split,end)]):
            x,y,w,h=crops[index]
            parts.append(f'[r{index}]trim=start={a}:end={b},setpts=PTS-STARTPTS,'
                f'crop={w}:{h}:{x}:{y},scale=1600:900:flags=lanczos,setsar=1[p{index}]')
        graph='[0:v]split=2[r0][r1];'+';'.join(parts)+';[p0][p1]concat=n=2:v=1:a=0[v]'
        cmd=['ffmpeg','-v','error','-nostdin','-y','-i',str(reference),'-filter_complex',graph,
            '-map','[v]','-an','-c:v','libx264','-threads','2','-preset','veryfast','-crf','18',str(prepared)]
        run(cmd)
    enable = '+'.join(f'between(n,{a},{b-1})' for a,b in face) or '0'
    graph=(f'[1:v]setpts=(PTS-STARTPTS)*{ratio:.12f},scale={width}:{height}:flags=lanczos,'
        f'fps={fps},trim=end_frame={frames},setpts=N/({fps}*TB),setsar=1[ref];'
        f"[0:v][ref]overlay=0:0:eof_action=pass:enable='lt(n,{frames})'[bg];"
        f'[2:v]setpts=N/({fps}*TB),setsar=1[face];'
        f"[bg][face]overlay=0:0:eof_action=pass:enable='{enable}'[base];"
        f'[3:v]setpts=N/({fps}*TB),format=yuv420p[cam];'
        f'[4:v]format=gray,setpts=N/({fps}*TB)[mask];[cam][mask]alphamerge[pip];'
        f"[base][pip]overlay={width-size-margin}:{height-size-margin}:"
        f"enable='lt(n,{frames})*not({enable})':eof_action=pass,"
        f'setpts=N/({fps}*TB),format=yuv420p,setparams=range=limited:'
        'color_primaries=bt709:color_trc=bt709:colorspace=bt709[v]')
    (work/'compose.filter').write_text(graph)
    temp=work/'video.partial.mp4'
    cmd=['ffmpeg','-v','error','-nostdin','-y','-filter_complex_threads','2']
    if hardware:
        cmd += ['-hwaccel','videotoolbox']
    cmd += ['-i',str(media),'-i',str(prepared),'-f','concat','-safe','0','-i',str(face_list),
        '-f','concat','-safe','0','-i',str(square_list),'-loop','1','-framerate',str(fps),'-i',str(mask),
        '-filter_complex',graph,'-map','[v]','-an']
    cmd += (['-c:v','h264_videotoolbox','-b:v','32M','-allow_sw','0'] if hardware else
        ['-c:v','libx264','-threads','2','-preset','veryfast','-crf','18'])
    cmd += ['-bf','0','-fps_mode','passthrough','-frames:v',str(output_frames),
        '-progress',str(work/'render.progress'),str(temp)]
    print('Composition de l’introduction…',flush=True)
    run(cmd)
    if int(probe(temp)['streams'][0]['nb_read_packets']) != output_frames:
        raise RuntimeError('Rendu vidéo incomplet.')
    partial=target.with_name(target.stem+'.partial.mp4')
    cmd=['ffmpeg','-v','error','-nostdin','-y','-i',str(temp),'-i',str(media),
        '-map','0:v:0','-map','1:a:0','-c','copy']
    if preview:
        cmd += ['-t',str(frames/fps)]
    run(cmd+['-movflags','+faststart',str(partial)])
    final_probe=probe(partial)
    vv=next(s for s in final_probe['streams'] if s['codec_type']=='video')
    aa=next(s for s in final_probe['streams'] if s['codec_type']=='audio')
    if abs(float(vv['duration'])-float(aa['duration'])) > .03:
        raise RuntimeError('Écart audio vidéo excessif.')
    if not preview:
        def audio_hash(path):
            return run(['ffmpeg','-v','error','-i',str(path),'-map','0:a:0','-c','copy',
                '-f','hash','-hash','sha256','-'])
        if audio_hash(partial) != audio_hash(media):
            raise RuntimeError('Le master audio a changé.')
    decode=['ffmpeg','-v','error','-xerror','-nostdin']
    if hardware:
        decode += ['-hwaccel','videotoolbox','-hwaccel_output_format','videotoolbox_vld']
    run(decode+['-i',str(partial),'-map','0:v:0','-an','-f','null','-'])
    boundaries={0,frames-1,output_frames-1}
    if frames<output_frames:
        boundaries.add(frames)
    for a,b in face:
        boundaries.update([a,min(b,output_frames-1)])
    for n in sorted(boundaries):
        raw=run(['ffmpeg','-v','error','-xerror','-nostdin','-ss',str(n/fps),'-i',str(partial),
            '-frames:v','1','-vf','scale=64:36','-pix_fmt','rgb24','-f','rawvideo','-'])
        if len(raw)!=64*36*3:
            raise RuntimeError('Image manquante au raccord d’introduction.')
    partial.replace(target)
    result=prefix if preview else doc
    result['face_crop']=crop
    result['editorial_overlays']={'manifest':str(target.with_suffix('.edit.json')),
        'intro_seconds':[0,frames/fps],'camera_timeline_unchanged':True}
    target.with_suffix('.sources.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
    word_path=media.with_suffix('.words.json')
    if word_path.exists():
        words=json.loads(word_path.read_text())
        if preview:
            words=[w for w in words if (w['start']+w['end'])/2 < frames/fps]
        target.with_suffix('.words.json').write_text(json.dumps(words,ensure_ascii=False,indent=2))
    target.with_suffix('.edit.json').write_text(json.dumps(spec|{'frames':frames,'face_intervals':face},indent=2))
    receipt.write_text(json.dumps({'signature':signature,'output_stamp':file_stamp(target),
        'frames':output_frames,'av_delta_ms':1000*(float(vv['duration'])-float(aa['duration'])),
        'audio_bitstream_identical':not preview,'full_decode_ok':True,
        'verified_boundaries':len(boundaries)},indent=2))
    print('Introduction prête :',target,flush=True)
    return target


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--media',required=True)
    parser.add_argument('--out',required=True)
    parser.add_argument('--spec',required=True)
    parser.add_argument('--workdir',required=True)
    parser.add_argument('--preview-only',action='store_true')
    parser.add_argument('--hardware',action='store_true')
    parser.add_argument('--no-open',action='store_true')
    args=parser.parse_args()
    build(args.media,args.out,args.spec,args.workdir,args.preview_only,args.hardware)


if __name__=='__main__':
    main()
