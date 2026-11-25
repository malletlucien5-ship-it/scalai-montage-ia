import React from 'react';
import {AbsoluteFill, Easing, interpolate, useCurrentFrame} from '../../shared/rt';
import {siOpenai} from 'simple-icons';
import {INTER_L} from '../../shared/localFonts';
import {Plate} from '../../shared/Plate';
import {SfxTrack, SfxCue} from '../../shared/Sfx';

// d205 : logo OpenAI blanc lumineux + « GPT 6 Astra » à droite du cadre.
// Réf. 68,83 s (apparition floue sur ~14 images, sans mouvement) -> 73,53 s (coupe franche).
// Géométrie relevée à 70,5 s (1920x1080) : logo 262 px centré (1440, 386), texte 1155..1728, ligne de base 637.
// Cible : « Le dernier modèle de ChatGPT, Astra, » : apparition sur « Astra » (50,89 s),
// tenue jusqu'à la fin de « ... à un tout autre niveau. » (55,95 s).
const FPS = 30;
const AT = 50.95;
const END = 56.05;
const DUR = Math.round((END - AT) * FPS);
const IN = 14;

const GLOW = 'drop-shadow(0 0 6px rgba(255,255,255,0.7)) drop-shadow(0 0 22px rgba(255,255,255,0.45))';

const Astra: React.FC<{showPlate?: boolean}> = ({showPlate = true}) => {
  const f = useCurrentFrame();
  const p = interpolate(f, [0, IN], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic)});
  const blur = (1 - p) * 22;
  return (
    <AbsoluteFill style={{overflow: 'hidden'}}>
      <Plate show={showPlate} />
      <AbsoluteFill style={{opacity: p, filter: `blur(${blur.toFixed(2)}px)`}}>
        <svg
          viewBox="0 0 24 24"
          width={262}
          height={262}
          style={{position: 'absolute', left: 1440 - 131, top: 386 - 131, filter: GLOW, overflow: 'visible'}}
        >
          <path d={siOpenai.path} fill="#fff" />
        </svg>
        <div
          style={{
            position: 'absolute',
            left: 1441 - 400,
            width: 800,
            top: 637 - 99,
            textAlign: 'center',
            fontFamily: INTER_L,
            fontWeight: 700,
            fontSize: 101,
            letterSpacing: -1.8,
            lineHeight: '120px',
            color: '#fff',
            whiteSpace: 'nowrap',
            filter: GLOW,
          }}
        >
          GPT 6 Astra
        </div>
      </AbsoluteFill>
      <SfxTrack cues={cuesExportees} />
    </AbsoluteFill>
  );
};

export const meta = {
  id: 'd205-logo-astra',
  fps: FPS,
  durationInFrames: DUR,
  defaultProps: {showPlate: true},
  occurrences: [{ref: [68.83, 73.53] as [number, number], at: AT, from: 0, durationInFrames: DUR, mode: 'plein' as const}],
};
export default Astra;

// Signaux sonores exportés pour la bibliothèque (cloud/cues_globaux.py).
const cuesExportees: SfxCue[] = [{frame: 1, name: 'grave-apparition'}];
export const cues = cuesExportees;
