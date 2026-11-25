import React from 'react';
import {AbsoluteFill, Easing, Sequence, interpolate, useCurrentFrame} from '../../shared/rt';
import {INTER_L} from '../../shared/localFonts';
import {Plate} from '../../shared/Plate';
import {SfxCue, SfxTrack} from '../../shared/Sfx';

// d215 : 4 tuiles bleu marine numérotées en bas à droite, remplies une à une de texte.
// Réf. 482,50-489,44 / 510,67-523,45 / 542,33-545,44 (coupes franches en sortie). Chez Dan, posées sur le speaker.
const FPS = 30;
const GAP = 15;
const s2f = (s: number) => Math.round(s * FPS);
const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const OUT = Easing.out(Easing.cubic);

// Géométrie mesurée sur 1920x1080 : tuile 193x211, pas 212,3, gauche 1043, haut 823, rayon 14.
const X0 = 1043;
const PITCH = 212.3;
const W = 193;
const H = 211;
const TOP = 823;

const TEXTS: {lines: string[]; size: number; lh: number}[] = [
  {lines: ['Créer le bot', 'et son rôle'], size: 32, lh: 40},
  {lines: ['Tâches', 'propres', 'au rôle'], size: 34, lh: 40},
  {lines: ['Groupe', 'de bots'], size: 34, lh: 40},
  {lines: ['Travailler', 'par', 'objectif'], size: 33, lh: 38},
];

// intro : 'slide' (montée échelonnée depuis le bas) ou 'blur' (groupe entier, flou → net).
// filled : tuiles déjà remplies à l'entrée. fills : [tuile, sortie du chiffre (s), entrée du texte (s)] en temps local.
type Occ = {ref: [number, number]; at: number; end: number; intro: 'slide' | 'blur'; filled: number; fills: [number, number, number][]};
const OCCS: Occ[] = [
  // « Voilà comment fonctionne Grogbots, vous pouvez créer un nouveau bot et lui attribuer un nom ainsi qu'un rôle. Donc beaucoup de gens commencent par créer un bot »
  {ref: [482.5, 489.44], at: 527.75, end: 535.6, intro: 'slide', filled: 0, fills: [[0, 530.05 - 527.75, 530.15 - 527.75]]},
  // « Ensuite, vous aurez juste à créer le bot … lui confier toutes les tâches liées à ce rôle. Et vous pouvez même créer une conversation de groupe … par catégories, »
  {
    ref: [510.67, 523.45], at: 566.7, end: 580.85, intro: 'blur', filled: 1,
    fills: [[1, 570.6 - 566.7, 571.0 - 566.7], [2, 573.45 - 566.7, 573.9 - 566.7]],
  },
  // « Ensuite, vous pouvez simplement utiliser cette conversation pour accomplir toutes les tâches liées à cet objectif-là. »
  {ref: [542.33, 545.44], at: 599.05, end: 603.45, intro: 'blur', filled: 3, fills: [[3, 599.85 - 599.05, 600.4 - 599.05]]},
];

const plan = (() => {
  let from = 0;
  return OCCS.map((o) => {
    const dur = s2f(o.end - o.at);
    const p = {o, from, dur};
    from += dur + GAP;
    return p;
  });
})();

const Tile: React.FC<{i: number; num: number; txt: number}> = ({i, num, txt}) => {
  const t = TEXTS[i];
  return (
    <div
      style={{
        position: 'absolute', left: X0 + PITCH * i, top: TOP, width: W, height: H, borderRadius: 14, boxSizing: 'border-box', overflow: 'hidden',
        border: '2px solid #2172bb',
        boxShadow: 'inset 0 1.5px 0 rgba(130,175,215,0.55), 0 10px 26px rgba(0,0,0,0.45)',
        background: [
          'radial-gradient(ellipse 110px 70px at 78% 100%, rgba(25,95,175,0.55), rgba(25,95,175,0) 100%)',
          'linear-gradient(90deg, rgba(45,75,125,0.7) 0%, rgba(45,75,125,0) 16%, rgba(0,0,0,0) 44%, rgba(70,100,150,0.13) 50%, rgba(0,0,0,0) 57%)',
          'linear-gradient(180deg, #06295a 0%, #042552 30%, #031f49 58%, #042853 100%)',
        ].join(', '),
      }}
    >
      {num > 0 && (
        <div style={{position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: INTER_L, fontWeight: 700, fontSize: 84, color: '#fff', opacity: num}}>
          {i + 1}
        </div>
      )}
      {txt > 0 && (
        <div
          style={{
            position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
            fontFamily: INTER_L, fontWeight: 700, fontSize: t.size, lineHeight: `${t.lh}px`, color: '#fff', textAlign: 'center', letterSpacing: -0.3,
            opacity: interpolate(txt, [0, 1], [0.3, 1]), filter: `blur(${interpolate(txt, [0, 1], [7, 0])}px)`,
          }}
        >
          {t.lines.map((l, k) => (
            <div key={k} style={{whiteSpace: 'nowrap'}}>{l}</div>
          ))}
        </div>
      )}
    </div>
  );
};

const OccView: React.FC<{o: Occ}> = ({o}) => {
  const f = useCurrentFrame();
  const blurIn = o.intro === 'blur' ? interpolate(f, [0, 8], [0, 1], {...clamp, easing: OUT}) : 1;
  return (
    <AbsoluteFill
      style={
        o.intro === 'blur'
          ? {opacity: interpolate(blurIn, [0, 1], [0.35, 1]), filter: `blur(${interpolate(blurIn, [0, 1], [9, 0])}px)`, transform: `translateY(${interpolate(blurIn, [0, 1], [-14, 0])}px)`}
          : undefined
      }
    >
      {[0, 1, 2, 3].map((i) => {
        const s = -3 + 3 * i;
        const y = o.intro === 'slide' ? interpolate(f, [s, s + 9], [300, 0], {...clamp, easing: OUT}) : 0;
        let num = i < o.filled ? 0 : 1;
        let txt = i < o.filled ? 1 : 0;
        const fill = o.fills.find((x) => x[0] === i);
        if (fill) {
          const fo = s2f(fill[1]);
          const fi = s2f(fill[2]);
          num = interpolate(f, [fo, fo + 3], [1, 0], clamp);
          txt = f < fi ? 0 : interpolate(f, [fi, fi + 11], [0.02, 1], {...clamp, easing: OUT});
        }
        return (
          <div key={i} style={{position: 'absolute', inset: 0, transform: y ? `translateY(${y}px)` : undefined}}>
            <Tile i={i} num={num} txt={txt} />
          </div>
        );
      })}
    </AbsoluteFill>
  );
};

// Sons (SFX-REGLES.md) : grave-apparition à l'arrivée du groupe de tuiles (écarts < 0,12 s) et à chaque texte qui remplit une tuile.
const CUES: SfxCue[] = plan.flatMap(({o, from}) => [
  {frame: from, name: 'grave-apparition' as const},
  ...o.fills.map((x) => ({frame: from + s2f(x[2]), name: 'grave-apparition' as const})),
]);

const EtapesTuiles: React.FC<{showPlate?: boolean}> = ({showPlate = true}) => (
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
  id: 'd215-etapes-tuiles',
  fps: FPS,
  durationInFrames: plan[plan.length - 1].from + plan[plan.length - 1].dur,
  defaultProps: {showPlate: true},
  occurrences: plan.map(({o, from, dur}) => ({ref: o.ref, at: o.at, from, durationInFrames: dur, mode: 'plein' as const})),
};
export default EtapesTuiles;

// Signaux sonores exportés pour la bibliothèque (cloud/cues_globaux.py).
export const cues = CUES;
