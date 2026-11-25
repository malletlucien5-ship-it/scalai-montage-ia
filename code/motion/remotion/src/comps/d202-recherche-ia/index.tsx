import React from 'react';
import {AbsoluteFill, Easing, interpolate, useCurrentFrame} from '../../shared/rt';
import {INTER_L} from '../../shared/localFonts';
import {SfxTrack, SfxCue} from '../../shared/Sfx';

// Référence 7.73-12.74 s : barre de recherche blanche sur dégradé bleu nuit.
// Cercle loupe qui monte du bas, s'élargit en barre, frappe, curseur bleu, clic,
// pastille « Réflexion… » avec sphère de points, glissement à gauche puis zoom de sortie.
const FPS = 30;
const AT = 7.75; // début dans la voix coupée (intro 1,1 s avant « Les modèles », comme chez Dan)
const DUR = Math.round((14.2 - AT) * FPS); // jusqu'à la fin de « l'instant T. »

const TEXT = "Les modèles d'IA changent tout le temps";
const THINK = 'Réflexion...';

// Temps locaux (s). Mots de Lucien : Les 8.85, temps 10.49, rester 10.97, instant T 14.19.
const T = {
  rise: 0,
  expand: [0.47, 1.26] as const,
  caret: 1.05,
  type: [1.1, 2.6] as const, // 8.85 -> 10.35
  cursorIn: 2.95,
  cursorAt: 3.2,
  click: 3.3,
  shrink: [3.33, 3.6] as const,
  exit: 5.55,
};

const CX = 958;
const CY = 538;
const H = 148;
const FULL = {l: 324, r: 1592};
const PILL = {l: 640, r: 1280};

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const io = Easing.bezier(0.65, 0, 0.35, 1);

const Background: React.FC = () => (
  <AbsoluteFill
    style={{
      background: [
        // Ellipse ajustée sur la référence (centre 960,2000 ; rayons 400x600 ; d visible 1,54-3,76)
        'radial-gradient(ellipse 1504px 2256px at 960px 2000px, #9ad8ff 0%, #89cafd 40.9%, #71acfd 45.4%, #5a90e0 50%, #4474bd 54.5%, #35609e 59.1%, #2a4e83 63.6%, #1e3d6d 68.2%, #132f5a 72.7%, #0c2649 77.3%, #091c3b 81.8%, #06162c 86.4%, #05101c 90.9%, #030910 95.5%, #01060b 100%)',
        '#01060b',
      ].join(','),
    }}
  />
);

const Loupe: React.FC<{x: number; y: number; opacity?: number}> = ({x, y, opacity = 1}) => (
  <svg width={64} height={64} viewBox="0 0 64 64" style={{position: 'absolute', left: x - 32, top: y - 32, opacity}}>
    <circle cx={27} cy={27} r={16} fill="none" stroke="#111" strokeWidth={6} />
    <path d="M39 39 L53 53" stroke="#111" strokeWidth={7} strokeLinecap="round" />
  </svg>
);

// Sphère de points bleu-violet qui tourne (icône de la pastille).
const DOTS = (() => {
  const n = 150;
  const pts: {x: number; y: number; z: number}[] = [];
  const ga = Math.PI * (3 - Math.sqrt(5));
  for (let i = 0; i < n; i++) {
    const y = 1 - (i / (n - 1)) * 2;
    const r = Math.sqrt(1 - y * y);
    const th = ga * i;
    pts.push({x: Math.cos(th) * r, y, z: Math.sin(th) * r});
  }
  return pts;
})();

const Sphere: React.FC<{cx: number; cy: number; r: number; t: number}> = ({cx, cy, r, t}) => {
  const a = t * 1.6;
  const tilt = 0.35;
  return (
    <svg width={r * 2 + 8} height={r * 2 + 8} style={{position: 'absolute', left: cx - r - 4, top: cy - r - 4}}>
      <defs>
        <radialGradient id="d202sph" cx="40%" cy="35%" r="70%">
          <stop offset="0%" stopColor="#dfe6ff" />
          <stop offset="100%" stopColor="#a9b8f0" />
        </radialGradient>
      </defs>
      <circle cx={r + 4} cy={r + 4} r={r} fill="url(#d202sph)" opacity={0.85} />
      {DOTS.map((p, i) => {
        const x1 = p.x * Math.cos(a) + p.z * Math.sin(a);
        const z1 = -p.x * Math.sin(a) + p.z * Math.cos(a);
        const y2 = p.y * Math.cos(tilt) - z1 * Math.sin(tilt);
        const z2 = p.y * Math.sin(tilt) + z1 * Math.cos(tilt);
        const depth = (z2 + 1) / 2;
        const col = x1 > 0.2 ? '#6a3fe0' : '#2f64e6';
        return (
          <circle
            key={i}
            cx={r + 4 + x1 * r * 0.95}
            cy={r + 4 + y2 * r * 0.95}
            r={1.6 + depth * 2.6}
            fill={col}
            opacity={0.25 + depth * 0.75}
          />
        );
      })}
    </svg>
  );
};

const Cursor: React.FC<{x: number; y: number; opacity: number; scale: number}> = ({x, y, opacity, scale}) => (
  <svg
    width={80}
    height={72}
    viewBox="0 0 80 72"
    style={{position: 'absolute', left: x, top: y, opacity, transform: `scale(${scale})`, transformOrigin: '0 0'}}
  >
    <defs>
      <linearGradient id="d202cur" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0%" stopColor="#3b6ef0" />
        <stop offset="100%" stopColor="#4a4fd8" />
      </linearGradient>
    </defs>
    <path d="M0 0 L68 22 L40 33 L38 63 Z" fill="url(#d202cur)" />
  </svg>
);

const Scene: React.FC = () => {
  const f = useCurrentFrame();
  const t = f / FPS;

  // 1. Cercle qui monte du bas (décroissance exponentielle, tau 0,15 s)
  const top = CY - H / 2 + 500 * Math.exp(-Math.max(0, t - T.rise) / 0.15);

  // 2. Élargissement en barre
  const pe = io(interpolate(t, T.expand, [0, 1], clamp));
  const wExp = H + (FULL.r - FULL.l - H) * pe;
  let left = CX - wExp / 2;
  let right = CX + wExp / 2;

  // 4. Rétrécissement en pastille après le clic
  const ps = Easing.out(Easing.cubic)(interpolate(t, T.shrink, [0, 1], clamp));
  if (t >= T.shrink[0]) {
    left = interpolate(ps, [0, 1], [FULL.l, PILL.l]);
    right = interpolate(ps, [0, 1], [FULL.r, PILL.r]);
  }

  // 5. Sortie : glissement à gauche avec étirement, puis zoom flou
  const te = t - T.exit;
  let blurX = 0;
  let zoom = 1;
  let zoomBlur = 0;
  if (te > 0) {
    const eIn = Easing.in(Easing.quad);
    left = interpolate(te, [0, 0.36, 0.63], [PILL.l, -80, -700], {...clamp, easing: eIn});
    right = interpolate(te, [0, 0.2, 0.36, 0.63], [PILL.r, 1266, 1180, 1004], clamp);
    blurX = interpolate(te, [0, 0.12, 0.36, 0.55, 0.63], [0, 10, 26, 14, 4], clamp);
    zoom = interpolate(te, [0.63, 0.9], [1, 5.2], {...clamp, easing: Easing.in(Easing.quad)});
    zoomBlur = interpolate(te, [0.63, 0.9], [0, 22], clamp);
  }

  const w = right - left;
  const radius = Math.min(H / 2, 46 + (1 - Math.min(1, (w - H) / 120)) * (H / 2 - 46));

  // Texte tapé
  const n = Math.floor(interpolate(t, T.type, [0, TEXT.length], clamp));
  const typed = TEXT.slice(0, n);
  const showCaret = t >= T.caret;
  const textOp = interpolate(t, [T.click, T.click + 0.15], [1, 0], clamp);
  const textGrey = interpolate(t, [T.click, T.click + 0.08], [0, 1], clamp);

  // Loupe : centrée dans le cercle, puis à droite de la barre
  const loupeX = right - interpolate(w, [H, FULL.r - FULL.l], [H / 2, 82], clamp);
  const loupeOp = t < T.shrink[0] ? 1 : textOp;

  // Pastille « Réflexion… »
  const thinkOp = interpolate(t, [T.shrink[0] + 0.08, T.shrink[1] + 0.05], [0, 1], clamp) * interpolate(te, [0.2, 0.4], [1, 0], clamp);

  // Curseur
  const pc = Easing.out(Easing.cubic)(interpolate(t, [T.cursorIn, T.cursorAt], [0, 1], clamp));
  const curX = interpolate(pc, [0, 1], [1010, 1512]);
  const curY = interpolate(pc, [0, 1], [1110, 530]);
  const curOp = t < T.cursorIn ? 0 : interpolate(t, [T.click + 0.05, T.click + 0.25], [1, 0], clamp);
  const curScale = interpolate(t, [T.click - 0.04, T.click, T.click + 0.08], [1, 0.85, 1], clamp);

  const barTop = t < T.expand[0] ? top : CY - H / 2;

  return (
    <AbsoluteFill style={{overflow: 'hidden'}}>
      <Background />
      <svg width={0} height={0} style={{position: 'absolute'}}>
        <filter id="d202mb" x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation={`${blurX} 0`} />
        </filter>
      </svg>
      <AbsoluteFill
        style={{
          transform: `scale(${zoom})`,
          transformOrigin: '832px 540px',
          filter: zoomBlur > 0 ? `blur(${zoomBlur}px)` : undefined,
        }}
      >
        <div style={{position: 'absolute', inset: 0, filter: blurX > 0.3 ? 'url(#d202mb)' : undefined}}>
          <div
            style={{
              position: 'absolute',
              left,
              top: barTop,
              width: w,
              height: H,
              borderRadius: radius,
              background: 'linear-gradient(180deg, #e8edf5 0%, #e3e9f2 100%)',
              boxShadow: '0 0 16px 3px rgba(225,235,255,0.55), 0 0 46px 6px rgba(150,185,255,0.35)',
              overflow: 'hidden',
            }}
          >
            {thinkOp > 0 && (
              <div
                style={{
                  position: 'absolute',
                  inset: 0,
                  opacity: thinkOp,
                  background: 'radial-gradient(ellipse 360px 120px at 330px 50%, rgba(160,185,235,0.45), rgba(160,185,235,0) 100%)',
                }}
              />
            )}
          </div>
          {/* Loupe */}
          {loupeOp > 0 && <Loupe x={loupeX} y={barTop + H / 2} opacity={loupeOp} />}
          {/* Texte tapé */}
          {showCaret && textOp > 0 && (
            <div
              style={{
                position: 'absolute',
                left: FULL.l + 72,
                top: CY - 40,
                height: 80,
                lineHeight: '80px',
                fontFamily: INTER_L,
                fontWeight: 800,
                fontSize: 50,
                letterSpacing: -0.5,
                color: textGrey > 0.5 ? '#8a8f99' : '#111',
                opacity: textOp,
                whiteSpace: 'pre',
              }}
            >
              {typed}
              <span style={{fontWeight: 700}}>|</span>
            </div>
          )}
          {/* Pastille Réflexion */}
          {thinkOp > 0 && (
            <div style={{position: 'absolute', left: 0, top: 0, width: 1920, height: 1080, opacity: thinkOp}}>
              <Sphere cx={left + 104} cy={CY} r={50} t={t} />
              <div
                style={{
                  position: 'absolute',
                  left: left + 202,
                  top: CY - 50,
                  height: 100,
                  lineHeight: '100px',
                  fontFamily: INTER_L,
                  fontWeight: 400,
                  fontSize: 74,
                  letterSpacing: -1,
                  whiteSpace: 'pre',
                  background: 'linear-gradient(90deg, #2f6fe2 0%, #3d58da 100%)',
                  WebkitBackgroundClip: 'text',
                  backgroundClip: 'text',
                  color: 'transparent',
                }}
              >
                {THINK}
              </div>
            </div>
          )}
        </div>
        {curOp > 0 && <Cursor x={curX} y={curY} opacity={curOp} scale={curScale} />}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

// Sons (SFX-REGLES.md) : whoosh à l'entrée du plein écran, frappe pendant la saisie,
// clic sur la loupe, pop à l'arrivée de la pastille, whoosh au glissement de sortie.
const CUES: SfxCue[] = [
  {frame: 0, name: 'whoosh-transition'},
  {frame: Math.round(T.type[0] * FPS), name: 'frappe-clavier', durationInFrames: Math.round((T.type[1] - T.type[0]) * FPS)},
  {frame: Math.round(T.click * FPS), name: 'clic'},
  {frame: Math.round((T.shrink[0] + 0.1) * FPS), name: 'pop'},
  {frame: Math.round(T.exit * FPS), name: 'whoosh-transition'},
];

const RechercheIA: React.FC<{showPlate?: boolean}> = () => (
  <AbsoluteFill style={{backgroundColor: '#01060b'}}>
    <Scene />
    <SfxTrack cues={CUES} />
  </AbsoluteFill>
);

export const meta = {
  id: 'd202-recherche-ia',
  fps: FPS,
  durationInFrames: DUR,
  defaultProps: {showPlate: true},
  occurrences: [{ref: [7.73, 12.74] as [number, number], at: AT, from: 0, durationInFrames: DUR, mode: 'plein' as const}],
};
export default RechercheIA;

// Signaux sonores exportés pour la bibliothèque (cloud/cues_globaux.py).
export const cues = CUES;
