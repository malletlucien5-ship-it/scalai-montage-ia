import React from 'react';
import {loadFont as inter} from '@remotion/google-fonts/Inter';

const SANS = inter('normal', {weights: ['700', '800']}).fontFamily;
const FPS = 30;

export type PillStyle = 'tip' | 'name';
export type PillSpec = {
  style: PillStyle;
  text: string;
  in: number; // image où la pilule est encore entièrement sous le cadre (s, relatif)
  out?: {t: number; kind: 'slide' | 'fade'};
  bottom: number; // bord bas de la boîte au repos (px)
  h: number;
  size: number;
  padX: number;
  w?: number; // largeur fixe de la boîte (relevée sur l'original)
  icon?: React.ReactNode;
};

// Entrée mesurée : la boîte part juste sous le cadre et remonte en décroissance exponentielle (x0,87 par image).
// Sortie « slide » mesurée : chute accélérée, décalage = 2,75 x (1,22^f - 1), 22 images.
// Sortie « fade » mesurée : flou et fondu sur 19 images avec légère descente.
export const pillMotion = (frame: number, p: PillSpec) => {
  const fIn = frame - Math.round(p.in * FPS);
  if (fIn < 0) return null;
  const top = p.bottom - p.h;
  let dy = (1080 - top + 8) * Math.pow(0.87, fIn);
  let opacity = 1;
  let blur = 0;
  if (p.out) {
    const fo = frame - Math.round(p.out.t * FPS);
    if (fo >= 0) {
      if (p.out.kind === 'slide') {
        if (fo > 22) return null;
        dy += 2.75 * (Math.pow(1.22, fo) - 1);
      } else {
        if (fo > 19) return null;
        const k = fo / 19;
        opacity = 1 - Math.pow(k, 1.3);
        blur = 9 * k;
        dy += 22 * k;
      }
    }
  }
  return {dy, opacity, blur};
};

export const Pill: React.FC<{p: PillSpec; frame: number}> = ({p, frame}) => {
  const m = pillMotion(frame, p);
  if (!m) return null;
  const tip = p.style === 'tip';
  return (
    <div
      style={{
        position: 'absolute',
        left: 0,
        right: 0,
        top: p.bottom - p.h,
        display: 'flex',
        justifyContent: 'center',
        transform: `translateY(${m.dy}px)`,
        opacity: m.opacity,
        filter: m.blur > 0.1 ? `blur(${m.blur}px)` : undefined,
      }}
    >
      <div
        style={{
          height: p.h,
          boxSizing: 'border-box',
          padding: p.icon ? `0 0 0 ${p.padX}px` : `0 ${p.padX}px`,
          width: p.w,
          display: 'flex',
          alignItems: 'center',
          gap: p.icon ? 31 : 0,
          borderRadius: tip ? 16 : 14,
          ...(tip
            ? {
                background: 'rgba(8,24,46,0.55)',
                border: '5px solid #17F5F8',
                boxShadow: '0 0 14px rgba(23,245,248,0.65), inset 0 0 12px rgba(23,245,248,0.45)',
              }
            : {
                background:
                  'radial-gradient(ellipse 70% 90% at 8% 105%, rgba(24,92,122,0.95) 0%, rgba(24,92,122,0) 70%), linear-gradient(180deg, #0B2D44 0%, #06223A 60%, #041B30 100%)',
                border: '1.5px solid rgba(110,208,228,0.8)',
                boxShadow: '0 6px 24px rgba(0,0,0,0.35)',
              }),
        }}
      >
        {p.icon}
        <span
          style={{
            fontFamily: SANS,
            fontWeight: tip ? 800 : 700,
            fontSize: p.size,
            lineHeight: 1,
            whiteSpace: 'pre',
            letterSpacing: tip ? '-0.005em' : '0',
            color: tip ? '#FFFFFF' : '#12E8F8',
            textShadow: tip ? '0 3px 8px rgba(0,0,0,0.55)' : '0 0 10px rgba(18,232,248,0.25)',
            marginTop: p.size * 0.04,
          }}
        >
          {p.text}
        </span>
      </div>
    </div>
  );
};
