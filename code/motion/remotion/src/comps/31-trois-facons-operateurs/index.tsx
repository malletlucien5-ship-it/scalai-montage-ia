import React from 'react';
import {SfxTrack, SfxCue} from '../../shared/Sfx';
import {AbsoluteFill, Img, Sequence, staticFile, useCurrentFrame, Easing} from '../../shared/rt';
import {noise2D} from '@remotion/noise';
import {NightBg, SerifTitle, SERIF, SANS, ease, BlurWord} from './lib';

// 31 : « 3 Ways Operators Deploy Claude », carrés chiffrés italiques.
// Réf. 427,03-431,86 / 446,18-448,98 / 488,59-491,92 / 505,34-514,68 (variante speaker en carte).
const D_A = 145;
const D_B = 84;
const D_C = 100;
const D_D = 280;
const GAP = 15;
export const meta = {
  id: '31-trois-facons-operateurs',
  durationInFrames: D_A + D_B + D_C + D_D + 3 * GAP,
  fps: 30,
  defaultProps: {showPlate: true},
  occurrences: [
    {ref: [427.03, 431.86], from: 0, durationInFrames: D_A, mode: 'overlay' as const},
    {ref: [446.18, 448.98], from: D_A + GAP, durationInFrames: D_B, mode: 'overlay' as const},
    {ref: [488.59, 491.92], from: D_A + D_B + 2 * GAP, durationInFrames: D_C, mode: 'overlay' as const},
    {ref: [505.34, 514.68], from: D_A + D_B + D_C + 3 * GAP, durationInFrames: D_D, mode: 'overlay' as const},
  ],
};

const CYAN = '#10E6F7';
const TITLE = ['Opérateurs\u00a0:', '3', 'usages', 'de', 'Claude'];
// fond de chaque carré : base indigo + bande claire placée différemment (mesure pixel)
const SHEEN = [100, 45, 0];
const squareBg = (i: number) => {
  const p = SHEEN[i];
  return `linear-gradient(172deg, rgb(60,62,118) ${Math.max(0, p - 70)}%, rgb(66,86,146) ${Math.max(0, p - 25)}%, rgb(75,110,172) ${p}%, rgb(66,86,146) ${Math.min(100, p + 25)}%, rgb(60,62,118) ${Math.min(100, p + 70)}%)`;
};

const Square: React.FC<{
  i: number; x: number; y: number; size: number; radius: number; digitO: number; digitBlur: number; opacity: number; glow?: boolean;
}> = ({i, x, y, size, radius, digitO, digitBlur, opacity, glow}) => (
  <div
    style={{
      position: 'absolute',
      left: x - size / 2,
      top: y - size / 2,
      width: size,
      height: size,
      borderRadius: radius,
      background: squareBg(i),
      opacity,
      boxShadow: glow
        ? '0 0 22px rgba(16,200,230,0.22), 0 8px 24px rgba(0,0,0,0.55)'
        : '0 10px 26px rgba(0,0,0,0.5), inset 0 1px 1px rgba(160,180,230,0.25)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
    }}
  >
    <div
      style={{
        fontFamily: SERIF,
        fontStyle: 'italic',
        fontSize: size * 0.78,
        lineHeight: 1,
        color: CYAN,
        opacity: digitO,
        filter: digitBlur > 0.05 ? `blur(${digitBlur}px)` : undefined,
        textShadow: '0 0 10px rgba(16,230,247,0.65), 0 0 26px rgba(16,230,247,0.35)',
        marginTop: size * 0.02,
        marginLeft: -size * 0.03,
      }}
    >
      {i + 1}
    </div>
  </div>
);

// Libellé sous un carré, mot par mot en fondu flouté.
const Label: React.FC<{f: number; x: number; top: number; lines: string[][]; starts: number[]; size: number; lh: number}> = ({f, x, top, lines, starts, size, lh}) => {
  let k = 0;
  return (
    <div
      style={{
        position: 'absolute',
        left: x - 400,
        width: 800,
        top,
        textAlign: 'center',
        fontFamily: SANS,
        fontWeight: 700,
        fontSize: size,
        lineHeight: `${lh}px`,
        color: 'white',
        whiteSpace: 'nowrap',
      }}
    >
      {lines.map((ln, i) => (
        <div key={i}>
          {ln.map((w, j) => {
            const s = starts[k++];
            return (
              <React.Fragment key={j}>
                <BlurWord f={f} start={s} dur={8} blur={10}>
                  {w}
                </BlurWord>
                {j < ln.length - 1 ? ' ' : ''}
              </React.Fragment>
            );
          })}
        </div>
      ))}
    </div>
  );
};

const XS = [358, 960, 1556];
const Y0 = 579;
const LABEL_TOP = 743;
const LABELS = [[['Prompts', 'système']], [['Skills']], [['Tâches', 'Cowork'], ['planifiées']]];

const digitState = (f: number, s: number) => ({o: ease(f, s, s + 10, 0, 1), b: ease(f, s, s + 10, 12, 0)});

// Scène plein écran. act[i] = opacité (1 actif, 0,35 inactif), lab = départs des mots par carré.
const Board: React.FC<{f: number; title: boolean; ys: number[]; dig: number[]; act: number[]; lab: (number[] | null)[]}> = ({f, title, ys, dig, act, lab}) => (
  <AbsoluteFill>
    <NightBg />
    <SerifTitle f={title ? f : 999} words={TITLE} starts={[3, 8, 13, 18, 22]} size={108} top={97} dur={12} />
    {XS.map((x, i) => {
      const d = digitState(f, dig[i]);
      return <Square key={i} i={i} x={x} y={ys[i]} size={240} radius={22} digitO={d.o} digitBlur={d.b} opacity={act[i]} />;
    })}
    {lab.map((st, i) => (st ? <Label key={i} f={f} x={XS[i]} top={LABEL_TOP} lines={LABELS[i]} starts={st} size={i === 2 ? 57 : 65} lh={76} /> : null))}
  </AbsoluteFill>
);

const OccA: React.FC = () => {
  const f = useCurrentFrame();
  const rise = (off: number) => Y0 + 83 * Math.exp(-0.08 * (f - 28 - off));
  const dim = ease(f, 76, 85, 1, 0.35, Easing.inOut(Easing.quad));
  return (
    <Board f={f} title ys={[rise(0), rise(10), rise(16)]} dig={[27, 31, 35]} act={[1, dim, dim]} lab={[[76, 91], null, null]} />
  );
};

const OccB: React.FC = () => {
  const f = useCurrentFrame();
  const a2 = ease(f, 8, 18, 0.35, 1, Easing.inOut(Easing.quad));
  return <Board f={f} title={false} ys={[Y0, Y0, Y0]} dig={[-99, -99, -99]} act={[1, a2, 0.35]} lab={[[-99, -99], [38], null]} />;
};

const OccC: React.FC = () => {
  const f = useCurrentFrame();
  const a3 = ease(f, 7, 17, 0.35, 1, Easing.inOut(Easing.quad));
  return <Board f={f} title={false} ys={[Y0, Y0, Y0]} dig={[-99, -99, -99]} act={[1, 1, a3]} lab={[[-99, -99], [-99], [17, 32, 42]]} />;
};

// Variante carte speaker : fond noir à lueurs bleu-teal relevées sur 505-514 s.
// Les lueurs dérivent lentement (bruit), comme dans l'original.
const CARD = {x: 34, y: 248, w: 526, h: 550, r: 18};
const holePath = () => {
  const {x, y, w, h, r} = CARD;
  return `M0 0H1920V1080H0Z M${x + r} ${y} H${x + w - r} A${r} ${r} 0 0 1 ${x + w} ${y + r} V${y + h - r} A${r} ${r} 0 0 1 ${x + w - r} ${y + h} H${x + r} A${r} ${r} 0 0 1 ${x} ${y + h - r} V${y + r} A${r} ${r} 0 0 1 ${x + r} ${y} Z`;
};
const HOLE_MASK = `url("data:image/svg+xml;utf8,${encodeURIComponent(
  `<svg xmlns='http://www.w3.org/2000/svg' width='1920' height='1080'><path fill-rule='evenodd' fill='black' d='${holePath()}'/></svg>`,
)}")`;

const SpeakerBg: React.FC<{f: number}> = ({f}) => {
  const n = (s: string, amp: number) => noise2D(s, f / 150, 0) * amp;
  const g = [
    `radial-gradient(ellipse ${560 + n('a', 40)}px ${330 + n('b', 25)}px at ${430 + n('c', 35)}px ${990 + n('d', 20)}px, rgba(42,64,78,1) 0%, rgba(38,62,80,0.75) 40%, rgba(30,55,72,0) 100%)`,
    `radial-gradient(ellipse ${600 + n('e', 40)}px ${270 + n('f', 20)}px at ${930 + n('g', 40)}px ${1030 + n('h', 15)}px, rgba(32,58,76,0.95) 0%, rgba(28,54,72,0.6) 45%, rgba(20,45,60,0) 100%)`,
    `radial-gradient(ellipse 330px 170px at 520px 1090px, rgba(48,56,64,0.85), rgba(48,56,64,0) 100%)`,
    `radial-gradient(ellipse 420px 760px at 1880px 700px, rgba(7,18,24,1), rgba(7,18,24,0) 100%)`,
    `radial-gradient(ellipse 260px 220px at 60px 780px, rgba(12,28,40,0.9), rgba(12,28,40,0) 100%)`,
    '#000',
  ];
  return <AbsoluteFill style={{background: g.join(', '), WebkitMaskImage: HOLE_MASK, maskImage: HOLE_MASK}} />;
};

const XD = [775, 1203, 1630];
const YD = 424;
const LABELS_D = [[['Prompts'], ['système']], [['Skills']], [['Tâches', 'Cowork'], ['planifiées']]];

const OccD: React.FC<{showPlate: boolean}> = ({showPlate}) => {
  const f = useCurrentFrame();
  const starts = [[63, 78], [116], [206, 221, 236]];
  const dig = [5, 17, 35];
  return (
    <AbsoluteFill>
      <SpeakerBg f={f} />
      <Img
        src={staticFile('31/speaker.jpg')}
        style={{
          position: 'absolute',
          left: CARD.x,
          top: CARD.y,
          width: CARD.w,
          height: CARD.h,
          borderRadius: CARD.r,
          objectFit: 'cover',
          objectPosition: '50% 50%',
        }}
      />
      <div
        style={{
          position: 'absolute',
          left: CARD.x,
          top: CARD.y,
          width: CARD.w,
          height: CARD.h,
          borderRadius: CARD.r,
          border: '1.5px solid rgba(235,235,240,0.75)',
          boxSizing: 'border-box',
        }}
      />
      {XD.map((x, i) => {
        const d = digitState(f, dig[i]);
        return <Square key={i} i={i} x={x} y={YD} size={214} radius={20} digitO={d.o} digitBlur={d.b} opacity={1} glow />;
      })}
      {XD.map((x, i) => (
        <Label key={i} f={f} x={x} top={560} lines={LABELS_D[i]} starts={starts[i]} size={i === 2 ? 59 : 67} lh={80} />
      ))}
    </AbsoluteFill>
  );
};

// Bruitages (SFX-REGLES.md) : nappe à l'image 0 de chaque occurrence, grave à l'arrivée de chaque carré.
const O_B = D_A + GAP;
const O_C = O_B + D_B + GAP;
const O_D = O_C + D_C + GAP;
const CUES: SfxCue[] = [
  {frame: 0, name: 'nappe-ecran-titre'},
  {frame: 3, name: 'grave-apparition'}, // carré 1
  {frame: 13, name: 'grave-apparition'}, // carré 2
  {frame: 19, name: 'grave-apparition'}, // carré 3
  {frame: O_B, name: 'nappe-ecran-titre'},
  {frame: O_C, name: 'nappe-ecran-titre'},
  {frame: O_D, name: 'nappe-ecran-titre'},
];

const Comp: React.FC<{showPlate?: boolean}> = ({showPlate = true}) => {
  const seq: [number, React.ReactNode][] = [
    [D_A, <OccA />],
    [GAP, <NightBg />],
    [D_B, <OccB />],
    [GAP, <NightBg />],
    [D_C, <OccC />],
    [GAP, <NightBg />],
    [D_D, <OccD showPlate={showPlate} />],
  ];
  let t = 0;
  return (
    <AbsoluteFill style={{background: showPlate ? '#000' : 'transparent'}}>
      {seq.map(([d, el], i) => {
        const from = t;
        t += d;
        return (
          <Sequence key={i} from={from} durationInFrames={d}>
            {el}
          </Sequence>
        );
      })}
      <SfxTrack cues={CUES} />
    </AbsoluteFill>
  );
};
export default Comp;

// Signaux sonores exportés pour la bibliothèque (cloud/cues_globaux.py).
export const cues = CUES;
