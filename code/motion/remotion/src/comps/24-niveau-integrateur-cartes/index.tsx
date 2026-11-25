import React from 'react';
import {SfxTrack, SfxCue} from '../../shared/Sfx';
import {AbsoluteFill, Sequence, useCurrentFrame, Easing, interpolate} from '../../shared/rt';
import {SANS, ease, clamp, BlurWord} from './lib';

// 24 : « How to operate at Integrator level », 3 cartes lumineuses qui se remplissent.
// Réf. 297,00-302,14 / 312,28-314,85 / 321,95-325,46.
const D1 = 154;
const D2 = 77;
const D3 = 105;
const GAP = 15;
export const meta = {
  id: '24-niveau-integrateur-cartes',
  durationInFrames: D1 + D2 + D3 + 2 * GAP,
  fps: 30,
  occurrences: [
    {ref: [297.00, 302.14], from: 0, durationInFrames: D1, mode: 'plein' as const},
    {ref: [312.28, 314.85], from: D1 + GAP, durationInFrames: D2, mode: 'plein' as const},
    {ref: [321.95, 325.46], from: D1 + D2 + 2 * GAP, durationInFrames: D3, mode: 'plein' as const},
  ],
};

const BLUE = '#03A6FF';

const Bg: React.FC = () => (
  <AbsoluteFill
    style={{
      background:
        'radial-gradient(ellipse 900px 520px at 960px 330px, rgb(9,24,52) 0%, rgb(7,17,38) 45%, rgba(5,11,27,1) 100%), rgb(4,9,22)',
    }}
  />
);

const XS = [237, 730, 1223];
const CARD = {w: 462, h: 350, top: 427};
const TXT = [
  {v: 'Utiliser', n: ['Connecteurs']},
  {v: 'Créer', n: ['Visualisations']},
  {v: 'Créer', n: ['Artefacts', 'interactifs']},
];

const Card: React.FC<{f: number; i: number; appear: number; starts: number[] | null}> = ({f, i, appear, starts}) => {
  const p = ease(f, appear, appear + 8, 0, 1, Easing.out(Easing.quad));
  const t = TXT[i];
  return (
    <div
      style={{
        position: 'absolute',
        left: XS[i],
        top: CARD.top,
        width: CARD.w,
        height: CARD.h,
        borderRadius: 30,
        background: 'rgb(9,53,93)',
        border: '2px solid rgba(40,95,150,0.55)',
        boxShadow: '0 0 34px rgba(20,110,220,0.28), 0 0 90px rgba(10,80,190,0.14)',
        opacity: p,
        transform: `scale(${0.96 + 0.04 * p})`,
        filter: p < 0.99 ? `blur(${(1 - p) * 6}px)` : undefined,
      }}
    >
      <div
        style={{
          position: 'absolute',
          left: CARD.w / 2 - 48,
          top: 60,
          width: 96,
          height: 96,
          borderRadius: '50%',
          background: 'rgb(4,63,109)',
          border: '1.5px solid rgba(0,120,215,0.85)',
          boxShadow: '0 0 14px rgba(0,140,255,0.55), inset 0 0 10px rgba(0,120,230,0.35)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontFamily: SANS,
          fontWeight: 700,
          fontSize: 49,
          color: 'rgb(12,162,253)',
          textShadow: '0 0 10px rgba(12,162,253,0.6)',
        }}
      >
        {i + 1}
      </div>
      {starts && (
        <div style={{position: 'absolute', left: 0, width: CARD.w, top: 186, textAlign: 'center', fontFamily: SANS, whiteSpace: 'nowrap'}}>
          <div style={{fontWeight: 700, fontSize: 40, lineHeight: '50px', color: 'rgb(125,150,180)'}}>
            <BlurWord f={f} start={starts[0]} dur={8} blur={8}>
              {t.v}
            </BlurWord>
          </div>
          <div style={{fontWeight: 700, fontSize: 44, lineHeight: '64px', color: 'rgb(246,244,242)'}}>
            {t.n.map((w, j) => (
              <React.Fragment key={j}>
                <BlurWord f={f} start={starts[j + 1]} dur={8} blur={8}>
                  {w}
                </BlurWord>
                {j < t.n.length - 1 ? ' ' : ''}
              </React.Fragment>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

type St = {f: number; dur: number; titleIn: number; appear: number[]; texts: (number[] | null)[]; blurIn?: boolean};
const Scene: React.FC<St> = ({f, dur, titleIn, appear, texts, blurIn}) => {
  const zoom = interpolate(f, [0, dur], [1, 1.028], clamp);
  const tp = ease(f, titleIn, titleIn + 10, 0, 1, Easing.out(Easing.quad));
  const b = blurIn ? interpolate(f, [0, 1, 2, 3, 4, 5, 6, 7], [22, 21, 18, 12, 6, 3.5, 1.5, 0], clamp) : 0;
  return (
    <AbsoluteFill style={{filter: b > 0.05 ? `blur(${b}px)` : undefined}}>
      <Bg />
      <AbsoluteFill style={{transform: `scale(${zoom})`, transformOrigin: '960px 470px'}}>
        <div
          style={{
            position: 'absolute',
            top: 96,
            left: 0,
            right: 0,
            textAlign: 'center',
            fontFamily: SANS,
            fontWeight: 700,
            fontSize: 92,
            letterSpacing: 0,
            lineHeight: '116px',
            whiteSpace: 'nowrap',
            opacity: tp,
            filter: tp < 0.99 ? `blur(${(1 - tp) * 12}px)` : undefined,
          }}
        >
          <span style={{color: 'rgb(246,241,236)', textShadow: '0 0 12px rgba(255,255,255,0.25)'}}>Opérer au </span>
          <span style={{color: BLUE, textShadow: '0 0 14px rgba(3,166,255,0.75), 0 0 34px rgba(3,166,255,0.35)'}}>niveau Intégrateur</span>
        </div>
        {[0, 1, 2].map((i) => (
          <Card key={i} f={f} i={i} appear={appear[i]} starts={texts[i]} />
        ))}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

const P = -99;
const Occ1: React.FC = () => {
  const f = useCurrentFrame();
  return <Scene f={f} dur={D1} titleIn={7} appear={[37, 46, 55]} texts={[[92, 102], null, null]} />;
};
const Occ2: React.FC = () => {
  const f = useCurrentFrame();
  return <Scene f={f} dur={D2} titleIn={P} appear={[P, P, P]} texts={[[P, P], [23, 33], null]} />;
};
const Occ3: React.FC = () => {
  const f = useCurrentFrame();
  return <Scene f={f} dur={D3} titleIn={P} appear={[P, P, P]} texts={[[P, P], [P, P], [27, 34, 44]]} blurIn />;
};

// Bruitages (SFX-REGLES.md) : nappe à l'image 0 de chaque occurrence, grave à l'arrivée de chaque carte.
const O2 = D1 + GAP;
const O3 = O2 + D2 + GAP;
const CUES: SfxCue[] = [
  {frame: 0, name: 'nappe-ecran-titre'},
  {frame: 38, name: 'grave-apparition'}, // carte 1
  {frame: 47, name: 'grave-apparition'}, // carte 2
  {frame: 56, name: 'grave-apparition'}, // carte 3
  {frame: O2, name: 'nappe-ecran-titre'},
  {frame: O3, name: 'nappe-ecran-titre'},
];

const Comp: React.FC = () => {
  const seq: [number, React.ReactNode][] = [
    [D1, <Occ1 />],
    [GAP, <Bg />],
    [D2, <Occ2 />],
    [GAP, <Bg />],
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
