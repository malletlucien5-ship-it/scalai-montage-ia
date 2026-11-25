import React from 'react';
import {AbsoluteFill, Easing, interpolate, useCurrentFrame} from '../../shared/rt';
import {INTER_L} from '../../shared/localFonts';
import {SfxTrack, SfxCue} from '../../shared/Sfx';

// d224 (plein cadre) : fond noir traversé d'un halo bleu en diagonale, icône d'app blanche à biseau chromé
// + pilule verre sombre dessous. Chez Dan : « Λ » + « apex.host/yt ». Ici : cerveau stylisé noir + « Second cerveau ».
// Réf. : coupe franche vers le fond 1119,43 s, icône et pilule floues -> nettes (~12 images), coupe franche 1121,47 s.
// Géométrie (1920x1080, 1119,8 s) : tuile 410 px centrée (960, 504) ; pilule centrée x 960, y 737..846 (h 109, rayon 24).
// Cible : « Un système de second cerveau qui connaît absolument tout sur vous. »
//   placé juste après les sous-titres « second cerveau » : sur « qui » (1196,98 s) jusqu'à « vous. » (1198,74 s).
const FPS = 30;
const AT = 1196.98;
const END = 1198.95;
const DUR = Math.round((END - AT) * FPS);
const IN0 = 1;
const IN_LEN = 12;
const SIZE = 410;
const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

const Background: React.FC = () => {
  const f = useCurrentFrame();
  const drift = f * 0.6;
  return (
    <AbsoluteFill style={{background: '#010102'}}>
      <svg width={1920} height={1080} style={{position: 'absolute', inset: 0}}>
        <defs>
          <linearGradient id="d224band" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="#0B2250" />
            <stop offset="0.45" stopColor="#063060" />
            <stop offset="0.75" stopColor="#0C2258" />
            <stop offset="1" stopColor="#2A1F70" />
          </linearGradient>
          <filter id="d224blur" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="70" />
          </filter>
        </defs>
        <path
          d={`M${1130 + drift} -150 C${1200 + drift} 250 ${1050 + drift} 700 ${720 + drift} 1250`}
          stroke="url(#d224band)"
          strokeWidth={330}
          fill="none"
          filter="url(#d224blur)"
          opacity={0.95}
        />
      </svg>
    </AbsoluteFill>
  );
};

// Cerveau stylisé (vue de côté, deux hémisphères, circonvolutions au trait).
const Brain: React.FC<{s: number}> = ({s}) => {
  const half = (
    <g>
      <path d="M50 17 C41 9 25 11 21 23 C11 25 6 37 11 46 C4 54 7 67 17 71 C18 81 29 88 38 83 C42 89 50 88 50 88" />
      <path d="M50 33 C43 29 35 33 35 40" />
      <path d="M21 23 C27 27 29 33 27 38" />
      <path d="M11 46 C18 47 24 51 24 58" />
      <path d="M50 57 C44 55 38 59 38 66" />
      <path d="M17 71 C24 70 28 72 30 77" />
    </g>
  );
  return (
    <svg width={s} height={s} viewBox="0 0 100 100" fill="none" stroke="#0E1626" strokeWidth={7.4} strokeLinecap="round" strokeLinejoin="round">
      {half}
      <g transform="translate(100 0) scale(-1 1)">{half}</g>
      <path d="M50 17 V88" />
    </svg>
  );
};

const Tile: React.FC = () => {
  const r = SIZE * 0.23;
  const ring = SIZE * 0.05;
  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        borderRadius: r,
        background:
          'linear-gradient(155deg, #ffffff 0%, #6f6f72 8%, #fafafa 16%, #3c3c3f 27%, #ececee 40%, #8d8d90 52%, #ffffff 64%, #404043 78%, #f4f4f4 90%, #7a7a7d 100%)',
        boxShadow: '0 16px 40px rgba(0,0,0,0.55), inset 0 0 0 2px rgba(40,40,42,0.75)',
      }}
    >
      <div
        style={{
          position: 'absolute',
          inset: ring,
          borderRadius: r - ring * 0.8,
          background: 'linear-gradient(180deg, #ededee 0%, #e2e2e4 55%, #d6d6d9 100%)',
          boxShadow: 'inset 0 0 0 2px rgba(30,30,32,0.5), inset 0 4px 8px rgba(255,255,255,0.9), inset 0 -10px 16px rgba(0,0,0,0.10)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <Brain s={236} />
      </div>
    </div>
  );
};

const IconeSecondCerveau: React.FC<{showPlate?: boolean}> = () => {
  const f = useCurrentFrame();
  const p = interpolate(f, [IN0, IN0 + IN_LEN], [0, 1], {...clamp, easing: Easing.out(Easing.cubic)});
  const look: React.CSSProperties = {
    opacity: p,
    transform: `scale(${1.08 - 0.08 * p})`,
    filter: p < 1 ? `blur(${((1 - p) * 20).toFixed(2)}px)` : undefined,
  };
  return (
    <AbsoluteFill style={{overflow: 'hidden'}}>
      <Background />
      <AbsoluteFill style={{...look, transformOrigin: '960px 560px'}}>
        <div style={{position: 'absolute', left: 960 - SIZE / 2, top: 504 - SIZE / 2, width: SIZE, height: SIZE}}>
          <Tile />
        </div>
        <div style={{position: 'absolute', left: 0, width: 1920, top: 737, display: 'flex', justifyContent: 'center'}}>
          <div
            style={{
              height: 109,
              padding: '0 34px',
              borderRadius: 24,
              background: 'linear-gradient(180deg, #4a505c 0%, #2c313b 35%, #1b1f28 70%, #14171e 100%)',
              boxShadow: 'inset 0 0 0 2px rgba(200,206,222,0.6), inset 0 3px 2px rgba(255,255,255,0.22), 0 10px 26px rgba(0,0,0,0.5)',
              display: 'flex',
              alignItems: 'center',
              fontFamily: INTER_L,
              fontWeight: 700,
              fontSize: 40,
              letterSpacing: -0.5,
              color: '#fff',
              whiteSpace: 'nowrap',
            }}
          >
            Second cerveau
          </div>
        </div>
      </AbsoluteFill>
      <SfxTrack cues={cuesExportees} />
    </AbsoluteFill>
  );
};

export const meta = {
  id: 'd224-icone-second-cerveau',
  fps: FPS,
  durationInFrames: DUR,
  defaultProps: {showPlate: true},
  occurrences: [{ref: [1119.43, 1121.47] as [number, number], at: AT, from: 0, durationInFrames: DUR, mode: 'plein' as const}],
};
export default IconeSecondCerveau;

// Signaux sonores exportés pour la bibliothèque (cloud/cues_globaux.py).
const cuesExportees: SfxCue[] = [{frame: IN0 + 1, name: 'grave-apparition'}];
export const cues = cuesExportees;
