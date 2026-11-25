import React from 'react';
import {AbsoluteFill, Easing, Sequence, interpolate, useCurrentFrame} from '../../shared/rt';
import {INTER_L} from '../../shared/localFonts';
import {SfxCue, SfxTrack} from '../../shared/Sfx';

// d211 : « Every great AI promt follows this process », 4 cartes verre M A P S (réf. 204,60-218,15 et 220,95-223,25).
// Géométrie relevée sur des images 1920x1080 de l'original. La vignette du speaker (bas droite) n'est pas reproduite.
const FPS = 30;
const GAP = 15;
const s2f = (s: number) => Math.round(s * FPS);
const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const OUT = Easing.out(Easing.cubic);

const TITLE = [['Tout', 'bon', 'prompt'], ['IA', 'suit', 'ce', 'processus']];
// Titre personnalisable par placement (prop `titre`, mots par ligne). Défaut : titre dan2.
const TitreCtx = React.createContext<string[][]>(TITLE);
// Libellés : les 4 termes anglais de Dan, cohérents avec l'acronyme M A P S (Lucien dit « Ask » et « Shape » à l'oral).
const CARDS = [
  {l: 'M', label: 'Mission', icon: 'flag'},
  {l: 'A', label: 'Ask', icon: 'chat'},
  {l: 'P', label: 'Parameters', icon: 'sliders'},
  {l: 'S', label: 'Shape', icon: 'doc'},
] as const;

// Carte : gauche 50 + 465 i, largeur 427, haut 275, bas 962, rayon 44. Pastille d'icône 86 px centrée sur le bord haut.
const CX = (i: number) => 263 + 465 * i;
const CARD_W = 427;
const CARD_TOP = 275;
const CARD_H = 687;

// Occurrences (temps en s depuis le début de l'occurrence). lit : allumage du contour, lab : arrivée du libellé.
type Step = {lit: number; lab: number};
type Occ = {ref: [number, number]; at: number; end: number; intro: boolean; steps: (Step | 'on' | null)[]};
const OCCS: Occ[] = [
  {
    // « il faut suivre le framework Maps » 214,68 → fin de « … ce sont les paramètres. » 227,28
    ref: [204.6, 218.15],
    at: 214.68,
    end: 227.28,
    intro: true,
    steps: [
      {lit: 218.45 - 214.68, lab: 219.40 - 214.68}, // « La première partie, c'est la mission »
      {lit: 222.05 - 214.68, lab: 222.72 - 214.68}, // « La deuxième, c'est Ask »
      {lit: 225.40 - 214.68, lab: 226.20 - 214.68}, // « La troisième, c'est P, ce sont les paramètres »
      null,
    ],
  },
  {
    // « Et enfin, le S, c'est Shape. » 230,70 → « … une fois le travail terminé. » 242,80
    ref: [220.95, 223.25],
    at: 230.70,
    end: 242.80,
    intro: false,
    steps: ['on', 'on', 'on', {lit: 230.80 - 230.70, lab: 231.62 - 230.70}],
  },
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

const Icon: React.FC<{k: string}> = ({k}) => {
  const st = {fill: 'none', stroke: '#fff', strokeWidth: 2.2, strokeLinecap: 'round', strokeLinejoin: 'round'} as const;
  return (
    <svg width={46} height={46} viewBox="0 0 40 40">
      {k === 'flag' && (
        <g {...st}>
          <path d="M5 30 L13 19 L18 25 L24 14 L30 30" />
          <path d="M24 14 L24 5 L32 8 L24 11" />
        </g>
      )}
      {k === 'chat' && (
        <g {...st}>
          <path d="M7 9 h26 a2 2 0 0 1 2 2 v13 a2 2 0 0 1 -2 2 h-17 l-6 6 v-6 h-3 a2 2 0 0 1 -2 -2 v-13 a2 2 0 0 1 2 -2 z" />
          <circle cx="14" cy="17.5" r="0.9" fill="#fff" />
          <circle cx="20" cy="17.5" r="0.9" fill="#fff" />
          <circle cx="26" cy="17.5" r="0.9" fill="#fff" />
        </g>
      )}
      {k === 'sliders' && (
        <g {...st}>
          <path d="M7 11 h26 M7 20 h26 M7 29 h26" />
          <circle cx="16" cy="11" r="3" fill="#0a1a28" />
          <circle cx="25" cy="20" r="3" fill="#0a1a28" />
          <circle cx="18" cy="29" r="3" fill="#0a1a28" />
        </g>
      )}
      {k === 'doc' && (
        <g {...st}>
          <path d="M11 5 h13 l7 7 v22 a1.5 1.5 0 0 1 -1.5 1.5 h-18.5 a1.5 1.5 0 0 1 -1.5 -1.5 v-27.5 a1.5 1.5 0 0 1 1.5 -1.5 z" />
          <path d="M24 5 v7 h7" />
          <path d="M15 19 h11 M15 23.5 h11 M15 28 h7" />
        </g>
      )}
    </svg>
  );
};

// Fond : noir, halo bleu en haut au centre et nappe bleue en bas, quelques particules.
const Bg: React.FC = () => {
  const f = useCurrentFrame();
  const dots = [
    [1035, 548], [1020, 580], [1066, 632], [1093, 764], [1336, 826], [648, 856], [349, 900], [502, 668], [1827, 700], [1245, 975], [686, 946], [1145, 1048],
  ];
  return (
    <AbsoluteFill style={{background: '#000'}}>
      <AbsoluteFill style={{background: 'radial-gradient(ellipse 520px 260px at 1010px 0px, rgba(4,40,62,0.6), rgba(0,0,0,0) 100%)'}} />
      <AbsoluteFill style={{background: 'radial-gradient(ellipse 820px 330px at 720px 1110px, rgba(6,48,82,0.8), rgba(0,0,0,0) 100%)'}} />
      <AbsoluteFill style={{background: 'radial-gradient(ellipse 1000px 440px at 960px 600px, rgba(0,78,120,0.8), rgba(0,0,0,0) 100%)'}} />
      {dots.map(([x, y], i) => (
        <div
          key={i}
          style={{
            position: 'absolute', left: x, top: y - ((f * 0.12 * (1 + (i % 3))) % 40), width: 3, height: 3, borderRadius: 2,
            background: 'rgba(90,170,230,0.55)', opacity: 0.4 + 0.4 * Math.abs(Math.sin(f / 23 + i)),
          }}
        />
      ))}
    </AbsoluteFill>
  );
};

const Card: React.FC<{i: number; enter: number; letter: number; lit: number; lab: number}> = ({i, enter, letter, lit, lab}) => {
  const c = CARDS[i];
  const cx = CX(i);
  const left = cx - CARD_W / 2;
  const y = interpolate(enter, [0, 1], [70, 0]);
  const border = `rgba(${Math.round(interpolate(lit, [0, 1], [40, 30]))},${Math.round(interpolate(lit, [0, 1], [125, 170]))},${Math.round(interpolate(lit, [0, 1], [175, 235]))},${interpolate(lit, [0, 1], [0.75, 1])})`;
  const bw = interpolate(lit, [0, 1], [2, 3.2]);
  const glow = `0 0 ${interpolate(lit, [0, 1], [12, 18])}px ${interpolate(lit, [0, 1], [0, 11])}px rgba(0,150,230,${0.18 + 0.6 * lit}), 0 0 ${interpolate(lit, [0, 1], [30, 64])}px ${interpolate(lit, [0, 1], [0, 18])}px rgba(0,125,215,${0.1 + 0.45 * lit})`;
  const labBlur = interpolate(lab, [0, 1], [9, 0]);
  return (
    <div style={{position: 'absolute', left: 0, top: 0, width: 1920, height: 1080, opacity: enter < 1 ? enter : undefined, transform: y > 0.01 ? `translateY(${y}px)` : undefined}}>
      {/* halo additif (les halos de deux cartes voisines s'additionnent dans l'intervalle, comme dans la réf.) */}
      <div style={{position: 'absolute', left, top: CARD_TOP, width: CARD_W, height: CARD_H, borderRadius: 44, boxShadow: glow, mixBlendMode: 'plus-lighter'}} />
      {/* carte verre */}
      <div
        style={{
          position: 'absolute', left, top: CARD_TOP, width: CARD_W, height: CARD_H, borderRadius: 44, boxSizing: 'border-box',
          border: `${bw}px solid ${border}`, overflow: 'hidden',
          // Carte inactive sombre (réf. 214,0 : intérieur #00111B, haut #011D30), sans voile clair ni bande diagonale.
          background: 'linear-gradient(180deg, #021f33 0%, #01151f 22%, #00111b 45%, #000d18 75%, #000b15 100%)',
        }}
      >
        {/* Carte allumée : intérieur marine plus profond (réf. 222,5 : #000D15 -> #01080C). */}
        <div style={{position: 'absolute', inset: 0, opacity: lit, background: 'linear-gradient(180deg, #021a2b 0%, #000f19 30%, #000d15 60%, #01080c 100%)'}} />
      </div>
      {/* point lumineux en bas */}
      <div style={{position: 'absolute', left: cx - 13, top: 939, width: 26, height: 26, borderRadius: 13, background: 'radial-gradient(circle, rgba(70,200,255,1) 0%, rgba(20,160,240,0.8) 30%, rgba(0,140,230,0.4) 60%, rgba(0,100,200,0) 100%)', filter: 'blur(1px)'}} />
      {/* pastille d'icône */}
      <div
        style={{
          position: 'absolute', left: cx - 43, top: CARD_TOP - 43, width: 86, height: 86, borderRadius: 43, boxSizing: 'border-box',
          border: `3px solid rgba(40,170,235,${interpolate(lit, [0, 1], [0.8, 1])})`,
          background: 'radial-gradient(circle at 45% 30%, #173248 0%, #081a2a 55%, #04111c 100%)',
          boxShadow: `0 0 ${8 + 14 * lit}px rgba(0,150,240,${0.35 + 0.5 * lit})`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}
      >
        <Icon k={c.icon} />
      </div>
      {/* lettre lumineuse : contour clair dessous, remplissage cyan dessus, halo */}
      {[0, 1].map((layer) => (
        <div
          key={layer}
          style={{
            position: 'absolute', left: cx - 200, width: 400, top: 355, height: 330, textAlign: 'center',
            fontFamily: INTER_L, fontWeight: 800, fontSize: 272, lineHeight: '330px',
            color: layer ? '#0199E8' : 'rgba(115,208,255,1)',
            WebkitTextStroke: layer ? undefined : '5px rgba(115,208,255,1)',
            textShadow: layer ? undefined : '0 0 14px rgba(0,160,255,0.95), 0 0 36px rgba(0,130,255,0.6)',
            opacity: letter,
          }}
        >
          {c.l}
        </div>
      ))}
      {/* libellé */}
      {lab > 0 && (
        <div
          style={{
            position: 'absolute', left: cx - 220, width: 440, top: 686, textAlign: 'center',
            fontFamily: INTER_L, fontWeight: 700, fontSize: 64, lineHeight: '80px', color: '#fff', letterSpacing: -0.5,
            opacity: interpolate(lab, [0, 1], [0.55, 1]), filter: `blur(${labBlur}px)`,
            transform: `translateY(${interpolate(lab, [0, 1], [12, 0])}px)`,
          }}
        >
          {c.label}
        </div>
      )}
    </div>
  );
};

const Title: React.FC<{f: number; intro: boolean}> = ({f, intro}) => {
  const titre = React.useContext(TitreCtx);
  let k = 0;
  return (
    <div style={{position: 'absolute', left: 28, width: 1920, top: 28, textAlign: 'center', fontFamily: INTER_L, fontWeight: 700, fontSize: 86, lineHeight: '90px', color: '#fff', letterSpacing: -1}}>
      {titre.map((line, li) => (
        <div key={li}>
          {line.map((w, wi) => {
            const s = 3 + 3.3 * k++;
            const p = intro ? interpolate(f, [s, s + 14], [0, 1], {...clamp, easing: OUT}) : 1;
            return (
              <span
                key={wi}
                style={{
                  display: 'inline-block', marginRight: wi < line.length - 1 ? '0.25em' : 0,
                  opacity: p, transform: `translateY(${interpolate(p, [0, 1], [42, 0])}px)`,
                  filter: `blur(${interpolate(p, [0, 1], [3, 0])}px)`,
                  color: `rgb(${Math.round(interpolate(p, [0, 1], [170, 255]))},${Math.round(interpolate(p, [0, 1], [170, 255]))},${Math.round(interpolate(p, [0, 1], [175, 255]))})`,
                }}
              >
                {w}
              </span>
            );
          })}
        </div>
      ))}
    </div>
  );
};

const OccView: React.FC<{o: Occ}> = ({o}) => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill>
      <Bg />
      <Title f={f} intro={o.intro} />
      {CARDS.map((_, i) => {
        const cs = -6 + 12 * i;
        const enter = o.intro ? interpolate(f, [cs, cs + 16], [0, 1], {...clamp, easing: OUT}) : 1;
        const letter = o.intro ? interpolate(f, [cs + 2, cs + 18], [0.25, 1], clamp) : 1;
        const st = o.steps[i];
        let lit = 0;
        let lab = 0;
        if (st === 'on') {
          lit = 1;
          lab = 1;
        } else if (st) {
          lit = interpolate(f, [s2f(st.lit), s2f(st.lit) + 22], [0, 1], {...clamp, easing: Easing.inOut(Easing.quad)});
          lab = interpolate(f, [s2f(st.lab), s2f(st.lab) + 10], [0, 1], {...clamp, easing: OUT});
          if (f < s2f(st.lab)) lab = 0;
        }
        return <Card key={i} i={i} enter={enter} letter={letter} lit={lit} lab={lab} />;
      })}
    </AbsoluteFill>
  );
};

// Sons (SFX-REGLES.md) : whoosh à l'entrée du plein écran, grave-apparition sur chaque libellé.
const CUES: SfxCue[] = plan.flatMap(({o, from}) => [
  {frame: from, name: 'whoosh-transition' as const},
  ...o.steps.flatMap((st) => (st && st !== 'on' ? [{frame: from + s2f(st.lab), name: 'grave-apparition' as const}] : [])),
]);

const MapsFramework: React.FC<{showPlate?: boolean; titre?: string[][]}> = ({titre = TITLE}) => (
  <TitreCtx.Provider value={titre}>
  <AbsoluteFill style={{background: '#000', overflow: 'hidden'}}>
    {plan.map(({o, from, dur}, i) => (
      <Sequence key={i} from={from} durationInFrames={dur} layout="none">
        <OccView o={o} />
      </Sequence>
    ))}
    <SfxTrack cues={CUES} />
  </AbsoluteFill>
  </TitreCtx.Provider>
);

export const meta = {
  id: 'd211-maps-framework',
  fps: FPS,
  durationInFrames: plan[plan.length - 1].from + plan[plan.length - 1].dur,
  defaultProps: {showPlate: true},
  occurrences: plan.map(({o, from, dur}) => ({ref: o.ref, at: o.at, from, durationInFrames: dur, mode: 'plein' as const})),
};
export default MapsFramework;

// Signaux sonores exportés pour la bibliothèque (cloud/cues_globaux.py).
export const cues = CUES;
