import React from 'react';
import {SfxTrack, SfxCue} from '../../shared/Sfx';
import {AbsoluteFill, Sequence, useCurrentFrame, interpolate, Easing} from '../../shared/rt';
import {NightBg, SerifTitle, SANS, clamp, BlurWord, ease} from './lib';

// 41 : « The Agent-Building Framework », pyramide 1-2-3, flèches pointillées manuscrites.
// Réf. 762,80-771,10 / 784,48-788,09 / 795,16-798,23.
const D1 = 249;
const D2 = 108;
const D3 = 92;
const GAP = 15;
export const meta = {
  id: '41-pyramide-framework',
  durationInFrames: D1 + D2 + D3 + 2 * GAP,
  fps: 30,
  occurrences: [
    {ref: [762.80, 771.10], from: 0, durationInFrames: D1, mode: 'plein' as const},
    {ref: [784.48, 788.09], from: D1 + GAP, durationInFrames: D2, mode: 'plein' as const},
    {ref: [795.16, 798.23], from: D1 + D2 + 2 * GAP, durationInFrames: D3, mode: 'plein' as const},
  ],
};

const TITLE = ['Le', 'cadre', 'pour', 'bâtir', 'des', 'agents'];

// Chute des étages : position du haut de chaque étage relevée image par image (s -> y).
const keys = (pts: number[], ys: number[], f: number) =>
  interpolate(f / 30, pts, ys, {...clamp});
const T1 = {pts: [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 2.0], ys: [-180, -10, 168, 312, 418, 504, 576, 624, 672, 706, 730, 754, 768, 782, 792, 800, 803]};
const T2 = {pts: [0.55, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2.1, 2.4], ys: [-190, 34, 144, 216, 288, 336, 384, 422, 456, 480, 504, 518, 538, 552, 565, 570]};
const T3 = {pts: [0.85, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2.1, 2.4, 2.8], ys: [-240, -60, 5, 35, 62, 92, 120, 152, 180, 205, 226, 260, 285, 290]};

// Géométrie finale (px) : [haut, bas, demi-largeur haute, demi-largeur basse], centre x 958.
const CX = 958;
const TIERS = [
  {top: 803, h: 155, wt: 350, wb: 438, n: '1'},
  {top: 570, h: 185, wt: 209, wb: 308, n: '2'},
  {top: 290, h: 226, wt: 0, wb: 152, n: '3'},
];

const Tier: React.FC<{i: number; top: number}> = ({i, top}) => {
  const t = TIERS[i];
  const pad = 40;
  const W = t.wb * 2 + pad * 2;
  const H = t.h + pad * 2;
  const x0 = pad + t.wb;
  const pts = `${x0 - t.wt},${pad} ${x0 + t.wt},${pad} ${x0 + t.wb},${pad + t.h} ${x0 - t.wb},${pad + t.h}`;
  const gid = `g41_${i}`;
  return (
    <div style={{position: 'absolute', left: CX - x0, top: top - pad, width: W, height: H}}>
      <svg width={W} height={H} style={{position: 'absolute', overflow: 'visible', filter: 'drop-shadow(0 0 16px rgba(70,90,255,0.4))'}}>
        <defs>
          <linearGradient id={gid} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="rgb(170,190,255)" />
            <stop offset="0.12" stopColor="rgb(140,160,248)" />
            <stop offset="0.3" stopColor="rgb(80,102,202)" />
            <stop offset="0.5" stopColor="rgb(65,84,178)" />
            <stop offset="0.66" stopColor="rgb(57,71,157)" />
            <stop offset="0.8" stopColor="rgb(44,55,127)" />
            <stop offset="0.9" stopColor="rgb(29,36,88)" />
            <stop offset="1" stopColor="rgb(30,38,125)" />
          </linearGradient>
          <linearGradient id={gid + 'e'} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="rgba(190,200,255,0.9)" />
            <stop offset="1" stopColor="rgba(70,85,255,0.9)" />
          </linearGradient>
          <clipPath id={gid + 'c'}>
            <polygon points={pts} />
          </clipPath>
          <filter id={gid + 'b1'} x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation={16} />
          </filter>
          <filter id={gid + 'b2'} x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation={4} />
          </filter>
        </defs>
        <polygon points={pts} fill={`url(#${gid})`} />
        {/* Biseau : reflet clair le long du bord gauche, liseré bleu saturé à droite et en bas (relevé pixel). */}
        <g clipPath={`url(#${gid}c)`}>
          <line x1={x0 - t.wt} y1={pad - 20} x2={x0 - t.wb} y2={pad + t.h + 20} stroke="rgb(170,180,255)" strokeWidth={30} filter={`url(#${gid}b1)`} />
          <line x1={x0 - t.wt} y1={pad - 20} x2={x0 - t.wb} y2={pad + t.h + 20} stroke="rgb(150,160,255)" strokeWidth={6} filter={`url(#${gid}b2)`} />
          <line x1={x0 + t.wt} y1={pad - 20} x2={x0 + t.wb} y2={pad + t.h + 20} stroke="rgb(62,80,240)" strokeWidth={16} filter={`url(#${gid}b2)`} />
          <line x1={x0 - t.wb} y1={pad + t.h} x2={x0 + t.wb} y2={pad + t.h} stroke="rgb(52,68,235)" strokeWidth={10} filter={`url(#${gid}b2)`} />
          <line x1={x0 - t.wt - 20} y1={pad} x2={x0 + t.wt + 20} y2={pad} stroke="rgb(200,212,255)" strokeWidth={8} filter={`url(#${gid}b2)`} />
        </g>
      </svg>
      <div
        style={{
          position: 'absolute',
          left: 0,
          width: W,
          top: pad + t.h * (i === 2 ? 0.66 : 0.52),
          transform: 'translateY(-50%)',
          textAlign: 'center',
          fontFamily: SANS,
          fontWeight: 700,
          fontSize: 112,
          lineHeight: 1,
          color: 'white',
          textShadow: '0 0 8px rgba(255,255,255,0.35)',
        }}
      >
        {t.n}
      </div>
    </div>
  );
};

// Flèches pointillées manuscrites, tracées de l'étage vers le libellé.
// Centres des tirets relevés sur l'image pleine résolution (798,0 s), dans l'ordre du tracé, puis spline Catmull-Rom.
const PTS: [number, number][][] = [
  [[578, 884], [568, 879], [546, 868], [521, 860], [494, 857], [468, 863], [445, 877], [424, 894], [400, 906], [373, 907], [353, 890], [343, 866], [337, 839], [335, 826]],
  [[1196, 654], [1205, 652], [1229, 647], [1256, 643], [1283, 640], [1307, 646], [1317, 667], [1302, 688], [1276, 689], [1259, 669], [1262, 642], [1278, 624], [1303, 614], [1330, 612], [1357, 610], [1384, 609], [1411, 609], [1438, 608], [1465, 606], [1492, 604], [1519, 602], [1546, 598], [1572, 592], [1597, 582], [1607, 576]],
  [[856, 443], [847, 440], [821, 432], [795, 425], [768, 420], [741, 421], [716, 429], [701, 448], [704, 473], [725, 489], [752, 491], [778, 484], [791, 462], [782, 437], [764, 418], [738, 412], [711, 414], [684, 418], [658, 423], [631, 428], [604, 432], [578, 437], [551, 440], [524, 443], [497, 445], [470, 444], [443, 441], [417, 434], [395, 420], [387, 412]],
];
const catmull = (p: [number, number][]) => {
  let d = `M ${p[0][0]} ${p[0][1]}`;
  for (let i = 0; i < p.length - 1; i++) {
    const p0 = p[Math.max(0, i - 1)];
    const p1 = p[i];
    const p2 = p[i + 1];
    const p3 = p[Math.min(p.length - 1, i + 2)];
    const c1 = [p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6];
    const c2 = [p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6];
    d += ` C ${c1[0].toFixed(1)} ${c1[1].toFixed(1)}, ${c2[0].toFixed(1)} ${c2[1].toFixed(1)}, ${p2[0]} ${p2[1]}`;
  }
  return d;
};
const PATHS = PTS.map(catmull);

const DashPath: React.FC<{i: number; p: number}> = ({i, p}) => {
  if (p <= 0.001) return null;
  const id = `m41_${i}`;
  return (
    <svg width={1920} height={1080} style={{position: 'absolute', left: 0, top: 0, overflow: 'visible', filter: 'drop-shadow(0 0 4px rgba(255,255,255,0.7))'}}>
      <defs>
        <mask id={id} maskUnits="userSpaceOnUse" x="0" y="0" width="1920" height="1080">
          <path d={PATHS[i]} fill="none" stroke="white" strokeWidth={14} pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - p} strokeLinecap="round" />
        </mask>
      </defs>
      <path d={PATHS[i]} fill="none" stroke="white" strokeWidth={4.2} strokeDasharray="16 10.5" strokeLinecap="round" mask={`url(#${id})`} />
    </svg>
  );
};

const LABELS = [
  {x: 130, y: 767, w: ['Un', 'agent', 'principal']},
  {x: 1272, y: 517, w: ['Sous-agents', 'spécialisés']},
  {x: 62, y: 348, w: ['Connecte-les', 'à', 'Telegram']},
];

const Label: React.FC<{f: number; i: number; starts: number[]}> = ({f, i, starts}) => {
  const L = LABELS[i];
  return (
    <div
      style={{
        position: 'absolute',
        left: L.x,
        top: L.y - 35,
        height: 70,
        display: 'flex',
        alignItems: 'center',
        fontFamily: SANS,
        fontWeight: 700,
        fontSize: 52,
        color: 'white',
        whiteSpace: 'nowrap',
        textShadow: '0 0 10px rgba(255,255,255,0.45)',
      }}
    >
      {L.w.map((w, j) => (
        <React.Fragment key={j}>
          <BlurWord f={f} start={starts[j]} dur={9} blur={10} rise={10}>
            {w}
          </BlurWord>
          {j < L.w.length - 1 ? ' ' : ''}
        </React.Fragment>
      ))}
    </div>
  );
};

type St = {f: number; titleOn: boolean; tops: number[]; paths: number[]; labels: (number[] | null)[]};
const Scene: React.FC<St> = ({f, titleOn, tops, paths, labels}) => (
  <AbsoluteFill>
    <NightBg />
    {[0, 1, 2].map((i) => (
      <Tier key={i} i={i} top={tops[i]} />
    ))}
    {paths.map((p, i) => (
      <DashPath key={i} i={i} p={p} />
    ))}
    {labels.map((s, i) => (s ? <Label key={i} f={f} i={i} starts={s} /> : null))}
    <SerifTitle f={titleOn ? f : 999} words={TITLE} starts={[48, 52, 56, 59, 62, 64]} size={141} top={16} dur={14} />
  </AbsoluteFill>
);

const FINAL = [803, 570, 290];
const DONE = [-99, -99, -99];

const Occ1: React.FC = () => {
  const f = useCurrentFrame();
  const tops = [keys(T1.pts, T1.ys, f), keys(T2.pts, T2.ys, f), keys(T3.pts, T3.ys, f)];
  return <Scene f={f} titleOn tops={tops} paths={[ease(f, 137, 160, 0, 1, Easing.inOut(Easing.sin)), 0, 0]} labels={[[158, 170, 182], null, null]} />;
};
const Occ2: React.FC = () => {
  const f = useCurrentFrame();
  return <Scene f={f} titleOn={false} tops={FINAL} paths={[1, ease(f, 4, 30, 0, 1, Easing.inOut(Easing.sin)), 0]} labels={[DONE, [48, 58], null]} />;
};
const Occ3: React.FC = () => {
  const f = useCurrentFrame();
  return <Scene f={f} titleOn={false} tops={FINAL} paths={[1, 1, ease(f, -5, 26, 0, 1, Easing.inOut(Easing.sin))]} labels={[DONE, DONE, [28, 38, 48]]} />;
};

// Bruitages (SFX-REGLES.md) : nappe à l'image 0 de chaque occurrence, grave à l'arrivée de chaque étage,
// whoosh au tracé de chaque flèche pointillée.
const O2 = D1 + GAP;
const O3 = O2 + D2 + GAP;
const CUES: SfxCue[] = [
  {frame: 0, name: 'nappe-ecran-titre'},
  {frame: 10, name: 'grave-apparition'}, // étage 1
  {frame: 17, name: 'grave-apparition'}, // étage 2
  {frame: 26, name: 'grave-apparition'}, // étage 3
  {frame: 137, name: 'whoosh-transition'}, // flèche 1
  {frame: O2, name: 'nappe-ecran-titre'},
  {frame: O2 + 4, name: 'whoosh-transition'}, // flèche 2
  {frame: O3, name: 'nappe-ecran-titre'},
  {frame: O3, name: 'whoosh-transition'}, // flèche 3 (déjà en cours de tracé à l'image 0)
];

const Comp: React.FC = () => {
  const seq: [number, React.ReactNode][] = [
    [D1, <Occ1 />],
    [GAP, <NightBg />],
    [D2, <Occ2 />],
    [GAP, <NightBg />],
    [D3, <Occ3 />],
  ];
  let t = 0;
  return (
    <AbsoluteFill style={{background: '#000'}}>
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
