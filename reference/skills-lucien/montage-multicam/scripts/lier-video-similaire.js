// Pose la vidéo similaire d'un Short dans YouTube Studio (Chrome de Lucien, extension Claude in Chrome).
// Règle du 11/11/2026 : Studio refuse le navigateur du serveur, la pose se fait ici puis se relit.
// Usage : ouvrir https://studio.youtube.com/video/<id>/edit, attendre 4 s, prendre une capture (sinon
// l'extension vidIQ capte le contexte JS), puis exécuter ce code avec TITRE remplacé par un extrait du titre
// de la vidéo longue. Renvoie "<id> ok", "<id> deja" ou la cause d'échec. Relire ensuite après rechargement.
const TITRE = /__TITRE__/i;
const pause = ms => new Promise(r => setTimeout(r, ms));
let t = null;
for (let i = 0; i < 40 && !t; i++) { await pause(300); t = document.querySelector('#linked-video-editor-link'); }
async function go() {
  if (!t) return 'pas de champ';
  if (TITRE.test(t.innerText)) return 'deja';
  t.click();
  let o = null;
  for (let i = 0; i < 20 && !o; i++) { await pause(300); o = [...document.querySelectorAll('[role=option]')].find(x => TITRE.test(x.innerText || '')); }
  if (!o) return 'option introuvable';
  o.click(); await pause(1200);
  if (!TITRE.test(document.querySelector('#linked-video-editor-link').innerText)) return 'non choisi';
  const s = document.querySelector('ytcp-button#save'); s.click();
  for (let i = 0; i < 30; i++) { await pause(500); if (s.hasAttribute('disabled')) return 'ok'; }
  return 'enregistrement non confirmé';
}
location.pathname.split('/')[2] + ' ' + await go()
