---
name: etalonnage-look-a
description: À utiliser dès qu'une vidéo de Lucien filmée à la caméra DJI est montée, rendue ou livrée (montage YouTube multicam, VSL, FAQ, Short, envoi à Ruben), ou quand Lucien parle d'étalonnage, de couleurs, de look, de colorimétrie, de « la version qu'on avait dite », d'image fade, verdâtre, trop sombre ou cramée.
---

# Étalonnage look A

Toute vidéo caméra DJI de Lucien sort étalonnée avec le look A.
Un rendu sans étalonnage n'est pas livrable.
Le look A ne change jamais. Seule la base change, mesurée rush par rush selon la lumière.

## Chaîne

Ordre : base du rush, puis look A, après la mise à l'échelle de l'image caméra.

```
base   = colorchannelmixer=rr=R:gg=G:bb=B,eq=gamma=1.03:contrast=1.05:saturation=1.05
look A = colorchannelmixer=rr=1.0:gg=0.972:bb=0.99,eq=brightness=0.03:contrast=1.06:saturation=1.12,unsharp=5:5:0.5
```

Le premier filtre du look A retire la dominante verte laissée par la base.

## Outil

`~/CODE/auto-edit/tools/etalonnage.py`, avec `/usr/bin/python3`.

| Besoin | Commande |
|---|---|
| Mesurer la base de chaque rush | `etalonnage.py bases --out DIR --cams DJI_A.MP4 DJI_B.MP4` |
| Lire les chaînes complètes | `etalonnage.py grades --out DIR` |
| Montage multicam | `pipeline.py assemble` étalonne d'office (`DIR/etalonnage.json`) |
| Rendu sans étalonnage, sur demande écrite de Lucien | `pipeline.py assemble --no-grade` |

`assemble` crée ou complète `DIR/etalonnage.json` tout seul : la commande `bases` sert seulement à mesurer avant le rendu.
Le rendu (`clipper/source_media.py`, champ `camera_grades`) étalonne l'image caméra avant la composition.
En plan visage, l'image entière reçoit le look A.
En plan écran, le carré visage reçoit le look A et la capture d'écran garde ses couleurs d'origine.
Aucun découpage manuel n'est nécessaire.

## Mesure de la base

1. Prendre 5 images du rush, à 10, 30, 50, 70 et 90 % de sa durée.
2. Mesurer la moyenne RVB du mur vide entre la tête et le bras du micro.
3. Gains de départ = (226, 223, 216) divisé par le mur brut.
4. Appliquer base + look A, puis remesurer.
5. Si G > R, baisser `gg`. Si B > G, baisser `bb`.
6. Si plus de 15 % des pixels saturent, baisser les trois gains.
7. Répéter jusqu'à ce que les deux contrôles passent.

Cible du mur après look A : R ≥ G ≥ B, autour de (220, 218, 212).
Pièce à mur blanc (chambre de Lucien, VSL AI Advantage) : cible (240, 238, 233), mur blanc neutre, choisie par Lucien le 11/10/2026 (`--cible 240,238,233`). La cible beige y donne un mur gris crème, rejeté.
Le contrôle exige la cible de la pièce à 6 près par canal : un mur chaud à (240, 236, 225) avec 13 % de saturation a été rejeté le 11/10/2026.
Aucun étalonnage supplémentaire ne se pose sur le look A sans planche validée par Lucien.
`etalonnage.json` garde les mesures et `controle_ok` par rush.

## Contrôles avant livraison

- `controle_ok` vaut `true` pour chaque rush du montage.
- Extraire une image visage et une image écran du rendu : le visage a le look A, l'écran garde ses couleurs.
- Un rush recadré plus serré que les autres reçoit sa propre base.

## Erreurs connues

| Erreur | Correction |
|---|---|
| Étalonner le montage entier après le rendu | La capture d'écran prend la dominante bleue de la base. Étalonner dans le rendu, caméra seule. |
| Réutiliser la base d'un autre jour | La lumière change. Mesurer chaque rush. |
| Régler la base sur le mur seul | L'image sature à 15 à 20 %. Le contrôle de saturation est obligatoire. |
| Livrer sans étalonnage parce que la consigne ne le redit pas | Le look A s'applique à chaque montage DJI. |

Version Short vertical et autres looks essayés : `~/.claude/skills/short-icones-pointage/references/couleurs.md`.
