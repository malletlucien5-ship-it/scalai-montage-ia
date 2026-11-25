import React from 'react';
import {AbsoluteFill, Easing, Sequence, interpolate, useCurrentFrame} from '../../shared/rt';
import {loadFont as inter} from '@remotion/google-fonts/Inter';
import {Plate} from '../../shared/Plate';
import {SfxTrack, SfxCue} from '../../shared/Sfx';

const SANS = inter('normal', {weights: ['700']}).fontFamily;
const FPS = 30;
const RED = '#D41E22';

// Entrée identique aux sous-titres cinétiques (mesurée) : montée de 70 px, décroissance x0,87 par image.
const rise = (f: number) => ({
  transform: `translateY(${70 * Math.pow(0.87, f)}px)`,
  opacity: 1 - 0.4 * Math.pow(0.75, f),
  filter: `blur(${2.5 * Math.pow(0.6, f)}px)`,
});

type Item = {
  t: number; // apparition (s, relatif au début de l'occurrence)
  text: string;
  size: number;
  baseline: number;
  left?: number; // alignement gauche
  right?: number; // alignement droit (bord droit du texte)
  strike?: {t: number; thick: number; pre: number; post: number; dur: number};
};

// Barré : trait rouge à bouts ronds tiré de gauche à droite (relevé : 17 à 20 images, départ lent, longue traîne).
const Strike: React.FC<{f: number; s: NonNullable<Item['strike']>; size: number}> = ({f, s, size}) => {
  const p = interpolate(f, [0, s.dur], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.bezier(0.55, 0, 0.2, 1)});
  if (f < 0) return null;
  return (
    <div
      style={{
        position: 'absolute',
        left: -s.pre,
        top: size * 0.585 - s.thick / 2,
        height: s.thick,
        width: `calc(${s.thick}px + (100% + ${s.pre + s.post - s.thick}px) * ${p})`,
        borderRadius: s.thick,
        background: RED,
        boxShadow: '0 1px 4px rgba(0,0,0,0.35)',
      }}
    />
  );
};

const Word: React.FC<{it: Item}> = ({it}) => {
  const frame = useCurrentFrame();
  const f = frame - Math.round(it.t * FPS);
  if (f < 0) return null;
  const top = it.baseline - it.size * 0.969;
  return (
    <div
      style={{
        position: 'absolute',
        top,
        left: it.left,
        right: it.right !== undefined ? 1920 - it.right : undefined,
        ...rise(f),
      }}
    >
      <div
        style={{
          position: 'relative',
          fontFamily: SANS,
          fontWeight: 700,
          fontSize: it.size,
          lineHeight: 1.21,
          color: '#FFFFFF',
          whiteSpace: 'pre',
          letterSpacing: '0',
          textShadow: '0 3px 10px rgba(0,0,0,0.55), 0 1px 3px rgba(0,0,0,0.35)',
        }}
      >
        {it.text}
        {it.strike ? <Strike f={frame - Math.round(it.strike.t * FPS)} s={it.strike} size={it.size * 1.21} /> : null}
      </div>
    </div>
  );
};

// Occurrence A : réf. 406,5 à 410,5 s. Occurrence B : réf. 751,5 à 755,1 s.
const OCC: {start: number; end: number; items: Item[]}[] = [
  {
    start: 406.5,
    end: 410.5,
    items: [
      {t: 406.934, text: 'Agir', size: 111, baseline: 926, right: 1690, strike: {t: 407.4, thick: 14, pre: 18, post: 11, dur: 20}},
      {t: 409.567, text: 'Diriger', size: 110, baseline: 928, left: 178},
    ],
  },
  {
    start: 751.5,
    end: 755.1,
    items: [
      {t: 751.734, text: 'Humain sur la boucle', size: 80, baseline: 962, left: 82},
      {t: 753.267, text: 'Humain dans la boucle', size: 80, baseline: 962, right: 1826, strike: {t: 753.8, thick: 17, pre: 12, post: 11, dur: 17}},
    ],
  },
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

// grave-apparition contient environ 74 ms de silence initial. Le départ deux
// images plus tôt cale son attaque sur l'image où le mot ou le trait apparaît.
const ATTACK_LEAD = 2;
const CUES: SfxCue[] = plan.flatMap(({o, from}) =>
  o.items.flatMap((it) => [
    {frame: Math.max(0, from + Math.round((it.t - o.start) * FPS) - ATTACK_LEAD), name: 'grave-apparition' as const},
    ...(it.strike ? [{frame: Math.max(0, from + Math.round((it.strike.t - o.start) * FPS) - ATTACK_LEAD), name: 'grave-apparition' as const}] : []),
  ]),
);

const MotsBarres: React.FC<{showPlate?: boolean}> = ({showPlate = true}) => (
  <AbsoluteFill style={{backgroundColor: 'transparent'}}>
    <Plate show={showPlate} />
    {plan.map(({o, from, dur}, i) => (
      <Sequence key={i} from={from} durationInFrames={dur} layout="none">
        <AbsoluteFill>
          {o.items.map((it, j) => (
            <Word key={j} it={{...it, t: it.t - o.start, strike: it.strike ? {...it.strike, t: it.strike.t - o.start} : undefined}} />
          ))}
        </AbsoluteFill>
      </Sequence>
    ))}
    <SfxTrack cues={CUES} />
  </AbsoluteFill>
);

export const meta = {
  id: '02-mots-barres',
  durationInFrames: plan[plan.length - 1].from + plan[plan.length - 1].dur,
  fps: FPS,
  defaultProps: {showPlate: true},
  occurrences: plan.map(({o, from, dur}) => ({ref: [o.start, o.end] as [number, number], from, durationInFrames: dur, mode: 'overlay' as const})),
};
export default MotsBarres;

// Signaux sonores exportés pour la bibliothèque (cloud/cues_globaux.py).
export const cues = CUES;
