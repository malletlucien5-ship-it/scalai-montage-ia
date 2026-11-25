import React from 'react';
import {Easing, interpolate} from './rt';

// Outils communs aux captures d'écran macOS de Dan (ChatGPT, Grok) : caméra à images clés, curseur, fond d'écran.

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

// Caméra : [image, échelle, tx, ty]. L'écran 1920x1080 est affiché à scale(s) puis translaté de (tx, ty).
// Entre deux clés : courbe in-out cubique (les mouvements de Screen Studio de Dan), ou 'out' pour un arrêt amorti.
export type CamKey = [number, number, number, number, ('io' | 'out' | 'lin')?];
export const camAt = (keys: CamKey[], f: number) => {
  if (f <= keys[0][0]) return {s: keys[0][1], x: keys[0][2], y: keys[0][3]};
  for (let i = 0; i < keys.length - 1; i++) {
    const a = keys[i];
    const b = keys[i + 1];
    if (f <= b[0]) {
      const ease = b[4] === 'out' ? Easing.out(Easing.cubic) : b[4] === 'lin' ? (x: number) => x : Easing.inOut(Easing.cubic);
      const p = interpolate(f, [a[0], b[0]], [0, 1], {...clamp, easing: ease});
      return {s: a[1] + (b[1] - a[1]) * p, x: a[2] + (b[2] - a[2]) * p, y: a[3] + (b[3] - a[3]) * p};
    }
  }
  const z = keys[keys.length - 1];
  return {s: z[1], x: z[2], y: z[3]};
};

// Flou de mouvement : proportionnel au déplacement apparent d'un point central entre deux images.
export const camBlur = (keys: CamKey[], f: number, gain = 0.09, max = 14) => {
  const a = camAt(keys, f - 0.5);
  const b = camAt(keys, f + 0.5);
  const px = 960 * (b.s - a.s) + (b.x - a.x);
  const py = 540 * (b.s - a.s) + (b.y - a.y);
  return Math.min(max, Math.hypot(px, py) * gain);
};

export const Camera: React.FC<{keys: CamKey[]; f: number; children: React.ReactNode; blurGain?: number}> = ({keys, f, children, blurGain}) => {
  const c = camAt(keys, f);
  const bl = camBlur(keys, f, blurGain);
  return (
    <div
      style={{
        position: 'absolute', left: 0, top: 0, width: 1920, height: 1080, transformOrigin: '0 0',
        transform: `translate(${c.x}px, ${c.y}px) scale(${c.s})`,
        filter: bl > 0.3 ? `blur(${bl.toFixed(2)}px)` : undefined,
      }}
    >
      {children}
    </div>
  );
};

// Trajectoire de curseur : [image, x, y] (coordonnées de l'écran), interpolation amortie.
export type CurKey = [number, number, number];
export const curAt = (keys: CurKey[], f: number) => {
  if (f <= keys[0][0]) return {x: keys[0][1], y: keys[0][2]};
  for (let i = 0; i < keys.length - 1; i++) {
    const a = keys[i];
    const b = keys[i + 1];
    if (f <= b[0]) {
      const p = interpolate(f, [a[0], b[0]], [0, 1], {...clamp, easing: Easing.inOut(Easing.quad)});
      return {x: a[1] + (b[1] - a[1]) * p, y: a[2] + (b[2] - a[2]) * p};
    }
  }
  const z = keys[keys.length - 1];
  return {x: z[1], y: z[2]};
};

// Flèche macOS : corps noir, liseré blanc, ombre portée. (x, y) = pointe. h = hauteur affichée.
export const Cursor: React.FC<{x: number; y: number; h: number; press?: number; blur?: number}> = ({x, y, h, press = 0, blur = 0}) => {
  const k = h / 24;
  const sc = 1 - 0.12 * press;
  return (
    <svg
      width={18 * k}
      height={26 * k}
      viewBox="0 0 18 26"
      style={{
        position: 'absolute', left: x - 2.2 * k, top: y - 1.4 * k, overflow: 'visible',
        transform: `scale(${sc})`, transformOrigin: `${2.2 * k}px ${1.4 * k}px`,
        filter: `drop-shadow(0 ${0.6 * k}px ${0.9 * k}px rgba(0,0,0,0.45))${blur > 0.3 ? ` blur(${blur}px)` : ''}`,
      }}
    >
      <path d="M2.2 1.4 L2.2 20.2 L6.6 16.1 L9.6 23.2 L12.9 21.8 L9.9 14.9 L15.9 14.9 Z" fill="#000" stroke="#fff" strokeWidth={1.5} strokeLinejoin="round" />
    </svg>
  );
};

// Fond d'écran bleu de macOS visible autour des fenêtres de Dan : nuit bleu marine, vague claire à gauche
// (y ≈ 500-560 px, x < 180) et à droite (y ≈ 480-620 px). Relevé sur la réf. 177,8 s.
export const FondMac: React.FC = () => (
  <div style={{position: 'absolute', left: -400, top: -300, width: 2720, height: 1680, background: '#03142b', overflow: 'hidden'}}>
    <div style={{position: 'absolute', inset: 0, background: 'linear-gradient(180deg, #2c5277 0%, #163a5e 18%, #0a2a4c 40%, #072a4c 60%, #032340 80%, #021a33 100%)'}} />
    {/* vague gauche : lame claire puis bleu vif en dessous */}
    <div style={{position: 'absolute', left: 400 - 420, top: 300 + 520, width: 720, height: 560, borderRadius: '50%', background: 'radial-gradient(closest-side, #3fb4f2 0%, #2a90d6 45%, rgba(20,90,170,0.6) 72%, rgba(10,50,110,0) 100%)'}} />
    <div style={{position: 'absolute', left: 400 - 360, top: 300 + 500, width: 640, height: 60, borderRadius: '50%', transform: 'rotate(-6deg)', background: 'radial-gradient(closest-side, rgba(235,248,255,0.95), rgba(160,215,250,0.5) 55%, rgba(120,190,240,0) 100%)'}} />
    {/* vague droite */}
    <div style={{position: 'absolute', left: 400 + 1640, top: 300 + 380, width: 760, height: 420, borderRadius: '50%', background: 'radial-gradient(closest-side, #4e8fc6 0%, #2f6ea8 45%, rgba(20,70,130,0.5) 75%, rgba(10,40,90,0) 100%)'}} />
    <div style={{position: 'absolute', left: 400 + 1700, top: 300 + 500, width: 560, height: 46, borderRadius: '50%', transform: 'rotate(10deg)', background: 'radial-gradient(closest-side, rgba(220,240,255,0.85), rgba(150,200,240,0.4) 60%, rgba(120,180,230,0) 100%)'}} />
    {/* bas sombre */}
    <div style={{position: 'absolute', left: 0, top: 300 + 980, width: 2720, height: 400, background: 'linear-gradient(180deg, rgba(4,46,79,0.0), #042e4f 30%, #021f38 100%)'}} />
  </div>
);
