import React from 'react';
import {AbsoluteFill, Easing, Img, interpolate, Sequence, staticFile, useCurrentFrame} from '../../shared/rt';
import {SfxTrack, SfxCue} from '../../shared/Sfx';
import {INTER_L} from '../../shared/localFonts';

// 22 : iPhone, messagerie LinkedIn mobile, frappe « YOUTUBE OS », réponse avec document.
// Occurrence 1 : 247,81 s à 252,92 s (153 images).
// Occurrence 2 : 885,70 s à 891,76 s (182 images), même animation, zoom prolongé.
// Entre les deux : 0,5 s de fond neutre.
const OCC1 = 153;
const GAP = 15;
const OCC2 = 182;
export const meta = {id: '22-telephone-dm', durationInFrames: OCC1 + GAP + OCC2, fps: 30,
  occurrences: [
    {ref: [247.81, 252.92], from: 0, durationInFrames: OCC1, mode: 'plein'},
    {ref: [885.7, 891.76], from: OCC1 + GAP, durationInFrames: OCC2, mode: 'plein'},
  ],
};

// Géométrie du téléphone relevée à 250,8 s (repos, échelle 1).
const PW = 467;
const PH = 970;
const REST_TOP = 68;

const SF = `-apple-system, "SF Pro Text", "Helvetica Neue", ${INTER_L}, sans-serif`;

const T = {
  name: 'Lucien Mallet',
  sub: 'lucien-ia',
  stats: '2,6 M abonnés · 3,5 k posts',
  line1: 'Vous suivez ce compte LinkedIn depuis 2024',
  line2: 'Relations en commun : chriswillx et 66 autres',
  replies: 'Répond généralement en',
  repliesBold: 'moins d’une heure',
  link: 'En savoir plus sur la messagerie LinkedIn',
  viewProfile: 'Voir le profil',
  time: '12:38',
  stamp: '12:38',
  message: 'Écrire un message…',
  typed: 'YOUTUBE OS',
  hey: 'Salut Koen',
  here: 'Et voilà',
  docTitle: 'Lucien Mallet - Playbook de l’OS IA d’entreprise',
  docHost: 'google.com',
};

const W = '#FFFFFF';
const GRAY = '#A8ABB0';
const SCREEN = '#1B1F23';
const KB_BG = '#16181C';
const KEY = '#343537';
const KEY_ON = '#4C4B4E';
const LI = '#0A66C2'; // bleu LinkedIn officiel
const PURPLE = LI;
const SEND = LI;
const CAM = '#2F3438';
const BUBBLE_IN = '#2F3438';
const LI_LINK = '#71B7FB';

// Frappe : [instant d'apparition du caractère en s, caractère]
const TYPING: [number, string][] = [
  [1.2, 'Y'], [1.4, 'O'], [1.5, 'U'], [1.6, 'T'], [1.75, 'U'], [1.9, 'B'], [2.0, 'E'], [2.15, ' '], [2.25, 'O'], [2.4, 'S'],
];
const KB_IN = [0.72, 1.02];
// Minutage propre à chaque occurrence (relevé image par image).
type Timing = {clear: number; kbOut: [number, number]; sent: number; hey: number; here: number; doc: number; zoom: number[]};
const TIM1: Timing = {clear: 2.68, kbOut: [2.6, 2.8], sent: 2.77, hey: 2.9, here: 3.4, doc: 3.53, zoom: [3.45, 4.0, 5.0, 5.9]};
const TIM2: Timing = {clear: 2.55, kbOut: [2.78, 2.92], sent: 2.9, hey: 3.1, here: 3.6, doc: 3.9, zoom: [3.7, 4.25, 5.25, 5.9]};

// ---------- icônes ----------
// Logo officiel LinkedIn « in » (absent de simple-icons)
const InBadge: React.FC<{s: number}> = ({s}) => (
  <svg width={s} height={s} viewBox="0 0 24 24" style={{display: 'inline-block', verticalAlign: 'middle'}}>
    <rect width={24} height={24} rx={3.5} fill={LI} />
    <path fill="#fff" d="M5.3 9.4h2.9V19H5.3zM6.75 4.8a1.68 1.68 0 110 3.36 1.68 1.68 0 010-3.36zM10.1 9.4h2.78v1.31h.04c.39-.73 1.33-1.5 2.74-1.5 2.93 0 3.47 1.93 3.47 4.44V19h-2.89v-4.6c0-1.1-.02-2.51-1.53-2.51-1.53 0-1.77 1.2-1.77 2.43V19H10.1z" />
  </svg>
);
const Stroke: React.FC<{d: string; s: number; w?: number; c?: string; vb?: number}> = ({d, s, w = 1.8, c = W, vb = 24}) => (
  <svg width={s} height={s} viewBox={`0 0 ${vb} ${vb}`} fill="none" stroke={c} strokeWidth={w} strokeLinecap="round" strokeLinejoin="round">
    <path d={d} />
  </svg>
);
const IC = {
  video: 'M3 7h11a1 1 0 011 1v8a1 1 0 01-1 1H3a1 1 0 01-1-1V8a1 1 0 011-1z M15 11l6-3.5v9L15 13',
  clip: 'M20 11.5l-8.2 8.2a5 5 0 01-7.1-7.1l8.5-8.5a3.3 3.3 0 014.7 4.7l-8.5 8.5a1.7 1.7 0 01-2.4-2.4l7.8-7.8',
  back: 'M15 4l-8 8 8 8',
  tag: 'M3 12.5V4a1 1 0 011-1h8.5L21 11.5 12.5 20z M7.5 7.5h.01',
  mic: 'M12 3a3 3 0 00-3 3v6a3 3 0 006 0V6a3 3 0 00-3-3z M5.5 11a6.5 6.5 0 0013 0 M12 17.5V21',
  image: 'M4 4h16v16H4z M4 16l5-5 4 4 3-3 4 4 M15.5 8.5h.01',
  sticker: 'M4 7a3 3 0 013-3h10a3 3 0 013 3v7a3 3 0 01-3 3h-5l-4 3v-3H7a3 3 0 01-3-3z M8.5 10.5h.01 M12 10.5h.01 M15.5 10.5h.01',
  plus: 'M12 3a9 9 0 110 18 9 9 0 010-18z M12 8v8 M8 12h8',
  search: 'M10.5 4a6.5 6.5 0 110 13 6.5 6.5 0 010-13z M15.5 15.5L20 20',
  info: 'M12 3a9 9 0 110 18 9 9 0 010-18z M12 11v5.5 M12 7.6h.01',
  share: 'M21 3L3 10l7 3 3 7z M10 13l4-4',
  globe: 'M12 3a9 9 0 110 18 9 9 0 010-18z M3 12h18 M12 3c3 3.2 3 14.8 0 18 M12 3c-3 3.2-3 14.8 0 18',
  replies: 'M2 8h6 M1 12h5 M2 16h6 M9 12a7 6 0 117 6l-3 2 .5-3A6 6 0 019 12z M11 12l2.5 1.5L16 10',
};

const Avatar: React.FC<{d: number; dot?: number}> = ({d, dot}) => (
  <div style={{position: 'relative', width: d, height: d}}>
    <Img src={staticFile('lucien-rond.png')} style={{width: d, height: d, borderRadius: '50%', objectFit: 'cover'}} />
    {dot ? (
      <div
        style={{
          position: 'absolute',
          right: -dot * 0.15,
          bottom: -dot * 0.05,
          width: dot,
          height: dot,
          borderRadius: '50%',
          background: '#01A04A',
          border: `${Math.max(2, dot * 0.22)}px solid ${SCREEN}`,
        }}
      />
    ) : null}
  </div>
);

// ---------- barre d'état + encoche ----------
const StatusBar: React.FC = () => (
  <>
    <div style={{position: 'absolute', left: 50, top: 21, fontSize: 19, fontWeight: 600, color: W, letterSpacing: -0.3, display: 'flex', alignItems: 'center', gap: 4}}>
      {T.time}
      <svg width={15} height={15} viewBox="0 0 24 24">
        <path d="M21 3L3 10.5l8 1.5 1.5 8z" fill={W} />
      </svg>
    </div>
    {/* encoche : partie haute + pilule */}
    <div style={{position: 'absolute', left: 142, top: 0, width: 177, height: 50, background: '#000', borderRadius: '0 0 26px 26px'}} />
    <div style={{position: 'absolute', left: 167, top: 30, width: 133, height: 44, background: '#000', borderRadius: 22}} />
    <div style={{position: 'absolute', left: 275, top: 50, width: 10, height: 10, borderRadius: 5, background: '#0e1330', boxShadow: 'inset 0 0 3px #3a4a9a'}} />
    {/* signal, wifi, batterie */}
    <svg style={{position: 'absolute', left: 331, top: 26}} width={22} height={16} viewBox="0 0 22 16">
      {[0, 1, 2, 3].map((i) => (
        <rect key={i} x={i * 5.5} y={12 - i * 3.5} width={4} height={4 + i * 3.5} rx={1} fill={W} />
      ))}
    </svg>
    <svg style={{position: 'absolute', left: 360, top: 24}} width={21} height={18} viewBox="0 0 24 20">
      <path d="M12 18l3-3.3a4.3 4.3 0 00-6 0z" fill={W} />
      <path d="M5.6 11.7a9 9 0 0112.8 0 M2.3 8.3a13.8 13.8 0 0119.4 0" stroke={W} strokeWidth={2.6} fill="none" strokeLinecap="round" />
    </svg>
    <div style={{position: 'absolute', left: 391, top: 25, width: 30, height: 17, borderRadius: 6, background: W, color: '#000', fontSize: 13, fontWeight: 700, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>85</div>
    <div style={{position: 'absolute', left: 422, top: 31, width: 3, height: 6, borderRadius: 2, background: 'rgba(255,255,255,0.5)'}} />
  </>
);

// ---------- en-tête + profil ----------
const Header: React.FC = () => (
  <>
    <div style={{position: 'absolute', left: 38, top: 81}}>
      <Stroke d={IC.back} s={24} w={2} />
    </div>
    <div style={{position: 'absolute', left: 75, top: 74}}>
      <div style={{borderRadius: '50%', padding: 1.5, border: '1.5px solid #555'}}>
        <Avatar d={33} dot={11} />
      </div>
    </div>
    <div style={{position: 'absolute', left: 121, top: 74, color: W, fontSize: 16, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 4}}>
      {T.name} <InBadge s={16} />
    </div>
    <div style={{position: 'absolute', left: 121, top: 96, color: GRAY, fontSize: 12}}>{T.sub}</div>
    <div style={{position: 'absolute', left: 364, top: 81}}>
      <Stroke d={IC.video} s={25} w={1.8} />
    </div>
    {[0, 1, 2].map((i) => (
      <div key={i} style={{position: 'absolute', left: 409 + i * 7, top: 92, width: 4.5, height: 4.5, borderRadius: 3, background: W}} />
    ))}
  </>
);

const Profile: React.FC = () => (
  <div style={{position: 'absolute', left: 0, top: 0, width: PW}}>
    <div style={{position: 'absolute', left: 234 - 48, top: 143}}>
      <Avatar d={96} dot={17} />
    </div>
    <div style={{position: 'absolute', top: 249, width: PW, textAlign: 'center', color: W, fontSize: 19, fontWeight: 700, letterSpacing: -0.2}}>
      {T.name} <InBadge s={19} />
    </div>
    {[
      [277, T.stats],
      [299, T.line1],
      [321, T.line2],
    ].map(([y, s]) => (
      <div key={String(y)} style={{position: 'absolute', top: y as number, width: PW, textAlign: 'center', color: '#C4C6CA', fontSize: 14.6, whiteSpace: 'nowrap'}}>
        {s}
      </div>
    ))}
    <div style={{position: 'absolute', top: 346, width: PW, display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 4, color: '#C4C6CA', fontSize: 15}}>
      <Stroke d={IC.replies} s={25} w={1.3} c="#C4C6CA" />
      <span>
        {T.replies} <b style={{color: W, fontWeight: 600}}>{T.repliesBold}</b>
      </span>
    </div>
    <div style={{position: 'absolute', top: 374, width: PW, textAlign: 'center', color: LI_LINK, fontSize: 13}}>{T.link}</div>
    <div style={{position: 'absolute', top: 406, left: 234 - 60, width: 120, height: 32, borderRadius: 16, border: '1.5px solid rgba(255,255,255,0.75)', boxSizing: 'border-box', color: W, fontSize: 13.5, fontWeight: 600, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
      {T.viewProfile}
    </div>
  </div>
);

// ---------- document reçu ----------
const Doc: React.FC = () => {
  const lines = [
    'Ce SOP t’aide à intégrer l’IA dans toute ton entreprise sans recruter, sans compétences techniques et sans systèmes complexes.',
    'Notre approche consiste à mettre en place l’IA de façon simple et concrète, pour renforcer tes opérations, ton équipe et tes flux de travail.',
    'Ce processus crée un système d’exploitation où l’IA travaille aux côtés de ton équipe, avec des résultats durables.',
    'C’est exactement ce que propose mon programme Elite Coaching.',
    'Écris-moi « ELITE » sur LinkedIn si tu veux en savoir plus.',
  ];
  return (
    <div style={{width: 248, height: 212, borderRadius: 14, overflow: 'hidden', background: '#26292D'}}>
      <div style={{height: 131, background: '#FAFAFA', position: 'relative', overflow: 'hidden', padding: '8px 22px 0 29px', color: '#333'}}>
        <div style={{fontSize: 4.4, lineHeight: '6px'}}>
          <span style={{background: '#F5F200', fontWeight: 700}}>NOTE : ce document fait partie de mon programme Elite Coaching.</span>
        </div>
        {lines.map((l, i) => (
          <div key={i} style={{fontSize: 3.6, lineHeight: '4.8px', marginTop: 5, color: '#444'}}>
            {l}
          </div>
        ))}
        <div style={{fontSize: 3.6, marginTop: 5, color: '#3A5FD0', textDecoration: 'underline'}}>https://www.linkedin.com/in/lucien-ia/</div>
        <div style={{position: 'absolute', left: 29, top: 108, fontSize: 9.2, fontWeight: 700, color: '#111', lineHeight: '11.5px', width: 210}}>
          LE SYSTÈME D’EXPLOITATION IA POUR LES DIRIGEANTS
        </div>
      </div>
      <div style={{padding: '12px 14px 0 13px'}}>
        <div style={{color: W, fontSize: 13.8, fontWeight: 600, lineHeight: '16.5px', height: 33, overflow: 'hidden'}}>{T.docTitle}</div>
        <div style={{display: 'flex', alignItems: 'center', gap: 6, marginTop: 11, color: GRAY, fontSize: 12}}>
          <Stroke d={IC.globe} s={16} w={1.6} c={GRAY} />
          {T.docHost}
        </div>
      </div>
    </div>
  );
};

// ---------- clavier AZERTY ----------
const ROWS = ['QWERTYUIOP', 'ASDFGHJKL', 'ZXCVBNM'];
const keyPos = (ch: string): {x: number; y: number} | null => {
  const r1 = ROWS[0].indexOf(ch);
  if (r1 >= 0) return {x: 42 + r1 * 43.6, y: 686};
  const r2 = ROWS[1].indexOf(ch);
  if (r2 >= 0) return {x: 64 + r2 * 43.6, y: 744};
  const r3 = ROWS[2].indexOf(ch);
  if (r3 >= 0) return {x: 108 + r3 * 43.6, y: 802};
  if (ch === ' ') return {x: 240, y: 862};
  return null;
};

const Key: React.FC<{x: number; y: number; w?: number; label: React.ReactNode; fs?: number; on?: boolean}> = ({x, y, w = 38, label, fs = 22, on}) => (
  <div
    style={{
      position: 'absolute',
      left: x - w / 2,
      top: y - 22,
      width: w,
      height: 44,
      borderRadius: 8,
      background: on ? KEY_ON : KEY,
      color: W,
      fontSize: fs,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      boxShadow: '0 1px 0 rgba(0,0,0,0.5)',
    }}
  >
    {label}
  </div>
);

const Keyboard: React.FC<{caps: boolean; pressed: string | null; sugg: string[]}> = ({caps, pressed, sugg}) => {
  const lab = (c: string) => (caps ? c : c.toLowerCase());
  const pp = pressed && pressed !== ' ' ? keyPos(pressed) : null;
  return (
    <div style={{position: 'absolute', left: 0, top: 0, width: PW, height: PH}}>
      <div style={{position: 'absolute', left: 24, top: 612, width: 420, height: 420, background: KB_BG, borderRadius: 16}} />
      {/* suggestions */}
      {sugg.map((s, i) => (
        <div key={i} style={{position: 'absolute', left: 30 + i * 140, width: 140, top: 624, textAlign: 'center', color: '#C9CACD', fontSize: 17}}>
          {s}
        </div>
      ))}
      <div style={{position: 'absolute', left: 164, top: 628, width: 1, height: 22, background: '#34363A'}} />
      <div style={{position: 'absolute', left: 304, top: 628, width: 1, height: 22, background: '#34363A'}} />
      {ROWS[0].split('').map((c, i) => (
        <Key key={c} x={42 + i * 43.6} y={686} label={lab(c)} on={pressed === c} />
      ))}
      {ROWS[1].split('').map((c, i) => (
        <Key key={c} x={64 + i * 43.6} y={744} label={lab(c)} on={pressed === c} />
      ))}
      <Key x={49} y={802} w={46} label={<svg width={20} height={20} viewBox="0 0 24 24"><path d="M12 3l9 9h-5v8H8v-8H3z" fill={caps ? W : 'none'} stroke={W} strokeWidth={1.6} strokeLinejoin="round" /></svg>} />
      {ROWS[2].split('').map((c, i) => (
        <Key key={c} x={108 + i * 43.6} y={802} label={lab(c)} on={pressed === c} />
      ))}
      <Key x={427} y={802} w={46} label={<svg width={24} height={18} viewBox="0 0 26 18"><path d="M8 1h16v16H8L1 9z" fill="none" stroke={W} strokeWidth={1.6} strokeLinejoin="round" /><path d="M12 5.5l7 7 M19 5.5l-7 7" stroke={W} strokeWidth={1.6} /></svg>} />
      <Key x={48} y={862} w={44} fs={17} label="123" />
      <Key x={102} y={862} w={44} label={<svg width={22} height={22} viewBox="0 0 24 24"><circle cx={12} cy={12} r={9} fill={W} /><circle cx={9} cy={10} r={1.3} fill={KEY} /><circle cx={15} cy={10} r={1.3} fill={KEY} /><path d="M7.5 13.5a5 5 0 009 0z" fill={KEY} /></svg>} />
      <div style={{position: 'absolute', left: 134, top: 840, width: 211, height: 44, borderRadius: 8, background: pressed === ' ' ? KEY_ON : KEY}}>
        <div style={{position: 'absolute', right: 10, bottom: 5, fontSize: 8, color: '#8a8a8e', fontWeight: 600}}>EN NL</div>
      </div>
      <Key x={401} y={862} w={98} label={<svg width={24} height={20} viewBox="0 0 24 20"><path d="M20 3v8H5 M9 6.5L5 11l4 4.5" fill="none" stroke={W} strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" /></svg>} />
      <div style={{position: 'absolute', left: 48, top: 908}}>
        <Stroke d={IC.globe} s={26} w={1.6} />
      </div>
      <div style={{position: 'absolute', left: 404, top: 906}}>
        <Stroke d={IC.mic} s={26} w={1.8} />
      </div>
      {/* bulle de la touche enfoncée */}
      {pp ? (
        <>
          <div style={{position: 'absolute', left: pp.x - 19, top: pp.y - 40, width: 38, height: 62, background: KEY_ON, borderRadius: '0 0 8px 8px'}} />
          <div
            style={{
              position: 'absolute',
              left: pp.x - 31,
              top: pp.y - 94,
              width: 62,
              height: 64,
              background: KEY_ON,
              borderRadius: 12,
              color: W,
              fontSize: 34,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 2px 6px rgba(0,0,0,0.4)',
            }}
          >
            {lab(pressed!)}
          </div>
        </>
      ) : null}
    </div>
  );
};

// ---------- barre de message ----------
const Bar: React.FC<{cy: number; text: string; typing: boolean}> = ({cy, text, typing}) => (
  <div style={{position: 'absolute', left: 0, top: cy - 22, width: PW, height: 44}}>
    <div style={{position: 'absolute', left: 22, right: 22, top: 0, bottom: 0, borderRadius: 22, background: '#1A1C1E'}} />
    {typing ? (
      <>
        <div style={{position: 'absolute', left: 26, top: 5, width: 34, height: 34, borderRadius: 17, background: CAM, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
          <Stroke d="M12 6v12M6 12h12" s={20} w={2.2} />
        </div>
        <div style={{position: 'absolute', left: 74, top: 11, fontSize: 16, color: W, whiteSpace: 'pre'}}>
          {text}
          <span style={{display: 'inline-block', width: 2, height: 19, background: '#6C4BFF', verticalAlign: 'middle', marginLeft: 1}} />
        </div>
        <div style={{position: 'absolute', left: 395, top: 5, width: 50, height: 34, borderRadius: 17, background: SEND, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
          <svg width={20} height={20} viewBox="0 0 24 24"><path d="M21 3L3 10l7 3 3 7z" fill={W} /><path d="M10 13l5-5" stroke={SEND} strokeWidth={2} /></svg>
        </div>
      </>
    ) : (
      <>
        <div style={{position: 'absolute', left: 26, top: 5, width: 34, height: 34, borderRadius: 17, background: CAM, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
          <Stroke d="M12 6v12M6 12h12" s={20} w={2.2} />
        </div>
        <div style={{position: 'absolute', left: 70, top: 12, fontSize: 15.5, color: '#9A9DA2'}}>{T.message}</div>
        {[IC.image, IC.clip, IC.sticker, IC.mic].map((d, i) => (
          <div key={i} style={{position: 'absolute', left: 280 + i * 40.7, top: 9}}>
            <Stroke d={d} s={26} w={1.7} />
          </div>
        ))}
      </>
    )}
  </div>
);

// ---------- messages (pile ancrée en bas) ----------
const Messages: React.FC<{t: number; tm: Timing}> = ({t, tm}) => {
  const pop = (t0: number) => interpolate(t, [t0, t0 + 0.12], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic)});
  const pSent = t >= tm.sent ? 1 : 0;
  const pHey = pop(tm.hey);
  const pHere = pop(tm.here);
  const pDoc = interpolate(t, [tm.doc, tm.doc + 0.25], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic)});
  // hauteurs (échelle 1) et écarts relevés
  const items: {h: number; gap: number; p: number; node: React.ReactNode; right?: boolean; key: string}[] = [
    {key: 'yt', h: 40, gap: 0, p: pSent, right: true, node: null},
    {key: 'hey', h: 36, gap: 14, p: pHey, node: null},
    {key: 'here', h: 33, gap: 10, p: pHere, node: null},
    {key: 'doc', h: 212, gap: 6, p: pDoc, node: null},
  ];
  const BOTTOM = 869;
  let y = BOTTOM;
  const pos: Record<string, number> = {};
  for (let i = items.length - 1; i >= 0; i--) {
    const it = items[i];
    const hh = (it.h + (i < items.length - 1 && items[i + 1].p > 0 ? 0 : 0)) * it.p;
    if (it.p <= 0) continue;
    y -= hh;
    pos[it.key] = y;
    y -= it.gap * it.p;
  }
  if (pSent <= 0) return null;
  const bubble = (txt: string, top: number, op: number) => (
    <div style={{position: 'absolute', left: 70, top, height: 36, padding: '0 14px', borderRadius: 18, background: BUBBLE_IN, color: W, fontSize: 15.5, display: 'flex', alignItems: 'center', opacity: op}}>
      {txt}
    </div>
  );
  const lastTop = pDoc > 0 ? (pos.doc ?? 0) + 212 : pHere > 0 ? (pos.here ?? 0) + 33 : (pos.hey ?? 0) + 36;
  return (
    <>
      <div style={{position: 'absolute', top: pos.yt - 45 + 13, width: PW, textAlign: 'center', color: '#8E9196', fontSize: 11}}>{T.stamp}</div>
      <div style={{position: 'absolute', left: 326, width: 122, top: pos.yt, height: 40, borderRadius: 20, background: PURPLE, color: W, fontSize: 15.5, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
        {T.typed}
      </div>
      {pHey > 0 ? bubble(T.hey, pos.hey, pHey) : null}
      {pHere > 0 ? bubble(T.here, pos.here - 1, pHere) : null}
      {pDoc > 0 ? (
        <>
          <div style={{position: 'absolute', left: 70, top: pos.doc}}>
            <Doc />
          </div>
        </>
      ) : null}
      {pHey > 0 ? (
        <div style={{position: 'absolute', left: 28, top: lastTop - 29}}>
          <Avatar d={29} />
        </div>
      ) : null}
    </>
  );
};

// ---------- téléphone complet ----------
const PhoneBody: React.FC<{t: number; tm: Timing}> = ({t, tm}) => {
  const kbIn = interpolate(t, KB_IN, [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic)});
  const kbOut = interpolate(t, tm.kbOut, [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.in(Easing.cubic)});
  const kb = kbIn * (1 - kbOut);
  const typed = TYPING.filter(([s]) => t >= s).map(([, c]) => c).join('');
  const typing = t >= 1.15 && t < tm.clear;
  const caps = t >= 1.05 && t < tm.kbOut[1];
  let pressed: string | null = null;
  for (const [s, c] of TYPING) if (t >= s - 0.1 && t < s) pressed = c;
  // suggestions relevées image par image (décalées d'environ 0,1 s sur la frappe)
  const lag = TYPING.filter(([s0]) => t - 0.08 >= s0).map(([, c]) => c).join('');
  const sugg = t >= tm.clear
    ? ['I', 'THE', 'I’M']
    : !caps
    ? ['I', 'The', 'I’m']
    : lag.length <= 1
      ? ['I', 'THE', 'I’M']
      : lag.length <= 4
        ? ['“YO”', 'YOU', 'YOUR']
        : lag.length <= 6
          ? ['“YOUTU”', 'YOUTUBE', '']
          : lag.length <= 9
            ? ['IS', 'EN', '']
            : ['“OS”', 'OSMOSE', '🐄'];
  const barCy = interpolate(kb, [0, 1], [901, 580]);
  return (
    <div style={{position: 'absolute', inset: 0, fontFamily: SF}}>
      {/* châssis cuivré */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          borderRadius: 78,
          background: 'linear-gradient(180deg, #7A2E18 0%, #C8683F 6%, #E9946A 40%, #B45F3E 75%, #F7BE94 99%)',
          boxShadow: '0 30px 60px rgba(0,0,0,0.55)',
        }}
      />
      <div style={{position: 'absolute', inset: 3, borderRadius: 75, background: 'linear-gradient(90deg, #F0A077 0%, #C4673F 3%, #D98559 50%, #B4603F 97%, #E69067 100%)'}} />
      {/* boutons latéraux */}
      {[
        [213, 55],
        [298, 80],
        [393, 80],
      ].map(([y, h]) => (
        <div key={y} style={{position: 'absolute', left: -5, top: y, width: 7, height: h, borderRadius: 3, background: 'linear-gradient(90deg,#8E4027,#E48A5E)'}} />
      ))}
      <div style={{position: 'absolute', right: -5, top: 310, width: 7, height: 110, borderRadius: 3, background: 'linear-gradient(90deg,#E48A5E,#8E4027)'}} />
      <div style={{position: 'absolute', inset: 8, borderRadius: 70, background: '#020203'}} />
      <div style={{position: 'absolute', left: 20, top: 18, right: 20, bottom: 18, borderRadius: 60, background: SCREEN, overflow: 'hidden'}}>
        <div style={{position: 'absolute', left: -20, top: -18, width: PW, height: PH}}>
          <Profile />
          <div style={{position: 'absolute', left: 0, top: 0, width: PW, height: 877, overflow: 'hidden'}}>
            <Messages t={t} tm={tm} />
          </div>
          {kb > 0 ? (
            <div style={{position: 'absolute', inset: 0, transform: `translateY(${(1 - kb) * 360}px)`}}>
              <Keyboard caps={caps} pressed={pressed} sugg={sugg} />
            </div>
          ) : null}
          <Bar cy={barCy} text={typed} typing={typing} />
          {/* voile sous la barre quand le clavier est rentré */}
          <div style={{position: 'absolute', left: 0, right: 0, top: 0, height: 128, background: `linear-gradient(${SCREEN} 88%, rgba(27,31,35,0))`}} />
          <Header />
          <StatusBar />
        </div>
      </div>
    </div>
  );
};

const PhoneScene: React.FC<{tm: Timing; lead?: number}> = ({tm, lead = 0}) => {
  const f = useCurrentFrame();
  const t = Math.max(0, (f - lead) / 30);
  const visible = f >= lead;
  // montée : sortie exponentielle relevée sur les images
  const top = interpolate(t, [0, 0.1, 0.3, 0.5, 0.7, 1.0, 1.7, 2.4, 3.0], [1080, 925, 744, 560, 440, 318, 152, 90, REST_TOP], {extrapolateRight: 'clamp'});
  const rotY = 63 * Math.exp(-1.6 * t);
  const shiftX = -45 * Math.exp(-1.5 * t);
  // zoom ancré sur le bas du téléphone
  const zoom = interpolate(t, tm.zoom, [1, 1.225, 1.595, 1.665], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const bottom = top + PH;
  return (
    <AbsoluteFill style={{perspective: 5000}}>
      <Img src={staticFile('22/bg.jpg')} style={{position: 'absolute', width: 1920, height: 1080}} />
      {visible && rotY > 0.5 ? (
        // flanc gauche : silhouette cuivrée derrière le téléphone, décalée de l'épaisseur projetée
        <div
          style={{
            position: 'absolute',
            left: 960 + shiftX - (PW / 2) * Math.cos((rotY * Math.PI) / 180) - 60 * Math.sin((rotY * Math.PI) / 180),
            top: top + 2,
            width: 160,
            height: PH - 4,
            borderRadius: 78,
            background: 'linear-gradient(90deg,#9A4A2C 0%,#D48456 35%,#B8653F 70%)',
          }}
        />
      ) : null}
      {visible ? (
        <div
          style={{
            position: 'absolute',
            left: 960 - PW / 2 + shiftX,
            top,
            width: PW,
            height: PH,
            transformOrigin: `50% ${PH - (bottom - 1035 > 0 ? 3 : 3)}px`,
            transform: `scale(${zoom}) rotateY(${-rotY}deg)`,
            transformStyle: 'preserve-3d',
          }}
        >
          <div style={{position: 'absolute', inset: 0, transform: 'translateZ(0.1px)'}}>
            <PhoneBody t={t} tm={tm} />
          </div>
        </div>
      ) : null}
    </AbsoluteFill>
  );
};

export default function TelephoneDM() {
  return (
    <AbsoluteFill style={{background: '#000'}}>
      <SfxTrack cues={cuesExportees} />
      <Sequence durationInFrames={OCC1}>
        <PhoneScene tm={TIM1} />
      </Sequence>
      <Sequence from={OCC1} durationInFrames={GAP}>
        <Img src={staticFile('22/bg.jpg')} style={{width: 1920, height: 1080}} />
      </Sequence>
      <Sequence from={OCC1 + GAP} durationInFrames={OCC2}>
        <PhoneScene tm={TIM2} lead={6} />
      </Sequence>
    </AbsoluteFill>
  );
}

// Signaux sonores exportés pour la bibliothèque (cloud/cues_globaux.py).
const cuesExportees: SfxCue[] = [
        // occurrence 1 : montée, une touche par clic, document reçu
        {frame: 1, name: 'whoosh-transition'},
        {frame: 33, name: 'clic'},
        {frame: 39, name: 'clic'},
        {frame: 42, name: 'clic'},
        {frame: 45, name: 'clic'},
        {frame: 50, name: 'clic'},
        {frame: 54, name: 'clic'},
        {frame: 57, name: 'clic'},
        {frame: 61, name: 'clic'},
        {frame: 64, name: 'clic'},
        {frame: 69, name: 'clic'},
        {frame: 106, name: 'notification'},
        // occurrence 2 (départ image 168, téléphone à 174)
        {frame: 175, name: 'whoosh-transition'},
        {frame: 207, name: 'clic'},
        {frame: 213, name: 'clic'},
        {frame: 216, name: 'clic'},
        {frame: 219, name: 'clic'},
        {frame: 224, name: 'clic'},
        {frame: 228, name: 'clic'},
        {frame: 231, name: 'clic'},
        {frame: 235, name: 'clic'},
        {frame: 238, name: 'clic'},
        {frame: 243, name: 'clic'},
        {frame: 291, name: 'notification'},
      ];
export const cues = cuesExportees;
