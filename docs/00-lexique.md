# Lexique : tous les mots du montage, en clair

Lis cette fiche avant les autres. Chaque mot technique du dépôt y est expliqué.
Un mot inconnu dans une autre fiche ? Cherche-le ici avec Cmd+F.
Tu peux aussi demander à Claude : « explique-moi ce mot avec un exemple ».

## L'histoire d'une vidéo en 10 lignes

1. Lucien se filme face à une caméra et enregistre son écran en même temps.
2. Tu reçois donc deux types de fichiers : la vidéo de son visage et la vidéo de son écran.
3. Claude met ces deux vidéos en phase, comme on aligne deux pistes de musique.
4. Claude écrit le texte de tout ce que Lucien dit, mot par mot, avec l'heure exacte de chaque mot.
5. Grâce à ce texte, Claude coupe les silences, les « euh » et les phrases ratées.
6. Claude choisit quand montrer le visage et quand montrer l'écran.
7. Claude corrige les couleurs du visage et nettoie le son de la voix.
8. Lucien regarde, fait ses propres coupes et valide.
9. Claude ajoute les animations, les images d'illustration, la musique et les bruitages.
10. Claude contrôle le résultat. Tu envoies le fichier final à Lucien.

## Le tournage

| Mot | Ce que ça veut dire |
|---|---|
| **Rush** | Fichier vidéo brut, tel qu'il sort de la caméra, avant tout montage. |
| **Prise** | Un enregistrement continu. Lucien peut faire plusieurs prises pour une vidéo. |
| **DJI** | Marque de la caméra de Lucien. Ses fichiers s'appellent `DJI_0042.MP4`. |
| **Fichier LRF** | Petite copie basse qualité que la caméra DJI crée à côté de chaque rush. Elle sert à travailler vite. Même nom que le rush, avec `.LRF` à la fin. |
| **OBS** | Logiciel gratuit qui enregistre l'écran de l'ordinateur. Il enregistre aussi le micro de Lucien. Le fichier porte la date et l'heure, par exemple `2026-11-20 14-03-12.mp4`. |
| **Script** | Le texte que Lucien lit pendant qu'il filme. Il est dans un Google Doc. |
| **Prompteur** | Écran qui fait défiler le script devant Lucien pour qu'il le lise. |
| **Face caméra** | Lucien regarde l'objectif et parle au spectateur. |

## Les formats

| Mot | Ce que ça veut dire |
|---|---|
| **4K** | Image très détaillée de 3840 points de large. Les rushs DJI sont en 4K. Ils pèsent lourd. |
| **2560x1440** | Taille de l'image finale d'une vidéo YouTube : 2560 points de large, 1440 de haut. |
| **1080x1920** | Taille d'un Short : image verticale, comme un écran de téléphone. |
| **i/s (images par seconde)** | Une vidéo est une suite de photos. 50 i/s = 50 photos par seconde. Les vidéos de Lucien sont à 50 i/s. |
| **x1,06** | La vidéo finale est accélérée de 6 %. Lucien parle un peu plus vite, sans que ça s'entende. |
| **YouTube long** | Vidéo de 10 à 40 minutes sur la chaîne de Lucien. |
| **Short** | Vidéo verticale de moins d'une minute pour YouTube Shorts, TikTok ou Reels. |
| **Pub** | Vidéo courte diffusée en publicité payante sur Facebook ou Instagram. |
| **VSL** | « Video Sales Letter ». Vidéo qui présente une offre et pousse à réserver un appel. |
| **Podcast hebdo** | Vidéo de la semaine où Lucien commente les actualités de l'IA. |

## Les étapes du montage

| Mot | Ce que ça veut dire |
|---|---|
| **Chantier** | Le dossier d'une vidéo. Il contient les rushs, les réglages et les sorties. Un chantier = une vidéo. |
| **Brief** | Tes réponses aux 7 questions de Claude au début d'une vidéo. Fichier `brief.json`. |
| **Calage** (ou synchro) | Mettre la vidéo du visage et la vidéo de l'écran en phase. Claude compare le son des deux fichiers. Il trouve le décalage exact, comme on aligne deux enregistrements du même clap. |
| **Résidu de calage** | L'erreur qui reste après le calage. Sous 1 milliseconde, c'est parfait : l'œil et l'oreille ne voient aucun décalage. |
| **Transcription** | Le texte écrit de tout ce que Lucien dit. |
| **Horodatage** | L'heure exacte de chaque mot dans la vidéo, par exemple « Claude » à 12,48 s. Claude s'en sert pour couper et pour placer les animations. |
| **Coupe** | Un morceau retiré de la vidéo : silence, « euh », bégaiement, phrase ratée. |
| **Mot tranché** | Un mot coupé en deux par erreur. Claude les cherche après chaque série de coupes. |
| **Alternance visage/écran** | Le montage passe du visage de Lucien en grand à son écran d'ordinateur, puis revient. Ça garde le spectateur attentif. |
| **Carré visage** | Petit carré aux coins arrondis, en bas à droite, qui montre le visage de Lucien pendant qu'on voit son écran. |
| **Recadrage (crop)** | Garder une partie de l'image et jeter le reste. Exemple : garder le visage, retirer le mur autour. |
| **Plage interdite** | Moment où l'écran de Lucien montre son script ou la fenêtre d'OBS. Le spectateur ne doit jamais le voir. Claude montre alors le visage. |
| **Cadence** | Le rythme des changements de plan. Ici : un changement toutes les 4 à 10 secondes. |
| **Version vierge** | Premier montage : coupes et alternance visage/écran, sans animation ni musique. |
| **Proxy** | Copie légère et petite d'une vidéo. Lucien la regarde sur son téléphone pour couper vite. |
| **Compteur d'images** | Numéro d'image affiché dans un coin du proxy. Lucien peut dire « coupe à l'image 1234 ». |
| **Aperçu** | Un petit extrait rendu avant le gros rendu. Il sert à vérifier un réglage sans perdre une heure. |
| **Rendu** | Le moment où l'ordinateur fabrique le fichier vidéo final. Ça peut prendre de quelques minutes à plusieurs heures. |
| **Encodage** | La compression de la vidéo dans un fichier `.mp4`. Fait partie du rendu. |
| **Cache** | Morceaux déjà rendus que Claude garde. Si tu changes un détail, seuls les morceaux touchés sont refaits. |
| **Sobre** | Version propre : coupes finales, couleurs et son traités, sans animation. |
| **Motion** (version) | La version sobre avec les animations, les illustrations, la musique et les bruitages. |
| **Final** | La version contrôlée, prête à publier. |
| **Livrable** | Un fichier envoyé à Lucien pour validation. |

## Le logiciel de montage de Lucien

| Mot | Ce que ça veut dire |
|---|---|
| **DaVinci Resolve** | Logiciel de montage vidéo gratuit. Lucien y fait ses propres coupes. |
| **EDL** | Petit fichier texte qui liste les coupes faites dans Resolve. Claude le lit pour appliquer les coupes de Lucien. |
| **fcpxml** | Autre format de liste de coupes. Resolve sait l'ouvrir. |
| **Projet Resolve** | Le fichier de travail de Lucien dans Resolve, avec ses coupes. |

## L'image et la couleur

| Mot | Ce que ça veut dire |
|---|---|
| **Étalonnage** | Corriger les couleurs et la lumière d'une image. Exemple : rendre une peau moins verte ou une image moins sombre. |
| **Look A** | Le réglage de couleur choisi par Lucien pour son visage. Image un peu plus lumineuse, contrastée et colorée, peau chaude. Il s'applique à toutes ses vidéos. Il ne change jamais. |
| **Base** | Petite correction faite avant le look A, rush par rush, selon la lumière du jour. Elle rend les rushs pareils entre eux. |
| **Planche d'étalonnage** | Une image qui montre la même photo du visage en plusieurs versions : brute, look A, variantes. Lucien choisit. |
| **Planche** (en général) | Une image qui rassemble plusieurs vignettes de la vidéo côte à côte. On voit tout d'un coup d'œil. |
| **LUT** | Fichier de réglage couleur qu'on charge dans un logiciel de montage. Une sorte de filtre Instagram professionnel. |
| **Powergrade** | Réglage couleur enregistré dans Resolve, à réutiliser d'une vidéo à l'autre. |
| **Brut** | L'image telle qu'elle sort de la caméra, sans correction. |

## Le son

| Mot | Ce que ça veut dire |
|---|---|
| **Piste** | Une couche de son. La vidéo finale en a trois : voix, musique, bruitages. |
| **Chaîne voix** | Une suite de traitements appliqués à la voix, dans un ordre fixe. Elle rend la voix claire et régulière. |
| **Débruitage** | Retirer les bruits de fond : ventilateur, rue, souffle du micro. DeepFilterNet est l'outil utilisé. |
| **Gate** | Coupe automatique du son quand personne ne parle. Les respirations et bruits entre les phrases disparaissent. |
| **Coupe-bas / coupe-haut** | Retirer les sons très graves (vibrations, ronflement) et très aigus (sifflements). |
| **Égalisation** | Monter ou baisser certaines fréquences de la voix, comme les réglages basses et aigus d'une enceinte. |
| **Exciter** | Ajoute un peu de brillance à la voix pour qu'elle sonne plus présente. |
| **Dé-esseur** | Adoucit les « s » et les « ch » trop sifflants. |
| **Compresseur** | Rapproche les passages forts et faibles. La voix garde le même volume du début à la fin. |
| **Normalisation** | Régler le volume global à une valeur cible précise. |
| **LUFS** | Unité du volume ressenti par l'oreille. YouTube vise environ -14 LUFS. Les vidéos de Lucien sont à -16 LUFS. Plus le chiffre est proche de 0, plus c'est fort. |
| **LU** | Écart de volume entre deux sons. « Musique 21 LU sous la voix » = la musique est nettement plus basse que la voix. |
| **dBFS et crête** | La crête est le pic de son le plus fort. 0 dBFS est le maximum absolu. Au-delà, le son grésille. Aucune crête ne doit toucher 0 dBFS. |
| **Ducking** | La musique baisse toute seule quand Lucien parle et remonte quand il se tait. |
| **Bruitages (sfx)** | Petits sons qui accompagnent les animations : clic, « whoosh », frappe de clavier. |
| **Sound design** | Le choix et le placement des bruitages. |
| **Stems** | Les trois pistes livrées à part : `voix.wav`, `musique.wav`, `bruitages.wav`. On peut retoucher un volume sans tout refaire. |
| **Master** | Le son final mélangé, prêt à publier. |
| **Mixage** | Régler le volume de chaque piste pour qu'elles s'entendent bien ensemble. |

## Les animations et illustrations

| Mot | Ce que ça veut dire |
|---|---|
| **Motion design** | Animations graphiques ajoutées à la vidéo : textes qui apparaissent, logos, flèches, cartes, sous-titres animés. |
| **Remotion** | Outil qui fabrique des animations vidéo à partir de code. Claude écrit le code, Remotion produit la vidéo. |
| **Composition** | Une animation dans Remotion. Le dépôt en contient 80. |
| **Référence** | Une vidéo d'un autre créateur dont Lucien veut copier le style d'animation. Exemple : Dan Martell. |
| **Sous-titres cinétiques** | Sous-titres animés, mot par mot, qui apparaissent au rythme de la voix. |
| **Lower third** | Bandeau en bas de l'écran avec un nom et un titre, par exemple « Lucien, fondateur de ScalAI ». |
| **CTA** | « Call to action ». Message qui demande au spectateur d'agir : réserver un appel, cliquer sur un lien. |
| **Calque transparent** | Une animation sans fond, qu'on pose par-dessus la vidéo. |
| **B-roll** | Plan d'illustration posé sur la voix de Lucien. Exemple : il parle de bureaux, on voit un bureau. |
| **Banque libre** | Site de vidéos gratuites et utilisables légalement : Pexels, Mixkit. |
| **Licence** | Le droit d'utiliser une vidéo ou une musique. Sans licence valable, YouTube peut bloquer la vidéo. |
| **Ancrer une animation sur un mot** | Faire apparaître l'animation au moment exact où Lucien prononce un mot précis. |

## Les outils techniques

| Mot | Ce que ça veut dire |
|---|---|
| **Claude Code** | L'assistant de Claude qui lit, écrit et lance des programmes sur ton ordinateur. C'est lui qui monte. |
| **Claude Max** | L'abonnement Claude payant qui donne assez d'usage pour monter des vidéos. |
| **Terminal** | Fenêtre où l'on tape des commandes texte. Sur Mac : application « Terminal ». |
| **Commande** | Une ligne tapée dans le terminal, par exemple `claude` pour lancer Claude Code. |
| **Dépôt (repo)** | Un dossier de code partagé sur GitHub. Celui-ci s'appelle `scalai-montage-ia`. |
| **GitHub** | Site qui héberge les dépôts de code. |
| **Git** | Outil qui garde l'historique des fichiers d'un dépôt. |
| **Cloner** | Télécharger un dépôt GitHub sur ton ordinateur. |
| **Commit / push** | Enregistrer une modification (commit) puis l'envoyer sur GitHub (push). Claude s'en charge. |
| **Local** | Le travail se fait sur ton ordinateur. |
| **Cloud** | Le travail se fait sur un ordinateur distant d'Anthropic, depuis claude.ai/code. |
| **Clé API** | Un mot de passe qui donne à Claude accès à un service payant, comme ElevenLabs. Il reste secret. |
| **`.env`** | Fichier caché où tu ranges tes clés API. Il ne part jamais sur GitHub. |
| **Pipeline** | La suite de programmes qui fait le montage, étape par étape. |
| **ffmpeg** | Programme gratuit qui découpe, assemble et encode les vidéos. Le pipeline l'utilise partout. |
| **Python** | Langage dans lequel le pipeline est écrit. |
| **Node / npm** | Outils nécessaires pour faire tourner Remotion. |
| **Environnement virtuel (`.venv`)** | Dossier qui contient les bibliothèques Python du dépôt, à part du reste de ton ordinateur. |
| **Script** (technique) | Un petit programme, par exemple `scripts/installer.sh`. À ne pas confondre avec le script lu par Lucien. |
| **ElevenLabs Scribe** | Service en ligne qui fait la transcription. Rapide et précis. |
| **faster-whisper** | Outil de transcription gratuit qui tourne sur ton ordinateur. Plus lent. |
| **Fal.ai** | Service en ligne qui génère des images et des vidéos par IA. |
| **OpenRouter** | Service qui donne accès à plusieurs modèles d'IA. Il aide à choisir visage ou écran. |
| **Epidemic Sound** | Bibliothèque payante de musiques et de bruitages. Celle de Lucien est à son nom. |
| **JSON** | Format de fichier texte qui range des réglages. Exemple : `brief.json`, `montage.json`. |
| **`montage.json`** | Le plan du montage : chaque morceau, sa source, visage ou écran. Claude le modifie, puis relance le rendu. |
