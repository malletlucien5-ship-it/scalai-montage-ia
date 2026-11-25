import React from 'react';
import {AbsoluteFill, Sequence, useCurrentFrame} from '../../shared/rt';
import {loadFont as inter} from '@remotion/google-fonts/Inter';
import {Plate} from '../../shared/Plate';
import {SfxTrack, SfxCue} from '../../shared/Sfx';

const SANS = inter('normal', {weights: ['700']}).fontFamily;
const FPS = 30;
const CYAN = '#1BD9EA';

type Step = {
  n: string;
  text: string;
  start: number; // début de l'occurrence (réf., s)
  end: number;
  in: number; // image 0 de l'entrée (réf., s)
  out?: number; // début du fondu de sortie (réf., s)
  left: number; // bord gauche de la boîte
  cell: number; // largeur de la case du chiffre (jusqu'au filet)
  gap: number; // filet -> texte
  w: number; // largeur de la boîte relevée sur l'original
  size: number; // police réduite au minimum pour que le texte tienne (72 px dans l'original)
};

// Relevés 1920x1080 : boîte haute de 161 px (y 870 à 1031), chiffre 114 px, texte 72 px.
const STEPS: Step[] = [
  {n: '1', text: 'Crée un nouveau projet', size: 64, start: 102.5, end: 106.1, in: 102.667, out: 105.9, left: 34, w: 1015, cell: 176, gap: 50},
  {n: '2', text: 'Rédige un prompt maître', size: 64, start: 111.9, end: 115.5, in: 112.134, out: 114.9, left: 54, w: 1121, cell: 216, gap: 70},
  {n: '3', text: 'Ajoute les fichiers', size: 50, start: 149.0, end: 151.05, in: 149.3, left: 51, w: 790, cell: 211, gap: 63},
];

// Entrée mesurée : fondu + flou + montée de 48 px en décroissance (x0,87 par image).
// Sortie mesurée : fondu + flou sur 16 images avec une légère remontée.
const motion = (f: number, fo: number | null) => {
  let dy = 48 * Math.pow(0.87, f);
  let op = 1 - Math.pow(0.82, f);
  let blur = 8 * Math.pow(0.8, f);
  if (fo !== null && fo >= 0) {
    const k = Math.min(1, fo / 16);
    op *= 1 - k;
    blur += 7 * k;
    dy -= 10 * k;
  }
  return {dy, op, blur};
};

const StepView: React.FC<{s: Step}> = ({s}) => {
  const frame = useCurrentFrame();
  const f = frame - Math.round((s.in - s.start) * FPS);
  if (f < 0) return null;
  const fo = s.out !== undefined ? frame - Math.round((s.out - s.start) * FPS) : null;
  const m = motion(f, fo);
  if (m.op <= 0.001) return null;
  return (
    <div
      style={{
        position: 'absolute',
        left: s.left,
        top: 870,
        height: 161,
        width: s.w,
        display: 'flex',
        alignItems: 'stretch',
        boxSizing: 'border-box',
        borderRadius: 12,
        border: '1.5px solid rgba(96,186,206,0.72)',
        // Lueur relevée : plus claire en haut à gauche (x 200, y 890 : #14465E), sombre en bas (#07263D), fond #02162B à droite.
        background:
          'radial-gradient(ellipse 22% 95% at 14% 0%, rgba(24,78,104,0.95) 0%, rgba(24,78,104,0) 100%), radial-gradient(ellipse 30% 150% at 8% 0%, rgba(10,50,72,0.5) 0%, rgba(2,20,40,0) 100%), linear-gradient(90deg, #08283F 0%, #052139 22%, #031B32 40%, #02182D 65%, #02162B 100%)',
        boxShadow: '0 6px 22px rgba(0,0,0,0.35)',
        transform: `translateY(${m.dy}px)`,
        opacity: m.op,
        filter: m.blur > 0.1 ? `blur(${m.blur}px)` : undefined,
      }}
    >
      <div
        style={{
          width: s.cell,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontFamily: SANS,
          fontWeight: 700,
          fontSize: 114,
          color: CYAN,
          lineHeight: 1,
          paddingTop: 2,
        }}
      >
        {s.n}
      </div>
      <div style={{width: 1.5, margin: '14px 0', background: 'rgba(96,186,206,0.6)'}} />
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          paddingLeft: s.gap,
          fontFamily: SANS,
          fontWeight: 700,
          fontSize: s.size,
          color: CYAN,
          whiteSpace: 'pre',
          lineHeight: 1,
          paddingTop: 0,
          textShadow: '0 0 12px rgba(27,217,234,0.2)',
        }}
      >
        {s.text}
      </div>
    </div>
  );
};

const plan = (() => {
  let at = 0;
  return STEPS.map((s, i) => {
    if (i > 0) at += 0.5;
    const from = Math.round(at * FPS);
    const dur = Math.round((s.end - s.start) * FPS);
    at += s.end - s.start;
    return {s, from, dur};
  });
})();

// Bruitages (SFX-REGLES.md) : grave-apparition à l'arrivée de chaque étape,
// sur la première image visible (l'image 0 de l'entrée est à opacité nulle).
const CUES: SfxCue[] = plan.map(({s, from}) => ({frame: from + Math.round((s.in - s.start) * FPS) + 1, name: 'grave-apparition'}));

const EtapeNumerotee: React.FC<{showPlate?: boolean}> = ({showPlate = true}) => (
  <AbsoluteFill style={{backgroundColor: 'transparent'}}>
    <Plate show={showPlate} />
    {plan.map(({s, from, dur}, i) => (
      <Sequence key={i} from={from} durationInFrames={dur} layout="none">
        <StepView s={s} />
      </Sequence>
    ))}
    <SfxTrack cues={CUES} />
  </AbsoluteFill>
);

export const meta = {
  id: '14-etape-numerotee',
  durationInFrames: plan[plan.length - 1].from + plan[plan.length - 1].dur,
  fps: FPS,
  defaultProps: {showPlate: true},
  occurrences: plan.map(({s, from, dur}) => ({ref: [s.start, s.end] as [number, number], from, durationInFrames: dur, mode: 'overlay' as const})),
};
export default EtapeNumerotee;

// Signaux sonores exportés pour la bibliothèque (cloud/cues_globaux.py).
export const cues = CUES;
