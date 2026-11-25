import React from 'react';
import {AbsoluteFill, CalculateMetadataFunction, Sequence} from '../../shared/rt';
import {Plate} from '../../shared/Plate';
import {SfxTrack, SfxCue} from '../../shared/Sfx';
import {OccView, SANS, SERIF, SC_K, S_K} from '../01-sous-titres-cinetiques/index';
import type {Line, Occ, W} from '../01-sous-titres-cinetiques/data';

// Sous-titres cinétiques de 01 posés sur la vidéo de Lucien.
// Les temps (start, end, t de chaque mot) sont en secondes de la vidéo de Lucien.
// Chaque occurrence se place à start x 30, sans fond neutre entre deux occurrences.
const FPS = 30;
const MAX_W = 1800; // au-delà, la ligne passe sur deux lignes comme dans 01
const LINE_GAP = 140 / 80; // écart de ligne de base relevé dans 01 (832 -> 972 à 80 px), proportionnel à la taille

export type Props = {occs: Occ[]; durationInFrames: number; showPlate?: boolean};

// Mesure de largeur par canvas, avec les polices et facteurs de 01.
let ctx: CanvasRenderingContext2D | null = null;
const wordWidth = (w: W, size: number) => {
  if (typeof document === 'undefined') return 0;
  ctx = ctx ?? document.createElement('canvas').getContext('2d');
  if (!ctx) return 0;
  const kind = w[2] ?? 'w';
  if (kind === 'sc' || kind === 's') {
    const fs = size * (kind === 'sc' ? SC_K : S_K);
    ctx.font = `italic 400 ${fs}px ${SERIF}`;
    const ls = kind === 'sc' ? 0.076 * fs * w[1].length : 0;
    return ctx.measureText(w[1]).width + ls;
  }
  ctx.font = `700 ${size}px ${SANS}`;
  return ctx.measureText(w[1]).width;
};
const lineWidth = (words: W[], size: number) =>
  words.reduce((acc, w, j) => acc + wordWidth(w, size) + (j === 0 || w[1].startsWith(',') ? 0 : size * 0.26), 0);

// Une ligne trop large se coupe en deux au point qui équilibre le mieux les deux moitiés.
const wrapLines = (lines: Line[]): Line[] =>
  lines.flatMap((l) => {
    if (l.words.length < 2 || lineWidth(l.words, l.size) <= MAX_W) return [l];
    let best = 1;
    let bestW = Infinity;
    for (let k = 1; k < l.words.length; k++) {
      const m = Math.max(lineWidth(l.words.slice(0, k), l.size), lineWidth(l.words.slice(k), l.size));
      if (m < bestW) {
        bestW = m;
        best = k;
      }
    }
    return [
      {baseline: l.baseline - l.size * LINE_GAP, size: l.size, words: l.words.slice(0, best)},
      {baseline: l.baseline, size: l.size, words: l.words.slice(best)},
    ];
  });

// grave-apparition sur les mots en couleur, un seul son si deux mots arrivent à moins de 0,12 s.
const cuesFor = (occs: Occ[]): SfxCue[] => {
  const frames = occs
    .flatMap((o) => o.lines.flatMap((l) => l.words.filter((w) => w[2] === 'c' || w[2] === 'r' || w[2] === 'sc').map((w) => Math.round(w[0] * FPS))))
    .sort((a, b) => a - b);
  const out: SfxCue[] = [];
  let prev = -100;
  for (const f of frames) {
    if (f - prev > 0.12 * FPS) out.push({frame: f, name: 'grave-apparition'});
    prev = f;
  }
  return out;
};

const SousTitresLucien: React.FC<Props> = ({occs, showPlate = false}) => (
  <AbsoluteFill style={{backgroundColor: 'transparent'}}>
    <Plate show={showPlate} />
    {occs.map((o, i) => {
      const from = Math.round(o.start * FPS);
      // Le mot se cale sur round((t - start) x 30) dans OccView, soit round(t x 30) à une image près.
      return (
        <Sequence key={i} from={from} durationInFrames={Math.max(1, Math.round((o.end - o.start) * FPS))} layout="none">
          <OccView o={{...o, lines: wrapLines(o.lines)}} />
        </Sequence>
      );
    })}
    <SfxTrack cues={cuesFor(occs)} force />
  </AbsoluteFill>
);

export const calculateMetadata: CalculateMetadataFunction<Props> = ({props}) => ({durationInFrames: props.durationInFrames});

const DEFAULT: Props = {
  durationInFrames: 180,
  showPlate: false,
  occs: [
    {start: 0.5, end: 2.8, lines: [{baseline: 956, size: 80, words: [[0.6, 'Tu'], [0.8, 'passes'], [1.0, 'au'], [1.3, 'niveau', 'c'], [1.6, 'supérieur', 'c']]}]},
    {start: 3.2, end: 5.8, lines: [{baseline: 972, size: 80, words: [[3.3, 'Si'], [3.45, 'tu'], [3.6, 'le'], [3.75, 'fais'], [3.9, 'plus'], [4.05, 'de'], [4.2, '3 fois', 'c'], [4.4, 'par'], [4.55, 'semaine,'], [4.9, 'crée'], [5.05, 'un'], [5.2, 'skill', 'c']]}]},
  ],
};

export const meta = {
  id: '01b-sous-titres-lucien',
  durationInFrames: DEFAULT.durationInFrames,
  fps: FPS,
  defaultProps: DEFAULT,
  calculateMetadata,
};
export default SousTitresLucien;

// Signaux calculés depuis les props : le son interne reste actif (force).
export const cuesDynamiques = true;
