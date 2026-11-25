import React from 'react';
import {AbsoluteFill, Sequence, useCurrentFrame, useVideoConfig} from '../../shared/rt';
import {loadFont as inter} from '@remotion/google-fonts/Inter';
import {Plate} from '../../shared/Plate';
import {SfxTrack, SfxCue} from '../../shared/Sfx';
import {OCCS, Occ, W} from './data';
import {DIDOT_L} from '../../shared/localFonts';

export const SANS = inter('normal', {weights: ['700']}).fontFamily;
// Serif de l'original : Didot italique (police système macOS), identifié par recouvrement de formes.
export const SERIF = `Didot, ${DIDOT_L}, serif`; // DidotL : substitut local (Lambda n'a pas Didot)

const FPS = 30;
// Calage du serif : « 1000 » et « Claude » hauts de 129 px et « 1000 » large de 379 px comme l'original.
export const SC_K = 1.8;
export const S_K = 1.66;
export const SC_LS = '0.076em';
const S_DY = -8; // « Claude » en Didot se pose 8 px plus haut dans l'original
const GAP = 0.5; // fond neutre entre deux occurrences non contiguës
export const COL = {w: '#FFFFFF', c: '#0AFAFA', r: '#F81E22', s: '#FFFFFF', sc: '#7AFBF6'};

// Planning : les occurrences contiguës (fin == début suivant) s'enchaînent sans pause.
const plan = (() => {
  let at = 0;
  return OCCS.map((o, i) => {
    if (i > 0 && Math.abs(OCCS[i - 1].end - o.start) > 0.01) at += GAP;
    const from = Math.round(at * FPS);
    const dur = Math.round((o.end - o.start) * FPS);
    at += o.end - o.start;
    return {o, from, dur};
  });
})();
const TOTAL = Math.round(plan[plan.length - 1].from + plan[plan.length - 1].dur);

// Bruitages (SFX-REGLES.md, règle 6) : grave-apparition sur les seuls mots en couleur (cyan, rouge, serif cyan),
// calé sur la première image visible du mot. Mots arrivant à moins de 0,12 s d'écart : un seul son.
const CUES: SfxCue[] = (() => {
  const frames = plan
    .flatMap(({o, from}) =>
      o.lines.flatMap((l) =>
        l.words.filter((w) => w[2] === 'c' || w[2] === 'r' || w[2] === 'sc').map((w) => from + Math.round((w[0] - o.start) * FPS)),
      ),
    )
    .sort((a, b) => a - b);
  const out: SfxCue[] = [];
  let prev = -100;
  for (const f of frames) {
    if (f - prev > 0.12 * FPS) out.push({frame: f, name: 'grave-apparition'});
    prev = f;
  }
  return out;
})();

// Entrée mesurée : montée de 70 px en décroissance exponentielle (x0,87 par image),
// opacité de 0,6 à 1 (x0,75 par image), léger flou résiduel.
const Word: React.FC<{w: W; t0: number; size: number}> = ({w, t0, size}) => {
  const frame = useCurrentFrame();
  const [t, text, kind = 'w'] = w;
  const f = frame - Math.round((t - t0) * FPS);
  const hidden = f < 0;
  const dy = hidden ? 0 : 70 * Math.pow(0.87, f);
  const op = hidden ? 0 : 1 - 0.4 * Math.pow(0.75, f);
  const blur = hidden ? 0 : 2.5 * Math.pow(0.6, f);
  const serif = kind === 's' || kind === 'sc';
  return (
    <span
      style={{
        display: 'inline-block',
        transform: `translateY(${dy + (kind === 's' ? S_DY : 0)}px)`,
        opacity: op,
        filter: blur > 0.2 ? `blur(${blur}px)` : undefined,
        color: COL[kind],
        fontFamily: serif ? SERIF : SANS,
        fontStyle: serif ? 'italic' : 'normal',
        fontWeight: serif ? 400 : 700,
        fontSize: kind === 'sc' ? size * SC_K : kind === 's' ? size * S_K : size,
        lineHeight: `${size * 1.21}px`,
        verticalAlign: 'baseline',
        letterSpacing: kind === 'sc' ? SC_LS : serif ? '0' : '0',
        textShadow:
          kind === 'sc'
            ? '0 0 10px rgba(90,250,245,0.6), 0 0 22px rgba(60,240,235,0.35), 0 4px 14px rgba(0,0,0,0.45)'
            : kind === 'c'
              ? '0 0 12px rgba(10,250,250,0.35), 0 3px 10px rgba(0,0,0,0.5)'
              : '0 3px 10px rgba(0,0,0,0.55), 0 1px 3px rgba(0,0,0,0.35)',
      }}
    >
      {text}
    </span>
  );
};

export const OccView: React.FC<{o: Occ}> = ({o}) => (
  <AbsoluteFill>
    {o.lines.map((l, i) => (
      <div
        key={i}
        style={{
          position: 'absolute',
          left: 0,
          right: 0,
          // Inter : ligne de base à 0,969 em sous le haut de la boîte avec line-height 1,21.
          top: l.baseline - l.size * 0.969 - (l.size * 1.21 - l.size * 1.21) / 2,
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'baseline',
          lineHeight: 1.21,
          whiteSpace: 'pre',
        }}
      >
        {l.words.map((w, j) => (
          <span key={j} style={{marginLeft: j === 0 || w[1].startsWith(',') ? 0 : l.size * 0.26}}><Word w={w} t0={o.start} size={l.size} /></span>
        ))}
      </div>
    ))}
  </AbsoluteFill>
);

const SousTitres: React.FC<{showPlate?: boolean}> = ({showPlate = true}) => (
  <AbsoluteFill style={{backgroundColor: 'transparent'}}>
    <Plate show={showPlate} />
    {plan.map(({o, from, dur}, i) => (
      <Sequence key={i} from={from} durationInFrames={dur} layout="none">
        <OccView o={o} />
      </Sequence>
    ))}
    <SfxTrack cues={CUES} />
  </AbsoluteFill>
);

export const meta = {
  id: '01-sous-titres-cinetiques',
  durationInFrames: TOTAL,
  fps: FPS,
  defaultProps: {showPlate: true},
  // Une entrée par occurrence (OCCURRENCES.md), tirée du même planning que l'animation.
  occurrences: plan.map(({o, from, dur}) => ({ref: [o.start, o.end] as [number, number], from, durationInFrames: dur, mode: 'overlay' as const})),
};
export const PLAN = plan;
export default SousTitres;

// Signaux sonores exportés pour la bibliothèque (cloud/cues_globaux.py).
export const cues = CUES;
