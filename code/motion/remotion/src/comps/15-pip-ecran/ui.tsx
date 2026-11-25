// Kit d'interface du lot F (IDs 15, 17, 23, 25, 26, 39).
// Fond sombre dégradé bleu-teal, carte speaker, curseurs, icônes au trait, polices Claude.
import React from 'react';
import {AbsoluteFill, Img, staticFile, interpolate, Easing} from '../../shared/rt';
import {loadFont as instrument} from '@remotion/google-fonts/InstrumentSans';
import {loadFont as serif} from '@remotion/google-fonts/SourceSerif4';

export const SANS = instrument('normal', {weights: ['400', '500', '600', '700']}).fontFamily;
export const SERIF = serif('normal', {weights: ['300', '400', '500']}).fontFamily;

export const K = {
  modal: '#353533',
  win: '#1e1e1c',
  field: '#4d4d4a',
  fieldText: '#ececea',
  placeholder: '#8e8e8b',
  muted: '#83837f',
  label: '#ebebe8',
  blue: '#2f6fe0',
  orange: '#D97757',
};

// Interpolation bornée avec courbe douce.
export const ease = (f: number, a: number, b: number, from = 0, to = 1, e = Easing.bezier(0.33, 0, 0.2, 1)) =>
  interpolate(f, [a, b], [from, to], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: e});

// Fond noir avec lueur bleu-teal en bas à gauche.
export const TealBg: React.FC<{cx?: number; cy?: number; rx?: number; ry?: number; hole?: string}> = ({cx = 520, cy = 1110, rx = 820, ry = 560, hole}) => (
  <AbsoluteFill
    style={{
      clipPath: hole ? `path(evenodd, 'M0 0H1920V1080H0Z ${hole}')` : undefined,
      background: `radial-gradient(ellipse ${rx}px ${ry}px at ${cx}px ${cy}px, #2c4553 0%, #203a48 28%, #11283a 52%, #06121b 75%, #000 100%)`,
      backgroundColor: '#000',
    }}
  />
);

// Carte speaker : cadre, coins, ombre et lueur de l'original. Intérieur gris (aperçu) ou transparent (alpha).
export const SpeakerCard: React.FC<{x: number; y: number; w: number; h: number; radius?: number; fill?: boolean; style?: React.CSSProperties}> = ({x, y, w, h, radius = 16, fill = true, style}) => (
  <div
    style={{
      position: 'absolute', left: x, top: y, width: w, height: h, borderRadius: radius, overflow: 'hidden',
      background: fill ? '#1A1A1C' : 'transparent',
      boxShadow: '0 0 0 1.5px rgba(200,200,200,0.55), 0 20px 60px rgba(0,0,0,0.55)', ...style,
    }}
  />
);

// Chemin SVG d'un rectangle arrondi, pour percer le fond en alpha.
export const roundRectPath = (x: number, y: number, w: number, h: number, r: number) =>
  `M${x + r} ${y}H${x + w - r}A${r} ${r} 0 0 1 ${x + w} ${y + r}V${y + h - r}A${r} ${r} 0 0 1 ${x + w - r} ${y + h}H${x + r}A${r} ${r} 0 0 1 ${x} ${y + h - r}V${y + r}A${r} ${r} 0 0 1 ${x + r} ${y}Z`;

// Curseurs macOS.
export const Cursor: React.FC<{x: number; y: number; kind?: 'hand' | 'ibeam' | 'arrow'; scale?: number; opacity?: number}> = ({x, y, kind = 'hand', scale = 1, opacity = 1}) => {
  if (kind === 'ibeam')
    return (
      <svg style={{position: 'absolute', left: x - 9 * scale, top: y - 18 * scale, opacity}} width={18 * scale} height={36 * scale} viewBox="0 0 18 36">
        <path d="M3 2h4.5c1 0 1.5.6 1.5 1.3C9 2.6 9.5 2 10.5 2H15M9 3.3v29.4M3 34h4.5c1 0 1.5-.6 1.5-1.3 0 .7.5 1.3 1.5 1.3H15M6 18h6" stroke="#fff" strokeWidth="4" fill="none" strokeLinecap="round" />
        <path d="M3 2h4.5c1 0 1.5.6 1.5 1.3C9 2.6 9.5 2 10.5 2H15M9 3.3v29.4M3 34h4.5c1 0 1.5-.6 1.5-1.3 0 .7.5 1.3 1.5 1.3H15M6 18h6" stroke="#000" strokeWidth="1.8" fill="none" strokeLinecap="round" />
      </svg>
    );
  if (kind === 'arrow')
    return (
      <svg style={{position: 'absolute', left: x - 2 * scale, top: y - 2 * scale, opacity, filter: 'drop-shadow(0 2px 3px rgba(0,0,0,0.4))'}} width={28 * scale} height={40 * scale} viewBox="0 0 28 40">
        <path d="M2 2 L2 31 L9 24.5 L14 36 L19 34 L14 22.5 L24 22.5 Z" fill="#000" stroke="#fff" strokeWidth="2.2" strokeLinejoin="round" />
      </svg>
    );
  // main pointeur, pointe de l'index en (x, y)
  return (
    <svg style={{position: 'absolute', left: x - 15 * scale, top: y - 3 * scale, opacity, filter: 'drop-shadow(0 2px 3px rgba(0,0,0,0.45))'}} width={46 * scale} height={52 * scale} viewBox="0 0 46 52">
      <path
        d="M15 3.5c-2.4 0-4 1.8-4 4.2v19.8l-3.3-3.6c-1.9-2-4.6-2.2-6.3-.6-1.5 1.5-1.4 3.6.1 5.7l8.6 12.2c2.9 4.1 6.9 7.3 12.9 7.3h4.4c7.6 0 12.6-5.5 12.6-13.2V24.6c0-2.3-1.6-3.9-3.7-3.9-1.3 0-2.4.6-3 1.6v-1.2c0-2.3-1.6-3.9-3.7-3.9-1.3 0-2.3.6-2.9 1.5-.4-1.9-1.9-3.1-3.7-3.1-1.2 0-2.2.5-2.9 1.3V7.7c0-2.4-1.6-4.2-4-4.2z"
        fill="#fff" stroke="#000" strokeWidth="2.2" strokeLinejoin="round"
      />
      <path d="M22.5 29v9M28.5 29v9M34.2 29v9" stroke="#000" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
};

// Icônes au trait (style lucide), dessinées en SVG.
type IP = {size?: number; color?: string; sw?: number; style?: React.CSSProperties};
const Svg: React.FC<IP & {children: React.ReactNode; vb?: string}> = ({size = 24, color = '#cfcfcc', sw = 1.7, style, children, vb = '0 0 24 24'}) => (
  <svg width={size} height={size} viewBox={vb} fill="none" stroke={color} strokeWidth={sw} strokeLinecap="round" strokeLinejoin="round" style={style}>
    {children}
  </svg>
);
export const IPlus: React.FC<IP> = (p) => <Svg {...p}><path d="M12 5v14M5 12h14" /></Svg>;
export const IX: React.FC<IP> = (p) => <Svg {...p}><path d="M6 6l12 12M18 6L6 18" /></Svg>;
export const IChats: React.FC<IP> = (p) => <Svg {...p}><path d="M10 3.5a6.3 6.3 0 0 0-5.5 9.4L3.6 16.4l3.6-.8A6.3 6.3 0 1 0 10 3.5z" /><path d="M16.8 9.6a5.2 5.2 0 0 1 1.9 7.4l.8 3.2-3.2-.8a5.2 5.2 0 0 1-5.5-.9" /></Svg>;
export const IProjects: React.FC<IP> = (p) => <Svg {...p}><path d="M7.5 3.8h9M5.8 6.8h12.4" /><path d="M4 10h16l-1.2 8.3a2.2 2.2 0 0 1-2.2 1.9H7.4a2.2 2.2 0 0 1-2.2-1.9z" /></Svg>;
export const IStack: React.FC<IP> = (p) => <Svg {...p}><path d="M12 2.8v2.2M12 10v2.4M12 17.4v3.8" /><path d="M5.4 5h10.4l2.7 2.5-2.7 2.5H5.4a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1z" /><path d="M18.6 12.4H8.2l-2.7 2.5 2.7 2.5h10.4a1 1 0 0 0 1-1v-3a1 1 0 0 0-1-1z" /></Svg>;
export const IShapes: React.FC<IP> = (p) => <Svg {...p}><circle cx="7" cy="16.5" r="3.6" /><rect x="13" y="11.5" width="7" height="9" rx="1.6" /><path d="M8.2 12.2a5.3 5.3 0 0 1 10.1-2.4" /></Svg>;
export const IBriefcase: React.FC<IP> = (p) => <Svg {...p}><rect x="3" y="7" width="18" height="13" rx="2.2" /><path d="M8.5 7V5.3A1.3 1.3 0 0 1 9.8 4h4.4a1.3 1.3 0 0 1 1.3 1.3V7M3 13.2h6.5M14.5 13.2H21M10.8 13.2h2.4" /></Svg>;
export const IPalette: React.FC<IP> = (p) => <Svg {...p}><path d="M12 3a9 9 0 1 0 0 18c1.2 0 1.8-.8 1.8-1.7 0-1.2-1-1.5-1-2.6 0-.9.8-1.6 1.7-1.6h2.3A4.2 4.2 0 0 0 21 11c0-4.4-4-8-9-8z" /><circle cx="7.5" cy="11" r="1" /><circle cx="10" cy="7" r="1" /><circle cx="14.5" cy="7" r="1" /></Svg>;
export const IBuilding: React.FC<IP> = (p) => <Svg {...p}><rect x="4" y="3.5" width="10" height="17" rx="1" /><path d="M14 9.5h5a1 1 0 0 1 1 1v10H14M7.5 7.5h3M7.5 11h3M7.5 14.5h3M8.5 20.5v-3h1v3" /></Svg>;
export const ILock: React.FC<IP> = (p) => <Svg {...p}><rect x="5" y="10.5" width="14" height="10" rx="2" /><path d="M8 10.5V7.5a4 4 0 0 1 8 0v3M12 14.5v2.5" /></Svg>;
export const IMic: React.FC<IP> = (p) => <Svg {...p}><rect x="9" y="3" width="6" height="11" rx="3" /><path d="M5.5 11a6.5 6.5 0 0 0 13 0M12 17.5V21" /></Svg>;
export const IWave: React.FC<IP> = (p) => <Svg {...p}><path d="M3 10v4M7 7v10M11 4v16M15 8v8M19 10.5v3M21.5 11v2" /></Svg>;
export const IPen: React.FC<IP> = (p) => <Svg {...p}><path d="M4 20l1-4.5L16 4.5a2 2 0 0 1 3 3L8 18.5z" /><path d="M14 6.5l3 3" /></Svg>;
export const IChart: React.FC<IP> = (p) => <Svg {...p}><path d="M3 20h18M4 16l5-6 4 3 7-8" /></Svg>;
export const IBulb: React.FC<IP> = (p) => <Svg {...p}><path d="M9 18h6M10 21h4M12 3a6 6 0 0 0-3.5 10.9c.6.5 1 1.2 1 2V17h5v-1.1c0-.8.4-1.5 1-2A6 6 0 0 0 12 3z" /></Svg>;
export const IChevron: React.FC<IP> = (p) => <Svg {...p}><path d="M6 9l6 6 6-6" /></Svg>;
export const IFile: React.FC<IP> = (p) => <Svg {...p}><path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z" /><path d="M14 3v5h5" /></Svg>;
export const ISearch: React.FC<IP> = (p) => <Svg {...p}><circle cx="11" cy="11" r="7" /><path d="M20 20l-4-4" /></Svg>;

// Étoile Claude (logo simple-icons).
import {siClaude} from 'simple-icons';
export const ClaudeStar: React.FC<{size: number; color?: string; style?: React.CSSProperties}> = ({size, color = '#D97757', style}) => (
  <svg width={size} height={size} viewBox="0 0 24 24" style={style}><path d={siClaude.path} fill={color} /></svg>
);

// Texte tapé : renvoie le préfixe visible selon le temps.
export const typed = (text: string, f: number, start: number, cps: number, fps = 30) => {
  const n = Math.max(0, Math.floor(((f - start) / fps) * cps));
  return text.slice(0, Math.min(text.length, n));
};
