import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame} from '../../shared/rt';
import {INTER_L} from '../../shared/localFonts';
import {SfxTrack, SfxCue} from '../../shared/Sfx';

// Référence 1060.3-1064.3 s : carte sombre arrondie (points macOS) sur dégradé bleu.
// La carte s'élargit, « Strategy = sequencing » tapé lettre à lettre (fondu par lettre),
// frise de 5 pastilles bleues cochées qui glissent depuis la droite en s'agrandissant.
const FPS = 30;
const AT = 1135.84; // « stratégie » (Parce que la stratégie c'est simplement…)
const DUR = Math.round((1140.7 - AT) * FPS); // jusqu'à la fin de « vous aurez des résultats. »

const TITLE = 'Stratégie = séquençage';

const CARD = {cx: 960, top: 320, h: 457, w: 1156, r: 58};
const DOT_Y = 356;
const STEP_X = [526, 738, 950, 1162, 1374];
const STEP_Y = 578;
const STEP_R = 35;
const NUM_Y = 665;

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const L = TITLE.length;
const TYPE_T = [0, 0.1, 0.2, 0.3, 0.5, 0.62];
const TYPE_N = [1, 6, 12, 16, 20, 21].map((n) => (n / 21) * L + (n === 1 ? 0 : 0.99));
// Instant d'apparition de la lettre i (inverse de la courbe de frappe).
const letterT = (i: number) => interpolate(i + 1, TYPE_N, TYPE_T, clamp);
const decay = (t: number, tau: number) => Math.exp(-Math.max(0, t) / tau);

// Dégradé ajusté sur la référence : ellipse centrée (1000,1100), lueur cyan en bas,
// bleu marine en bas à gauche.
const Background: React.FC = () => (
  <AbsoluteFill
    style={{
      background: [
        'radial-gradient(ellipse 760px 700px at 0px 1080px, rgba(0,8,90,0.8) 0%, rgba(0,8,90,0.3) 55%, rgba(0,8,90,0) 100%)',
        'radial-gradient(ellipse 2082px 1190px at 1000px 1100px, #01a0fa 0%, #019bf6 1.9%, #0094ee 9.4%, #0188db 17%, #0172bb 24.5%, #01538e 32.1%, #022e61 39.6%, #011149 47.2%, #02092e 54.7%, #02051c 62.3%, #030311 69.8%, #03020b 77.4%, #030206 84.9%, #030205 92.5%, #030202 100%)',
      ].join(','),
    }}
  />
);

const Check: React.FC<{x: number; s: number; op: number}> = ({x, s, op}) => (
  <svg
    width={STEP_R * 2}
    height={STEP_R * 2}
    viewBox="0 0 70 70"
    style={{position: 'absolute', left: x - STEP_R, top: STEP_Y - STEP_R, transform: `scale(${s})`, opacity: op}}
  >
    <circle cx={35} cy={35} r={35} fill="#0a86e2" />
    <path d="M23 36 L31.5 44.5 L47.5 27" fill="none" stroke="#0c1726" strokeWidth={5.2} strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

const Scene: React.FC = () => {
  const f = useCurrentFrame();
  const t = f / FPS;

  const w = CARD.w - 528 * decay(t, 0.15);
  const left = CARD.cx - w / 2;

  // Points macOS : très écartés au départ, se resserrent en haut à gauche.
  const k = decay(t, 0.13);
  const dotOff = 49 + 213 * k;
  const dotGap = 19 + 149 * k;

  // Frappe mesurée (lettres visibles à 0,1/0,2/0,3/0,5/0,62 s), fondu de 0,08 s par lettre ; texte centré.
  const shown = Math.floor(interpolate(t, TYPE_T, TYPE_N, clamp));

  // Éléments de la frise : glissement depuis la droite + agrandissement, décalés de 0,05 s.
  const item = (idx: number) => {
    const s = 0.2 + 0.05 * idx;
    const dt = t - s;
    if (dt < 0) return {dx: 0, sc: 0, op: 0};
    return {dx: 460 * Math.exp(-dt / 0.12), sc: 1 - Math.exp(-dt / 0.13), op: Math.min(1, dt / 0.06)};
  };

  return (
    <AbsoluteFill style={{overflow: 'hidden'}}>
      <Background />
      <div
        style={{
          position: 'absolute',
          left,
          top: CARD.top,
          width: w,
          height: CARD.h,
          borderRadius: CARD.r,
          background: '#101010',
          border: '2.5px solid #e9dede',
          boxSizing: 'border-box',
          boxShadow: '0 0 14px 2px rgba(255,236,236,0.38), 0 0 40px 4px rgba(255,236,236,0.1)',
        }}
      />
      {['#ff5f57', '#febc2e', '#28c840'].map((c, i) => (
        <div
          key={c}
          style={{position: 'absolute', left: left + dotOff + i * dotGap - 6.5, top: DOT_Y - 6.5, width: 13, height: 13, borderRadius: 7, background: c}}
        />
      ))}
      <div
        style={{
          position: 'absolute',
          left: 0,
          right: 0,
          top: 415 - 60,
          height: 120,
          lineHeight: '120px',
          textAlign: 'center',
          fontFamily: INTER_L,
          fontWeight: 700,
          fontSize: 78,
          letterSpacing: -0.5,
          color: '#fff4f2',
          whiteSpace: 'pre',
          textShadow: '0 0 12px rgba(255,210,205,0.55)',
        }}
      >
        {TITLE.slice(0, shown)
          .split('')
          .map((ch, i) => (
            <span key={i} style={{opacity: interpolate(t, [letterT(i), letterT(i) + 0.08], [0.15, 1], clamp)}}>
              {ch}
            </span>
          ))}
      </div>
      {STEP_X.map((x, i) => {
        const a = item(i);
        const numOp = interpolate(t - (0.3 + 0.05 * i), [0, 0.25], [0, 1], clamp);
        return (
          <React.Fragment key={i}>
            {i < 4 &&
              (() => {
                const c = item(i + 0.5);
                if (c.op <= 0) return null;
                const x0 = x + 54 + c.dx;
                const x1 = STEP_X[i + 1] - 56 + c.dx * 1.15;
                const mid = (x0 + x1) / 2;
                const half = ((x1 - x0) / 2) * c.sc;
                return (
                  <svg width={1920} height={20} style={{position: 'absolute', left: 0, top: STEP_Y - 10, opacity: c.op}}>
                    <line x1={mid - half} x2={mid + half} y1={10} y2={10} stroke="#e6e6e6" strokeWidth={2} />
                    <circle cx={mid - half} cy={10} r={5 * c.sc} fill="#f2f2f2" />
                    <circle cx={mid + half} cy={10} r={5 * c.sc} fill="#f2f2f2" />
                  </svg>
                );
              })()}
            {a.op > 0 && <Check x={x + a.dx} s={a.sc} op={a.op} />}
            {numOp > 0 && (
              <div
                style={{
                  position: 'absolute',
                  left: x + a.dx - 40,
                  width: 80,
                  top: NUM_Y - 22,
                  height: 44,
                  lineHeight: '44px',
                  textAlign: 'center',
                  fontFamily: INTER_L,
                  fontWeight: 400,
                  fontSize: 31,
                  color: '#f1f1f1',
                  opacity: numOp,
                  textShadow: '0 0 6px rgba(255,255,255,0.3)',
                }}
              >
                {i + 1}
              </div>
            )}
          </React.Fragment>
        );
      })}
    </AbsoluteFill>
  );
};

// Sons : whoosh à l'entrée de la carte, frappe pendant la saisie, un pop pour la frise
// (les pastilles arrivent à moins de 0,12 s d'écart).
const CUES: SfxCue[] = [
  {frame: 0, name: 'whoosh-transition'},
  {frame: 0, name: 'frappe-clavier', durationInFrames: Math.round(0.62 * FPS)},
  {frame: 7, name: 'pop'},
];

const StrategieSequence: React.FC<{showPlate?: boolean}> = () => (
  <AbsoluteFill style={{backgroundColor: '#030305'}}>
    <Scene />
    <SfxTrack cues={CUES} />
  </AbsoluteFill>
);

export const meta = {
  id: 'd222-strategie-sequence',
  fps: FPS,
  durationInFrames: DUR,
  defaultProps: {showPlate: true},
  occurrences: [{ref: [1060.3, 1064.3] as [number, number], at: AT, from: 0, durationInFrames: DUR, mode: 'plein' as const}],
};
export default StrategieSequence;

// Signaux sonores exportés pour la bibliothèque (cloud/cues_globaux.py).
export const cues = CUES;
