import React from 'react';
import {AbsoluteFill, interpolate, OffthreadVideo, staticFile, useCurrentFrame} from '../../shared/rt';
import {SfxTrack, SfxCue} from '../../shared/Sfx';
import {INTER_L} from '../../shared/localFonts';

// 08 : salle de contrôle (image IA), l'écran central affiche « 2 + 2 = ? » caractère par caractère.
// Référence 42,61 s à 45,95 s. Fond : image IA animée (seedance, 5 s) lue à 0,52x pour retrouver
// la poussée de l'original (x1,063 en 3,35 s). Le texte suit la poussée mesurée sur la vidéo.
export const meta = {
  id: '08-salle-controle',
  durationInFrames: 100,
  fps: 30,
  occurrences: [{ref: [42.61, 45.95], from: 0, durationInFrames: 100, mode: 'plein'}],
};

// Apparition sèche de chaque caractère (relevée à 10 i/s).
// x = centre du caractère en coordonnées monde (avant poussée).
const CHARS: {c: string; at: number; x: number; small?: boolean}[] = [
  {c: '2', at: 19, x: 771},
  {c: '+', at: 35, x: 839, small: true},
  {c: '2', at: 42, x: 905},
  {c: '=', at: 57, x: 980, small: true},
  {c: '?', at: 70, x: 1046},
];

export default function SalleControle() {
  const f = useCurrentFrame();
  const RATE = 0.52;
  const vt = (f / 30) * RATE;
  // Zoom de la vidéo générée mesuré par recalage d'images, centre (850, 450).
  const s = interpolate(vt, [0, 0.35, 0.7, 1.05, 1.4, 1.75], [1, 1.0075, 1.015, 1.0275, 1.05, 1.0675], {extrapolateRight: 'extend'});
  return (
    <AbsoluteFill style={{background: '#02060d', overflow: 'hidden'}}>
      <OffthreadVideo src={staticFile('08/salle-controle.mp4')} muted playbackRate={RATE} style={{width: '100%', height: '100%'}} />
      <AbsoluteFill style={{transformOrigin: '850px 450px', transform: `scale(${s})`}}>
        {CHARS.map((ch, i) => (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: ch.x - 60,
              width: 120,
              top: 356 - 100,
              height: 100,
              display: 'flex',
              alignItems: 'flex-end',
              justifyContent: 'center',
              opacity: f >= ch.at ? 1 : 0,
              fontFamily: `"SF Pro Display", -apple-system, ${INTER_L}, sans-serif`,
              fontWeight: 600,
              fontSize: ch.c === '+' ? 76 : ch.c === '=' ? 86 : 94,
              lineHeight: 1,
              color: '#3fd2ff',
              textShadow: '0 0 10px rgba(40,170,255,0.75), 0 0 26px rgba(30,140,255,0.45)',
            }}
          >
            <span style={{transform: `translateY(${ch.small ? -8 : 0}px)`, display: 'inline-block', marginBottom: -12}}>{ch.c}</span>
          </div>
        ))}
      </AbsoluteFill>
      {/* Bruitages : nappe en ouverture, grave à l'arrivée de la ligne « 2 + 2 = ? » (premier caractère, image 19). */}
      <SfxTrack
        cues={cuesExportees}
      />
    </AbsoluteFill>
  );
}

// Signaux sonores exportés pour la bibliothèque (cloud/cues_globaux.py).
const cuesExportees: SfxCue[] = [
          {frame: 0, name: 'nappe-ecran-titre'},
          {frame: 19, name: 'grave-apparition'},
        ];
export const cues = cuesExportees;
