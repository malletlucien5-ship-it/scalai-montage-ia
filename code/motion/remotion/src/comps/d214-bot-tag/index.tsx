import React from 'react';
import {AbsoluteFill, Sequence, useCurrentFrame} from '../../shared/rt';
import {INTER_L} from '../../shared/localFonts';
import {Plate} from '../../shared/Plate';
import {SfxTrack, SfxCue} from '../../shared/Sfx';

// d214 : étiquette de bot en bas à gauche (carte gris foncé + mascotte colorée).
// Réf. 454,73 s « Sales Bot » (montée depuis le bas du cadre), 469,2 s « Finance Bot » monte par-dessus
// et recouvre la première carte (dont un liseré reste visible au-dessus), coupe franche à 482,0 s.
// Géométrie relevée (1920x1080) : carte x 64 (61 pour la 2e), haut 852, bas 1000 (148 px), rayon ~14,
// fond opaque #2E2E2E, liseré 1,5 px #BEBCBD ; texte blanc regular capitale 29 px (~41 px) à x 241, marge droite 31 ;
// mascotte rose #DE2885 : triangle arrondi 97..203 x 877..974 ; mascotte verte #009753 : gélule 90..203 x 889..962 ;
// yeux noirs en capsules inclinées 7 x 20.
// Les deux cartes ont la même largeur (celle de « Bot commercial ») pour que la seconde recouvre la première comme chez Dan.
// Mouvement mesuré : écart initial ~200 px sous la place, x0,88 par image, léger flou et fondu sur les 4 premières images.
// Cible : « mon bot commercial » (486,19) ; « Mon bot financier » (509,77) jusqu'à la fin de la phrase équivalente
// à celle où Dan garde l'étiquette (« ... le travail d'une entreprise entière. » 527,68).
const FPS = 30;
const OCC = {ref: [454.73, 482.0] as [number, number], start: 486.12, end: 527.8};
const DUR = Math.round((OCC.end - OCC.start) * FPS);
const SECOND = Math.round((509.7 - OCC.start) * FPS);

const Pink: React.FC = () => (
  <svg width={1920} height={1080} style={{position: 'absolute', left: 0, top: 0}}>
    <polygon points="150,886 106,965 194,965" fill="#DE2885" stroke="#DE2885" strokeWidth={18} strokeLinejoin="round" />
    <rect x={146.5} y={920} width={7} height={20} rx={3.5} fill="#111111" transform="rotate(-14 150 930)" />
    <rect x={170.5} y={916} width={7} height={20} rx={3.5} fill="#111111" transform="rotate(-14 174 926)" />
  </svg>
);
const Green: React.FC = () => (
  <svg width={1920} height={1080} style={{position: 'absolute', left: 0, top: 0}}>
    <rect x={90} y={889} width={113} height={73} rx={36.5} fill="#009753" />
    <rect x={146.5} y={908} width={7} height={20} rx={3.5} fill="#111111" transform="rotate(-14 150 918)" />
    <rect x={176.5} y={903} width={7} height={20} rx={3.5} fill="#111111" transform="rotate(-14 180 913)" />
  </svg>
);

const Card: React.FC<{f: number; left: number; top: number; width: number; text: string; icon: React.ReactNode}> = ({f, left, top, width, text, icon}) => {
  if (f < 0) return null;
  const dy = 200 * Math.pow(0.88, f);
  const op = Math.min(1, 0.55 + f * 0.12);
  const blur = f < 4 ? 2.5 * (1 - f / 4) : 0;
  return (
    <div style={{position: 'absolute', left: 0, top: 0, width: 1920, height: 1080, transform: `translateY(${dy}px)`, opacity: op, filter: blur > 0.1 ? `blur(${blur}px)` : undefined}}>
      <div
        style={{
          position: 'absolute',
          left,
          top,
          height: 148,
          width,
          boxSizing: 'border-box',
          padding: `0 31px 0 ${241 - left}px`,
          display: 'flex',
          alignItems: 'center',
          background: '#2E2E2E',
          border: '1.5px solid #BEBCBD',
          borderRadius: 14,
          boxShadow: '0 0 0 1px rgba(0,0,0,0.55), 0 6px 18px rgba(0,0,0,0.3)',
        }}
      >
        <span style={{fontFamily: INTER_L, fontWeight: 400, fontSize: 41, lineHeight: 1, color: '#FFFFFF', whiteSpace: 'pre', letterSpacing: '-0.005em'}}>{text}</span>
      </div>
      <div style={{position: 'absolute', left: left - 64, top: top - 852, width: 1920, height: 1080}}>{icon}</div>
    </div>
  );
};

const Tags: React.FC = () => {
  const f = useCurrentFrame();
  return (
    <>
      <Card f={f} left={64} top={852} width={505} text="Bot commercial" icon={<Pink />} />
      <Card f={f - SECOND} left={61} top={856} width={511} text="Bot financier" icon={<Green />} />
    </>
  );
};

// grave-apparition sur l'arrivée de chaque carte.
const CUES: SfxCue[] = [
  {frame: 0, name: 'grave-apparition'},
  {frame: SECOND, name: 'grave-apparition'},
];

const BotTag: React.FC<{showPlate?: boolean}> = ({showPlate = true}) => (
  <AbsoluteFill style={{overflow: 'hidden'}}>
    <Plate show={showPlate} />
    <Sequence from={0} durationInFrames={DUR} layout="none">
      <Tags />
    </Sequence>
    <SfxTrack cues={CUES} />
  </AbsoluteFill>
);

export const meta = {
  id: 'd214-bot-tag',
  fps: FPS,
  durationInFrames: DUR,
  defaultProps: {showPlate: true},
  occurrences: [{ref: OCC.ref, at: OCC.start, from: 0, durationInFrames: DUR, mode: 'plein' as const}],
};
export default BotTag;

// Signaux sonores exportés pour la bibliothèque (cloud/cues_globaux.py).
export const cues = CUES;
