import React from 'react';
import {AbsoluteFill, Sequence, useCurrentFrame} from '../../shared/rt';
import {Plate} from '../../shared/Plate';
import {SfxTrack, SfxCue} from '../../shared/Sfx';
import {GlossyPill, GlossySpec} from './GlossyPill';

// d209 : bouton « Pro Tip » en bas à droite -> « Astuce ».
// Réf. 186,77 -> 203,7 s (apparition sur « a pro tip », coupe franche avant « Next ») et 586,1 -> 601,3 s.
// Géométrie relevée à 190 s : boîte 1563..1886 x 869..984 (323 x 116), rayon ~24, texte gras capitale 41 px (~56 px).
// Cible : « Et petite astuce » (195,27) -> fin de « bienvenue au club. » (213,56), avant « Ensuite » ;
//         « voici une astuce » (640,89) -> fin de « la méthode du caméscope. » (661,63).
const FPS = 30;
const PILL: GlossySpec = {text: 'Astuce', right: 1886, bottom: 984, h: 116, size: 56, padX: 66, radius: 24};

const OCCS = [
  {ref: [186.7, 203.7] as [number, number], start: 195.17, end: 213.7},
  {ref: [586.1, 601.3] as [number, number], start: 640.79, end: 661.75},
];
const GAP = 15;
const plan = (() => {
  let from = 0;
  return OCCS.map((o) => {
    const dur = Math.round((o.end - o.start) * FPS);
    const p = {o, from, dur};
    from += dur + GAP;
    return p;
  });
})();

// grave-apparition sur la première image visible du bouton.
const CUES: SfxCue[] = plan.map(({from}) => ({frame: from, name: 'grave-apparition' as const}));

// Libellé personnalisable par placement (prop `libelle`). Défaut : « Astuce » (dan2).
const OccView: React.FC<{libelle: string}> = ({libelle}) => {
  const frame = useCurrentFrame();
  return <GlossyPill p={{...PILL, text: libelle}} frame={frame} />;
};

const ProTip: React.FC<{showPlate?: boolean; libelle?: string}> = ({showPlate = true, libelle = PILL.text}) => (
  <AbsoluteFill style={{overflow: 'hidden'}}>
    <Plate show={showPlate} />
    {plan.map(({from, dur}, i) => (
      <Sequence key={i} from={from} durationInFrames={dur} layout="none">
        <OccView libelle={libelle} />
      </Sequence>
    ))}
    <SfxTrack cues={CUES} />
  </AbsoluteFill>
);

export const meta = {
  id: 'd209-pro-tip',
  fps: FPS,
  durationInFrames: plan[plan.length - 1].from + plan[plan.length - 1].dur,
  defaultProps: {showPlate: true},
  occurrences: plan.map(({o, from, dur}) => ({ref: o.ref, at: o.start, from, durationInFrames: dur, mode: 'plein' as const})),
};
export default ProTip;

// Signaux sonores exportés pour la bibliothèque (cloud/cues_globaux.py).
export const cues = CUES;
