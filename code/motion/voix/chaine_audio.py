"""Chaîne d'amélioration de la voix, vendue depuis le pipeline auto-edit de Lucien.

Origine du code :
- `~/CODE/auto-edit/auto_edit.py` : constantes de la chaîne, `polish_audio`,
  `_vad_speech_gate`, `_measure_chain_latency`, `_measure_loudness`,
  `load_audio_mono`.
- `~/CODE/auto-edit/multicam.py` : `_chunked_deepfilternet_denoise`.
- Valeurs décrites dans `montage-multicam/references/chaine-audio.md`.
  Elles viennent d'un calage Optuna contre Auphonic. Ne pas les modifier sans mesure.

Écarts assumés avec l'original, sans changement de réglage :
1. Les étapes échouent avec une erreur claire. L'original passait un étage
   en silence quand DeepFilterNet, Silero ou scipy manquait.
2. Les fichiers intermédiaires sont en flottant 32 bits. L'original écrivait
   du PCM 16 bits entre les étages. On évite ainsi une requantification.
3. Le gate lit Silero depuis le paquet pip `silero-vad` épinglé.
   L'original passait par `torch.hub`, qui télécharge la branche principale.
4. Le rééchantillonnage 48 kHz vers 16 kHz du gate appelle `soxr` en
   qualité `soxr_hq`. C'est l'appel exact que fait `librosa.resample` par défaut.
5. La sortie est un WAV 48 kHz de même durée que l'entrée. L'original muxait
   directement dans la vidéo en AAC. Le recalage de latence est identique.
6. DeepFilterNet et Silero tournent sur un fil torch chacun. Sur le conteneur
   4 CPU, quatre fils rendent Silero trente fois plus lent.
7. Retour de 192 kHz à 48 kHz après loudnorm dynamique : soxr en précision
   par défaut (20 bits). En précision 28, ffmpeg 6.1 restait bloqué sans fin
   à 3 s de la fin, sur 22 min de voix réelle. Écart entre les deux : -100 dB,
   décalage inférieur à 0,1 µs. L'original passait par le rééchantillonneur swr.
   Tous les appels ffmpeg partent aussi avec `-nostdin` et stdin sur /dev/null.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from functools import lru_cache
from pathlib import Path

# ─── Réglages figés (auto_edit.py, lignes 119 à 160) ─────────────────────────
LOUDNESS_TARGET_LUFS = -15.76
LOUDNESS_TRUE_PEAK   = -1.19
LOUDNESS_LRA         = 6.3
HPF_FREQ_HZ          = 65
LPF_FREQ_HZ          = 12110
AFFTDN_NR            = 4.2     # bas car DeepFilterNet a déjà débruité
DEESSER_INTENSITY    = 0.17
COMP_THRESH_DB       = -19.6
COMP_RATIO           = 2.16
COMP_ATTACK_MS       = 14
COMP_RELEASE_MS      = 186
COMP_MAKEUP_DB       = 1.96

# AutoEQ : 7 bandes calées sur la réponse Auphonic après DeepFilterNet
VOICE_EQ_CURVE = [
    (250,   1.0,  +4.13),  # chaleur
    (500,   1.4,  -3.04),  # retrait de boue
    (1500,  1.0,  +2.65),  # basse présence
    (3000,  1.0,  +8.72),  # présence forte
    (5500,  1.2,  +3.63),  # clarté
    (8500,  1.0,  +1.99),  # air
    (11000, 1.2,  +3.18),  # haut de l'air
]

BWE_AMOUNT = 0.23
BWE_DRIVE  = 4.1
BWE_FREQ   = 6500
BWE_CEIL   = 14000

VAD_GATE_ATTEN_DB = 80          # plancher des segments non-voix
VAD_GATE_PAD_MS   = 60          # marge avant et après chaque segment voix
VAD_GATE_FADE_MS  = 30          # fondu contre les claquements

AUDIO_SR = 48000

DFN_CHUNK_S = 120.0             # multicam.py : blocs de 120 s
DFN_CTX_S = 1.0                 # contexte jeté de chaque côté du bloc

DFN_MODEL = "DeepFilterNet3"
DFN_REPO = "https://github.com/Rikorose/DeepFilterNet"


class ChaineAudioErreur(RuntimeError):
    """Un étage de la chaîne a échoué. La chaîne ne se contourne jamais en silence."""


def log(message: str) -> None:
    print(message, flush=True)


def lancer(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    """subprocess.run sans entrée standard.

    ffmpeg lit sinon les touches sur stdin. Lancé depuis un shell dont stdin est
    une socket, la passe 2 de loudnorm est restée bloquée à 3 s de la fin
    sur 22 min d'audio. `-nostdin` et /dev/null ferment cette porte.
    """
    if cmd and Path(cmd[0]).name == "ffmpeg" and "-nostdin" not in cmd:
        cmd = [cmd[0], "-nostdin", *cmd[1:]]
    return subprocess.run(cmd, stdin=subprocess.DEVNULL, **kwargs)


def run(cmd: list[str], desc: str = "commande") -> subprocess.CompletedProcess:
    """auto_edit.run, avec une exception au lieu de sys.exit."""
    result = lancer(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise ChaineAudioErreur(f"{desc} : {result.stderr[-800:]}")
    return result


# ─── Chargement audio (auto_edit.load_audio_mono, version numpy) ─────────────

def load_audio_mono(path: str, sr: int = 16000):
    """Charge un audio en float32 mono à `sr` Hz, décodé par ffmpeg.

    auto_edit.load_audio_mono renvoyait un tenseur torch depuis du s16le.
    Ici le flux reste en f32le pour ne pas quantifier, et le résultat est numpy.
    """
    import numpy as np

    proc = lancer(
        ["ffmpeg", "-v", "error", "-i", path, "-vn",
         "-f", "f32le", "-acodec", "pcm_f32le", "-ac", "1", "-ar", str(sr), "-"],
        capture_output=True,
    )
    if proc.returncode != 0 or not proc.stdout:
        raise ChaineAudioErreur(
            f"ffmpeg n'a pas pu décoder {path} : "
            f"{proc.stderr.decode(errors='replace')[:300]}"
        )
    return np.frombuffer(proc.stdout, dtype=np.float32).copy()


# ─── Préparation des modèles ─────────────────────────────────────────────────

def _shim_torchaudio_backend() -> None:
    """Shim torchaudio.backend.common.AudioMetaData (retiré en torchaudio 2.11)."""
    import types
    if "torchaudio.backend.common" not in sys.modules:
        tb = types.ModuleType("torchaudio.backend")
        tbc = types.ModuleType("torchaudio.backend.common")

        class _Stub:
            pass

        tbc.AudioMetaData = _Stub
        sys.modules["torchaudio.backend"] = tb
        sys.modules["torchaudio.backend.common"] = tbc
        import torchaudio as _ta
        _ta.backend = tb


def _dfn_cache_dir() -> Path:
    from appdirs import user_cache_dir
    return Path(user_cache_dir("DeepFilterNet"))


def preparer_modele_deepfilternet() -> Path:
    """Garantit la présence de DeepFilterNet3 dans le cache de `df`.

    `df` télécharge le modèle par HTTPS depuis github.com/…/raw/main/models.
    Le proxy du conteneur cloud refuse ce chemin (403) mais sert les lectures git.
    En secours, on lit donc `models/DeepFilterNet3.zip` par un clone git partiel.
    """
    import zipfile

    cache = _dfn_cache_dir()
    model_dir = cache / DFN_MODEL
    if (model_dir / "config.ini").is_file():
        return model_dir
    cache.mkdir(parents=True, exist_ok=True)
    try:
        _shim_torchaudio_backend()
        from df.enhance import maybe_download_model
        maybe_download_model(DFN_MODEL)
    except (Exception, SystemExit) as exc:  # noqa: BLE001 - df appelle exit() sur un 403
        log(f"  Téléchargement HTTPS du modèle refusé ({exc}). Secours par git.")
    if (model_dir / "config.ini").is_file():
        return model_dir
    with tempfile.TemporaryDirectory() as tmp:
        clone = Path(tmp) / "dfn"
        env = dict(os.environ, GIT_LFS_SKIP_SMUDGE="1")
        for cmd in (
            ["git", "clone", "--depth", "1", "--filter=blob:none", "--sparse",
             DFN_REPO, str(clone)],
            ["git", "-C", str(clone), "sparse-checkout", "set", "models"],
        ):
            r = lancer(cmd, capture_output=True, text=True, env=env)
            if r.returncode != 0:
                raise ChaineAudioErreur(
                    f"Modèle {DFN_MODEL} introuvable. git a échoué : {r.stderr[-400:]}")
        archive = clone / "models" / f"{DFN_MODEL}.zip"
        if not archive.is_file() or not zipfile.is_zipfile(archive):
            raise ChaineAudioErreur(f"Archive {archive.name} absente du dépôt DeepFilterNet.")
        with zipfile.ZipFile(archive) as z:
            z.extractall(cache)
    if not (model_dir / "config.ini").is_file():
        raise ChaineAudioErreur(f"Modèle {DFN_MODEL} absent de {cache} après extraction.")
    return model_dir


def verifier_dependances(denoise: bool = True) -> None:
    """Échoue tôt, avant tout long calcul, si un étage manque."""
    manquants = []
    for module in ("numpy", "soundfile", "soxr", "scipy"):
        try:
            __import__(module)
        except ImportError:
            manquants.append(module)
    if denoise:
        for module in ("torch", "silero_vad", "appdirs"):
            try:
                __import__(module)
            except ImportError:
                manquants.append(module)
        try:
            _shim_torchaudio_backend()
            import df.enhance  # noqa: F401
        except ImportError as exc:
            manquants.append(f"deepfilternet ({exc})")
    if manquants:
        raise ChaineAudioErreur(
            "Dépendances absentes : " + ", ".join(manquants)
            + ". Lancer : .venv/bin/pip install -r voix/requirements.txt"
            " && .venv/bin/pip install --no-deps deepfilternet==0.5.6"
        )
    if denoise:
        preparer_modele_deepfilternet()


# ─── Étage 1 : DeepFilterNet3 par blocs (multicam._chunked_deepfilternet_denoise)

def _chunked_deepfilternet_denoise(audio_in_wav: str, chunk_s: float = DFN_CHUNK_S,
                                   ctx_s: float = DFN_CTX_S) -> str:
    """DeepFilterNet3 appliqué par blocs de chunk_s, élargis de ctx_s de chaque côté.

    Le contexte est jeté après coup pour des frontières sans couture. Le champ
    réceptif du réseau est bien inférieur à 1 s. Le pic mémoire reste borné à un bloc.
    Sortie : WAV 48 kHz flottant à côté de l'entrée.
    """
    try:
        _shim_torchaudio_backend()
        from df.enhance import enhance, init_df
        import numpy as np
        import soundfile as sf
        import torch
    except ImportError as exc:
        raise ChaineAudioErreur(f"DeepFilterNet indisponible : {exc}") from exc

    preparer_modele_deepfilternet()
    torch.set_num_threads(1)
    df_model, df_state, _ = init_df(log_level="WARNING", log_file=None)
    sr = df_state.sr()
    audio, src_sr = sf.read(audio_in_wav, dtype="float32")
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    audio = audio.astype(np.float32)
    if src_sr != sr:
        import soxr
        audio = soxr.resample(audio, src_sr, sr, quality="soxr_hq").astype(np.float32)
    n = len(audio)
    chunk = int(chunk_s * sr)
    ctx = int(ctx_s * sr)
    n_chunks = (n + chunk - 1) // chunk
    log(f"  DeepFilterNet3 (débruitage ML, {n_chunks} blocs de {chunk_s:.0f} s)...")
    out = np.zeros(n, dtype=np.float32)
    pos = 0
    t0 = time.time()
    while pos < n:
        a = max(0, pos - ctx)
        b = min(n, pos + chunk + ctx)
        seg = torch.from_numpy(audio[a:b].copy()).unsqueeze(0)
        with torch.no_grad():
            enh = enhance(df_model, df_state, seg).squeeze().cpu().numpy()[: b - a]
        s = pos - a
        end = min(pos + chunk, n)
        out[pos:end] = enh[s: s + (end - pos)]
        pos += chunk
        del seg, enh
        log(f"    bloc {pos // chunk}/{n_chunks} ({time.time() - t0:.0f} s)")
    out_path = audio_in_wav.replace(".wav", "_dfnet.wav")
    sf.write(out_path, out[:n], sr, subtype="FLOAT")
    return out_path


# ─── Étage 2 : gate de voix par VAD (auto_edit._vad_speech_gate) ─────────────

def charger_silero():
    """Silero-VAD : (modèle, get_speech_timestamps).

    Dépôt local d'abord (SILERO_VAD_DIR avec un hubconf.py, lu par torch.hub en source locale) :
    GitHub refuse torch.hub dans le cloud. Sinon le paquet pip `silero-vad` épinglé.
    """
    local = os.environ.get("SILERO_VAD_DIR")
    if local and os.path.isfile(os.path.join(local, "hubconf.py")):
        import torch
        model, utils = torch.hub.load(repo_or_dir=local, model="silero_vad", source="local")
        return model, utils[0]
    from silero_vad import get_speech_timestamps, load_silero_vad
    return load_silero_vad(), get_speech_timestamps


def _vad_speech_gate(audio_in_wav: str,
                     atten_db: float = VAD_GATE_ATTEN_DB, pad_ms: float = VAD_GATE_PAD_MS,
                     fade_ms: float = VAD_GATE_FADE_MS,
                     vad_threshold: float = 0.35, min_silence_ms: int = 120) -> dict:
    """Silence les segments non-voix avec un gate -80 dB et un fondu.

    C'est ce que fait Auphonic : plancher -180 dB contre -72 dB pour DeepFilterNet seul.
    """
    try:
        import numpy as _np
        import soundfile as sf
        import soxr
        import torch as _torch
        from scipy.ndimage import uniform_filter1d
        model, get_speech_timestamps = charger_silero()
    except ImportError as exc:
        raise ChaineAudioErreur(f"Gate VAD indisponible : {exc}") from exc

    log(f"  Gate de voix VAD (plancher -{atten_db} dB, marge {pad_ms} ms)...")
    _torch.set_num_threads(1)
    y, sr = sf.read(audio_in_wav, dtype="float32")
    if y.ndim > 1:
        y = y.mean(axis=1)
    y = y.astype(_np.float32)

    # librosa.resample(res_type="soxr_hq") appelle exactement soxr.resample.
    y16 = soxr.resample(y, sr, 16000, quality="soxr_hq").astype(_np.float32) if sr != 16000 else y
    ts = get_speech_timestamps(
        _torch.from_numpy(y16), model, sampling_rate=16000,
        threshold=vad_threshold, min_speech_duration_ms=80,
        min_silence_duration_ms=min_silence_ms, return_seconds=True,
    )

    floor = 10 ** (-atten_db / 20.0)  # -80 dB → 0.0001
    fade_samp = int(sr * fade_ms / 1000)
    env = _np.full(len(y), floor, dtype=_np.float32)
    for t in ts:
        s = max(0, int((t["start"] - pad_ms / 1000) * sr))
        e = min(len(y), int((t["end"] + pad_ms / 1000) * sr))
        env[s:e] = 1.0
    env = uniform_filter1d(env, size=max(2, fade_samp * 2))

    sf.write(audio_in_wav, (y * env).astype(_np.float32), sr, subtype="FLOAT")
    voix = sum(t["end"] - t["start"] for t in ts)
    return {"segments_voix": len(ts), "secondes_voix": round(voix, 2)}


# ─── Latence et niveau (auto_edit._measure_chain_latency, _measure_loudness) ──

def _measure_chain_latency(filter_chain_str: str, sr: int = AUDIO_SR,
                           duration_s: float = 3.0) -> float:
    """Latence (retard de groupe) d'une chaîne de filtres, mesurée par impulsion.

    Sans compensation, la chaîne décale l'énergie audio de 30 à 60 ms.
    """
    import numpy as _np
    import soundfile as _sf

    with tempfile.TemporaryDirectory() as tmp:
        imp_in = os.path.join(tmp, "impulse_in.wav")
        imp_out = os.path.join(tmp, "impulse_out.wav")

        n = int(sr * duration_s)
        impulse_pos = sr  # impulsion à t=1,0 s
        sig = _np.zeros(n, dtype=_np.float32)
        sig[impulse_pos] = 1.0
        _sf.write(imp_in, sig, sr)

        r = lancer([
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-i", imp_in, "-af", filter_chain_str,
            "-c:a", "pcm_f32le", "-ar", str(sr), imp_out,
        ], capture_output=True, text=True)
        if r.returncode != 0:
            raise ChaineAudioErreur(f"Mesure de latence impossible : {r.stderr[-400:]}")

        out, _ = _sf.read(imp_out)
        if out.ndim > 1:
            out = out.mean(axis=1)
        # Pic cherché dans [-50 ms, +300 ms] autour de l'impulsion
        search_start = max(0, impulse_pos - int(sr * 0.05))
        search_end = min(len(out), impulse_pos + int(sr * 0.3))
        region = out[search_start:search_end]
        if len(region) == 0:
            return 0.0
        peak_idx = search_start + int(_np.argmax(_np.abs(region)))
        return max(0.0, (peak_idx - impulse_pos) / sr)


def _loudnorm_json(stderr: str) -> dict | None:
    start = stderr.rfind("{")
    end = stderr.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        return json.loads(stderr[start:end + 1])
    except json.JSONDecodeError:
        return None


@lru_cache(maxsize=1)
def _aresample_48k() -> str:
    """Filtre 48 kHz : SWR, le rééchantillonneur de l'original auto-edit.

    soxr bloquait ffmpeg 6.1 à la vidange finale, même en précision par défaut :
    3 s avant la fin sur une voix de 80 s, le 27/09/2026. SWR finit au bon compte.
    VOIX_RESAMPLER=soxr rétablit soxr.
    """
    if os.environ.get("VOIX_RESAMPLER") == "soxr":
        return "aresample=48000:resampler=soxr"
    return "aresample=48000"


def _measure_loudness(audio_path: str, target_lufs: float) -> dict | None:
    """Passe 1 de loudnorm. Renvoie les mesures de la passe 2, ou None si quasi muet."""
    result = lancer([
        "ffmpeg", "-hide_banner", "-nostats", "-i", audio_path,
        "-af", f"loudnorm=I={target_lufs}:TP={LOUDNESS_TRUE_PEAK}:"
               f"LRA={LOUDNESS_LRA}:print_format=json",
        "-f", "null", "-",
    ], capture_output=True, text=True)
    data = _loudnorm_json(result.stderr or "")
    required = ("input_i", "input_tp", "input_lra", "input_thresh", "target_offset")
    if not data or not all(k in data for k in required):
        return None
    try:
        if float(data["input_i"]) < -70:
            return None
    except (ValueError, TypeError):
        return None
    return data


def mesurer_niveau(audio_path: str) -> dict:
    """Niveau intégré, pic vrai et LRA d'un fichier, lus par loudnorm."""
    result = lancer([
        "ffmpeg", "-hide_banner", "-nostats", "-i", audio_path, "-vn",
        "-af", f"loudnorm=I={LOUDNESS_TARGET_LUFS}:TP={LOUDNESS_TRUE_PEAK}:"
               f"LRA={LOUDNESS_LRA}:print_format=json",
        "-f", "null", "-",
    ], capture_output=True, text=True)
    data = _loudnorm_json(result.stderr or "")
    if not data:
        raise ChaineAudioErreur(f"Mesure de niveau impossible sur {audio_path}")
    return {
        "integre_lufs": float(data["input_i"]),
        "pic_vrai_dbtp": float(data["input_tp"]),
        "lra_lu": float(data["input_lra"]),
    }


# ─── Chaîne complète (auto_edit.polish_audio, sortie WAV) ────────────────────

def construire_filtres(denoise: bool = True) -> str:
    """Étages 3 à 9, exactement dans l'ordre de polish_audio.

    polish_audio est appelé avec deesser, hpf, autoeq et bwe actifs,
    deplosive et hum inactifs.
    """
    chain = []
    if denoise:
        chain.append(f"afftdn=nr={AFFTDN_NR}:nf=-25")
    chain.append(f"highpass=f={HPF_FREQ_HZ}:p=2")
    chain.append(f"lowpass=f={LPF_FREQ_HZ}")
    for f, q, g in VOICE_EQ_CURVE:
        chain.append(f"equalizer=f={f}:t=q:w={q}:g={g}")
    # Exciter AVANT le compresseur, sinon ses harmoniques sont recomprimées
    chain.append(
        f"aexciter=amount={BWE_AMOUNT}:drive={BWE_DRIVE}"
        f":blend=0:freq={BWE_FREQ}:ceil={BWE_CEIL}"
    )
    chain.append(f"deesser=i={DEESSER_INTENSITY}")
    # Étage dynamique UNIQUE. compand et dynaudnorm retirés (pompage).
    chain.append(
        f"acompressor=threshold={COMP_THRESH_DB}dB:ratio={COMP_RATIO}"
        f":attack={COMP_ATTACK_MS}:release={COMP_RELEASE_MS}"
        f":makeup={COMP_MAKEUP_DB}"
    )
    return ",".join(chain)


def extraire_48k(source: str, destination: str) -> dict:
    """Étage 0 : WAV 48 kHz mono. Flottant 32 bits au lieu de PCM 16 bits."""
    import soundfile as sf
    run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", source, "-vn", "-ar", str(AUDIO_SR), "-ac", "1",
        "-c:a", "pcm_f32le", destination,
    ], f"extraction audio de {source}")
    info = sf.info(destination)
    return {"echantillons": int(info.frames), "duree_s": info.frames / info.samplerate}


def ameliorer_wav(audio_48k: str, sortie: str, denoise: bool = True,
                  lufs: float = LOUDNESS_TARGET_LUFS) -> dict:
    """Applique la chaîne une seule fois sur un WAV complet 48 kHz mono.

    La sortie garde exactement le nombre d'échantillons de l'entrée.
    Le temps 0 de la sortie correspond au temps 0 de l'entrée, latence compensée.
    """
    import soundfile as sf

    info = sf.info(audio_48k)
    if info.samplerate != AUDIO_SR or info.channels != 1:
        raise ChaineAudioErreur(f"{audio_48k} doit être en 48 kHz mono.")
    n_samples = int(info.frames)
    duree = n_samples / AUDIO_SR
    rapport: dict = {"denoise": denoise, "duree_s": round(duree, 6), "temps_s": {}}
    t_total = time.time()

    with tempfile.TemporaryDirectory(dir=os.path.dirname(os.path.abspath(sortie))) as tmp:
        audio_in = os.path.join(tmp, "audio_48k.wav")
        audio_eq = os.path.join(tmp, "audio_eq.wav")
        shutil.copyfile(audio_48k, audio_in)

        if denoise:
            t = time.time()
            audio_in = _chunked_deepfilternet_denoise(audio_in)
            rapport["temps_s"]["deepfilternet"] = round(time.time() - t, 2)
            t = time.time()
            rapport["gate_vad"] = _vad_speech_gate(audio_in)
            rapport["temps_s"]["gate_vad"] = round(time.time() - t, 2)

        af_base = construire_filtres(denoise)
        rapport["filtres"] = af_base
        log(f"  Chaîne de filtres : {af_base}")
        chain_latency_s = _measure_chain_latency(af_base, sr=AUDIO_SR)
        rapport["latence_chaine_ms"] = round(chain_latency_s * 1000, 3)
        log(f"  Latence de chaîne mesurée : {chain_latency_s * 1000:.1f} ms (compensée)")

        t = time.time()
        run([
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-i", audio_in, "-af", af_base,
            "-c:a", "pcm_f32le", "-ar", str(AUDIO_SR), audio_eq,
        ], "chaîne de filtres (étage A)")
        rapport["temps_s"]["filtres"] = round(time.time() - t, 2)

        # Étage B : loudnorm deux passes (EBU R128)
        t = time.time()
        log("  Loudnorm passe 1 (mesure)...")
        measured = _measure_loudness(audio_eq, lufs)
        if not measured:
            raise ChaineAudioErreur(
                "Loudnorm passe 1 impossible : audio quasi muet ou mesure illisible.")
        rapport["loudnorm_passe1"] = {k: measured[k] for k in
                                      ("input_i", "input_tp", "input_lra", "input_thresh",
                                       "target_offset")}
        log(f"    mesuré : I={measured['input_i']} LUFS  TP={measured['input_tp']} dBTP  "
            f"LRA={measured['input_lra']} LU")
        ln_filter = (
            f"loudnorm=I={lufs}:TP={LOUDNESS_TRUE_PEAK}:LRA={LOUDNESS_LRA}"
            f":measured_I={measured['input_i']}"
            f":measured_TP={measured['input_tp']}"
            f":measured_LRA={measured['input_lra']}"
            f":measured_thresh={measured['input_thresh']}"
            f":offset={measured['target_offset']}"
            f":linear=true:print_format=json"
        )
        # Compensation de latence : atrim AVANT loudnorm, apad sur la durée exacte.
        # loudnorm sort en 192 kHz en mode dynamique : retour en 48 kHz par SWR.
        # soxr bloque ffmpeg 6.1 à la vidange finale (écart 7, voir _aresample_48k).
        parts = []
        if chain_latency_s > 0.001:
            parts.append(f"atrim=start={chain_latency_s:.6f},asetpts=PTS-STARTPTS")
        parts.append(ln_filter)
        parts.append(_aresample_48k())
        parts.append(f"apad=whole_len={n_samples}")
        af_final = ",".join(parts)
        log("  Loudnorm passe 2 + compensation de latence...")
        r = run([
            "ffmpeg", "-y", "-hide_banner", "-nostats",
            "-i", audio_eq, "-af", af_final,
            "-c:a", "pcm_f32le", "-ar", str(AUDIO_SR), "-ac", "1",
            "-frames:a", str(n_samples), sortie,
        ], "loudnorm passe 2")
        passe2 = _loudnorm_json(r.stderr) or {}
        rapport["loudnorm_passe2"] = {k: passe2.get(k) for k in
                                      ("output_i", "output_tp", "output_lra",
                                       "normalization_type")}
        rapport["temps_s"]["loudnorm"] = round(time.time() - t, 2)

        # Étage C : correction de niveau. Sur une voix très dynamique, loudnorm
        # quitte le mode linéaire et rate la cible de plusieurs dixièmes de LU.
        # Gain statique vers la cible, puis limiteur sous le pic vrai visé.
        mesure = _measure_loudness(sortie, lufs)
        if mesure:
            ecart = float(lufs) - float(mesure["input_i"])
            if abs(ecart) > 0.2 or float(mesure["input_tp"]) > LOUDNESS_TRUE_PEAK:
                plafond = 10 ** ((LOUDNESS_TRUE_PEAK - 0.5) / 20)
                corrige = os.path.join(tmp, "corrige.wav")
                # Le limiteur retire un peu de niveau : on réajuste le gain,
                # toujours depuis le même fichier, jusqu'à 0,1 LU de la cible.
                gain = ecart
                final = {}
                for _ in range(4):
                    run([
                        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-nostdin",
                        "-i", sortie, "-af",
                        f"volume={gain:.3f}dB,alimiter=limit={plafond:.5f}:attack=1:release=50"
                        f":level=false:latency=true",
                        "-c:a", "pcm_f32le", "-ar", str(AUDIO_SR), "-ac", "1",
                        "-frames:a", str(n_samples), corrige,
                    ], "correction de niveau")
                    final = _measure_loudness(corrige, lufs) or {}
                    if not final:
                        break
                    reste = float(lufs) - float(final["input_i"])
                    if abs(reste) <= 0.1:
                        break
                    gain += reste
                shutil.move(corrige, sortie)
                ecart = gain
                rapport["correction_niveau"] = {
                    "gain_db": round(ecart, 3),
                    "avant_i": mesure["input_i"], "avant_tp": mesure["input_tp"],
                    "apres_i": final.get("input_i"), "apres_tp": final.get("input_tp"),
                }
                log(f"  Correction de niveau : {ecart:+.2f} dB, "
                    f"I={final.get('input_i')} LUFS TP={final.get('input_tp')} dBTP")

    out_info = sf.info(sortie)
    if int(out_info.frames) != n_samples:
        # -frames:a coupe en paquets : on retaille à l'échantillon près.
        import numpy as np
        data, _ = sf.read(sortie, dtype="float32")
        fixed = np.zeros(n_samples, dtype=np.float32)
        fixed[: min(n_samples, len(data))] = data[:n_samples]
        sf.write(sortie, fixed, AUDIO_SR, subtype="FLOAT")
    rapport["temps_s"]["total"] = round(time.time() - t_total, 2)
    rapport["temps_par_minute_s"] = round(rapport["temps_s"]["total"] / max(duree / 60, 1e-9), 2)
    return rapport
