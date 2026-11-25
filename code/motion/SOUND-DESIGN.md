# Sound design : plan

Objectif : poser sur les 46 motion designs le même sound design que la vidéo de Dan Martell.
Analyse faite le 23/09/2026 sur `ref/ref.mp4`, fichiers de travail dans `sound/`.

## 1. Ce que contient la bande son de la référence

La voix a été séparée du reste avec Demucs (`sound/stems/htdemucs/ref/`).
La piste sans voix contient quatre couches.

| Couche | Rôle | Niveau mesuré |
|---|---|---|
| Voix | Dan | -16 LUFS intégré |
| Musique de fond | Nappe continue sous la voix, plus présente sur les écrans plein cadre | -37 à -43 LUFS, soit 21 à 27 LU sous la voix |
| Bruitages graves | Grondement bref ou nappe grave à chaque apparition d'élément (pilules, étapes, orbes, cartes) | Pics 12 dB au-dessus de la musique |
| Impacts et montées | Cartes de chapitre, iceberg, pyramide : impact large bande, grondement long, scintillement aigu | Jusqu'à -20 LUFS sur la scène iceberg |
| Interface | Clics, frappes clavier, envoi de message sur les fenêtres Claude | Petits pics aigus 3 à 16 kHz |

La carte complète est dans `sound/sound_map.md` (660 événements rattachés aux IDs du catalogue).
Chaque événement a son extrait audio dans `sound/clips_map/`.
Les gros plans spectraux sont dans `sound/specs/`.

Limite du détecteur : sur les écrans plein cadre, la musique a une grosse caisse régulière.
Le détecteur grave la compte comme bruitage (séries à 0,4 s d'écart sur 09, 24, 31, 37, 41).
Le tri final entre musique et bruitage se fait à l'écoute ou avec le classement de l'étape 3.

## 2. Musique : identifiée, récupérable à l'identique

Shazam reconnaît la musique de fond sur la piste sans voix, par fenêtres de 12 s toutes les 20 s.

| Plage dans la référence | Morceau | Artiste | Source | Confiance |
|---|---|---|---|---|
| ~45 s | Apparent Solution | Brendon Moeller | Epidemic Sound | 1 fenêtre |
| 140-230 s | Steall Waters | Luba Hilman | à confirmer sur Epidemic | 3 fenêtres |
| 420-570 s | Shadowed | John B. Lund | Epidemic Sound | 6 fenêtres |
| ~760 s et ~840 s | AIR (feat. Patricia Chaylade & Marilyn Garcia Leal) | Cosmic Call | à confirmer | 2 fenêtres |
| ~820 s | The Farmhouse | Silver Maple | Epidemic Sound | 1 fenêtre |

Les autres plages ne sont pas reconnues : musique trop basse ou morceaux absents de Shazam.

**Calage précis** (`sound/align_music.py`, chroma glissant sur l'aperçu Epidemic, sortie `sound/music_map.json`).
Dan change de morceau à chaque carte de chapitre. Chaque morceau démarre à 0:00 sur la carte.

| Chapitre | Plage (s) | Morceau | Départ dans le morceau |
|---|---|---|---|
| Intro | 0-22,8 | non identifié | |
| 1. Amateur | 22,8-82,3 | Apparent Solution, Brendon Moeller | 0:00 |
| 2. Habitué | 82,3-~263 | Steall Waters, Luba Hilman | 0:00 |
| 3. Intégrateur | ~263-404,2 | non identifié | |
| 4. Opérateur | 404,2-519,8 | Shadowed, John B. Lund | 0:00 |
| 4. Opérateur (suite) | 519,8-~575 | Shadowed, relancé | 0:00 |
| 5. Bâtisseur | ~575-734,4 | non identifié | |
| 6. Orchestrateur | 734,4-862,7 | The Farmhouse, Silver Maple | 0:00 |
| Outro | 862,7-897 | Pink Pulsar, ELFL | ~0:44 |

« AIR » (Cosmic Call) et « Polaroid Film » (KAYDEN) sortaient aussi dans Shazam. Ils sont absents du catalogue Epidemic et ne se calent pas : fausses détections.
Les trois plages non identifiées restent à chercher dans le catalogue Epidemic (recherche par ambiance, puis même calage chroma).

**Récupération** : un abonnement Epidemic Sound donne les mêmes fichiers, en qualité studio et sous licence.
La chaîne YouTube se déclare dans Epidemic pour éviter les réclamations Content ID.
Ne pas extraire la musique de la vidéo de Dan : pas de licence, qualité dégradée par la séparation.

**Étape à faire** : scanner les plages non reconnues par fenêtres de 8 s décalées de 4 s, pour compléter la liste.

## 3. Bruitages : pas de source publique, trois voies

Aucun pack de bruitages n'est attribué à l'équipe de Dan.
Shazam ne reconnaît pas les bruitages.
La musique vient d'Epidemic Sound, donc la banque de bruitages Epidemic est la source la plus probable.

| Voie | Fidélité | Qualité | Licence |
|---|---|---|---|
| A. Extraire les bruitages de la piste Demucs | Identique | Moyenne : restes de musique et artefacts | Aucune, à réserver à la référence d'écoute |
| B. Retrouver l'équivalent dans la banque Epidemic | Très proche, peut-être identique | Studio | Couverte par l'abonnement |
| C. Équivalents gratuits (Mixkit, Pixabay, Freesound) | Proche | Studio | Libre de droits selon la banque |

**Recommandation** : voie B, avec la voie A comme étalon.

### Résultat de la recherche d'identité (23/09/2026)

Méthode : empreinte de pics spectraux (principe de Shazam) entre la piste sans voix et 4 970 aperçus Epidemic, trouvés par une centaine de mots-clés.
Un fichier identique donne un pic net de votes à l'instant où il est posé.
Scripts : `sound/fp_scan.py`, sortie `sound/sfx_used.json` et `sound/sfx_used.md`.

**Confirmés, fichier identique** (20 à 42 votes, plusieurs utilisations) :

| Son Epidemic | Rôle chez Dan | Instants (s) |
|---|---|---|
| [Low, Long 03](https://www.epidemicsound.com/sound-effects/tracks/PP2iNsmWDD/) | Nappe grave sous chaque grand écran de titre serif (orbes, cartes Intégrateur, 3 façons, orbe Loops, pyramide, AI Playbook) | 22,2 ; 44,8 ; 246,0 ; 296,1 ; 426,1 ; 614,7 ; 762,1 ; 884,1 |
| [Designed, Boom, Low Hit](https://www.epidemicsound.com/sound-effects/tracks/pmCzzPFo22/) | Impact de chaque carte de chapitre (podiums 1 à 6) | 25,6 ; 82,5 ; 264,7 ; 403,6 ; 576,6 ; 735,0 |

**Probables, à confirmer à l'écoute** (12 à 19 votes, une ou deux utilisations) :
- intro 2 à 12 s : une douzaine d'impacts « Designed, Boom / Impact / Stinger / Bass Dive » empilés sous les sous-titres et l'iceberg ;
- [Swooshes, Whoosh, Low, Short 02](https://www.epidemicsound.com/sound-effects/tracks/xQCDxCzw3g/) à 36,2 et 401,8 s ;
- carte chapitre 6 : [Stinger, Aggressive Hit](https://www.epidemicsound.com/sound-effects/tracks/DWyxsBol9B/) 730,1 s, [Bass Dive, Sub Drop, Slow](https://www.epidemicsound.com/sound-effects/tracks/UydpArWUsp/) 733,5 s, [Riser, Low Risers](https://www.epidemicsound.com/sound-effects/tracks/1OpaNqtFpE/) 734,4 s ;
- outro : [Bass Dive, Cinematic Drop, Downer 18](https://www.epidemicsound.com/sound-effects/tracks/EGpNoXvVTj/) 865,7 s.

**Non retrouvés** : les petits sons fréquents (grave bref des pilules et étapes, pop des sous-titres, clics, frappe clavier).
Deux raisons probables. Ces sons graves courts donnent peu de pics spectraux, donc peu de votes. Les clics tombent souvent sous la voix, et Demucs les range en partie dans la piste voix.
Pour eux, on applique la voie B : le son Epidemic le plus proche de l'étalon, validé à l'oreille.

Méthode de la voie B :
1. Extraire un étalon propre par type de son depuis `clips_map/` : grondement de pilule, impact de chapitre, grondement long de l'iceberg, nappe des orbes, clic, frappe, envoi.
2. Pour chaque type, télécharger 20 à 40 candidats Epidemic par mots-clés (sub whoosh, low boom, cinematic impact, riser shimmer, UI click, keyboard typing).
3. Classer les candidats par similarité avec l'étalon : embeddings audio CLAP, distance cosinus, plus un contrôle par spectrogramme.
4. Garder le meilleur candidat par type, avec validation à l'oreille par Lucien sur une planche d'écoute.

## 4. Intégration dans les motion designs

1. Créer `remotion/public/sfx/` avec un fichier par type de son retenu.
2. Dans chaque composition, déclarer les signaux sonores en données : `{frame, son, gain_db}`. Les frames viennent de `sound_map.json`, recalées sur l'instant visuel de chaque apparition.
3. Ajouter un composant partagé `SfxTrack` qui pose un `<Audio>` Remotion par signal.
4. Rendre deux versions : l'aperçu mp4 avec bruitages, et un WAV des bruitages seuls par ID pour le montage.
5. Mixer au montage dans Resolve :
   - voix de Lucien à -16 LUFS ;
   - musique Epidemic 21 à 27 LU sous la voix, avec ducking automatique ;
   - bruitages 12 dB au-dessus de la musique.

## 5. Ce qu'il faut de Lucien

- Un abonnement Epidemic Sound. L'accès couvre la musique et les bruitages.
- Une écoute de validation de la planche de bruitages, 10 minutes.

## 6. Ordre d'exécution

1. Compléter l'identification de la musique (étape 2).
2. Extraire les étalons et construire la planche d'écoute de la référence (voie A).
3. Chercher et classer les équivalents Epidemic (voie B).
4. Intégrer les signaux sonores dans les 46 compositions et rendre.
5. Livrer la bobine complète avec son.
