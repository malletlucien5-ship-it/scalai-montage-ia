import React from 'react';
import {AbsoluteFill, useCurrentFrame} from '../../shared/rt';
import {Plate} from '../../shared/Plate';
import {SfxTrack, SfxCue} from '../../shared/Sfx';
import {Pill, PillSpec} from './Pill';

const FPS = 30;
const START = 87.5; // réf.
const END = 89.7;

// Icône « Projets » de Claude, relevée sur l'original (origine x 734, y 914) :
// barre 1 de 54 x 8 px, barre 2 de 72 x 9 px, bac de 93 x 62 px au trait de 7 px.
const ProjectsIcon: React.FC = () => (
  <svg width={94} height={97} viewBox="0 0 94 97" style={{flex: 'none', marginTop: 1}}>
    <g fill="none" stroke="#6CCFE6" strokeLinecap="round" strokeLinejoin="round">
      <line x1={24} y1={4} x2={70} y2={4} strokeWidth={8} />
      <line x1={15.5} y1={21.5} x2={78.5} y2={21.5} strokeWidth={8.5} />
      <path d="M 11.5 37.5 L 82.5 37.5 Q 90 37.5 89.3 45 L 84.5 85 Q 83.5 92.5 76 92.5 L 18 92.5 Q 10.5 92.5 9.5 85 L 4.7 45 Q 4 37.5 11.5 37.5 Z" strokeWidth={7} />
    </g>
  </svg>
);

const P: PillSpec = {
  style: 'name',
  text: 'Projets',
  in: 87.6 - START,
  out: {t: 88.75 - START, kind: 'slide'},
  bottom: 1039,
  h: 158,
  size: 80,
  padX: 40,
  w: 535,
  icon: <ProjectsIcon />,
};

// Bruitages (SFX-REGLES.md) : grave-apparition à l'arrivée (première image où la pilule dépasse du bas du cadre)
// et au départ de la sortie par le bas. L'original en compte deux sur cette plage.
const CUES: SfxCue[] = [
  {frame: Math.round(P.in * FPS) + 1, name: 'grave-apparition'},
  {frame: Math.round(P.out!.t * FPS), name: 'grave-apparition'},
];

const PiluleProjets: React.FC<{showPlate?: boolean}> = ({showPlate = true}) => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{backgroundColor: 'transparent', overflow: 'hidden'}}>
      <Plate show={showPlate} />
      <Pill p={P} frame={frame} />
      <SfxTrack cues={CUES} />
    </AbsoluteFill>
  );
};

export const meta = {
  id: '13-pilule-projets',
  durationInFrames: Math.round((END - START) * FPS),
  fps: FPS,
  defaultProps: {showPlate: true},
  occurrences: [{ref: [START, END] as [number, number], from: 0, durationInFrames: Math.round((END - START) * FPS), mode: 'overlay' as const}],
};
export default PiluleProjets;

// Signaux sonores exportés pour la bibliothèque (cloud/cues_globaux.py).
export const cues = CUES;
