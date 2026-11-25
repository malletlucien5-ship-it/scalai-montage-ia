import React from 'react';
import {Easing, interpolate} from '../../shared/rt';
import {INTER_L} from '../../shared/localFonts';

// Bouton noir brillant de la référence (« Pro Tip » 187-204 s, 586-601 s ; « chatgpt.com/download » 173-177,8 s).
// Relevé en 1920x1080, colonne verticale du bouton « Pro Tip » (boîte 1563..1886 x 869..984) :
// liseré clair 2 px, reflet haut 147 -> 48 sur 44 % de la hauteur, cassure nette vers #1A1A1A,
// puis assombrissement jusqu'à #080808 en bas ; anneau sombre de 1 px à l'extérieur ; texte blanc gras centré.
// Entrée mesurée : apparition floue sur ~11 images (flou ~10 px -> 0, opacité 0 -> 1, montée de ~6 px). Sortie : coupe franche.
export type GlossySpec = {text: string; right: number; bottom: number; h: number; size: number; padX: number; radius: number};

export const GLOSS_IN = 11;

export const GlossyPill: React.FC<{p: GlossySpec; frame: number}> = ({p, frame}) => {
  if (frame < 0) return null;
  const k = interpolate(frame, [0, GLOSS_IN], [0, 1], {extrapolateRight: 'clamp', easing: Easing.out(Easing.quad)});
  const op = interpolate(frame, [0, 1, 4, 8, GLOSS_IN], [0.18, 0.35, 0.65, 0.92, 1], {extrapolateRight: 'clamp'});
  const blur = 10 * Math.pow(1 - k, 1.4);
  const dy = 6 * (1 - k);
  return (
    <div
      style={{
        position: 'absolute',
        right: 1920 - p.right,
        top: p.bottom - p.h,
        height: p.h,
        boxSizing: 'border-box',
        padding: `0 ${p.padX}px`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        borderRadius: p.radius,
        border: '2px solid #9C9C9C',
        borderTopColor: '#C9C9C9',
        background:
          'linear-gradient(180deg, #9A9A9A 0%, #939393 6%, #787878 16%, #5E5E5E 26%, #474747 35%, #333333 42%, #2A2A2A 44%, #1B1B1B 45.5%, #1A1A1A 60%, #141414 74%, #0D0D0D 87%, #080808 96%, #0B0B0B 100%)',
        boxShadow: '0 0 0 1px rgba(0,0,0,0.75), inset 0 0 0 1px rgba(0,0,0,0.55), inset 10px 0 12px -8px rgba(0,0,0,0.35), inset -10px 0 12px -8px rgba(0,0,0,0.35), 0 6px 18px rgba(0,0,0,0.35)',
        opacity: op,
        transform: `translateY(${dy}px)`,
        filter: blur > 0.2 ? `blur(${blur.toFixed(2)}px)` : undefined,
      }}
    >
      <span
        style={{
          fontFamily: INTER_L,
          fontWeight: 700,
          fontSize: p.size,
          lineHeight: 1,
          color: '#FFFFFF',
          whiteSpace: 'pre',
          letterSpacing: '-0.01em',
          textShadow: '0 2px 4px rgba(0,0,0,0.65)',
          marginTop: p.size * 0.02,
        }}
      >
        {p.text}
      </span>
    </div>
  );
};
