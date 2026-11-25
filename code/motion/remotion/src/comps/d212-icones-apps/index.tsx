import React from 'react';
import {AbsoluteFill, Easing, interpolate, useCurrentFrame} from '../../shared/rt';
import {Plate} from '../../shared/Plate';
import {SfxTrack, SfxCue} from '../../shared/Sfx';

// d212 : deux icônes d'app (tuile blanche à biseau chromé, légère ombre) qui surgissent.
// Réf. 118,8 s : mascotte Claude Code à droite (apparition floue ~10 images).
//      119,73 s : icône Codex à gauche (apparition floue ~14 images).
//      121,7 s : panoramique caméra vers la gauche, les icônes filent hors cadre (~8 images, flou de bougé).
// Géométrie à 120,7 s : tuiles 232 px, centres (393, 465) et (1502, 465).
// Cible : « j'ai déjà Cloud Code, j'ai déjà Codex, est-ce que ce n'est pas la même chose ? »
//   Claude Code sur « Cloud Code » (102,40 s), Codex sur « Codex » (103,10 s), sortie après « chose ? » (104,68 s).
const FPS = 30;
const AT = 102.55;
const DUR = 72;
const IN_CLAUDE = 3;
const IN_CODEX = Math.round((103.1 - AT) * FPS);
const OUT = Math.round((104.7 - AT) * FPS);

const SIZE = 232;
const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

// Tuile d'app à biseau chromé (relevée sur la référence).
export const ChromeTile: React.FC<{size: number; inner?: string; children?: React.ReactNode}> = ({size, inner, children}) => {
  const r = size * 0.23;
  const ring = size * 0.052;
  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        width: size,
        height: size,
        borderRadius: r,
        background:
          'linear-gradient(155deg, #ffffff 0%, #6f6f72 8%, #fafafa 16%, #3c3c3f 27%, #ececee 40%, #8d8d90 52%, #ffffff 64%, #404043 78%, #f4f4f4 90%, #7a7a7d 100%)',
        boxShadow: '0 10px 22px rgba(0,0,0,0.35), 0 2px 5px rgba(0,0,0,0.3), inset 0 0 0 1.5px rgba(40,40,42,0.75)',
      }}
    >
      <div
        style={{
          position: 'absolute',
          inset: ring,
          borderRadius: r - ring * 0.8,
          background: inner ?? 'linear-gradient(180deg, #fbfbfb 0%, #f1f1f2 55%, #e4e4e6 100%)',
          boxShadow:
            'inset 0 0 0 1.5px rgba(30,30,32,0.55), inset 0 3px 5px rgba(255,255,255,0.9), inset 0 -6px 10px rgba(0,0,0,0.10), 0 0 2px rgba(0,0,0,0.4)',
          overflow: 'hidden',
        }}
      >
        {children}
      </div>
    </div>
  );
};

// Mascotte pixel de Claude Code (grille relevée : 10 x 7,5 unités).
const ClaudeMascot: React.FC<{w: number}> = ({w}) => {
  const u = 10;
  const d =
    `M1 0 H9 V1.75 H10 V3.85 H9 V5.6 H9 V7.5 H7.9 V5.6 H7.3 V7.5 H6.2 V5.6 H3.9 V7.5 H2.8 V5.6 H2.1 V7.5 H1 V5.6 V3.85 H0 V1.75 H1 Z`;
  return (
    <svg width={w} height={(w * 7.5) / 10} viewBox={`-0.15 -0.15 ${u + 0.3} 7.8`} style={{overflow: 'visible'}}>
      <defs>
        <linearGradient id="clawd" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#EC8A63" />
          <stop offset="1" stopColor="#D8704A" />
        </linearGradient>
      </defs>
      <path d={d} fill="url(#clawd)" stroke="#6a2e1a" strokeWidth={0.14} strokeLinejoin="round" />
      <path d="M1.1 0.12 H8.9" stroke="rgba(255,220,200,0.7)" strokeWidth={0.12} strokeLinecap="round" />
      <rect x={1.95} y={1.9} width={0.95} height={0.95} fill="#111" rx={0.08} />
      <rect x={7.1} y={1.9} width={0.95} height={0.95} fill="#111" rx={0.08} />
    </svg>
  );
};

// Icône Codex : nuage bleu à 8 lobes, dégradé violet -> bleu, invite « >_ » blanche.
const CodexCloud: React.FC<{w: number}> = ({w}) => {
  const lobes = 8;
  const R = 36;
  const r = 15.5;
  const pts: string[] = [];
  let d = '';
  for (let i = 0; i < lobes; i++) {
    const a0 = (i / lobes) * Math.PI * 2 - Math.PI / 2;
    const a1 = ((i + 1) / lobes) * Math.PI * 2 - Math.PI / 2;
    const x0 = 50 + R * Math.cos(a0);
    const y0 = 50 + R * Math.sin(a0);
    const x1 = 50 + R * Math.cos(a1);
    const y1 = 50 + R * Math.sin(a1);
    if (i === 0) d += `M${x0.toFixed(2)} ${y0.toFixed(2)} `;
    d += `A${r} ${r} 0 0 1 ${x1.toFixed(2)} ${y1.toFixed(2)} `;
    pts.push(`${x0},${y0}`);
  }
  d += 'Z';
  return (
    <svg width={w} height={w} viewBox="0 0 100 100" style={{overflow: 'visible'}}>
      <defs>
        <linearGradient id="codexG" x1="0.3" y1="0" x2="0.6" y2="1">
          <stop offset="0" stopColor="#D7A6F2" />
          <stop offset="0.28" stopColor="#7D72F6" />
          <stop offset="0.55" stopColor="#3F4CF6" />
          <stop offset="1" stopColor="#2A2BEA" />
        </linearGradient>
        <radialGradient id="codexH" cx="0.35" cy="0.25" r="0.5">
          <stop offset="0" stopColor="rgba(255,255,255,0.45)" />
          <stop offset="1" stopColor="rgba(255,255,255,0)" />
        </radialGradient>
      </defs>
      <path d={d} fill="url(#codexG)" stroke="#2322b8" strokeWidth={1} />
      <path d={d} fill="url(#codexH)" />
      <path d="M31 40 L41 50 L31 60" fill="none" stroke="#fff" strokeWidth={5.2} strokeLinecap="round" strokeLinejoin="round" />
      <path d="M50 61 H67" fill="none" stroke="#fff" strokeWidth={5.2} strokeLinecap="round" />
    </svg>
  );
};

const Appear: React.FC<{start: number; len: number; cx: number; cy: number; children: React.ReactNode}> = ({start, len, cx, cy, children}) => {
  const f = useCurrentFrame();
  const p = interpolate(f, [start, start + len], [0, 1], {...clamp, easing: Easing.out(Easing.cubic)});
  if (f < start) return null;
  const s = 1.05 - 0.05 * p;
  return (
    <div
      style={{
        position: 'absolute',
        left: cx - SIZE / 2,
        top: cy - SIZE / 2,
        width: SIZE,
        height: SIZE,
        opacity: p,
        transform: `scale(${s})`,
        filter: p < 1 ? `blur(${((1 - p) * 16).toFixed(2)}px)` : undefined,
      }}
    >
      {children}
    </div>
  );
};

const Apps: React.FC<{showPlate?: boolean}> = ({showPlate = true}) => {
  const f = useCurrentFrame();
  const o = interpolate(f, [OUT, OUT + 7], [0, 1], {...clamp, easing: Easing.in(Easing.cubic)});
  const dx = -2100 * o;
  const mb = Math.sin(Math.min(o, 1) * Math.PI) * 60 + (o > 0 ? 8 : 0);
  return (
    <AbsoluteFill style={{overflow: 'hidden'}}>
      <Plate show={showPlate} />
      <svg width={0} height={0} style={{position: 'absolute'}}>
        <filter id="d212mb" x="-50%" y="-10%" width="200%" height="120%">
          <feGaussianBlur stdDeviation={`${mb.toFixed(1)} 0`} />
        </filter>
      </svg>
      <AbsoluteFill style={{transform: `translateX(${dx}px)`, filter: o > 0 ? 'url(#d212mb)' : undefined}}>
        <Appear start={IN_CLAUDE} len={10} cx={1502} cy={465}>
          <ChromeTile size={SIZE}>
            <div style={{position: 'absolute', left: (SIZE - 2 * SIZE * 0.052 - 144) / 2, top: 56}}>
              <ClaudeMascot w={144} />
            </div>
          </ChromeTile>
        </Appear>
        <Appear start={IN_CODEX} len={14} cx={393} cy={465}>
          <ChromeTile size={SIZE}>
            <div style={{position: 'absolute', left: (SIZE - 2 * SIZE * 0.052 - 150) / 2, top: (SIZE - 2 * SIZE * 0.052 - 150) / 2}}>
              <CodexCloud w={150} />
            </div>
          </ChromeTile>
        </Appear>
      </AbsoluteFill>
      <SfxTrack
        cues={cuesExportees}
      />
    </AbsoluteFill>
  );
};

export const meta = {
  id: 'd212-icones-apps',
  fps: FPS,
  durationInFrames: DUR,
  defaultProps: {showPlate: true},
  occurrences: [{ref: [118.5, 121.95] as [number, number], at: AT, from: 0, durationInFrames: DUR, mode: 'plein' as const}],
};
export default Apps;

// Signaux sonores exportés pour la bibliothèque (cloud/cues_globaux.py).
const cuesExportees: SfxCue[] = [
          {frame: IN_CLAUDE + 1, name: 'grave-apparition'},
          {frame: IN_CODEX + 1, name: 'grave-apparition'},
          {frame: OUT, name: 'whoosh-transition'},
        ];
export const cues = cuesExportees;
