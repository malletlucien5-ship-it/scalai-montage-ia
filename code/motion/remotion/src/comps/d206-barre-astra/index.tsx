import React from 'react';
import {AbsoluteFill, Easing, Sequence, interpolate, useCurrentFrame} from '../../shared/rt';
import {INTER_L} from '../../shared/localFonts';
import {Plate} from '../../shared/Plate';
import {SfxCue, SfxTrack} from '../../shared/Sfx';

// Barre de saisie sombre « GPT-6 Astra » (réf. 149.5, 239.5, 281.5, 837.5, 864.5).
// Géométrie mesurée sur des images 1920x1080 de la réf. 239.5-254 :
// barre x 105→1814, centrée en y≈841, 235 px pour 1 ligne, +51 px par ligne (croissance instantanée),
// bord clair 2 px, rayon 58, fond #272727. Texte Inter 34 px blanc, x=155.
// Entrée : fondu + montée de 36 px + flou en ~14 images. Sortie : coupe franche.
const FPS = 30;

type Occ = {
  ref: [number, number];
  at: number; // début dans la timeline de la voix coupée (s)
  end: number; // fin (s, voix coupée)
  text: string;
  // [début de sous-chaîne, instant (s voix coupée)] : la sous-chaîne commence à être tapée à cet instant.
  anchors: [string, number][];
  typeEnd: number; // dernier caractère tapé (s voix coupée)
};

const OCC: Occ[] = [
  {
    ref: [149.5, 153.0],
    at: 145.1,
    end: 147.84,
    text: 'Commande-moi ma commande habituelle sur Uber Eats',
    anchors: [
      ['Commande-moi', 145.4],
      ['ma commande', 146.18],
      ['habituelle', 146.62],
      ['sur Uber', 147.0],
    ],
    typeEnd: 147.62,
  },
  {
    ref: [239.5, 254.0],
    at: 253.2,
    end: 270.4,
    text:
      'Récupère et classe tous les reçus du mois dernier. Ouvre le dossier Reçus sur mon ordinateur, lis chaque reçu, renomme chaque fichier avec la date et le destinataire. Ignore les reçus de voyage, calcule le total et envoie-le à mon directeur financier sur Slack.',
    anchors: [
      ['Récupère', 254.29],
      ['et classe', 254.85],
      ['tous les reçus', 255.29],
      ['du mois', 256.09],
      ['Ouvre', 257.09],
      ['sur mon ordinateur', 258.05],
      ['lis chaque', 259.19],
      ['renomme', 259.83],
      ['avec la date', 261.09],
      ['Ignore', 262.79],
      ['de voyage', 263.55],
      ['calcule', 264.01],
      ['et envoie-le', 265.31],
      ['directeur', 267.11],
      ['sur Slack', 268.39],
    ],
    typeEnd: 268.95,
  },
  {
    ref: [281.5, 294.0],
    at: 299.0,
    end: 314.7,
    text:
      "Fouille mes emails d'abonnements pour voir ce que je paie, connecte-toi à ma place à chaque outil et négocie une réduction via le chatbot du support.",
    anchors: [
      ['Fouille', 299.83],
      ['mes emails', 300.57],
      ["d'abonnements", 303.39],
      ['pour voir', 303.75],
      ['connecte-toi', 306.13],
      ['à ma place', 307.15],
      ['à chaque outil', 307.57],
      ['et négocie', 308.95],
      ['via le chatbot', 309.95],
      ['du support', 310.83],
    ],
    typeEnd: 311.6,
  },
  {
    ref: [837.5, 844.0],
    at: 900.1,
    end: 908.6,
    text: "Utilise Grok Bot, c'est une application sur mon ordinateur. Coordonne-toi avec les bots de Grok Bot pour accomplir cette tâche.",
    anchors: [
      ['Utilise', 900.28],
      ["c'est une", 900.96],
      ['sur mon', 901.36],
      ['ordinateur', 901.9],
      ['Coordonne-toi', 903.82],
      ['avec les bots', 904.42],
      ['de Grok Bot', 905.1],
      ['pour accomplir', 905.5],
    ],
    typeEnd: 906.6,
  },
  {
    ref: [864.5, 876.0],
    at: 930.2,
    end: 943.85,
    text:
      "Crée un rapport financier à partir des reçus récupérés tout à l'heure. Ouvre Grok Bot et donne les reçus à mon agent finance. Demande-lui un rapport visuel et envoie-le à mon comptable sur Slack.",
    anchors: [
      ['Crée', 930.4],
      ['à partir', 931.5],
      ['des reçus', 932.1],
      ['récupérés', 932.84],
      ['Ouvre', 933.86],
      ['et donne', 934.88],
      ['à mon agent', 935.68],
      ['Demande-lui', 938.14],
      ['un rapport visuel', 938.74],
      ['et envoie-le', 939.66],
      ['à mon comptable', 940.4],
      ['sur Slack', 942.64],
    ],
    typeEnd: 943.5,
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

// Nombre de caractères tapés à l'instant t (s, voix coupée) : interpolation linéaire entre ancres.
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

const W = 1709;
const LEFT = 105;
const CY = 841;

const HandIcon: React.FC = () => (
  <svg width={26} height={30} viewBox="0 0 24 28" fill="none" stroke="#B9B9B9" strokeWidth={1.9} strokeLinecap="round" strokeLinejoin="round">
    <path d="M7 14V5.5a1.6 1.6 0 0 1 3.2 0V13" />
    <path d="M10.2 12V3.6a1.6 1.6 0 0 1 3.2 0V12" />
    <path d="M13.4 12V4.8a1.6 1.6 0 0 1 3.2 0V13" />
    <path d="M16.6 13V7.6a1.6 1.6 0 0 1 3.2 0V17c0 5-3.2 9-8.4 9-3.6 0-5.6-1.8-7.4-4.6L1.6 17.6a1.6 1.6 0 0 1 2.6-1.8L7 19" />
  </svg>
);

const Mic: React.FC = () => (
  <svg width={26} height={34} viewBox="0 0 26 34" fill="none" stroke="#FFFFFF" strokeWidth={2.4} strokeLinecap="round">
    <rect x={8} y={1.5} width={10} height={19} rx={5} />
    <path d="M3 15.5c0 5.8 4.5 10 10 10s10-4.2 10-10" />
    <path d="M13 25.5v6.5" />
  </svg>
);

const Wave: React.FC<{color: string; w?: number}> = ({color, w = 24}) => (
  <svg width={w} height={w * 1.1} viewBox="0 0 24 26" stroke={color} strokeWidth={3.2} strokeLinecap="round">
    <path d="M2 10v6" />
    <path d="M7 6v14" />
    <path d="M12 2v22" />
    <path d="M17 6v14" />
    <path d="M22 10v6" />
  </svg>
);

const Bar: React.FC<{o: Occ}> = ({o}) => {
  const frame = useCurrentFrame();
  const t = o.at + frame / FPS;
  const n = typedChars(o, t);
  const typing = t >= firstTypeTime(o) - 1e-6;
  const done = t >= o.typeEnd;
  const cursorOn = typing && (!done || Math.floor((t - o.typeEnd) * FPS / 14) % 2 === 0);

  // Entrée mesurée : visible dès l'image 1, stable vers l'image 14.
  const p = interpolate(frame, [0, 14], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic)});
  const opacity = interpolate(frame, [0, 11], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const dy = (1 - p) * 40;
  const blur = (1 - p) * 8;

  return (
    <div
      style={{
        position: 'absolute',
        left: LEFT,
        top: CY,
        width: W,
        transform: `translateY(calc(-50% + ${dy}px))`,
        opacity,
        filter: blur > 0.05 ? `blur(${blur}px)` : undefined,
        boxSizing: 'border-box',
        background: '#272727',
        border: '2px solid #E6E6E8',
        borderRadius: 58,
        padding: '38px 48px 29px 48px',
        fontFamily: INTER_L,
      }}
    >
      <div style={{minHeight: 51, fontSize: 34, lineHeight: '51px', color: '#FFFFFF', whiteSpace: 'pre-wrap', wordBreak: 'normal', letterSpacing: -0.1}}>
        {o.text.slice(0, n)}
        {cursorOn ? (
          <span style={{display: 'inline-block', width: 0, position: 'relative'}}>
            <span style={{position: 'absolute', left: 1, top: -33, width: 2.5, height: 40, background: '#FFFFFF'}} />
          </span>
        ) : null}
      </div>
      <div style={{height: 66, marginTop: 46, display: 'flex', alignItems: 'center'}}>
        <svg width={24} height={24} viewBox="0 0 24 24" stroke="#FFFFFF" strokeWidth={2.2} strokeLinecap="round" style={{marginLeft: 9}}>
          <path d="M12 1v22M1 12h22" />
        </svg>
        <div
          style={{
            marginLeft: 34,
            height: 66,
            boxSizing: 'border-box',
            borderRadius: 33,
            background: '#2E2E2E',
            border: '1.5px solid #3D3D3D',
            display: 'flex',
            alignItems: 'center',
            padding: '0 28px 0 28px',
            gap: 16,
          }}
        >
          <HandIcon />
          <span style={{fontSize: 29, color: '#B9B9B9'}}>Demander l'approbation</span>
        </div>
        <div style={{flex: 1}} />
        <span style={{fontSize: 29, color: '#FFFFFF', fontWeight: 500}}>GPT-6 Astra</span>
        <span style={{fontSize: 29, color: '#939393', marginLeft: 17}}>Light</span>
        <svg width={18} height={12} viewBox="0 0 18 12" fill="none" stroke="#969696" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" style={{marginLeft: 20}}>
          <path d="M2 3l7 7 7-7" />
        </svg>
        <div style={{marginLeft: 38}}>
          <Mic />
        </div>
        <div
          style={{
            marginLeft: 35,
            marginRight: -1,
            width: 67,
            height: 67,
            borderRadius: '50%',
            background: '#436EEE',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <Wave color="#FFFFFF" />
        </div>
      </div>
    </div>
  );
};

// Sons : apparition de la barre sur l'image 1, frappe du premier au dernier caractère.
const CUES: SfxCue[] = plan.flatMap(({o, from}) => {
  const s = from + Math.round((firstTypeTime(o) - o.at) * FPS);
  const e = from + Math.round((o.typeEnd - o.at) * FPS);
  return [
    {frame: from + 1, name: 'grave-apparition' as const},
    {frame: s, name: 'frappe-clavier' as const, durationInFrames: Math.max(2, e - s)},
  ];
});

const BarreAstra: React.FC<{showPlate?: boolean}> = ({showPlate = true}) => (
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
  id: 'd206-barre-astra',
  fps: FPS,
  durationInFrames: plan[plan.length - 1].from + plan[plan.length - 1].dur,
  defaultProps: {showPlate: true},
  occurrences: plan.map(({o, from, dur}) => ({ref: o.ref, at: o.at, from, durationInFrames: dur, mode: 'plein' as const})),
};
export default BarreAstra;

// Signaux sonores exportés pour la bibliothèque (cloud/cues_globaux.py).
export const cues = CUES;
