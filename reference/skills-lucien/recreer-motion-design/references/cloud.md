# Mode cloud

## Préconditions

Le dépôt doit contenir le projet Remotion, les scripts cloud et ce skill.

Ajouter ces variables à l'environnement Claude Code cloud :

- `REMOTION_AWS_ACCESS_KEY_ID`
- `REMOTION_AWS_SECRET_ACCESS_KEY`
- `REMOTION_AWS_REGION`
- `FAL_KEY`

Garder la région `eu-north-1`. Ne jamais écrire une valeur dans le dépôt.

## Démarrage

```bash
bash cloud/setup.sh
bash cloud/fetch_inputs.sh NOM_PROJET
```

Le script installe ffmpeg, les paquets Node et les paquets Python. Il contrôle les noms des variables.

## Transcription

```bash
.venv/bin/python cloud/transcribe.py inputs/NOM_PROJET/video.mp4 \
  --asr fal --project NOM_PROJET --language en \
  --output edit/words.json
```

Le résultat utilise le format `w`, `s`, `e` du pipeline. Fal lit une URL S3 présignée.

## Rendu et assemblage

Rendre chaque composition sur Lambda. Garder une composition active à la fois.

Assembler les segments avec ffmpeg dans le conteneur. Mesurer dix secondes avant le rendu complet.

## Contrôle sans Jev

Extraire deux images par placement. Fournir les paires au modèle vision de la session cloud.

Utiliser les questions de `references/qa-checklist.md`. Appliquer les seuils décrits dans cette référence.

## Livraison

```bash
bash cloud/push_output.sh chemin/video-finale.mp4 NOM_PROJET
```

La commande renvoie une URL présignée valable sept jours.
