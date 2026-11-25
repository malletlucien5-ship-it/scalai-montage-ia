# Série de vidéos montées en parallèle (Hetzner, une session Opus par vidéo)

Runbook tiré du run FAQ pré-call v4 du 6 octobre 2026. Quatre vidéos, quatre sessions Opus 5.5, livrées en une soirée.
Branding obligatoire : `Resources/standards/branding-video-faq-precall.md` du vault.
Scripts : `scripts/serie/orchestration/` (infra, manifestes, coupes, rendu) et `scripts/serie/qa/` (contrôles des sessions).

## 1. Préflight sur le Mac, avant tout agent (10 min)

1. Chercher les coupes de Lucien : `ls -lt ~/Desktop/*davinci* ~/Desktop/*timeline*`. Lire chaque export avec `coupes_resolve.py`.
2. Mesurer la fin de chaque plaque : énergie des 0,3 dernières secondes. Une chute vers le silence numérique signale un mot coupé.
3. Pour chaque fin coupée, extraire la suite depuis les rushs avec `queues_rushs.py`.
4. Comparer une image de la plaque à la dernière version livrée. Décider l'étalonnage avant le brief.
5. Vérifier les soldes payants (Fal) avant de promettre un plan IA.
6. Lister les réponses aux questions de transcription ambiguës : chiffres, ordinaux, mots improvisés. Le script de Lucien fait foi.

Critère de sortie : un dossier par vidéo avec plaque, coupes, suite de fin et décision d'étalonnage.

## 2. Infrastructure Hetzner (15 min, scriptée)

- SUPPRIMÉS le 07/10/2026 (atelier et rendu). Atelier : CPX62 (16 vCPU, 32 Go, 0,25 €/h), `cloud-init-atelier.yaml`. Héberge les sessions et rend en local.
- Rendu n°2 : CCX33 (8 cœurs dédiés, 0,27 €/h), `cloud-init-rendu.yaml`. Accès SSH depuis l'atelier seulement.
- Label `service=martell-atelier` : hors du reaper. Suppression à la main après livraison.
- Créer les deux serveurs dès le départ. Le CCX33 a rendu à 23 i/s en 1080p.
- `rendre.sh` choisit la machine libre et exclut `manifeste.json` de la synchronisation.
- Sources et livrables par liens signés : `gen_manifestes.py` (72 h), téléchargement `fetch.py`.
- Dépôt privé cloné avec un jeton passé par stdin, jamais stocké.
- Pas d'Asus : Remotion rend sur CPU. La RTX 4050 est coupée en mode Eco, et le portable n'a que 15 Go de RAM.

## 3. Connexion Claude et sessions

- `claude auth login --claudeai` dans un tmux sur l'atelier. Lucien colle le code dans le chat ou sur Telegram : la branche relogin du bot est en tête, réparée le 06/10.
- Pré-régler `~/.claude.json` (onboarding, confiance des dossiers) et `skipDangerousModePermissionPrompt`.
- Une session par vidéo, et une seule : `claude --remote-control "FAQn v4" -n "FAQn v4" --model claude-opus-5-5 --dangerously-skip-permissions "$(cat CONSIGNE.txt)"` avec `IS_SANDBOX=1`.
- Fermer la fenêtre de nouveauté par `Escape` au premier lancement.
- Écrire dans la consigne initiale toutes les autorisations de Lucien : second serveur, `rendre.sh`, budget. Une session refuse une autorisation relayée par une autre session.

## 4. Brief initial complet

Tout ce qui suit était envoyé au compte-gouttes pendant le run. Le mettre dans la consigne de départ.
- Branding : le standard du vault, en entier.
- Structure : intro sans visage de 10 à 18 s, 2 à 3 animations concrètes liées aux mots, un seul texte fort à la fois.
- Diapositives : idée clé de 3 à 8 mots avec visuel, jamais le transcript, jamais de phrase tronquée, jamais de cadre vide.
- Sous-titres : jamais réduits, coupés au mot ; sur l'écran partagé, dans la moitié de Lucien.
- Coupes de Lucien : appliquées dans la composition, recalées au silence le plus proche (±80 ms, puis ±200 ms).
- Fin : suite des rushs raccordée par corrélation, dernier mot entier + 0,4 s.
- Identité propre à chaque vidéo : fond, palette, motif. Lister les fonds déjà pris.
- Interdits : horloges, boîtes lumineuses en série, clipart, `$`, placeholders, preuves non prononcées.
- Variante A/B éventuelle et 2 à 4 animations en milieu de vidéo.
- Plans IA : demande au coordinateur avec prompt, durée et instant.

## 5. Un seul arrêt de validation par vidéo

- La session dépose `planche.jpg` (12 images aux instants clés), `intro-extrait.mp4` et `plan.md`, puis attend « feu vert ».
- Le coordinateur relit la planche, puis une mosaïque de l'intro faite par `-ss` à des instants explicites. Jamais par un filtre `fps` : ses images tombent à 7,75 + 15,5 × n s.
- Corrections et feu vert dans un seul message. Ensuite, la session rend sans nouvel arrêt.
- Surveillance par `attente-intro.sh` (état et date de `etat.json`), lancée en tâche suivie, jamais par `&`.

## 6. Contrôles automatiques avant chaque dépôt

Chaque session lance ces contrôles sur le rendu final, pas sur des images fixes :
1. Décodage complet, nombre d'images, durées audio = vidéo.
2. Sous-titres mesurés sur l'image : hauteur des capitales, aucune phrase sous 92 % (`faq1_balayer_sous_titres.py`, `faq1_mesurer_sous_titres.py`).
3. Images fantômes : 20 à 30 images du master contre des rendus frais (`faq3_controle_fantomes.py`). Cause connue : clés React identiques entre éléments frères.
4. Centres vides : panneaux tous les 0,1 s, aucun vide de plus de 0,4 s (`faq3_centres_vides.py`).
5. Raccords : énergie de la voix à chaque coupe, aucun clic (`faq2_voix_coupee.py`, `faq4_raccord_voix.py`).
6. Fin : retranscription Whisper des 3 dernières secondes (`faq3_whisper_fin.py`).
7. Sonie : voix -16 LUFS, master -15,9 LUFS.

Le coordinateur refait seulement les points 1 et 6 et regarde une planche de 12 images.

## 7. Économie de tokens pour le coordinateur

- Ne jamais lire `plan.md` en entier. Lire la planche et le message de la session.
- Un message par session et par étape. Une règle utile à toutes part dans les quatre messages d'un coup.
- Ne pas relire un master que les contrôles automatiques valident. Regarder 12 images à des instants explicites.
- Ne pas déboguer l'infrastructure en direct : utiliser les scripts.

## 8. Mesures du run du 6 octobre 2026

- Préparation de l'infrastructure : 30 min. Montage et motion design : 1 h 30 par vidéo, en parallèle.
- Rendu 1440p50 : environ 11 i/s sur CPX62, avec Remotion et 3 sessions actives.
- Rendus perdus : 4 masters sans les coupes de Lucien, 2 à cause de sous-titres réduits, 1 à cause d'images fantômes, 1 à cause de centres vides.
- Coût Hetzner : environ 0,52 €/h pour les deux serveurs.

## 9. Clôture

1. Signer les liens privés 7 jours. Les noter dans `LIVRAISONS-V4.md`.
2. Archiver le code de chaque vidéo : bundle Git, diff non commité, scripts, props. Dépôt sur la Storage Box `jobs/<run>/code/`.
3. Récupérer les scripts de contrôle utiles dans `scripts/serie/qa/`.
4. Supprimer les deux serveurs après accord de Lucien.
