"""
Auto-tune v2 — loss focalisée sur l'erreur de bande (presence 1-10 kHz).
v1 minimisait mel_mse global → matched l'énergie totale mais ratait la distribution
fréquentielle. v2 utilise une distance log-magnitude bande-par-bande pondérée.
"""
import json
import subprocess
import sys
from pathlib import Path

import librosa
import numpy as np
import optuna

ROOT = Path(__file__).parent
AUDIO_DIR = Path("/Users/lucienmallet/Downloads/Audio")
INPUT_MP3 = AUDIO_DIR / "input.mp3"
REF_MP3 = AUDIO_DIR / "auphonic.mp3"
SR = 48000
N_FFT = 4096

REF_LUFS = -15.76
REF_LRA = 6.30
REF_TP = -1.19

# Bandes en Hz + poids perceptuel. Les bandes 1-10 kHz pèsent fort
# car c'est là que se joue la presence/intelligibilité (zone "voilée" du feedback user).
BANDS = [
    (60,    150,  0.5),
    (150,   300,  0.8),
    (300,   500,  1.0),
    (500,  1000,  1.2),
    (1000, 2000,  2.5),   # presence basse
    (2000, 3000,  3.0),   # presence — clé "voilée"
    (3000, 4000,  3.0),
    (4000, 6000,  3.0),   # clarté
    (6000, 8000,  2.5),
    (8000, 10000, 2.0),   # air bas
    (10000,12000, 1.5),
    (12000,15000, 0.8),
    (15000,20000, 0.3),
]

freqs_axis = librosa.fft_frequencies(sr=SR, n_fft=N_FFT)


def _avg_log_mag(wav):
    S = np.abs(librosa.stft(wav, n_fft=N_FFT, hop_length=1024))
    return 20 * np.log10(np.mean(S, axis=1) + 1e-8)


def _normalize_rms(wav, target_rms=0.1):
    rms = float(np.sqrt(np.mean(wav ** 2) + 1e-12))
    if rms < 1e-8:
        return wav
    return wav * (target_rms / rms)


# Pré-calcule le profil de référence (RMS-normalisé)
ref_wav, _ = librosa.load(str(REF_MP3), sr=SR, mono=True)
ref_wav = _normalize_rms(ref_wav)
ref_logmag = _avg_log_mag(ref_wav)
ref_band_db = []
for lo, hi, w in BANDS:
    m = (freqs_axis >= lo) & (freqs_axis < hi)
    ref_band_db.append(float(ref_logmag[m].mean()) if m.any() else 0.0)
ref_band_db = np.array(ref_band_db)
band_weights = np.array([b[2] for b in BANDS])


def run_ffmpeg(args):
    return subprocess.run(args, capture_output=True, text=True)


def measure_loudness(wav_path, target_lufs=-16):
    r = run_ffmpeg([
        "ffmpeg", "-hide_banner", "-nostats", "-i", str(wav_path),
        "-af", f"loudnorm=I={target_lufs}:TP=-1:LRA=11:print_format=json",
        "-f", "null", "-",
    ])
    s = r.stderr or ""
    a, b = s.rfind("{"), s.rfind("}")
    if a < 0 or b <= a:
        return None
    try:
        return json.loads(s[a:b + 1])
    except Exception:
        return None


def apply_chain(in_path, out_path, p):
    chain = [
        f"afftdn=nr={p['afftdn_nr']:.1f}:nf=-25",
        f"highpass=f={p['hpf']:.0f}:p=2",
        f"lowpass=f={p['lpf']:.0f}",
        # EQ 5 bandes
        f"equalizer=f=250:t=q:w=1.0:g={p['eq_warmth']:+.2f}",
        f"equalizer=f=500:t=q:w=1.5:g={p['eq_demud']:+.2f}",
        f"equalizer=f=3000:t=q:w=1.0:g={p['eq_presence']:+.2f}",
        f"equalizer=f=5500:t=q:w=1.2:g={p['eq_clarity']:+.2f}",
        f"equalizer=f=8500:t=q:w=1.0:g={p['eq_air']:+.2f}",
    ]
    if p["bwe_amount"] > 0.05:
        chain.append(
            f"aexciter=amount={p['bwe_amount']:.2f}:drive={p['bwe_drive']:.2f}"
            f":blend=0:freq=6500:ceil=14000"
        )
    chain.append(f"deesser=i={p['deesser_i']:.2f}")
    chain.append(
        f"acompressor=threshold={p['comp_thresh']:.1f}dB:ratio={p['comp_ratio']:.2f}"
        f":attack={p['comp_attack']:.0f}:release={p['comp_release']:.0f}"
        f":makeup={p['comp_makeup']:.2f}"
    )

    tmp_eq = out_path.with_suffix(".eq.wav")
    af = ",".join(chain)
    r1 = run_ffmpeg([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(in_path), "-af", af,
        "-ar", str(SR), "-ac", "1", "-c:a", "pcm_s16le", str(tmp_eq),
    ])
    if r1.returncode != 0:
        sys.stderr.write(f"\n[A FAIL] {af}\n{r1.stderr[-300:]}\n")
        return False

    m = measure_loudness(tmp_eq, target_lufs=p["lufs"])
    if m and float(m.get("input_i", "-99")) > -70:
        ln = (
            f"loudnorm=I={p['lufs']:.2f}:TP=-1:LRA={p['lra']:.2f}"
            f":measured_I={m['input_i']}:measured_TP={m['input_tp']}"
            f":measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}"
            f":offset={m['target_offset']}:linear=true"
        )
    else:
        ln = f"loudnorm=I={p['lufs']:.2f}:TP=-1:LRA={p['lra']:.2f}"

    r2 = run_ffmpeg([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(tmp_eq), "-af", ln,
        "-ar", str(SR), "-ac", "1", "-c:a", "pcm_s16le", str(out_path),
    ])
    try:
        tmp_eq.unlink()
    except Exception:
        pass
    return r2.returncode == 0


def loss(params, trial_num):
    out_dir = ROOT / "_runs2"
    out_dir.mkdir(exist_ok=True)
    out_wav = out_dir / f"t{trial_num}.wav"
    if not apply_chain(INPUT_MP3, out_wav, params):
        return 1e6, {}

    m = measure_loudness(out_wav)
    if not m:
        return 1e6, {}

    out_data, _ = librosa.load(str(out_wav), sr=SR, mono=True)
    out_data = _normalize_rms(out_data)
    out_logmag = _avg_log_mag(out_data)

    band_diffs = []
    for i, (lo, hi, w) in enumerate(BANDS):
        mask = (freqs_axis >= lo) & (freqs_axis < hi)
        if not mask.any():
            band_diffs.append(0.0); continue
        out_db = float(out_logmag[mask].mean())
        band_diffs.append(out_db - ref_band_db[i])
    band_diffs = np.array(band_diffs)

    # Erreur pondérée bande-par-bande (dB, pénalité quadratique)
    band_err = float(np.sum(band_weights * band_diffs ** 2) / np.sum(band_weights))

    lufs_diff = abs(float(m["input_i"]) - REF_LUFS)
    lra_diff = abs(float(m["input_lra"]) - REF_LRA)
    tp_diff = abs(float(m["input_tp"]) - REF_TP)

    L = (
        3.0 * band_err              # dB² pondéré, terme dominant — c'est ce qui rend la voix "voilée"
        + 2.0 * lufs_diff
        + 1.0 * lra_diff
        + 0.8 * tp_diff
    )

    if trial_num != "best":
        try: out_wav.unlink()
        except Exception: pass

    return L, {
        "lufs": float(m["input_i"]),
        "lra":  float(m["input_lra"]),
        "tp":   float(m["input_tp"]),
        "band_err": band_err,
        "presence_diff_db": float(band_diffs[5]),  # 2-3 kHz
        "clarity_diff_db":  float(band_diffs[7]),  # 4-6 kHz
        "air_diff_db":      float(band_diffs[9]),  # 8-10 kHz
    }


def objective(trial):
    params = {
        "afftdn_nr":   trial.suggest_float("afftdn_nr",   2.0, 15.0),
        "hpf":         trial.suggest_float("hpf",         60,  140),
        # KEY : on remonte la bande passante. v1 trouvait 10.9 kHz à tort.
        "lpf":         trial.suggest_float("lpf",         12000, 18000),
        "eq_warmth":   trial.suggest_float("eq_warmth",   -1.0, 4.0),
        "eq_demud":    trial.suggest_float("eq_demud",    -4.0, 1.0),
        # Élargi : Auphonic boost 2-4kHz d'~6dB
        "eq_presence": trial.suggest_float("eq_presence", 0.0, 7.0),
        # NOUVELLE BANDE clarity (5.5 kHz) — autorisée jusqu'à +6
        "eq_clarity":  trial.suggest_float("eq_clarity",  0.0, 6.0),
        # Air peut être positif maintenant
        "eq_air":      trial.suggest_float("eq_air",      -1.0, 5.0),
        "deesser_i":   trial.suggest_float("deesser_i",   0.05, 0.5),
        "bwe_amount":  trial.suggest_float("bwe_amount",  0.0, 4.0),
        "bwe_drive":   trial.suggest_float("bwe_drive",   1.0, 8.0),
        "comp_thresh": trial.suggest_float("comp_thresh", -24.0, -8.0),
        "comp_ratio":  trial.suggest_float("comp_ratio",  1.5, 4.0),
        "comp_attack": trial.suggest_float("comp_attack", 3, 40),
        "comp_release":trial.suggest_float("comp_release",80, 500),
        "comp_makeup": trial.suggest_float("comp_makeup", 1.0, 4.0),
        "lufs":        trial.suggest_float("lufs",        -17.5, -13.5),
        "lra":         trial.suggest_float("lra",         5.0, 11.0),
    }
    L, metrics = loss(params, trial_num=trial.number)
    for k, v in metrics.items():
        trial.set_user_attr(k, v)
    return L


def main():
    n_trials = int(sys.argv[1]) if len(sys.argv) > 1 else 150
    print(f"[tune-v2] n_trials = {n_trials}")
    print(f"[tune-v2] ref bands (dB): {dict(zip([f'{lo}-{hi}' for lo,hi,_ in BANDS], np.round(ref_band_db,1)))}")

    optuna.logging.set_verbosity(optuna.logging.WARNING)
    study = optuna.create_study(direction="minimize",
                                sampler=optuna.samplers.TPESampler(seed=42, n_startup_trials=20))

    best = float("inf")
    for i in range(n_trials):
        t = study.ask()
        try:
            L = objective(t)
        except Exception as e:
            print(f"  t{i}: FAIL {e}")
            study.tell(t, state=optuna.trial.TrialState.FAIL)
            continue
        study.tell(t, L)
        if L < best:
            best = L
            ua = t.user_attrs
            print(f"  t{i:3d}: L={L:6.2f} ★ band_err={ua.get('band_err',0):5.2f}  "
                  f"LUFS={ua.get('lufs',0):6.2f}  LRA={ua.get('lra',0):4.2f}  "
                  f"Δpresence={ua.get('presence_diff_db',0):+5.2f}  "
                  f"Δclarity={ua.get('clarity_diff_db',0):+5.2f}  "
                  f"Δair={ua.get('air_diff_db',0):+5.2f}")

    print(f"\n[tune-v2] best loss = {study.best_value:.3f}")
    print("[tune-v2] best params:")
    for k, v in study.best_params.items():
        print(f"  {k} = {v}")

    final_wav = ROOT / "best_output_v2.wav"
    apply_chain(INPUT_MP3, final_wav, study.best_params)
    with open(ROOT / "best_params_v2.json", "w") as f:
        json.dump({
            "best_loss": study.best_value,
            "params": study.best_params,
            "best_trial_attrs": study.best_trial.user_attrs,
        }, f, indent=2)
    print(f"[tune-v2] saved → best_params_v2.json + best_output_v2.wav")


if __name__ == "__main__":
    main()
