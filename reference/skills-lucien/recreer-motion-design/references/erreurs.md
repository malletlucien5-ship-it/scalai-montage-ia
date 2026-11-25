# Erreurs observées sur Martell Motion

## Orchestration

- Deux coupures de session ont provoqué sept agents dupliqués.
- Le binaire `codex-code-mode-host` manquait au premier lancement.
- Des agents ont été arrêtés avec leur session parente.
- Une reprise a repayé un handoff très long.

Règles : tester le lanceur. Garder les identifiants. Donner un propriétaire par fichier. Écrire un checkpoint court.

## Fidélité

- Des agents ont adapté le contenu pendant la phase de copie.
- Cinq cadres gris sont devenus transparents.
- La scène 37 affichait un `3` et une orbe vide.
- Plusieurs cartes webcam utilisaient un mauvais cadrage.
- Des textes source et des handles restaient visibles.

Règles : séparer copie et personnalisation. Définir l'état de chaque cadre. Comparer trois images par occurrence. Scanner les chaînes interdites.

## Audio

- La clé directe Epidemic renvoyait 401.
- 4 970 aperçus ont été comparés avant le classement des sons.
- Des extraits contaminés par la voix ont servi de candidats.
- Une dépendance Python manquait pendant le traitement.

Règles : tester l'accès. Classer le son avant la recherche. Garder la référence comme étalon. Valider les dépendances.

## Montage

- Whisper fusionnait les amorces avec la dernière prise.
- Lucien a coupé 38 reprises dans Resolve pendant une heure.
- Une fin de mot a été rognée.
- L'extension des fins de mot a rouvert 11 coupes Resolve.

Règles : transcrire portion par portion. Garder la dernière prise. Exécuter `tail_guard`. Limiter toute extension aux portions conservées.

## Cache et rendu

- Les motions ont été rendus après une modification de coupe.
- Un cache global a disparu. Cinquante et un clips ont disparu pendant une reconstruction.
- L'assemblage parallèle décalait environ une image par frontière.
- Le flou `geq` recalculait des millions de pixels sur toute la timeline.
- Plusieurs délais ont été annoncés avant une mesure.

Règles : séparer la composition de son placement. Conserver un `.range` par média. Tester les raccords. Précalculer les masques. Mesurer dix secondes chargées.

## AWS

- Le premier handoff indiquait une mauvaise région.
- Une simulation IAM sans contexte régional concluait à un refus SCP.
- Quatre compositions simultanées dépassaient la concurrence disponible.

Règles : lire la région du projet. Tester un DryRun régional. Rendre une composition à la fois avec une concurrence interne bornée.

## Contrôle qualité

- Le premier final avait une seule image contrôlée.
- Le contrôle de 170 images est arrivé après la livraison.
- Une image intermédiaire a masqué le défaut final de la scène 37.

Règles : contrôler avant l'assemblage. Extraire deux images par placement. Ajouter le début, le milieu et la fin des animations à étapes.

## Chiffres de référence

- 46 motions.
- 85 placements.
- 170 images de contrôle.
- 1 heure de reprise Resolve.
- près de 4 heures perdues sur le flou et les essais jetés.
- au moins 0,4898 $ de coût AWS documenté.
- 148 364 074 tokens comptés dans les sessions Codex ciblées.


## Short vertical depuis un rush DJI 4K (01/10/2026)

| Erreur | Correction |
|---|---|
| `OffthreadVideo` sur l'URL présignée du rush 4K de 2,2 Go : délai `delayRender` dépassé sur Lambda | Le compositeur télécharge le fichier entier. Fabriquer d'abord une plaque légère des seuls plans gardés : workflow `plaque.yml` (`cloud/plaque.py`), lecture du rush par plages d'octets |
| `apt-get update` sur le runner GitHub : 22 min | `plaque.yml` installe ffmpeg sans `update` quand c'est possible |
| `git push origin HEAD:main` depuis la copie locale `martell-motion-cloud` | La copie locale peut être sur une branche de session : deux commits étrangers sont partis sur `main`. Pousser depuis un worktree détaché sur `origin/main` |
| URL présignées dans les props par défaut | Le site Remotion est public sur S3. Props par défaut sans URL (`props.public.json`), URL passées en `--props` au rendu |
| Bruitages au gain de la règle sur une voix à -1,4 dBTP | Saturation à +1,5 dBFS. Gains divisés par 2 sur un Short : pic -1,8 dBFS |
| EDL Resolve d'un rush DJI 50 i/s | Timeline à 25 i/s : timecodes source à convertir à 25 i/s. Contrôler sur un début de mot |
| Dézoomer une prise 16:9 recadrée en 9:16 pleine hauteur | Crop plus large dans le cloud, plaque réduite et posée en bas, haut prolongé par une bande de mur fixe (miroir des rangées vides, même étalonnage) fondue sur 60 px |
| Flash d'intro de Dan copié en valeurs absolues sur un fond plus clair | Calques screen + multiply par case 3×4, résolus sur deux images de la plaque réelle (`edit/flashsolve.py`). À relancer après tout changement de plaque |
| Boucle d'attente d'un run GitHub limitée à 10 min | Elle s'arrête avant la fin et S3 garde l'ancienne plaque. Contrôler `rapport.json` (crop, largeur) avant de rendre |
| Motions inventés pour combler les passages vides d'une recréation | Lucien les a retirés. Une recréation garde seulement les motions de la référence. Proposer un ajout avant de le construire |
| Montée et whoosh sous le flash d'intro de Dan | Chez Dan, la transition est un flash et un clic. Rien d'autre |
| Son du flash d'intro Dan choisi au hasard (clic, whoosh) | Lucien veut le déclencheur photo Epidemic `c2b4d7f8-5d87-4d03-a837-b76a98bb85c8` (Olympus OM-D, 0,57 s, transitoire à +0,086 s), posé 0,09 s avant la coupe |
| Ombre du titre d'intro trop légère | Lucien veut un contour noir marqué : liseré 2 px + portée 6/8 px à 0,8 + halo 22 px |

## Série FAQ pré-call v4 (06/10/2026)

- Les coupes DaVinci de Lucien, exportées pendant le run, ont été oubliées : 4 masters à refaire.
- Le dernier mot était coupé dans la plaque elle-même. Aucun réglage du rendu ne pouvait le rendre.
- Quinze corrections sont parties en cours de route alors qu'elles tenaient dans le brief.
- Des sous-titres réduits jusqu'à 62 % ont passé un contrôle calculé.
- Des diapositives fantômes, dues à des clés React identiques, étaient invisibles sur les images fixes.
- Des cadres de diapositive sont restés vides jusqu'à 6,4 s avant l'arrivée de l'animation.
- Une planche faite par filtre `fps` a fait accuser un défaut qui n'existait pas.
- Une planche déposée venait d'anciennes images fixes.
- Le script de rendu copiait les manifestes privés vers le second serveur.
- Le bot Telegram ignorait les codes de connexion depuis l'arrêt de Clara.
- Les sessions ont refusé une autorisation relayée par une autre session.
- Le solde Fal était vide au moment d'un plan IA.
- Le détour par l'Asus a pris du temps pour un gain nul : Remotion rend sur CPU.

Règles : suivre `references/serie-videos.md`. Faire le préflight avant tout agent. Mettre tout le brief et toutes les autorisations dans la consigne initiale. Mesurer sur le rendu final, jamais sur des images fixes. Construire les planches par instants explicites.

## delayRender au chargement du module : rendu arrêté (15/11/2026)

Rendu motion cabinets : `delayRender('Google Sans')` posé au niveau du module de lot3.tsx. Chaque onglet du rendu déclenchait la minuterie au bout exact de `--timeout`, alors que les images sortaient. Rendu arrêté à l'image 453, débit tombé à 0,35 i/s.
Règle : une police ou un asset se charge dans le composant qui l'utilise (`useState(() => delayRender())` puis `useEffect` → `continueRender`), avec une promesse partagée. Jamais de `delayRender` hors composant. Contrôle exécuté par le code : superposer.py refuse tout delayRender hors useState, useMemo ou useCallback (code 2).
- 15/11/2026, vidéos cabinets : Lucien juge la musique « beaucoup trop forte » à 9,3 LU sous la voix et le b-roll trop présent. Cible : musique 15 LU sous la voix (plage contrôlée −20 à −13 dans `controles/son.py`), visage au moins 55 % du temps, carte texte = sous-titre sur le visage. Script : `placement/alleger.py` du chantier claude-cabinets-guide.
