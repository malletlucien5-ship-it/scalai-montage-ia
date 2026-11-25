# Étalonnage

## Chaîne validée (look A, 30/09/2026)

Base, appliquée au montage sur la source DJI :

```
colorchannelmixer=rr=1.10:gg=1.17:bb=1.25,eq=gamma=1.03:contrast=1.05:saturation=1.05
```

Look A, appliqué ensuite au montage 1080x1920 :

```
colorchannelmixer=rr=1.0:gg=0.972:bb=0.99,eq=brightness=0.03:contrast=1.06:saturation=1.12,unsharp=5:5:0.5
```

Le premier filtre du look A retire la dominante verte laissée par la base.

## Bases validées par pièce

Le look A ne change jamais. Seuls les gains `rr`, `gg`, `bb` de la base changent selon la lumière.

| Prise | Pièce | Base (gains R, V, B) | Mur mesuré après look A |
|---|---|---|---|
| `DJI_20260930210419_0071_D` (short Nul / Bien / Incroyable) | mur beige, lumière chaude | `rr=1.10:gg=1.17:bb=1.25` | légère dominante verte, acceptée |
| `DJI_20260930210806_0072_D` (avant / avec l'IA, v1) | mur beige, coin de plafond | `rr=1.126:gg=1.149:bb=1.207` | (231, 230, 221) |
| `DJI_20261001162806_0076_D` (avant / avec l'IA, v4 finale) | mur blanc, lumière froide, étagères | `rr=1.22:gg=1.17:bb=1.18` | (241, 241, 241) |
| `DJI_20261002190454_0081_D` (second cerveau, v4) | mur blanc cassé, canapé gris | `rr=1.158:gg=1.117:bb=1.152` | (218, 214, 204), 10,5 % saturé |

Chaîne complète de la v4 finale, dans l'ordre :

```
crop=1543:2743:341:469,scale=1080:1920:flags=lanczos,
colorchannelmixer=rr=1.22:gg=1.17:bb=1.18,eq=gamma=1.03:contrast=1.05:saturation=1.05,
colorchannelmixer=rr=1.0:gg=0.972:bb=0.99,eq=brightness=0.03:contrast=1.06:saturation=1.12,unsharp=5:5:0.5
```

## Calculer la base d'une nouvelle pièce

1. Extraire une image brute, recadrée, sans étalonnage.
2. Mesurer la moyenne RVB du mur sur une zone vide.
3. Gains de départ = (226, 223, 216) divisé par le mur brut.
4. Appliquer base + look A sur l'image et remesurer.
5. Si G > R, baisser `gg`. Si plus de 15 % des pixels saturent, baisser les trois gains.
6. Répéter jusqu'à ce que les deux contrôles passent sur chaque segment du montage. Script : `~/CODE/martell-motion-cloud/projets/short-second-cerveau-2026-10-02/edit/boucle_lumiere.py`.

Ne jamais s'arrêter au mur seul : le 02/10/2026, une base réglée sur le mur saturait 15 à 20 % de l'image et Lucien a jugé la luminosité horrible.

## Contrôle

Mesurer la moyenne RVB du mur sur une zone vide. Cible : R ≥ G ≥ B, autour de (220, 218, 212). Un mur avec G > R paraît fade et verdâtre.

## Autres looks proposés

Code dans `scripts/looks.py`. Lancer `python3 scripts/looks.py image.png planche.jpg` pour une planche comparée.

| Look | Effet |
|---|---|
| A Lumineux naturel | Retenu par Lucien |
| B Chaud premium | Tons chauds, courbe en S |
| C Ciné teal-orange | Ombres bleutées, noirs denses |
| D Pub éclatante | Très lumineux, mur proche du blanc brûlé |

Appliquer le look sur la vidéo avant Remotion. Les couleurs des étiquettes et des icônes restent alors intactes.
