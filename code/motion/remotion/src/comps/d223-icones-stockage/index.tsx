import React from 'react';
import {AbsoluteFill, Easing, interpolate, useCurrentFrame} from '../../shared/rt';
import {siNotion} from 'simple-icons';
import {SfxTrack, SfxCue} from '../../shared/Sfx';

// Référence 1088.0-1090.3 s : fond noir traversé d'un faisceau bleu-sarcelle en diagonale,
// tuiles d'app 3D (face blanche, biseau chromé) qui arrivent une à une, floues et sombres
// puis nettes : Obsidian, Google Drive, Notion. Chaque tuile sur son mot.
const FPS = 30;
const AT = 1154.08; // « Obsidian »
const DUR = Math.round((1156.45 - AT) * FPS); // jusqu'à la fin de « Notion » (1156.38)

// Arrivées locales (s) : Obsidian 1154.08, Google 1154.86, Notion 1155.78.
const ICONS: {t: number; cx: number; kind: 'obsidian' | 'drive' | 'notion'}[] = [
  {t: 0, cx: 545, kind: 'obsidian'},
  {t: 1154.86 - AT, cx: 963, kind: 'drive'},
  {t: 1155.78 - AT, cx: 1377, kind: 'notion'},
];
const CY = 539;
const TILE_W = 326;
const TILE_H = 320;

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

// Faisceau : bande courbe floue (centres mesurés : y0 x1080, y300 x1130, y760 x930, y900 x840,
// y1075 x700 à la fin) ; le bas glisse vers la droite d'environ 120 px et le haut s'assombrit.
const Beam: React.FC<{t: number}> = ({t}) => {
  const p = interpolate(t, [0, 2.3], [0, 1], clamp);
  const sh = (k: number) => -120 * k * (1 - p);
  const d = `M1060 -150 C1140 150 1130 330 1040 520 S${840 + sh(0.6)} ${900} ${650 + sh(1)} 1250`;
  const top = interpolate(p, [0, 1], [0, 1]);
  const mix = (a: number[], b: number[]) => `rgb(${a.map((v, i) => Math.round(v + (b[i] - v) * top)).join(',')})`;
  return (
    <svg width={1920} height={1080} style={{position: 'absolute', inset: 0}}>
      <defs>
        <linearGradient id="d223beam" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="0" y2="1080">
          <stop offset="0%" stopColor={mix([13, 96, 122], [5, 60, 86])} />
          <stop offset="35%" stopColor={mix([8, 80, 104], [5, 68, 92])} />
          <stop offset="70%" stopColor="#055a7c" />
          <stop offset="100%" stopColor="#134688" />
        </linearGradient>
        <filter id="d223blur" filterUnits="userSpaceOnUse" x={-800} y={-800} width={3520} height={2680}>
          <feGaussianBlur stdDeviation={90} />
        </filter>
      </defs>
      <path d={d} fill="none" stroke="url(#d223beam)" strokeWidth={470} filter="url(#d223blur)" />
    </svg>
  );
};

const ObsidianLogo: React.FC = () => (
  <svg width={172} height={221} viewBox="195 155 350 450">
    <defs>
      <linearGradient id="d223oA" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0%" stopColor="#d3c6fa" />
        <stop offset="100%" stopColor="#a78bf1" />
      </linearGradient>
      <linearGradient id="d223oB" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stopColor="#8456ee" />
        <stop offset="100%" stopColor="#a888f3" />
      </linearGradient>
      <linearGradient id="d223oC" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0%" stopColor="#6a35de" />
        <stop offset="100%" stopColor="#8250e6" />
      </linearGradient>
      <linearGradient id="d223oD" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0%" stopColor="#5b28c4" />
        <stop offset="100%" stopColor="#7f4be4" />
      </linearGradient>
    </defs>
    {/* A : facette haute, claire */}
    <path d="M262 262 L368 164 Q386 156 400 172 Q368 250 366 330 Q368 380 380 420 Q352 418 330 428 Q300 390 245 345 Z" fill="url(#d223oA)" />
    {/* B : facette droite */}
    <path d="M400 172 Q412 178 478 262 Q505 330 540 438 Q536 462 495 506 Q470 450 380 420 Q368 380 366 330 Q368 250 400 172 Z" fill="url(#d223oB)" />
    {/* C : facette gauche basse */}
    <path d="M245 345 Q300 390 330 428 Q312 500 322 560 Q300 572 290 566 Q228 505 200 468 Q196 455 205 440 Z" fill="url(#d223oC)" />
    {/* D : facette basse, profonde */}
    <path d="M330 428 Q352 418 380 420 Q470 450 495 506 Q482 540 472 590 Q466 600 450 598 Q380 580 322 560 Q312 500 330 428 Z" fill="url(#d223oD)" />
  </svg>
);

const DriveLogo: React.FC = () => (
  <svg width={204} height={182} viewBox="0 0 87.3 78">
    <path d="M6.6 66.85l3.85 6.65c.8 1.4 1.95 2.5 3.3 3.3L27.5 53H0c0 1.55.4 3.1 1.2 4.5z" fill="#0066DA" />
    <path d="M43.65 25L29.9 1.2c-1.35.8-2.5 1.9-3.3 3.3L1.2 48.5A9.06 9.06 0 0 0 0 53h27.5z" fill="#00AC47" />
    <path d="M73.55 76.8c1.35-.8 2.5-1.9 3.3-3.3l1.6-2.75 7.65-13.25c.8-1.4 1.2-2.95 1.2-4.5H59.8l5.85 11.5z" fill="#EA4335" />
    <path d="M43.65 25L57.4 1.2C56.05.4 54.5 0 52.9 0H34.4c-1.6 0-3.15.45-4.5 1.2z" fill="#00832D" />
    <path d="M59.8 53H27.5L13.75 76.8c1.35.8 2.9 1.2 4.5 1.2h50.8c1.6 0 3.15-.45 4.5-1.2z" fill="#2684FC" />
    <path d="M73.4 26.5L60.7 4.5c-.8-1.4-1.95-2.5-3.3-3.3L43.65 25 59.8 53h27.45c0-1.55-.4-3.1-1.2-4.5z" fill="#FFBA00" />
  </svg>
);

const NotionLogo: React.FC = () => (
  <svg width={178} height={178} viewBox="0 0 24 24">
    <path d={siNotion.path} fill="#0b0b0b" />
  </svg>
);

// Tuile 3D : biseau chromé (anneaux clairs et sombres) et face blanche légèrement ombrée.
const Tile: React.FC<{children: React.ReactNode}> = ({children}) => {
  const ring = (inset: number, bg: string, r: number) => (
    <div style={{position: 'absolute', inset, borderRadius: r, background: bg}} />
  );
  return (
    <div style={{position: 'relative', width: TILE_W, height: TILE_H}}>
      {ring(0, 'linear-gradient(160deg, #ffffff 0%, #7d7d7d 18%, #f4f4f4 34%, #4e4e4e 52%, #fbfbfb 68%, #7a7a7a 84%, #ffffff 100%)', 64)}
      {ring(4, 'linear-gradient(180deg, #2f2f2f 0%, #0c0c0c 50%, #3a3a3a 100%)', 60)}
      {ring(9, 'linear-gradient(200deg, #ffffff 0%, #9f9f9f 25%, #ffffff 45%, #858585 70%, #ffffff 100%)', 55)}
      {ring(15, 'linear-gradient(180deg, #5a5a5a 0%, #1a1a1a 100%)', 49)}
      {ring(18, 'linear-gradient(170deg, #ffffff 0%, #bdbdbd 50%, #f7f7f7 100%)', 46)}
      <div
        style={{
          position: 'absolute',
          inset: 21,
          borderRadius: 43,
          background: 'radial-gradient(ellipse 80% 70% at 50% 42%, #f6f6f6 0%, #eeeeee 60%, #dedede 100%)',
          boxShadow: 'inset 0 0 10px rgba(0,0,0,0.22), inset 0 -4px 8px rgba(0,0,0,0.08)',
        }}
      />
      <div
        style={{
          position: 'absolute',
          inset: 0,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          filter: 'drop-shadow(0 3px 2px rgba(0,0,0,0.28)) drop-shadow(0 1px 0 rgba(255,255,255,0.6))',
        }}
      >
        {children}
      </div>
    </div>
  );
};

const Scene: React.FC = () => {
  const f = useCurrentFrame();
  const t = f / FPS;
  return (
    <AbsoluteFill style={{overflow: 'hidden', background: '#000205'}}>
      <Beam t={t} />
      {ICONS.map((ic) => {
        const dt = t - ic.t;
        if (dt < 0) return null;
        const p = Easing.out(Easing.cubic)(interpolate(dt, [0, 0.45], [0, 1], clamp));
        const blur = interpolate(dt, [0, 0.4], [10, 0], {...clamp, easing: Easing.out(Easing.quad)});
        return (
          <div
            key={ic.kind}
            style={{
              position: 'absolute',
              left: ic.cx - TILE_W / 2,
              top: CY - TILE_H / 2 + 26 * (1 - p),
              opacity: 0.22 + 0.78 * p,
              filter: blur > 0.2 ? `blur(${blur}px)` : undefined,
            }}
          >
            <Tile>
              {ic.kind === 'obsidian' ? <ObsidianLogo /> : ic.kind === 'drive' ? <DriveLogo /> : <NotionLogo />}
            </Tile>
          </div>
        );
      })}
    </AbsoluteFill>
  );
};

// Sons : grave-apparition sur chaque tuile (première image visible).
const CUES: SfxCue[] = ICONS.map((ic) => ({frame: Math.round(ic.t * FPS), name: 'grave-apparition' as const}));

const IconesStockage: React.FC<{showPlate?: boolean}> = () => (
  <AbsoluteFill style={{backgroundColor: '#000205'}}>
    <Scene />
    <SfxTrack cues={CUES} />
  </AbsoluteFill>
);

export const meta = {
  id: 'd223-icones-stockage',
  fps: FPS,
  durationInFrames: DUR,
  defaultProps: {showPlate: true},
  occurrences: [{ref: [1088.0, 1090.3] as [number, number], at: AT, from: 0, durationInFrames: DUR, mode: 'plein' as const}],
};
export default IconesStockage;

// Signaux sonores exportés pour la bibliothèque (cloud/cues_globaux.py).
export const cues = CUES;
