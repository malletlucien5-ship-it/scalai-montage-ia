"""
Auto-tune v4 — 7 bandes EQ, DeepFilterNet3 en pré-traitement.
Loss : band_err pondéré sur 13 bandes, avec extra-poids sur les 3 bandes
restantes en déficit (1-2 kHz, 3-4 kHz, 10-12 kHz).
"""
import json
import subprocess
import sys
from pathlib import Path

import librosa
import numpy as np
import optuna

# Shim torchaudio.backend.common.AudioMetaData (supprimé en torchaudio 2.11)
# pour que df.enhance s'importe — on n'utilise pas son load_audio/save_audio.
import types
_tb = types.ModuleType("torchaudio.backend")
_tbc = types.ModuleType("torchaudio.backend.common")
class _Stub:
    pass
_tbc.AudioMetaData = _Stub
sys.modules.setdefault("torchaudio.backend", _tb)
sys.modules.setdefault("torchaudio.backend.common", _tbc)
import torchaudio
torchaudio.backend = _tb

from df.enhance import enhance, init_df  # noqa: E402

ROOT = Path(__file__).parent
INPUT_MP3 = Path("/Users/lucienmallet/Downloads/Audio/input.mp3")
INPUT_DF_WAV = ROOT / "input_dfnet.wav"
REF_MP3 = Path("/Users/lucienmallet/Downloads/Audio/auphonic.mp3")
SR = 48000
N_FFT = 4096

# Loudness Auphonic (verrouillé — pas tuné)
TARGET_LUFS = -15.76
TARGET_LRA = 6.30
TARGET_TP = -1.19

# Bandes + poids — extra-poids sur les 3 bandes encore en déficit après v2
BANDS = [
    (60,    150,  0.4),
    (150,   300,  0.7),
    (300,   500,  1.0),
    (500,  1000,  1.5),
    (1000, 2000,  4.0),   # +poids — était -3.5 dB en v2
    (2000, 3000,  3.0),
    (3000, 4000,  4.0),   # +poids — était -2.0 dB en v2
    (4000, 6000,  3.0),
    (6000, 8000,  2.5),
    (8000, 10000, 2.5),
    (10000,12000, 3.0),   # +poids — était -2.1 dB en v2
    (12000,15000, 1.0),
    (15000,20000, 0.3),
]

freqs_axis = librosa.fft_frequencies(sr=SR, n_fft=N_FFT)


def _avg_log_mag(wav):
    S = np.abs(librosa.stft(wav, n_fft=N_FFT, hop_length=1024))
    return 20 * np.log10(np.mean(S, axis=1) + 1e-8)


def _rms_normalize(wav, target=0.1):
    rms = float(np.sqrt(np.mean(wav ** 2) + 1e-12))
    return wav * (target / rms) if rms > 1e-8 else wav


ref_wav, _ = librosa.load(str(REF_MP3), sr=SR, mono=True)
ref_wav = _rms_normalize(ref_wav)
ref_lm = _avg_log_mag(ref_wav)
ref_band_db = np.array([
    float(ref_lm[(freqs_axis >= lo) & (freqs_axis < hi)].mean())
    for lo, hi, _ in BANDS
])
band_w = np.array([b[2] for b in BANDS])


def measure_loudness(wav_path, target):
    r = subprocess.run([
        "ffmpeg", "-hide_banner", "-nostats", "-i", str(wav_path),
        "-af", f"loudnorm=I={target}:TP=-1:LRA=11:print_format=json",
        "-f", "null", "-",
    ], capture_output=True, text=True)
    s = r.stderr or ""
    a, b = s.rfind("{"), s.rfind("}")
    if a < 0 or b <= a: return None
    try: return json.loads(s[a:b + 1])
    except Exception: return None


def apply_chain(in_path, out_path, p):
    chain = [
        f"afftdn=nr={p['afftdn_nr']:.1f}:nf=-25",
        f"highpass=f={p['hpf']:.0f}:p=2",
        f"lowpass=f={p['lpf']:.0f}",
        # 7 bandes EQ
        f"equalizer=f=250:t=q:w=1.0:g={p['eq_250']:+.2f}",
        f"equalizer=f=500:t=q:w=1.4:g={p['eq_500']:+.2f}",
        f"equalizer=f=1500:t=q:w=1.0:g={p['eq_1500']:+.2f}",
        f"equalizer=f=3000:t=q:w=1.0:g={p['eq_3000']:+.2f}",
        f"equalizer=f=5500:t=q:w=1.2:g={p['eq_5500']:+.2f}",
        f"equalizer=f=8500:t=q:w=1.0:g={p['eq_8500']:+.2f}",
        f"equalizer=f=11000:t=q:w=1.2:g={p['eq_11k']:+.2f}",
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
    r1 = subprocess.run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(in_path), "-af", af,
        "-ar", str(SR), "-ac", "1", "-c:a", "pcm_s16le", str(tmp_eq),
    ], capture_output=True, text=True)
    if r1.returncode != 0:
        sys.stderr.write(f"\n[A FAIL] {af}\n{r1.stderr[-300:]}\n")
        return False

    # Loudnorm VERROUILLÉ sur la cible Auphonic
    m = measure_loudness(tmp_eq, target=TARGET_LUFS)
    if m and float(m.get("input_i", "-99")) > -70:
        ln = (
            f"loudnorm=I={TARGET_LUFS}:TP={TARGET_TP}:LRA={TARGET_LRA}"
            f":measured_I={m['input_i']}:measured_TP={m['input_tp']}"
            f":measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}"
            f":offset={m['target_offset']}:linear=true"
        )
    else:
        ln = f"loudnorm=I={TARGET_LUFS}:TP={TARGET_TP}:LRA={TARGET_LRA}"

    r2 = subprocess.run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(tmp_eq), "-af", ln,
        "-ar", str(SR), "-ac", "1", "-c:a", "pcm_s16le", str(out_path),
    ], capture_output=True, text=True)
    try: tmp_eq.unlink()
    except Exception: pass
    return r2.returncode == 0


def loss(params, trial_num):
    out_dir = ROOT / "_runs4"
    out_dir.mkdir(exist_ok=True)
    out_wav = out_dir / f"t{trial_num}.wav"
    if not apply_chain(INPUT_DF_WAV, out_wav, params):
        return 1e6, {}
    m = measure_loudness(out_wav, target=-16)
    if not m: return 1e6, {}

    out_data, _ = librosa.load(str(out_wav), sr=SR, mono=True)
    out_data = _rms_normalize(out_data)
    out_lm = _avg_log_mag(out_data)

    diffs = []
    for i, (lo, hi, _) in enumerate(BANDS):
        mask = (freqs_axis >= lo) & (freqs_axis < hi)
        out_db = float(out_lm[mask].mean()) if mask.any() else 0.0
        diffs.append(out_db - ref_band_db[i])
    diffs = np.array(diffs)
    band_err = float(np.sum(band_w * diffs ** 2) / np.sum(band_w))

    lufs_diff = abs(float(m["input_i"]) - TARGET_LUFS)
    L = 5.0 * band_err + 1.5 * lufs_diff

    if trial_num != "best":
        try: out_wav.unlink()
        except Exception: pass

    return L, {
        "lufs": float(m["input_i"]),
        "lra":  float(m["input_lra"]),
        "tp":   float(m["input_tp"]),
        "band_err": band_err,
        "d_1k2k":   float(diffs[4]),
        "d_3k4k":   float(diffs[6]),
        "d_10k12k": float(diffs[10]),
        "d_max":    float(np.max(np.abs(diffs))),
    }


def objective(trial):
    p = {
        "afftdn_nr":   trial.suggest_float("afftdn_nr",   0.5, 5.0),
        "hpf":         trial.suggest_float("hpf",         60,  140),
        "lpf":         trial.suggest_float("lpf",         12000, 17000),
        "eq_250":      trial.suggest_float("eq_250",      -2.0, 5.0),
        "eq_500":      trial.suggest_float("eq_500",      -5.0, 2.0),
        "eq_1500":     trial.suggest_float("eq_1500",     -2.0, 6.0),
        "eq_3000":     trial.suggest_float("eq_3000",     0.0, 9.0),
        "eq_5500":     trial.suggest_float("eq_5500",     0.0, 7.0),
        "eq_8500":     trial.suggest_float("eq_8500",     -1.0, 6.0),
        "eq_11k":      trial.suggest_float("eq_11k",      0.0, 8.0),
        "deesser_i":   trial.suggest_float("deesser_i",   0.03, 0.4),
        "bwe_amount":  trial.suggest_float("bwe_amount",  0.0, 3.0),
        "bwe_drive":   trial.suggest_float("bwe_drive",   1.0, 8.0),
        "comp_thresh": trial.suggest_float("comp_thresh", -22.0, -8.0),
        "comp_ratio":  trial.suggest_float("comp_ratio",  1.5, 4.0),
        "comp_attack": trial.suggest_float("comp_attack", 2, 30),
        "comp_release":trial.suggest_float("comp_release",80, 500),
        "comp_makeup": trial.suggest_float("comp_makeup", 1.0, 4.0),
    }
    L, m = loss(p, trial_num=trial.number)
    for k, v in m.items(): trial.set_user_attr(k, v)
    return L


def main():
    if not INPUT_DF_WAV.exists():
        print("[v4] running DeepFilterNet3 on input.mp3 (one-shot)...")
        import soundfile as sf, torch
        df_model, df_state, _ = init_df()
        sr_df = df_state.sr()
        audio, src_sr = sf.read(str(INPUT_MP3))
        if audio.ndim > 1:
            audio = audio.mean(axis=1)
        if src_sr != sr_df:
            audio = librosa.resample(audio.astype(np.float32), orig_sr=src_sr, target_sr=sr_df)
        audio_t = torch.from_numpy(audio.astype(np.float32)).unsqueeze(0)
        enhanced = enhance(df_model, df_state, audio_t)
        sf.write(str(INPUT_DF_WAV), enhanced.squeeze().cpu().numpy(), sr_df)
        print(f"[v4] saved → {INPUT_DF_WAV}")

    n_trials = int(sys.argv[1]) if len(sys.argv) > 1 else 250
    print(f"[v4] n_trials={n_trials}  target LUFS={TARGET_LUFS}  LRA={TARGET_LRA}")
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    study = optuna.create_study(
        direction="minimize",
        sampler=optuna.samplers.TPESampler(seed=42, n_startup_trials=30)
    )
    best = float("inf")
    for i in range(n_trials):
        t = study.ask()
        try: L = objective(t)
        except Exception as e:
            print(f"  t{i}: FAIL {e}")
            study.tell(t, state=optuna.trial.TrialState.FAIL); continue
        study.tell(t, L)
        if L < best:
            best = L; ua = t.user_attrs
            print(f"  t{i:3d}: L={L:6.2f} ★ be={ua['band_err']:5.2f}  "
                  f"LUFS={ua['lufs']:6.2f}  "
                  f"Δ1k2k={ua['d_1k2k']:+5.2f}  Δ3k4k={ua['d_3k4k']:+5.2f}  "
                  f"Δ10k12k={ua['d_10k12k']:+5.2f}  Δmax={ua['d_max']:.2f}")
    print(f"\n[v4] best loss={study.best_value:.3f}")
    print("[v4] best params:")
    for k, v in study.best_params.items(): print(f"  {k} = {v}")

    final = ROOT / "best_output_v4.wav"
    apply_chain(INPUT_DF_WAV, final, study.best_params)
    with open(ROOT / "best_params_v4.json", "w") as f:
        json.dump({
            "best_loss": study.best_value,
            "params": study.best_params,
            "best_trial_attrs": study.best_trial.user_attrs,
        }, f, indent=2)
    print("[v4] saved → best_params_v4.json + best_output_v4.wav")


if __name__ == "__main__":
    main()
