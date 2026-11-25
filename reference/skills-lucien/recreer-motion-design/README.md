# recreer-motion-design

Skill pour recréer les animations d'une vidéo de référence avec Remotion. Il couvre l'inventaire, la réutilisation des assets, le son, le calage, AWS Lambda, l'assemblage et le contrôle visuel.

## Installation dans un environnement cloud

```bash
mkdir -p ~/.claude/skills
git clone https://github.com/malletlucien5-ship-it/recreer-motion-design.git \
  ~/.claude/skills/recreer-motion-design
```

Relancer ensuite la session de l'agent. Le skill se déclenche sur les demandes de copie de motion design ou de montage animé.

## Dépendances

- Python 3.10 ou plus récent
- Node.js 20 ou plus récent
- ffmpeg et ffprobe
- Remotion 4 avec `@remotion/lambda`
- AWS CLI configuré dans la région du projet
- esbuild dans le projet Remotion

Les scripts acceptent des chemins explicites. Aucun secret ne doit entrer dans le dépôt.
