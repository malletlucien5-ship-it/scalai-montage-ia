import React from 'react';
import {AbsoluteFill, Easing, Img, Sequence, interpolate, staticFile, useCurrentFrame} from '../../shared/rt';
import {Plate} from '../../shared/Plate';
import {SfxTrack, SfxCue} from '../../shared/Sfx';
import {INTER} from '../../shared/fonts';

// Référence : occurrence A 777,11 s à 780,94 s (Léo, ex-Kai), occurrence B 799,465 s à 803,736 s (Grégoire, ex-Reese).
// Portrait rond à lueur violette qui sort du flou, puis bulle dégradée qui se pose en se précisant.
const A_LEN = 115;
const B_LEN = 128;
const GAP = 15;
export const meta = {
  id: '42-avatar-bulle',
  durationInFrames: A_LEN + GAP + B_LEN,
  fps: 30,
  defaultProps: {showPlate: true},
  occurrences: [
    {ref: [777.11, 780.943], from: 0, durationInFrames: A_LEN, mode: 'overlay'},
    {ref: [799.465, 803.732], from: A_LEN + GAP, durationInFrames: B_LEN, mode: 'overlay'},
  ],
};

// Bruitages : grave-apparition au portrait, notification à la bulle (occurrence B décalée de A_LEN + GAP).
const SFX: SfxCue[] = [
  {frame: 12, name: 'grave-apparition'},
  {frame: 51, name: 'notification'},
  {frame: A_LEN + GAP + 1, name: 'grave-apparition'},
  {frame: A_LEN + GAP + 50, name: 'notification'},
];

const C = {cx: 1247, cy: 346, r: 238};
const cl = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

type Occ = {
  img: string;
  text: string;
  inStart: number; // début d'apparition du portrait
  bubStart: number; // début d'apparition de la bulle
  outStart?: number; // début de la sortie
  bub: {x: number; y: number; w: number; h: number; font: number; padL: number; right: string};
  // cadrage relevé sur l'original : taille de l'image et décalage dans le cercle de 476 px
  img_d: number;
  img_x: number;
  img_y: number;
  glowA: number;
};

const OCC_A: Occ = {
  img: '42/leo.jpg',
  text: "Salut Lucien, c'est moi, Léo !",
  inStart: 11,
  bubStart: 50,
  outStart: 88,
  bub: {x: 1358, y: 428, w: 506, h: 116, font: 29.5, padL: 40, right: 'rgb(238,140,219)'},
  img_d: 523,
  img_x: -45,
  img_y: -21,
  glowA: 0.8,
};
const OCC_B: Occ = {
  img: '42/gregoire.jpg',
  text: 'Lucien, belle affaire trouvée.',
  inStart: 0,
  bubStart: 49,
  bub: {x: 1336, y: 428, w: 550, h: 132, font: 35.5, padL: 48, right: 'rgb(245,110,212)'},
  img_d: 593,
  img_x: -78,
  img_y: -11,
  glowA: 0.95,
};

const AvatarBulle: React.FC<{occ: Occ}> = ({occ}) => {
  const f = useCurrentFrame();
  // portrait : fondu et flou qui se dissipe
  const pIn = interpolate(f, [occ.inStart, occ.inStart + 16], [0, 1], {...cl, easing: Easing.out(Easing.quad)});
  const pOp = interpolate(f, [occ.inStart, occ.inStart + 8], [0, 1], cl);
  // bulle : monte de 16 px, flou puis net
  const bIn = interpolate(f, [occ.bubStart, occ.bubStart + 12], [0, 1], {...cl, easing: Easing.out(Easing.cubic)});
  const bOp = interpolate(f, [occ.bubStart, occ.bubStart + 5], [0, 1], cl);
  // sortie : tout se floute et s'efface
  const out = occ.outStart === undefined ? 0 : interpolate(f, [occ.outStart, occ.outStart + 22], [0, 1], {...cl, easing: Easing.in(Easing.quad)});
  const outOp = 1 - interpolate(f, [(occ.outStart ?? 1e9) + 6, (occ.outStart ?? 1e9) + 22], [0, 1], cl);
  const pBlur = (1 - pIn) * 14 + out * 12;
  const bBlur = (1 - bIn) * 10 + out * 10;
  const b = occ.bub;
  return (
    <AbsoluteFill style={{fontFamily: INTER, opacity: outOp}}>
      {/* portrait */}
      <div
        style={{
          position: 'absolute',
          left: C.cx - C.r,
          top: C.cy - C.r,
          width: C.r * 2,
          height: C.r * 2,
          opacity: pOp,
          filter: pBlur > 0.05 ? `blur(${pBlur}px)` : undefined,
        }}
      >
        <div
          style={{
            position: 'absolute',
            inset: 0,
            borderRadius: '50%',
            // lueur violette mesurée : environ 0,38 au bord, nulle à 26 px
            boxShadow: `0 0 40px 0 rgba(95,70,250,${occ.glowA})`,
          }}
        />
        <div style={{position: 'absolute', inset: 0, borderRadius: '50%', overflow: 'hidden'}}>
          <Img
            src={staticFile(occ.img)}
            style={{position: 'absolute', left: occ.img_x, top: occ.img_y, width: occ.img_d, height: occ.img_d}}
          />
        </div>
        <div style={{position: 'absolute', inset: 0, borderRadius: '50%', border: '2.5px solid rgba(236,228,250,0.95)'}} />
      </div>
      {/* bulle */}
      <div
        style={{
          position: 'absolute',
          left: b.x,
          top: b.y + (1 - bIn) * 16,
          width: b.w,
          height: b.h,
          opacity: bOp,
          filter: bBlur > 0.05 ? `blur(${bBlur}px)` : undefined,
        }}
      >
        <div
          style={{
            position: 'absolute',
            inset: 0,
            borderRadius: 30,
            boxShadow: '0 0 28px 0 rgba(115,70,240,0.9)',
          }}
        />
        {/* queue en bas à gauche */}
        <svg style={{position: 'absolute', left: -32, top: b.h - 34, overflow: 'visible'}} width={60} height={36}>
          <path d="M60 0 C48 14 30 24 0 30 C28 32 48 30 60 22 Z" fill="rgb(128,118,248)" />
        </svg>
        <div
          style={{
            position: 'absolute',
            inset: 0,
            borderRadius: 30,
            background: `linear-gradient(98deg, rgb(132,120,250) 0%, rgb(160,112,240) 30%, rgb(198,114,228) 62%, ${b.right} 100%)`,
            overflow: 'hidden',
          }}
        >
          <div style={{position: 'absolute', inset: 0, background: 'linear-gradient(180deg, rgba(255,255,255,0.10) 0%, rgba(255,255,255,0) 50%, rgba(40,0,80,0.06) 100%)'}} />
        </div>
        <div
          style={{
            position: 'absolute',
            left: b.padL,
            top: 0,
            height: b.h,
            display: 'flex',
            alignItems: 'center',
            fontSize: b.font,
            fontWeight: 400,
            color: '#fff',
            whiteSpace: 'nowrap',
            letterSpacing: -0.2,
          }}
        >
          {occ.text}
        </div>
      </div>
    </AbsoluteFill>
  );
};

const Comp: React.FC<{showPlate?: boolean}> = ({showPlate = true}) => (
  <AbsoluteFill>
    <Plate show={showPlate} />
    <SfxTrack cues={SFX} />
    <Sequence durationInFrames={A_LEN}>
      <AvatarBulle occ={OCC_A} />
    </Sequence>
    <Sequence from={A_LEN + GAP} durationInFrames={B_LEN}>
      <AvatarBulle occ={OCC_B} />
    </Sequence>
  </AbsoluteFill>
);

export default Comp;

// Signaux sonores exportés pour la bibliothèque (cloud/cues_globaux.py).
export const cues = SFX;
