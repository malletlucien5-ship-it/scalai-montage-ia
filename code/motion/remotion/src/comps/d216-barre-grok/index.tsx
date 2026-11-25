import React from 'react';
import {AbsoluteFill, Easing, Sequence, interpolate, useCurrentFrame} from '../../shared/rt';
import {INTER_L} from '../../shared/localFonts';
import {Plate} from '../../shared/Plate';
import {SfxCue, SfxTrack} from '../../shared/Sfx';

// Barre de saisie Grok (réf. 502.5, 548.5, 569.5). Géométrie mesurée sur des images 1920x1080 (réf. 503.4, 507, 509.5) :
// pilule x 120→1799, centrée en y≈857, 165 px pour 1 ligne puis 63 px par ligne + 76 (croissance instantanée),
// bord clair 2 px, fond #232323. Bouton « + » rond gauche (centre x 197, r 50, #313131, centré verticalement),
// micro (x 1613) et bouton blanc (x 1723, r 49) calés à 89 px du bas. Texte Inter 41 px blanc, x=290.
// Curseur fixe avant et pendant la frappe, clignotant ensuite. Entrée : fondu + montée + flou (~12 images). Sortie : coupe franche.
const FPS = 30;

type Occ = {
  ref: [number, number];
  at: number;
  end: number;
  text: string;
  anchors: [string, number][];
  typeEnd: number;
};

const OCC: Occ[] = [
  {
    ref: [502.5, 511.0],
    at: 556.6,
    end: 566.0,
    text: 'Interviewe-moi, pose-moi des questions sur ma vie, fouille mes emails et mes messages Slack, puis dis-moi quels bots créer.',
    anchors: [
      ['Interviewe-moi', 557.24],
      ['pose-moi', 557.82],
      ['des questions', 558.16],
      ['sur ma vie', 558.72],
      ['fouille', 559.96],
      ['mes emails', 560.28],
      ['et mes messages', 560.96],
      ['Slack', 561.76],
      ['puis dis-moi', 563.0],
      ['quels bots', 563.3],
      ['créer', 564.14],
    ],
    typeEnd: 564.7,
  },
  {
    ref: [548.5, 559.0],
    at: 605.3,
    end: 614.05,
    text: 'Trie toute ma boîte mail, rédige une réponse pour chaque email qui en attend une et classe les newsletters en spam.',
    anchors: [
      ['Trie', 606.09],
      ['toute ma boîte', 606.61],
      ['rédige', 607.63],
      ['une réponse', 608.11],
      ['pour chaque email', 608.49],
      ['qui en attend', 608.85],
      ['et classe', 610.99],
      ['les newsletters', 612.13],
      ['en spam', 613.05],
    ],
    typeEnd: 613.45,
  },
  {
    ref: [569.5, 575.0],
    at: 626.8,
    end: 631.25,
    text: 'Fais ça tous les matins à 8 h et donne-moi un résumé de ce qui mérite mon attention.',
    anchors: [
      ['Fais ça', 627.06],
      ['tous les matins', 627.56],
      ['à 8 h', 628.34],
      ['et donne-moi', 629.2],
      ['un résumé', 629.46],
      ['de ce qui', 630.02],
      ['mérite', 630.26],
      ['mon attention', 630.58],
    ],
    typeEnd: 631.05,
  },
];

const GAP = 15;
const plan = (() => {
  let from = 0;
  return OCC.map((o) => {
    const dur = Math.round((o.end - o.at) * FPS);
    const p = {o, from, dur};
    from += dur + GAP;
    return p;
  });
})();

const typedChars = (o: Occ, t: number) => {
  const pts: [number, number][] = [];
  for (const [sub, time] of o.anchors) {
    const i = o.text.indexOf(sub);
    if (i >= 0) pts.push([time, i]);
  }
  pts.push([o.typeEnd, o.text.length]);
  pts.sort((a, b) => a[0] - b[0]);
  if (t < pts[0][0]) return 0;
  for (let k = 0; k < pts.length - 1; k++) {
    const [t0, c0] = pts[k];
    const [t1, c1] = pts[k + 1];
    if (t <= t1) return Math.floor(c0 + ((c1 - c0) * (t - t0)) / Math.max(1e-3, t1 - t0));
  }
  return o.text.length;
};
const firstTypeTime = (o: Occ) => Math.min(...o.anchors.map((a) => a[1]));

const LEFT = 120;
const W = 1679;
const CY = 857;

const Bar: React.FC<{o: Occ}> = ({o}) => {
  const frame = useCurrentFrame();
  const t = o.at + frame / FPS;
  const n = typedChars(o, t);
  const done = t >= o.typeEnd;
  const cursorOn = !done || Math.floor(((t - o.typeEnd) * FPS) / 14) % 2 === 0;

  const p = interpolate(frame, [0, 12], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic)});
  const opacity = interpolate(frame, [0, 9], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const dy = (1 - p) * 40;
  const blur = (1 - p) * 8;

  return (
    <div
      style={{
        position: 'absolute',
        left: LEFT,
        top: CY,
        width: W,
        minHeight: 165,
        transform: `translateY(calc(-50% + ${dy}px))`,
        opacity,
        filter: blur > 0.05 ? `blur(${blur}px)` : undefined,
        boxSizing: 'border-box',
        background: '#232323',
        border: '2px solid #D2D2D2',
        borderRadius: 82,
        padding: '36px 0',
        display: 'flex',
        alignItems: 'center',
        fontFamily: INTER_L,
      }}
    >
      {/* Bouton « + » centré verticalement */}
      <div
        style={{
          position: 'absolute',
          left: 197 - LEFT - 2 - 50,
          top: '50%',
          width: 100,
          height: 100,
          marginTop: -50,
          borderRadius: '50%',
          background: '#313131',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <svg width={26} height={26} viewBox="0 0 26 26" stroke="#CBCBCB" strokeWidth={2.4} strokeLinecap="round">
          <path d="M13 1v24M1 13h24" />
        </svg>
      </div>
      <div style={{marginLeft: 290 - LEFT - 2, width: 1280, fontSize: 41, lineHeight: '63px', color: '#FFFFFF', whiteSpace: 'pre-wrap', minHeight: 63, letterSpacing: -0.2, fontWeight: 500}}>
        {o.text.slice(0, n)}
        {cursorOn ? (
          <span style={{display: 'inline-block', width: 0, position: 'relative'}}>
            <span style={{position: 'absolute', left: 2, top: -38, width: 3, height: 47, background: '#FFFFFF'}} />
          </span>
        ) : null}
      </div>
      {/* Micro + bouton vocal, calés à 89 px du bas */}
      <svg
        width={28}
        height={38}
        viewBox="0 0 28 38"
        fill="none"
        stroke="#B5B5B5"
        strokeWidth={2.4}
        strokeLinecap="round"
        style={{position: 'absolute', left: 1613.5 - LEFT - 2 - 14, bottom: 89 - 2 - 19}}
      >
        <rect x={8.5} y={1.5} width={11} height={21} rx={5.5} />
        <path d="M3 17.5c0 6.4 4.9 11 11 11s11-4.6 11-11" />
        <path d="M14 28.5v7.5" />
      </svg>
      <div
        style={{
          position: 'absolute',
          left: 1723 - LEFT - 2 - 49,
          bottom: 89 - 2 - 49,
          width: 98,
          height: 98,
          borderRadius: '50%',
          background: '#FFFFFF',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <svg width={28} height={32} viewBox="0 0 28 32" stroke="#111111" strokeWidth={3.4} strokeLinecap="round">
          <path d="M2.5 13v6" />
          <path d="M8.5 8v16" />
          <path d="M14 3v26" />
          <path d="M19.5 8v16" />
          <path d="M25.5 13v6" />
        </svg>
      </div>
    </div>
  );
};

const CUES: SfxCue[] = plan.flatMap(({o, from}) => {
  const s = from + Math.round((firstTypeTime(o) - o.at) * FPS);
  const e = from + Math.round((o.typeEnd - o.at) * FPS);
  return [
    {frame: from + 1, name: 'grave-apparition' as const},
    {frame: s, name: 'frappe-clavier' as const, durationInFrames: Math.max(2, e - s)},
  ];
});

const BarreGrok: React.FC<{showPlate?: boolean}> = ({showPlate = true}) => (
  <AbsoluteFill style={{overflow: 'hidden'}}>
    <Plate show={showPlate} />
    {plan.map(({o, from, dur}, i) => (
      <Sequence key={i} from={from} durationInFrames={dur} layout="none">
        <Bar o={o} />
      </Sequence>
    ))}
    <SfxTrack cues={CUES} />
  </AbsoluteFill>
);

export const meta = {
  id: 'd216-barre-grok',
  fps: FPS,
  durationInFrames: plan[plan.length - 1].from + plan[plan.length - 1].dur,
  defaultProps: {showPlate: true},
  occurrences: plan.map(({o, from, dur}) => ({ref: o.ref, at: o.at, from, durationInFrames: dur, mode: 'plein' as const})),
};
export default BarreGrok;

// Signaux sonores exportés pour la bibliothèque (cloud/cues_globaux.py).
export const cues = CUES;
