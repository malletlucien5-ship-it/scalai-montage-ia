import React from 'react';
import {AbsoluteFill, Easing, interpolate, OffthreadVideo, Sequence, staticFile, useCurrentFrame} from '../../shared/rt';
import {SfxTrack, SfxCue} from '../../shared/Sfx';
import {INTER} from '../../shared/fonts';

// 34 : images IA animées (seedance, 5 s) plein cadre avec texte cinétique mot à mot en haut à gauche.
// Occurrences : 534,93-540,24 s (159 i), 672,81-676,94 s (124 i), 815,75-820,55 s (144 i).
// 15 images de fond neutre entre deux occurrences.

type Word = {w: string; at: number};
type Occ = {
  img: string;
  rate: number; // vitesse de lecture de la vidéo générée (5 s)
  dur: number;
  size: number; // taille de police
  lh: number; // interligne
  left: number;
  top: number; // haut des capitales de la ligne 1
  push: [number, number]; // échelle début, fin
  origin: string;
  lines: Word[][];
};

const OCCS: Occ[] = [
  {
    img: '34/directeur.mp4',
    rate: 0.94,
    dur: 159,
    size: 84,
    lh: 106,
    left: 72,
    top: 91,
    push: [1, 1],
    origin: '75% 55%',
    lines: [
      [
        {w: 'Avec', at: 48},
        {w: "l'IA,", at: 57},
        {w: 'ils', at: 81},
        {w: 'dirigent', at: 90},
        {w: 'le', at: 96},
        {w: 'travail,', at: 105},
      ],
      [
        {w: 'Ils', at: 114},
        {w: 'ne', at: 120},
        {w: 'font', at: 124},
        {w: 'pas', at: 128},
        {w: 'que', at: 132},
        {w: "l'exécuter", at: 138},
      ],
    ],
  },
  {
    img: '34/developpeur.mp4',
    rate: 1,
    dur: 124,
    size: 86,
    lh: 108,
    left: 60,
    top: 100,
    push: [1, 1],
    origin: '68% 50%',
    lines: [
      [
        {w: 'Dans', at: 3},
        {w: 'le', at: 6},
        {w: 'monde', at: 9},
        {w: 'de', at: 12},
        {w: "l'IA,", at: 15},
        {w: 'le', at: 48},
        {w: 'français', at: 52},
      ],
      [
        {w: 'est', at: 72},
        {w: 'le', at: 78},
        {w: 'nouveau', at: 84},
        {w: 'langage', at: 87},
        {w: 'de', at: 90},
        {w: 'programmation', at: 93},
      ],
    ],
  },
  {
    img: '34/orchestrateur.mp4',
    rate: 0.6, // la vidéo générée recadre plus que l'original : lecture ralentie
    dur: 144,
    size: 78,
    lh: 95,
    left: 54,
    top: 80,
    push: [1, 1],
    origin: '55% 45%',
    lines: [
      [
        {w: 'On', at: 3},
        {w: 'construit', at: 9},
        {w: 'la', at: 12},
        {w: 'machine', at: 18},
      ],
      [
        {w: 'qui', at: 36},
        {w: 'fait', at: 42},
        {w: 'tourner', at: 48},
        {w: 'la', at: 51},
        {w: 'machine', at: 57},
      ],
    ],
  },
];

const GAP = 15;

// Entrée d'un mot : monte de 26 px, passe de transparent à blanc, perd un léger flou.
const WordSpan: React.FC<{w: Word; f: number; size: number}> = ({w, f, size}) => {
  const t = interpolate(f, [w.at, w.at + 10], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });
  return (
    <span
      style={{
        display: 'inline-block',
        marginRight: size * 0.26,
        opacity: f < w.at ? 0 : interpolate(t, [0, 1], [0.35, 1]),
        transform: `translateY(${(1 - t) * 26}px)`,
        filter: `blur(${(1 - t) * 3}px)`,
      }}
    >
      {w.w}
    </span>
  );
};

const Scene: React.FC<{o: Occ}> = ({o}) => {
  const f = useCurrentFrame();
  const s = interpolate(f, [0, o.dur - 1], o.push);
  // Le haut des capitales Inter est à ~0,2 em sous le haut de la boîte de ligne (interligne = lh).
  const boxTop = o.top - (o.lh - o.size) / 2 - o.size * 0.2;
  return (
    <AbsoluteFill style={{background: '#000', overflow: 'hidden'}}>
      <AbsoluteFill style={{transform: `scale(${s})`, transformOrigin: o.origin}}>
        <OffthreadVideo src={staticFile(o.img)} muted playbackRate={o.rate} style={{width: '100%', height: '100%'}} />
      </AbsoluteFill>
      <div
        style={{
          position: 'absolute',
          left: o.left,
          top: boxTop,
          width: 1840,
          fontFamily: INTER,
          fontWeight: 700,
          fontSize: o.size,
          lineHeight: `${o.lh}px`,
          letterSpacing: -0.5,
          whiteSpace: 'nowrap',
          color: '#ffffff',
          // Dégradé horizontal : gris à gauche, blanc à partir de ~640 px (masque d'opacité).
          WebkitMaskImage: 'linear-gradient(90deg, rgba(0,0,0,0.55) 0px, rgba(0,0,0,0.72) 300px, #000 640px)',
        }}
      >
        {o.lines.map((line, i) => (
          <div key={i}>
            {line.map((w, j) => (
              <WordSpan key={j} w={w} f={f} size={o.size} />
            ))}
          </div>
        ))}
      </div>
    </AbsoluteFill>
  );
};

const starts: number[] = [];
let acc = 0;
for (const o of OCCS) {
  starts.push(acc);
  acc += o.dur + GAP;
}
const TOTAL = acc - GAP;

export const meta = {
  id: '34-images-ia-titres',
  durationInFrames: TOTAL,
  fps: 30,
  // from = 0, 174, 313.
  occurrences: [
    [534.93, 540.24],
    [672.81, 676.94],
    [815.75, 820.55],
  ].map((ref, i) => ({ref, from: starts[i], durationInFrames: OCCS[i].dur, mode: 'plein'})),
};

export default function ImagesIaTitres() {
  return (
    <AbsoluteFill style={{background: '#0b0d12'}}>
      {OCCS.map((o, i) => (
        <Sequence key={i} from={starts[i]} durationInFrames={o.dur}>
          <Scene o={o} />
        </Sequence>
      ))}
      {/* Bruitages. Scènes à 0, 174, 313 : nappe en ouverture, grave à l'arrivée de chaque ligne de texte. */}
      <SfxTrack
        cues={cuesExportees}
      />
    </AbsoluteFill>
  );
}

// Signaux sonores exportés pour la bibliothèque (cloud/cues_globaux.py).
const cuesExportees: SfxCue[] = [
          {frame: 0, name: 'nappe-ecran-titre'},
          {frame: 48, name: 'grave-apparition'},
          {frame: 114, name: 'grave-apparition'},
          {frame: 174, name: 'nappe-ecran-titre'},
          {frame: 177, name: 'grave-apparition'},
          {frame: 246, name: 'grave-apparition'},
          {frame: 313, name: 'nappe-ecran-titre'},
          {frame: 316, name: 'grave-apparition'},
          {frame: 349, name: 'grave-apparition'},
        ];
export const cues = cuesExportees;
