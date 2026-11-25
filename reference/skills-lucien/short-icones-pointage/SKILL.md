---
name: short-icones-pointage
description: Use when Lucien a filmé un Short vertical DJI où il pointe du doigt et veut des icônes d'outils qui apparaissent à son geste, façon Dan Martell (Bad/Good/Best, avant/avec l'IA, classement d'outils). Déclencheurs : "short comme Dan Martell", "mets les logos là où je pointe", "même motion que ce short", "classement d'outils IA en short", nouvelle vidéo DJI_*.MP4 avec un lien youtube.com/shorts de référence.
---

# Short à icônes pointées

Copier la mise en page d'un Short de référence. Poser les icônes d'outils sur une prise où Lucien pointe sans parler.

Lire aussi `recreer-motion-design` pour les règles générales de recréation.

## Process

1. **Analyser la référence.** Télécharger avec `yt-dlp`. Extraire une planche à 2 i/s et les coupes (`select='gt(scene,0.06)'`). Mesurer titre, étiquettes, icônes et rampe de flou à 30 i/s. Noter chaque révélation.
2. **Analyser la prise.** Vérifier la rotation (`display_matrix: rotation=90` : vidéo verticale). Mesurer le son avec `volumedetect`. Une prise sans voix se coupe sur les gestes.
3. **Repérer les gestes.** Planche à 5 i/s par passage. Noter l'arrivée du doigt à 0,2 s près. Garder les passages complets.
4. **Couper et cadrer.** Adapter `scripts/render.py` et `cuts.json`. Caler la tête de Lucien sur celle de la référence : même hauteur, même taille.
5. **Prolonger le fond.** Voir [references/cadrage-fond.md](references/cadrage-fond.md).
6. **Étalonner.** Appliquer le look A de [references/couleurs.md](references/couleurs.md). Contrôler la dominante du mur.
7. **Poser les icônes.** Copier `template/` dans `remotion/` du projet. Lier `node_modules` depuis `~/CODE/martell-motion-cloud/remotion`. Remplir `props.json`.
8. **Sound design.** Voir [references/son.md](references/son.md).
9. **Contrôler.** Extraire l'image de chaque révélation +3. Le doigt doit être sur l'étiquette quand l'icône devient nette.
10. **Livrer.** `SendUserFile` en `attach`. Copier sur le bureau si Lucien le demande.

## Préférences de Lucien (validées le 30/09/2026)

- Une seule position pour le tableau sur toute la vidéo.
- Titre en gras, centré en x, à la hauteur du titre de la référence.
- Icônes à la taille de la référence (188 px). Ne jamais les réduire pour caser un texte.
- Icônes espacées régulièrement.
- Étiquettes alignées à droite, à 14 px de leur icône.
- Étiquettes en français : « Nul : », « Bien : », « Incroyable : ».
- Si Lucien trace des croix sur une capture, les étiquettes vont sur les croix.
- Mur plat partout : aucun coin de pièce visible.
- Étalonnage : look A, lumineux naturel. Le PowerGrade Kodak « P&F colo rapide » a été essayé puis écarté le 01/10/2026.
- Aucune coupe dans la vidéo de Lucien : une seule prise continue.
- Rien ne s'ouvre sur son écran.

## Préférences de Lucien (02/10/2026, Short second cerveau)

- Reprendre sa timeline EDL à l'identique. Vérifier que chaque entrée et chaque sortie tombe dans un silence.
- Motion design translucide : Lucien reste visible sous le fond et sous les cartes (cartes à 80 % d'opacité, flou d'arrière-plan 10 px).
- Fondu vers le fond uni doux et bas : rien d'opaque au-dessus de 900 px, bleu à 72 % au maximum en bas.
- Lumière de transition : grosse, qui descend comme un soleil couchant, coupée net sur l'image où l'on passe à Lucien qui parle.
- Bruitages discrets : crête du mix sous −3 dBFS, gains autour de 0,12.
- Split : tête grosse et haute (haut des cheveux vers 210-230 px, échelle 0,9 à 0,98). Le visage ne touche jamais le sous-titre ni le fondu.
- Aucun ding sous une onomatopée de Lucien (« brrroup ») : il fait lui-même le son.
- Sous-titres mot pour mot. Retranscrire le montage avec deux modèles et le contexte de la source avant de les écrire.
- Gabarit des sous-titres de la référence : Anton 66 px en split, 62 px en plein cadre, contour 0,1 em.

## Erreurs déjà faites

| Erreur | Correction |
|---|---|
| Recadrer une prise paysage en 9:16 | Demander une prise verticale en plein pied |
| Prolonger le fond du côté où le corps touche le bord | Le bras paraît coupé net. Ne prolonger que les zones vides |
| Flux Fill pour supprimer un coin de mur | Il redessine le coin. Recopier en miroir un pan de mur plat (`scripts/plate_mur_plat.py`) |
| Images en boucle (`-loop 1`) sans `-t` en sortie | Rendu infini. Mettre `-t` en sortie et `-framerate` sur chaque entrée en boucle |
| Étiquettes recalculées à chaque section | Lucien veut une position fixe |
| Détecteur de peau sur la référence | Les étiquettes jaunes passent pour de la peau. Mesurer la référence à la main |
| `open(` dans un heredoc Bash | Le hook anti-ouverture bloque. Écrire un script avec `Path.read_text()` |
| Extraire la musique ou les bruitages d'un Short | Droits d'auteur. Recréer les bruitages par synthèse. Musique : « Utiliser ce son » dans l'app YouTube |
| EDL Resolve sur un DJI lu avec le timecode à 50 i/s | La piste `tmcd` de la DJI tourne à 25 i/s : 08:22:41:16 vaut 41,64 s. Lire le time_base de la piste data, sinon toutes les coupes partent 0,32 s trop tard |
| B-roll iPhone HDR (HLG) en premier dans la plaque | La plaque hérite du balisage HLG et Remotion la rend rouge et pixelisée. Convertir avec `colorspace=all=bt709:iprimaries=bt2020:ispace=bt2020ncl:itrc=bt2020-10`, puis baliser la sortie en bt709 |

## Variantes

| Variante | Référence | Fichiers |
|---|---|---|
| Nul / Bien / Incroyable, debout, 3 icônes en colonne | Dan, UH0pqsq2i80 | `template/`, `scripts/` |
| Avant l'IA / avec l'IA, assis, 2 icônes côte à côte | Dan, jkSJqLsjcQ4 | `variantes/avant-avec-ia/` |
| Second cerveau : hook B-roll, tête en haut et carte en bas (Obsidian, graphe du vault, chat), plein cadre et CTA | Dan, 8ER6koqRjKM | `~/CODE/martell-motion-cloud/projets/short-second-cerveau-2026-10-02/` |

Variante avant / avec l'IA :
- Le carré blanc reste net. Seuls le logo et le nom sont flous avant le geste.
- La révélation dure 6 images. Le bip part sur la première.
- Les noms sont blancs avec un contour noir de 9 px : un contour fin ne se lit pas sur un mur clair.
- Le bip vient de `bip.py`, synthétisé d'après le spectre de la référence.

## Caler les bips sur la référence

Quand Lucien veut les bips « au même moment que la référence » :
1. Mesurer les départs de bips de la référence sur la première note (`compare_bips.py`, bande 1500-1700 Hz). Contrôler chaque départ avec la révélation visuelle.
2. Mesurer l'arrivée de chaque doigt sur la prise (`arrivees.py`, 25 i/s). Le détecteur marche sous lumière neutre.
3. Monter avec `render3.py` : chaque section garde la durée de la référence. Entre les deux gestes, la vitesse s'ajuste pour que chaque arrivée tombe sur l'image du bip.
4. Rendre la vidéo Remotion, puis poser les bips avec `pose_bips.py`. Le mixage audio de Remotion retarde les sons d'environ 45 ms.
5. Contrôler avec `compare_bips.py` : écart visé inférieur à 10 ms.

Sans coupe (préférence de Lucien depuis le 01/10/2026) : utiliser `render4.py`. Une seule prise continue, vitesse constante entre deux gestes consécutifs, vitesse normale au début et à la fin. Contrôler l'absence de saut avec `select='gt(scene,0.05)'`.

## PowerGrade DaVinci Resolve (.drx)

Un `.drx` ne s'applique pas directement dans ffmpeg. Le pilotage externe de Resolve exige la version Studio. Méthode :
1. Extraire le `<Body>` hexadécimal. Retirer le premier octet, puis décompresser en zstd.
2. Lire les nœuds avec `powergrade/dump_pb.py` : noms, conversions de couleur, LUT, mélange.
3. Ignorer les conversions d'entrée prévues pour une autre caméra (S-Log3, etc.) : la DJI filme en Rec.709.
4. Recréer le look en une LUT 3D avec `powergrade/build_lut.py`, depuis les LUT fournies avec Resolve (`/Applications/DaVinci Resolve.app/Contents/Resources/LUT/`).
5. Appliquer `lut3d` après la correction de base. Montrer une planche avant / après.

« P&F colo rapide » = Rec.709 → Cineon → Kodak 2383 D55, mélangé à 50 %. Fichier prêt : `powergrade/pf_look50.cube`.

Pièges : `--props` ne change pas la durée sans `calculateMetadata` dans `Root.tsx`. `ffprobe` répète les valeurs d'un `stream_group` : lire la première ligne.

## Icônes

Prendre les SVG de `@lobehub/icons-static-svg` sur jsDelivr. Repli : `simple-icons`. Zapier : prendre `simple-icons` et colorer en `#FF4F00`. GPT Image : logo OpenAI. Gmail : Wikimedia Commons. Gamma : icône officielle de l'App Store (API iTunes Search, vendeur Gamma Tech, Inc.). Granola : favicon Google `t3.gstatic.com/faviconV2`. Ne jamais remplacer un logo par un mot-marque inventé.

## Étalonnage par pièce

Le réglage de base dépend de la lumière de la pièce. Mesurer le mur après étalonnage. Si G > R, corriger les gains `rr`, `gg`, `bb` de la base, puis remesurer.

Le détecteur automatique de doigt échoue sous lumière chaude. Dans ce cas, relever les gestes sur la planche à 5 i/s.

## Rendu

Rendre Remotion sur le Mac : la police SF Pro de la référence n'existe que sur macOS. Compter 55 s pour 12 s de vidéo.
