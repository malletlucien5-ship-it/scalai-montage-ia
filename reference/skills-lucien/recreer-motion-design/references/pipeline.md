# Pipeline

## Variables

```bash
export PROJECT=/chemin/du/projet
export REMOTION_DIR="$PROJECT/remotion"
export EDIT_DIR="$PROJECT/edit"
export REFERENCE="$PROJECT/ref/reference.mp4"
export TARGET=/chemin/video-cible.mp4
```

Les scripts acceptent des chemins explicites. Ils ne dépendent pas d'un dossier personnel.

## 1. Inventaire de la référence

Créer `CATALOGUE.md` avec une ligne par animation :

```text
| ID | Nom | Plages de référence en secondes | Contenu |
```

Extraire une planche à 10 images par seconde :

```bash
ffmpeg -ss DEBUT -t DUREE -i "$REFERENCE" \
  -vf 'fps=10,scale=960:-1' /tmp/motion-ID-%03d.jpg
```

Extraire les états clés en 1920 par 1080. Mesurer les rectangles, les couleurs et les images d'entrée.

## 2. Index des assets

```bash
python3 scripts/index_assets.py \
  --project "$PROJECT" \
  --catalogue "$PROJECT/CATALOGUE.md" \
  --output "$PROJECT/assets-index.json"
```

Le fichier contient les compositions Remotion et les images publiques. Chercher par identifiant, nom, description et mots du catalogue.

## 3. Métadonnées des compositions

Chaque composition exporte :

```ts
export const meta = {
  id: '09-orbes-level-up',
  durationInFrames: 282,
  fps: 30,
  description: 'Orbes de progression et consignes',
  occurrences: [
    {ref: [46.08, 51.42], from: 0, durationInFrames: 160, mode: 'plein'},
  ],
};
```

Lire toutes les occurrences :

```bash
node scripts/occurrences.mjs \
  --remotion "$REMOTION_DIR" \
  --output "$EDIT_DIR/occurrences.json"
```

## 4. Formats d'édition

`anchors.json` :

```json
{
  "segments": [
    {"ref_s": 0.0, "ref_e": 82.3, "cut_s": 0.0, "cut_e": 74.8, "absent": false}
  ],
  "mots_cles": [
    {"ref_t": 46.1, "cut_t": 41.7, "mot": "niveau"}
  ]
}
```

`placements.json` :

```json
[
  {
    "id": "09-orbes-level-up",
    "occ": 0,
    "from": 0,
    "dur": 160,
    "at": 41.7,
    "mode": "plein",
    "ref": [46.08, 51.42]
  }
]
```

Construire les placements :

```bash
python3 scripts/build_edit.py \
  --anchors "$EDIT_DIR/anchors.json" \
  --occurrences "$EDIT_DIR/occurrences.json" \
  --placements "$EDIT_DIR/placements.json" \
  --chapters "$EDIT_DIR/chapitres.json"
```

## 5. Mots et nouvelles coupes

Reporter les mots de la timeline source vers la coupe :

```bash
python3 scripts/words_cut.py \
  --source-map "$EDIT_DIR/montage.sources.json" \
  --cut-map "$EDIT_DIR/montage-cut.sources.json" \
  --words "$EDIT_DIR/montage.words.json" \
  --output "$EDIT_DIR/words_cut.json" \
  --transcript "$EDIT_DIR/transcript_cut.txt"
```

Reporter les ancres après une nouvelle coupe :

```bash
python3 scripts/remap.py \
  --old-words "$EDIT_DIR/words_cut.v1.json" \
  --new-words "$EDIT_DIR/words_cut.json" \
  --old-anchors "$EDIT_DIR/anchors.v1.json" \
  --anchors "$EDIT_DIR/anchors.json" \
  --old-captions "$EDIT_DIR/captions.v1.json" \
  --captions "$EDIT_DIR/captions.json"
```

Le contrôle de fin de mot cherche une coupe entre le début et la fin d'un mot. Toute coupe trouvée bloque l'assemblage.

## 6. Props

```bash
python3 scripts/make_props.py \
  --source "$TARGET" \
  --captions "$EDIT_DIR/captions.json" \
  --placements "$EDIT_DIR/placements.json" \
  --chapters "$EDIT_DIR/chapitres.json" \
  --output-dir "$EDIT_DIR/props"
```

## 7. Rendus Lambda et cache

Créer `render-config.json` :

```json
{
  "project_root": "/chemin/du/projet",
  "remotion_dir": "/chemin/du/projet/remotion",
  "source": "/chemin/video-cible.mp4",
  "output": "/chemin/video-finale.mp4",
  "placements": "/chemin/du/projet/edit/placements.json",
  "render_dir": "/chemin/du/projet/remotion/out/final",
  "site_name": "motion-project",
  "region": "REGION_DU_PROJET",
  "profile": "remotion-runtime",
  "scale": 1.3333333333333333,
  "fps": 30,
  "video_encoder": "libx264",
  "video_encoder_args": ["-crf", "16"],
  "copy_inactive": true,
  "sfx_gain": 0.4
}
```

Rendre les médias invalidés :

```bash
python3 scripts/render_final.py --config render-config.json --render-only
```

Le cache inclut la commande, la plage, le code partagé, la composition, les assets et les props.

## 8. Assemblage

Mesurer une fenêtre dense :

```bash
python3 scripts/render_final.py --config render-config.json \
  --skip-renders --benchmark 10 --start 120
```

Lancer l'assemblage après la mesure :

```bash
python3 scripts/render_final.py --config render-config.json --skip-renders
```

Le script étend les plages actives aux images clés. Il copie les segments sans calque quand l'encodeur produit le codec de la source. Il réencode les segments qui portent un plein écran, un calque, un badge ou un masque. Générer les masques statiques une seule fois.

Un mode parallèle exige un test de raccord image par image. Utiliser le mode séquentiel si un décalage apparaît.

## 9. Contrôle en masse

Extraire deux images par placement. Utiliser le premier tiers et les deux tiers de la durée. Créer une paire avec l'image de référence et l'image cible.

```bash
python3 ~/CODE/tools/jev/jev.py verify \
  --text rapport-qa.md \
  --rules references/qa-checklist.md
```

## 10. Livraison

```bash
ffprobe -v error -show_entries format=duration,size \
  -show_entries stream=codec_name,width,height,r_frame_rate,sample_rate \
  -of json /chemin/video-finale.mp4
```

Le rapport liste les fichiers, les durées, le coût AWS, les écarts et les signatures de cache.
