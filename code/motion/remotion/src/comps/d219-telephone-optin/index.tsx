import React from 'react';
import {AbsoluteFill, Easing, Img, interpolate, Sequence, staticFile, useCurrentFrame} from '../../shared/rt';
import {INTER_L} from '../../shared/localFonts';
import {SfxTrack, SfxCue} from '../../shared/Sfx';

// d219 (plein cadre) : iPhone à cadre orange cuivré à gauche + pilule verre sombre à droite.
// Chez Dan : profil Instagram, DM « AI BUSINESS » et pilule « Follow @... on instagram & DM me ».
// Ici : page d'inscription simple (AI Operating System, champ « Votre email », bouton « Recevoir gratuitement »),
// frappe de l'email, appui, confirmation ; pilule « Lien en description : entrez votre email, c'est gratuit ».
// Réf. occ. 1 : entrée 733,10 s (zoom arrière flou depuis ~x2,4, ~14 images), coupe franche 738,17 s.
// Réf. occ. 2 : 1252,0 -> 1257,0 s, même mise en place.
// Géométrie (1920x1080, 734,2 s) : téléphone ~410 x 906 centré (456, 523), rotation -2,3°, cadre 13 px ;
//   pilule x 718..1833, y 481..599 (rayon 36), icône 51 px à x 747, texte blanc gras ~36 px à x 819.
const FPS = 30;
const GAP = 15;

type Occ = {ref: [number, number]; at: number; end: number; kbIn: number; type0: number; type1: number; press: number; done: number};
// Temps en secondes dans la voix coupée.
const OCC: Occ[] = [
  // « vous avez simplement un lien en description. Vous cliquez dessus, vous rentrez votre email
  //   et je vous l'envoie instantanément. C'est complètement gratuit. »
  {ref: [733.07, 738.17], at: 792.3, end: 797.2, kbIn: 793.95, type0: 794.17, type1: 794.87, press: 795.03, done: 795.37},
  // « vous avez simplement un lien dans la description, cliquez dessus, je vous l'envoie instantanément. »
  {ref: [1251.9, 1257.0], at: 1334.25, end: 1337.45, kbIn: 1335.45, type0: 1335.6, type1: 1336.15, press: 1336.25, done: 1336.63},
];

const plan = (() => {
  let from = 0;
  return OCC.map((o) => {
    const dur = Math.round((o.end - o.at) * FPS);
    const loc = (t: number) => Math.round((t - o.at) * FPS);
    const r = {o, from, dur, t: {kbIn: loc(o.kbIn), type0: loc(o.type0), type1: loc(o.type1), press: loc(o.press), done: loc(o.done)}};
    from += dur + GAP;
    return r;
  });
})();
type T = (typeof plan)[number]['t'];

const EMAIL = 'vous@entreprise.fr';
const PH = {w: 410, h: 906, cx: 456, cy: 523, rot: -2.3, border: 13, r: 62};
const SW = PH.w - 2 * PH.border;
const SH = PH.h - 2 * PH.border;
const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const PURPLE = '#5B4FF5';

const Background: React.FC = () => (
  <AbsoluteFill style={{background: 'radial-gradient(ellipse 55% 60% at 22% 42%, #17181c 0%, #0b0b0d 45%, #020203 80%, #000 100%)'}} />
);

// Clavier iOS sombre AZERTY.
const Keyboard: React.FC<{active: string}> = ({active}) => {
  const rows = ['azertyuiop', 'qsdfghjklm', 'wxcvbn'];
  const key = (c: string, w = 30) => (
    <div
      key={c}
      style={{
        width: w,
        height: 42,
        borderRadius: 6,
        background: c === active ? '#6b6c70' : '#3b3c40',
        color: '#fff',
        fontFamily: INTER_L,
        fontSize: 19,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        boxShadow: '0 1px 0 rgba(0,0,0,0.6)',
      }}
    >
      {c}
    </div>
  );
  return (
    <div style={{position: 'absolute', left: 0, bottom: 0, width: SW, height: 300, background: '#1c1d20', paddingTop: 12}}>
      {rows.map((r, i) => (
        <div key={i} style={{display: 'flex', justifyContent: 'center', gap: 5, marginBottom: 11}}>
          {i === 2 && key('⇧', 42)}
          {r.split('').map((c) => key(c))}
          {i === 2 && key('⌫', 42)}
        </div>
      ))}
      <div style={{display: 'flex', justifyContent: 'center', gap: 5}}>
        {key('123', 70)}
        {key('@', 34)}
        {key(' ', 150)}
        {key('.', 34)}
        {key('OK', 70)}
      </div>
    </div>
  );
};

const Screen: React.FC<{t: T}> = ({t}) => {
  const f = useCurrentFrame();
  const n = Math.round(interpolate(f, [t.type0, t.type1], [0, EMAIL.length], clamp));
  const typed = EMAIL.slice(0, n);
  const lastChar = n > 0 && f <= t.type1 + 1 ? EMAIL[n - 1] : '';
  const kb = interpolate(f, [t.kbIn, t.kbIn + 7, t.press, t.press + 7], [0, 1, 1, 0], {...clamp, easing: Easing.out(Easing.cubic)});
  const pressS = interpolate(f, [t.press, t.press + 3, t.press + 7], [1, 0.95, 1], clamp);
  const done = interpolate(f, [t.done, t.done + 9], [0, 1], {...clamp, easing: Easing.out(Easing.back(1.4))});
  const caret = f >= t.kbIn && f < t.press && Math.floor(f / 8) % 2 === 0;
  const focus = f >= t.kbIn && f < t.press + 4;
  return (
    <div style={{position: 'absolute', inset: 0, background: '#0b0f12', overflow: 'hidden', borderRadius: PH.r - PH.border, fontFamily: INTER_L}}>
      {/* barre d'état */}
      <div style={{position: 'absolute', left: 40, top: 22, color: '#fff', fontWeight: 600, fontSize: 18}}>9:41</div>
      <div style={{position: 'absolute', left: SW / 2 - 62, top: 14, width: 124, height: 36, borderRadius: 18, background: '#000'}} />
      <div style={{position: 'absolute', right: 34, top: 25, display: 'flex', gap: 6, alignItems: 'flex-end'}}>
        {[6, 9, 12, 15].map((h, i) => (
          <div key={i} style={{width: 4, height: h, borderRadius: 1, background: '#fff'}} />
        ))}
        <div style={{width: 26, height: 13, borderRadius: 4, border: '1.5px solid rgba(255,255,255,0.8)', marginLeft: 6, padding: 1.5}}>
          <div style={{width: '70%', height: '100%', background: '#fff', borderRadius: 2}} />
        </div>
      </div>
      {/* contenu de la page */}
      <div style={{position: 'absolute', left: 0, top: 58, width: SW, bottom: 0, overflow: 'hidden'}}>
      <div style={{position: 'absolute', left: 0, top: 38 - kb * 120, width: SW, textAlign: 'center'}}>
        <div style={{margin: '0 auto', width: 132, height: 164, borderRadius: 6, overflow: 'hidden', position: 'relative', boxShadow: '0 10px 30px rgba(40,110,255,0.35)'}}>
          <Img src={staticFile('d219/couverture-mini.png')} style={{position: 'absolute', left: 0, top: -2, width: 150, height: 186}} />
          <div style={{position: 'absolute', inset: 0, background: 'linear-gradient(90deg, #000 0%, #000 34%, rgba(0,0,0,0) 60%)'}} />
          <svg width={132} height={164} style={{position: 'absolute', inset: 0}}>
            <text x={11} y={86} fontFamily={INTER_L} fontWeight={900} fontSize={85} fill="#fff" textLength={36} lengthAdjust="spacingAndGlyphs">
              AI
            </text>
            <text x={11} y={103} fontFamily={INTER_L} fontWeight={900} fontSize={16} fill="#fff" textLength={50} lengthAdjust="spacingAndGlyphs">
              OPERATING
            </text>
            <text x={11} y={128} fontFamily={INTER_L} fontWeight={900} fontSize={28} fill="#fff" textLength={50} lengthAdjust="spacingAndGlyphs">
              SYSTEM
            </text>
          </svg>
        </div>
        <div style={{marginTop: 30, color: '#fff', fontWeight: 800, fontSize: 29, letterSpacing: -0.5}}>AI Operating System</div>
        <div style={{marginTop: 10, color: '#a8abb0', fontSize: 16, lineHeight: '22px'}}>
          Le système complet pour faire tourner
          <br />
          votre entreprise avec l'IA
        </div>
        {/* champ email */}
        <div
          style={{
            margin: '30px auto 0',
            width: SW - 56,
            height: 54,
            borderRadius: 14,
            background: '#1b2026',
            border: `1.5px solid ${focus ? PURPLE : '#333a41'}`,
            display: 'flex',
            alignItems: 'center',
            padding: '0 18px',
            boxSizing: 'border-box',
            fontSize: 18,
            color: typed ? '#fff' : '#7d828a',
            textAlign: 'left',
          }}
        >
          {typed || (caret ? '' : 'Votre email')}
          {caret && <div style={{width: 2, height: 24, background: PURPLE, marginLeft: 1}} />}
          {!typed && caret && <span style={{color: '#7d828a'}}>Votre email</span>}
        </div>
        {/* bouton */}
        <div
          style={{
            margin: '14px auto 0',
            width: SW - 56,
            height: 54,
            borderRadius: 14,
            background: done > 0.5 ? '#1f9d55' : PURPLE,
            color: '#fff',
            fontWeight: 700,
            fontSize: 18,
            lineHeight: '54px',
            transform: `scale(${pressS})`,
          }}
        >
          {done > 0.5 ? '✓  Envoyé' : 'Recevoir gratuitement'}
        </div>
        {/* confirmation */}
        <div
          style={{
            margin: '26px auto 0',
            width: SW - 56,
            borderRadius: 16,
            background: '#1b2026',
            border: '1px solid #2c333a',
            padding: '14px 16px',
            boxSizing: 'border-box',
            display: 'flex',
            gap: 12,
            alignItems: 'center',
            textAlign: 'left',
            opacity: Math.min(1, done * 1.4),
            transform: `translateY(${(1 - done) * 24}px) scale(${0.9 + 0.1 * done})`,
          }}
        >
          <div style={{width: 40, height: 40, borderRadius: 10, background: PURPLE, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0}}>
            <svg width={24} height={24} viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth={2} strokeLinejoin="round">
              <rect x={3} y={5} width={18} height={14} rx={2} />
              <path d="M3.5 6.5 L12 13 L20.5 6.5" />
            </svg>
          </div>
          <div>
            <div style={{color: '#fff', fontWeight: 700, fontSize: 16}}>C'est envoyé !</div>
            <div style={{color: '#a8abb0', fontSize: 14, marginTop: 2}}>Vérifiez votre boîte mail</div>
          </div>
        </div>
      </div>
      </div>
      {kb > 0 && (
        <div style={{position: 'absolute', left: 0, bottom: 0, width: SW, height: 300, transform: `translateY(${(1 - kb) * 300}px)`}}>
          <Keyboard active={lastChar} />
        </div>
      )}
      <div style={{position: 'absolute', left: SW / 2 - 70, bottom: 9, width: 140, height: 5, borderRadius: 3, background: 'rgba(255,255,255,0.85)'}} />
    </div>
  );
};

const Phone: React.FC<{t: T}> = ({t}) => (
  <div
    style={{
      position: 'absolute',
      left: PH.cx - PH.w / 2,
      top: PH.cy - PH.h / 2,
      width: PH.w,
      height: PH.h,
      borderRadius: PH.r,
      transform: `perspective(2400px) rotateY(9deg) rotate(${PH.rot}deg)`,
      background: 'linear-gradient(160deg, #F08A45 0%, #B9531E 22%, #E07A35 45%, #8E3A12 70%, #D06A2B 100%)',
      boxShadow: '0 30px 60px rgba(0,0,0,0.7), inset 0 0 0 2px rgba(255,190,140,0.5)',
    }}
  >
    <div style={{position: 'absolute', inset: PH.border - 3, borderRadius: PH.r - PH.border + 3, background: '#050506'}} />
    <div style={{position: 'absolute', inset: PH.border, borderRadius: PH.r - PH.border}}>
      <Screen t={t} />
    </div>
  </div>
);

// Icône de la pilule : cadre arrondi (comme l'icône d'origine) contenant un maillon de lien.
const LinkIcon: React.FC = () => (
  <svg width={51} height={51} viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth={1.9} strokeLinecap="round" strokeLinejoin="round">
    <rect x={1.5} y={1.5} width={21} height={21} rx={6} />
    <path d="M10.6 13.4a3 3 0 0 0 4.2 0l2.3-2.3a3 3 0 0 0-4.2-4.2l-1 1" />
    <path d="M13.4 10.6a3 3 0 0 0-4.2 0l-2.3 2.3a3 3 0 0 0 4.2 4.2l1-1" />
  </svg>
);

const Pill: React.FC = () => (
  <div
    style={{
      position: 'absolute',
      left: 718,
      top: 481,
      width: 1115,
      height: 118,
      borderRadius: 36,
      background: 'linear-gradient(180deg, #555a62 0%, #33373e 30%, #22262c 62%, #1a1d22 100%)',
      boxShadow: 'inset 0 0 0 2px rgba(210,215,225,0.55), inset 0 3px 2px rgba(255,255,255,0.25), 0 10px 30px rgba(0,0,0,0.6)',
      display: 'flex',
      alignItems: 'center',
      paddingLeft: 29,
      boxSizing: 'border-box',
    }}
  >
    <LinkIcon />
    <div
      style={{
        marginLeft: 21,
        fontFamily: INTER_L,
        fontWeight: 700,
        fontSize: 35,
        letterSpacing: -0.4,
        color: '#fff',
        whiteSpace: 'nowrap',
        textShadow: '0 2px 4px rgba(0,0,0,0.4)',
      }}
    >
      Lien en description : entrez votre email, c’est gratuit
    </div>
  </div>
);

const Scene: React.FC<{t: T; dur: number}> = ({t, dur}) => {
  const f = useCurrentFrame();
  // Entrée : zoom arrière flou (échelle ~2,4 -> 1) sur 14 images, puis léger zoom lent.
  const p = interpolate(f, [0, 14], [0, 1], {...clamp, easing: Easing.out(Easing.exp)});
  const s = interpolate(p, [0, 1], [2.4, 1]) * interpolate(f, [14, dur], [1, 1.015], clamp);
  const blur = (1 - p) * 22;
  const fade = interpolate(f, [0, 2], [0, 1], clamp);
  return (
    <AbsoluteFill style={{overflow: 'hidden'}}>
      <Background />
      <AbsoluteFill style={{transformOrigin: '620px 540px', transform: `scale(${s})`, filter: blur > 0.2 ? `blur(${blur.toFixed(2)}px)` : undefined, opacity: fade}}>
        <Phone t={t} />
        <Pill />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

const CUES: SfxCue[] = plan.flatMap(({from, t}) => [
  {frame: from + 1, name: 'whoosh-transition' as const},
  {frame: from + t.type0, name: 'frappe-clavier' as const, durationInFrames: t.type1 - t.type0 + 1},
  {frame: from + t.press, name: 'clic' as const},
  {frame: from + t.done, name: 'notification' as const},
]);

const TelephoneOptin: React.FC<{showPlate?: boolean}> = () => (
  <AbsoluteFill style={{background: '#000'}}>
    {plan.map(({from, dur, t}, i) => (
      <Sequence key={i} from={from} durationInFrames={dur} layout="none">
        <Scene t={t} dur={dur} />
      </Sequence>
    ))}
    <SfxTrack cues={CUES} />
  </AbsoluteFill>
);

export const meta = {
  id: 'd219-telephone-optin',
  fps: FPS,
  durationInFrames: plan[plan.length - 1].from + plan[plan.length - 1].dur,
  defaultProps: {showPlate: true},
  occurrences: plan.map(({o, from, dur}) => ({ref: o.ref, at: o.at, from, durationInFrames: dur, mode: 'plein' as const})),
};
export default TelephoneOptin;

// Signaux sonores exportés pour la bibliothèque (cloud/cues_globaux.py).
export const cues = CUES;
