#!/usr/bin/python3
"""
auto_edit_ui.py — Interface web locale pour auto_edit.py + cut_silences.py
Double-cliquer sur "Launch Auto Edit.command" pour démarrer.
"""

import os
import sys
import json
import subprocess
import threading
import time
import uuid
import hashlib
import shutil
import queue
from pathlib import Path
from flask import Flask, request, jsonify, Response

# ─── Config ───────────────────────────────────────────────────────────────────

UPLOAD_DIR        = Path.home() / "Desktop" / "AutoEdit"
UPLOAD_DIR.mkdir(exist_ok=True)
PREVIEW_DIR       = UPLOAD_DIR / ".previews"
PREVIEW_DIR.mkdir(exist_ok=True)

SCRIPT_ELEVENLABS = str(Path(__file__).parent / "auto_edit.py")
SCRIPT_SILENCE    = str(Path(__file__).parent / "cut_silences.py")
PYTHON            = "/usr/bin/python3"
PORT              = 7842

# ─── In-process worker (FIX #5) ───────────────────────────────────────────────

# On ajoute le dossier du script au sys.path pour pouvoir importer auto_edit.py
# et cut_silences.py qui sont à côté.
_SCRIPT_DIR = str(Path(__file__).parent)
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

try:
    import auto_edit as _auto_edit_mod
    import cut_silences as _cut_silences_mod
    INPROC_AVAILABLE = True
except Exception as _e:
    print(f"[UI] In-process unavailable, fallback subprocess: {_e}")
    _auto_edit_mod = None
    _cut_silences_mod = None
    INPROC_AVAILABLE = False

USE_INPROC = os.environ.get("AUTOEDIT_INPROC", "1") != "0" and INPROC_AVAILABLE

# Sémaphore pour limiter à 2 jobs in-process simultanés (CPU/RAM-bound,
# notamment torch/Silero).
INPROC_SEMAPHORE = threading.Semaphore(2)

# job state :
#  status : queued | uploading | detecting | awaiting_confirm | running | done | error
#  log, output, segments, duration, video_path, mode, speed
JOBS: dict = {}
JOBS_LOCK  = threading.Lock()

# ─── Queue de jobs (FIX #12) ──────────────────────────────────────────────────

JOB_QUEUE = queue.Queue()
QUEUE_WORKERS = 2  # nb max de jobs concurrents (limite CPU/RAM)

app = Flask(__name__)

# ─── Helpers ──────────────────────────────────────────────────────────────────

def _run_subprocess(job_id, cmd):
    """Lance la commande et stream stdout dans le log du job."""
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, env=env, bufsize=1,
    )
    for line in proc.stdout:
        line = line.rstrip()
        if not line:
            continue
        with JOBS_LOCK:
            JOBS[job_id]["log"].append(line)
    proc.wait()
    return proc.returncode


def _run_in_process(job_id, module, video_path, args_list):
    """
    Exécute le pipeline auto_edit/cut_silences en in-process.
    Redirige stdout/stderr vers le log du job, ligne par ligne.

    Args:
        job_id: id du job
        module: _auto_edit_mod ou _cut_silences_mod
        video_path: chemin de la vidéo
        args_list: liste d'arguments CLI additionnels (ex: ["--preview-out", "x.json"])
    """
    import io
    import contextlib

    class _LineCapture(io.TextIOBase):
        def __init__(self, jid):
            self.jid = jid
            self.buf = ""

        def write(self, s):
            self.buf += s
            while "\n" in self.buf:
                line, self.buf = self.buf.split("\n", 1)
                line = line.rstrip()
                if line:
                    with JOBS_LOCK:
                        if self.jid in JOBS:
                            JOBS[self.jid]["log"].append(line)
            return len(s)

        def flush(self):
            # Flush du buffer résiduel
            if self.buf:
                line = self.buf.rstrip()
                self.buf = ""
                if line:
                    with JOBS_LOCK:
                        if self.jid in JOBS:
                            JOBS[self.jid]["log"].append(line)

    cap = _LineCapture(job_id)
    saved_argv = sys.argv[:]
    sys.argv = [module.__file__, str(video_path)] + list(args_list)

    # On limite à 2 jobs in-process simultanés (CPU/RAM-bound).
    with INPROC_SEMAPHORE:
        try:
            with contextlib.redirect_stdout(cap), contextlib.redirect_stderr(cap):
                try:
                    module.main()
                    cap.flush()
                    return 0
                except SystemExit as se:
                    cap.flush()
                    return int(se.code) if se.code else 0
        except Exception as e:
            cap.flush()
            with JOBS_LOCK:
                if job_id in JOBS:
                    JOBS[job_id]["log"].append(f"[ERREUR in-process] {e}")
            return 1
        finally:
            sys.argv = saved_argv


def _module_for_mode(mode):
    """Retourne le module Python à invoquer in-process pour un mode donné."""
    if mode == "silence":
        return _cut_silences_mod
    return _auto_edit_mod


def _run_pipeline(job_id, mode, video_path, args_list):
    """
    Dispatch run in-process si dispo, sinon subprocess fallback.
    `args_list` ne contient PAS le path de la vidéo (ajouté ici).
    """
    if USE_INPROC:
        module = _module_for_mode(mode)
        if module is not None:
            return _run_in_process(job_id, module, video_path, args_list)

    # Fallback subprocess
    script = SCRIPT_SILENCE if mode == "silence" else SCRIPT_ELEVENLABS
    cmd = [PYTHON, script, str(video_path)] + list(args_list)
    return _run_subprocess(job_id, cmd)


# ─── Cache preview (FIX #6) ───────────────────────────────────────────────────

def _video_hash(video_path):
    """Hash rapide basé sur path + mtime + size (pas du contenu)."""
    p = Path(video_path)
    return hashlib.sha1(
        f"{p.resolve()}|{p.stat().st_mtime}|{p.stat().st_size}".encode()
    ).hexdigest()[:12]


def _preview_variant(opts):
    """Suffixe de clé cache pour les options qui changent les segments détectés."""
    return "_tailrelaxed" if (opts or {}).get("tail_relaxed") else ""


def _preview_cache_lookup(video_path, mode, opts=None):
    """Retourne le path d'un preview JSON existant pour cette vidéo, ou None."""
    try:
        key = f"{_video_hash(video_path)}_{mode}{_preview_variant(opts)}"
    except Exception:
        return None
    candidate = PREVIEW_DIR / f"cached_{key}.json"
    return candidate if candidate.exists() else None


def _preview_cache_store(video_path, mode, preview_path, opts=None):
    """Copie le preview JSON dans le cache (clé persistante)."""
    try:
        key = f"{_video_hash(video_path)}_{mode}{_preview_variant(opts)}"
        cached = PREVIEW_DIR / f"cached_{key}.json"
        shutil.copyfile(preview_path, cached)
        return cached
    except Exception:
        return None


# ─── Phase 1 : détection (ou run complet) ────────────────────────────────────

def _polish_args(opts):
    args = []
    if not opts.get("polish", True):
        args.append("--no-polish")
    return args


def _tail_args(opts):
    """Coupe moins agressive en fin de phrase (les deux pipelines l'acceptent)."""
    return ["--tail", "relaxed"] if opts.get("tail_relaxed") else []


def job_detect_or_run(job_id, video_path, mode, speed, preview, opts):
    """
    Si preview=True  : détecte + dump JSON + attend confirmation
    Si preview=False : run complet (detect + export) directement
    """
    with JOBS_LOCK:
        JOBS[job_id]["status"]     = "detecting" if preview else "running"
        JOBS[job_id]["video_path"] = str(video_path)
        JOBS[job_id]["mode"]       = mode
        JOBS[job_id]["speed"]      = speed
        JOBS[job_id]["opts"]       = opts

    try:
        if preview:
            preview_json = PREVIEW_DIR / f"{job_id}.json"

            # FIX #6 : lookup cache preview (path+mtime+size → JSON déjà calculé)
            force_redetect = bool(opts.get("force_redetect"))
            if not force_redetect:
                cached_preview = _preview_cache_lookup(video_path, mode, opts)
                if cached_preview:
                    try:
                        shutil.copyfile(cached_preview, preview_json)
                        with open(preview_json) as f:
                            data = json.load(f)
                        with JOBS_LOCK:
                            JOBS[job_id]["log"].append(
                                f"[Cache] Preview réutilisé : {cached_preview.name}"
                            )
                            JOBS[job_id]["segments"]     = data["segments"]
                            JOBS[job_id]["duration"]     = data.get("duration", 0)
                            JOBS[job_id]["preview_path"] = str(preview_json)
                            JOBS[job_id]["status"]       = "awaiting_confirm"
                        return
                    except Exception as e:
                        with JOBS_LOCK:
                            JOBS[job_id]["log"].append(
                                f"[Cache] Erreur lecture cache ({e}), re-détection."
                            )

            args = ["--preview-out", str(preview_json)] + _tail_args(opts)
            code = _run_pipeline(job_id, mode, video_path, args)
            if code != 0 or not preview_json.exists():
                with JOBS_LOCK:
                    JOBS[job_id]["status"] = "error"
                return

            with open(preview_json) as f:
                data = json.load(f)
            with JOBS_LOCK:
                JOBS[job_id]["segments"]     = data["segments"]
                JOBS[job_id]["duration"]     = data.get("duration", 0)
                JOBS[job_id]["preview_path"] = str(preview_json)
                JOBS[job_id]["status"]       = "awaiting_confirm"

            # FIX #6 : stocker dans le cache pour réutilisation ultérieure
            _preview_cache_store(video_path, mode, preview_json, opts)
            return

        # Pas de preview : run complet
        args  = ["--speed", str(speed)]
        args += _polish_args({**opts, "mode": mode})
        args += _tail_args(opts)
        code  = _run_pipeline(job_id, mode, video_path, args)
        _finish_job(job_id, video_path, mode, speed, code)

    except Exception as e:
        with JOBS_LOCK:
            JOBS[job_id]["status"] = "error"
            JOBS[job_id]["log"].append(f"[ERREUR] {e}")


# ─── Phase 2 : export après confirmation ──────────────────────────────────────

def job_export_from_preview(job_id):
    with JOBS_LOCK:
        job = JOBS[job_id]
        video_path = Path(job["video_path"])
        mode       = job["mode"]
        speed      = job["speed"]
        preview    = job["preview_path"]
        opts       = job.get("opts", {})
        JOBS[job_id]["status"] = "running"

    try:
        args  = ["--from-json", preview, "--speed", str(speed)]
        args += _polish_args({**opts, "mode": mode})
        code  = _run_pipeline(job_id, mode, video_path, args)
        _finish_job(job_id, video_path, mode, speed, code)
    except Exception as e:
        with JOBS_LOCK:
            JOBS[job_id]["status"] = "error"
            JOBS[job_id]["log"].append(f"[ERREUR] {e}")


def _finish_job(job_id, video_path, mode, speed, returncode):
    stem   = video_path.stem
    suffix = video_path.suffix
    speed_tag = f"_x{speed:.2f}".replace(".", "p") if speed != 1.0 else ""
    if mode == "silence":
        out_dir = video_path.parent / f"{stem}_nosilence{speed_tag}"
        output  = out_dir / f"{stem}_nosilence{speed_tag}{suffix}"
    else:
        out_dir = video_path.parent / f"{stem}_edited{speed_tag}"
        output  = out_dir / f"{stem}_edited{speed_tag}{suffix}"

    with JOBS_LOCK:
        if returncode == 0 and output.exists():
            JOBS[job_id]["status"] = "done"
            JOBS[job_id]["output"] = str(output)
        else:
            JOBS[job_id]["status"] = "error"


# ─── Queue worker (FIX #12) ───────────────────────────────────────────────────

def _queue_worker():
    """Worker thread qui pop des tâches de JOB_QUEUE et les exécute."""
    while True:
        try:
            task = JOB_QUEUE.get()
            if task is None:
                break
            job_id, save_path, mode, speed, preview, opts = task
            with JOBS_LOCK:
                if job_id in JOBS and JOBS[job_id]["status"] == "error":
                    # Job déjà annulé pendant qu'il était en queue → skip
                    JOB_QUEUE.task_done()
                    continue
            job_detect_or_run(job_id, save_path, mode, speed, preview, opts)
        except Exception as e:
            print(f"[queue worker] {e}")
        finally:
            try:
                JOB_QUEUE.task_done()
            except ValueError:
                pass


# Lancement des workers (au chargement du module pour qu'ils existent
# que ce soit en `python3 auto_edit_ui.py` direct ou via WSGI).
for _i in range(QUEUE_WORKERS):
    threading.Thread(target=_queue_worker, daemon=True, name=f"queue-worker-{_i}").start()


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    build = str(int(time.time()))
    html  = HTML.replace("__BUILD__", build)
    resp  = Response(html, mimetype="text/html")
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    resp.headers["Pragma"]        = "no-cache"
    return resp


@app.route("/upload", methods=["POST"])
def upload():
    mode    = request.form.get("mode", "silence")
    speed   = float(request.form.get("speed", "1.0"))
    preview = request.form.get("preview", "0") == "1"
    opts    = {
        "polish": request.form.get("polish", "1") == "1",
        "force_redetect": request.form.get("force_redetect", "0") == "1",
        "tail_relaxed": request.form.get("tail_relaxed", "0") == "1",
    }

    print(f"\n[Upload] mode={mode} speed={speed} preview={preview} opts={opts}")

    if mode == "elevenlabs" and "ELEVENLABS_API_KEY" not in os.environ:
        return jsonify({"error": "ELEVENLABS_API_KEY manquante dans ~/.zshrc"}), 400

    # FIX #12 : accepter plusieurs fichiers d'un coup
    files = request.files.getlist("file")
    if not files:
        # Fallback compat : ancien client envoyait juste un "file" simple
        f = request.files.get("file")
        files = [f] if f else []

    if not files:
        return jsonify({"error": "Pas de fichier reçu."}), 400

    job_ids = []
    for f in files:
        if not f or not f.filename:
            continue
        filename  = Path(f.filename).name.replace(" ", "_")
        save_path = UPLOAD_DIR / filename
        try:
            f.save(save_path)
            print(f"[Upload] {filename} : {save_path.stat().st_size // 1024 // 1024} MB")
        except Exception as e:
            print(f"[Upload] Erreur save {filename} : {e}")
            continue

        job_id = str(uuid.uuid4())
        with JOBS_LOCK:
            JOBS[job_id] = {
                "status": "queued", "log": [], "output": None,
                "segments": None, "duration": 0,
                "video_path": str(save_path),
                "mode": mode, "speed": speed, "opts": opts,
                "filename": filename,
            }
        JOB_QUEUE.put((job_id, save_path, mode, speed, preview, opts))
        job_ids.append(job_id)

    if not job_ids:
        return jsonify({"error": "Aucun fichier valide."}), 400

    # backward-compat : `job_id` = premier de la liste pour anciens clients
    return jsonify({"job_ids": job_ids, "job_id": job_ids[0]})


@app.route("/confirm/<job_id>", methods=["POST"])
def confirm(job_id):
    with JOBS_LOCK:
        job = JOBS.get(job_id)
        if not job:
            return jsonify({"error": "job introuvable"}), 404
        if job["status"] != "awaiting_confirm":
            return jsonify({"error": f"statut invalide : {job['status']}"}), 400
    t = threading.Thread(target=job_export_from_preview, args=(job_id,), daemon=True)
    t.start()
    return jsonify({"ok": True})


@app.route("/cancel/<job_id>", methods=["POST"])
def cancel(job_id):
    with JOBS_LOCK:
        if job_id in JOBS:
            JOBS[job_id]["status"] = "error"
            JOBS[job_id]["log"].append("[Annulé par l'utilisateur]")
    return jsonify({"ok": True})


@app.route("/status/<job_id>")
def status(job_id):
    from_idx = int(request.args.get("from", 0))
    with JOBS_LOCK:
        job = JOBS.get(job_id)
    if not job:
        return jsonify({"error": "job introuvable"}), 404
    return jsonify({
        "status":   job["status"],
        "log":      job["log"][from_idx:],
        "output":   job.get("output"),
        "segments": job.get("segments"),
        "duration": job.get("duration"),
    })


@app.route("/stream/<job_id>")
def stream(job_id):
    """
    FIX #15 : Server-Sent Events. Stream incrémental des logs + status.
    Le client peut basculer en fallback /status si SSE échoue.
    """
    def gen():
        last_idx = 0
        last_status = None
        keepalive_ts = time.time()
        while True:
            with JOBS_LOCK:
                job = JOBS.get(job_id)
                if not job:
                    yield f"event: error\ndata: {json.dumps({'error': 'job introuvable'})}\n\n"
                    return
                new_logs = job["log"][last_idx:]
                last_idx = len(job["log"])
                status_now = job["status"]
                payload = {
                    "status":   status_now,
                    "log":      new_logs,
                    "output":   job.get("output"),
                    "segments": job.get("segments"),
                    "duration": job.get("duration"),
                }
            if new_logs or status_now != last_status:
                yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
                last_status = status_now
                keepalive_ts = time.time()
            if status_now in ("done", "error"):
                return
            # keepalive toutes les 15s pour éviter timeouts proxy
            if time.time() - keepalive_ts > 15:
                yield ": keepalive\n\n"
                keepalive_ts = time.time()
            time.sleep(0.5)

    headers = {
        "Cache-Control":     "no-cache, no-store",
        "X-Accel-Buffering": "no",
        "Connection":        "keep-alive",
    }
    return Response(gen(), mimetype="text/event-stream", headers=headers)


@app.route("/reveal")
def reveal():
    path = request.args.get("path", "")
    if path and os.path.exists(path):
        subprocess.Popen(["open", "-R", path])
    return jsonify({"ok": True})


# ─── HTML ─────────────────────────────────────────────────────────────────────

HTML = r"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AutoEdit</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#0c0c0f;
  --surface:#141417;
  --surface2:#1c1c21;
  --border:#252529;
  --accent:#7c7cff;
  --accent2:#5c5cf0;
  --text:#eeeef0;
  --muted:#666672;
  --success:#34d399;
  --error:#f87171;
  --warn:#fbbf24;
  --r:14px;
}
body{
  background:var(--bg);color:var(--text);
  font-family:-apple-system,BlinkMacSystemFont,"SF Pro Display","Helvetica Neue",sans-serif;
  min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;
  gap:18px;padding:32px 20px;
}
.logo{font-size:20px;font-weight:700;letter-spacing:-0.5px}
.logo em{color:var(--accent);font-style:normal}

/* Mode selector */
.mode-selector{
  display:flex;background:var(--surface);border:1px solid var(--border);
  border-radius:99px;padding:4px;gap:2px;
}
.mode-btn{
  padding:8px 20px;border-radius:99px;border:none;
  font-size:13px;font-weight:500;cursor:pointer;
  background:transparent;color:var(--muted);transition:all .18s;white-space:nowrap;
}
.mode-btn.active{background:var(--accent);color:#fff}
.mode-btn:not(.active):hover{color:var(--text)}

/* Options row */
.options{display:flex;gap:10px;align-items:center;flex-wrap:wrap;justify-content:center}
.opt-toggle{
  display:flex;align-items:center;gap:8px;
  background:var(--surface);border:1px solid var(--border);
  border-radius:99px;padding:7px 14px 7px 8px;
  font-size:12px;color:var(--muted);cursor:pointer;user-select:none;
  transition:all .15s;
}
.opt-toggle:hover{color:var(--text)}
.opt-toggle.on{border-color:var(--accent);color:var(--accent);background:rgba(124,124,255,.05)}
.opt-dot{
  width:14px;height:14px;border-radius:50%;background:var(--border);
  transition:background .15s;flex-shrink:0;display:flex;align-items:center;justify-content:center;
  font-size:9px;color:#fff;font-weight:bold;
}
.opt-toggle.on .opt-dot{background:var(--accent)}

/* Drop zone */
#drop-zone{
  width:100%;max-width:500px;
  border:1.5px dashed var(--border);border-radius:var(--r);
  padding:64px 40px;text-align:center;cursor:pointer;
  transition:border-color .2s,background .2s,transform .15s;background:var(--surface);
}
#drop-zone:hover,#drop-zone.over{border-color:var(--accent);background:rgba(124,124,255,.05)}
#drop-zone.over{transform:scale(1.01)}
.drop-icon{font-size:44px;margin-bottom:16px;opacity:.85}
.drop-title{font-size:16px;font-weight:600;margin-bottom:6px}
.drop-sub{font-size:13px;color:var(--muted);line-height:1.5}
.drop-formats{display:inline-flex;gap:6px;margin-top:14px;flex-wrap:wrap;justify-content:center}
.fmt{
  font-size:11px;padding:3px 8px;border-radius:6px;
  background:var(--surface2);color:var(--muted);
  border:1px solid var(--border);font-family:monospace;
}

/* Card */
#card{
  width:100%;max-width:560px;
  background:var(--surface);border:1px solid var(--border);
  border-radius:var(--r);padding:24px;display:none;flex-direction:column;gap:20px;
}
.card-top{display:flex;align-items:flex-start;gap:14px}
.card-icon-wrap{
  width:44px;height:44px;border-radius:12px;background:var(--surface2);
  display:flex;align-items:center;justify-content:center;font-size:22px;flex-shrink:0;
}
.card-meta{flex:1;min-width:0}
.card-name{font-size:14px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.card-status{font-size:12px;color:var(--muted);margin-top:3px}
.badge{font-size:11px;font-weight:600;padding:4px 10px;border-radius:99px;white-space:nowrap;flex-shrink:0}
.badge-running{background:rgba(124,124,255,.15);color:var(--accent)}
.badge-done{background:rgba(52,211,153,.12);color:var(--success)}
.badge-error{background:rgba(248,113,113,.12);color:var(--error)}
.badge-upload{background:rgba(251,191,36,.12);color:var(--warn)}
.badge-preview{background:rgba(124,124,255,.12);color:var(--accent)}

#upload-row{display:none;flex-direction:column;gap:8px}
.upload-label{font-size:12px;color:var(--muted);display:flex;justify-content:space-between}
.process-label{font-size:12px;color:var(--muted);display:flex;justify-content:space-between;gap:12px}
.process-label strong{color:var(--text);font-weight:600}

.progress-wrap{background:var(--surface2);border-radius:99px;height:5px;overflow:hidden}
.progress-fill{height:100%;border-radius:99px;background:var(--accent);width:0%;transition:width .5s cubic-bezier(.4,0,.2,1)}
.progress-fill.indeterminate{width:35%;animation:slide 1.6s ease-in-out infinite}
@keyframes slide{0%{transform:translateX(-180%)}100%{transform:translateX(500%)}}
#main-progress-wrap{display:flex;flex-direction:column;gap:8px}

.steps{display:flex;flex-direction:column;gap:5px}
.step{
  font-size:13px;color:var(--muted);display:flex;align-items:center;gap:10px;
  padding:5px 0;transition:color .2s;
}
.step.active{color:var(--text)}
.step.done{color:var(--success)}
.step-indicator{
  width:7px;height:7px;border-radius:50%;background:var(--border);
  flex-shrink:0;transition:background .2s;
}
.step.active .step-indicator{background:var(--accent);box-shadow:0 0 8px var(--accent)}
.step.done  .step-indicator{background:var(--success)}
.step-label{flex:1}
.step-time{font-size:11px;color:var(--muted)}

details summary{
  font-size:12px;color:var(--muted);cursor:pointer;user-select:none;
  list-style:none;display:flex;align-items:center;gap:6px;
}
details summary::-webkit-details-marker{display:none}
.caret{display:inline-block;transition:transform .2s;font-size:10px}
details[open] .caret{transform:rotate(90deg)}
.log-box{
  background:var(--bg);border:1px solid var(--border);border-radius:10px;
  padding:12px 14px;font-family:"SF Mono","Fira Code","Menlo",monospace;
  font-size:11.5px;line-height:1.8;color:var(--muted);
  max-height:220px;overflow-y:auto;margin-top:10px;white-space:pre-wrap;word-break:break-all;
}
.log-line-step{color:var(--accent);font-weight:600}
.log-line-ok{color:var(--success)}
.log-line-err{color:var(--error)}

.done-box{
  background:var(--surface2);border:1px solid var(--border);border-radius:10px;
  padding:12px 14px;font-size:12px;font-family:"SF Mono","Fira Code","Menlo",monospace;
  color:var(--muted);word-break:break-all;line-height:1.5;
}
.actions{display:flex;gap:10px}
button{
  flex:1;padding:11px 16px;border-radius:10px;border:none;
  font-size:14px;font-weight:500;cursor:pointer;
  transition:opacity .15s,transform .1s;
}
button:active{transform:scale(.97)}
.btn-primary{background:var(--accent);color:#fff}
.btn-primary:hover{background:var(--accent2)}
.btn-secondary{background:var(--surface2);color:var(--text);border:1px solid var(--border)}
.btn-secondary:hover{opacity:.8}
.btn-danger{background:rgba(248,113,113,.1);color:var(--error);border:1px solid rgba(248,113,113,.3)}

/* Preview summary */
.preview-summary{
  display:flex;gap:16px;padding:14px;background:var(--surface2);
  border:1px solid var(--border);border-radius:10px;
}
.preview-stat{flex:1;text-align:center}
.preview-stat-val{font-size:20px;font-weight:700;color:var(--accent);line-height:1.2}
.preview-stat-lbl{font-size:10px;color:var(--muted);margin-top:4px;text-transform:uppercase;letter-spacing:0.5px}

/* Timeline */
.timeline-wrap{
  background:var(--surface2);border:1px solid var(--border);
  border-radius:10px;padding:14px;
}
.timeline-label{font-size:11px;color:var(--muted);margin-bottom:8px;display:flex;justify-content:space-between}
.timeline{
  position:relative;height:28px;background:var(--bg);border-radius:4px;overflow:hidden;
}
.timeline-seg{
  position:absolute;top:0;bottom:0;
  background:linear-gradient(180deg,var(--accent),var(--accent2));
  transition:opacity .15s;
}
.timeline-seg:hover{opacity:.8}

hr{border:none;border-top:1px solid var(--border);margin:0}
</style>
</head>
<body>

<div class="logo">Auto<em>Edit</em></div>

<!-- Mode selector -->
<div class="mode-selector">
  <button class="mode-btn active" id="btn-mode-silence"    onclick="setMode('silence')">✂️&nbsp; Silences seulement</button>
  <button class="mode-btn"        id="btn-mode-elevenlabs" onclick="setMode('elevenlabs')">🤖&nbsp; ElevenLabs + Claude</button>
</div>

<!-- Options : speed + preview -->
<div class="options">
  <div class="opt-toggle" id="opt-speed" onclick="toggleSpeed()">
    <span class="opt-dot"></span>
    <span>⚡ Accélérer 1.06×</span>
  </div>
  <div class="opt-toggle" id="opt-preview" onclick="togglePreview()">
    <span class="opt-dot"></span>
    <span>👁️ Aperçu avant export</span>
  </div>
  <div class="opt-toggle on" id="opt-polish" onclick="toggleOpt('polish')">
    <span class="opt-dot">✓</span>
    <span>🎚️ Polish audio</span>
  </div>
  <div class="opt-toggle" id="opt-tail_relaxed" onclick="toggleOpt('tail_relaxed')" title="Garde ~0.3s de plus après le dernier mot d'une phrase (évite les fins de mots rognées). Les débuts de phrase ne changent pas.">
    <span class="opt-dot"></span>
    <span>🫁 Fins de phrase relâchées</span>
  </div>
  <div class="opt-toggle" id="opt-force_redetect" onclick="toggleOpt('force_redetect')">
    <span class="opt-dot"></span>
    <span>🔄 Forcer re-détection</span>
  </div>
</div>

<div id="drop-zone" onclick="document.getElementById('file-input').click()">
  <div class="drop-icon">🎬</div>
  <div class="drop-title">Glisse ta vidéo ici</div>
  <div class="drop-sub">ou clique pour sélectionner un fichier</div>
  <div class="drop-formats">
    <span class="fmt">.mp4</span>
    <span class="fmt">.mov</span>
    <span class="fmt">.mkv</span>
    <span class="fmt">.avi</span>
  </div>
</div>
<input type="file" id="file-input" accept="video/*" multiple style="display:none">

<div id="card">

  <div class="card-top">
    <div class="card-icon-wrap" id="card-icon">⚙️</div>
    <div class="card-meta">
      <div class="card-name"   id="card-name">—</div>
      <div class="card-status" id="card-status">En attente…</div>
    </div>
    <div class="badge badge-running" id="badge">● EN COURS</div>
  </div>

  <div id="upload-row">
    <div class="upload-label">
      <span>Upload en cours…</span>
      <span id="upload-pct">0%</span>
    </div>
    <div class="progress-wrap">
      <div class="progress-fill" id="upload-bar" style="background:var(--warn)"></div>
    </div>
  </div>

  <div id="main-progress-wrap" style="display:none">
    <div class="process-label">
      <span id="progress-label">Traitement en cours…</span>
      <strong id="progress-pct">—</strong>
    </div>
    <div class="progress-wrap">
      <div class="progress-fill indeterminate" id="main-bar"></div>
    </div>
  </div>

  <!-- Steps silence -->
  <div class="steps" id="steps-silence" style="display:none">
    <div class="step" id="ss-1"><div class="step-indicator"></div><span class="step-label">Extraction audio</span><span class="step-time" id="st1"></span></div>
    <div class="step" id="ss-2"><div class="step-indicator"></div><span class="step-label">Détection silences (VAD)</span><span class="step-time" id="st2"></span></div>
    <div class="step" id="ss-3"><div class="step-indicator"></div><span class="step-label">Export vidéo</span><span class="step-time" id="st3"></span></div>
  </div>

  <!-- Steps elevenlabs -->
  <div class="steps" id="steps-elevenlabs" style="display:none">
    <div class="step" id="se-1"><div class="step-indicator"></div><span class="step-label">Extraction audio</span><span class="step-time" id="et1"></span></div>
    <div class="step" id="se-2"><div class="step-indicator"></div><span class="step-label">Détection silences (VAD)</span><span class="step-time" id="et2"></span></div>
    <div class="step" id="se-3"><div class="step-indicator"></div><span class="step-label">Transcription ElevenLabs</span><span class="step-time" id="et3"></span></div>
    <div class="step" id="se-4"><div class="step-indicator"></div><span class="step-label">Analyse & coupes Claude</span><span class="step-time" id="et4"></span></div>
    <div class="step" id="se-5"><div class="step-indicator"></div><span class="step-label">Export vidéo</span><span class="step-time" id="et5"></span></div>
  </div>

  <!-- Aperçu -->
  <div id="preview-section" style="display:none;flex-direction:column;gap:14px">
    <div class="preview-summary">
      <div class="preview-stat">
        <div class="preview-stat-val" id="prev-segs">—</div>
        <div class="preview-stat-lbl">Segments</div>
      </div>
      <div class="preview-stat">
        <div class="preview-stat-val" id="prev-kept">—</div>
        <div class="preview-stat-lbl">Conservé</div>
      </div>
      <div class="preview-stat">
        <div class="preview-stat-val" id="prev-cut">—</div>
        <div class="preview-stat-lbl">Coupé</div>
      </div>
    </div>
    <div class="timeline-wrap">
      <div class="timeline-label">
        <span>Timeline (segments conservés en couleur)</span>
        <span id="tl-dur">—</span>
      </div>
      <div class="timeline" id="timeline"></div>
    </div>
    <div class="actions">
      <button class="btn-primary"   id="btn-confirm">▶ Confirmer et exporter</button>
      <button class="btn-danger"    id="btn-cancel">Annuler</button>
    </div>
  </div>

  <hr id="log-hr" style="display:none">

  <details id="log-details" style="display:none">
    <summary><span class="caret">▶</span> Détails du traitement</summary>
    <div class="log-box" id="log-box"></div>
  </details>

  <div id="done-section" style="display:none;flex-direction:column;gap:14px">
    <hr>
    <div class="done-box" id="output-path"></div>
    <div class="actions">
      <button class="btn-primary"   id="btn-finder">📂 Ouvrir dans Finder</button>
      <button class="btn-secondary" id="btn-new">Nouvelle vidéo</button>
    </div>
  </div>

</div>

<script>
window.onerror = function(msg, src, line) {
  var d = document.createElement('div');
  d.style = 'position:fixed;bottom:0;left:0;right:0;background:#f87171;color:#000;padding:12px;font-family:monospace;font-size:12px;z-index:9999';
  d.textContent = 'JS ERROR: ' + msg + ' (ligne ' + line + ')';
  document.body.appendChild(d);
};

// ─── State ────────────────────────────────────────────────────────────────────
let mode            = 'silence';
let speedOn         = false;
let previewOn       = false;
let opts            = { polish: true, force_redetect: false, tail_relaxed: false };
let jobId           = null;
let pollTimer       = null;
let logLen          = 0;
let currentStepId   = null;
let currentStepStart= null;
let exportStarted   = false;

const STEPS = {
  silence: [
    { id:'ss-1', t:'st1', pattern:/\[1\/|extraction audio/i },
    { id:'ss-2', t:'st2', pattern:/\[2\/|d.tection.*silence|vad/i },
    { id:'ss-3', t:'st3', pattern:/\[3\/|export|encodage/i },
  ],
  elevenlabs: [
    { id:'se-1', t:'et1', pattern:/\[1\/|extraction audio/i },
    { id:'se-2', t:'et2', pattern:/\[2\/|d.tection.*silence|vad/i },
    { id:'se-3', t:'et3', pattern:/\[3\/|transcription|elevenlabs|scribe/i },
    { id:'se-4', t:'et4', pattern:/\[4\/|construction|coupes|claude/i },
    { id:'se-5', t:'et5', pattern:/export|encodage.*segment/i },
  ],
};

const dropZone  = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const card      = document.getElementById('card');

// ─── Toggles ──────────────────────────────────────────────────────────────────
function setMode(m) {
  mode = m;
  document.getElementById('btn-mode-silence').classList.toggle('active',    m === 'silence');
  document.getElementById('btn-mode-elevenlabs').classList.toggle('active', m === 'elevenlabs');
}
function toggleSpeed() {
  speedOn = !speedOn;
  document.getElementById('opt-speed').classList.toggle('on', speedOn);
  const dot = document.querySelector('#opt-speed .opt-dot');
  dot.textContent = speedOn ? '✓' : '';
}
function togglePreview() {
  previewOn = !previewOn;
  document.getElementById('opt-preview').classList.toggle('on', previewOn);
  const dot = document.querySelector('#opt-preview .opt-dot');
  dot.textContent = previewOn ? '✓' : '';
}
function toggleOpt(key) {
  opts[key] = !opts[key];
  const el  = document.getElementById('opt-' + key);
  el.classList.toggle('on', opts[key]);
  el.querySelector('.opt-dot').textContent = opts[key] ? '✓' : '';
}

// ─── Drag & Drop ──────────────────────────────────────────────────────────────
['dragenter','dragover'].forEach(ev => {
  window.addEventListener(ev, e => {
    e.preventDefault(); e.stopPropagation();
    if (e.dataTransfer) e.dataTransfer.dropEffect = 'copy';
    dropZone.classList.add('over');
  });
});
window.addEventListener('dragleave', e => {
  e.preventDefault();
  if (e.clientX === 0 && e.clientY === 0) dropZone.classList.remove('over');
});
window.addEventListener('drop', e => {
  e.preventDefault(); e.stopPropagation();
  dropZone.classList.remove('over');
  const files = e.dataTransfer.files;
  if (files && files.length) start(files);
});
fileInput.addEventListener('change', () => {
  if (fileInput.files && fileInput.files.length) start(fileInput.files);
});

// ─── Flow ─────────────────────────────────────────────────────────────────────
// FIX #12 : accepte un FileList. Premier fichier suivi dans la card, les autres
// tournent en background côté serveur (queue).
function start(filesOrFile) {
  let files;
  if (filesOrFile instanceof FileList) {
    files = Array.from(filesOrFile);
  } else if (Array.isArray(filesOrFile)) {
    files = filesOrFile;
  } else {
    files = [filesOrFile];
  }
  if (!files.length) return;
  const labelName = files.length === 1
    ? files[0].name
    : `${files[0].name}  (+${files.length - 1} en queue)`;
  showCard(labelName);
  upload(files);
}

function upload(files) {
  const fd  = new FormData();
  files.forEach(f => fd.append('file', f));
  fd.append('mode',    mode);
  fd.append('speed',     speedOn   ? '1.06' : '1.0');
  fd.append('preview',   previewOn ? '1'    : '0');
  fd.append('polish', opts.polish ? '1' : '0');
  fd.append('force_redetect', opts.force_redetect ? '1' : '0');
  fd.append('tail_relaxed', opts.tail_relaxed ? '1' : '0');

  const xhr = new XMLHttpRequest();
  xhr.upload.onprogress = e => {
    if (!e.lengthComputable) return;
    const pct = Math.round((e.loaded / e.total) * 100);
    document.getElementById('upload-bar').style.width = pct + '%';
    document.getElementById('upload-pct').textContent = pct + '%';
    if (pct === 100) {
      hide('upload-row'); show('main-progress-wrap'); show('steps-' + mode);
      show('log-hr'); show('log-details'); setBadge('running');
      document.getElementById('card-status').textContent = 'Traitement en cours…';
    }
  };
  xhr.onload = () => {
    let data;
    try { data = JSON.parse(xhr.responseText); }
    catch(e) { showError('Réponse invalide'); return; }
    if (data.error) { showError(data.error); return; }
    // FIX #12 : on suit le premier job. Les autres tournent en background.
    jobId  = data.job_id;
    logLen = 0;
    hide('upload-row'); show('main-progress-wrap'); show('steps-' + mode);
    show('log-hr'); show('log-details'); setBadge('running');
    const queued = (data.job_ids && data.job_ids.length) || 1;
    if (queued > 1) {
      document.getElementById('card-status').textContent =
        `Traitement (1/${queued})…  ${queued - 1} autre(s) en queue`;
    } else {
      document.getElementById('card-status').textContent = 'Traitement en cours…';
    }
    poll();
  };
  xhr.onerror = () => showError("Erreur réseau");
  xhr.open('POST', '/upload');
  xhr.send(fd);
}

// FIX #15 : SSE (EventSource) au lieu de poll 700ms.
// Fallback automatique sur /status si SSE échoue.
function poll() {
  if (pollTimer) { clearInterval(pollTimer); pollTimer = null; }
  if (window._es) { try { window._es.close(); } catch(e) {} window._es = null; }

  const trySse = () => {
    const es = new EventSource('/stream/' + jobId);
    window._es = es;
    let gotMessage = false;
    es.onmessage = (ev) => {
      gotMessage = true;
      let data;
      try { data = JSON.parse(ev.data); } catch(e) { return; }
      (data.log || []).forEach(line => {
        logLen++;
        if (detectProgress(line)) return;
        appendLog(line);
        detectStep(line);
      });
      if (data.status === 'awaiting_confirm') {
        es.close(); window._es = null;
        showPreview(data.segments || [], data.duration || 0);
      }
      if (data.status === 'done')  { es.close(); window._es = null; showDone(data.output); }
      if (data.status === 'error') { es.close(); window._es = null; showError('Erreur. Voir détails.'); }
    };
    es.onerror = () => {
      // Si jamais eu de message, fallback poll. Sinon (déjà connecté),
      // on laisse le navigateur retenter — sauf si fermé manuellement.
      try { es.close(); } catch(e) {}
      window._es = null;
      if (!gotMessage) startFallbackPoll();
    };
  };

  const startFallbackPoll = () => {
    if (pollTimer) clearInterval(pollTimer);
    pollTimer = setInterval(async () => {
      try {
        const res  = await fetch('/status/' + jobId + '?from=' + logLen);
        const data = await res.json();
        (data.log || []).forEach(line => {
          logLen++;
          if (detectProgress(line)) return;
          appendLog(line);
          detectStep(line);
        });
        if (data.status === 'awaiting_confirm') {
          clearInterval(pollTimer); pollTimer = null;
          showPreview(data.segments || [], data.duration || 0);
        }
        if (data.status === 'done')  { clearInterval(pollTimer); pollTimer = null; showDone(data.output); }
        if (data.status === 'error') { clearInterval(pollTimer); pollTimer = null; showError('Erreur. Voir détails.'); }
      } catch(e) { /* on retentera au tick suivant */ }
    }, 1500);
  };

  if (typeof EventSource !== 'undefined') {
    trySse();
  } else {
    startFallbackPoll();
  }
}

function detectStep(line) {
  const steps = STEPS[mode];
  steps.forEach(({id, t, pattern}, i) => {
    if (!pattern.test(line)) return;
    if (currentStepId && currentStepId !== id) {
      document.getElementById(currentStepId).className = 'step done';
      const prev = steps.find(s => s.id === currentStepId);
      if (prev) document.getElementById(prev.t).textContent =
        ((Date.now() - currentStepStart) / 1000).toFixed(0) + 's';
    }
    document.getElementById(id).className = 'step active';
    currentStepId = id; currentStepStart = Date.now();
    const bar = document.getElementById('main-bar');
    const isExportStep = i === steps.length - 1;
    if (isExportStep && !exportStarted) {
      bar.classList.add('indeterminate');
      bar.style.width = '35%';
      document.getElementById('progress-label').textContent = 'Préparation export…';
      document.getElementById('progress-pct').textContent = '—';
      return;
    }
    if (!exportStarted) {
      bar.classList.remove('indeterminate');
      const pct = Math.round(25 + (i / Math.max(1, steps.length - 1)) * 55);
      bar.style.width = pct + '%';
      document.getElementById('progress-label').textContent = 'Traitement en cours…';
      document.getElementById('progress-pct').textContent = pct + '%';
    }
  });
}

function detectProgress(line) {
  const m = line.match(/Progression export\s*:\s*([\d.]+)s\s*\/\s*([\d.]+)s\s*\((\d+)%\)/i);
  if (!m) return false;

  exportStarted = true;
  const done = Number(m[1]);
  const total = Number(m[2]);
  const pct = Math.max(0, Math.min(100, Number(m[3])));
  const bar = document.getElementById('main-bar');

  bar.classList.remove('indeterminate');
  bar.style.width = pct + '%';
  document.getElementById('progress-label').textContent =
    'Export vidéo : ' + fmtTime(done) + ' / ' + fmtTime(total);
  document.getElementById('progress-pct').textContent = pct + '%';
  document.getElementById('card-status').textContent = 'Export en cours…';
  return true;
}

function appendLog(line) {
  const box  = document.getElementById('log-box');
  const span = document.createElement('span');
  if (/^\[/.test(line))            span.className = 'log-line-step';
  else if (/✓|Terminé/.test(line)) span.className = 'log-line-ok';
  else if (/erreur|error/i.test(line)) span.className = 'log-line-err';
  span.textContent = line + '\n';
  box.appendChild(span); box.scrollTop = box.scrollHeight;
}

// ─── Preview ──────────────────────────────────────────────────────────────────
function showPreview(segments, duration) {
  document.getElementById('card-icon').textContent   = '👁️';
  document.getElementById('card-status').textContent = 'Aperçu — confirmer pour exporter';
  setBadge('preview');

  const kept = segments.reduce((a, [s, e]) => a + (e - s), 0);
  const cut  = duration - kept;

  document.getElementById('prev-segs').textContent = segments.length;
  document.getElementById('prev-kept').textContent = fmtTime(kept);
  document.getElementById('prev-cut').textContent  = fmtTime(cut);
  document.getElementById('tl-dur').textContent    = fmtTime(duration) + ' total';

  // Timeline : chaque segment = un bloc coloré proportionnel
  const tl = document.getElementById('timeline');
  tl.innerHTML = '';
  if (duration > 0) {
    segments.forEach(([s, e]) => {
      const div = document.createElement('div');
      div.className = 'timeline-seg';
      div.style.left  = (100 * s / duration)     + '%';
      div.style.width = (100 * (e - s) / duration) + '%';
      div.title = fmtTime(s) + ' → ' + fmtTime(e);
      tl.appendChild(div);
    });
  }

  show('preview-section');
  const bar = document.getElementById('main-bar');
  bar.classList.remove('indeterminate');
  bar.style.width = '60%';
  document.getElementById('progress-label').textContent = 'Détection terminée';
  document.getElementById('progress-pct').textContent = '60%';

  document.getElementById('btn-confirm').onclick = async () => {
    hide('preview-section');
    setBadge('running');
    document.getElementById('card-icon').textContent   = '⚙️';
    document.getElementById('card-status').textContent = 'Export en cours…';
    bar.classList.add('indeterminate'); bar.style.width = '35%';
    document.getElementById('progress-label').textContent = 'Préparation export…';
    document.getElementById('progress-pct').textContent = '—';
    exportStarted = false;
    await fetch('/confirm/' + jobId, { method: 'POST' });
    poll();
  };
  document.getElementById('btn-cancel').onclick = async () => {
    await fetch('/cancel/' + jobId, { method: 'POST' });
    resetToDrop();
  };
}

function fmtTime(s) {
  s = Math.round(s);
  const m = Math.floor(s / 60), ss = s % 60;
  return m + ':' + String(ss).padStart(2, '0');
}

// ─── UI states ────────────────────────────────────────────────────────────────
function showCard(name) {
  dropZone.style.display = 'none';
  card.style.display     = 'flex';

  document.getElementById('card-name').textContent   = name;
  document.getElementById('card-status').textContent = 'Upload…';
  document.getElementById('card-icon').textContent   = '⚙️';
  document.getElementById('log-box').innerHTML       = '';
  document.getElementById('output-path').textContent = '';
  document.getElementById('done-section').style.display    = 'none';
  document.getElementById('preview-section').style.display = 'none';
  document.getElementById('upload-bar').style.width  = '0%';
  document.getElementById('main-bar').classList.add('indeterminate');
  document.getElementById('main-bar').style.width    = '0%';
  document.getElementById('main-bar').style.background = 'var(--accent)';
  document.getElementById('progress-label').textContent = 'Traitement en cours…';
  document.getElementById('progress-pct').textContent = '—';

  ['silence','elevenlabs'].forEach(m => {
    STEPS[m].forEach(({id, t}) => {
      document.getElementById(id).className = 'step';
      document.getElementById(t).textContent = '';
    });
    hide('steps-' + m);
  });
  currentStepId = null;
  exportStarted = false;

  show('upload-row'); hide('main-progress-wrap');
  hide('log-hr');     hide('log-details');
  setBadge('upload'); logLen = 0;
}

function showDone(output) {
  document.getElementById('card-icon').textContent   = '✅';
  document.getElementById('card-status').textContent = 'Vidéo éditée avec succès';
  setBadge('done');
  if (currentStepId) document.getElementById(currentStepId).className = 'step done';
  const bar = document.getElementById('main-bar');
  bar.classList.remove('indeterminate');
  bar.style.width = '100%';
  document.getElementById('progress-label').textContent = 'Export terminé';
  document.getElementById('progress-pct').textContent = '100%';
  document.getElementById('output-path').textContent = output;
  document.getElementById('done-section').style.display = 'flex';
  document.getElementById('log-details').open = false;

  document.getElementById('btn-finder').onclick = async () => {
    await fetch('/reveal?path=' + encodeURIComponent(output));
  };
  document.getElementById('btn-new').onclick = resetToDrop;
}

function resetToDrop() {
  dropZone.style.display = ''; card.style.display = 'none';
  fileInput.value = ''; jobId = null;
}

function showError(msg) {
  document.getElementById('card-icon').textContent   = '❌';
  document.getElementById('card-status').textContent = msg;
  setBadge('error');
  const bar = document.getElementById('main-bar');
  bar.classList.remove('indeterminate');
  bar.style.width      = '100%';
  bar.style.background = 'var(--error)';
  document.getElementById('log-details').open = true;
}

function setBadge(type) {
  const b = document.getElementById('badge');
  const map = {
    upload:  ['badge-upload',  '↑ UPLOAD'],
    running: ['badge-running', '● EN COURS'],
    done:    ['badge-done',    '✓ TERMINÉ'],
    error:   ['badge-error',   '✕ ERREUR'],
    preview: ['badge-preview', '👁 APERÇU'],
  };
  const [cls, label] = map[type];
  b.className   = 'badge ' + cls;
  b.textContent = label;
}

function show(id) { document.getElementById(id).style.display = ''; }
function hide(id) { document.getElementById(id).style.display = 'none'; }
</script>
</body>
</html>"""


# ─── Main ─────────────────────────────────────────────────────────────────────

def open_browser():
    time.sleep(1.2)
    subprocess.Popen(["open", f"http://localhost:{PORT}"])

if __name__ == "__main__":
    threading.Thread(target=open_browser, daemon=True).start()
    print(f"✓ AutoEdit UI démarré → http://localhost:{PORT}")
    print(f"  Fichiers traités    → {UPLOAD_DIR}")
    print(f"  Aperçus JSON        → {PREVIEW_DIR}")
    print(f"  Ctrl+C pour arrêter\n")
    app.run(host="127.0.0.1", port=PORT, debug=False, threaded=True)
