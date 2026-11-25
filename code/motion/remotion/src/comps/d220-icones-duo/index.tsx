import React from 'react';
import {AbsoluteFill, Easing, interpolate, useCurrentFrame} from '../../shared/rt';
import {siOpenai} from 'simple-icons';
import {Plate} from '../../shared/Plate';
import {SfxTrack, SfxCue} from '../../shared/Sfx';

// d220 : icône Grok (fantôme blanc sur tuile noire) à gauche, icône OpenAI à droite,
// qui glissent l'une vers l'autre et se collent au centre.
// Réf. : Grok 949,63 s (flou -> net ~11 images), OpenAI 950,45 s (~8 images),
//        glissement 952,23 -> 953,17 s (28 images, ease in-out), coupe franche 954,97 s.
// Géométrie (1920x1080) : tuiles 208 px, centres (419, 763) et (1503, 763) puis (820, 765) et (1064, 765).
// Cible : « ... utiliser ces deux outils qui sont extrêmement puissants. Ils travaillent maintenant ensemble
//   au lieu d'être séparés. » : Grok sur « deux » (1020,49 s), OpenAI juste avant « puissants » (1021,89 s),
//   glissement sur « ensemble » (1023,27 s), fin après « séparés » (1024,87 s).
const FPS = 30;
const AT = 1020.45;
const END = 1024.95;
const DUR = Math.round((END - AT) * FPS);
const IN_GROK = 2;
const IN_OAI = Math.round((1021.75 - AT) * FPS);
const SLIDE = Math.round((1023.2 - AT) * FPS);
const SLIDE_LEN = 28;

const SIZE = 208;
const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

// Tuile d'app à biseau chromé (même relevé que d212).
const ChromeTile: React.FC<{size: number; inner?: string; children?: React.ReactNode}> = ({size, inner, children}) => {
  const r = size * 0.23;
  const ring = size * 0.052;
  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        width: size,
        height: size,
        borderRadius: r,
        background:
          'linear-gradient(155deg, #ffffff 0%, #6f6f72 8%, #fafafa 16%, #3c3c3f 27%, #ececee 40%, #8d8d90 52%, #ffffff 64%, #404043 78%, #f4f4f4 90%, #7a7a7d 100%)',
        boxShadow: '0 10px 22px rgba(0,0,0,0.35), 0 2px 5px rgba(0,0,0,0.3), inset 0 0 0 1.5px rgba(40,40,42,0.75)',
      }}
    >
      <div
        style={{
          position: 'absolute',
          inset: ring,
          borderRadius: r - ring * 0.8,
          background: inner ?? 'linear-gradient(180deg, #fbfbfb 0%, #f1f1f2 55%, #e4e4e6 100%)',
          boxShadow:
            'inset 0 0 0 1.5px rgba(30,30,32,0.55), inset 0 3px 5px rgba(255,255,255,0.9), inset 0 -6px 10px rgba(0,0,0,0.10), 0 0 2px rgba(0,0,0,0.4)',
          overflow: 'hidden',
        }}
      >
        {children}
      </div>
    </div>
  );
};

// Icône Grok : tuile noire, dôme blanc (fantôme) et deux yeux-pilules inclinés.
const GrokFace: React.FC<{s: number}> = ({s}) => (
  <svg width={s} height={s} viewBox="0 0 1 1" style={{position: 'absolute', inset: 0}}>
    <defs>
      <linearGradient id="grokDome" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stopColor="#ffffff" />
        <stop offset="0.6" stopColor="#f4f4f5" />
        <stop offset="1" stopColor="#dcdcde" />
      </linearGradient>
      <linearGradient id="grokTop" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stopColor="#2a2a2c" />
        <stop offset="0.25" stopColor="#0a0a0b" />
        <stop offset="1" stopColor="#050506" />
      </linearGradient>
    </defs>
    <rect x={0} y={0} width={1} height={1} fill="url(#grokTop)" />
    <path d="M0 0.52 C0.1 0.25 0.38 0.12 0.62 0.17 C0.85 0.22 0.99 0.5 1.02 0.8 L1.02 1.02 L0 1.02 Z" fill="url(#grokDome)" />
    <rect x={-0.065} y={-0.135} width={0.13} height={0.27} rx={0.065} fill="#0c0c0d" transform="translate(0.47 0.49) rotate(-27)" />
    <rect x={-0.065} y={-0.135} width={0.13} height={0.27} rx={0.065} fill="#0c0c0d" transform="translate(0.73 0.39) rotate(-27)" />
  </svg>
);

const Duo: React.FC<{showPlate?: boolean}> = ({showPlate = true}) => {
  const f = useCurrentFrame();
  const sl = interpolate(f, [SLIDE, SLIDE + SLIDE_LEN], [0, 1], {...clamp, easing: Easing.inOut(Easing.cubic)});
  const gx = interpolate(sl, [0, 1], [419, 820]);
  const ox = interpolate(sl, [0, 1], [1503, 1064]);
  const cy = interpolate(sl, [0, 1], [763, 765]);
  const inner = SIZE - 2 * SIZE * 0.052;

  const tile = (start: number, len: number, cx: number, children: React.ReactNode, innerBg?: string) => {
    if (f < start) return null;
    const p = interpolate(f, [start, start + len], [0, 1], {...clamp, easing: Easing.out(Easing.cubic)});
    return (
      <div
        style={{
          position: 'absolute',
          left: cx - SIZE / 2,
          top: cy - SIZE / 2,
          width: SIZE,
          height: SIZE,
          opacity: p,
          transform: `scale(${1.05 - 0.05 * p})`,
          filter: p < 1 ? `blur(${((1 - p) * 16).toFixed(2)}px)` : undefined,
        }}
      >
        <ChromeTile size={SIZE} inner={innerBg}>
          {children}
        </ChromeTile>
      </div>
    );
  };

  return (
    <AbsoluteFill style={{overflow: 'hidden'}}>
      <Plate show={showPlate} />
      {tile(IN_GROK, 11, gx, <GrokFace s={inner} />, '#070708')}
      {tile(
        IN_OAI,
        8,
        ox,
        <svg viewBox="0 0 24 24" width={inner * 0.78} height={inner * 0.78} style={{position: 'absolute', left: inner * 0.11, top: inner * 0.11}}>
          <path d={siOpenai.path} fill="#0b0b0c" />
        </svg>,
      )}
      <SfxTrack
        cues={cuesExportees}
      />
    </AbsoluteFill>
  );
};

export const meta = {
  id: 'd220-icones-duo',
  fps: FPS,
  durationInFrames: DUR,
  defaultProps: {showPlate: true},
  occurrences: [{ref: [949.5, 954.97] as [number, number], at: AT, from: 0, durationInFrames: DUR, mode: 'plein' as const}],
};
export default Duo;

// Signaux sonores exportés pour la bibliothèque (cloud/cues_globaux.py).
const cuesExportees: SfxCue[] = [
          {frame: IN_GROK + 1, name: 'grave-apparition'},
          {frame: IN_OAI + 1, name: 'grave-apparition'},
          {frame: SLIDE, name: 'whoosh-transition'},
        ];
export const cues = cuesExportees;
