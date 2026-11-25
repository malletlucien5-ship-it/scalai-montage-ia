import React from 'react';
import {AbsoluteFill, Img, interpolate, staticFile, useCurrentFrame} from '../../shared/rt';
import {INTER_L} from '../../shared/localFonts';
import {SfxTrack, SfxCue} from '../../shared/Sfx';

// Référence 156.5-160.9 s : fond noir, lueur bleue en bas, cerveau filaire discret,
// phrase blanche grasse tapée lettre à lettre au centre avec curseur texte.
const FPS = 30;
const AT = 151.0; // « Parce que le vrai travail, c'est de réfléchir » (le = 151.14)
const DUR = Math.round((156.2 - AT) * FPS); // jusqu'à la fin de « copier-coller » (156.06)

const TEXT = 'le vrai travail, c’est de réfléchir';
const TYPE: [number, number] = [0.1, 2.3]; // début sur « le », fin après « réfléchir » (152.64)

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

// Dégradé ajusté sur la référence : cercle centré (800,1550), lueur cyan en bas,
// bleu marine en bas à gauche, reflet sarcelle en bas à droite.
const Background: React.FC = () => (
  <AbsoluteFill
    style={{
      background: [
        'radial-gradient(ellipse 720px 640px at 0px 1080px, rgba(0,24,110,0.85) 0%, rgba(0,24,110,0.35) 55%, rgba(0,24,110,0) 100%)',
        'radial-gradient(ellipse 620px 520px at 1920px 1080px, rgba(5,64,100,0.55) 0%, rgba(5,64,100,0) 100%)',
        'radial-gradient(circle 1820px at 800px 1550px, #03a4fa 0%, #019df7 25.9%, #0093ec 31.6%, #0084d4 37.3%, #016fb5 43%, #02528e 48.7%, #03376d 54.4%, #032044 60.1%, #041227 65.8%, #040817 71.5%, #04030f 77.2%, #040306 82.9%, #040203 88.6%, #040201 100%)',
      ].join(','),
    }}
  />
);

// Texte personnalisable (prop `texte`). Largeur visuelle conservée : un texte plus long réduit le corps.
const Scene: React.FC<{texte: string}> = ({texte}) => {
  const f = useCurrentFrame();
  const t = f / FPS;
  const brainOp = interpolate(t, [0.05, 0.45], [0, 1], clamp);
  const n = Math.floor(interpolate(t, TYPE, [1, texte.length], clamp));
  const taille = Math.min(98, (98 * TEXT.length) / Math.max(1, texte.length));
  return (
    <AbsoluteFill style={{overflow: 'hidden'}}>
      <Background />
      <Img src={staticFile('d207/cerveau.svg')} style={{position: 'absolute', left: 0, top: 0, width: 1920, height: 1080, opacity: 0.22 * brainOp}} />
      <div
        style={{
          position: 'absolute',
          left: 0,
          right: 0,
          top: 540 - 60,
          height: 120,
          lineHeight: '120px',
          textAlign: 'center',
          fontFamily: INTER_L,
          fontWeight: 800,
          fontSize: taille,
          letterSpacing: -1,
          color: '#fff',
          whiteSpace: 'pre',
          textShadow: '0 3px 10px rgba(0,0,0,0.45)',
        }}
      >
        {texte.slice(0, n)}
        <span style={{fontWeight: 700}}>|</span>
      </div>
    </AbsoluteFill>
  );
};

// Sons : whoosh à l'entrée du plein écran, frappe pendant la saisie.
const CUES: SfxCue[] = [
  {frame: 0, name: 'whoosh-transition'},
  {frame: Math.round(TYPE[0] * FPS), name: 'frappe-clavier', durationInFrames: Math.round((TYPE[1] - TYPE[0]) * FPS)},
];

const CerveauFrappe: React.FC<{showPlate?: boolean; texte?: string}> = ({texte = TEXT}) => (
  <AbsoluteFill style={{backgroundColor: '#030305'}}>
    <Scene texte={texte} />
    <SfxTrack cues={CUES} />
  </AbsoluteFill>
);

export const meta = {
  id: 'd207-cerveau-frappe',
  fps: FPS,
  durationInFrames: DUR,
  defaultProps: {showPlate: true},
  occurrences: [{ref: [156.5, 160.9] as [number, number], at: AT, from: 0, durationInFrames: DUR, mode: 'plein' as const}],
};
export default CerveauFrappe;

// Signaux sonores exportés pour la bibliothèque (cloud/cues_globaux.py).
export const cues = CUES;
