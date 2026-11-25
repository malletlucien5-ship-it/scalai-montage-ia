import React from 'react';
import {AbsoluteFill, interpolate, Easing} from '../../shared/rt';
import {loadFont as bodoni} from '@remotion/google-fonts/BodoniModa';
import {loadFont as inter} from '@remotion/google-fonts/Inter';

// Police des titres : Bodoni Moda italique (le plus proche du Didot italique de la référence).
// Mesure : « Bodoni 72 Book Italic » (macOS) colle à la référence, Bodoni Moda sert de repli.
const BODONI_MODA = bodoni('italic', {weights: ['400', '500'], subsets: ['latin', 'latin-ext']}).fontFamily;
export const SERIF = `"Bodoni 72", ${BODONI_MODA}, serif`;
// Mesure : Helvetica Neue Bold colle aux largeurs de mots de la référence (Inter en repli).
const INTER_F = inter('normal', {weights: ['600', '700', '800'], subsets: ['latin', 'latin-ext']}).fontFamily;
export const SANS = `"Helvetica Neue", ${INTER_F}, sans-serif`;

// Fond bleu nuit : haut (22,22,26) vers bas (23,37,63), relevé sur la référence.
export const NightBg: React.FC = () => (
  <AbsoluteFill
    style={{
      background:
        'linear-gradient(180deg, rgb(22,22,26) 0%, rgb(27,26,32) 18%, rgb(27,28,40) 33%, rgb(26,31,46) 50%, rgb(27,32,54) 67%, rgb(24,35,60) 83%, rgb(23,37,64) 100%)',
    }}
  />
);

export const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
export const ease = (f: number, a: number, b: number, from = 0, to = 1, e = Easing.out(Easing.cubic)) =>
  interpolate(f, [a, b], [from, to], {...clamp, easing: e});

// Mot qui apparaît en fondu flouté.
export const BlurWord: React.FC<{
  f: number; start: number; dur?: number; children: React.ReactNode; style?: React.CSSProperties; blur?: number; rise?: number;
}> = ({f, start, dur = 12, children, style, blur = 14, rise = 0}) => {
  const p = ease(f, start, start + dur, 0, 1, Easing.out(Easing.quad));
  return (
    <span
      style={{
        display: 'inline-block',
        opacity: p,
        filter: `blur(${(1 - p) * blur}px)`,
        transform: `translateY(${(1 - p) * rise}px)`,
        ...style,
      }}
    >
      {children}
    </span>
  );
};

// Titre serif italique argenté avec halo, révélé mot par mot.
export const SerifTitle: React.FC<{
  f: number; words: string[]; starts: number[]; size?: number; top?: number; dur?: number; left?: number;
}> = ({f, words, starts, size = 96, top = 40, dur = 14, left}) => (
  <div
    style={{
      position: 'absolute',
      top,
      left: left ?? 0,
      right: left === undefined ? 0 : undefined,
      textAlign: left === undefined ? 'center' : 'left',
      fontFamily: SERIF,
      fontStyle: 'italic',
      fontWeight: 400,
      fontSize: size,
      letterSpacing: -size * 0.012,
      lineHeight: 1.2,
      whiteSpace: 'nowrap',
      filter: 'drop-shadow(0 0 7px rgba(255,255,255,0.45))',
    }}
  >
    {words.map((w, i) => (
      <React.Fragment key={i}>
        <BlurWord f={f} start={starts[i] ?? 0} dur={dur}>
          <span
            style={{
              backgroundImage: 'linear-gradient(180deg, #ffffff 15%, #d9d9e0 55%, #8e8e99 100%)',
              WebkitBackgroundClip: 'text',
              backgroundClip: 'text',
              color: 'transparent',
              paddingRight: size * 0.08,
            }}
          >
            {w}
          </span>
        </BlurWord>
        {i < words.length - 1 ? ' ' : ''}
      </React.Fragment>
    ))}
  </div>
);

// Sphère bleue brillante (dégradé vertical indigo vers bleu vif, liseré clair, halo).
export const SPHERE_BG =
  'linear-gradient(180deg, rgb(62,68,134) 0%, rgb(52,76,140) 14%, rgb(46,84,146) 26%, rgb(40,95,161) 38%, rgb(30,112,184) 50%, rgb(20,130,206) 63%, rgb(12,146,229) 77%, rgb(8,152,236) 86%, rgb(10,138,214) 100%)';

export const Sphere: React.FC<{r: number; children?: React.ReactNode; style?: React.CSSProperties}> = ({r, children, style}) => (
  <div
    style={{
      position: 'absolute',
      left: -r,
      top: -r,
      width: 2 * r,
      height: 2 * r,
      borderRadius: '50%',
      background: SPHERE_BG,
      boxShadow: [
        `inset ${r * 0.02}px ${r * 0.035}px ${r * 0.03}px rgba(190,210,240,0.55)`,
        `inset 0 0 ${r * 0.02}px ${r * 0.012}px rgba(150,180,220,0.55)`,
        `inset 0 0 ${r * 0.1}px ${r * 0.02}px rgba(120,170,225,0.35)`,
        `inset 0 -${r * 0.04}px ${r * 0.05}px rgba(15,50,95,0.55)`,
        `0 ${r * 0.05}px ${r * 0.14}px rgba(0,0,0,0.45)`,
      ].join(', '),
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      overflow: 'hidden',
      ...style,
    }}
  >
    {children}
  </div>
);

// Arc blanc lumineux autour d'une sphère. side = moitié basse ou haute.
// Le tracé part de l'extrémité `from` et progresse de 0 à 1.
export const RingArc: React.FC<{
  R: number; side: 'bottom' | 'top'; from: 'left' | 'right'; p: number; width?: number; startDeg?: number; endDeg?: number;
}> = ({R, side, from, p, width = 7}) => {
  if (p <= 0.001) return null;
  const L = `${-R},0`;
  const Rt = `${R},0`;
  let d: string;
  if (side === 'bottom') d = from === 'left' ? `M ${L} A ${R} ${R} 0 0 0 ${Rt}` : `M ${Rt} A ${R} ${R} 0 0 1 ${L}`;
  else d = from === 'right' ? `M ${Rt} A ${R} ${R} 0 0 0 ${L}` : `M ${L} A ${R} ${R} 0 0 1 ${Rt}`;
  const pad = R + 40;
  return (
    <svg
      width={pad * 2}
      height={pad * 2}
      viewBox={`${-pad} ${-pad} ${pad * 2} ${pad * 2}`}
      style={{position: 'absolute', left: -pad, top: -pad, overflow: 'visible', filter: 'drop-shadow(0 0 6px rgba(255,255,255,0.75)) drop-shadow(0 0 14px rgba(190,215,255,0.35))'}}
    >
      <path d={d} fill="none" stroke="white" strokeWidth={width} strokeLinecap="butt" pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - Math.min(1, p)} />
    </svg>
  );
};
