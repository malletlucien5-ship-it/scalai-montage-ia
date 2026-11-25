import React from 'react';
import {AbsoluteFill, OffthreadVideo, staticFile} from '../../shared/rt';
import {SfxTrack, SfxCue} from '../../shared/Sfx';

// 03 : iceberg « Claude ». Référence 10,28-14,25 s (119 images).
// Décision de Lucien : la plage n'a aucun texte incrusté, on reprend le métrage original
// (extrait copié dans public/03/iceberg-ref.mp4, recalé à 30 i/s).
export const meta = {
  id: '03-iceberg-claude',
  durationInFrames: 119,
  fps: 30,
  occurrences: [{ref: [10.28, 14.25], from: 0, durationInFrames: 119, mode: 'plein'}],
};

export default function Iceberg() {
  return (
    <AbsoluteFill style={{backgroundColor: '#0E0E10'}}>
      <OffthreadVideo src={staticFile('03/iceberg-ref.mp4')} muted style={{width: '100%', height: '100%'}} />
      {/* Bruitages : choc à l'apparition de l'iceberg, nappe sous la bascule sous l'eau (image 48). */}
      <SfxTrack
        cues={cuesExportees}
      />
    </AbsoluteFill>
  );
}

// Signaux sonores exportés pour la bibliothèque (cloud/cues_globaux.py).
const cuesExportees: SfxCue[] = [
          {frame: 0, name: 'impact-chapitre'},
          {frame: 48, name: 'nappe-ecran-titre'},
        ];
export const cues = cuesExportees;
