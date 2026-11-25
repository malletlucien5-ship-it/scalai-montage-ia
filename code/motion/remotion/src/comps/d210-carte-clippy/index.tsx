import React from 'react';
import {AbsoluteFill, Easing, interpolate, useCurrentFrame} from '../../shared/rt';
import {Plate} from '../../shared/Plate';
import {SfxTrack, SfxCue} from '../../shared/Sfx';

// d210 : carte bleu clair à droite, trombone à yeux sur une feuille jaune lignée (dessin SVG).
// Réf. : apparition 201,13 s (flou + fondu + légère montée, ~12 images), coupe franche 203,70 s.
// Géométrie à 202,0 s (1920x1080) : carte x 1213..1850, y 301..778 (637 x 477), rayon 18, #78D4FB.
// Cible : « C'est un peu comme l'application Paperclip de Microsoft ... bienvenue au club. »
//   apparition sur « Paperclip » (208,76 s), fin après « club » (213,56 s).
const FPS = 30;
const AT = 208.76;
const END = 213.7;
const DUR = Math.round((END - AT) * FPS);
const IN = 12;

const CARD = {x: 1213, y: 301, w: 637, h: 477};

// Feuille jaune gondolée (coordonnées locales de la carte).
const PAPER =
  'M262 168 C330 146 430 136 530 120 C492 185 486 300 446 440 C350 420 220 398 108 380 C150 330 175 250 262 168 Z';

const paperLines = () => {
  const out: string[] = [];
  for (let i = 0; i < 24; i++) {
    const y0 = 150 + i * 13.2;
    // lignes montant vers la droite, légère ondulation qui suit le gondolage
    out.push(`M80 ${y0 + 34} C220 ${y0 + 20} 360 ${y0 - 6} 560 ${y0 - 40}`);
  }
  return out;
};

const WIRE =
  'M258 208 L262 300 Q265 332 289 332 Q313 332 313 300 L318 112 Q321 46 290 44 Q259 44 255 92 L240 342 Q238 394 291 394 Q344 394 346 342 L352 214';

const Clippy: React.FC = () => (
  <svg width={CARD.w} height={CARD.h} viewBox={`0 0 ${CARD.w} ${CARD.h}`} style={{position: 'absolute', inset: 0}}>
    <defs>
      <clipPath id="d210paper">
        <path d={PAPER} />
      </clipPath>
      <linearGradient id="d210paperG" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0" stopColor="#FBF8A6" />
        <stop offset="0.55" stopColor="#F6F29A" />
        <stop offset="1" stopColor="#E9E28A" />
      </linearGradient>
      <linearGradient id="d210wire" x1="0" y1="0" x2="1" y2="0">
        <stop offset="0" stopColor="#6E73AD" />
        <stop offset="0.45" stopColor="#A9AEDF" />
        <stop offset="1" stopColor="#6B70A6" />
      </linearGradient>
      <radialGradient id="d210eye" cx="0.45" cy="0.35" r="0.7">
        <stop offset="0" stopColor="#ffffff" />
        <stop offset="0.7" stopColor="#f1f1f4" />
        <stop offset="1" stopColor="#b9bccc" />
      </radialGradient>
      <filter id="d210soft" x="-20%" y="-20%" width="140%" height="140%">
        <feGaussianBlur stdDeviation="7" />
      </filter>
    </defs>
    {/* feuille */}
    <path d={PAPER} fill="url(#d210paperG)" />
    <g clipPath="url(#d210paper)">
      {paperLines().map((d, i) => (
        <path key={i} d={d} stroke="#8DB2A6" strokeWidth={1.6} fill="none" opacity={0.85} />
      ))}
      <path d="M170 392 C205 330 245 250 300 160" stroke="#E2917F" strokeWidth={1.8} fill="none" />
      <path d="M182 394 C217 332 257 252 312 162" stroke="#E2917F" strokeWidth={1.2} fill="none" opacity={0.7} />
      {/* ombre du trombone sur la feuille */}
      <path d={WIRE} transform="translate(62 36) skewX(-12)" stroke="rgba(70,70,40,0.45)" strokeWidth={13} fill="none" filter="url(#d210soft)" />
    </g>
    <path d={PAPER} fill="none" stroke="rgba(150,140,60,0.35)" strokeWidth={1.2} />
    {/* fil du trombone */}
    <path d={WIRE} stroke="#3C3F67" strokeWidth={15} fill="none" strokeLinecap="round" strokeLinejoin="round" />
    <path d={WIRE} stroke="url(#d210wire)" strokeWidth={11.5} fill="none" strokeLinecap="round" strokeLinejoin="round" />
    <path d={WIRE} transform="translate(-2 -1)" stroke="rgba(235,237,255,0.8)" strokeWidth={3} fill="none" strokeLinecap="round" strokeLinejoin="round" />
    {/* yeux */}
    <ellipse cx={231} cy={142} rx={37} ry={31} fill="url(#d210eye)" stroke="#6d7087" strokeWidth={1.2} />
    <ellipse cx={330} cy={166} rx={39} ry={33} fill="url(#d210eye)" stroke="#6d7087" strokeWidth={1.2} />
    <circle cx={236} cy={143} r={17} fill="#0b0b0d" />
    <circle cx={324} cy={166} r={17.5} fill="#0b0b0d" />
    <circle cx={230} cy={136} r={5} fill="rgba(255,255,255,0.85)" />
    <circle cx={318} cy={159} r={5} fill="rgba(255,255,255,0.85)" />
    {/* sourcils */}
    <path d="M204 106 Q236 80 273 96" stroke="#0e0e10" strokeWidth={9} fill="none" strokeLinecap="round" />
    <path d="M320 114 Q352 100 377 140" stroke="#0e0e10" strokeWidth={9} fill="none" strokeLinecap="round" />
  </svg>
);

const CarteClippy: React.FC<{showPlate?: boolean}> = ({showPlate = true}) => {
  const f = useCurrentFrame();
  const p = interpolate(f, [0, IN], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic)});
  return (
    <AbsoluteFill style={{overflow: 'hidden'}}>
      <Plate show={showPlate} />
      <div
        style={{
          position: 'absolute',
          left: CARD.x,
          top: CARD.y + 20 * (1 - p),
          width: CARD.w,
          height: CARD.h,
          borderRadius: 18,
          background: '#78D4FB',
          overflow: 'hidden',
          opacity: p,
          filter: p < 1 ? `blur(${((1 - p) * 18).toFixed(2)}px)` : undefined,
          boxShadow: '0 12px 30px rgba(0,0,0,0.25)',
        }}
      >
        <Clippy />
      </div>
      <SfxTrack cues={cuesExportees} />
    </AbsoluteFill>
  );
};

export const meta = {
  id: 'd210-carte-clippy',
  fps: FPS,
  durationInFrames: DUR,
  defaultProps: {showPlate: true},
  occurrences: [{ref: [201.13, 203.7] as [number, number], at: AT, from: 0, durationInFrames: DUR, mode: 'plein' as const}],
};
export default CarteClippy;

// Signaux sonores exportés pour la bibliothèque (cloud/cues_globaux.py).
const cuesExportees: SfxCue[] = [{frame: 1, name: 'grave-apparition'}];
export const cues = cuesExportees;
