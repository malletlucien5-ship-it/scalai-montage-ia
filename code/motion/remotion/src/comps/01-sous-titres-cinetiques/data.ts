// Occurrences relevées sur ref/ref.mp4 (temps en secondes de la référence).
// t = première image où le mot est visible, relevée à l'image près (détection par différence de luminance
// puis contrôle sur tuiles numérotées). Couleurs : w blanc, c cyan, r rouge, s serif blanc, sc serif cyan.
// Chaque ligne française tient dans la largeur de la ligne anglaise, à la même taille.
export type W = [number, string, ('w' | 'c' | 'r' | 's' | 'sc')?];
export type Line = {baseline: number; size: number; words: W[]};
export type Occ = {start: number; end: number; lines: Line[]};

export const OCCS: Occ[] = [
  {start: 0, end: 3.3, lines: [
    {baseline: 763, size: 99, words: [[0.133, "J'ai"], [0.367, 'passé']]},
    {baseline: 923, size: 101, words: [[1.034, '1000', 'sc'], [1.535, 'heures'], [2.169, 'dans'], [2.67, 'Claude', 's']]},
  ]},
  {start: 3.3, end: 5.1, lines: [{baseline: 945, size: 126, words: [[3.734, 'Tous'], [4.134, 'les'], [4.501, 'jours']]}]},
  {start: 5.1, end: 6.0, lines: [{baseline: 945, size: 124, words: [[5.267, 'Outils']]}]},
  {start: 6.0, end: 7.2, lines: [{baseline: 945, size: 125, words: [[6.0, 'Processus']]}]},
  {start: 7.2, end: 8.5, lines: [{baseline: 952, size: 101, words: [[7.233, 'Entreprises'], [7.767, 'à millions']]}]},
  {start: 37.367, end: 40.6, lines: [
    {baseline: 832, size: 80, words: [[37.5, 'Tu'], [37.767, 'utilises'], [38.0, 'à peine']]},
    {baseline: 972, size: 80, words: [[38.7, '5 %', 'r'], [38.9, 'de'], [39.1, 'ce'], [39.1, 'que'], [39.3, 'fait'], [39.5, 'Claude']]},
  ]},
  {start: 83.4, end: 85.7, lines: [{baseline: 970, size: 81, words: [[83.433, "L'habitué"], [83.767, 'voit'], [83.934, 'Claude'], [84.101, 'comme'], [84.268, 'un'], [84.434, 'bureau', 'c']]}]},
  {start: 286.9, end: 289.6, lines: [{baseline: 972, size: 80, words: [[287.0, 'Créer', 'c'], [287.368, 'et'], [287.768, 'agir', 'c'], [288.168, 'dans'], [288.867, 'Claude']]}]},
  {start: 374.0, end: 375.9, lines: [{baseline: 970, size: 80, words: [[374.267, 'Je'], [374.434, 'garde'], [374.634, 'tout'], [374.767, 'à', 'c'], [374.934, "l'œil", 'c']]}]},
  {start: 377.9, end: 379.9, lines: [{baseline: 970, size: 80, words: [[377.95, 'Ajoute'], [378.25, 'Claude'], [378.517, 'in'], [378.818, 'Chrome', 'c']]}]},
  {start: 452.5, end: 454.6, lines: [{baseline: 956, size: 80, words: [[452.634, 'Garde-les'], [452.634, 'en'], [452.634, 'skills', 'c']]}]},
  {start: 469.0, end: 471.6, lines: [
    {baseline: 832, size: 80, words: [[469.067, 'Si'], [469.2, 'je'], [469.334, 'le'], [469.467, 'fais'], [469.601, 'plus'], [469.734, 'de'], [469.8, '3x', 'c'], [470.017, 'par', 'c'], [470.083, 'semaine', 'c'], [470.083, ',']]},
    {baseline: 983, size: 80, words: [[471.002, 'autant'], [471.002, 'en'], [471.002, 'faire'], [471.002, 'un'], [471.002, 'skill', 'c']]},
  ]},
  {start: 610.0, end: 615.5, lines: [{baseline: 1000, size: 80, words: [[610.4, 'Tu'], [610.634, 'es'], [610.868, 'dans les'], [611.101, '0,04 %', 'c'], [613.003, 'des'], [613.337, 'gens']]}]},
  {start: 645.0, end: 647.0, lines: [{baseline: 956, size: 80, words: [[645.9, 'Je'], [645.9, 'les'], [645.9, 'trouve'], [645.9, 'jetables', 'r']]}]},
  {start: 775.0, end: 777.0, lines: [{baseline: 956, size: 80, words: [[775.4, "C'est"], [775.4, 'ton'], [775.4, 'orchestrateur', 'c']]}]},
  {start: 851.0, end: 852.9, lines: [{baseline: 956, size: 80, words: [[851.3, 'Moi,'], [851.701, 'humain', 'c'], [851.901, 'sur', 'c'], [852.001, 'la', 'c'], [852.101, 'boucle', 'c']]}]},
  {start: 860.0, end: 861.9, lines: [{baseline: 956, size: 80, words: [[860.47, 'TOI', 'c'], [860.47, 'aussi,'], [860.47, 'tu'], [860.47, 'peux']]}]},
];
