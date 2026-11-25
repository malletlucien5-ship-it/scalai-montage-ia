import React from 'react';
import {SfxTrack, SfxCue} from '../../shared/Sfx';
import {AbsoluteFill, Easing, Img, interpolate, staticFile, useCurrentFrame} from '../../shared/rt';
import {INTER} from '../../shared/fonts';

// Réf 627.56 à 635.53 s. Speaker en carte à gauche, triangle Agent / APIs / Systèmes.
export const meta = {
  id: '38-graphe-agent',
  durationInFrames: 239,
  fps: 30,
  occurrences: [{ref: [627.56, 635.53] as [number, number], from: 0, durationInFrames: 239, mode: 'overlay' as const}],
};

const FPS = 30;
const ease = Easing.out(Easing.cubic);
const ramp = (t: number, a: number, b: number, e = ease) =>
  interpolate(t, [a, b], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: e});

const R = 72;
const N = {
  agent: {x: 1350, y: 325, label: 'Agent'},
  sys: {x: 1570, y: 708, label: 'Systèmes'},
  api: {x: 1128, y: 708, label: 'APIs'},
};

type P = {x: number; y: number};
// segment d'un bord de cercle à l'autre
const seg = (a: P, b: P, gapA = R + 2, gapB = R + 4) => {
  const dx = b.x - a.x;
  const dy = b.y - a.y;
  const L = Math.hypot(dx, dy);
  const ux = dx / L;
  const uy = dy / L;
  return {x1: a.x + ux * gapA, y1: a.y + uy * gapA, x2: b.x - ux * gapB, y2: b.y - uy * gapB, ux, uy};
};

const EDGES = [
  {s: seg(N.agent, N.sys), t0: 1.0, t1: 1.5},
  {s: seg(N.sys, N.api), t0: 2.75, t1: 3.3},
  {s: seg(N.api, N.agent), t0: 4.45, t1: 4.8},
];
const NODE_T = [{k: 'agent', t: -0.05}, {k: 'sys', t: 1.62}, {k: 'api', t: 3.38}] as const;

// masque : tout opaque sauf la carte speaker (rectangle arrondi)
const HOLE = `url("data:image/svg+xml;utf8,${encodeURIComponent(
  '<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080"><path fill-rule="evenodd" fill="black" d="M0 0H1920V1080H0Z M156 204H722A20 20 0 0 1 742 224V838A20 20 0 0 1 722 858H156A20 20 0 0 1 136 838V224A20 20 0 0 1 156 204Z"/></svg>'
)}")`;

const Node: React.FC<{p: P & {label: string}; a: number}> = ({p, a}) => (
  <div
    style={{
      position: 'absolute',
      left: p.x - R,
      top: p.y - R,
      width: R * 2,
      height: R * 2,
      borderRadius: R,
      boxSizing: 'border-box',
      background: 'radial-gradient(circle at 50% 30%, #25398a 0%, #172a70 35%, #0c1640 75%, #0a1234 100%)',
      border: '2.5px solid #4553a0',
      boxShadow: '0 0 26px rgba(50,90,255,0.55), 0 0 60px rgba(40,70,220,0.25), inset 0 0 18px rgba(0,0,0,0.35)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      fontFamily: INTER,
      fontWeight: 700,
      fontSize: p.label.length > 6 ? 29 : 32,
      letterSpacing: -0.3,
      color: '#e6efff',
      textShadow: '0 0 10px rgba(160,190,255,0.55)',
      opacity: a,
      transform: `scale(${0.85 + 0.15 * a})`,
    }}
  >
    {p.label}
  </div>
);

// bruitages calés sur les images où chaque élément devient visible (SFX-REGLES.md)
const CUES: SfxCue[] = [
  {frame: 0, name: 'whoosh-transition'}, // carte speaker et plein écran
  {frame: 4, name: 'grave-apparition'}, // nœud Agent
  {frame: 51, name: 'grave-apparition'}, // nœud Systèmes
  {frame: 104, name: 'grave-apparition'}, // nœud APIs
];

const Comp: React.FC<{showPlate?: boolean}> = ({showPlate = true}) => {
  const f = useCurrentFrame();
  const t = f / FPS;
  const glow = ramp(t, 0, 0.6);

  // carte speaker de l'original : 606 x 654 px en (136, 204), coins 20 px. Le rush de Lucien se pose dessous au montage.
  const CARD = {x: 136, y: 204, w: 606, h: 654};

  return (
    <AbsoluteFill>
      <AbsoluteFill
        style={{
          background: '#00030b',
          // trou transparent à l'emplacement de la carte en rendu alpha
          WebkitMaskImage: showPlate ? undefined : HOLE,
          maskImage: showPlate ? undefined : HOLE,
        }}
      >
      <AbsoluteFill
        style={{
          background:
            'radial-gradient(ellipse 620px 560px at 1350px 560px, rgba(2,30,70,0.95) 0%, rgba(1,20,48,0.7) 35%, rgba(0,8,22,0.4) 70%, rgba(0,3,11,0) 100%)',
          opacity: 0.6 + 0.4 * glow,
        }}
      />
      <div style={{position: 'absolute', left: 0, top: 0, width: 330, height: 1080, background: '#000610'}} />
      </AbsoluteFill>
      <Img
        src={staticFile('38/speaker.jpg')}
        style={{
          position: 'absolute',
          left: CARD.x,
          top: CARD.y,
          width: CARD.w,
          height: CARD.h,
          borderRadius: 20,
          objectFit: 'cover',
          objectPosition: '50% 50%',
          boxShadow: '0 0 0 1.5px rgba(255,255,255,0.4), 0 20px 60px rgba(0,0,0,0.6)',
        }}
      />
      {/* arêtes */}
      <svg width={1920} height={1080} style={{position: 'absolute', left: 0, top: 0}}>
        <defs>
          <filter id="g38" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="3" result="b" />
            <feMerge>
              <feMergeNode in="b" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>
        {EDGES.map(({s, t0, t1}, i) => {
          const p = ramp(t, t0, t1, Easing.inOut(Easing.quad));
          if (p <= 0) return null;
          const ex = s.x1 + (s.x2 - s.x1) * p;
          const ey = s.y1 + (s.y2 - s.y1) * p;
          // pointe de flèche
          const ah = 17;
          const aw = 8.5;
          const bx = ex - s.ux * ah;
          const by = ey - s.uy * ah;
          const nx = -s.uy;
          const ny = s.ux;
          // impulsions lumineuses après la construction
          const pulses = t > t1 + 0.3 ? [0].map((o) => ((t - t1 - 0.3) / 1.6 + o + i * 0.21) % 1) : [];
          return (
            <g key={i} filter="url(#g38)">
              <line x1={s.x1} y1={s.y1} x2={bx} y2={by} stroke="#4d61bd" strokeWidth={3.2} strokeLinecap="round" />
              <polygon points={`${ex},${ey} ${bx + nx * aw},${by + ny * aw} ${bx - nx * aw},${by - ny * aw}`} fill="#5670dc" />
              {pulses.map((q, k) => (
                <circle
                  key={k}
                  cx={s.x1 + (s.x2 - s.x1) * q}
                  cy={s.y1 + (s.y2 - s.y1) * q}
                  r={4.5}
                  fill="#a8bcff"
                  opacity={Math.sin(q * Math.PI) * ramp(t, t1 + 0.3, t1 + 0.6)}
                />
              ))}
            </g>
          );
        })}
      </svg>
      {NODE_T.map(({k, t: nt}) => (
        <Node key={k} p={N[k]} a={ramp(t, nt, nt + 0.32)} />
      ))}
    <SfxTrack cues={CUES} />
    </AbsoluteFill>
  );
};

export default Comp;

// Signaux sonores exportés pour la bibliothèque (cloud/cues_globaux.py).
export const cues = CUES;
