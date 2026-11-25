# Multicam PiP + détection du script (vidéo du 12/09/2026)

## Objectif

Monter la vidéo « Higgsfield rebuild avec Claude Code » à partir de deux rushs
caméra DJI et d'un enregistrement d'écran OBS. Sortie : un MP4 1440p prêt pour
YouTube, coupes silences + euh, changement de plan toutes les 8 à 12 s, visage en
incrustation carrée bas droite sur les plans écran, jamais une image du script.

## Sources

| Source | Fichier | Durée | Format |
|---|---|---|---|
| Caméra 1 | `~/Desktop/DJI_20260912191003_0059_D.MP4` | 26 min 40 | 4K 50 fps |
| Caméra 2 | `~/Desktop/DJI_20260912193644_0060_D.MP4` | 9 min 03 | 4K 50 fps |
| Écran | `~/Movies/2026-09-12 19-04-44.mp4` | 35 min 41 | 1080p 30 fps HEVC |

L'audio final vient de la caméra. L'écran sert à l'image seulement.

## Décisions validées avec Lucien

- Incrustation bas droite.
- Script visible = plan face plein cadre.
- Coupes silences + euh seulement. Restarts et euh résiduels à la main.
- 1440p, vitesse x1.06, chaîne audio d'auto_edit complète.
- Cadence cam 50 fps conservée en sortie. Le 30 fps proposé aurait produit un
  judder 50 vers 30 sur le visage. L'écran 30 fps est dupliqué vers 50 sans dommage.

## Changements en cours de route

- Les deux clés ElevenLabs stockées renvoient 401. Transcription en repli local
  faster-whisper medium (`--transcriber whisper`). Whisper gomme une partie des
  « euh » : 5 fillers coupés au lieu de plusieurs dizaines. Lucien s'en charge.
- La fenêtre OBS apparaît 30 fois à l'écran (changements d'onglet). Ces plages
  sont ajoutées aux plages interdites, même traitement que le script.
- La cascade gloutonne d'`enforce_layout_constraints` ne tient pas un plafond
  sur les deux layouts. Remplacée par un solveur DP (`solve_layouts_dp`) quand
  `--max-face` est donné.

## Modifications dans `multicam.py`

1. **Layout `pip`** (`--layout-mode pip`) : l'écran croppé sur la fenêtre remplit
   le cadre (`fit` sur fond `0x181818`). Le visage recadré en carré depuis la 4K
   est incrusté dans un coin (`--pip-corner`, défaut bas droite), côté
   `--pip-size` × hauteur (défaut 0,22), marge `--pip-margin` (défaut 40 px).
   Le nom `split` reste celui du JSON et du prompt Claude, `pip` change le rendu.
2. **Cadence** : `--max-face` active `solve_layouts_dp`. Minimise la durée des
   segments qui contredisent la préférence LLM sous : chaque run dans
   [`--min-shot`, max(`--max-split`, `--max-face`)]. Segments verrouillés face :
   plages interdites, hors couverture écran, 8 s d'intro et d'outro. Un verrou
   remet le compteur de run à zéro et la portion libre qui le précède paie son
   dépassement. Bornes souples (40 pts/s), le DP rend toujours une solution.
3. **Plages interdites** : `--face-ranges FICHIER.json`, liste `[start, end]`
   en temps écran. Tout segment dont la fenêtre écran chevauche une plage
   (marge 0,5 s) est forcé face. Réappliqué au rendu depuis un JSON édité.
4. **Vitesse** : `--speed` passé à `_plan_segments`, vitesse effective par segment
   = frames entrée / frames sortie (setpts + atempo), comme auto_edit.
5. **Transcription** : `--transcriber whisper` = faster-whisper medium CPU int8,
   mots au format Scribe, prompt initial qui pousse les hésitations.
6. **Polish** : appel `polish_audio` inchangé (denoise, deesser, hpf, autoeq,
   bwe, loudnorm -14 LUFS), identique au run habituel.

## Détection du script (`detect_script_ranges.py`)

- Une image par seconde de l'écran, 480 px de large (`ffmpeg -vf fps=1`).
- Empreinte = image réduite en gris 48x27 normalisée. Distance L1 à une ou
  plusieurs références. Seuil auto (creux après le premier pic) ou `--threshold`.
- Plages contiguës, trous ≤ `--gap` comblés, plages < `--min` ignorées.
- Résultat du 12/09 : script 4 → 134 s et 367 → 368 s (seuil 0,12, second
  candidat le plus proche à 0,186 = page Topaz). OBS : 30 plages, 68 s.

## Réglages du run

```
--resolution 1440 --layout-mode pip --pip-corner bottom-right --pip-size 0.27 --pip-radius 0.08
--pip-margin 40 --speed 1.06 --screen-fit fit --screen-crop 120:26:1668:1028
--face-crop 1050:250:1800:1800 --min-shot 5 --max-split 14 --max-face 14
--face-ranges forbidden_ranges.json --transcriber whisper
```

Plan retenu (`~/Desktop/montage-2026-09-12/montage.plan-v1.json`) : 220 segments,
93 plans, 10,3 s de moyenne, aucun plan < 5 s, 16 min conservées → 15,1 min.

## Contrôles

- Sync GCC-PHAT : 7 points, confiance 140 à 220, résidu du fit 0,3 ms, dérive
  8,4 µs/s.
- Énergie vocale 150 ms après chaque coupe : 3 fins suspectes sur 220, toutes
  des jonctions de fillers.
- Aucun segment `pip` ne chevauche une plage interdite (marge 0,5 s).
- Test de rendu 3 segments : 15 s entrée → 14,16 s sortie (x1,06 exact), 704
  frames à 50 fps.
