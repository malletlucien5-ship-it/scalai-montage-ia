import React from 'react';
import {AbsoluteFill, Sequence, useCurrentFrame} from '../../shared/rt';
import {Plate} from '../../shared/Plate';
import {SfxTrack, SfxCue} from '../../shared/Sfx';
import {Pill, PillSpec} from './Pill';

const FPS = 30;

// Occurrences relevées (temps réf. en secondes). Géométrie mesurée sur des images 1920x1080.
const TIP = (text: string, inT: number, out: PillSpec['out'], bottom = 1041): PillSpec => ({style: 'tip', text, in: inT, out, bottom, h: 157, size: 88, padX: 47, w: 453});

const OCC: {start: number; end: number; pills: PillSpec[]}[] = [
  {start: 198.5, end: 202.4, pills: [TIP('ASTUCE', 198.72, {t: 201.55, kind: 'fade'})]},
  {start: 336.0, end: 339.4, pills: [{style: 'tip', text: 'Coup avancé', in: 336.19, out: {t: 338.73, kind: 'fade'}, bottom: 1014, h: 144, size: 80, padX: 26, w: 700}]},
  {start: 375.9, end: 377.95, pills: [TIP('ASTUCE', 376.033, {t: 377.036, kind: 'slide'})]},
  {
    start: 540.0,
    end: 544.3,
    pills: [
      TIP('ASTUCE', 540.3, {t: 541.70, kind: 'slide'}),
      {style: 'name', text: 'Enchaîne tes skills', in: 542.733, bottom: 1045, h: 177, size: 94, padX: 23, w: 928},
    ],
  },
  {
    start: 677.4,
    end: 682.4,
    pills: [
      TIP('ASTUCE', 677.567, {t: 679.435, kind: 'slide'}),
      {style: 'name', text: 'Mode Plan', in: 680.7, bottom: 1037, h: 177, size: 90, padX: 57, w: 579},
    ],
  },
  {
    start: 704.9,
    end: 710.6,
    pills: [
      TIP('ASTUCE', 704.967, {t: 706.136, kind: 'slide'}),
      {style: 'name', text: 'Claude Code Remote', in: 707.5, bottom: 1031, h: 166, size: 83, padX: 21, w: 922},
    ],
  },
  {start: 833.8, end: 835.05, pills: [TIP('ASTUCE', 833.834, undefined, 1047)]},
];

const plan = (() => {
  let at = 0;
  return OCC.map((o, i) => {
    if (i > 0) at += 0.5;
    const from = Math.round(at * FPS);
    const dur = Math.round((o.end - o.start) * FPS);
    at += o.end - o.start;
    return {o, from, dur};
  });
})();

// Bruitages (SFX-REGLES.md) : grave-apparition à l'arrivée de chaque pilule, sur la première image
// où elle dépasse du bas du cadre (à l'image 0 de l'entrée, elle est encore entièrement sous le cadre).
const CUES: SfxCue[] = plan.flatMap(({o, from}) =>
  o.pills.map((p) => ({frame: from + Math.round((p.in - o.start) * FPS) + 1, name: 'grave-apparition' as const})),
);

const OccView: React.FC<{o: (typeof OCC)[number]}> = ({o}) => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill>
      {o.pills.map((p, i) => (
        <Pill key={i} frame={frame} p={{...p, in: p.in - o.start, out: p.out ? {...p.out, t: p.out.t - o.start} : undefined}} />
      ))}
    </AbsoluteFill>
  );
};

const Pilules: React.FC<{showPlate?: boolean}> = ({showPlate = true}) => (
  <AbsoluteFill style={{backgroundColor: 'transparent', overflow: 'hidden'}}>
    <Plate show={showPlate} />
    {plan.map(({o, from, dur}, i) => (
      <Sequence key={i} from={from} durationInFrames={dur} layout="none">
        <OccView o={o} />
      </Sequence>
    ))}
    <SfxTrack cues={CUES} />
  </AbsoluteFill>
);

export const meta = {
  id: '28-pilules-lower-third',
  durationInFrames: plan[plan.length - 1].from + plan[plan.length - 1].dur,
  fps: FPS,
  defaultProps: {showPlate: true},
  occurrences: plan.map(({o, from, dur}) => ({ref: [o.start, o.end] as [number, number], from, durationInFrames: dur, mode: 'overlay' as const})),
};
export default Pilules;

// Signaux sonores exportés pour la bibliothèque (cloud/cues_globaux.py).
export const cues = CUES;
