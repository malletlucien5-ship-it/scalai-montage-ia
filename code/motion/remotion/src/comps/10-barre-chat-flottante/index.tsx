import React from 'react';
import {AbsoluteFill, Sequence, useCurrentFrame} from '../../shared/rt';
import {Plate} from '../../shared/Plate';
import {SfxTrack, SfxCue} from '../../shared/Sfx';
import {ChatBar} from './ChatBar';
import {TYPING} from './typing';
import {BLINK} from './blink';

const FPS = 30;
const GAP = 15; // 0,5 s de fond neutre entre deux occurrences

type Prompt = {
  key: string; // clé de TYPING
  text: string;
  from: number; // temps ref où ce texte remplace le précédent
};
type Bar = {
  enter: number; // temps ref du début de l'entrée
  exit?: number; // temps ref du début de la sortie
  end?: number; // temps ref où la barre disparaît (coupe)
  scale: number;
  cx?: number;
  bottom: number;
  lines: number;
  extraH?: number;
  textMaxW?: number;
  textDy?: number;
  sepDy?: number;
  prompts: Prompt[];
};
type Occ = {start: number; end: number; bars: Bar[]};

const S1 = {scale: 1, bottom: 1038, lines: 1};
const SM = {scale: 0.856, bottom: 1031, lines: 1};

// Occurrences de la référence, dans l'ordre (temps en secondes de ref.mp4).
export const OCCS: Occ[] = [
  {
    start: 51.418,
    end: 57.524,
    bars: [
      {
        enter: 51.45,
        scale: 0.871,
        cx: 959.5,
        bottom: 1039,
        lines: 3,
        textDy: -9,
        prompts: [
          {
            key: 'a',
            from: 0,
            text: 'Aide-moi à rédiger un e-mail pour signer un gros contrat.\nAvant de répondre, pose-moi toutes les questions utiles pour bien faire ce travail.',
          },
        ],
      },
    ],
  },
  {start: 71.95, end: 74.074, bars: [{enter: 72.02, ...S1, prompts: [{key: 'b', from: 0, text: 'Vérifie ton travail'}]}]},
  {
    start: 122.2,
    end: 127.327,
    bars: [{enter: 122.25, ...S1, prompts: [{key: 'c', from: 0, text: 'Interroge-moi pour créer un prompt maître de marketeur.'}]}],
  },
  {
    start: 202.2,
    end: 208.809,
    bars: [{enter: 202.25, ...S1, prompts: [{key: 'd', from: 0, text: 'Interroge-moi pour un prompt système de marketing de contenu.'}]}],
  },
  {
    start: 358.0,
    end: 370.937,
    bars: [
      {
        enter: 358.12,
        exit: 363.06,
        end: 363.5,
        ...S1,
        prompts: [
          {key: 'e1', from: 0, text: "Regarde mon agenda, dis-moi ce qui m'échappe."},
          {key: 'e2', from: 360.927, text: 'Regarde mes emails. Dis-moi ce que je dois savoir.'},
        ],
      },
      {
        enter: 363.53,
        scale: 0.786,
        bottom: 1038,
        lines: 3,
        extraH: 10,
        textMaxW: 1110,
        sepDy: -9,
        prompts: [
          {
            key: 'e3',
            from: 0,
            text: "Je suis le PDG de mon entreprise. Parcours Slack sur la dernière semaine et donne-moi une vision de PDG de ce qui se passe dans toute l'entreprise.",
          },
        ],
      },
    ],
  },
  {start: 431.865, end: 437.203, bars: [{enter: 431.92, ...SM, prompts: [{key: 'f', from: 0, text: 'Interroge-moi pour créer un prompt système marketing.'}]}]},
  {
    start: 463.6,
    end: 467.9,
    bars: [{enter: 463.66, exit: 467.44, ...SM, prompts: [{key: 'g', from: 0, text: "Transforme ce qu'on vient de faire en skill : /ops:revue-hebdo"}]}],
  },
  {start: 485.418, end: 488.588, bars: [{enter: 485.48, ...SM, prompts: [{key: 'h', from: 0, text: '/statut-entreprise'}]}]},
];

const occFrames = (o: Occ) => Math.round((o.end - o.start) * FPS);

// Fraction tapée à l'instant t (s de ref), interpolée sur les mesures.
const typedFrac = (key: string, t: number, t0: number) => {
  let kf = TYPING[key];
  if (kf[0][1] > 0.02) kf = [[Math.max(t0, kf[0][0] - kf[0][1] * 2.2), 0], ...kf];
  else kf = [[kf[0][0] - 0.03, 0], ...kf];
  if (t <= kf[0][0]) return 0;
  for (let i = 1; i < kf.length; i++) {
    if (t <= kf[i][0]) {
      const [ta, fa] = kf[i - 1];
      const [tb, fb] = kf[i];
      return fa + ((fb - fa) * (t - ta)) / (tb - ta);
    }
  }
  return 1;
};

const BarAt: React.FC<{bar: Bar; t: number}> = ({bar, t}) => {
  if (t < bar.enter) return null;
  if (bar.end !== undefined && t >= bar.end) return null;
  // prompt courant
  let p = bar.prompts[0];
  for (const q of bar.prompts) if (t >= q.from) p = q;
  const t0 = p.from || bar.enter + 0.1;
  const frac = typedFrac(p.key, t, t0);
  const n = Math.round(frac * p.text.length);
  const text = p.text.slice(0, n);
  // curseur plein pendant la frappe, puis clignotement irrégulier relevé sur la référence
  let showCursor = true;
  for (const [tb, v] of BLINK[p.key]) if (t >= tb) showCursor = v === 1;
  return (
    <ChatBar
      scale={bar.scale}
      cx={bar.cx ?? 960}
      bottom={bar.bottom}
      lines={bar.lines}
      extraH={bar.extraH}
      textMaxW={bar.textMaxW}
      textDy={bar.textDy}
      sepDy={bar.sepDy}
      text={text}
      showCursor={showCursor}
      enter={(t - bar.enter) * FPS}
      exit={bar.exit !== undefined ? (t - bar.exit) * FPS : -1}
    />
  );
};

const OccView: React.FC<{occ: Occ}> = ({occ}) => {
  const f = useCurrentFrame();
  const t = occ.start + f / FPS;
  return (
    <AbsoluteFill>
      {occ.bars.map((b, i) => (
        <BarAt key={i} bar={b} t={t} />
      ))}
    </AbsoluteFill>
  );
};

// Début (en frames) de chaque occurrence dans la composition.
export const OCC_STARTS = OCCS.reduce<number[]>((acc, o, i) => {
  acc.push(i === 0 ? 0 : acc[i - 1] + occFrames(OCCS[i - 1]) + GAP);
  return acc;
}, []);

const TOTAL = OCC_STARTS[OCCS.length - 1] + occFrames(OCCS[OCCS.length - 1]);

// Bruitages calculés depuis le minutage mesuré :
// whoosh-transition à l'image où la barre apparaît, frappe-clavier du premier au dernier caractère.
// Aucun envoi n'est visible dans la référence (les barres sortent sans clic), donc aucun clic.
const typedCount = (p: Prompt, bar: Bar, t: number) =>
  Math.round(typedFrac(p.key, t, p.from || bar.enter + 0.1) * p.text.length);

const SFX: SfxCue[] = OCCS.flatMap((occ, i) => {
  const base = OCC_STARTS[i];
  const n = occFrames(occ);
  const cues: SfxCue[] = [];
  for (const bar of occ.bars) {
    cues.push({frame: base + Math.round((bar.enter - occ.start) * FPS) + 1, name: 'whoosh-transition'});
    bar.prompts.forEach((p, k) => {
      const until = k + 1 < bar.prompts.length ? bar.prompts[k + 1].from : bar.end ?? Infinity;
      let first = -1;
      let last = -1;
      for (let f = 0; f < n; f++) {
        const t = occ.start + f / FPS;
        if (t < bar.enter || t < p.from || t >= until) continue;
        const c = typedCount(p, bar, t);
        if (c >= 1 && first < 0) first = f;
        if (c >= p.text.length) {
          last = f;
          break;
        }
      }
      if (first >= 0) {
        const end = last >= 0 ? last : n - 1;
        cues.push({frame: base + first, name: 'frappe-clavier', durationInFrames: Math.max(2, end - first + 2)});
      }
    });
  }
  return cues;
});

export const meta = {
  id: '10-barre-chat-flottante',
  durationInFrames: TOTAL,
  fps: FPS,
  defaultProps: {showPlate: true},
  // une entrée par occurrence, tirée du minutage OCCS / OCC_STARTS
  occurrences: OCCS.map((o, i) => ({
    ref: [o.start, o.end],
    from: OCC_STARTS[i],
    durationInFrames: occFrames(o),
    mode: 'overlay',
  })),
};

const Comp: React.FC<{showPlate?: boolean}> = ({showPlate = true}) => (
  <AbsoluteFill>
    <Plate show={showPlate} />
    <SfxTrack cues={SFX} />
    {OCCS.map((o, i) => (
      <Sequence key={i} from={OCC_STARTS[i]} durationInFrames={occFrames(o)}>
        <OccView occ={o} />
      </Sequence>
    ))}
  </AbsoluteFill>
);

export default Comp;

// Signaux sonores exportés pour la bibliothèque (cloud/cues_globaux.py).
export const cues = SFX;
