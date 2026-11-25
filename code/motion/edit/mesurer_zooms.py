#!/usr/bin/env python3
"""Mesurer les zooms d'une vidéo de référence.

Le script estime, image par image, la similitude qui relie deux images
consécutives : échelle, translation et point fixe. Une suite d'échelles
supérieures à 1 donne une poussée progressive. Une coupe dont les deux côtés
montrent le même plan à une autre échelle donne un zoom sec.

Sorties :
- `--courbe` : échelle cumulée par image, utile pour lire une courbe d'easing.
- `--output` : liste des zooms avec début, fin, échelles, point visé et type.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np

ANALYSE_W = 640
ANALYSE_H = 360


def lire_images(source: str, debut: float | None, duree: float | None):
    """Décoder la vidéo en niveaux de gris à 640 x 360, sans changer la cadence."""
    cmd = ["ffmpeg", "-v", "error"]
    if debut is not None:
        cmd += ["-ss", f"{debut:.3f}"]
    cmd += ["-i", source]
    if duree is not None:
        cmd += ["-t", f"{duree:.3f}"]
    cmd += [
        "-vf", f"scale={ANALYSE_W}:{ANALYSE_H}:flags=area,format=gray",
        "-f", "rawvideo", "-",
    ]
    taille = ANALYSE_W * ANALYSE_H
    with subprocess.Popen(cmd, stdout=subprocess.PIPE) as proc:
        assert proc.stdout is not None
        while True:
            brut = proc.stdout.read(taille)
            if len(brut) < taille:
                break
            yield np.frombuffer(brut, np.uint8).reshape(ANALYSE_H, ANALYSE_W)


def fps_source(source: str) -> float:
    sortie = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=r_frame_rate", "-of", "csv=p=0", source],
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    num, den = sortie.split("/")
    return float(num) / float(den)


class Estimateur:
    """Similitude entre deux images par points ORB et RANSAC."""

    def __init__(self) -> None:
        self.orb = cv2.ORB_create(nfeatures=1500, fastThreshold=12)
        self.bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

    def points(self, image):
        return self.orb.detectAndCompute(image, None)

    def similitude(self, a, b):
        kp_a, des_a = a
        kp_b, des_b = b
        if des_a is None or des_b is None or len(kp_a) < 30 or len(kp_b) < 30:
            return None
        paires = self.bf.match(des_a, des_b)
        if len(paires) < 30:
            return None
        src = np.float32([kp_a[m.queryIdx].pt for m in paires])
        dst = np.float32([kp_b[m.trainIdx].pt for m in paires])
        matrice, masque = cv2.estimateAffinePartial2D(
            src, dst, method=cv2.RANSAC, ransacReprojThreshold=2.0,
            maxIters=2000, confidence=0.995,
        )
        if matrice is None:
            return None
        inliers = int(masque.sum())
        if inliers < 25:
            return None
        echelle = float(np.hypot(matrice[0, 0], matrice[1, 0]))
        return {
            "echelle": echelle,
            "tx": float(matrice[0, 2]),
            "ty": float(matrice[1, 2]),
            "inliers": inliers,
            "ratio": inliers / len(paires),
        }


def point_fixe(sim: dict) -> tuple[float, float] | None:
    """Point qui ne bouge pas pendant le zoom, en fraction de l'image."""
    s = sim["echelle"]
    if abs(1.0 - s) < 1e-4:
        return None
    x = sim["tx"] / (1.0 - s) / ANALYSE_W
    y = sim["ty"] / (1.0 - s) / ANALYSE_H
    return x, y


def difference(a, b) -> float:
    return float(np.mean(cv2.absdiff(a, b)))


def analyser(source: str, debut: float | None, duree: float | None):
    fps = fps_source(source)
    est = Estimateur()
    t0 = debut or 0.0
    lignes = []
    prec = None
    prec_pts = None
    for index, image in enumerate(lire_images(source, debut, duree)):
        pts = est.points(image)
        ligne = {"i": index, "t": round(t0 + index / fps, 4)}
        if prec is not None:
            ligne["diff"] = round(difference(prec, image), 2)
            sim = est.similitude(prec_pts, pts)
            if sim:
                ligne.update({k: round(v, 5) if isinstance(v, float) else v
                              for k, v in sim.items()})
        lignes.append(ligne)
        prec, prec_pts = image, pts
    return fps, lignes


def regrouper(lignes, fps, seuil_pas=0.0015, min_images=4, seuil_sec=0.04):
    """Transformer la suite d'échelles en zooms progressifs et zooms secs."""
    zooms = []
    courant = None

    def fermer():
        nonlocal courant
        if courant and len(courant["pas"]) >= min_images:
            pas = courant["pas"]
            cumul = float(np.prod([p["echelle"] for p in pas]))
            fixes = [point_fixe(p) for p in pas]
            fixes = [f for f in fixes if f and 0 <= f[0] <= 1 and 0 <= f[1] <= 1]
            profil = np.cumprod([p["echelle"] for p in pas])
            zooms.append({
                "type": "progressif",
                "debut": pas[0]["t"] - 1 / fps,
                "fin": pas[-1]["t"],
                "duree_images": len(pas),
                "facteur": round(cumul, 4),
                "sens": "avant" if cumul > 1 else "arriere",
                "point_vise": [round(float(np.median([f[0] for f in fixes])), 3),
                               round(float(np.median([f[1] for f in fixes])), 3)]
                if fixes else None,
                "profil": [round(float(v), 4) for v in profil],
            })
        courant = None

    for ligne in lignes:
        s = ligne.get("echelle")
        ratio = ligne.get("ratio", 0)
        if s is not None and ratio > 0.35 and abs(s - 1) > seuil_sec \
                and ligne.get("diff", 0) > 6:
            fermer()
            fixe = point_fixe(ligne)
            zooms.append({
                "type": "sec",
                "debut": ligne["t"],
                "fin": ligne["t"],
                "facteur": round(s, 4),
                "sens": "avant" if s > 1 else "arriere",
                "point_vise": [round(fixe[0], 3), round(fixe[1], 3)] if fixe else None,
            })
            continue
        if s is not None and ratio > 0.5 and abs(s - 1) > seuil_pas:
            sens = s > 1
            if courant and courant["sens"] != sens:
                fermer()
            if not courant:
                courant = {"sens": sens, "pas": []}
            courant["pas"].append(ligne)
        else:
            fermer()
    fermer()
    return zooms


def image_a(source: str, t: float):
    brut = subprocess.run(
        ["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", source, "-frames:v", "1",
         "-vf", f"scale={ANALYSE_W}:{ANALYSE_H},format=gray", "-f", "rawvideo", "-"],
        check=True, capture_output=True,
    ).stdout
    if len(brut) < ANALYSE_W * ANALYSE_H:
        return None
    return np.frombuffer(brut[:ANALYSE_W * ANALYSE_H], np.uint8).reshape(ANALYSE_H, ANALYSE_W)


def marquer_visages(source: str, zooms: list[dict]) -> None:
    """Indiquer si le zoom porte sur un plan où l'orateur est visible."""
    cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    for zoom in zooms:
        image = image_a(source, zoom["debut"] + 0.02)
        visages = [] if image is None else cascade.detectMultiScale(
            image, scaleFactor=1.1, minNeighbors=6, minSize=(40, 40))
        zoom["visage"] = len(visages) > 0
        if len(visages):
            x, y, w, h = max(visages, key=lambda v: v[2] * v[3])
            zoom["visage_centre"] = [round((x + w / 2) / ANALYSE_W, 3),
                                     round((y + h / 2) / ANALYSE_H, 3)]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("source", help="Fichier ou URL de la référence")
    parser.add_argument("--debut", type=float, help="Début de la fenêtre en secondes")
    parser.add_argument("--duree", type=float, help="Durée de la fenêtre en secondes")
    parser.add_argument("--output", required=True, help="JSON des zooms")
    parser.add_argument("--courbe", help="JSON des mesures image par image")
    args = parser.parse_args()

    fps, lignes = analyser(args.source, args.debut, args.duree)
    zooms = regrouper(lignes, fps)
    marquer_visages(args.source, zooms)
    Path(args.output).write_text(json.dumps(
        {"source": args.source, "fps": fps, "zooms": zooms},
        indent=2, ensure_ascii=False))
    if args.courbe:
        Path(args.courbe).write_text(json.dumps(lignes))
    print(f"{len(zooms)} zooms, {len(lignes)} images analysées", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
