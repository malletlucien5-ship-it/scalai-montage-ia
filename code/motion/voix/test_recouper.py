"""Tests de la recoupe 4K (voix/recouper.py) sur médias synthétiques.

Deux faux rushs 640x360 50 i/s. Chaque image porte son numéro et celui du rush
dans une bande de 16 carrés noirs ou blancs (un bit par carré), plus le numéro
en clair par drawtext pour l'œil. Le proxy 320x180 enchaîne une partie des deux
rushs. L'EDL de 3 coupes est écrite à la main au format Resolve. Le deuxième
événement chevauche les deux rushs.

Chaque image de la sortie est décodée et comparée à l'image source attendue.

Lancer : .venv/bin/python -m pytest voix/test_recouper.py -v
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

sys.path.insert(0, str(Path(__file__).resolve().parent))
import recouper  # noqa: E402

FPS = 50
W, H = 640, 360
BLOC = 40            # 16 carrés de 40 px sur la largeur
POLICE = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"

# Rushs : (identifiant, nombre d'images, GOP, début des horodatages en s)
RUSH_A = (1, 300, 50, 0.0)
RUSH_B = (2, 250, 37, 3.2)     # horodatages décalés, comme un rush qui ne part pas de 0
# Proxy : A[20, 220) puis B[10, 160)
PLAGES = [(0, 200, "A", 20), (200, 150, "B", 10)]

EDL_RESOLVE = """TITLE: Timeline 1
FCM: NON-DROP FRAME

001  AX       V     C        00:00:01:05 00:00:02:10 01:00:00:00 01:00:01:05
* FROM CLIP NAME: proxy.mov

002  AX       A     C        00:00:01:05 00:00:02:10 01:00:00:00 01:00:01:05
* FROM CLIP NAME: proxy.mov

003  AX       V     C        00:00:03:30 00:00:04:30 01:00:01:05 01:00:02:05
* FROM CLIP NAME: proxy.mov

004  AX       A     C        00:00:03:30 00:00:04:30 01:00:01:05 01:00:02:05
* FROM CLIP NAME: proxy.mov

005  AX       V     C        00:00:06:00 00:00:06:40 01:00:02:05 01:00:02:45
* FROM CLIP NAME: proxy.mov

006  AX       A     C        00:00:06:00 00:00:06:40 01:00:02:05 01:00:02:45
* FROM CLIP NAME: proxy.mov
"""

# Images attendues : (rush, image) pour chaque image de sortie.
ATTENDU = ([(1, i) for i in range(75, 130)]          # proxy 55..109
           + [(1, i) for i in range(200, 220)]       # proxy 180..199
           + [(2, i) for i in range(10, 40)]         # proxy 200..229
           + [(2, i) for i in range(110, 150)])      # proxy 300..339
TOTAL = len(ATTENDU)   # 145


def ffmpeg(*args: str) -> None:
    subprocess.run(["ffmpeg", "-v", "error", "-nostdin", "-y", *args], check=True)


def generer_rush(chemin: Path, ident: int, images: int, gop: int, debut: float) -> None:
    lum = (f"if(lt(Y\\,{BLOC})\\,if(bitand(N+4096*{ident}\\,pow(2\\,floor(X/{BLOC})))\\,235\\,16)"
           f"\\,40+mod(X+2*Y+9*N\\,160))")
    texte = f",drawtext=fontfile={POLICE}:text='R{ident} %{{frame_num}}':x=40:y=150:" \
            "fontsize=96:fontcolor=white" if Path(POLICE).exists() else ""
    ffmpeg("-f", "lavfi", "-i", f"nullsrc=s={W}x{H}:r={FPS}",
           "-vf", f"geq=lum='{lum}':cb=128:cr=128{texte}", "-frames:v", str(images),
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-g", str(gop),
           "-pix_fmt", "yuv420p", "-output_ts_offset", str(debut), str(chemin))


def lire_images(chemin: Path, w: int = W, h: int = H) -> np.ndarray:
    r = subprocess.run(["ffmpeg", "-v", "error", "-nostdin", "-i", str(chemin), "-map", "0:v:0",
                        "-fps_mode", "passthrough", "-f", "rawvideo", "-pix_fmt", "gray", "pipe:1"],
                       capture_output=True, check=True)
    return np.frombuffer(r.stdout, np.uint8).reshape(-1, h, w)


def codes(images: np.ndarray) -> list[tuple[int, int]]:
    """Lit (rush, image) dans la bande de carrés de chaque image."""
    n, h, w = images.shape
    b = w // 16
    res = []
    for img in images:
        bits = [img[b // 4: 3 * b // 4, k * b + b // 4: k * b + 3 * b // 4].mean() > 128
                for k in range(16)]
        v = sum(1 << k for k, bit in enumerate(bits) if bit)
        res.append((v >> 12, v & 4095))
    return res


@pytest.fixture(scope="module")
def medias(tmp_path_factory) -> dict:
    d = tmp_path_factory.mktemp("recoupe")
    rushs = {"A": d / "DJI_0001.MP4", "B": d / "DJI_0002.MP4"}
    generer_rush(rushs["A"], *RUSH_A)
    generer_rush(rushs["B"], *RUSH_B)
    # Proxy 1080p réduit : 320x180, A[20, 220) puis B[10, 160).
    proxy = d / "proxy.mov"
    ffmpeg("-i", str(rushs["A"]), "-i", str(rushs["B"]), "-filter_complex",
           "[0:v]trim=start_frame=20:end_frame=220,setpts=PTS-STARTPTS[a];"
           "[1:v]trim=start_frame=10:end_frame=160,setpts=PTS-STARTPTS[b];"
           "[a][b]concat=n=2:v=1:a=0,scale=320:180[v]",
           "-map", "[v]", "-c:v", "libx264", "-crf", "12", "-g", "25", "-pix_fmt", "yuv420p",
           str(proxy))
    sources = {
        "version": 1, "fps": FPS, "proxy": {"largeur": 320, "hauteur": 180, "images": 350},
        "plages": [{"proxy_debut": p0, "images": n, "camera": str(rushs[c]), "camera_debut": c0,
                    "camera_largeur": W, "camera_hauteur": H} for p0, n, c, c0 in PLAGES],
        "audio": {"wav": "s3://bucket/outputs/test/synchro/voix.wav", "sample_rate": 48000},
    }
    (d / "sources.json").write_text(json.dumps(sources))
    edl = d / "Timeline 1.edl"
    edl.write_text(EDL_RESOLVE.replace("\n", "\r\n"))   # Resolve sous Windows : CRLF
    rng = np.random.default_rng(3)
    wav = d / "timeline.wav"
    sf.write(wav, (0.1 * rng.standard_normal((TOTAL * 48000 // FPS, 2))).astype(np.float32),
             48000, subtype="PCM_24")
    return {"dossier": d, "rushs": rushs, "proxy": proxy, "sources": d / "sources.json",
            "edl": edl, "wav": wav}


# ─── Analyse ─────────────────────────────────────────────────────────────────

def test_timecodes():
    assert recouper.tc_vers_images("01:00:00:00", 50) == 180000
    assert recouper.tc_vers_images("00:00:01:49", 50) == 99
    assert recouper.images_vers_tc(180055, 50) == "01:00:01:05"
    with pytest.raises(recouper.ErreurEntree):
        recouper.tc_vers_images("00:00:01:50", 50)
    with pytest.raises(recouper.ErreurEntree):
        recouper.tc_vers_images("00:00:01;10", 50)


def test_lire_edl_resolve():
    m = recouper.lire_edl(EDL_RESOLVE.replace("\n", "\r\n"), FPS)
    assert m.titre == "Timeline 1"
    assert len(m.evenements) == 6
    v = [e for e in m.evenements if e.video]
    assert [(e.src_in, e.src_out, e.rec_in) for e in v] == [
        (55, 110, 180000), (180, 230, 180055), (300, 340, 180105)]
    assert all(e.clip == "proxy.mov" for e in m.evenements)
    assert sum(e.audio for e in m.evenements) == 3


def test_fondu_refuse():
    edl = EDL_RESOLVE.replace(
        "003  AX       V     C        00:00:03:30",
        "003  AX       V     D    025 00:00:03:30")
    with pytest.raises(recouper.ErreurEntree, match="transition"):
        recouper.lire_edl(edl, FPS)


def test_vitesse_refusee():
    edl = EDL_RESOLVE + "M2   AX       100.0                00:00:06:00\n"
    with pytest.raises(recouper.ErreurEntree, match="M2"):
        recouper.lire_edl(edl, FPS)


def _plan(texte_edl: str, sources_obj: dict, debut=None):
    m = recouper.lire_edl(texte_edl, FPS)
    s = recouper.lire_sources(sources_obj)
    d = debut if debut is not None else min(e.rec_in for e in m.evenements)
    return recouper.planifier(m, s, FPS, d, 0, recouper.choisir_proxy(m.evenements, None), False)


def _sources_factices() -> dict:
    return {"version": 1, "fps": FPS, "proxy": {"largeur": 1920, "hauteur": 1080, "images": 350},
            "plages": [{"proxy_debut": p0, "images": n, "camera": f"s3://b/{c}.MP4",
                        "camera_debut": c0, "camera_largeur": 3840, "camera_hauteur": 2160}
                       for p0, n, c, c0 in PLAGES]}


def test_plan_chevauchement_deux_rushs():
    segments, total, avert = _plan(EDL_RESOLVE, _sources_factices())
    assert total == TOTAL
    assert [(s.sortie_debut, s.images, s.camera, s.camera_debut) for s in segments] == [
        (0, 55, "s3://b/A.MP4", 75),
        (55, 20, "s3://b/A.MP4", 200),
        (75, 30, "s3://b/B.MP4", 10),
        (105, 40, "s3://b/B.MP4", 110)]
    assert avert == []


def test_plan_trou_noir_et_raccord_continu():
    # Événement 2 décalé de 10 images : trou noir. Événement 3 prolonge le 2 dans B : fusion.
    edl = """TITLE: T
FCM: NON-DROP FRAME
001  AX       V     C        00:00:01:05 00:00:02:10 01:00:00:00 01:00:01:05
* FROM CLIP NAME: proxy.mov
002  AX       V     C        00:00:04:10 00:00:04:30 01:00:01:15 01:00:01:35
* FROM CLIP NAME: proxy.mov
003  AX       V     C        00:00:04:30 00:00:05:00 01:00:01:35 01:00:02:05
* FROM CLIP NAME: proxy.mov
"""
    segments, total, avert = _plan(edl, _sources_factices())
    assert total == 55 + 10 + 40
    assert [(s.sortie_debut, s.images, s.camera, s.camera_debut) for s in segments] == [
        (0, 55, "s3://b/A.MP4", 75), (55, 10, None, 0), (65, 40, "s3://b/B.MP4", 20)]
    assert any("trou" in a for a in avert)


def test_image_hors_plage_refusee():
    obj = _sources_factices()
    obj["plages"][1]["proxy_debut"] = 210        # trou 200..209 dans le proxy
    obj["plages"][1]["images"] = 140
    with pytest.raises(recouper.ErreurEntree, match="plage"):
        _plan(EDL_RESOLVE, obj)


def test_fcpxml_equivalent():
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE fcpxml>
<fcpxml version="1.9">
  <resources>
    <format id="r1" frameDuration="1/50s" width="1920" height="1080"/>
    <asset id="r2" name="proxy.mov" start="0s" duration="7s" hasVideo="1" hasAudio="1" format="r1"/>
  </resources>
  <library><event name="E"><project name="Timeline 1">
    <sequence format="r1" tcStart="3600/1s" tcFormat="NDF" duration="145/50s">
      <spine>
        <asset-clip ref="r2" name="proxy.mov" offset="3600/1s" start="55/50s" duration="55/50s"/>
        <asset-clip ref="r2" name="proxy.mov" offset="180055/50s" start="180/50s" duration="1s"/>
        <asset-clip ref="r2" name="proxy.mov" offset="180105/50s" start="6s" duration="40/50s"/>
      </spine>
    </sequence>
  </project></event></library>
</fcpxml>
"""
    m = recouper.lire_fcpxml(xml, FPS)
    assert m.debut_timeline == 180000
    s = recouper.lire_sources(_sources_factices())
    seg_x, total_x, _ = recouper.planifier(m, s, FPS, m.debut_timeline, 0, "proxy.mov", False)
    seg_e, total_e, _ = _plan(EDL_RESOLVE, _sources_factices())
    assert total_x == total_e
    assert [(a.sortie_debut, a.images, a.camera, a.camera_debut) for a in seg_x] == \
           [(a.sortie_debut, a.images, a.camera, a.camera_debut) for a in seg_e]


def test_controle_raccord_detecte_decalage():
    rng = np.random.default_rng(0)
    src = {i: rng.integers(0, 255, (90, 160), dtype=np.uint8) for i in range(9, 13)}
    seg = recouper.Segment(0, 2, "cam", 10, 3840, 2160)
    bon = {0: src[10], 1: src[11]}
    faux = {0: src[11], 1: src[12]}            # une image de trop au début
    assert all(r["ok"] for r in recouper.controler_raccords([seg], [src], bon))
    assert not any(r["ok"] for r in recouper.controler_raccords([seg], [src], faux))


# ─── Bout en bout ────────────────────────────────────────────────────────────

def test_proxy_correspond_aux_sources(medias):
    """Le proxy de test respecte le contrat de sources.json image par image."""
    lus = codes(lire_images(medias["proxy"], 320, 180))
    attendu = [(1, 20 + f) for f in range(200)] + [(2, 10 + f) for f in range(150)]
    assert lus == attendu


def test_rushs_lisibles(medias):
    assert codes(lire_images(medias["rushs"]["A"]))[:3] == [(1, 0), (1, 1), (1, 2)]
    assert codes(lire_images(medias["rushs"]["B"]))[-1] == (2, 249)
    assert recouper.sonder_camera(str(medias["rushs"]["B"]), FPS).debut_s == pytest.approx(3.2)


def test_recoupe_image_par_image(medias):
    d = medias["dossier"]
    sortie = d / "cut" / "sortie.mov"
    code = recouper.main([
        "--projet", "test", "--edl", str(medias["edl"]), "--wav", str(medias["wav"]),
        "--sources", str(medias["sources"]), "--sortie", str(sortie),
        "--travail", str(d / "travail"), "--taille", f"{W}x{H}", "--sans-envoi"])
    assert code == 0
    lus = codes(lire_images(sortie))
    assert len(lus) == TOTAL
    faux = [(j, lu, att) for j, (lu, att) in enumerate(zip(lus, ATTENDU)) if lu != att]
    assert faux == []
    # Format et audio
    p = recouper.sonder_sortie(sortie)
    v, a = p["video"], p["audio"]
    assert (v["codec_name"], v["pix_fmt"], v["r_frame_rate"]) == ("h264", "yuv420p", "50/1")
    assert int(v["nb_read_packets"]) == TOTAL
    assert (a["codec_name"], int(a["sample_rate"])) == ("pcm_s24le", 48000)
    assert int(a["duration_ts"]) == TOTAL * 48000 // FPS
    assert recouper.md5_audio(sortie) == recouper.md5_audio(medias["wav"])
    # GOP 100 : aucune image clé espacée de plus de 100 images
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries",
                        "packet=flags", "-of", "csv=p=0", str(sortie)],
                       capture_output=True, text=True, check=True)
    cles = [i for i, f in enumerate(r.stdout.split()) if f.startswith("K")]
    assert cles[0] == 0 and max(np.diff(cles + [TOTAL])) <= 100
    rapport = json.loads(sortie.with_name("sortie.rapport.json").read_text())
    assert rapport["raccords"]["faux"] == 0
    assert rapport["audio_identique_au_wav"] is True
    # Aucun intermédiaire ne reste
    assert list((d / "travail").glob("segment-*")) == []


def test_wav_de_mauvaise_duree_bloque(medias):
    d = medias["dossier"]
    court = d / "court.wav"
    x, sr = sf.read(medias["wav"])
    sf.write(court, x[: len(x) - 480], sr, subtype="PCM_24")   # 10 ms de moins
    code = recouper.main([
        "--projet", "test", "--edl", str(medias["edl"]), "--wav", str(court),
        "--sources", str(medias["sources"]), "--sortie", str(d / "cut" / "court.mov"),
        "--travail", str(d / "travail2"), "--taille", f"{W}x{H}", "--sans-envoi"])
    assert code == 3
    assert not (d / "cut" / "court.mov").exists()


def test_recoupe_avec_trou_noir(medias):
    """Un trou dans la timeline donne des images noires, le reste garde les bonnes images."""
    d = medias["dossier"]
    edl = d / "trou.edl"
    edl.write_text("""TITLE: Trou
FCM: NON-DROP FRAME

001  AX       V     C        00:00:00:00 00:00:00:30 01:00:00:00 01:00:00:30
* FROM CLIP NAME: proxy.mov

002  AX       V     C        00:00:05:40 00:00:06:10 01:00:00:37 01:00:01:07
* FROM CLIP NAME: proxy.mov

003  AX       A     C        00:00:05:40 00:00:06:15 01:00:00:37 01:00:01:12
* FROM CLIP NAME: proxy.mov
""")
    total = 30 + 7 + 20 + 5         # l'audio dépasse la vidéo de 5 images : noir en fin
    wav = d / "trou.wav"
    sf.write(wav, np.zeros((total * 48000 // FPS, 2), np.float32), 48000, subtype="PCM_24")
    sortie = d / "cut" / "trou.mov"
    code = recouper.main([
        "--projet", "test", "--edl", str(edl), "--wav", str(wav),
        "--sources", str(medias["sources"]), "--sortie", str(sortie),
        "--travail", str(d / "travail3"), "--taille", f"{W}x{H}", "--sans-envoi"])
    assert code == 0
    images = lire_images(sortie)
    assert len(images) == total
    lus = codes(images)
    assert lus[:30] == [(1, 20 + i) for i in range(30)]
    assert lus[37:57] == [(2, 10 + 90 + i) for i in range(20)]      # proxy 290 = B 100
    noirs = list(range(30, 37)) + list(range(57, 62))
    # gris plein écart après conversion : le noir vidéo (Y = 16) devient 0
    assert all(float(images[j].mean()) < 2 for j in noirs)


def test_son_reconstruit_depuis_voix(tmp_path):
    """Sans WAV du monteur : le son suit les coupes de l'EDL dans voix.wav."""
    sr, spf = 48000, 960
    voix = tmp_path / "voix.wav"
    x = (np.arange(300 * spf, dtype=np.float32) % 1000) / 2000.0   # signal repérable
    sf.write(str(voix), x, sr, subtype="FLOAT")
    brut = {"version": 1, "fps": FPS, "proxy": {"largeur": 1920, "hauteur": 1080, "images": 300},
            "plages": [{"proxy_debut": 0, "images": 200, "camera": "A.mp4", "camera_debut": 0,
                        "camera_largeur": W, "camera_hauteur": H},
                       {"proxy_debut": 200, "images": 100, "camera": "B.mp4", "camera_debut": 50,
                        "camera_largeur": W, "camera_hauteur": H}],
            "audio": {"wav": str(voix), "sample_rate": sr}}
    sources = recouper.lire_sources(brut)
    Seg = recouper.Segment
    segments = [Seg(0, 20, "A.mp4", 10), Seg(20, 30, "A.mp4", 30),   # contigus : pas de fondu
                Seg(50, 5, None), Seg(55, 40, "B.mp4", 60),          # noir puis rush B
                Seg(95, 10, "A.mp4", 190)]
    total = 105
    sortie = recouper.wav_depuis_voix(segments, total, brut, sources, FPS, tmp_path)
    y, sr_lu = sf.read(str(sortie), dtype="float32")
    info = sf.info(str(sortie))
    assert (info.subtype, sr_lu) == ("PCM_24", sr)
    assert len(y) == total * spf
    tol = 2 ** -22
    nf = int(recouper.FONDU_COUPE_S * sr)
    # A 10..60 recopié tel quel au milieu, sans fondu au raccord contigu 30/30.
    assert np.allclose(y[nf:50 * spf - nf], x[10 * spf + nf:60 * spf - nf], atol=tol)
    assert np.allclose(y[20 * spf - 5:20 * spf + 5], x[30 * spf - 5:30 * spf + 5], atol=tol)
    # Noir : silence. Rush B image 60 = proxy 210.
    assert not y[50 * spf:55 * spf].any()
    assert np.allclose(y[55 * spf + nf:95 * spf - nf], x[210 * spf + nf:250 * spf - nf], atol=tol)
    # Fondus aux coupes non contiguës : bords atténués.
    assert abs(y[55 * spf]) < 1e-3 and abs(y[95 * spf - 1]) < 1e-3
