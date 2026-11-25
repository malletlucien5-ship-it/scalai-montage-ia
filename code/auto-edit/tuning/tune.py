"""
Auto-tune ffmpeg polish chain to match Auphonic reference.

Usage:  python3 tune.py [n_trials]

Input:  /Users/lucienmallet/Downloads/Audio/input.mp3
Target: /Users/lucienmallet/Downloads/Audio/auphonic.mp3
Output: tuning/best_params.json  +  tuning/best_output.wav
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

# --- pre-load reference once ---
ref_wav, _ = librosa.load(str(REF_MP3), sr=SR, mono=True)
# normalize peak to compare timbre fairly with our output (which we'll also normalize for distance comp)
ref_rms = np.sqrt(np.mean(ref_wav ** 2) + 1e-12)

# Reference loudness metrics (already measured externally: I=-15.76, LRA=6.3, TP=-1.19)
REF_LUFS = -15.76
REF_LRA = 6.30
REF_TP = -1.19


def run_ffmpeg(args, capture=True):
    r = subprocess.run(args, capture_output=capture, text=True)
    return r


def measure_loudness(wav_path, target_lufs=-16):
    r = subprocess.run(
        [
            "ffmpeg",
            "-hide_banner", "-nostats",
            "-i", str(wav_path),
            "-af", f"loudnorm=I={target_lufs}:TP=-1:LRA=11:print_format=json",
            "-f", "null", "-",
        ],
        capture_output=True, text=True,
    )
    s = r.stderr or ""
    a, b = s.rfind("{"), s.rfind("}")
    if a < 0 or b <= a:
        return None
    try:
        return json.loads(s[a:b + 1])
    except Exception:
        return None


def apply_chain(in_path, out_path, params):
    chain = []

    # 1. Denoise (afftdn)
    chain.append(f"afftdn=nr={params['afftdn_nr']:.1f}:nf=-25")

    # 2. Highpass
    chain.append(f"highpass=f={params['hpf']:.0f}:p=2")

    # 3. Lowpass
    chain.append(f"lowpass=f={params['lpf']:.0f}")

    # 4. EQ — 4 bands (freq fixe, gain tuné)
    chain.append(f"equalizer=f=250:t=q:w=1.0:g={params['eq_warmth']:+.2f}")
    chain.append(f"equalizer=f=400:t=q:w=1.5:g={params['eq_demud']:+.2f}")
    chain.append(f"equalizer=f=3000:t=q:w=1.0:g={params['eq_presence']:+.2f}")
    chain.append(f"equalizer=f=8000:t=q:w=1.0:g={params['eq_air']:+.2f}")

    # 5. Exciter (optional via amount=0)
    if params["bwe_amount"] > 0.05:
        chain.append(
            f"aexciter=amount={params['bwe_amount']:.2f}"
            f":drive={params['bwe_drive']:.2f}"
            f":blend=0:freq=7500:ceil=12000"
        )

    # 6. De-esser
    chain.append(f"deesser=i={params['deesser_i']:.2f}")

    # 7. Compressor
    chain.append(
        f"acompressor=threshold={params['comp_thresh']:.1f}dB"
        f":ratio={params['comp_ratio']:.2f}"
        f":attack={params['comp_attack']:.0f}"
        f":release={params['comp_release']:.0f}"
        f":makeup={params['comp_makeup']:.2f}"
    )

    af_chain = ",".join(chain)
    tmp_eq = out_path.with_suffix(".eq.wav")

    r1 = run_ffmpeg([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(in_path), "-af", af_chain,
        "-ar", str(SR), "-ac", "1", "-c:a", "pcm_s16le",
        str(tmp_eq),
    ])
    if r1.returncode != 0:
        sys.stderr.write(f"\n[ffmpeg stage A FAIL]\nchain: {af_chain}\n{r1.stderr[-500:]}\n")
        return False

    # 8. Loudnorm 2-pass
    target_lufs = params["lufs"]
    target_lra = params["lra"]
    m = measure_loudness(tmp_eq, target_lufs=target_lufs)
    if m and float(m.get("input_i", "-99")) > -70:
        ln = (
            f"loudnorm=I={target_lufs:.2f}:TP=-1:LRA={target_lra:.2f}"
            f":measured_I={m['input_i']}:measured_TP={m['input_tp']}"
            f":measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}"
            f":offset={m['target_offset']}:linear=true:print_format=summary"
        )
    else:
        ln = f"loudnorm=I={target_lufs:.2f}:TP=-1:LRA={target_lra:.2f}"

    r2 = run_ffmpeg([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(tmp_eq), "-af", ln,
        "-ar", str(SR), "-ac", "1", "-c:a", "pcm_s16le",
        str(out_path),
    ])
    if r2.returncode != 0:
        sys.stderr.write(f"\n[ffmpeg stage B FAIL]\nln: {ln}\n{r2.stderr[-500:]}\n")
    try:
        tmp_eq.unlink()
    except Exception:
        pass
    return r2.returncode == 0


def spectral_distance(wav_a, wav_b):
    """Multi-band log-mel + MFCC distance. Both arrays mono @ SR."""
    n = min(len(wav_a), len(wav_b))
    a = wav_a[:n].astype(np.float32)
    b = wav_b[:n].astype(np.float32)

    # Match RMS so we compare timbre, not absolute level (loudness handled separately)
    rms_a = np.sqrt(np.mean(a ** 2) + 1e-12)
    rms_b = np.sqrt(np.mean(b ** 2) + 1e-12)
    if rms_a > 1e-6:
        a = a * (rms_b / rms_a)

    # Log-mel
    mel_a = librosa.feature.melspectrogram(y=a, sr=SR, n_fft=2048, hop_length=512, n_mels=128)
    mel_b = librosa.feature.melspectrogram(y=b, sr=SR, n_fft=2048, hop_length=512, n_mels=128)
    log_a = librosa.power_to_db(mel_a + 1e-10)
    log_b = librosa.power_to_db(mel_b + 1e-10)
    mel_mse = float(np.mean((log_a - log_b) ** 2))

    # MFCC
    mfcc_a = librosa.feature.mfcc(S=log_a, n_mfcc=20)
    mfcc_b = librosa.feature.mfcc(S=log_b, n_mfcc=20)
    mfcc_l2 = float(np.mean((mfcc_a - mfcc_b) ** 2))

    # Spectral centroid (brightness)
    cent_a = float(np.mean(librosa.feature.spectral_centroid(y=a, sr=SR)))
    cent_b = float(np.mean(librosa.feature.spectral_centroid(y=b, sr=SR)))
    cent_diff = abs(cent_a - cent_b) / 1000.0  # kHz

    return mel_mse, mfcc_l2, cent_diff


def loss(params, trial_num=None):
    out_dir = ROOT / "_runs"
    out_dir.mkdir(exist_ok=True)
    out_wav = out_dir / f"trial_{trial_num or 'x'}.wav"

    if not apply_chain(INPUT_MP3, out_wav, params):
        return 1e6, {}

    # Loudness check
    m = measure_loudness(out_wav)
    if not m:
        return 1e6, {}
    lufs_diff = abs(float(m["input_i"]) - REF_LUFS)
    lra_diff = abs(float(m["input_lra"]) - REF_LRA)
    tp_diff = abs(float(m["input_tp"]) - REF_TP)

    # Spectral distance
    out_wav_data, _ = librosa.load(str(out_wav), sr=SR, mono=True)
    mel_mse, mfcc_l2, cent_diff = spectral_distance(out_wav_data, ref_wav)

    # Combined loss — weights tuned to make all terms ~comparable magnitude
    # Weights chosen so each term contributes O(1-10) at typical magnitudes
    L = (
        3.0 * lufs_diff       # LUFS — most audible
        + 2.0 * lra_diff      # dynamics
        + 1.5 * tp_diff       # peak headroom
        + 0.04 * mel_mse      # timbre (typical ~100-300)
        + 0.005 * mfcc_l2     # timbre fine (typical ~500-1500)
        + 1.5 * cent_diff     # brightness (kHz)
    )

    # cleanup non-best
    if trial_num is not None and trial_num != "best":
        try:
            out_wav.unlink()
        except Exception:
            pass

    return L, {
        "lufs": float(m["input_i"]),
        "lra": float(m["input_lra"]),
        "tp": float(m["input_tp"]),
        "mel_mse": mel_mse,
        "mfcc_l2": mfcc_l2,
        "cent_diff_khz": cent_diff,
    }


def objective(trial):
    params = {
        "afftdn_nr": trial.suggest_float("afftdn_nr", 4, 20),
        "hpf": trial.suggest_float("hpf", 50, 130),
        "lpf": trial.suggest_float("lpf", 10000, 18000),
        "eq_warmth": trial.suggest_float("eq_warmth", -2.0, 3.5),
        "eq_demud": trial.suggest_float("eq_demud", -4.0, 0.5),
        "eq_presence": trial.suggest_float("eq_presence", -1.0, 5.0),
        "eq_air": trial.suggest_float("eq_air", -1.0, 5.0),
        "deesser_i": trial.suggest_float("deesser_i", 0.05, 0.7),
        "bwe_amount": trial.suggest_float("bwe_amount", 0.0, 3.0),
        "bwe_drive": trial.suggest_float("bwe_drive", 1.0, 8.0),
        "comp_thresh": trial.suggest_float("comp_thresh", -28.0, -10.0),
        "comp_ratio": trial.suggest_float("comp_ratio", 1.3, 4.0),
        "comp_attack": trial.suggest_float("comp_attack", 3, 40),
        "comp_release": trial.suggest_float("comp_release", 80, 500),
        "comp_makeup": trial.suggest_float("comp_makeup", 1.0, 4.0),
        "lufs": trial.suggest_float("lufs", -18.0, -13.5),
        "lra": trial.suggest_float("lra", 4.0, 11.0),
    }
    L, metrics = loss(params, trial_num=trial.number)
    for k, v in metrics.items():
        trial.set_user_attr(k, v)
    return L


def main():
    n_trials = int(sys.argv[1]) if len(sys.argv) > 1 else 80
    print(f"[tune] n_trials = {n_trials}")
    print(f"[tune] reference: I={REF_LUFS}  LRA={REF_LRA}  TP={REF_TP}")

    optuna.logging.set_verbosity(optuna.logging.WARNING)
    study = optuna.create_study(direction="minimize",
                                sampler=optuna.samplers.TPESampler(seed=42))

    best_so_far = float("inf")
    for i in range(n_trials):
        t = study.ask()
        try:
            L = objective(t)
        except Exception as e:
            print(f"  trial {i}: FAIL {e}")
            study.tell(t, state=optuna.trial.TrialState.FAIL)
            continue
        study.tell(t, L)
        if L < best_so_far:
            best_so_far = L
            print(f"  trial {i:3d}: loss={L:.3f} ★ "
                  f"LUFS={t.user_attrs.get('lufs', 0):.2f} "
                  f"LRA={t.user_attrs.get('lra', 0):.2f} "
                  f"mel={t.user_attrs.get('mel_mse', 0):.2f} "
                  f"mfcc={t.user_attrs.get('mfcc_l2', 0):.2f}")
        elif i % 10 == 0:
            print(f"  trial {i:3d}: loss={L:.3f}")

    print(f"\n[tune] best loss = {study.best_value:.3f}")
    print("[tune] best params:")
    for k, v in study.best_params.items():
        print(f"  {k} = {v}")

    # Render final best output
    print("\n[tune] rendering best output…")
    final_wav = ROOT / "best_output.wav"
    apply_chain(INPUT_MP3, final_wav, study.best_params)

    with open(ROOT / "best_params.json", "w") as f:
        json.dump({
            "best_loss": study.best_value,
            "ref_lufs": REF_LUFS, "ref_lra": REF_LRA, "ref_tp": REF_TP,
            "params": study.best_params,
            "best_trial_attrs": study.best_trial.user_attrs,
        }, f, indent=2)
    print(f"[tune] saved → {ROOT / 'best_params.json'}")
    print(f"[tune] best wav → {final_wav}")


if __name__ == "__main__":
    main()
