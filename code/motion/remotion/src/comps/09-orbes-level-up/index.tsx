import React from 'react';
import {SfxTrack, SfxCue} from '../../shared/Sfx';
import {AbsoluteFill, Sequence, useCurrentFrame, Easing, interpolate} from '../../shared/rt';
import {NightBg, SerifTitle, Sphere, RingArc, SANS, ease, clamp, BlurWord} from './lib';

// 09 : orbes « Level Up from Amateur » (réf. 46,07-51,42 s puis 61,93-65,43 s).
const OCC1 = 160;
const GAP = 15;
const OCC2 = 105;
export const meta = {
  id: '09-orbes-level-up',
  durationInFrames: OCC1 + GAP + OCC2,
  fps: 30,
  occurrences: [
    {ref: [46.08, 51.42], from: 0, durationInFrames: OCC1, mode: 'plein' as const},
    {ref: [61.93, 65.43], from: OCC1 + GAP, durationInFrames: OCC2, mode: 'plein' as const},
  ],
};

const R = 225; // rayon de base mesuré
const ARC_R = 271;
const X1 = 488;
const X2 = 1362;
const CY = 540;
const ACTIVE = 1.44;

const TITLE = ['Passer', 'le', 'cap', 'Amateur'];

const Digit: React.FC<{n: string; o: number}> = ({n, o}) => (
  <div
    style={{
      fontFamily: SANS,
      fontWeight: 700,
      fontSize: 322,
      lineHeight: 1,
      color: 'white',
      opacity: o,
      marginTop: 6,
      textShadow: '0 0 10px rgba(255,255,255,0.75), 0 0 28px rgba(150,210,255,0.55)',
    }}
  >
    {n}
  </div>
);

// Texte de l'orbe actif, mot par mot, en fondu flouté.
const OrbText: React.FC<{f: number; lines: string[][]; starts: number[]; blur?: number; dim?: number}> = ({f, lines, starts, blur = 0, dim = 1}) => {
  let k = 0;
  return (
    <div
      style={{
        fontFamily: SANS,
        fontWeight: 700,
        fontSize: 57,
        lineHeight: 1.33,
        color: 'white',
        textAlign: 'center',
        whiteSpace: 'nowrap',
        textShadow: '0 0 8px rgba(255,255,255,0.55), 0 0 18px rgba(160,210,255,0.4)',
        filter: blur > 0 ? `blur(${blur}px)` : undefined,
        opacity: dim,
        letterSpacing: 0.3,
        marginTop: -6,
      }}
    >
      {lines.map((ln, i) => (
        <div key={i}>
          {ln.map((w, j) => {
            const s = starts[k++];
            return (
              <React.Fragment key={j}>
                <BlurWord f={f} start={s} dur={7} blur={8} rise={25}>
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

const Orb: React.FC<{x: number; y: number; s: number; arc: React.ReactNode; children: React.ReactNode}> = ({x, y, s, arc, children}) => (
  <div style={{position: 'absolute', left: x, top: y, transform: `scale(${s})`}}>
    <Sphere r={R}>{children}</Sphere>
    {arc}
  </div>
);

const T1 = ['Force', 'Claude'];
const T1b = ['à', "t'interroger"];
const T2b = ['à', 'se', 'relire'];

const Occ1: React.FC = () => {
  const f = useCurrentFrame();
  // montée de la sphère : approche exponentielle mesurée (k = 0,128 / image)
  const rise = f < 3 ? 9999 : 673 * Math.exp(-0.128 * (f - 8));
  const baseY = CY + rise;
  // séparation 1 | 2
  const sp = f < 41 ? 0 : (1 - Math.exp(-0.118 * (f - 41))) * interpolate(f, [41, 44], [0.6, 1], clamp);
  const x1 = 960 + (X1 - 960) * sp;
  const x2 = 960 + (X2 - 960) * sp;
  const arc1 = ease(f, 25, 60, 0, 1, Easing.inOut(Easing.sin));
  const arc2 = ease(f, 45, 63, 0, 1, Easing.inOut(Easing.sin));
  // morph de l'orbe 1
  const d1 = ease(f, 96, 104, 1, 0, Easing.inOut(Easing.quad));
  const g1 = ease(f, 100, 118, 1, 1.35, Easing.out(Easing.cubic)) + ease(f, 118, 148, 0, ACTIVE - 1.35, Easing.out(Easing.quad));
  const dy1 = 0;
  const dy2 = ease(f, 110, 150, 0, 42, Easing.out(Easing.cubic));
  return (
    <AbsoluteFill>
      <NightBg />
      <SerifTitle f={f} words={TITLE} starts={[0, 5, 11, 18]} size={94} top={29} dur={14} />
      {f >= 36 && (
        <Orb x={x2} y={baseY + dy2} s={1} arc={<RingArc R={ARC_R} side="top" from="right" p={arc2} />}>
          <Digit n="2" o={1} />
        </Orb>
      )}
      <Orb x={x1} y={baseY + dy1} s={g1} arc={<RingArc R={ARC_R} side="bottom" from="left" p={arc1} />}>
        <div style={{position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
          <Digit n="1" o={d1} />
        </div>
        <div style={{position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
          <OrbText f={f} lines={[T1, T1b]} starts={[104, 110, 117, 123]} />
        </div>
      </Orb>
    </AbsoluteFill>
  );
};

const Occ2: React.FC = () => {
  const f = useCurrentFrame();
  const inBlur = interpolate(f, [0, 6], [22, 0], {...clamp, easing: Easing.out(Easing.quad)});
  const s1 = ease(f, 0, 16, 1.32, 1, Easing.out(Easing.quad));
  const dy1 = 0;
  const t1blur = ease(f, 44, 60, 0, 4.5);
  const t1dim = ease(f, 44, 60, 1, 0.72);
  const s2 = ease(f, 17, 35, 1, 1.35, Easing.out(Easing.cubic)) + ease(f, 35, 50, 0, ACTIVE - 1.35, Easing.out(Easing.quad));
  const dy2 = ease(f, 17, 45, 42, 58, Easing.out(Easing.cubic));
  const d2 = ease(f, 22, 37, 1, 0, Easing.inOut(Easing.quad));
  return (
    <AbsoluteFill style={{filter: inBlur > 0.05 ? `blur(${inBlur}px)` : undefined}}>
      <NightBg />
      <SerifTitle f={99} words={TITLE} starts={[0, 0, 0, 0]} size={94} top={29} />
      <Orb x={X2} y={CY + dy2} s={s2} arc={<RingArc R={ARC_R} side="top" from="right" p={1} />}>
        <div style={{position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
          <Digit n="2" o={d2} />
        </div>
        <div style={{position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
          <OrbText f={f} lines={[T1, T2b]} starts={[36, 45, 53, 53, 53]} />
        </div>
      </Orb>
      <Orb x={X1} y={CY + dy1} s={s1} arc={<RingArc R={ARC_R} side="bottom" from="left" p={1} />}>
        <OrbText f={99} lines={[T1, T1b]} starts={[0, 0, 0, 0]} blur={t1blur} dim={t1dim} />
      </Orb>
    </AbsoluteFill>
  );
};

// Bruitages (SFX-REGLES.md) : nappe à l'image 0 de chaque occurrence, grave à l'arrivée de chaque sphère,
// pop quand le libellé remplace le chiffre.
const CUES: SfxCue[] = [
  {frame: 0, name: 'nappe-ecran-titre'},
  {frame: 7, name: 'grave-apparition'}, // sphère 1 entre par le bas
  {frame: 43, name: 'grave-apparition'}, // sphère 2 sort de derrière la 1
  {frame: 104, name: 'pop'}, // libellé 1 remplace le chiffre
  {frame: OCC1 + GAP, name: 'nappe-ecran-titre'},
  {frame: OCC1 + GAP + 36, name: 'pop'}, // libellé 2 remplace le chiffre
];

const Comp: React.FC = () => (
  <AbsoluteFill style={{background: 'rgb(22,26,40)'}}>
    <Sequence durationInFrames={OCC1}>
      <Occ1 />
    </Sequence>
    <Sequence from={OCC1} durationInFrames={GAP}>
      <NightBg />
    </Sequence>
    <Sequence from={OCC1 + GAP} durationInFrames={OCC2}>
      <Occ2 />
    </Sequence>
    <SfxTrack cues={CUES} />
  </AbsoluteFill>
);
export default Comp;

// Signaux sonores exportés pour la bibliothèque (cloud/cues_globaux.py).
export const cues = CUES;
