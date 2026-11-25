"""Tests du script Amélioration de la voix + Synchronisation.

Signaux synthétiques : voix de synthèse (syllabes voisées, fricatives, pauses)
sur un bruit rose. Les vidéos de test sont générées par ffmpeg à 50 i/s.
Le maître est un MOV façon OBS (micro en PCM 24 bits) ou un WAV séparé.

Les rushs portent leur numéro d'image incrusté par drawtext. Le test du proxy
le relit dans chaque image par comparaison à des gabarits de chiffres.

Lancer : .venv/bin/python -m pytest voix/test_ameliorer_voix.py -v
"""

from __future__ import annotations

import json
import random
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ameliorer_voix  # noqa: E402
import synchro  # noqa: E402

SR = 48000


def test_commande_proxy_lambda(tmp_path):
    sources = tmp_path / "sources.json"
    sortie = tmp_path / "proxy.mov"
    cmd = ameliorer_voix.commande_proxy_lambda(
        "projet-test", sources, "s3://bucket/voix.wav", sortie)
    assert cmd[:3] == [sys.executable, str(ameliorer_voix.PROXY_LAMBDA_SCRIPT), "--proxy"]
    assert cmd[cmd.index("--projet") + 1] == "projet-test"
    assert cmd[cmd.index("--sources") + 1] == str(sources)
    assert cmd[cmd.index("--wav") + 1] == "s3://bucket/voix.wav"
    assert cmd[cmd.index("--sortie") + 1] == str(sortie)
    assert "--sans-envoi" in cmd


def test_proxy_lambda_possible_exige_projet_et_variables(monkeypatch):
    args = type("Args", (), {"projet": "projet-test"})()
    for nom in ("REMOTION_AWS_ACCESS_KEY_ID", "REMOTION_AWS_SECRET_ACCESS_KEY",
                "REMOTION_AWS_REGION"):
        monkeypatch.delenv(nom, raising=False)
    assert not ameliorer_voix.proxy_lambda_possible(args)
    monkeypatch.setenv("REMOTION_AWS_ACCESS_KEY_ID", "x")
    monkeypatch.setenv("REMOTION_AWS_SECRET_ACCESS_KEY", "x")
    monkeypatch.setenv("REMOTION_AWS_REGION", "eu-north-1")
    assert ameliorer_voix.proxy_lambda_possible(args)
    args.projet = None
    assert not ameliorer_voix.proxy_lambda_possible(args)


# ─── Signaux synthétiques ────────────────────────────────────────────────────

def bruit_rose(n: int, rng: np.random.Generator) -> np.ndarray:
    spectre = np.fft.rfft(rng.standard_normal(n))
    f = np.arange(len(spectre), dtype=np.float64)
    f[0] = 1.0
    x = np.fft.irfft(spectre / np.sqrt(f), n)
    return (x / (np.std(x) + 1e-12)).astype(np.float32)


def voix_synthetique(duree: float, graine: int) -> np.ndarray:
    """Syllabes voisées à f0 variable, fricatives et pauses, jamais répétées."""
    rng = np.random.default_rng(graine)
    n = int(duree * SR)
    x = np.zeros(n, dtype=np.float64)
    pos = int(0.2 * SR)
    while pos < n:
        longueur = int(rng.uniform(0.08, 0.30) * SR)
        fin = min(n, pos + longueur)
        t = np.arange(fin - pos) / SR
        if rng.random() < 0.8:
            f0 = rng.uniform(95, 210) * (1 + 0.15 * np.sin(2 * np.pi * rng.uniform(2, 6) * t))
            phase = 2 * np.pi * np.cumsum(f0) / SR
            formant = rng.uniform(500, 2500)
            phases = rng.uniform(0, 2 * np.pi, 25)
            syl = sum((1 / k) * np.exp(-((k * f0.mean() - formant) / 900) ** 2)
                      * np.sin(k * phase + phases[k]) for k in range(1, 25))
        else:
            syl = rng.standard_normal(len(t)) * 0.3
            syl = np.diff(np.concatenate([[0.0], syl]))  # bruit plus aigu
        env = np.sin(np.pi * np.linspace(0, 1, len(t))) ** 0.7
        x[pos:fin] += syl * env * rng.uniform(0.4, 1.0)
        pos = fin + int(rng.choice([rng.uniform(0.02, 0.12), rng.uniform(0.2, 0.6)]) * SR)
    x = x / (np.max(np.abs(x)) + 1e-12) * 0.5
    x += 0.003 * bruit_rose(n, rng)
    return x.astype(np.float32)


def degrader(x: np.ndarray, graine: int) -> np.ndarray:
    """Son témoin : bande passante réduite, écho de pièce, bruit rose plus fort."""
    from scipy.signal import butter, sosfilt
    rng = np.random.default_rng(graine)
    y = sosfilt(butter(4, [150, 6000], btype="band", fs=SR, output="sos"), x)
    y = y + 0.35 * np.concatenate([np.zeros(900), y[:-900]])
    y = 0.4 * y + 0.01 * bruit_rose(len(y), rng)
    return y.astype(np.float32)


def temoin(wav: np.ndarray, debut: float, derive: float, duree: float, graine: int) -> np.ndarray:
    """témoin[u] = wav(debut + (1 + derive) · u), puis dégradé."""
    return degrader(synchro.extraire_recale(wav, debut, derive, int(duree * SR)), graine)


def piste16(nom: str, x48: np.ndarray) -> synchro.Piste:
    import soxr
    return synchro.Piste(nom, soxr.resample(x48, SR, 16000, quality="HQ").astype(np.float32))


# ─── Synchronisation sur tableaux ────────────────────────────────────────────

def test_offset_connu_retrouve_a_moins_d_une_ms():
    wav = voix_synthetique(90.0, 1)
    offset = 23.4567
    cam = temoin(wav, offset, 0.0, 40.0, 2)
    r = synchro.mesurer_paire(piste16("cam", cam), piste16("wav", wav))
    assert r["accepte"], r.get("raison")
    assert abs(r["a"] - offset) < 0.001, r["a"]


@pytest.mark.parametrize("derive", [11e-6, -40e-6])
def test_derive_connue_retrouvee(derive):
    wav = voix_synthetique(300.0, 3)
    offset = 31.25
    cam = temoin(wav, offset, derive, 240.0, 4)
    r = synchro.mesurer_paire(piste16("cam", cam), piste16("wav", wav))
    assert r["accepte"], r.get("raison")
    assert abs(r["a"] - offset) < 0.001
    assert abs(r["d"] - derive) < 2e-6, f"dérive {r['d'] * 1e6:.2f} µs/s"
    assert r["derive_source"] == "mesuree"
    assert len(r["points"]) >= 3


def test_voix_differente_refusee():
    wav = voix_synthetique(90.0, 5)
    autre = voix_synthetique(40.0, 6)
    r = synchro.mesurer_paire(piste16("cam", degrader(autre, 7)), piste16("wav", wav))
    assert not r["accepte"]


def test_recalage_de_derive_exact():
    """extraire_recale suit master(t0 + (1 + d)·n/sr) au dixième de µs près.

    Somme de sinus : la valeur attendue se calcule en tout point.
    Couvre la fraction d'échantillon de t0, avec et sans dérive.
    """
    t = np.arange(30 * SR) / SR
    freqs = [97.3, 431.7, 1234.5, 3777.7, 9100.1]

    def f(tt):
        return sum(np.sin(2 * np.pi * x * tt + i) for i, x in enumerate(freqs))

    def df(tt):
        return sum(2 * np.pi * x * np.cos(2 * np.pi * x * tt + i) for i, x in enumerate(freqs))

    wav = f(t).astype(np.float32)
    for d, t0 in [(50e-6, 5.0), (50e-6, 5.0 + 0.37 / SR), (-40e-6, 3.123456),
                  (0.0, 2.5 + 0.5 / SR), (11e-6, 7.0)]:
        n = 20 * SR
        out = synchro.extraire_recale(wav, t0, d, n)
        k = np.arange(SR, n - SR, 997)
        tt = t0 + (1 + d) * k / SR
        err = out[k] - f(tt)
        retard = -np.sum(err * df(tt)) / np.sum(df(tt) ** 2)
        assert abs(retard) < 1e-7, (d, t0, retard)
        assert np.max(np.abs(err)) < 1e-3, (d, t0)


def test_cadence_hors_50_refusee():
    cams = [{"nom": "x.mp4", "fps": "30000/1001", "fps_moyen": "30000/1001"}]
    with pytest.raises(ameliorer_voix.ErreurEntree, match="50 i/s"):
        ameliorer_voix.verifier_cadence(cams)
    ameliorer_voix.verifier_cadence([{"nom": "y.mp4", "fps": "50/1", "fps_moyen": "50/1"}])


# ─── Médias synthétiques ─────────────────────────────────────────────────────

POLICE = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"


def _video_numerotee(largeur: int, hauteur: int, fond: int, texte: str) -> str:
    """Fond gris uni et numéro incrusté par drawtext, 50 i/s."""
    return (f"color=c=0x{fond:02x}{fond:02x}{fond:02x}:s={largeur}x{hauteur}:r=50,"
            f"drawtext=fontfile={POLICE}:text='{texte}':fontsize={hauteur // 4}"
            f":x={largeur // 10}:y={hauteur // 3}:fontcolor=white")


NUMERO = "%{eif\\:n\\:d\\:5}"


def ecrire_rush(chemin: Path, audio: np.ndarray, creation: str, largeur: int = 640,
                hauteur: int = 360, fond: int = 40) -> None:
    """Rush caméra : numéro d'image incrusté, son témoin AAC, comme un DJI."""
    wav = chemin.with_suffix(".temoin.wav")
    sf.write(wav, audio, SR, subtype="PCM_16")
    frames = int(round(len(audio) / SR * 50))
    subprocess.run([
        "ffmpeg", "-y", "-v", "error",
        "-f", "lavfi", "-i", _video_numerotee(largeur, hauteur, fond, NUMERO),
        "-i", str(wav), "-map", "0:v", "-map", "1:a",
        "-frames:v", str(frames), "-c:v", "libx264", "-preset", "veryfast", "-g", "50",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k",
        "-metadata", f"creation_time={creation}", str(chemin),
    ], check=True)
    wav.unlink()


def ecrire_obs(chemin: Path, audio: np.ndarray) -> None:
    """Enregistrement OBS : capture d'écran et micro stéréo en PCM 24 bits 48 kHz."""
    wav = chemin.with_suffix(".micro.wav")
    sf.write(wav, np.stack([audio, audio], axis=1), SR, subtype="PCM_24")
    subprocess.run([
        "ffmpeg", "-y", "-v", "error",
        "-f", "lavfi", "-i", "testsrc2=size=320x180:rate=30", "-i", str(wav),
        "-map", "0:v", "-map", "1:a", "-shortest",
        "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
        "-c:a", "pcm_s24le", str(chemin),
    ], check=True)
    wav.unlink()


# Rush : (source, maître attendu, début dans le maître, durée, création, taille, fond)
RUSHS = {
    "c_rush.mp4": ("a", "2026-09-20 10-00-00.mov", 50.0, 30.0, "2026-09-20T10:00:50Z",
                   (640, 360), 90),
    "a_rush.mp4": ("b", "micro_B.wav", 5.0, 25.0, "2026-09-20T10:05:05Z", (960, 540), 140),
    "b_rush.mp4": ("a", "2026-09-20 10-00-00.mov", 10.0, 25.0, "2026-09-20T10:00:10Z",
                   (640, 360), 40),
}
ORDRE = ["b_rush.mp4", "c_rush.mp4", "a_rush.mp4"]
DERIVE = 11e-6


@pytest.fixture(scope="module")
def projet_synthetique(tmp_path_factory):
    d = tmp_path_factory.mktemp("projet")
    voix = {"a": voix_synthetique(100.0, 11), "b": voix_synthetique(60.0, 12)}
    ecrire_obs(d / "2026-09-20 10-00-00.mov", voix["a"])
    sf.write(d / "micro_B.wav", np.stack([voix["b"], voix["b"]], axis=1), SR, subtype="PCM_24")
    for i, (nom, (src, _, debut, duree, creation, (w, h), fond)) in enumerate(RUSHS.items()):
        ecrire_rush(d / nom, temoin(voix[src], debut, DERIVE, duree, 20 + i), creation, w, h, fond)
    entrees = [d / "a_rush.mp4", d / "micro_B.wav", d / "c_rush.mp4",
               d / "2026-09-20 10-00-00.mov", d / "b_rush.mp4"]
    random.Random(3).shuffle(entrees)
    return d, entrees, voix


@pytest.fixture(scope="module")
def rendu(projet_synthetique, tmp_path_factory):
    d, entrees, voix = projet_synthetique
    sortie = tmp_path_factory.mktemp("sortie")
    rapport_chemin = sortie / "rapport.json"
    code = ameliorer_voix.main(["rendre", *map(str, entrees), "--no-denoise", "--local",
                                "--sortie", str(sortie), "--travail", str(sortie / "travail"),
                                "--rapport", str(rapport_chemin)])
    rapport = json.loads(rapport_chemin.read_text())
    return code, rapport, sortie, d, voix


def _sonde(chemin: Path) -> dict:
    return json.loads(subprocess.run(
        ["ffprobe", "-v", "error", "-print_format", "json", "-show_streams", "-show_format",
         str(chemin)], capture_output=True, text=True, check=True).stdout)


def test_rendu_appairage(rendu):
    code, rapport, _, _, _ = rendu
    assert code == 0, rapport["rendu"]["controles"]["echecs"]
    maitres = {m["nom"]: m["origine"] for m in rapport["analyse"]["maitres"]}
    assert maitres == {"2026-09-20 10-00-00.mov": "obs", "micro_B.wav": "audio"}
    cams = rapport["analyse"]["cameras"]
    assert [c["nom"] for c in cams] == ORDRE
    for c in cams:
        _, maitre, debut, *_ = RUSHS[c["nom"]]
        assert [s["maitre"] for s in c["segments"]] == [maitre]
        # offset en temps témoin : t_w = a + (1 + d)·u
        assert abs(c["segments"][0]["offset_s"] - debut) < 0.001, (c["nom"], c["segments"])
        assert c["couverture_pct"] > 99.9


def test_proxy_format(rendu):
    _, rapport, sortie, _, _ = rendu
    proxy = sortie / "proxy.mov"
    p = _sonde(proxy)
    v = next(s for s in p["streams"] if s["codec_type"] == "video")
    a = next(s for s in p["streams"] if s["codec_type"] == "audio")
    assert (v["codec_name"], v["width"], v["height"]) == ("h264", 1920, 1080)
    assert v["r_frame_rate"] == "50/1" and v["avg_frame_rate"] == "50/1"
    assert int(v["nb_frames"]) == 4000
    assert (a["codec_name"], int(a["sample_rate"]), int(a["channels"])) == ("pcm_s24le", 48000, 1)
    assert int(a["duration_ts"]) == 4000 * 960
    assert any(s.get("tags", {}).get("timecode") == "00:00:00:00" for s in p["streams"])
    # GOP fixe de 25 images, sans images B
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                        "packet=flags", "-of", "csv=p=0", str(proxy)],
                       capture_output=True, text=True, check=True)
    cles = [i for i, l in enumerate(r.stdout.split()) if "K" in l]
    assert cles == list(range(0, 4000, 25))
    ctrl = rapport["rendu"]["controles"]
    assert ctrl["ok"] and ctrl["audio_proxy_identique_voix"]
    assert abs(ctrl["niveau_integre_lufs"] + 15.76) <= 0.5
    assert ctrl["pic_vrai_dbtp"] <= -1.0


def _gris(chemin: Path, filtre: str = "", images: int | None = None) -> np.ndarray:
    """Images en niveaux de gris 480x270, décodées par ffmpeg."""
    cmd = ["ffmpeg", "-v", "error", *(["-f", "lavfi"] if filtre else []),
           "-i", filtre or str(chemin)]
    if images:
        cmd += ["-frames:v", str(images)]
    cmd += ["-vf", "scale=480:270:flags=area,format=gray", "-f", "rawvideo", "-"]
    brut = subprocess.run(cmd, capture_output=True, check=True).stdout
    return np.frombuffer(brut, dtype=np.uint8).reshape(-1, 270, 480).astype(np.float32)


def _gabarits(largeur: int, hauteur: int, fond: int):
    """Chiffres 0 à 9 rendus comme dans le rush, puis ramenés au format du proxy."""
    g = _gris(None, _video_numerotee(largeur, hauteur, fond, "%{eif\\:n*11111\\:d\\:5}")
              + f",scale=1920:1080", images=10)
    colonnes = np.where((g > fond + 60).any(axis=(0, 1)))[0]
    lignes = np.where((g > fond + 60).any(axis=(0, 2)))[0]
    x0, x1 = colonnes[0], colonnes[-1] + 1
    y0, y1 = lignes[0], lignes[-1] + 1
    bords = np.linspace(x0, x1, 6).round().astype(int)
    cellules = [(bords[i], bords[i + 1]) for i in range(5)]
    return g[:, y0:y1], (y0, y1), cellules


def _lire_numero(image: np.ndarray, gabarits) -> int:
    g, (y0, y1), cellules = gabarits
    zone = image[y0:y1]
    chiffres = []
    for a, b in cellules:
        ecarts = [np.sum((zone[:, a:b] - g[k][:, a:b]) ** 2) for k in range(10)]
        chiffres.append(int(np.argmin(ecarts)))
    return int("".join(map(str, chiffres)))


def test_proxy_image_pour_image(rendu):
    """Chaque image du proxy montre le numéro d'image que sources.json annonce."""
    _, _, sortie, d, _ = rendu
    doc = json.loads((sortie / "sources.json").read_text())
    images = _gris(sortie / "proxy.mov")
    assert len(images) == doc["proxy"]["images"] == 4000
    for plage in doc["plages"]:
        nom = Path(plage["camera"]).name
        _, _, _, _, _, (w, h), fond = RUSHS[nom]
        gab = _gabarits(w, h, fond)
        for f in range(plage["proxy_debut"], plage["proxy_debut"] + plage["images"]):
            img = images[f]
            # Le fond identifie le rush, le numéro identifie l'image.
            assert abs(float(np.median(img)) - fond) < 6, (f, nom, np.median(img))
            attendu = plage["camera_debut"] + (f - plage["proxy_debut"])
            assert _lire_numero(img, gab) == attendu, (f, nom)


def test_sources_json(rendu):
    _, rapport, sortie, d, _ = rendu
    doc = json.loads((sortie / "sources.json").read_text())
    assert set(doc) == {"version", "fps", "proxy", "plages", "audio"}
    assert doc["version"] == 1 and doc["fps"] == 50
    assert doc["proxy"] == {"largeur": 1920, "hauteur": 1080, "images": 4000}
    assert doc["audio"]["sample_rate"] == 48000
    assert Path(doc["audio"]["wav"]) == (sortie / "voix.wav").resolve()
    assert sf.info(doc["audio"]["wav"]).frames == 4000 * 960
    debut = 0
    for plage, nom in zip(doc["plages"], ORDRE):
        assert set(plage) == {"proxy_debut", "images", "camera", "camera_debut",
                              "camera_largeur", "camera_hauteur"}
        _, _, _, duree, _, (w, h), _ = RUSHS[nom]
        assert plage["camera"] == str(d / nom)
        assert plage["proxy_debut"] == debut and plage["camera_debut"] == 0
        assert plage["images"] == int(duree * 50)
        assert (plage["camera_largeur"], plage["camera_hauteur"]) == (w, h)
        debut += plage["images"]
    assert debut == doc["proxy"]["images"]
    assert rapport["rendu"]["sources"] == doc


def test_voix_synchro_moins_d_une_ms(rendu):
    """Contrôle indépendant : voix.wav tombe au bon endroit des deux maîtres."""
    _, rapport, sortie, d, voix = rendu
    ctrl = rapport["rendu"]["controles"]
    assert ctrl["residu_synchro_max_ms"] is not None and ctrl["residu_synchro_max_ms"] < 1.0
    audio, _ = sf.read(sortie / "voix.wav", dtype="float32")
    debut_proxy = dict(zip(ORDRE, (0, 1250, 2750)))
    for nom in ("c_rush.mp4", "a_rush.mp4", "b_rush.mp4"):
        src, _, debut, _, _, _, _ = RUSHS[nom]
        for tau in (3.0, 12.0, 20.0):
            n0 = debut_proxy[nom] * 960 + int(tau * SR)
            ref = audio[n0: n0 + 3 * SR]
            t_attendu = debut + tau * (1 + DERIVE)
            maitre = voix[src]
            tgt = maitre[int((t_attendu - 0.1) * SR): int((t_attendu + 3.1) * SR)]
            m = synchro.xcorr_detail(ref, tgt, SR)
            assert abs(m["position"] - 0.1) < 0.001, (nom, tau, m)


def test_rush_sans_correspondance_refuse(projet_synthetique, tmp_path, capsys):
    d, _, _ = projet_synthetique
    intrus = tmp_path / "intrus.mp4"
    ecrire_rush(intrus, degrader(voix_synthetique(20.0, 99), 98), "2026-09-20T11:00:00Z")
    code = ameliorer_voix.main(["analyser", str(d / "2026-09-20 10-00-00.mov"),
                                str(d / "b_rush.mp4"), str(intrus),
                                "--travail", str(tmp_path / "travail")])
    err = capsys.readouterr().err
    assert code == 2
    assert "intrus.mp4 n'a aucune correspondance fiable" in err
    assert "confiance" in err


def test_rush_sans_correspondance_couvert_par_son_secours(projet_synthetique, tmp_path):
    """Incident I5 : faux départ hors OBS. Son propre son le couvre, synchro contrôlée."""
    d, _, _ = projet_synthetique
    dossier = tmp_path / "rushs"
    dossier.mkdir()
    intrus = dossier / "intrus.mp4"
    ecrire_rush(intrus, degrader(voix_synthetique(20.0, 99), 98), "2026-09-20T11:00:00Z")
    secours = tmp_path / "intrus.wav"   # comme extraire_audio_camera.py (repli ffmpeg)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(intrus), "-map", "0:a:0", "-vn",
                    "-ar", str(SR), "-c:a", "pcm_s24le", str(secours)], check=True)
    sortie = tmp_path / "sortie"
    rapport_chemin = sortie / "rapport.json"
    code = ameliorer_voix.main(["rendre", str(d / "2026-09-20 10-00-00.mov"),
                                str(d / "b_rush.mp4"), str(intrus), "--secours", str(secours),
                                "--no-denoise", "--local", "--sans-proxy", "--sortie", str(sortie),
                                "--travail", str(tmp_path / "travail"),
                                "--rapport", str(rapport_chemin)])
    rapport = json.loads(rapport_chemin.read_text())
    assert code == 0, rapport["rendu"]["controles"]["echecs"]
    cams = {c["nom"]: c for c in rapport["analyse"]["cameras"]}
    assert [c["nom"] for c in rapport["analyse"]["cameras"]] == ["b_rush.mp4", "intrus.mp4"]
    assert cams["b_rush.mp4"]["couverture_obs_pct"] > 99.9
    assert cams["b_rush.mp4"]["couverture_secours_pct"] == 0.0
    assert cams["intrus.mp4"]["couverture_obs_pct"] == 0.0
    assert cams["intrus.mp4"]["couverture_secours_pct"] > 99.9
    assert [s["maitre"] for s in cams["intrus.mp4"]["segments"]] == ["intrus.wav"]
    assert any("aucun maître principal" in a for a in rapport["analyse"]["avertissements"])
    residus = [r for r in rapport["rendu"]["controles"]["residus_synchro"]
               if r["camera"] == "intrus.mp4" and r["conclusif"]]
    assert residus and max(abs(r["residu_ms"]) for r in residus) < 1.0, residus


# ─── Chaîne complète avec DeepFilterNet ──────────────────────────────────────

def test_chaine_complete_deepfilternet(tmp_path):
    pytest.importorskip("df")
    import chaine_audio
    x = voix_synthetique(12.0, 30)
    src = tmp_path / "voix.wav"
    sf.write(src, x, SR, subtype="FLOAT")
    sortie = tmp_path / "voix_amelioree.wav"
    r = chaine_audio.ameliorer_wav(str(src), str(sortie), denoise=True)
    assert r["denoise"] and "deepfilternet" in r["temps_s"] and "gate_vad" in r
    assert "afftdn=nr=4.2:nf=-25" in r["filtres"]
    assert sf.info(str(sortie)).frames == len(x)
