import React from 'react';
import {Easing, interpolate} from '../../shared/rt';
import {INTER_L} from '../../shared/localFonts';
// Police système de l'app Claude : SF Pro (vue par Chrome headless sur macOS).
export const SF = `-apple-system, "SF Pro Text", "SF Pro", system-ui, ${INTER_L}, sans-serif`;

// Barre de saisie Claude, mesurée sur la référence à l'échelle 1 (occurrence « Check your work ») :
// boîte 1370 x 248, bas à y=1038, centrée en x=960.
export const BASE_W = 1370;
export const BASE_H = 248;
export const LINE_H = 68;

export type BarProps = {
  scale: number;
  cx: number;
  bottom: number;
  lines: number; // nombre de lignes de texte réservées
  extraH?: number; // hauteur en plus (unités échelle 1)
  textMaxW?: number; // largeur max du texte (unités échelle 1)
  textDy?: number; // décalage vertical du texte (unités échelle 1)
  sepDy?: number; // décalage vertical du séparateur (unités échelle 1)
  text: string;
  showCursor: boolean;
  enter: number; // frames depuis le début de l'entrée (>= 0)
  exit?: number; // frames depuis le début de la sortie (< 0 si pas de sortie)
};

const C = {
  bg: 'rgb(14,12,10)',
  border: 'rgba(214,212,208,0.78)',
  sep: 'rgb(34,31,29)',
  gray: 'rgb(160,157,156)',
  plus: 'rgb(146,144,142)',
  mic: 'rgb(200,197,196)',
  orange: 'rgb(217,84,27)',
};

export const ChatBar: React.FC<BarProps> = ({
  scale: s,
  cx,
  bottom,
  lines,
  extraH = 0,
  textMaxW,
  textDy = 0,
  sepDy = 0,
  text,
  showCursor,
  enter,
  exit = -1,
}) => {
  const h = BASE_H + (lines - 1) * LINE_H + extraH;
  // Entrée : montée depuis le bas, fondu, flou qui se dissipe, fond qui s'opacifie.
  const eo = Easing.out(Easing.cubic);
  let ty = interpolate(enter, [0, 22], [62, 0], {easing: eo, extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  let op = interpolate(enter, [0, 9], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  let blur = interpolate(enter, [0, 13], [9, 0], {easing: eo, extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  let bgA = interpolate(enter, [2, 17], [0.15, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  if (exit >= 0) {
    const ei = Easing.in(Easing.quad);
    op = interpolate(exit, [4, 13], [1, 0], {easing: ei, extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
    blur = interpolate(exit, [0, 12], [0, 9], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
    bgA = interpolate(exit, [3, 11], [1, 0.4], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
    ty = 0;
  }
  const W = BASE_W;
  return (
    <div
      style={{
        position: 'absolute',
        left: cx - (W * s) / 2,
        top: bottom - h * s,
        width: W,
        height: h,
        transform: `translateY(${ty * s}px) scale(${s})`,
        transformOrigin: '0 0',
        opacity: op,
        filter: blur > 0.05 ? `blur(${blur}px)` : undefined,
        fontFamily: SF,
      }}
    >
      {/* fond verre dépoli puis opaque */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          borderRadius: 20,
          overflow: 'hidden',
          backdropFilter: 'blur(14px)',
        }}
      >
        <div style={{position: 'absolute', inset: 0, background: C.bg, opacity: bgA}} />
      </div>
      <div
        style={{
          position: 'absolute',
          inset: 0,
          borderRadius: 20,
          border: `1.6px solid ${C.border}`,
        }}
      />
      {/* texte tapé */}
      <div
        style={{
          position: 'absolute',
          left: 32,
          top: 36 + textDy,
          width: textMaxW ?? W - 68,
          fontSize: 44,
          lineHeight: `${LINE_H}px`,
          color: '#f4f3f2',
          fontWeight: 400,
          letterSpacing: 0,
          whiteSpace: 'pre-wrap',
          wordBreak: 'normal',
        }}
      >
        {text}
        <span style={{position: 'relative', display: 'inline-block', width: 0}}>
          <span
            style={{
              position: 'absolute',
              left: 1,
              top: -41,
              width: 2.6,
              height: 52,
              background: '#fff',
              opacity: showCursor ? 1 : 0,
            }}
          />
        </span>
      </div>
      {/* séparateur */}
      <div style={{position: 'absolute', left: 32, right: 32, top: h - 121 + sepDy, height: 1.5, background: C.sep}} />
      {/* bouton + */}
      <svg style={{position: 'absolute', left: 32, top: h - 90, overflow: 'visible'}} width={64} height={64}>
        <circle cx={32} cy={32} r={31} fill="none" stroke={C.plus} strokeWidth={2.2} />
        <path d="M32 21 V43 M21 32 H43" stroke={C.plus} strokeWidth={2.6} strokeLinecap="round" />
      </svg>
      {/* sélecteur de modèle */}
      <div
        style={{
          position: 'absolute',
          right: 260,
          top: h - 58 - 20,
          height: 40,
          display: 'flex',
          alignItems: 'center',
          fontSize: 30.4,
          color: C.gray,
          letterSpacing: -0.2,
          whiteSpace: 'nowrap',
        }}
      >
        Sonnet 4.6
      </div>
      <svg style={{position: 'absolute', right: 222, top: h - 58 - 8}} width={28} height={16}>
        <path d="M3 3 L14 13 L25 3" fill="none" stroke={C.gray} strokeWidth={2.6} strokeLinecap="round" strokeLinejoin="round" />
      </svg>
      {/* micro */}
      <svg style={{position: 'absolute', right: 150, top: h - 58 - 22}} width={34} height={46}>
        <rect x={10} y={2} width={14} height={25} rx={7} fill="none" stroke={C.mic} strokeWidth={2.6} />
        <path d="M4 20 C4 30 10 34 17 34 C24 34 30 30 30 20 M17 34 V43 M11 43 H23" fill="none" stroke={C.mic} strokeWidth={2.6} strokeLinecap="round" />
      </svg>
      {/* bouton d'envoi orange */}
      <svg style={{position: 'absolute', right: 34, top: h - 58 - 39}} width={78} height={78}>
        <circle cx={39} cy={39} r={39} fill={C.orange} />
        <path d="M39 53 V26 M28 36.5 L39 25.5 L50 36.5" fill="none" stroke="#fff" strokeWidth={3.6} strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    </div>
  );
};
