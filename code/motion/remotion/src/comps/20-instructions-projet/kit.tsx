// Kit d'interface Claude recréée (lot E). Dupliqué tel quel dans chaque dossier du lot.
import React from 'react';
import {AbsoluteFill, Img, interpolate, staticFile, useCurrentFrame, Easing} from '../../shared/rt';
import {siClaude} from 'simple-icons';
import {INTER} from '../../shared/fonts';

export const FONT = `-apple-system, BlinkMacSystemFont, "SF Pro Text", ${INTER}, sans-serif`;
export const CL = {
  orange: '#D97757',
  send: '#C95A2E',
  text: '#ECE9E6',
  textDim: '#A9A4A0',
  gray: '#8A8581',
  label: '#65615F',
};

export const useT = () => useCurrentFrame() / 30;

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

// Interpolation par paires [temps, valeur].
export const keys = (t: number, k: [number, number][], ease?: (x: number) => number) =>
  interpolate(t, k.map((a) => a[0]), k.map((a) => a[1]), ease ? {...clamp, easing: ease} : clamp);

// Courbe mesurée image par image (pas dt secondes).
export const samples = (t: number, arr: number[], dt = 0.1, t0 = 0) =>
  interpolate(t, arr.map((_, i) => t0 + i * dt), arr, clamp);

export const fade = (t: number, t0: number, d = 0.15) => interpolate(t, [t0, t0 + d], [0, 1], clamp);
export const easeOut = Easing.bezier(0.2, 0.7, 0.3, 1);
export const easeInOut = Easing.bezier(0.45, 0, 0.25, 1);

// Frappe caractère par caractère.
export const typed = (s: string, t: number, t0: number, cps: number, start = 0) => {
  const n = Math.max(0, Math.min(s.length, Math.floor(start + (t - t0) * cps)));
  return t < t0 ? s.slice(0, start) : s.slice(0, n);
};
export const typedN = (len: number, t: number, t0: number, t1: number) =>
  Math.round(interpolate(t, [t0, t1], [0, len], clamp));

export const Bg: React.FC<{id: string}> = ({id}) => (
  <AbsoluteFill style={{backgroundColor: '#000'}}>
    <Img src={staticFile(`${id}/bg.png`)} style={{width: '100%', height: '100%'}} />
  </AbsoluteFill>
);

export const Camera: React.FC<{
  scale: number; ox: number; oy: number; tx?: number; ty?: number;
  blur?: number; bright?: number; children: React.ReactNode;
}> = ({scale, ox, oy, tx = 0, ty = 0, blur = 0, bright = 1, children}) => (
  <AbsoluteFill
    style={{
      transform: `translate(${tx}px, ${ty}px) scale(${scale})`,
      transformOrigin: `${ox}px ${oy}px`,
      filter: blur > 0 || bright !== 1 ? `blur(${blur}px) brightness(${bright})` : undefined,
    }}
  >
    {children}
  </AbsoluteFill>
);

export const MacWindow: React.FC<{
  x: number; y: number; w: number; h: number; r?: number;
  titleH?: number; titleBg?: string; bodyBg?: string; title?: React.ReactNode; titleSize?: number;
  titleColor?: string; dotX?: number; dotGap?: number; dotR?: number; sep?: string;
  border?: string; titleSpacing?: number; children?: React.ReactNode; shadow?: string; font?: string;
}> = ({
  x, y, w, h, r = 26, titleH = 55, titleBg = '#13100F', bodyBg = '#1A1716', title = 'Claude',
  titleSize = 19, titleColor = '#8D8986', dotX = 37, dotGap = 30, dotR = 9, sep = 'transparent',
  border = 'rgba(214,214,214,0.82)', titleSpacing = 0.2, children,
  shadow = '0 40px 90px rgba(0,0,0,0.55), 0 10px 30px rgba(0,0,0,0.35)', font = FONT,
}) => (
  <div
    style={{
      position: 'absolute', left: x, top: y, width: w, height: h, borderRadius: r,
      background: bodyBg, boxShadow: shadow, overflow: 'hidden', fontFamily: font,
    }}
  >
    <div style={{position: 'absolute', left: 0, top: 0, width: w, height: titleH, background: titleBg, borderBottom: `1px solid ${sep}`}}>
      {['#F75C5C', '#F8BC2D', '#2AC343'].map((c, i) => (
        <div key={i} style={{position: 'absolute', left: dotX + i * dotGap - dotR, top: titleH / 2 - dotR, width: dotR * 2, height: dotR * 2, borderRadius: dotR, background: c}} />
      ))}
      <div style={{position: 'absolute', left: 0, width: w, top: 0, height: titleH, lineHeight: `${titleH}px`, textAlign: 'center', color: titleColor, fontSize: titleSize, fontWeight: 500, letterSpacing: titleSpacing}}>
        {title}
      </div>
    </div>
    {children}
    <div style={{position: 'absolute', inset: 0, borderRadius: r, border: `1.6px solid ${border}`, pointerEvents: 'none'}} />
  </div>
);

// Logo Claude (simple-icons), orange.
export const ClaudeMark: React.FC<{x: number; y: number; size: number; color?: string; glow?: boolean; opacity?: number}> = ({
  x, y, size, color = CL.orange, glow = true, opacity = 1,
}) => (
  <svg
    viewBox="0 0 24 24" width={size} height={size}
    style={{position: 'absolute', left: x - size / 2, top: y - size / 2, opacity, filter: glow ? `drop-shadow(0 0 ${size * 0.18}px rgba(217,119,87,0.45))` : undefined}}
  >
    <path d={siClaude.path} fill={color} />
  </svg>
);

// Pointeur macOS.
export const Cursor: React.FC<{x: number; y: number; size?: number; opacity?: number}> = ({x, y, size = 28, opacity = 1}) => (
  <svg viewBox="0 0 20 28" width={size * 0.72} height={size} style={{position: 'absolute', left: x, top: y, opacity}}>
    <path d="M1 1 L1 21 L6 16.5 L9.5 24.5 L12.5 23.2 L9.1 15.4 L15.5 15.4 Z" fill="#111" stroke="#fff" strokeWidth={1.6} strokeLinejoin="round" />
  </svg>
);

// Points de réflexion : trois points qui s'allument l'un après l'autre.
export const ThinkingDots: React.FC<{x: number; y: number; t: number; size?: number}> = ({x, y, t, size = 7}) => (
  <div style={{position: 'absolute', left: x, top: y - size / 2, display: 'flex', gap: size * 0.7}}>
    {[0, 1, 2].map((i) => {
      const ph = (t * 2.6 - i * 0.28) % 1;
      const a = 0.35 + 0.6 * Math.max(0, Math.sin(Math.PI * Math.max(0, Math.min(1, ph))));
      return <div key={i} style={{width: size, height: size, borderRadius: size, background: `rgba(200,195,190,${a})`}} />;
    })}
  </div>
);

export const Caret: React.FC<{h: number; color?: string; on?: boolean}> = ({h, color = CL.text, on = true}) => (
  <span style={{display: 'inline-block', width: 2, height: h, background: on ? color : 'transparent', verticalAlign: 'middle', marginLeft: 1, transform: 'translateY(-1px)'}} />
);

// Icône micro au trait.
export const Mic: React.FC<{x: number; y: number; h: number; color?: string}> = ({x, y, h, color = '#8A847F'}) => (
  <svg viewBox="0 0 24 32" width={h * 0.75} height={h} style={{position: 'absolute', left: x - (h * 0.75) / 2, top: y - h / 2}}>
    <rect x="7" y="2" width="10" height="17" rx="5" fill="none" stroke={color} strokeWidth="2.2" />
    <path d="M3 14 a9 9 0 0 0 18 0 M12 23 V29 M7 29.5 H17" fill="none" stroke={color} strokeWidth="2.2" strokeLinecap="round" />
  </svg>
);

export const ArrowUp: React.FC<{size: number; color?: string; stroke?: number}> = ({size, color = '#fff', stroke = 3}) => (
  <svg viewBox="0 0 24 24" width={size} height={size}>
    <path d="M12 20 V5 M5.5 11.5 L12 5 L18.5 11.5" fill="none" stroke={color} strokeWidth={stroke} strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

export const Chevron: React.FC<{size: number; color?: string}> = ({size, color = '#8A847F'}) => (
  <svg viewBox="0 0 24 24" width={size} height={size} style={{display: 'inline-block'}}>
    <path d="M5 9 L12 16 L19 9" fill="none" stroke={color} strokeWidth={2.4} strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

export const Plus: React.FC<{size: number; color?: string}> = ({size, color = '#C4BDB8'}) => (
  <svg viewBox="0 0 24 24" width={size} height={size}>
    <path d="M12 4 V20 M4 12 H20" stroke={color} strokeWidth={2} strokeLinecap="round" />
  </svg>
);
