import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame} from '../../shared/rt';
import {loadFont as inter} from '@remotion/google-fonts/Inter';
import {Plate} from '../../shared/Plate';
import {SfxTrack, SfxCue} from '../../shared/Sfx';

const SANS = inter('normal', {weights: ['600', '700']}).fontFamily;
const FPS = 30;
const NB = ' '; // espace fine insécable avant les deux-points

// Relevés (1920x1080) : boîte x 32 à 500, haut 48, hauteur 98 (niveaux 1 à 5).
// Largeur fixe 468 px comme l'original. Police 46 px (niveaux 1 à 5) et 40 px au niveau 6, boîte de 83 px de haut.
// « Niveau » est abrégé en « Niv. » pour que les libellés français tiennent à la taille d'origine.
export const LEVELS: {label: string; size: number}[] = [
  {label: `Niv. 1/6${NB}: Amateur`, size: 46},
  {label: `Niv. 2/6${NB}: Habitué`, size: 46},
  {label: `Niv. 3/6${NB}: Intégrateur`, size: 46},
  {label: `Niv. 4/6${NB}: Opérateur`, size: 46},
  {label: `Niv. 5/6${NB}: Bâtisseur`, size: 46},
  {label: `Niv. 6/6${NB}: Orchestrateur`, size: 40},
];

export const Badge: React.FC<{level: number; opacity?: number; label?: string}> = ({level, opacity = 1, label: labelOverride}) => {
  const {size} = LEVELS[level];
  const label = labelOverride ?? LEVELS[level].label;
  const h = level === 5 ? 83 : 98;
  const top = level === 5 ? 52 : 48;
  return (
    <div
      style={{
        position: 'absolute',
        left: 32,
        top,
        width: 468,
        boxSizing: 'border-box',
        height: h,
        borderRadius: 10,
        background: 'linear-gradient(180deg, rgba(48,126,170,0.70) 0%, rgba(44,118,162,0.70) 100%)',
        border: '1.5px solid rgba(205,222,238,0.50)',
        boxShadow: 'inset 0 1.5px 0 rgba(170,210,235,0.45), 0 2px 10px rgba(0,0,0,0.12)',
        backdropFilter: 'blur(6px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        opacity,
      }}
    >
      <span
        style={{
          fontFamily: SANS,
          fontWeight: 600,
          fontSize: size,
          color: '#EAF0F4',
          letterSpacing: '-0.005em',
          whiteSpace: 'pre',
          textShadow: '0 1px 3px rgba(0,0,0,0.25)',
          marginTop: 0,
        }}
      >
        {label}
      </span>
    </div>
  );
};

// Montage de démonstration : apparition sèche (coupe) de chaque variante, comme dans la référence,
// puis fondu de sortie mesuré sur le dernier plan (réf. 861,33 s : 13 images).
const LEAD = 0.5;
const HOLD = 2.5;
const FADE = 13;
const TOTAL = Math.round((LEAD + HOLD * 6 + 0.5) * FPS) + FADE;

// Bruitages (SFX-REGLES.md) : grave-apparition à l'arrivée de chaque variante du badge (images 15, 90, 165, 240, 315, 390).
const CUES: SfxCue[] = [0, 1, 2, 3, 4, 5].map((i) => ({frame: Math.round((LEAD + HOLD * i) * FPS), name: 'grave-apparition'}));

const BadgeNiveau: React.FC<{showPlate?: boolean}> = ({showPlate = true}) => {
  const frame = useCurrentFrame();
  const t = frame / FPS - LEAD;
  const lvl = Math.min(5, Math.floor(t / HOLD));
  const endFade = Math.round((LEAD + HOLD * 6) * FPS);
  const op = interpolate(frame, [endFade, endFade + FADE], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return (
    <AbsoluteFill style={{backgroundColor: 'transparent'}}>
      <Plate show={showPlate} />
      {t >= 0 && op > 0 ? <Badge level={lvl} opacity={op} /> : null}
      <SfxTrack cues={CUES} />
    </AbsoluteFill>
  );
};

// Plages de chaque niveau dans la référence, relevées par balayage à 2 i/s (précision 0,5 s).
// Le badge disparaît pendant les écrans pleins (podiums, fenêtres) : au montage, garder la variante affichée
// sur toute la plage et la masquer sous les plans pleins. Dans la composition, chaque variante dure 2,5 s.
const LEVEL_REF: [number, number][] = [
  [26.8, 80.0],
  [83.4, 263.0],
  [265.5, 401.0],
  [404.5, 575.0],
  [578.0, 733.0],
  [736.0, 861.95],
];

export const meta = {
  id: '05-badge-niveau',
  durationInFrames: TOTAL,
  fps: FPS,
  defaultProps: {showPlate: true},
  occurrences: LEVEL_REF.map((ref, i) => ({
    ref,
    from: Math.round((LEAD + HOLD * i) * FPS),
    durationInFrames: Math.round(HOLD * FPS) + (i === 5 ? FADE : 0),
    mode: 'overlay' as const,
  })),
};
export default BadgeNiveau;

// Signaux sonores exportés pour la bibliothèque (cloud/cues_globaux.py).
export const cues = CUES;
