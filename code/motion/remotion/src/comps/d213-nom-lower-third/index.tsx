import React from 'react';
import {AbsoluteFill, Easing, Sequence, interpolate, useCurrentFrame} from '../../shared/rt';
import {INTER_L} from '../../shared/localFonts';
import {Plate} from '../../shared/Plate';
import {SfxTrack, SfxCue} from '../../shared/Sfx';

// d213 : barre de verre fumé en bas à gauche avec le nom et le rôle.
// Réf. 255,13 -> 258,83 s (apparition floue ~8 images au passage sur le plan de coupe, sortie en coupe franche).
// Géométrie relevée à 257,5 s (1920x1080) : boîte 30..1021 x 908..1012 (104 px), rayon ~22, liseré clair 1,5 px ;
// premier élément à x 55, texte gras blanc capitale 22 px (~30 px), séparateur vertical fin, titre 21 px après,
// marge droite 95 px. Dégradé vertical relevé : clair en haut (#6E747C), creux sombre à mi-hauteur (#16202C),
// remontée vers #4A535D en bas ; bas droit plus clair (#565658).
// Personnalisation : pas d'icône Instagram ni de pseudo ; « Grégory | Responsable des événements ».
// Cible : « qui s'appelle Grégory » (272,84) -> ~4 s, fin avant « Et à lui seul » (275,10) prolongée comme chez Dan (3,7 s).
const FPS = 30;
const OCC = {ref: [255.13, 258.83] as [number, number], start: 272.84, end: 276.7};
const DUR = Math.round((OCC.end - OCC.start) * FPS);
const IN = 8;
const CUES: SfxCue[] = [{frame: 0, name: 'grave-apparition'}];

const TXT: React.CSSProperties = {fontFamily: INTER_L, fontWeight: 700, fontSize: 30, lineHeight: 1, color: '#FFFFFF', whiteSpace: 'pre', letterSpacing: '0.005em', textShadow: '0 1px 3px rgba(0,0,0,0.45)'};

const Bar: React.FC = () => {
  const f = useCurrentFrame();
  const k = interpolate(f, [0, IN], [0, 1], {extrapolateRight: 'clamp', easing: Easing.out(Easing.quad)});
  const op = interpolate(f, [0, 1, 3, 6, IN], [0.2, 0.4, 0.7, 0.93, 1], {extrapolateRight: 'clamp'});
  return (
    <div
      style={{
        position: 'absolute',
        left: 30,
        top: 908,
        height: 104,
        boxSizing: 'border-box',
        padding: '0 95px 0 25px',
        display: 'flex',
        alignItems: 'center',
        borderRadius: 22,
        border: '1.5px solid rgba(196,202,210,0.7)',
        background:
          'linear-gradient(90deg, rgba(0,0,0,0) 45%, rgba(130,120,120,0.16) 88%, rgba(90,95,105,0.1) 100%), linear-gradient(180deg, #6E747C 0%, #4C525A 8%, #3D434D 18%, #313B44 28%, #212A31 40%, #16202C 50%, #1D2330 57%, #292F3C 67%, #343D46 78%, #3F4952 90%, #4A535D 100%)',
        boxShadow: '0 0 0 1px rgba(0,0,0,0.35), inset 0 1px 0 rgba(255,255,255,0.18), 0 6px 20px rgba(0,0,0,0.35)',
        opacity: op,
        transform: `translateY(${6 * (1 - k)}px)`,
        filter: k < 0.98 ? `blur(${(9 * Math.pow(1 - k, 1.4)).toFixed(2)}px)` : undefined,
      }}
    >
      <span style={TXT}>Grégory</span>
      <div style={{width: 1.5, height: 36, margin: '0 21px 0 29px', background: 'rgba(200,205,212,0.55)'}} />
      <span style={TXT}>Responsable des événements</span>
    </div>
  );
};

const NomLowerThird: React.FC<{showPlate?: boolean}> = ({showPlate = true}) => (
  <AbsoluteFill style={{overflow: 'hidden'}}>
    <Plate show={showPlate} />
    <Sequence from={0} durationInFrames={DUR} layout="none">
      <Bar />
    </Sequence>
    <SfxTrack cues={CUES} />
  </AbsoluteFill>
);

export const meta = {
  id: 'd213-nom-lower-third',
  fps: FPS,
  durationInFrames: DUR,
  defaultProps: {showPlate: true},
  occurrences: [{ref: OCC.ref, at: OCC.start, from: 0, durationInFrames: DUR, mode: 'plein' as const}],
};
export default NomLowerThird;

// Signaux sonores exportés pour la bibliothèque (cloud/cues_globaux.py).
export const cues = CUES;
