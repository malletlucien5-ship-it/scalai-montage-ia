"""Appairage et synchronisation de l'audio maître avec le son témoin des caméras.

L'audio maître vient du fichier OBS (piste micro en PCM) ou d'un WAV séparé.

Origine du code :
- `~/CODE/auto-edit/multicam.py` : `_xcorr_offset` (GCC-PHAT, copié tel quel),
  `_load_pcm_window`, `measure_sync` (point large, points serrés, fit linéaire,
  tolérance de 15 ms), constantes `XCORR_SR`, `XCORR_MIN_CONF`, `SYNC_LINEAR_TOL`.
- `~/CODE/auto-edit/tools/sync_discontinuous.py` : rapport pic sur second pic,
  fenêtres de validation intercalées jamais utilisées pour le fit.

Conventions de temps :
- `u` : temps du son témoin de la caméra, 0 au premier échantillon audio.
- `t_w` : temps de l'audio maître, 0 au premier échantillon.
- Modèle : t_w = a + (1 + d) · u. `a` est l'offset, `d` la dérive d'horloge.
"""

from __future__ import annotations

import math
import subprocess
from dataclasses import dataclass, field

import numpy as np

# ─── Constantes (multicam.py) ────────────────────────────────────────────────
XCORR_SR = 16000        # taux pour la corrélation fine
XCORR_MIN_CONF = 6.0    # confiance min (pic / médiane) d'un point serré
SYNC_LINEAR_TOL = 0.015 # résidu max (s) pour accepter le fit linéaire

# ─── Constantes propres à l'appairage ────────────────────────────────────────
GROSSIER_SR = 4000      # recherche large sur tout le WAV
SONDE_MAX_S = 20.0      # durée max d'une fenêtre sonde
SONDE_PAS_S = 60.0      # une sonde par minute de caméra
SONDES_MIN, SONDES_MAX = 3, 16
GROSSIER_MIN_CONF = 14.0  # une recherche sur une heure de WAV monte à ~9 sur du bruit
GROSSIER_MIN_RATIO = 1.6  # pic / second pic hors ±0,3 s (sync_discontinuous : 1,35)
GROUPE_TOL_S = 0.2        # sondes du même appairage : offsets à 0,2 s près
FIN_FENETRE_S = 20.0
FIN_PAS_S = 60.0
FIN_POINTS_MAX = 40
FIN_RECHERCHE_S = 0.25    # ± autour de l'offset prévu
FIN_MIN_RATIO = 1.3
POINTS_MIN = 2
DERIVE_SPAN_MIN_S = 120.0  # en dessous, la dérive vient des autres paires
VALIDATION_MAX = 8
SILENCE_RMS = 1e-4         # -80 dBFS : fenêtre sans signal, ignorée


class SynchroErreur(RuntimeError):
    """Appairage impossible ou synchronisation non fiable."""


# ─── GCC-PHAT (multicam.py, copié tel quel) ──────────────────────────────────

def _load_pcm_window(wav_path, t0, dur, sr=XCORR_SR):
    r = subprocess.run(
        ["ffmpeg", "-nostdin", "-v", "error", "-ss", f"{max(0.0, t0):.3f}", "-t", f"{dur:.3f}",
         "-i", wav_path, "-f", "f32le", "-ac", "1", "-ar", str(sr), "pipe:1"],
        capture_output=True, stdin=subprocess.DEVNULL)
    return np.frombuffer(r.stdout, dtype=np.float32).copy()


def _xcorr_offset(ref, tgt, sr=XCORR_SR):
    """
    Position de `ref` à l'intérieur de `tgt` par corrélation GCC-PHAT
    (blanchiment spectral → robuste aux timbres différents des deux micros).
    Retourne (position_s, confidence). confidence = pic / médiane(|cc|).
    """
    if len(ref) < sr or len(tgt) <= len(ref):
        return None, 0.0
    ref = ref - ref.mean()
    tgt = tgt - tgt.mean()
    n = 1
    while n < len(ref) + len(tgt):
        n <<= 1
    R = np.fft.rfft(tgt, n) * np.conj(np.fft.rfft(ref, n))
    R /= np.abs(R) + 1e-12
    cc = np.fft.irfft(R, n)
    valid = cc[: len(tgt) - len(ref) + 1]
    p = int(np.argmax(valid))
    conf = float(valid[p] / (np.median(np.abs(valid)) + 1e-12))
    return p / sr, conf


# ─── GCC-PHAT détaillé : même formule, plus sous-échantillon et second pic ───

def _next_pow2(n: int) -> int:
    p = 1
    while p < n:
        p <<= 1
    return p


class SpectreCible:
    """Cache du spectre d'une cible longue. Évite une FFT du WAV par sonde."""

    def __init__(self, tgt: np.ndarray):
        self.tgt = (tgt - tgt.mean()).astype(np.float32)
        self._cache: dict[int, np.ndarray] = {}

    def spectre(self, n: int) -> np.ndarray:
        if n not in self._cache:
            self._cache = {n: np.fft.rfft(self.tgt, n)}
        return self._cache[n]


def xcorr_detail(ref: np.ndarray, tgt, sr: int, exclusion_s: float = 0.3) -> dict | None:
    """Comme `_xcorr_offset`, avec interpolation parabolique et rapport au second pic.

    `tgt` est un tableau ou un `SpectreCible`. Retourne None si les tailles ne
    permettent pas la mesure.
    """
    cible = tgt if isinstance(tgt, SpectreCible) else None
    tgt_arr = cible.tgt if cible else tgt
    if len(ref) < sr // 2 or len(tgt_arr) <= len(ref):
        return None
    ref = ref - ref.mean()
    if float(np.sqrt(np.mean(ref ** 2))) < SILENCE_RMS:
        return None
    n = _next_pow2(len(ref) + len(tgt_arr))
    T = cible.spectre(n) if cible else np.fft.rfft(tgt_arr - tgt_arr.mean(), n)
    R = T * np.conj(np.fft.rfft(ref, n))
    R /= np.abs(R) + 1e-12
    cc = np.fft.irfft(R, n)
    valid = cc[: len(tgt_arr) - len(ref) + 1]
    p = int(np.argmax(valid))
    peak = float(valid[p])
    conf = float(peak / (np.median(np.abs(valid)) + 1e-12))
    frac = 0.0
    if 0 < p < len(valid) - 1:
        y0, y1, y2 = float(valid[p - 1]), peak, float(valid[p + 1])
        den = y0 - 2 * y1 + y2
        if den < 0:
            frac = max(-0.5, min(0.5, 0.5 * (y0 - y2) / den))
    excl = int(exclusion_s * sr)
    lo, hi = max(0, p - excl), min(len(valid), p + excl + 1)
    reste = np.concatenate([valid[:lo], valid[hi:]])
    second = float(reste.max()) if len(reste) else 0.0
    ratio = peak / second if second > 1e-12 else float("inf")
    return {"position": (p + frac) / sr, "confiance": conf, "ratio": ratio}


# ─── Pistes ──────────────────────────────────────────────────────────────────

def decimer(x16: np.ndarray, facteur: int) -> np.ndarray:
    from scipy.signal import resample_poly
    return resample_poly(x16, 1, facteur).astype(np.float32)


@dataclass
class Piste:
    """Audio mono en mémoire, à XCORR_SR, avec sa version grossière."""
    nom: str
    x16: np.ndarray
    x4: np.ndarray = field(default=None, repr=False)
    _spectre: SpectreCible | None = field(default=None, repr=False)

    def __post_init__(self):
        if self.x4 is None:
            self.x4 = decimer(self.x16, XCORR_SR // GROSSIER_SR)

    @property
    def duree(self) -> float:
        return len(self.x16) / XCORR_SR

    def spectre_grossier(self) -> SpectreCible:
        if self._spectre is None:
            self._spectre = SpectreCible(self.x4)
        return self._spectre

    def fenetre(self, t0: float, dur: float, sr: int = XCORR_SR) -> np.ndarray:
        x = self.x16 if sr == XCORR_SR else self.x4
        a = int(round(t0 * sr))
        b = int(round((t0 + dur) * sr))
        if a < 0 or b > len(x):
            out = np.zeros(b - a, dtype=np.float32)
            s0, s1 = max(0, a), min(len(x), b)
            if s1 > s0:
                out[s0 - a: s1 - a] = x[s0:s1]
            return out
        return x[a:b]


# ─── Mesure d'une paire caméra / WAV ─────────────────────────────────────────

def _sondes(duree: float) -> tuple[list[float], float]:
    """Débuts des fenêtres sondes dans la caméra, et leur durée."""
    k = max(SONDES_MIN, min(SONDES_MAX, math.ceil(duree / SONDE_PAS_S)))
    w = min(SONDE_MAX_S, 0.8 * duree / k)
    if w < 1.0:
        return [], 0.0
    pas = duree / k
    return [i * pas + (pas - w) / 2 for i in range(k)], w


def recherche_grossiere(cam: Piste, wav: Piste) -> list[dict]:
    """Chaque sonde de la caméra cherchée dans tout le WAV, à GROSSIER_SR."""
    debuts, w = _sondes(cam.duree)
    cible = wav.spectre_grossier()
    out = []
    for u0 in debuts:
        ref = cam.fenetre(u0, w, GROSSIER_SR)
        m = xcorr_detail(ref, cible, GROSSIER_SR)
        if m is None:
            continue
        m["u"] = u0
        m["offset"] = m["position"] - u0
        m["retenue"] = (m["confiance"] >= GROSSIER_MIN_CONF
                        and m["ratio"] >= GROSSIER_MIN_RATIO)
        out.append(m)
    return out


def _meilleur_groupe(sondes: list[dict]) -> list[dict]:
    retenues = [s for s in sondes if s["retenue"]]
    meilleur, score = [], 0.0
    for s in retenues:
        groupe = [q for q in retenues if abs(q["offset"] - s["offset"]) <= GROUPE_TOL_S]
        sc = sum(q["confiance"] for q in groupe)
        if sc > score:
            meilleur, score = groupe, sc
    return meilleur


def _fit(points: list[dict]) -> tuple[float, float, float]:
    u = np.array([p["u"] for p in points])
    o = np.array([p["offset"] for p in points])
    if len(points) >= 2 and np.ptp(u) > 1e-6:
        d, a = np.polyfit(u, o, 1)
    else:
        d, a = 0.0, float(np.mean(o))
    resid = float(np.max(np.abs(o - (a + d * u)))) if len(points) else float("inf")
    return float(a), float(d), resid


def _fit_robuste(points: list[dict]) -> tuple[list[dict], list[dict], float, float, float]:
    """Fit linéaire, puis retrait des pires points tant que le résidu dépasse la tolérance.

    Au plus 20 % des points sont écartés. Retourne (gardés, écartés, a, d, résidu).
    """
    gardes = list(points)
    ecartes: list[dict] = []
    a, d, resid = _fit(gardes)
    max_ecart = int(0.2 * len(points))
    while resid > SYNC_LINEAR_TOL and len(gardes) > 3 and len(ecartes) < max_ecart:
        pire = max(gardes, key=lambda p: abs(p["offset"] - (a + d * p["u"])))
        gardes.remove(pire)
        ecartes.append(pire)
        a, d, resid = _fit(gardes)
    return gardes, ecartes, a, d, resid


def _point_fin(cam: Piste, wav: Piste, u0: float, w: float, prevu: float,
               recherche: float) -> dict | None:
    ref = cam.fenetre(u0, w)
    t0 = u0 + prevu - recherche
    tgt = wav.fenetre(t0, w + 2 * recherche)
    m = xcorr_detail(ref, tgt, XCORR_SR, exclusion_s=min(0.3, recherche / 2))
    if m is None:
        return None
    # Le pic aligne le centre des fenêtres : offset rattaché au centre.
    return {"u": u0 + w / 2, "offset": t0 + m["position"] - u0,
            "confiance": m["confiance"], "ratio": m["ratio"]}


def mesurer_paire(cam: Piste, wav: Piste) -> dict:
    """Mesure l'appairage d'une caméra avec un WAV.

    Retourne un dict avec `accepte`. Si accepté : offset `a`, dérive `d`,
    résidu, points, validation et intervalle `u` couvert.
    """
    sondes = recherche_grossiere(cam, wav)
    groupe = _meilleur_groupe(sondes)
    res: dict = {
        "camera": cam.nom, "maitre": wav.nom, "accepte": False,
        "sondes": [{k: round(float(s[k]), 4) for k in ("u", "offset", "confiance", "ratio")}
                   | {"retenue": s["retenue"]} for s in sondes],
        "confiance_grossiere": round(max((s["confiance"] for s in sondes), default=0.0), 2),
    }
    if not groupe:
        res["raison"] = "aucune sonde fiable"
        return res
    ref = max(groupe, key=lambda s: s["confiance"])
    a0 = ref["offset"]
    res["offset_grossier"] = round(a0, 4)

    # Intervalle de u couvert par le WAV, marge de 0,5 s
    u_debut = max(0.0, -a0) + 0.5
    u_fin = min(cam.duree, wav.duree - a0) - 0.5
    span = u_fin - u_debut
    if span < 2.0:
        res["raison"] = f"recouvrement trop court ({span:.1f} s)"
        return res
    w = min(FIN_FENETRE_S, span / 3)
    w = max(w, min(2.0, span))
    n_pts = max(3, min(FIN_POINTS_MAX, int(span / FIN_PAS_S) + 1))
    debuts = np.linspace(u_debut, u_fin - w, n_pts) if span > w else np.array([u_debut])
    # On part de la sonde de référence pour propager la dérive vers les deux bords.
    ordre = sorted(range(len(debuts)), key=lambda i: abs(debuts[i] - ref["u"]))
    points: list[dict] = []
    mesures: list[dict] = []
    for i in ordre:
        u0 = float(debuts[i])
        if len(points) >= 2:
            a_e, d_e, _ = _fit(points)
            prevu = a_e + d_e * (u0 + w / 2)
        else:
            prevu = a0
        p = _point_fin(cam, wav, u0, w, prevu, FIN_RECHERCHE_S)
        if p is None:
            continue
        p["retenu"] = p["confiance"] >= XCORR_MIN_CONF and p["ratio"] >= FIN_MIN_RATIO
        mesures.append(p)
        if p["retenu"] and abs(p["offset"] - prevu) <= GROUPE_TOL_S:
            points.append(p)
    points.sort(key=lambda p: p["u"])
    res["points_mesures"] = len(mesures)
    if len(points) < min(POINTS_MIN, len(debuts)):
        res["raison"] = f"{len(points)} point(s) fin(s) fiable(s) sur {len(mesures)}"
        return res
    gardes, ecartes, a, d, resid = _fit_robuste(points)
    res.update({
        "a": a, "d": d, "residu_ms": round(resid * 1000, 3),
        "points": [{k: round(float(p[k]), 6) for k in ("u", "offset", "confiance", "ratio")}
                   for p in gardes],
        "points_ecartes": len(ecartes),
        "confiance": round(float(np.median([p["confiance"] for p in gardes])), 2),
        "span_s": round(float(gardes[-1]["u"] - gardes[0]["u"]) if gardes else 0.0, 2),
        "derive_source": "mesuree",
    })
    if resid > SYNC_LINEAR_TOL:
        res["raison"] = f"fit linéaire refusé, résidu {resid * 1000:.1f} ms"
        return res
    if res["span_s"] < DERIVE_SPAN_MIN_S:
        res["derive_source"] = "courte"
    res["validation"] = valider_paire(cam, wav, a, d, [p["u"] for p in gardes], w)
    echecs = [v for v in res["validation"] if v["conclusif"] and not v["ok"]]
    if echecs:
        res["raison"] = f"{len(echecs)} fenêtre(s) de validation hors tolérance"
        return res
    res["accepte"] = True
    res["u_couvert"] = [max(0.0, -a / (1 + d)), min(cam.duree, (wav.duree - a) / (1 + d))]
    return res


def valider_paire(cam: Piste, wav: Piste, a: float, d: float, us: list[float],
                  w: float) -> list[dict]:
    """Fenêtres intercalées entre les points du fit, jamais utilisées pour le fit."""
    milieux = [(us[i] + us[i + 1]) / 2 for i in range(len(us) - 1)]
    if len(milieux) > VALIDATION_MAX:
        idx = np.linspace(0, len(milieux) - 1, VALIDATION_MAX).round().astype(int)
        milieux = [milieux[i] for i in sorted(set(idx))]
    out = []
    for uc in milieux:
        u0 = uc - w / 2
        if u0 < 0 or u0 + w > cam.duree:
            continue
        prevu = a + d * uc
        p = _point_fin(cam, wav, u0, w, prevu, 0.1)
        if p is None:
            continue
        delta = p["offset"] - prevu
        conclusif = p["confiance"] >= XCORR_MIN_CONF and p["ratio"] >= FIN_MIN_RATIO
        out.append({"u": round(uc, 3), "delta_ms": round(delta * 1000, 3),
                    "confiance": round(p["confiance"], 2), "conclusif": conclusif,
                    "ok": abs(delta) <= SYNC_LINEAR_TOL})
    return out


def appliquer_derive_globale(paires: list[dict]) -> float | None:
    """Les paires courtes reprennent la dérive des paires longues.

    La dérive est une propriété des deux horloges (caméra, enregistreur).
    Retourne la dérive globale, ou None si aucune paire n'est assez longue.
    """
    longues = [p for p in paires if p["accepte"] and p["derive_source"] == "mesuree"]
    if not longues:
        for p in paires:
            if p["accepte"] and p["derive_source"] == "courte":
                p["derive_source"] = "courte, non corrigée"
        return None
    poids = np.array([p["span_s"] ** 2 for p in longues])
    d_g = float(np.sum(poids * np.array([p["d"] for p in longues])) / np.sum(poids))
    for p in paires:
        if p["accepte"] and p["derive_source"] == "courte":
            us = np.array([q["u"] for q in p["points"]])
            os_ = np.array([q["offset"] for q in p["points"]])
            p["d_mesuree"] = p["d"]
            p["d"] = d_g
            p["a"] = float(np.mean(os_ - d_g * us))
            p["residu_ms"] = round(float(np.max(np.abs(os_ - (p["a"] + d_g * us)))) * 1000, 3)
            p["derive_source"] = "globale"
    return d_g


# ─── Rééchantillonnage de dérive ─────────────────────────────────────────────

RETARD_DEMI_TAPS = 128     # filtre de retard fractionnaire : 257 coefficients
RETARD_KAISER_BETA = 9.0


def retard_fractionnaire(y: np.ndarray, k0: int, r: float, n_out: int) -> np.ndarray:
    """out[n] = y(k0 + r + n), 0 <= r < 1, par sinus cardinal fenêtré (Kaiser).

    Bande passante plate bien au-delà de 12 kHz à 48 kHz, là où la chaîne coupe.
    """
    from scipy.signal import oaconvolve

    L = RETARD_DEMI_TAPS
    k = np.arange(-L, L + 1)
    h = np.sinc(k - r) * np.kaiser(2 * L + 1, RETARD_KAISER_BETA)
    h = (h / h.sum()).astype(np.float32)
    a = k0 - L
    seg = np.zeros(n_out + 2 * L, dtype=np.float32)
    s0, s1 = max(0, a), min(len(y), a + len(seg))
    if s1 > s0:
        seg[s0 - a: s1 - a] = y[s0:s1]
    # out[n] = Σ_k y[k0 + n + k] · h[k]
    return oaconvolve(seg, h[::-1], mode="valid")[:n_out].astype(np.float32)


def extraire_recale(master: np.ndarray, t_debut: float, d: float, n_out: int,
                    sr: int = 48000, marge: int = 4800) -> np.ndarray:
    """Échantillons out[n] = master(t_debut + (1 + d) · n / sr).

    Rééchantillonnage soxr en qualité VHQ au rapport exact (1 + d).
    ffmpeg `asetrate` n'accepte que des Hz entiers : 1 Hz à 48 kHz vaut
    20,8 µs/s, plus que la dérive mesurée (~11 µs/s). Pas d'atempo.
    La fraction d'échantillon restante passe par un retard fractionnaire.
    Sans lui, l'erreur atteignait un demi-échantillon (10 µs).
    """
    import soxr

    pos = t_debut * sr
    i_ent = math.floor(pos)
    frac = pos - i_ent
    i0 = i_ent - marge
    besoin = int(math.ceil(n_out * (1 + d))) + 2 * marge + 2
    seg = np.zeros(besoin, dtype=np.float32)
    s0, s1 = max(0, i0), min(len(master), i0 + besoin)
    if s1 > s0:
        seg[s0 - i0: s1 - i0] = master[s0:s1]
    if abs(d) < 1e-12:
        y = seg
        x0 = marge + frac
    else:
        # y[k] = seg(k · (1 + d))
        y = soxr.resample(seg, sr * (1 + d), sr, quality="VHQ").astype(np.float32)
        x0 = (marge + frac) / (1 + d)
    k0 = math.floor(x0)
    r = x0 - k0
    if r < 1e-6:
        out = y[k0: k0 + n_out]
    elif r > 1 - 1e-6:
        out = y[k0 + 1: k0 + 1 + n_out]
    else:
        out = retard_fractionnaire(y, k0, r, n_out)
    if len(out) < n_out:
        out = np.concatenate([out, np.zeros(n_out - len(out), dtype=np.float32)])
    return out


# ─── Contrôle final : audio livré contre son témoin ──────────────────────────

def residus_finaux(final16: np.ndarray, temoin: Piste, av: float, n_fenetres: int = 6,
                   w: float = 10.0, recherche: float = 0.1) -> list[dict]:
    """Décalage mesuré entre l'audio livré et le son témoin, en plusieurs points.

    `final16` est l'audio livré du rush à 16 kHz, 0 à la première image.
    Le témoin est au temps u = τ - av. Un résidu positif : audio livré en retard.
    """
    duree = len(final16) / XCORR_SR
    w = min(w, duree / 3)
    if w < 1.0:
        return []
    out = []
    for tau0 in np.linspace(0.5, duree - w - 0.5, n_fenetres):
        ref = final16[int(tau0 * XCORR_SR): int((tau0 + w) * XCORR_SR)]
        tgt = temoin.fenetre(tau0 - av - recherche, w + 2 * recherche)
        m = xcorr_detail(ref, tgt, XCORR_SR, exclusion_s=recherche / 2)
        if m is None:
            continue
        conclusif = m["confiance"] >= XCORR_MIN_CONF and m["ratio"] >= FIN_MIN_RATIO
        out.append({"tau": round(float(tau0), 3),
                    "residu_ms": round((recherche - m["position"]) * 1000, 3),
                    "confiance": round(m["confiance"], 2), "conclusif": conclusif})
    return out
