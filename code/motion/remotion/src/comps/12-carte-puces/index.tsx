import React from 'react';
import {AbsoluteFill, Easing, interpolate, useCurrentFrame} from '../../shared/rt';
import {Plate} from '../../shared/Plate';
import {SfxTrack, SfxCue} from '../../shared/Sfx';
import {INTER} from '../../shared/fonts';

// Référence : 89,623 s (coupe) à 95,362 s. Carte verre à droite, 4 puces qui apparaissent
// une par une : la sphère surgit, puis le mot se dévoile (fondu + flou qui se dissipe).
export const meta = {
  id: '12-carte-puces',
  durationInFrames: 172,
  fps: 30,
  defaultProps: {showPlate: true},
  occurrences: [{ref: [89.623, 95.357], from: 0, durationInFrames: 172, mode: 'overlay'}],
};

// Bruitages : grave-apparition à l'arrivée de la carte, puis sur chaque puce.
const SFX: SfxCue[] = [
  {frame: 0, name: 'grave-apparition'},
  {frame: 4, name: 'grave-apparition'},
  {frame: 36, name: 'grave-apparition'},
  {frame: 70, name: 'grave-apparition'},
  {frame: 115, name: 'grave-apparition'},
];

const CARD = {x: 1194, y: 97, w: 606, h: 850};
const ROWS = [203, 413, 623, 831]; // centres verticaux des lignes (px absolus)
// [image d'apparition de la sphère, image de début du mot]
const TIMING: [number, number][] = [
  [4, 10],
  [36, 52],
  [70, 95],
  [115, 138],
];
const WORDS = ['Rôle', 'Initiative', 'Client', 'Processus'];

const cl = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

const Bullet: React.FC<{cy: number; f: number; start: number}> = ({cy, f, start}) => {
  const sc = interpolate(f, [start, start + 3, start + 5], [0, 1.08, 1], {...cl, easing: Easing.out(Easing.quad)});
  return (
    <div
      style={{
        position: 'absolute',
        left: 1306 - CARD.x - 28,
        top: cy - CARD.y - 28,
        width: 56,
        height: 56,
        borderRadius: 28,
        transform: `scale(${sc})`,
        background: 'linear-gradient(180deg, rgb(122,246,248) 0%, rgb(100,195,215) 35%, rgb(80,130,170) 65%, rgb(60,72,120) 100%)',
        boxShadow: '0 0 10px rgba(90,210,235,0.25)',
      }}
    />
  );
};

const Word: React.FC<{cy: number; f: number; start: number; text: string}> = ({cy, f, start, text}) => {
  const p = interpolate(f, [start - 1, start + 4], [0, 1], cl);
  const blur = interpolate(f, [start, start + 7], [3, 0], {...cl, easing: Easing.out(Easing.quad)});
  const dy = interpolate(f, [start, start + 14], [16, 0], {...cl, easing: Easing.out(Easing.cubic)});
  return (
    <div
      style={{
        position: 'absolute',
        left: 1366 - CARD.x,
        top: cy - CARD.y - 50 + dy,
        height: 100,
        lineHeight: '100px',
        fontSize: 73,
        fontWeight: 800,
        letterSpacing: -0.5,
        color: '#fff',
        whiteSpace: 'nowrap',
        opacity: p,
        filter: blur > 0.05 ? `blur(${blur}px)` : undefined,
        textShadow: '0 0 10px rgba(255,255,255,0.55), 0 0 26px rgba(200,235,255,0.25)',
      }}
    >
      {text}
    </div>
  );
};

const CartePuces: React.FC<{showPlate?: boolean}> = ({showPlate = true}) => {
  const f = useCurrentFrame();
  const bgA = interpolate(f, [0, 17], [0.2, 1], {...cl, easing: Easing.inOut(Easing.quad)});
  const op = interpolate(f, [0, 3], [0.4, 1], cl);
  const ty = interpolate(f, [0, 16], [36, 0], {...cl, easing: Easing.out(Easing.cubic)});
  const blur = interpolate(f, [0, 12], [5, 0], cl);
  return (
    <AbsoluteFill style={{fontFamily: INTER}}>
      <Plate show={showPlate} />
      <SfxTrack cues={SFX} />
      <div
        style={{
          position: 'absolute',
          left: CARD.x,
          top: CARD.y,
          width: CARD.w,
          height: CARD.h,
          opacity: op,
          transform: `translateY(${ty}px)`,
          filter: blur > 0.05 ? `blur(${blur}px)` : undefined,
        }}
      >
        {/* halo externe */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            borderRadius: 24,
            boxShadow: '0 0 40px rgba(60,190,220,0.18), 0 0 90px rgba(40,150,200,0.1)',
            opacity: bgA,
          }}
        />
        {/* verre dépoli puis fond marine */}
        <div style={{position: 'absolute', inset: 0, borderRadius: 24, overflow: 'hidden', backdropFilter: 'blur(22px)'}}>
          <div
            style={{
              position: 'absolute',
              inset: 0,
              opacity: bgA,
              // reflet diagonal : profil mesuré sur l'original le long de l'axe 155,8°
              background: 'linear-gradient(155.8deg, rgb(3,26,46) 0%, rgb(3,26,46) 4%, rgb(5,30,52) 8%, rgb(6,34,55) 12%, rgb(8,41,63) 16%, rgb(10,48,71) 20%, rgb(13,55,80) 24%, rgb(16,64,89) 28%, rgb(18,70,95) 31%, rgb(16,66,92) 34%, rgb(13,57,82) 38%, rgb(10,48,71) 42%, rgb(8,39,62) 46%, rgb(6,34,55) 50%, rgb(5,30,52) 54%, rgb(2,26,46) 58%, rgb(2,22,43) 64%, rgb(2,22,43) 100%)',
            }}
          />
          <div
            style={{
              position: 'absolute',
              inset: 0,
              opacity: 1 - bgA,
              background: 'rgba(120,90,140,0.22)',
            }}
          />
        </div>
        <div style={{position: 'absolute', inset: 0, borderRadius: 24, border: '2px solid rgba(96,160,172,0.85)'}} />
        {ROWS.map((cy, i) => (
          <React.Fragment key={i}>
            <Bullet cy={cy} f={f} start={TIMING[i][0]} />
            <Word cy={cy} f={f} start={TIMING[i][1]} text={WORDS[i]} />
          </React.Fragment>
        ))}
      </div>
    </AbsoluteFill>
  );
};

export default CartePuces;

// Signaux sonores exportés pour la bibliothèque (cloud/cues_globaux.py).
export const cues = SFX;
