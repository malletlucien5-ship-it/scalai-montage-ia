#!/usr/bin/python3
"""Orchestrateur montage multicam (webcam DJI + écran OBS) — réglages ScalAI figés.

Étapes (chacune idempotente, cache dans OUT/work) :

  pipeline.py prep   --cam A.MP4 [B.MP4 ...] --screen S.mp4 --out DIR
      sync GCC-PHAT, frames écran 1 fps, planches-contact toutes les 6 s
      (DIR/sheets/scan_NN.jpg) → Claude les LIT pour repérer script / OBS / visuels.
  pipeline.py ranges --out DIR --script-ref f00006.jpg[,f00131.jpg] --obs-ref f00001.jpg[,...]
                     [--split "300-365,372-400,..."]
      détection déterministe des plages interdites (script + fenêtre OBS) et
      écriture de split_ranges.json (plages visuelles données en secondes écran).
  pipeline.py plan   --out DIR [--min-shot 4 --max-run 10] [--transcriber whisper]
      transcription + coupes silences/euh + layouts (LLM + DP) → DIR/montage.json
      puis analyse (analyze_plan.py). Ne rend rien.
  pipeline.py render --out DIR [--plan montage.json] [--name montage]
      rendu 1440p 50 fps x1.06 + polish, puis verify_output.py.
  pipeline.py cuts   --out DIR --resolve-project NOM [--media montage.mp4]
      lit les coupes Resolve, écrit montage-cut.json, rend montage-cut.mp4.
      Ajoute montage-final.mp4 lorsque DIR/intro.json est configuré.
  pipeline.py finish --out DIR --media montage-cut.mp4 [--preview-only]
      applique l’introduction configurée depuis la référence et les rushs.

Tout tourne en arrière-plan de la conversation via nohup si --background.
Rien ne s'ouvre à l'écran (--no-notify partout).
"""
import argparse, json, os, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
AE = HERE.parent
PY = sys.executable
MULTICAM = str(AE / "multicam.py")


def source_module():
    """Le renderer original est aussi importable sans charger le clipper."""
    import importlib.util
    path = AE.parent / 'clipper/clipper/source_media.py'
    spec = importlib.util.spec_from_file_location('source_media', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_source_table(plan_path, target):
    p = json.loads(Path(plan_path).read_text())
    from resolve_cuts import probe_dur, probe_fps
    module = source_module()
    doc = module.from_multicam(p, [probe_dur(x) for x in p['cam_parts']], probe_fps(p['cam_parts'][0]))
    Path(target).with_suffix('.sources.json').write_text(json.dumps(doc, ensure_ascii=False, indent=2))

# Réglages validés le 12/09/2026 (voir docs/superpowers/specs/2026-09-12-*.md)
DEFAULTS = dict(
    resolution="1440", layout_mode="pip", pip_corner="bottom-right", pip_size="0.40",
    pip_radius="0.08", pip_margin="40", speed="1.06", screen_fit="fit",
    screen_crop="0:0:1920:1080",          # écran complet, fond du bureau conservé
    face_crop="1050:100:1800:1800",       # cadrage validé le 14/09/2026
    min_shot="4", max_run="10", transcriber="whisper",
)


def sh(cmd, log=None, background=False):
    print("$", " ".join(f'"{c}"' if " " in c else c for c in cmd), flush=True)
    if background and log:
        with open(log, "ab") as f:
            p = subprocess.Popen(cmd, stdout=f, stderr=subprocess.STDOUT, start_new_session=True)
        print(f"  → pid {p.pid}, log {log}")
        return 0
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    lines = [l for l in r.stdout.splitlines() if "warn" not in l.lower()]
    print("\n".join(lines[-40:]))
    if log:
        Path(log).write_text(r.stdout)
    return r.returncode


def state(out):
    p = out / "pipeline.json"
    return json.loads(p.read_text()) if p.exists() else {}


def save(out, st):
    (out / "pipeline.json").write_text(json.dumps(st, ensure_ascii=False, indent=1))


def base_cmd(st, out):
    return [PY, MULTICAM, *st["cam"], "--screen", st["screen"], "--out", str(out / "montage.mp4"),
            "--workdir", str(out / "work"), "--no-notify"]


def cmd_prep(a):
    out = Path(a.out).resolve(); (out / "work").mkdir(parents=True, exist_ok=True)
    st = state(out); st.update(cam=[str(Path(c).resolve()) for c in a.cam], screen=str(Path(a.screen).resolve()),
                               audio=a.audio)
    save(out, st)
    rc = sh(base_cmd(st, out) + ["--resolution", DEFAULTS["resolution"], "--sync-only"], out / "work/sync.log")
    if rc:
        sys.exit("sync échouée")
    fr = out / "work/scrframes"; fr.mkdir(exist_ok=True)
    if not any(fr.iterdir()):
        sh(["ffmpeg", "-v", "error", "-i", st["screen"], "-vf", "fps=1,scale=480:-1", "-q:v", "4",
            str(fr / "f%05d.jpg")])
    sh([PY, str(HERE / "contact_sheets.py"), "frames", str(fr), "--step", "6", "--out", str(out / "sheets")])
    print("\nSUITE : lire DIR/sheets/scan_*.jpg (Read), noter en secondes ÉCRAN : (1) images de "
          "référence du script et de la fenêtre OBS (fNNNNN.jpg = seconde NNNNN-1), (2) plages "
          "visuelles (résultat affiché, images, vidéo, pricing, clés API). Puis `ranges`.")


def cmd_ranges(a):
    out = Path(a.out).resolve(); st = state(out); fr = out / "work/scrframes"
    det = str(AE / "detect_script_ranges.py")
    forb = []
    if a.script_ref:
        refs = sum((["--ref", r] for r in a.script_ref.split(",")), [])
        sh([PY, det, str(fr), *refs, "--threshold", "0.12", "--gap", "2", "--out", str(out / "script_ranges.json")])
        forb += json.loads((out / "script_ranges.json").read_text())
    if a.obs_ref:
        refs = sum((["--ref", r] for r in a.obs_ref.split(",")), [])
        sh([PY, det, str(fr), *refs, "--threshold", "0.15", "--gap", "1", "--out", str(out / "obs_ranges.json")])
        forb += json.loads((out / "obs_ranges.json").read_text())
    merged = []
    for s, e in sorted(forb):
        if merged and s <= merged[-1][1] + 1.0:
            merged[-1][1] = max(merged[-1][1], e)
        else:
            merged.append([s, e])
    (out / "forbidden_ranges.json").write_text(json.dumps(merged))
    print(f"forbidden_ranges.json : {len(merged)} plages, {sum(e-s for s,e in merged):.0f}s")
    if a.split:
        sp = []
        for tok in a.split.split(","):
            x, y = tok.split("-"); sp.append([float(x), float(y)])
        m = []
        for s, e in sorted(sp):
            if m and s <= m[-1][1] + 2:
                m[-1][1] = max(m[-1][1], e)
            else:
                m.append([s, e])
        (out / "split_ranges.json").write_text(json.dumps(m))
        print(f"split_ranges.json : {len(m)} plages, {sum(e-s for s,e in m):.0f}s")
    print("SUITE : vérifier les bords des plages sur vignettes (contact_sheets), puis `plan`.")


def plan_args(st, out, a):
    d = DEFAULTS
    cmd = base_cmd(st, out) + [
        "--resolution", d["resolution"], "--layout-mode", d["layout_mode"], "--pip-corner", d["pip_corner"],
        "--pip-size", d["pip_size"], "--pip-radius", d["pip_radius"], "--pip-margin", d["pip_margin"],
        "--speed", d["speed"], "--screen-fit", d["screen_fit"], "--screen-crop", d["screen_crop"],
        "--face-crop", a.face_crop or d["face_crop"],
        "--min-shot", str(a.min_shot), "--max-split", str(a.max_run), "--max-face", str(a.max_run),
        "--transcriber", a.transcriber]
    if (out / "forbidden_ranges.json").exists():
        cmd += ["--face-ranges", str(out / "forbidden_ranges.json")]
    # Réglages de coupe propres à la vidéo (ex. {"--drop-db": 20, "--trail": 0.1}).
    if (out / "cut_params.json").exists():
        for k, v in json.loads((out / "cut_params.json").read_text()).items():
            cmd += [k, str(v)]
    if (out / "split_ranges.json").exists():
        cmd += ["--split-ranges", str(out / "split_ranges.json")]
    cuts = []
    for name in ("cut_ranges.json", "restarts_auto.json"):
        if (out / name).exists():
            cuts += json.loads((out / name).read_text())
    if cuts:
        combined = out / "work/cut_ranges.all.json"
        combined.write_text(json.dumps(sorted(cuts)))
        cmd += ["--cut-ranges", str(combined)]
    return cmd


MLX_PY = AE / ".venv-mlx/bin/python"


def take_sources(out, st=None):
    """Table source d'une prise : audio OBS maître ou audio caméra, fins rognées corrigées."""
    from obs_master import to_obs_master, output_words
    from tail_guard import extend_tails
    from resolve_cuts import probe_dur, probe_fps
    st = st or state(out)
    plan = json.loads((out / "montage.json").read_text())
    # Rupture de synchro mesurée (OBS qui perd du temps) : offsets séparés de part et d'autre.
    if (out / "sync_breaks.json").exists():
        plan["sync"]["breaks"] = json.loads((out / "sync_breaks.json").read_text())
    if st.get("audio", "camera") == "obs":
        doc = to_obs_master(plan)
    else:
        doc = source_module().from_multicam(plan, [probe_dur(x) for x in plan["cam_parts"]],
                                            probe_fps(plan["cam_parts"][0]))
        doc["source_duration_seconds"] = sum(probe_dur(x) for x in plan["cam_parts"])
    fixed = extend_tails(doc, float(plan.get("speed", 1)))
    words = json.loads((out / "work/multicam.transcache.json").read_text())["words"]
    # Les mots suivent la timeline de la prise, parties caméra comprises.
    offsets, pos = {}, 0.
    for path in plan["cam_parts"]:
        offsets[path] = pos; pos += probe_dur(path)
    flat = {**doc, "chunks": [{**c, "camera": {**c["camera"], "start": c["camera"]["start"] + offsets[c["camera"]["path"]],
                                                 "end": c["camera"]["end"] + offsets[c["camera"]["path"]]}}
                              for c in doc["chunks"]]}
    return doc, output_words(flat, words, plan["sync"].get("av_cam", 0.)), fixed


def transcribe_chunks(table, target, pad=None):
    """Transcription portion par portion (mlx-whisper) : les amorces ratées restent visibles."""
    if not MLX_PY.exists():
        sys.exit(f"Environnement mlx absent : {MLX_PY}. Créer avec python3.14 -m venv puis pip install mlx-whisper.")
    extra = [] if pad is None else ["--pad", str(pad)]
    rc = sh([str(MLX_PY), str(HERE / "segment_transcribe.py"), str(table), "--out", str(target), *extra,
             "--no-open"], target.with_suffix(".log"))
    if rc:
        sys.exit("transcription par portion échouée")
    return json.loads(target.read_text())


def fine_review(doc, target):
    """Relecture fine par phrase acoustique (restart_detect) : amorce reprise dans la même
    portion. Retourne les coupes en secondes de sortie."""
    from restart_detect import split_phrases, phrase_table, attach_text, fine_cuts
    phrases = split_phrases(doc)
    table = target.with_suffix(".table.json")
    table.write_text(json.dumps(phrase_table(phrases, doc["fps"]), ensure_ascii=False))
    attach_text(phrases, transcribe_chunks(table, target, pad=0))
    cuts = fine_cuts(phrases)
    for c in cuts:
        print(f"  relecture fine {c['range'][0]:8.2f}-{c['range'][1]:8.2f} {c['why'][:48]:48s} {c['text'][:70]}")
    return cuts


def restart_pass(out, st):
    """Ajoute à restarts_auto.json les amorces ratées du plan courant. Retourne le nombre ajouté."""
    from restart_detect import detect, phrase_repeats
    from resolve_cuts import probe_dur
    doc, _, _ = take_sources(out, st)
    table = out / "work/take.sources.json"
    table.write_text(json.dumps(doc, ensure_ascii=False))
    segs = transcribe_chunks(table, out / "work/segments.text.json")
    plan = json.loads((out / "montage.json").read_text())
    offsets, pos = {}, 0.
    for path in plan["cam_parts"]:
        offsets[path] = pos; pos += probe_dur(path)
    av = plan["sync"].get("av_cam", 0.)
    auto_file = out / "restarts_auto.json"
    auto = json.loads(auto_file.read_text()) if auto_file.exists() else []
    report = []
    added = 0
    for i, why in sorted(detect(segs).items()):
        cam = segs[i]["camera"]
        r = [round(offsets[cam["path"]] + cam["start"] - av, 3), round(offsets[cam["path"]] + cam["end"] - av, 3)]
        report.append({"range": r, "why": why, "text": segs[i]["text"]})
        if not any(abs(r[0] - x) < .05 and abs(r[1] - y) < .05 for x, y in auto):
            auto.append(r); added += 1
    # Répétition à l'intérieur d'un passage : Whisper l'a gardée dans la transcription globale.
    words = json.loads((out / "work/multicam.transcache.json").read_text())["words"]
    spans = [(offsets[s["camera"]["path"]] + s["camera"]["start"] - av,
              offsets[s["camera"]["path"]] + s["camera"]["end"] - av) for s in segs]
    for a, b in phrase_repeats(words):
        if not 1.0 <= b - a <= 10 or not any(x - .1 <= a and b <= y + .1 for x, y in spans):
            continue
        r = [round(a, 3), round(b - .12, 3)]
        text = " ".join(w["word"] for w in words if a <= w["start"] < b)
        report.append({"range": r, "why": "répétition dans le passage", "text": text})
        if not any(abs(r[0] - x) < .05 and abs(r[1] - y) < .05 for x, y in auto):
            auto.append(r); added += 1
    # Amorce et reprise dans la même portion : Whisper les fusionne sur la portion
    # entière. Relecture fine par phrase acoustique (amorces seulement à ce stade).
    from restart_detect import output_to_source
    for c in fine_review(doc, out / "work/take.phrases.text.json"):
        (pa, a), (pb, b) = (output_to_source(doc, t) for t in c["range"])
        if pa != pb or b <= a:
            continue
        r = [round(offsets[pa] + a - av, 3), round(offsets[pa] + b - av, 3)]
        report.append({"range": r, "why": c["why"], "text": c["text"]})
        if not any(abs(r[0] - x) < .05 and abs(r[1] - y) < .05 for x, y in auto):
            auto.append(r); added += 1
    auto_file.write_text(json.dumps(sorted(auto)))
    log = out / "work/restarts.report.json"
    old = json.loads(log.read_text()) if log.exists() else []
    log.write_text(json.dumps(old + report, ensure_ascii=False, indent=1))
    for row in report:
        print(f"  reprise {row['range'][0]:8.2f} {row['why']:40s} {row['text'][:70]}")
    return added


def cmd_plan(a):
    out = Path(a.out).resolve(); st = state(out)
    # Les reprises automatiques se recalculent à chaque plan : des coupes héritées
    # d'une version précédente du détecteur ne doivent jamais survivre (AI Advantage, 10/10/2026).
    if a.restarts:
        for name in ("restarts_auto.json", "work/restarts.report.json"):
            f = out / name
            if f.exists():
                f.replace(f.with_name(f.stem + ".precedent" + f.suffix))
    rc = sh(plan_args(st, out, a) + ["--preview-out", str(out / "montage.json")], out / "work/plan.log")
    if rc:
        sys.exit("plan échoué (transcription ? clé OpenRouter ?)")
    # Reprises : on coupe chaque amorce ratée, puis on replanifie. Les nouvelles
    # portions peuvent révéler une amorce de plus, d'où la boucle bornée.
    for loop in range(3 if a.restarts else 0):
        added = restart_pass(out, st)
        print(f"[Reprises] passe {loop + 1} : {added} nouvelle(s) amorce(s)")
        if not added:
            break
        if sh(plan_args(st, out, a) + ["--preview-out", str(out / "montage.json")], out / "work/plan.log"):
            sys.exit("replanification échouée")
    sh([PY, str(HERE / "analyze_plan.py"), str(out / "montage.json"), "--min-shot", str(a.min_shot),
        "--max-run", str(a.max_run)])
    print("SUITE : si 'ÉCRAN sur plage interdite' est vide → `render`.")


def cmd_render(a):
    out = Path(a.out).resolve(); st = state(out)
    plan = Path(a.plan) if a.plan else out / "montage.json"
    log = out / f"work/render-{a.name}.log"
    if a.background:
        cmd = [PY, str(HERE / 'pipeline.py'), 'render', '--out', str(out),
            '--plan', str(plan), '--name', a.name, '--no-open']
        if getattr(a, 'finish', False):
            cmd += ['--finish']
        sh(cmd, log, background=True)
        return
    target = out / f"{a.name}.mp4"
    if target.exists():
        target.rename(out / f"{a.name}.prev.mp4")
    cmd = [PY, MULTICAM, *st["cam"], "--from-json", str(plan), "--out", str(target),
           "--workdir", str(out / "work"), "--workers", "3", "--no-notify"]
    rc = sh(cmd, log)
    if rc:
        sys.exit("rendu échoué")
    write_source_table(plan, target)
    if sh([PY, str(HERE / "verify_output.py"), str(target), "--sheet-dir", str(out / "sheets")]):
        sys.exit('Vérification du rendu échouée.')
    if getattr(a, 'finish', False):
        finish_configured(out, target.name)


def cmd_finish(a):
    out = Path(a.out).resolve()
    if a.preview_only and a.name == 'montage-final':
        a.name = 'intro-preview'
    media = Path(a.media)
    if not media.is_absolute():
        media = out / media
    spec = Path(a.intro_spec) if a.intro_spec else out / 'intro.json'
    target = out / (a.name + '.mp4')
    cmd = [PY, str(HERE / 'intro.py'), '--media', str(media), '--out', str(target),
        '--spec', str(spec), '--workdir', str(out / 'work' / ('intro-' + a.name)), '--no-open']
    if a.preview_only:
        cmd += ['--preview-only']
    if a.encoder == 'videotoolbox' or (a.encoder == 'auto' and sys.platform == 'darwin'):
        cmd += ['--hardware']
    rc = sh(cmd, out / 'work' / ('finish-' + a.name + '.log'), background=a.background)
    if rc:
        sys.exit('Composition de l’introduction échouée.')


def finish_configured(out, media):
    if (out / 'intro.json').exists():
        cmd_finish(argparse.Namespace(out=str(out), media=media, intro_spec=None,
            name='montage-final', preview_only=False, encoder='auto', background=False))


def cmd_assemble(a):
    """Une ou plusieurs prises → montage.mp4 depuis les rushs, en un seul rendu vidéo."""
    from merge_source_plans import merge
    from restart_detect import detect
    from tail_guard import protected_words
    from quiet_cleanup import read_audio, refine_kept, remap_words
    out = Path(a.out).resolve(); (out / "work").mkdir(parents=True, exist_ok=True)
    takes = [Path(t).resolve() for t in a.takes] if a.takes else [out]
    docs, words, cams = [], [], []
    for t in takes:
        st = state(t)
        doc, w, fixed = take_sources(t, st)
        docs.append(doc); words.append(w); cams += st["cam"]
        print(f"{t.name} : {len(doc['chunks'])} portions, {len(fixed)} fins de mot rallongées")
    doc, w = merge(docs, words, cams)
    fps = doc["fps"]
    module = source_module()

    def keep_frames(doc, drop):
        kept, pos = [], 0
        for i, c in enumerate(doc["chunks"]):
            if i not in drop:
                kept.append([pos, pos + c["frames"]])
            pos += c["frames"]
        return kept

    # Reprises restantes, surtout entre deux prises (fin rejouée au début de la suivante).
    table = out / "work/assemble.sources.json"
    table.write_text(json.dumps(doc, ensure_ascii=False))
    segs = transcribe_chunks(table, out / "work/assemble.segments.json")
    drop = detect(segs)
    for i, why in sorted(drop.items()):
        print(f"  reprise retirée {i:4d} {why:40s} {segs[i]['text'][:70]}")
    protect = protected_words(doc)
    if drop:
        kept = keep_frames(doc, drop)
        w, protect = remap_words(w, kept, fps), remap_words(protect, kept, fps)
        doc = module.slice_frames(doc, kept)
    # Creux presque muets mesurés sur l'audio maître, avant tout rendu vidéo.
    pcm = out / "work/assemble.pcm.wav"
    module.render_audio(doc, pcm, workdir=out / "work/audio-chunks", workers=4)
    audio, sr = read_audio(pcm)
    total = sum(c["frames"] for c in doc["chunks"])
    clean, report = refine_kept([[0, total]], audio, sr, w + protect, fps=fps)
    print(f"Creux retirés avant rendu : {report['removed_frames'] / fps:.2f}s")
    w = remap_words(w, clean, fps)
    protect = remap_words(protect, clean, fps)
    doc = module.slice_frames(doc, clean)
    if a.fine:
        # Relecture fine : amorce et reprise dans la même portion.
        from restart_detect import kept_frames
        fine = fine_review(doc, out / "work/assemble.phrases.text.json")
        (out / "work/fine_cuts.json").write_text(json.dumps(fine, ensure_ascii=False, indent=1))
        if fine:
            before = total_frames(doc)
            kept = kept_frames(before, fine, fps)
            w, protect = remap_words(w, kept, fps), remap_words(protect, kept, fps)
            doc = module.slice_frames(doc, kept)
            print(f"Relecture fine : {len(fine)} coupe(s), {(before - total_frames(doc)) / fps:.2f}s retirées")
    # Garde-fou des raccords : aucun mot coupé en deux par un raccord automatique (10/10/2026).
    from raccords_mots import auditer, corriger
    faits, _ = corriger(doc, auditer(doc), float(DEFAULTS["speed"]))
    (out / "work/raccords-mots.json").write_text(json.dumps(faits, ensure_ascii=False, indent=1))
    print(f"Mots restaurés aux raccords : {len(faits)}")
    for c in doc["chunks"]:
        c.pop("tail_guard_frames", None)
    pcm.unlink()
    if a.dry:
        print(f"[dry] {len(doc['chunks'])} portions, {total_frames(doc)/fps/60:.2f} min, {len(w)} mots.")
        (out / "work" / f"{a.name}.dry.sources.json").write_text(json.dumps(doc, ensure_ascii=False))
        (out / "work" / f"{a.name}.dry.words.json").write_text(json.dumps(w, ensure_ascii=False))
        (out / "work" / f"{a.name}.dry.protect.json").write_text(json.dumps(protect))
        return

    target = out / f"{a.name}.mp4"
    if target.exists():
        target.rename(out / f"{a.name}.prev.mp4")
    raw = out / "work" / f"{a.name}-brut.mp4"
    if not a.no_grade:
        # Look A sur la caméra seule, base mesurée par rush (skill etalonnage-look-a).
        import etalonnage
        rushes = sorted({c["camera"]["path"] for c in doc["chunks"]})
        etalonnage.bases(out, rushes)
        doc["camera_grades"] = {k: v for k, v in etalonnage.grades(out).items() if k in rushes}
        print(f"Étalonnage look A : {len(doc['camera_grades'])}/{len(rushes)} rush(s)")
    module.render(doc, raw, horizontal=True, workdir=out / "work/clips", workers=4)
    sys.path.insert(0, str(AE))
    from auto_edit import polish_audio
    polish_audio(str(raw), str(target))
    raw.unlink()
    target.with_suffix(".sources.json").write_text(json.dumps(doc, ensure_ascii=False, indent=2))
    target.with_suffix(".words.json").write_text(json.dumps(w, ensure_ascii=False, indent=2))
    target.with_suffix(".protect.json").write_text(json.dumps(protect))
    src = doc.get("source_duration_seconds", 0)
    print(f"Sources {src/60:.1f} min → rendu {total_frames(doc)/fps/60:.2f} min "
          f"({doc.get('part_count', 1)} prise(s), {len(set(c['camera']['path'] for c in doc['chunks']))} rush(s) caméra)")
    cmd_verify(argparse.Namespace(out=str(out), name=a.name))


def total_frames(doc):
    return sum(c["frames"] for c in doc["chunks"])


def cmd_verify(a):
    out = Path(a.out).resolve()
    target = out / f'{a.name}.mp4'
    plan = out / f'{a.name}.json'
    if target.exists() and plan.exists() and not target.with_suffix('.sources.json').exists():
        write_source_table(plan, target)
    rc=sh([PY, str(HERE / "verify_output.py"), str(target), "--sheet-dir", str(out / "sheets")])
    if rc:
        sys.exit('Vérification vidéo échouée.')
    words=target.with_suffix('.words.json')
    if words.exists():
        from quiet_cleanup import audit_video
        protect=target.with_suffix('.protect.json')
        extra=json.loads(protect.read_text()) if protect.exists() else []
        audit=audit_video(target,json.loads(words.read_text())+extra)
        (out/'work'/f'{a.name}.quiet-audit.json').write_text(json.dumps(audit))
        print(f"Creux acoustiques résiduels : {audit['eligible_quiet_spans']}")
        if audit['eligible_quiet_spans']:
            sys.exit('Creux acoustiques résiduels : nettoyer avant livraison.')


def kept_from_edl(path, fps):
    """Plages gardées (images du média) d'une EDL CMX 3600 exportée par DaVinci, piste vidéo."""
    import re
    def tc(s):
        h, m, sec, f = map(int, s.split(":"))
        return int(round((h * 3600 + m * 60 + sec) * fps)) + f
    kept = []
    for line in path.read_text(errors="ignore").splitlines():
        m = re.match(r"^\d{3}\s+\S+\s+V\s+C\s+(\S+)\s+(\S+)\s+\S+\s+\S+", line)
        if m:
            kept.append([tc(m.group(1)), tc(m.group(2))])
    if not kept:
        sys.exit(f"EDL sans plan vidéo : {path}")
    return kept


def cmd_cuts(a):
    out = Path(a.out).resolve()
    kept = out / "resolve_kept_frames.json"
    if getattr(a, "edl", None):
        # Timeline exportée de DaVinci (EDL CMX 3600) : coupes de Lucien à l'image près.
        kept.write_text(json.dumps(kept_from_edl(Path(a.edl), json.loads(
            (out / Path(a.media).with_suffix('.sources.json').name).read_text())["fps"])))
    elif sh([PY, str(HERE / "resolve_cuts.py"), "extract", a.resolve_project, "--media", a.media, "--out", str(kept)]):
        sys.exit("lecture Resolve échouée")
    table = out / Path(a.media).with_suffix('.sources.json').name
    if table.exists():
        module = source_module()
        original = json.loads(table.read_text())
        intervals = json.loads(kept.read_text())
        # Les coupes de Lucien font foi : aucune coupe automatique en plus (règle du 10/10/2026).
        # Seules restaurations permises : fins de mot (tail_guard) et mots coupés aux raccords.
        lucien_frames = sum(y - x for x, y in intervals)
        auto_ends = [((c.get('audio') or c['camera'])['path'], (c.get('audio') or c['camera'])['end'])
                     for c in original['chunks']]
        cut = module.slice_frames(original, intervals)
        # Raccords des coupes de Lucien : là où deux plages gardées se touchent dans la sortie.
        bords, pos = set(), 0
        for x, y in intervals[:-1]:
            pos += y - x; bords.add(pos)
        pos, proteges = 0, set()
        for i, c in enumerate(cut['chunks'][:-1]):
            pos += c['frames']
            if pos in bords:
                proteges.add((i, i + 1))
        # Aucun ajout automatique après les coupes de Lucien (règles des 08/10 et 10/10/2026) :
        # les raccords qui tranchent un mot sont listés ; seules ses demandes écrites sont restaurées.
        from raccords_mots import auditer, src as _src, decaler
        (out / 'work/raccords-mots.json').write_text(json.dumps(auditer(cut), ensure_ascii=False, indent=1))
        demandes = out / 'restaurations.json'
        for r in (json.loads(demandes.read_text()) if demandes.exists() else []):
            ch = cut['chunks']
            for i, c in enumerate(ch):
                s = _src(c)
                if r['source'] in s['path'] and abs(s['end'] - r['frontiere']) < .03:
                    if r['cote'] == 'creux' and i + 1 < len(ch):
                        decaler(c, 'end', _src(ch[i + 1])['start'] - s['end'])
                    else:
                        decaler(c, 'end', r['jusqu_a'] - s['end'])
                    c['frames'] = max(1, round((_src(c)['end'] - _src(c)['start']) * cut['fps'] / float(DEFAULTS['speed'])))
                    print(f"Restauré sur demande : {r['mot']}")
                    break
            else:
                print(f"Demande introuvable : {r['mot']}")
        if sum(c['frames'] for c in cut['chunks']) < lucien_frames:
            sys.exit("Refus : le montage coupé est plus court que la timeline de Lucien. "
                     "Aucune coupe automatique n'est permise après ses coupes.")
        target = out / 'montage-cut.mp4'
        if target.exists():
            target.rename(out / 'montage-cut.prev.mp4')
        raw = out / 'work/montage-cut-brut.mp4'
        module.render(cut, raw, horizontal=True)
        sys.path.insert(0, str(AE))
        from auto_edit import polish_audio
        polish_audio(str(raw), str(target))
        raw.unlink()
        target.with_suffix('.sources.json').write_text(json.dumps(cut, ensure_ascii=False, indent=2))
        # Composer aussi la transcription sur la timeline actuellement coupée.
        word_file = out / Path(a.media).with_suffix('.words.json').name
        if word_file.exists():
            old_words = json.loads(word_file.read_text())
            result, offset = [], 0.
            for a0, b0 in intervals:
                start, end = a0/original['fps'], b0/original['fps']
                for word in old_words:
                    if start <= (word['start']+word['end'])/2 < end:
                        result.append({**word, 'start': offset+max(0.,word['start']-start),
                                       'end': offset+min(end-start,word['end']-start)})
                offset += end-start
            target.with_suffix('.words.json').write_text(json.dumps(result, ensure_ascii=False, indent=2))
        if sh([PY, str(HERE / 'verify_output.py'), str(target), '--sheet-dir', str(out / 'sheets')]):
            sys.exit('Vérification des coupes échouée.')
        finish_configured(out, target.name)
        return
    sh([PY, str(HERE / "resolve_cuts.py"), "apply", str(out / "montage.json"), str(kept), str(out / "montage-cut.json")])
    a.plan = str(out / "montage-cut.json"); a.name = "montage-cut"
    cmd_render(a)
    if not getattr(a, 'finish', False):
        finish_configured(out, 'montage-cut.mp4')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("prep"); p.add_argument("--cam", nargs="+", required=True); p.add_argument("--screen", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--audio", choices=("camera", "obs"), default="obs",
                   help="Piste audio maître : OBS (défaut depuis le 15/09/2026) ou caméra.")
    p.add_argument('--no-open', action='store_true')
    r = sub.add_parser("ranges"); r.add_argument("--out", required=True); r.add_argument("--script-ref", default=None)
    r.add_argument("--obs-ref", default=None); r.add_argument("--split", default=None)
    r.add_argument('--no-open', action='store_true')
    for name in ("plan", "render", "verify", "cuts"):
        s = sub.add_parser(name); s.add_argument("--out", required=True)
        s.add_argument("--min-shot", type=float, default=float(DEFAULTS["min_shot"]))
        s.add_argument("--max-run", type=float, default=float(DEFAULTS["max_run"]))
        s.add_argument("--transcriber", default=DEFAULTS["transcriber"], choices=("whisper", "elevenlabs"))
        s.add_argument("--face-crop", default=None); s.add_argument("--plan", default=None)
        s.add_argument("--name", default="montage"); s.add_argument("--background", action="store_true")
        s.add_argument("--resolve-project", default=None); s.add_argument("--media", default="montage.mp4")
        s.add_argument("--edl", default=None, help="EDL CMX 3600 exportée de DaVinci au lieu du projet Resolve.")
        s.add_argument('--finish', action='store_true', help='Ajouter l’introduction configurée après le rendu.')
        s.add_argument('--no-restarts', dest='restarts', action='store_false',
                       help='Ne pas couper les amorces ratées (transcription portion par portion).')
        s.add_argument('--no-open', action='store_true')
    g = sub.add_parser('assemble')
    g.add_argument('--out', required=True)
    g.add_argument('--takes', nargs='*', help='Dossiers de prise dans l’ordre (défaut : OUT seul).')
    g.add_argument('--name', default='montage')
    g.add_argument('--dry', action='store_true', help='Tout préparer sans rendu vidéo.')
    g.add_argument('--no-grade', action='store_true', help='Sans étalonnage look A de la caméra.')
    g.add_argument('--no-fine', dest='fine', action='store_false',
                   help='Sans relecture fine par phrase (amorce reprise dans la même portion).')
    g.add_argument('--no-open', action='store_true')
    f = sub.add_parser('finish')
    f.add_argument('--out', required=True)
    f.add_argument('--media', default='montage-cut.mp4')
    f.add_argument('--intro-spec')
    f.add_argument('--name', default='montage-final')
    f.add_argument('--preview-only', action='store_true')
    f.add_argument('--encoder', choices=['auto', 'videotoolbox', 'x264'], default='auto')
    f.add_argument('--background', action='store_true')
    f.add_argument('--no-open', action='store_true')
    a = ap.parse_args()
    {"prep": cmd_prep, "ranges": cmd_ranges, "plan": cmd_plan, "render": cmd_render,
     "verify": cmd_verify, "cuts": cmd_cuts, "finish": cmd_finish, "assemble": cmd_assemble}[a.cmd](a)


if __name__ == "__main__":
    main()
