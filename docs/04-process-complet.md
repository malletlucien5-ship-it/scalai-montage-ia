# Process complet

> Un mot inconnu ? Il est expliqué dans [00-lexique.md](00-lexique.md).

Un montage suit toujours le même ordre. Chaque étape attend la validation de la précédente.
Pour chaque étape : ce qui se passe, pourquoi, et ce que tu fais.

## 0. Réception des rushs

**Ce qui se passe.** Lucien t'envoie ses fichiers bruts :

- `DJI_*.MP4` : la vidéo de son visage, en 4K.
- `DJI_*.LRF` : les copies légères de ces vidéos. Elles servent à travailler vite.
- Le fichier OBS : la vidéo de son écran, avec sa voix.

**Ce que tu fais.** Range-les dans `chantiers/<date>-<sujet>/rushs/`.
Ce dossier reste sur ton ordinateur et ne part jamais sur GitHub.
Sans fichiers `.LRF`, Claude travaille sur la 4K. C'est plus lent, mais ça marche.

## 1. Entretien de chantier

**Ce qui se passe.** Claude te pose 7 questions sur la vidéo.
Type de vidéo, rushs, animations, illustrations filmées, illustrations à chercher, son et couleur, musique.

**Pourquoi.** Chaque vidéo est différente. Tes réponses fixent ce que Claude va fabriquer.
Elles vont dans `brief.json`. La vidéo suivante les reprend par défaut.

## 2. Calage et transcription

**Calage : ce qui se passe.** La caméra et OBS ont enregistré en même temps, mais pas au même instant exact.
Le fichier caméra peut commencer 3 secondes avant le fichier OBS, par exemple.
Claude compare le son des deux fichiers et trouve ce décalage.
C'est comme aligner deux enregistrements d'un même clap de mains.

**Pourquoi.** Sans calage, les lèvres de Lucien ne suivraient pas sa voix.
L'erreur restante doit être sous 1 milliseconde. Claude la mesure et te la donne.

**Piège connu.** La date écrite dans les fichiers DJI est fausse : l'horloge de la caméra est déréglée.
Seul le calage au son dit quel rush va avec quel fichier OBS.
Un rush qui ne se cale sur aucun fichier OBS est souvent un essai. Claude demande avant de l'utiliser.

**Transcription : ce qui se passe.** Claude fait écrire tout ce que dit Lucien, mot par mot.
Chaque mot reçoit son heure exacte dans la vidéo.
Le service ElevenLabs Scribe transcrit 18 minutes d'audio en 24 secondes.

**Pourquoi.** Ce texte horodaté sert à tout le reste : couper, choisir les plans, placer les animations.

## 3. Version vierge

**Ce qui se passe.** Claude fait un premier montage simple :

- il coupe les silences, les « euh », les bégaiements et les phrases ratées ;
- il alterne entre le visage de Lucien en grand et son écran avec un petit carré visage ;
- il nettoie la voix une seule fois.

Pas d'animation, pas de musique, pas de sous-titres à ce stade.

**Ce que tu fais.** Avant le rendu complet, Claude te montre un aperçu de 2 morceaux.
Tu vérifies la taille du carré visage et le cadrage. Tu dis OK ou tu demandes un changement.

**Sorties.**

- `montage.mp4` : la vidéo complète en haute qualité.
- Un proxy : petite copie légère, avec un numéro d'image dans un coin. Lucien la regarde pour faire ses coupes.

## 4. Planche d'étalonnage

**Ce qui se passe.** Claude fabrique une image qui montre le visage de Lucien en plusieurs versions de couleur.
Brute, avec le look A, et quelques variantes proches.

**Ce que tu fais.** Tu l'envoies à Lucien. Il choisit. En général, il garde le look A.

## 5. Coupes de Lucien

**Ce qui se passe.** Lucien ouvre la vidéo dans DaVinci Resolve et fait ses propres coupes.
Il te renvoie son projet Resolve ou une EDL, la liste de ses coupes.

**Ce que fait Claude.** Il applique les coupes de Lucien à l'image près.
Il n'ajoute aucune coupe de lui-même.
Il cherche ensuite les mots coupés en deux par erreur et te montre la liste avant tout rendu.

## 6. Animations et illustrations, en parallèle

**Ce qui se passe.** Pendant que Lucien coupe, Claude prépare les animations et les b-roll décidés au brief.
Chaque animation apparaît sur un mot précis de la transcription.

**Ce que tu fais.** Claude te montre deux images de chaque animation. Tu valides avant le rendu.

## 7. Sobre

**Ce qui se passe.** Claude assemble les coupes finales, la couleur choisie et la voix traitée.
C'est une version propre, sans animation.

**Ce que tu fais.** Tu l'envoies à Lucien. Il valide.

## 8. Motion

**Ce qui se passe.** Claude ajoute sur la version sobre :

- les animations et les b-roll ;
- les sous-titres ;
- la musique, nettement plus basse que la voix ;
- les bruitages.

Le volume final suit des valeurs fixes. Voix à -16 LUFS, aucun son qui sature.

## 9. Final et livraison

**Ce qui se passe.** Claude contrôle tout avant l'envoi :

- la durée ;
- le calage du son sur l'image ;
- les volumes ;
- des images prises à intervalles réguliers ;
- l'absence de mots coupés en deux.

Pour une vidéo longue, Claude rédige aussi la description YouTube avec les chapitres.

**Shorts.** Claude ne prépare les Shorts qu'après deux accords de Lucien.
D'abord la vidéo longue acceptée, puis son message « prépare les Shorts ».

## Retouches

- **Volume à corriger.** Claude repart des trois pistes séparées : voix, musique, bruitages.
  Il ne retouche que la piste concernée. La voix n'est jamais nettoyée deux fois.
- **Image à corriger.** Claude modifie `montage.json`, le plan du montage, puis relance le rendu.
  Seuls les morceaux modifiés sont refaits. Le reste vient du cache.
