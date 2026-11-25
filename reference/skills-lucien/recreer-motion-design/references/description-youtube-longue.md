# Description automatique des vidéos longues

Appliquer cette procédure à chaque vidéo longue envoyée en privé sur YouTube par un skill de montage.
L’accord d’envoi privé inclut la rédaction et l’ajout de cette description.
Exclure les Shorts et leur parcours Clipper.

## Préparer depuis le contenu final

Lire la transcription du montage final et ses chapitres.
Réutiliser les fichiers disponibles. Une nouvelle coupe exige les horodatages de cette nouvelle version.
Relever chaque ressource annoncée et chaque appel à réserver un rendez-vous.
Retrouver les ressources dans le catalogue existant. Vérifier leur destination.
Une ressource annoncée sans lien retrouvé doit être signalée à Lucien.
Ne jamais inventer un guide, un téléchargement, un résultat ou une promesse.

Lire les descriptions de trois vidéos longues récentes de Lucien avec l’API YouTube.
Reprendre leurs formulations utiles et les liens suivis existants.
Rédiger directement avec le modèle de la session.

## Vidéos sur les cabinets comptables (règle de Lucien du 17/11/2026)

L'unique appel à l'action est l'opt-in des 7 agents IA : `https://optin.scalai.fr/7-agents-compta`.
Première ligne : « Recevez gratuitement les 7 agents IA dont chaque cabinet comptable a besoin : https://go.scalai.fr/r/<slug>/optin ».
La ligne `cta_links` de position `optin` pointe vers l'opt-in avec les paramètres UTM de la vidéo.
Aucun lien de rendez-vous, d'audit ni de LinkedIn. Le dernier chapitre s'appelle « Conclusion ».
Contrôle : `verifier_cta_cabinets` de `cloud/youtube_upload.py` (main e06dee1) refuse l'envoi sinon.
Exemple : description de MOafsLm9aRo.

## Structure

1. Placer le rendez-vous en première ligne. Adapter le bénéfice au sujet et au CTA prononcé.
2. Placer LinkedIn en deuxième bloc.
3. Ajouter uniquement les ressources annoncées dans cette vidéo.
4. Décrire brièvement le contenu avec ses mots-clés naturels.
5. Ajouter les chapitres issus du montage final lorsque leurs horodatages sont disponibles.
6. Terminer par une invitation à s’abonner.

Limiter la présentation du contenu à environ 80 à 150 mots, hors liens et chapitres.
Éviter les listes de mots-clés, les hashtags génériques et les crédits avant les CTA.
Aucune ligne « toutes mes ressources gratuites » par défaut.

Liens suivis propres à chaque vidéo (règle de Lucien du 10/11/2026) : créer dans `cta_links` (Supabase, worker go-scalai) un `resource_slug` court et lisible par vidéo, par exemple `cabinet-ia`, avec les positions `audit` et `linkedin`.
La destination garde la cible habituelle et ajoute `utm_source=youtube&utm_medium=video&utm_campaign=<slug>-<année>&utm_content=<id YouTube>`.
Liens affichés : `https://go.scalai.fr/r/<slug>/audit` et `https://go.scalai.fr/r/<slug>/linkedin`, jamais de paramètre visible ni d'identifiant dans l'URL affichée.
Tester chaque lien en `curl -I` (HEAD ne compte pas de clic), 302 vers la bonne destination, puis relire la description par l'API après 20 s.

Liens génériques, seulement en repli :

- Rendez-vous : `https://go.scalai.fr/r/youtube/form`.
- LinkedIn : `https://go.scalai.fr/r/youtube/linkedin`.
- Guide OS IA : `https://go.scalai.fr/r/youtube/optin-os-ia-entreprise`, seulement quand la vidéo l’annonce.

Exemple du premier CTA : « Obtiens ta roadmap gratuite pour intégrer l’IA dans ton entreprise ».
Adapter cette phrase au contenu. Garder les offres et les conditions réellement prononcées.

Les chapitres commencent à `0:00`. Utiliser des titres courts et des horaires croissants.
Contrôler les horaires sur la durée finale. Ne jamais reprendre les horaires des rushs.

## Ajouter lors de l’envoi privé

Enregistrer la description UTF-8 dans le dossier du projet : `youtube-description.txt`.
Vérifier le texte contre cette procédure avec Jev avant son envoi.
Relire les résultats incertains avec le modèle de la session.
Si Jev est indisponible, vérifier directement le texte contre cette procédure.

Avec `cloud/youtube_upload.py`, fournir `--description-file CHEMIN/youtube-description.txt`.
Un uploader équivalent reçoit le même texte dans `snippet.description`.
Conserver le statut privé. La description ne déclenche aucune programmation ou publication.

Pour une vidéo déjà envoyée en privé, modifier sa description sans renvoyer le fichier vidéo.
Relire son `snippet` avant modification et préserver les autres champs.
Relire ensuite `snippet.description` et `status.privacyStatus` avec l’API.
Vérifier que la description correspond au fichier et que la vidéo reste privée.
En cas de divergence, reprendre la modification des métadonnées sur le même identifiant vidéo.
Conserver l’identifiant, le fichier et la vérification dans le rapport de livraison.
