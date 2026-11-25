import React from 'react';
import {AbsoluteFill, Easing, interpolate, useCurrentFrame} from '../../shared/rt';
import {Plate} from '../../shared/Plate';
import {SfxTrack, SfxCue} from '../../shared/Sfx';
import {ARIAL_L} from '../../shared/localFonts';
// Police de l'original : Helvetica Neue (système macOS).
const HELV = `"Helvetica Neue", Helvetica, Arial, ${ARIAL_L}, sans-serif`;

// Référence : 351,3 s à 357,97 s (image n = 0 à 200, mesures à 29,97 i/s).
// Carré blanc qui monte, s'étire en pilule, barre de progression verte et rouge,
// la barre devient le bouton rouge « S'abonner », clic (gris), puis « S'abonner et changer ».
export const meta = {
  id: '27-bouton-abonnement',
  durationInFrames: 200,
  fps: 30,
  defaultProps: {showPlate: true},
  occurrences: [{ref: [351.3, 357.967], from: 0, durationInFrames: 200, mode: 'overlay'}],
};

// Bruitages : grave-apparition à l'entrée du carré, clic à l'appui du bouton, pop à la transformation finale.
const SFX: SfxCue[] = [
  {frame: 3, name: 'grave-apparition'},
  {frame: 123, name: 'clic'},
  {frame: 129, name: 'pop'},
];

const CX = 960;
const PILL_TOP = 903;
const PILL_H = 128;
const BAR_Y = 959; // haut de la barre de progression
const BAR_H = 17;
const RED = 'rgb(255,0,4)';
const GREEN = 'rgb(12,252,0)';
const GRAY = 'rgb(69,69,69)';
const FONT = 70;

const cl = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const lin = (f: number, xs: number[], ys: number[]) => interpolate(f, xs, ys, cl);

// Mot qui se déroule lettre par lettre depuis le bas (chaque lettre monte dans le masque du bouton).
const Roll: React.FC<{text: string; f: number; start: number; step: number; dur?: number; offset?: number}> = ({
  text,
  f,
  start,
  step,
  dur = 6,
  offset = 0,
}) => (
  <>
    {text.split('').map((ch, i) => {
      const s = start + (i + offset) * step;
      const y = interpolate(f, [s, s + dur], [1, 0], {...cl, easing: Easing.out(Easing.cubic)});
      return (
        <span key={i} style={{display: 'inline-block', whiteSpace: 'pre', transform: `translateY(${y * FONT * 1.05}px)`}}>
          {ch}
        </span>
      );
    })}
  </>
);

const BoutonAbonnement: React.FC<{showPlate?: boolean}> = ({showPlate = true}) => {
  const f = useCurrentFrame();

  // 1. Carré qui monte puis s'étire en pilule
  const top = interpolate(f, [2.5, 13], [1085, PILL_TOP], {...cl, easing: Easing.out(Easing.cubic)});
  const w = interpolate(f, [13.3, 42], [120, 874], {...cl, easing: Easing.out(Easing.cubic)});
  const radius = interpolate(w, [120, 400, 874], [22, 40, 50], cl);
  const stretchBlur = lin(f, [3, 5, 8, 14, 18, 24, 28], [0, 2.5, 0, 0, 2.2, 1, 0]);

  // 2. Barre de progression (demi-largeur depuis le centre)
  const half = lin(f, [16, 17, 20, 24, 28, 32, 36, 40, 44, 48, 52], [0, 4, 31, 130, 221, 275, 310, 330, 342, 349, 350]);
  const split = lin(f, [59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73], [818, 810, 797, 780, 755, 730, 707, 687, 667, 655, 642, 635, 622, 616, 609]);

  // 3. La barre devient le bouton rouge
  const k = [81, 84, 88, 94];
  const bx0 = lin(f, k, [CX - half, 642, 662, 674]);
  const bx1 = lin(f, k, [CX + half, 1277, 1255, 1245]);
  const by0 = lin(f, k, [BAR_Y, 942, 929, 924]);
  const by1 = lin(f, k, [BAR_Y + BAR_H, 993, 1006, 1011]);
  const bRad = lin(f, k, [8.5, 8, 7, 7]);

  // 4. Clic : léger enfoncement puis gris, puis le bloc gris s'étend dans la pilule
  const press = lin(f, [123, 124.5, 126, 127.5], [1, 0.965, 0.965, 1]);
  const isGray = f >= 126.5;
  const ex = [129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 145];
  const gx0 = lin(f, ex, [674, 665, 647, 627, 610, 592, 580, 572, 567, 560, 555]);
  const gx1 = lin(f, ex, [1245, 1255, 1270, 1290, 1310, 1327, 1335, 1345, 1352, 1355, 1365]);
  const moveBlur = lin(f, [129, 130.5, 133, 135], [0, 3, 2, 0]);
  const textLeft = lin(f, [129, 132, 134, 136, 138, 140, 144], [782, 665, 625, 605, 590, 585, 581]);

  // 5. Sortie vers le bas
  const exitY = lin(f, [170, 176, 180, 184, 188, 190, 192, 194, 196, 198], [0, 5, 17, 30, 45, 65, 85, 118, 150, 178]);

  const showBar = f >= 16 && f < 81;
  const showButton = f >= 81;
  const expanding = f >= 129;
  const rx0 = expanding ? gx0 : CX + (bx0 - CX) * press;
  const rx1 = expanding ? gx1 : CX + (bx1 - CX) * press;
  const ry0 = expanding ? 923 : 967.5 + (by0 - 967.5) * press;
  const ry1 = expanding ? 1012 : 967.5 + (by1 - 967.5) * press;
  // texte centré dans le bouton rouge, puis calé à gauche (x=581) pendant l'extension
  const pc = (textLeft - 581) / (782 - 581);
  const anchor = 581 + pc * (CX - 581);

  return (
    <AbsoluteFill style={{fontFamily: HELV}}>
      <Plate show={showPlate} />
      <SfxTrack cues={SFX} />
      <AbsoluteFill style={{transform: `translateY(${exitY}px)`}}>
        {/* pilule blanche */}
        <div
          style={{
            position: 'absolute',
            left: CX - w / 2,
            top,
            width: w,
            height: PILL_H,
            borderRadius: radius,
            background: '#fff',
            filter: stretchBlur > 0.05 ? `blur(${stretchBlur}px)` : undefined,
            opacity: f < 2.5 ? 0 : 1,
          }}
        />
        {/* barre de progression */}
        {showBar && half > 0 && (
          <div
            style={{
              position: 'absolute',
              left: CX - half,
              top: BAR_Y,
              width: half * 2,
              height: BAR_H,
              borderRadius: BAR_H / 2,
              overflow: 'hidden',
              background: RED,
            }}
          >
            <div style={{position: 'absolute', left: 0, top: 0, bottom: 0, width: Math.max(0, split - (CX - half)), background: GREEN}} />
          </div>
        )}
        {/* bouton */}
        {showButton && (
          <div
            style={{
              position: 'absolute',
              left: rx0,
              top: ry0,
              width: rx1 - rx0,
              height: ry1 - ry0,
              borderRadius: expanding ? 8 : bRad,
              background: isGray ? GRAY : RED,
              overflow: 'hidden',
              filter: moveBlur > 0.05 ? `blur(${moveBlur}px)` : undefined,
            }}
          >
            <div
              style={{
                position: 'absolute',
                left: anchor - rx0,
                top: 941 - ry0 - 15,
                transform: `translateX(${-50 * pc}%)`,
                fontSize: FONT,
                lineHeight: `${FONT * 1.2}px`,
                fontWeight: 700,
                letterSpacing: 0,
                color: '#f4f4f4',
                whiteSpace: 'nowrap',
              }}
            >
              <Roll text="S'abonner" f={f} start={85} step={1.7} />
              <span style={{position: 'absolute', left: '100%', top: 0}}>
                {f >= 134 && <Roll text=" et changer" f={f} start={134} step={1.1} />}
              </span>
            </div>
          </div>
        )}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

export default BoutonAbonnement;

// Signaux sonores exportés pour la bibliothèque (cloud/cues_globaux.py).
export const cues = SFX;
