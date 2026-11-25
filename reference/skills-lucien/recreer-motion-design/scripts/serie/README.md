# Scripts de série (run FAQ v4, 06/10/2026)

Mode d'emploi : `references/serie-videos.md`.

## orchestration/
- `coupes_resolve.py` : export Resolve (EDL ou DRT) vers segments à garder et à retirer.
- `queues_rushs.py` : suite d'une plaque depuis les rushs, pour un dernier mot coupé.
- `gen_manifestes.py` : liens GET/PUT signés 72 h par vidéo. `fetch.py` : téléchargement côté serveur.
- `cloud-init-atelier.yaml`, `cloud-init-rendu.yaml` : CPX62 atelier et CCX33 de rendu.
- `rendre.sh` : rendu sur la machine libre, manifestes exclus. `lancer-session.exemple.sh` : session Opus Remote Control.
- `attente-intro.sh` : surveillance de `etat.json` par état et date.

## qa/ (écrits par les sessions, à adapter aux props du projet)
- Sous-titres sur l'image : `faq1_balayer_sous_titres.py`, `faq1_mesurer_sous_titres.py`.
- Images fantômes : `faq3_controle_fantomes.py`, `faq2_compare_master.py`, `faq1_comparer.py`.
- Centres vides : `faq3_centres_vides.py`.
- Coupes et raccords : `faq3_caler_coupes.py`, `faq2_voix_coupee.py`, `faq4_raccord_voix.py`, `faq4_whisper_jonctions.py`.
- Fin et suite : `faq3_whisper_fin.py`, `faq1_caler_queue.py`, `faq3_eq_queue.py`.
- Divers : `faq2_mesure_vsl.py` (mesure de la référence), `faq3_detourer.py` (détourage photo), `faq2_controle_final.py`, `faq1_controles.py`.
