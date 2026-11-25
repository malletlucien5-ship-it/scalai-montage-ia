import React from 'react';
import {AbsoluteFill, CalculateMetadataFunction, Sequence, interpolate, useCurrentFrame} from '../../shared/rt';
import {Plate} from '../../shared/Plate';
import {SfxTrack, SfxCue} from '../../shared/Sfx';
import {Badge} from '../05-badge-niveau/index';

// Badge de niveau de 05 posé sur les chapitres de la vidéo de Lucien (temps en secondes de sa vidéo).
// Entrée mesurée sur l'original : apparition sèche. Sortie mesurée : fondu de 13 images qui finit à `end`.
const FPS = 30;
const FADE = 13;

export type Chapitre = {niveau: number; label?: string; start: number; end: number};
export type Props = {chapitres: Chapitre[]; durationInFrames: number; showPlate?: boolean};

const ChapitreView: React.FC<{c: Chapitre; dur: number}> = ({c, dur}) => {
  const frame = useCurrentFrame();
  const op = interpolate(frame, [dur - FADE, dur], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const level = Math.min(5, Math.max(0, Math.round(c.niveau) - 1));
  return op > 0 ? <Badge level={level} label={c.label} opacity={op} /> : null;
};

const BadgeChapitres: React.FC<Props> = ({chapitres, showPlate = false}) => {
  // grave-apparition à chaque entrée de badge (SFX-REGLES.md).
  const cues: SfxCue[] = chapitres.map((c) => ({frame: Math.round(c.start * FPS), name: 'grave-apparition'}));
  return (
    <AbsoluteFill style={{backgroundColor: 'transparent'}}>
      <Plate show={showPlate} />
      {chapitres.map((c, i) => {
        const from = Math.round(c.start * FPS);
        const dur = Math.max(1, Math.round(c.end * FPS) - from);
        return (
          <Sequence key={i} from={from} durationInFrames={dur} layout="none">
            <ChapitreView c={c} dur={dur} />
          </Sequence>
        );
      })}
      <SfxTrack cues={cues} force />
    </AbsoluteFill>
  );
};

export const calculateMetadata: CalculateMetadataFunction<Props> = ({props}) => ({durationInFrames: props.durationInFrames});

const DEFAULT: Props = {
  durationInFrames: 240,
  showPlate: false,
  chapitres: [
    {niveau: 1, start: 0.5, end: 3.5},
    {niveau: 2, label: 'Niv. 2/6 : Habitué', start: 4.0, end: 7.5},
  ],
};

export const meta = {
  id: '05b-badge-chapitres',
  durationInFrames: DEFAULT.durationInFrames,
  fps: FPS,
  defaultProps: DEFAULT,
  calculateMetadata,
};
export default BadgeChapitres;

// Signaux calculés depuis les props : le son interne reste actif (force).
export const cuesDynamiques = true;
