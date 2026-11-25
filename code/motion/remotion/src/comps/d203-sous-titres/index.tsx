import React, {useLayoutEffect, useState} from 'react';
import {AbsoluteFill, Easing, Sequence, continueRender, delayRender, interpolate, useCurrentFrame} from '../../shared/rt';
import {INTER_L} from '../../shared/localFonts';
import {Plate} from '../../shared/Plate';
import {SfxTrack, SfxCue} from '../../shared/Sfx';

// d203 : sous-titres cinétiques (réf. 12,7-16,05 ; 305,5-310 ; 375,5-384 ; 754,5-760 ; 931,5-936 ; 1016,5-1022 ; 1077,5-1084).
// Mesures sur l'original en 1920x1080 :
// - blanc gras, centré ; taille 80 px max (capitale ~58 px), réduite pour que la ligne tienne en ~1790 px ;
// - 1 ligne : ligne de base 860 (846..870 selon l'occurrence) ; 2 lignes : lignes de base 812 et 914 ;
// - chaque mot part 120 px sous sa place, remonte en x0,865 par image, opacité 0,35 -> 1 et flou 5 -> 0 en ~17 images ;
// - dégradé noir en bas (alpha 0,04 à y 600 -> 0,60 à y 1080), fondu d'entrée ~20 images ;
// - soulignement cyan (#00B8EE -> #00C8EA), 15 px, bouts ronds, 13 px sous la ligne de base, tracé gauche -> droite en 14 images ;
// - sortie : coupe franche.
const FPS = 30;
const MAX_SIZE = 80;
const MAX_W = 1780;
const BASE_1 = 860;
const BASE_2 = [812, 914];

type Wd = [number, string]; // [temps du mot dans la voix coupée (s), texte]
type Occ = {ref: [number, number]; start: number; end: number; lines: Wd[][]; ul?: {line: number; from: number; to: number; t: number}};

const OCCS: Occ[] = [
  {
    ref: [12.7, 16.05],
    start: 11.75,
    end: 14.85,
    lines: [[[12.01, 'Il'], [12.07, 'faut'], [12.15, 'savoir'], [12.37, 'quel'], [12.73, 'modèle'], [12.97, 'marche'], [13.31, 'à'], [13.61, 'l’instant'], [13.95, 'T']]],
    ul: {line: 0, from: 6, to: 8, t: 14.1},
  },
  {
    ref: [305.5, 310],
    start: 330.8,
    end: 337.3,
    lines: [
      [[331.08, 'Si'], [331.14, 'vous'], [331.26, 'êtes'], [331.4, 'encore'], [332.6, 'en'], [333.04, 'train'], [333.2, 'd’effectuer'], [333.6, 'une'], [333.74, 'tâche']],
      [[333.96, 'que'], [334.18, 'l’IA'], [334.42, 'peut'], [334.58, 'faire,'], [335.38, 'alors'], [335.48, 'c’est'], [335.92, 'vous'], [336.14, 'qui'], [336.52, 'êtes'], [336.66, 'la'], [336.78, 'contrainte']],
    ],
  },
  {
    ref: [375.5, 384],
    start: 410.1,
    end: 418.1,
    lines: [
      [[410.4, 'La'], [410.5, 'plateforme'], [410.8, 'd’agent'], [411.14, 'la'], [411.34, 'plus'], [411.52, 'simple']],
      [[412.03, 'qui'], [412.13, 'a'], [412.25, 'jamais'], [412.59, 'été'], [412.77, 'créée']],
    ],
  },
  {
    ref: [754.5, 760],
    start: 812.05,
    end: 816.3,
    lines: [
      [[812.36, 'ChatGPT'], [812.74, 'devient'], [812.94, 'votre'], [813.34, 'point'], [813.74, 'de'], [813.82, 'contact'], [814.0, 'principal']],
      [[814.34, 'et'], [814.7, 'va'], [814.84, 'piloter'], [815.32, 'les'], [815.4, 'bots'], [815.5, 'à'], [815.64, 'votre'], [815.74, 'place']],
    ],
  },
  {
    ref: [931.5, 936],
    start: 1002.2,
    end: 1006.5,
    lines: [
      [[1002.5, 'Vous'], [1002.62, 'devenez'], [1002.9, 'le'], [1002.94, 'directeur,']],
      [[1003.52, 'vous'], [1003.64, 'n’êtes'], [1003.84, 'pas'], [1004.02, 'l’exécutant']],
    ],
  },
  {
    ref: [1016.5, 1022],
    start: 1087.6,
    end: 1096.8,
    lines: [
      [[1087.91, 'Un'], [1087.97, 'système'], [1088.19, 'de'], [1088.39, 'mémoire'], [1088.81, 'complet']],
      [[1094.09, 'pour'], [1094.19, 'être'], [1094.37, 'immédiatement'], [1095.11, 'opérationnel'], [1095.59, 'avec'], [1095.77, 'le'], [1095.91, 'nouveau'], [1096.19, 'modèle'], [1096.45, 'IA']],
    ],
  },
  {
    ref: [1077.5, 1084],
    start: 1196.2,
    end: 1200.2,
    lines: [[[1196.52, 'Second'], [1196.68, 'cerveau']]],
  },
];

const GAP = 15;
const plan = (() => {
  let from = 0;
  return OCCS.map((o) => {
    const dur = Math.round((o.end - o.start) * FPS);
    const p = {o, from, dur};
    from += dur + GAP;
    return p;
  });
})();
const TOTAL = plan[plan.length - 1].from + plan[plan.length - 1].dur;

// Son (SFX-REGLES.md règle 6) : grave-apparition seulement sur l'élément mis en couleur (le soulignement cyan).
const CUES: SfxCue[] = plan.flatMap(({o, from}) => (o.ul ? [{frame: from + Math.round((o.ul.t - o.start) * FPS) + 1, name: 'grave-apparition' as const}] : []));

// Largeur naturelle d'une ligne à 80 px, mesurée dans le navigateur une fois les polices chargées.
const lineText = (l: Wd[]) => l.map((w) => w[1]).join(' ');
const measure = (text: string) => {
  const c = document.createElement('canvas').getContext('2d')!;
  c.font = `800 ${MAX_SIZE}px ${INTER_L}`;
  return c.measureText(text).width;
};
// Attend que la graisse 800 d'Inter locale soit chargée (ensureLocalFonts l'ajoute de façon asynchrone).
const waitFont = () =>
  new Promise<void>((resolve) => {
    const t0 = Date.now();
    const tick = () => {
      const ok = Array.from(document.fonts as unknown as Iterable<FontFace>).some(
        (f) => f.family.replace(/"/g, '') === INTER_L && String(f.weight) === '800' && f.status === 'loaded',
      );
      if (ok || Date.now() - t0 > 8000) document.fonts.ready.then(() => resolve());
      else setTimeout(tick, 30);
    };
    tick();
  });
const useSizes = (lines: Wd[][]) => {
  const [sizes, setSizes] = useState<number[] | null>(null);
  const [handle] = useState(() => delayRender('mesure des lignes'));
  useLayoutEffect(() => {
    waitFont().then(() => {
      setSizes(lines.map((l) => Math.min(MAX_SIZE, (MAX_SIZE * MAX_W) / measure(lineText(l)))));
      continueRender(handle);
    });
  }, [handle, lines]);
  return sizes;
};

// Courbes mesurées sur « need » (réf. 13,08 s) : écart 120 px x0,865^f ; opacité et flou relevés image par image.
const wordState = (f: number) => {
  const dy = 120 * Math.pow(0.865, f);
  const op = interpolate(f, [0, 1, 2, 3, 5, 7, 9, 11, 13, 17], [0.35, 0.55, 0.64, 0.7, 0.77, 0.83, 0.87, 0.91, 0.94, 1], {extrapolateRight: 'clamp'});
  const blur = interpolate(f, [0, 1, 2, 3, 5, 7, 9, 11, 13, 17], [5, 3.5, 2.8, 2.2, 1.6, 1.1, 0.7, 0.4, 0.2, 0], {extrapolateRight: 'clamp'});
  return {dy, op, blur};
};

const Line: React.FC<{words: Wd[]; t0: number; size: number; base: number; ul?: Occ['ul']}> = ({words, t0, size, base, ul}) => {
  const frame = useCurrentFrame();
  const refs: (HTMLSpanElement | null)[] = [];
  const [ulBox, setUlBox] = useState<{x: number; w: number} | null>(null);
  useLayoutEffect(() => {
    if (!ul) return;
    const a = refs[ul.from];
    const b = refs[ul.to];
    if (a && b) setUlBox({x: a.offsetLeft, w: b.offsetLeft + b.offsetWidth - a.offsetLeft});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [size]);
  const ulP = ul ? interpolate(frame - Math.round((ul.t - t0) * FPS), [0, 14], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic)}) : 0;
  return (
    <div style={{position: 'absolute', left: 0, right: 0, top: base - size * 0.97, display: 'flex', justifyContent: 'center'}}>
      <div style={{position: 'relative', display: 'flex', gap: size * 0.26, whiteSpace: 'pre'}}>
        {ul && ulBox && ulP > 0 ? (
          <div
            style={{
              position: 'absolute',
              left: ulBox.x,
              top: size * 0.97 + 13,
              height: 15,
              width: Math.max(15, ulBox.w * ulP),
              borderRadius: 8,
              background: 'linear-gradient(180deg, #00BAEF 0%, #00C4EC 55%, #00C8EE 100%)',
              boxShadow: '0 3px 8px rgba(0,0,0,0.35)',
            }}
          />
        ) : null}
        {words.map((w, i) => {
          const f = frame - Math.round((w[0] - t0) * FPS);
          const s = f < 0 ? null : wordState(f);
          return (
            <span
              key={i}
              ref={(el) => {
                refs[i] = el;
              }}
              style={{
                display: 'inline-block',
                fontFamily: INTER_L,
                fontWeight: 800,
                fontSize: size,
                lineHeight: `${size * 1.2}px`,
                color: '#FFFFFF',
                
                opacity: s ? s.op : 0,
                transform: `translateY(${s ? s.dy : 0}px)`,
                filter: s && s.blur > 0.15 ? `blur(${s.blur}px)` : undefined,
                textShadow: '0 3px 10px rgba(0,0,0,0.45)',
              }}
            >
              {w[1]}
            </span>
          );
        })}
      </div>
    </div>
  );
};

const GRADIENT =
  'linear-gradient(180deg, rgba(0,0,0,0) 50%, rgba(0,0,0,0.04) 55.5%, rgba(0,0,0,0.09) 60%, rgba(0,0,0,0.15) 65%, rgba(0,0,0,0.23) 69.5%, rgba(0,0,0,0.31) 74%, rgba(0,0,0,0.38) 78.7%, rgba(0,0,0,0.42) 83.3%, rgba(0,0,0,0.5) 88%, rgba(0,0,0,0.54) 92.6%, rgba(0,0,0,0.58) 97.2%, rgba(0,0,0,0.6) 100%)';

const OccView: React.FC<{o: Occ}> = ({o}) => {
  const frame = useCurrentFrame();
  const sizes = useSizes(o.lines);
  const g = interpolate(frame, [0, 20], [0, 1], {extrapolateRight: 'clamp', easing: Easing.out(Easing.quad)});
  const two = o.lines.length > 1;
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{background: GRADIENT, opacity: g}} />
      {sizes
        ? o.lines.map((l, i) => (
            <Line key={i} words={l} t0={o.start} size={sizes[i]} base={two ? BASE_2[i] : BASE_1} ul={o.ul && o.ul.line === i ? o.ul : undefined} />
          ))
        : null}
    </AbsoluteFill>
  );
};

const SousTitres: React.FC<{showPlate?: boolean}> = ({showPlate = true}) => (
  <AbsoluteFill style={{overflow: 'hidden'}}>
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
  id: 'd203-sous-titres',
  fps: FPS,
  durationInFrames: TOTAL,
  defaultProps: {showPlate: true},
  occurrences: plan.map(({o, from, dur}) => ({ref: o.ref, at: o.start, from, durationInFrames: dur, mode: 'plein' as const})),
};
export default SousTitres;

// Signaux sonores exportés pour la bibliothèque (cloud/cues_globaux.py).
export const cues = CUES;
