import React from 'react';
import {AbsoluteFill, Sequence, useCurrentFrame} from '../../shared/rt';
import {Plate} from '../../shared/Plate';
import {SfxTrack, SfxCue} from '../../shared/Sfx';
import {GlossyPill, GlossySpec} from '../d209-pro-tip/GlossyPill';

// d208 : bouton noir brillant « chatgpt.com/download » en bas à droite (même style que d209).
// Réf. 173,03 -> 177,8 s (apparition floue ~11 images, coupe franche avant « Go to your settings »).
// Géométrie relevée à 176,5 s : boîte 1414..1903 x 850..963 (489 x 113), texte 1448..1871, hauteur du « h » 29 px (~40 px).
// Cible : « re-télécharger ChatGPT » (« télécharger » 172,56) -> fin de « ... pas particulièrement fan. » (178,17).
const FPS = 30;
const PILL: GlossySpec = {text: 'chatgpt.com/download', right: 1903, bottom: 963, h: 113, size: 38, padX: 34, radius: 24};
const OCC = {ref: [173.0, 177.8] as [number, number], start: 172.46, end: 178.3};
const DUR = Math.round((OCC.end - OCC.start) * FPS);
const CUES: SfxCue[] = [{frame: 0, name: 'grave-apparition'}];

const OccView: React.FC = () => {
  const frame = useCurrentFrame();
  return <GlossyPill p={PILL} frame={frame} />;
};

const PiluleUrl: React.FC<{showPlate?: boolean}> = ({showPlate = true}) => (
  <AbsoluteFill style={{overflow: 'hidden'}}>
    <Plate show={showPlate} />
    <Sequence from={0} durationInFrames={DUR} layout="none">
      <OccView />
    </Sequence>
    <SfxTrack cues={CUES} />
  </AbsoluteFill>
);

export const meta = {
  id: 'd208-pilule-url',
  fps: FPS,
  durationInFrames: DUR,
  defaultProps: {showPlate: true},
  occurrences: [{ref: OCC.ref, at: OCC.start, from: 0, durationInFrames: DUR, mode: 'plein' as const}],
};
export default PiluleUrl;

// Signaux sonores exportés pour la bibliothèque (cloud/cues_globaux.py).
export const cues = CUES;
