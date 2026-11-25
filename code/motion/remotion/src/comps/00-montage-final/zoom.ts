// Zooms de la couche de base. Même format et même calcul que
// .claude/skills/recreer-motion-design/scripts/zooms.py (filtre ffmpeg de secours).

export type Zoom = {
  at: number; // début de la montée, en secondes sur la timeline
  fin: number; // retour à 1
  facteur: number; // échelle atteinte
  montee?: number; // durée de la montée (0,5 s par défaut)
  descente?: number; // 0 : retour sec à la fin
  point?: [number, number]; // point fixe, en fraction de l'image
  courbe?: number[]; // coefficients du polynôme d'easing
};

// Courbe mesurée sur Dan Martell : E(u) = 3u² - 2u³.
export const COURBE_DAN = [0, 0, 3, -2];
const POINT_DEFAUT: [number, number] = [0.5, 0.45];

const clip = (x: number) => Math.min(1, Math.max(0, x));
const poly = (coefs: number[], u: number) => coefs.reduce((s, c, p) => s + c * u ** p, 0);

// t : temps de la timeline en secondes. Les zooms qui se chevauchent s'additionnent,
// le dernier zoom actif de la liste donne le point, comme dans zooms.py.
export const echelleZoom = (zooms: Zoom[], t: number) => {
  let echelle = 1;
  let point = POINT_DEFAUT;
  for (const z of zooms) {
    if (t < z.at || t > z.fin) continue;
    const courbe = z.courbe ?? COURBE_DAN;
    const montee = Math.max(1e-3, z.montee ?? 0.5);
    let valeur = poly(courbe, clip((t - z.at) / montee));
    const descente = z.descente ?? 0;
    if (descente > 0) valeur *= poly(courbe, clip((z.fin - t) / descente));
    echelle += (z.facteur - 1) * valeur;
    point = z.point ?? POINT_DEFAUT;
  }
  return {echelle, point};
};
