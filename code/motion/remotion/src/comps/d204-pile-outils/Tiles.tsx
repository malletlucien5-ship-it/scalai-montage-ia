import React from 'react';
import {siOpenai} from 'simple-icons';
import {INTER_L} from '../../shared/localFonts';

// Tuile isométrique : carré arrondi (plan) projeté par scaleY(K) rotate(-45deg).
// Mesures réf. 1920x1080 : tuile 1 = 333 x 176 px (x 793-1126), trait ~13 px dans le plan.
export const S = 262;
export const R = 46;
export const K = 0.529;
export const ST = 15;

export type Face = 'num' | 'openai' | 'grok' | 'handoff' | 'brain';
export type TileLook = {
  chrome: number; // 0 = contour blanc plat (occ. 1), 1 = contour chromé + épaisseur
  lit: number; // lueur bleue (occ. 2)
  purple?: boolean; // tuile 4 : lueur violette
};

const PLANE: React.CSSProperties = {
  position: 'absolute',
  left: 0,
  top: 0,
  width: S,
  height: S,
  transform: `scaleY(${K}) rotate(-45deg)`,
  transformOrigin: '50% 50%',
};

const mix = (a: number[], b: number[], t: number) => a.map((v, i) => Math.round(v + (b[i] - v) * t));
const rgb = (c: number[], a = 1) => `rgba(${c[0]},${c[1]},${c[2]},${a})`;

// Contenu d'une icône, dessiné droit (contre-rotation +45°) : à l'écran il reste droit, écrasé verticalement par K.
const Upright: React.FC<{size: number; dx?: number; dy?: number; children: React.ReactNode}> = ({size, dx = 0, dy = 0, children}) => (
  <div
    style={{
      position: 'absolute',
      left: S / 2 - size / 2,
      top: S / 2 - size / 2,
      width: size,
      height: size,
      transform: `rotate(45deg) translate(${dx}px, ${dy / K}px)`,
    }}
  >
    {children}
  </div>
);

const OpenAI: React.FC<{size: number; color?: string}> = ({size, color = '#0b0d10'}) => (
  <svg width={size} height={size} viewBox="0 0 24 24" style={{display: 'block'}}>
    <path d={siOpenai.path} fill={color} />
  </svg>
);

// Fantôme blanc (Grok Bot) : corps arrondi, deux yeux verticaux.
const Ghost: React.FC<{w: number; eyes?: number; outline?: boolean}> = ({w, eyes = 0, outline}) => (
  <svg width={w} height={w} viewBox="0 0 100 100" style={{display: 'block', overflow: 'visible'}}>
    <path
      d="M8 60 C8 30 30 12 56 12 C80 12 94 30 94 52 C94 74 80 92 56 92 L20 92 C12 92 8 86 8 78 Z"
      fill="#fbfbfb"
      stroke={outline ? '#0b0d10' : 'none'}
      strokeWidth={outline ? 6 : 0}
    />
    <rect x={44 + eyes} y={36} width={13} height={24} rx={6.5} fill="#0b0d10" />
    <rect x={66 + eyes} y={38} width={13} height={24} rx={6.5} fill="#0b0d10" />
  </svg>
);

const Brain: React.FC<{w: number}> = ({w}) => (
  <svg width={w} height={w} viewBox="0 0 100 100" style={{display: 'block'}}>
    <g fill="#0b0d10">
      <circle cx="30" cy="34" r="17" />
      <circle cx="50" cy="26" r="17" />
      <circle cx="70" cy="34" r="17" />
      <circle cx="22" cy="54" r="16" />
      <circle cx="78" cy="54" r="16" />
      <circle cx="34" cy="70" r="17" />
      <circle cx="66" cy="70" r="17" />
      <circle cx="50" cy="52" r="24" />
    </g>
    <g fill="none" stroke="#f4f4f4" strokeWidth="3.4" strokeLinecap="round">
      <path d="M50 16 L50 84" />
      <path d="M22 40 C30 34 36 44 44 38" />
      <path d="M16 58 C24 52 30 62 40 56 C44 54 46 58 46 62" />
      <path d="M28 76 C34 70 40 78 44 72" />
      <path d="M78 40 C70 34 64 44 56 38" />
      <path d="M84 58 C76 52 70 62 60 56 C56 54 54 58 54 62" />
      <path d="M72 76 C66 70 60 78 56 72" />
    </g>
  </svg>
);

const FaceContent: React.FC<{face: Face; n: number; lit: number; frame: number; chrome?: number}> = ({face, n, lit, frame, chrome = 0}) => {
  if (face === 'num') {
    return (
      <div
        style={{
          position: 'absolute',
          inset: 0,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontFamily: INTER_L,
          fontWeight: 800,
          fontSize: 132,
          lineHeight: 1,
          // Chiffre blanc sur la pile plate (réf. 31,3), gris acier sur la pile chromée (réf. 59,5 : #878C90).
          color: rgb(mix(mix([250, 250, 250], [135, 140, 144], chrome), [226, 234, 240], lit)),
          transform: 'rotate(90deg)',
        }}
      >
        {n}
      </div>
    );
  }
  if (face === 'openai') return <Upright size={196} dy={-2}><OpenAI size={196} /></Upright>;
  if (face === 'grok') {
    // Réf. 329.5 : face noire, grand corps blanc (croissant noir en haut à gauche et pointe droite noire), yeux au centre-droit.
    const eyes = 3 * Math.sin(frame / 9);
    return (
      <>
        <div style={{position: 'absolute', inset: 0, background: '#07080a'}} />
        <Upright size={420} dx={-8} dy={22}>
          <svg width={420} height={420} viewBox="0 0 420 420" style={{display: 'block'}}>
            <defs>
              <radialGradient id="gk" cx="0.45" cy="0.55" r="0.55">
                <stop offset="0" stopColor="#ffffff" />
                <stop offset="0.8" stopColor="#f1f2f3" />
                <stop offset="1" stopColor="#c9cdd1" />
              </radialGradient>
            </defs>
            <circle cx={210} cy={210} r={140} fill="url(#gk)" />
            <rect x={200 + eyes} y={140} width={30} height={85} rx={15} fill="#0b0d10" />
            <rect x={260 + eyes} y={144} width={30} height={85} rx={15} fill="#0b0d10" />
          </svg>
        </Upright>
      </>
    );
  }
  if (face === 'handoff') {
    return (
      <>
        <Upright size={100} dx={-66} dy={-24}><OpenAI size={100} /></Upright>
        <Upright size={60} dx={-8} dy={8}>
          <svg width={60} height={60} viewBox="0 0 60 60">
            <path d="M14 6 L14 34 L44 34" fill="none" stroke="#0b0d10" strokeWidth="7" strokeLinejoin="round" />
            <path d="M40 22 L54 34 L40 46 Z" fill="#0b0d10" />
          </svg>
        </Upright>
        <Upright size={116} dx={52} dy={28}><Ghost w={116} outline /></Upright>
      </>
    );
  }
  return <Upright size={196} dy={0}><Brain w={196} /></Upright>;
};

export const Tile: React.FC<{
  cx: number;
  cy: number;
  sc: number;
  n: number;
  face: Face;
  look: TileLook;
  frame: number;
  faceIn?: number; // 0..1 : fondu de la face icône par-dessus la face numérotée
}> = ({cx, cy, sc, n, face, look, frame, faceIn = 1}) => {
  const {chrome, lit} = look;
  const gid = `t${n}`;
  const glowC = look.purple ? [128, 84, 255] : [36, 124, 255];
  const glow =
    lit > 0.01
      ? `drop-shadow(0 0 ${8 * sc}px ${rgb(glowC, Math.min(1, 1.1 * lit))}) drop-shadow(0 0 ${22 * sc}px ${rgb(glowC, Math.min(1, lit))}) drop-shadow(0 0 ${44 * sc}px ${rgb(glowC, 0.7 * lit)})`
      : `drop-shadow(0 0 5px rgba(255,255,255,${0.35 * (1 - chrome)}))`;
  const iconFace = face !== 'num';
  const rim = (w: boolean) => (
    <svg width={S} height={S} style={{position: 'absolute', inset: 0, overflow: 'visible'}}>
      <defs>
        <linearGradient id={`${gid}c${w ? 'w' : 'n'}`} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#ffffff" />
          <stop offset="0.3" stopColor={w ? '#c9ced3' : '#9aa1a8'} />
          <stop offset="0.5" stopColor="#f2f4f6" />
          <stop offset="0.72" stopColor={w ? '#b8bec4' : '#8b9299'} />
          <stop offset="1" stopColor="#ffffff" />
        </linearGradient>
      </defs>
      {/* contour blanc plat (occ. 1) */}
      <rect x={ST / 2} y={ST / 2} width={S - ST} height={S - ST} rx={R - ST / 2} fill="none" stroke="#fbfbfb" strokeWidth={ST} opacity={1 - chrome} />
      {/* contour chromé */}
      <rect x={ST / 2} y={ST / 2} width={S - ST} height={S - ST} rx={R - ST / 2} fill="none" stroke={`url(#${gid}c${w ? 'w' : 'n'})`} strokeWidth={w ? ST + 3 : ST} opacity={chrome} />
      <rect x={ST + 0.5} y={ST + 0.5} width={S - 2 * ST - 1} height={S - 2 * ST - 1} rx={R - ST} fill="none" stroke="#1b2126" strokeWidth={1.6} opacity={chrome * 0.8} />
    </svg>
  );
  const darkFill = (
    <svg width={S} height={S} style={{position: 'absolute', inset: 0}}>
      <defs>
        <linearGradient id={`${gid}f`} x1="0" y1="1" x2="1" y2="0">
          {/* Losange inactif sombre teinté teal (réf. 31,3 : #053345 ; réf. 59,5 : #0B212C), jamais bleu vif. */}
          <stop offset="0" stopColor={rgb(mix(mix([2, 30, 42], [3, 15, 20], chrome), [8, 22, 28], lit))} />
          <stop offset="1" stopColor={rgb(mix(mix([7, 54, 70], [9, 28, 35], chrome), [22, 44, 52], lit))} />
        </linearGradient>
      </defs>
      <rect x={ST / 2} y={ST / 2} width={S - ST} height={S - ST} rx={R - ST / 2} fill={`url(#${gid}f)`} fillOpacity={0.9 + 0.1 * chrome} />
    </svg>
  );
  const whiteFill = (
    <svg width={S} height={S} style={{position: 'absolute', inset: 0}}>
      <defs>
        <radialGradient id={`${gid}w`} cx="0.45" cy="0.45" r="0.75">
          <stop offset="0" stopColor="#ffffff" />
          <stop offset="0.7" stopColor="#f1f2f3" />
          <stop offset="1" stopColor="#cfd3d7" />
        </radialGradient>
      </defs>
      <rect x={ST / 2} y={ST / 2} width={S - ST} height={S - ST} rx={R - ST / 2} fill={`url(#${gid}w)`} />
    </svg>
  );
  const thick = 6 * Math.max(chrome, iconFace ? faceIn : 0);
  return (
    <div style={{position: 'absolute', left: cx - S / 2, top: cy - S / 2, width: S, height: S, transform: `scale(${sc})`, filter: glow}}>
      {/* épaisseur de la dalle */}
      {thick > 0.5 ? (
        <div style={{position: 'absolute', inset: 0, transform: `translateY(${thick}px)`}}>
          <div style={PLANE}>
            <svg width={S} height={S} style={{position: 'absolute', inset: 0}}>
              <defs>
                <linearGradient id={`${gid}s`} x1="0" y1="0" x2="1" y2="1">
                  <stop offset="0" stopColor="#5d646b" />
                  <stop offset="0.5" stopColor="#c3c8cd" />
                  <stop offset="1" stopColor="#6c737a" />
                </linearGradient>
              </defs>
              <rect x={0} y={0} width={S} height={S} rx={R} fill={`url(#${gid}s)`} />
            </svg>
          </div>
        </div>
      ) : null}
      <div style={PLANE}>
        <div style={{position: 'absolute', inset: 0, borderRadius: R, overflow: 'hidden'}}>
          {darkFill}
          <FaceContent face="num" n={n} lit={lit} frame={frame} chrome={chrome} />
          {iconFace ? (
            <div style={{position: 'absolute', inset: 0, opacity: faceIn}}>
              {whiteFill}
              <FaceContent face={face} n={n} lit={0} frame={frame} />
            </div>
          ) : null}
        </div>
        {rim(false)}
        {iconFace ? <div style={{position: 'absolute', inset: 0, opacity: faceIn}}>{rim(true)}</div> : null}
      </div>
    </div>
  );
};
