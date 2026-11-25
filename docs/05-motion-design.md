# Motion design

> Un mot inconnu ? Il est expliqué dans [00-lexique.md](00-lexique.md).

## Faut-il en créer ?

Claude te pose la question à chaque vidéo. Repère par type :

| Type | Motion design |
|---|---|
| YouTube long | Oui : sous-titres animés, titres de chapitre, cartes, fenêtres d'outils |
| Pub ou VSL (vidéo de vente) | Oui, dense : intro, prix, étapes, appel à l'action |
| Short | Léger : sous-titres et icônes |
| Podcast hebdo | Panneau gris fixe, aucune animation en plus |
| Vidéo brute demandée par Lucien | Non |

## Références existantes

| Référence | Où | Contenu |
|---|---|---|
| Dan Martell, « 1000+ hours of Learning Claude » | `code/motion/CATALOGUE.md` | 46 animations recréées en Remotion (`code/motion/remotion/src/comps/01-…` à `46-…`) |
| Animations maison | `code/motion/remotion/src/comps/d2xx-…` | 34 animations faites pour les vidéos de Lucien : astuce, bandeau nom et titre, appel à cliquer sur un lien, téléphone d'inscription, logos d'applications |
| VSL « AI Advantage » | `reference/skills-lucien/recreer-motion-design/references/bibliotheque-motion-lucien.md` | Intro « TEMPS », horloge, prix, étapes, CTA. Médias absents ici : demande-les à Lucien |
| Nouvelle référence | Lien YouTube fourni par Lucien | Claude recrée chaque animation à l'identique |

Le code, les images, les vidéos IA et les polices de `remotion/public` sont ici.
Les bruitages sous licence Epidemic de `remotion/public/sfx/` ne le sont pas.
Une animation qui en a besoin affiche un manque au rendu. Claude te le signale et pose un son de ta bibliothèque.

## Règles de Lucien

- Une animation s'ancre sur un mot de la transcription. Jamais sur une seconde fixe.
- Textes en Helvetica Neue. Logos de marque officiels en couleur, jamais redessinés.
- Bleu de marque ScalAI : `#1A5CFF`. Une copie de référence garde les couleurs de la référence.
- Une copie reproduit la référence au même endroit, même taille, même timing.
- Aucun retour visage de moins de 1,5 s entre deux plans d'animation ou de b-roll.
- Deux images par animation placée, montrées avant le rendu complet.

## Lancer Remotion

```bash
cd code/motion/remotion
npm ci
npx remotion studio --no-open      # aperçu, ouvre seulement si tu le demandes
npx remotion render src/index.ts <Composition> out/x.mp4 --codec=h264 --crf=16
```

Animation sans fond, à poser par-dessus la vidéo : `--codec=prores --prores-profile=4444 --pixel-format=yuva444p10le --image-format=png`.
