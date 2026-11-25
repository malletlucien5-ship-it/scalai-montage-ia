import React from 'react';
import {SfxTrack, SfxCue} from '../../shared/Sfx';
import {AbsoluteFill, Sequence, useCurrentFrame, Easing, interpolate} from '../../shared/rt';
import {NightBg, SerifTitle, SERIF, SANS, ease, clamp, BlurWord} from './lib';

// 37 : « The 3 Categories Inside Claude Code », sphère violette, anneau, Loops / Tools / Apps.
// Réf. 615,78-622,05 / 635,53-637,80 / 647,41-649,45.
const D1 = 188;
const D2 = 68;
const D3 = 61;
const GAP = 15;
export const meta = {
  id: '37-orbe-arc-categories',
  durationInFrames: D1 + D2 + D3 + 2 * GAP,
  fps: 30,
  occurrences: [
    {ref: [615.78, 622.05], from: 0, durationInFrames: D1, mode: 'plein' as const},
    {ref: [635.53, 637.80], from: D1 + GAP, durationInFrames: D2, mode: 'plein' as const},
    {ref: [647.41, 649.45], from: D1 + D2 + 2 * GAP, durationInFrames: D3, mode: 'plein' as const},
  ],
};

const CX = 955;
const CY = 537;
const R = 267;
const RING = 315;
const TITLE = ['Les', '3', 'catégories', 'dans', 'Claude', 'Code'];

const sphereStyle = (r: number): React.CSSProperties => ({
  position: 'absolute',
  left: -r,
  top: -r,
  width: 2 * r,
  height: 2 * r,
  borderRadius: '50%',
  background: [
    `radial-gradient(circle at 50% 22%, rgba(95,125,255,0.9) 0%, rgba(90,115,255,0.35) 30%, rgba(90,115,255,0) 55%)`,
    'linear-gradient(180deg, rgb(120,140,255) 0%, rgb(86,113,255) 12%, rgb(79,103,253) 24%, rgb(72,92,236) 34%, rgb(64,82,203) 43%, rgb(59,72,172) 53%, rgb(52,63,140) 62%, rgb(47,55,119) 72%, rgb(43,49,107) 82%, rgb(38,42,92) 92%, rgb(34,36,80) 100%)',
  ].join(', '),
  boxShadow: [
    `inset 0 -${r * 0.05}px ${r * 0.08}px rgba(20,22,60,0.55)`,
    `0 -${r * 0.05}px ${r * 0.3}px rgba(70,85,255,0.35)`,
    `0 ${r * 0.05}px ${r * 0.15}px rgba(0,0,0,0.45)`,
  ].join(', '),
});


// Liserés relevés par angle sur la référence (0° = haut, sens horaire).
// A : large reflet lavande sur le haut. B : liseré bleu saturé étroit en bas à gauche.
const conic = (stops: [number, number, number, number][]) =>
  `conic-gradient(from 0deg at 50% 50%, ${[...stops, stops[0]].map((c, i) => `rgba(${c[0]},${c[1]},${c[2]},${c[3]}) ${i * 30}deg`).join(', ')})`;
const RIM_A = conic([
  [178, 195, 255, 1], [136, 156, 252, 1], [85, 108, 253, 0.6], [56, 66, 171, 0], [36, 41, 110, 0], [29, 33, 90, 0],
  [33, 37, 110, 0], [40, 48, 152, 0], [64, 75, 215, 0], [126, 137, 255, 0.9], [160, 176, 255, 1], [180, 198, 255, 1],
]);
const RIM_B = conic([
  [0, 0, 0, 0], [0, 0, 0, 0], [70, 90, 230, 0.3], [56, 66, 171, 0.85], [36, 41, 110, 0.85], [29, 33, 90, 0.85],
  [33, 37, 112, 0.95], [42, 49, 154, 1], [66, 76, 218, 1], [118, 132, 252, 0.7], [0, 0, 0, 0], [0, 0, 0, 0],
]);
const MASK_A = 'radial-gradient(circle closest-side, rgba(0,0,0,0) 74%, rgba(0,0,0,0.35) 85%, rgba(0,0,0,0.55) 90.6%, rgba(0,0,0,0.75) 94.3%, rgba(0,0,0,0.88) 96.6%, #000 98.5%)';
const MASK_B = 'radial-gradient(circle closest-side, rgba(0,0,0,0) 91.5%, rgba(0,0,0,0.6) 95%, #000 97.5%)';

const Orb: React.FC<{r: number}> = ({r}) => (
  <div style={{...sphereStyle(r), overflow: 'hidden'}}>
    <div
      style={{
        position: 'absolute',
        inset: 0,
        borderRadius: '50%',
        background: [
          'radial-gradient(ellipse 72% 34% at 50% 4%, rgba(225,230,255,0.34) 0%, rgba(154,170,255,0.16) 42%, rgba(110,130,255,0) 76%)',
          'radial-gradient(ellipse 84% 30% at 50% 98%, rgba(17,20,62,0.56) 0%, rgba(29,34,91,0.18) 62%, rgba(29,34,91,0) 100%)',
        ].join(', '),
      }}
    />
    <div style={{position: 'absolute', inset: 0, borderRadius: '50%', background: RIM_A, WebkitMaskImage: MASK_A, maskImage: MASK_A}} />
    <div style={{position: 'absolute', inset: 0, borderRadius: '50%', background: RIM_B, WebkitMaskImage: MASK_B, maskImage: MASK_B}} />
  </div>
);

const Node: React.FC<{x: number; y: number; r: number; s: number}> = ({x, y, r, s}) => (
  <div style={{position: 'absolute', left: x, top: y, transform: `scale(${s})`}}>
    <Orb r={r} />
  </div>
);

// Chiffre italique puis libellé, au même emplacement.
const Tag: React.FC<{
  f: number; x: number; y: number; align: 'right' | 'left' | 'center'; num: string; numIn: number; numOut: number; label: string; labelIn: number;
}> = ({f, x, y, align, num, numIn, numOut, label, labelIn}) => {
  const nIn = ease(f, numIn, numIn + 9, 0, 1);
  const nOut = ease(f, numOut, numOut + 7, 1, 0, Easing.in(Easing.quad));
  const n = Math.min(nIn, nOut);
  const box: React.CSSProperties = {
    position: 'absolute',
    top: y - 40,
    height: 80,
    display: 'flex',
    alignItems: 'center',
    whiteSpace: 'nowrap',
    ...(align === 'right' ? {right: 1920 - x, justifyContent: 'flex-end'} : align === 'left' ? {left: x} : {left: x - 300, width: 600, justifyContent: 'center'}),
  };
  const numX = align === 'right' ? {right: 1920 - x + 0} : align === 'left' ? {left: x} : {left: x - 300, width: 600, justifyContent: 'center'};
  return (
    <>
      <div style={{...box, ...numX}}>
        <span
          style={{
            fontFamily: SERIF,
            fontStyle: 'italic',
            fontSize: 60,
            color: 'rgb(225,228,245)',
            opacity: n,
            filter: `blur(${(1 - nIn) * 8}px)`,
            textShadow: '0 0 8px rgba(200,210,255,0.35)',
          }}
        >
          {num}
        </span>
      </div>
      <div style={box}>
        <BlurWord f={f} start={labelIn} dur={9} blur={10}>
          <span
            style={{
              fontFamily: SANS,
              fontWeight: 700,
              fontSize: 52,
              color: 'white',
              textShadow: '0 0 10px rgba(255,255,255,0.55), 0 0 22px rgba(170,190,255,0.35)',
            }}
          >
            {label}
          </span>
        </BlurWord>
      </div>
    </>
  );
};

type Cfg = {
  f: number; titleOn: boolean; y: number; s: number; ring: number; nodes: [number, number, number];
  nums: [number, number, number]; outs: [number, number, number]; labels: [number, number, number];
};

const Diagram: React.FC<Cfg> = ({f, titleOn, y, s, ring, nodes, nums, outs, labels}) => {
  const d = `M ${-RING} 0 A ${RING} ${RING} 0 0 0 ${RING} 0`;
  return (
    <AbsoluteFill>
      <NightBg />
      <SerifTitle f={titleOn ? f : 999} words={TITLE} starts={[0, 5, 10, 15, 20, 23]} size={120} top={27} dur={12} />
      <div style={{position: 'absolute', left: CX, top: y, transform: `scale(${s})`}}>
        <Orb r={R} />
        {ring > 0.001 && (
          <svg
            width={800}
            height={800}
            viewBox="-400 -400 800 800"
            style={{position: 'absolute', left: -400, top: -400, overflow: 'visible', filter: 'drop-shadow(0 0 7px rgba(255,255,255,0.8)) drop-shadow(0 0 18px rgba(200,210,255,0.4))'}}
          >
            <path d={d} fill="none" stroke="white" strokeWidth={10} pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - ring} />
          </svg>
        )}
        <Node x={-314} y={3} r={25} s={nodes[0]} />
        <Node x={5} y={313} r={30} s={nodes[1]} />
        <Node x={315} y={3} r={20} s={nodes[2]} />
        <div style={{position: 'absolute', left: -CX, top: -CY, width: 1920, height: 1080}}>
          <Tag f={f} x={617} y={590} align="right" num="1" numIn={nums[0]} numOut={outs[0]} label="Boucles" labelIn={labels[0]} />
          <Tag f={f} x={960} y={913} align="center" num="2" numIn={nums[1]} numOut={outs[1]} label="Outils" labelIn={labels[1]} />
          <Tag f={f} x={1290} y={590} align="left" num="3" numIn={nums[2]} numOut={outs[2]} label="Applications" labelIn={labels[2]} />
        </div>
      </div>
    </AbsoluteFill>
  );
};

const NEVER = 99999;
const pop = (f: number, s: number) =>
  interpolate(f, [s, s + 5, s + 8], [0, 1.15, 1], {...clamp, easing: Easing.out(Easing.quad)});

const Occ1: React.FC = () => {
  const f = useCurrentFrame();
  const y = f < 48 ? CY + 930 * Math.pow(1 - interpolate(f, [7, 48], [0, 1], clamp), 2) : CY;
  const s = ease(f, 50, 140, 0.84, 1, Easing.inOut(Easing.sin));
  const ring = ease(f, 28, 64, 0, 1, Easing.inOut(Easing.sin));
  return (
    <Diagram
      f={f}
      titleOn
      y={y}
      s={s}
      ring={ring}
      nodes={[pop(f, 46), pop(f, 52), pop(f, 60)]}
      nums={[55, 60, 68]}
      outs={[133, NEVER, NEVER]}
      labels={[143, NEVER, NEVER]}
    />
  );
};

const Occ2: React.FC = () => {
  const f = useCurrentFrame();
  return <Diagram f={f} titleOn={false} y={CY} s={1} ring={1} nodes={[1, 1, 1]} nums={[NEVER, -99, -99]} outs={[-99, 6, NEVER]} labels={[-99, 16, NEVER]} />;
};

const Occ3: React.FC = () => {
  const f = useCurrentFrame();
  return <Diagram f={f} titleOn={false} y={CY} s={1} ring={1} nodes={[1, 1, 1]} nums={[NEVER, NEVER, -99]} outs={[-99, -99, 2]} labels={[-99, -99, 17]} />;
};

// Bruitages (SFX-REGLES.md) : nappe à l'image 0 de chaque occurrence, grave à l'arrivée de la sphère,
// pop sur chaque nœud qui s'allume et sur chaque libellé qui remplace un chiffre.
const O2 = D1 + GAP;
const O3 = O2 + D2 + GAP;
const CUES: SfxCue[] = [
  {frame: 0, name: 'nappe-ecran-titre'},
  {frame: 11, name: 'grave-apparition'}, // sphère entre par le bas
  {frame: 46, name: 'pop'}, // nœud gauche
  {frame: 52, name: 'pop'}, // nœud bas
  {frame: 60, name: 'pop'}, // nœud droit
  {frame: 143, name: 'pop'}, // « Boucles » remplace 1
  {frame: O2, name: 'nappe-ecran-titre'},
  {frame: O2 + 16, name: 'pop'}, // « Outils » remplace 2
  {frame: O3, name: 'nappe-ecran-titre'},
  {frame: O3 + 17, name: 'pop'}, // « Apps » remplace 3
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
