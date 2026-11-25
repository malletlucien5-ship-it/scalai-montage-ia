# Chaîne audio exacte

Valeurs lues dans `~/CODE/auto-edit/auto_edit.py`, fonction `polish_audio`.
Elles viennent d'un calage Optuna contre Auphonic.
Ne pas les modifier sans mesure.

La chaîne s'applique une seule fois, après la concaténation des clips.
Un master déjà traité ne repasse jamais dedans.
L'option `denoise=False` coupe les étages 1, 2 et 3 ensemble.

## Ordre des étages

| # | Étage | Réglage |
|---|---|---|
| 0 | Extraction | WAV 48 kHz, mono, PCM 16 bits |
| 1 | DeepFilterNet3 | Débruitage et déréverbération par modèle |
| 2 | Gate de voix par VAD | Non-voix à -80 dB, marge 60 ms, fondu 30 ms |
| 3 | Débruitage résiduel | `afftdn=nr=4.2:nf=-25` |
| 4 | Coupe-bas | `highpass=f=65:p=2` |
| 5 | Coupe-haut | `lowpass=f=12110` |
| 6 | Égalisation voix | 7 bandes, table ci-dessous |
| 7 | Exciter | `aexciter=amount=0.23:drive=4.1:blend=0:freq=6500:ceil=14000` |
| 8 | Dé-esseur | `deesser=i=0.17` |
| 9 | Compresseur | Seuil -19,6 dB, ratio 2,16, attaque 14 ms, relâche 186 ms, gain +1,96 dB |
| 10 | Normalisation | `loudnorm` deux passes, I=-15,76, TP=-1,19, LRA=6,3, `linear=true` |
| 11 | Recalage | Latence de chaîne mesurée puis compensée, `apad` sur la durée vidéo exacte |

Un seul étage dynamique existe. Le gate `compand` et `dynaudnorm` ont été retirés car la cascade produisait du pompage.

L'exciter passe avant le compresseur. Ses harmoniques seraient recomprimées dans l'autre ordre.

## Table d'égalisation

| Fréquence | Q | Gain | Rôle |
|---|---|---|---|
| 250 Hz | 1,0 | +4,13 dB | chaleur |
| 500 Hz | 1,4 | -3,04 dB | retrait de boue |
| 1 500 Hz | 1,0 | +2,65 dB | basse présence |
| 3 000 Hz | 1,0 | +8,72 dB | présence forte |
| 5 500 Hz | 1,2 | +3,63 dB | clarté |
| 8 500 Hz | 1,0 | +1,99 dB | air |
| 11 000 Hz | 1,2 | +3,18 dB | haut de l'air |

## Cible de niveau

La cible réelle vaut **-15,76 LUFS**, pas -14 LUFS.
Le pic vrai plafonne à -1,19 dBTP.
La plage dynamique visée vaut 6,3 LU.
La mesure de la première passe alimente la seconde.

## Équivalent DaVinci Resolve

Un monteur sans le pipeline Python reproduit la chaîne dans Fairlight, dans cet ordre, sur la piste de voix.

| Étage | Outil Fairlight |
|---|---|
| 1 et 3 | Noise Reduction, réglage doux |
| 2 | Gate, seuil sous le niveau de respiration, attaque 5 ms, relâche 60 ms |
| 4 et 5 | EQ, coupe-bas 65 Hz, coupe-haut 12 kHz |
| 6 | EQ paramétrique, les 7 bandes du tableau |
| 8 | De-Esser, intensité faible |
| 9 | Compressor, les 5 valeurs du tableau |
| 10 | Loudness normalisation sur le bus principal, cible -15,76 LUFS, pic -1,19 dBTP |

L'exciter n'a pas d'équivalent direct dans Fairlight.
Le remplacer par un léger relevé de 1 dB entre 6,5 et 14 kHz.

## Contrôle

Mesurer le rendu avant livraison.
La mesure attendue tient à 0,5 LU de la cible.
Le pic vrai ne dépasse jamais -1 dBTP.
