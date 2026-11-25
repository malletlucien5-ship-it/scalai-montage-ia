import React from 'react';
import {SfxTrack, SfxCue} from '../../shared/Sfx';
import {AbsoluteFill, Easing, interpolate, useCurrentFrame} from '../../shared/rt';
import {ARIAL_L} from '../../shared/localFonts';
// police de l'original : Helvetica Neue (mesurée sur le bouton et les descriptions)
const INTER = `"Helvetica Neue", Helvetica, Arial, ${ARIAL_L}, sans-serif`;

// Réf 820.55 à 824.52 s. Capture « Comment fonctionne Apex » + bouton CTA mot à mot.
export const meta = {
  id: '44-apex-cta',
  durationInFrames: 119,
  fps: 30,
  occurrences: [{ref: [820.55, 824.52] as [number, number], from: 0, durationInFrames: 119, mode: 'plein' as const}],
};

const FPS = 30;
const ease = Easing.out(Easing.cubic);
const ramp = (t: number, a: number, b: number, e = ease) =>
  interpolate(t, [a, b], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: e});

type Card = {
  id: string;
  x: number;
  y: number;
  w: number;
  h: number;
  emoji: string;
  title: string;
  sub: string;
  subC: string;
  desc: string;
  tags: string[];
  green?: boolean;
};

const C1 = 590;
const C2 = 840;
const C3 = 1090;
const CW = 236;

const CARDS: Card[] = [
  {id: 'sec', x: C1, y: 182, w: CW, h: 170, emoji: '🔐', title: 'Sécurité', sub: 'LE BOUCLIER', subC: '#8985d0', desc: 'Auto-hébergé. Les données sont à toi.', tags: ['Auto-hébergé', '1Password']},
  {id: 'gw', x: C2, y: 182, w: CW, h: 170, emoji: '📱', title: 'Passerelle', sub: 'LA PORTE D’ENTRÉE', subC: '#dc9352', desc: 'Tes apps reliées. Aucun nouvel outil.', tags: ['Slack', 'Email', 'WhatsApp']},
  {id: 'pi', x: C3, y: 182, w: CW, h: 170, emoji: '✍️', title: 'Agent PI', sub: 'LES MAINS', subC: '#5f8ad8', desc: 'Écrit du code. Fait des tâches. Agit.', tags: ['Tri des emails', 'Tâches web'], green: true},
  {id: 'hb', x: C1, y: 372, w: CW, h: 186, emoji: '❤️', title: 'Battement', sub: 'LE POULS', subC: '#c8639a', desc: 'Proactif. Agit sans qu’on lui demande.', tags: ['Priorités du jour', 'Briefings']},
  {id: 'sk', x: C3, y: 372, w: CW, h: 186, emoji: '⚡', title: 'Skills', sub: 'L’EXPERTISE', subC: '#52d69c', desc: 'Des playbooks prêts à l’emploi pour le travail complexe.', tags: ['Veille financière', 'Contenu'], green: true},
  {id: 'mem', x: 774, y: 579, w: 368, h: 186, emoji: '🧬', title: 'Mémoire', sub: 'LA PERSONNALITÉ', subC: '#45c6bc', desc: 'Te connaît. Retient les conversations, les préférences et le contexte de chaque échange.', tags: ['Notion', 'Livres', 'Transcriptions', 'CRM'], green: true},
];

// trajectoire du curseur (coordonnées écran à l'échelle 1)
const CUR: [number, number, number][] = [
  [0.0, 645, 365],
  [0.1, 672, 347],
  [0.4, 690, 345],
  [0.5, 835, 335],
  [0.6, 905, 334],
  [0.95, 930, 330],
  [1.0, 1015, 325],
  [1.1, 1125, 322],
  [1.2, 1158, 318],
  [1.45, 1155, 325],
  [1.5, 1065, 355],
  [1.6, 835, 465],
  [1.7, 752, 495],
  [2.0, 750, 500],
  [2.1, 955, 490],
  [2.2, 1180, 480],
  [2.3, 1210, 476],
  [2.6, 1218, 482],
  [2.7, 1160, 535],
  [2.8, 1035, 640],
  [2.9, 1005, 663],
  [3.97, 1003, 668],
];

const inRect = (px: number, py: number, c: {x: number; y: number; w: number; h: number}) => px >= c.x && px <= c.x + c.w && py >= c.y && py <= c.y + c.h;

const Arrow: React.FC = () => (
  <svg width={30} height={42} viewBox="0 0 20 28" style={{filter: 'drop-shadow(0 2px 3px rgba(0,0,0,0.6))'}}>
    <path d="M1.5 1.5 L1.5 22 L6.5 17.3 L10 25.5 L13.4 24 L10 16 L17 16 Z" fill="#111" stroke="#fff" strokeWidth={1.6} strokeLinejoin="round" />
  </svg>
);

const Words: React.FC<{words: string[]; t: number; inAt: number[]; outAt?: number[]}> = ({words, t, inAt, outAt}) => (
  <>
    {words.map((w, i) => {
      const a = ramp(t, inAt[i], inAt[i] + 0.16);
      const o = outAt ? ramp(t, outAt[i], outAt[i] + 0.12) : 0;
      return (
        <span
          key={i}
          style={{
            display: 'inline-block',
            marginRight: i < words.length - 1 ? '0.26em' : 0,
            opacity: a * (1 - o),
            transform: `translateY(${(1 - a) * 18 - o * 12}px)`,
          }}
        >
          {w}
        </span>
      );
    })}
  </>
);

// bruitages calés sur les images où chaque élément devient visible (SFX-REGLES.md)
const CUES: SfxCue[] = [
  {frame: 0, name: 'whoosh-transition'}, // fenêtre « Comment fonctionne Apex »
  {frame: 5, name: 'grave-apparition'}, // montée du bouton
];

const Comp: React.FC = () => {
  const f = useCurrentFrame();
  const t = f / FPS;
  const scale = 1 + 0.0076 * (t - 0.95);

  const cx = interpolate(t, CUR.map((p) => p[0]), CUR.map((p) => p[1]), {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.inOut(Easing.sin)});
  const cy = interpolate(t, CUR.map((p) => p[0]), CUR.map((p) => p[2]), {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.inOut(Easing.sin)});

  // intensité de survol lissée : on échantillonne la position du curseur sur les 4 dernières images
  const hoverOf = (c: {x: number; y: number; w: number; h: number}) => {
    let acc = 0;
    for (let k = 0; k < 5; k++) {
      const tt = Math.max(0, t - k / FPS);
      const px = interpolate(tt, CUR.map((p) => p[0]), CUR.map((p) => p[1]), {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.inOut(Easing.sin)});
      const py = interpolate(tt, CUR.map((p) => p[0]), CUR.map((p) => p[2]), {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.inOut(Easing.sin)});
      acc += inRect(px, py, c) ? 1 : 0;
    }
    return acc / 5;
  };

  const btn = ramp(t, 0, 0.5);
  const W1 = ['Rejoindre', 'la', 'liste', 'd’attente', 'Apex'];
  const W1in = [0.22, 0.34, 0.46, 0.58, 0.72];
  const W1out = [2.02, 1.94, 1.86, 1.78, 1.68];
  const W2 = ['Lien', 'en', 'description'];
  const W2in = [2.12, 2.32, 2.5];

  return (
    <AbsoluteFill style={{background: '#000', fontFamily: INTER}}>
      {/* fond noir, lueurs teal en bas */}
      <AbsoluteFill
        style={{
          background:
            'radial-gradient(ellipse 520px 380px at 2% 72%, rgba(22,58,74,0.85) 0%, rgba(12,34,46,0.5) 45%, rgba(0,0,0,0) 100%), radial-gradient(ellipse 900px 300px at 50% 104%, rgba(46,78,92,0.9) 0%, rgba(24,44,56,0.55) 45%, rgba(0,0,0,0) 100%), linear-gradient(180deg, #000 0%, #000 45%, #03080b 100%)',
        }}
      />
      {/* fenêtre capture */}
      <div style={{position: 'absolute', inset: 0, transform: `scale(${scale})`, transformOrigin: '960px 451px'}}>
        <div
          style={{
            position: 'absolute',
            left: 138,
            top: 89,
            width: 1643,
            height: 725,
            borderRadius: 22,
            boxSizing: 'border-box',
            background: '#0a0d18',
            border: '1.5px solid #3b3e4c',
            boxShadow: '0 0 60px rgba(0,0,0,0.8)',
            overflow: 'hidden',
          }}
        >
          <div style={{position: 'absolute', left: 0, right: 0, top: 0, textAlign: 'center', fontSize: 11.5, letterSpacing: 4, fontWeight: 500, color: '#5f626d'}}>ARCHITECTURE</div>
          <div style={{position: 'absolute', left: 0, right: 0, top: 23, textAlign: 'center', fontSize: 25, fontWeight: 700, color: '#eef2ff', letterSpacing: -0.2}}>Comment fonctionne Apex</div>
        </div>
        {/* cartes */}
        {CARDS.map((c) => {
          const h = hoverOf(c);
          return (
            <div
              key={c.id}
              style={{
                position: 'absolute',
                left: c.x,
                top: c.y,
                width: c.w,
                height: c.h,
                borderRadius: 12,
                boxSizing: 'border-box',
                background: h > 0 ? `rgb(${25 + h * 2},${28 + h * 2},${46 + h * 6})` : '#191c2e',
                border: `1.5px solid rgba(${38 + h * 40},${42 + h * 40},${58 + h * 45},1)`,
                boxShadow: `0 ${6 + h * 10}px ${14 + h * 22}px rgba(0,0,0,${0.35 + h * 0.3})`,
                transform: `scale(${1 + h * 0.045})`,
                zIndex: h > 0 ? 2 : 1,
                textAlign: 'center',
              }}
            >
              <div style={{position: 'absolute', left: 0, right: 0, top: 19, fontSize: 24, lineHeight: '28px'}}>{c.emoji}</div>
              <div style={{position: 'absolute', left: 0, right: 0, top: 61, fontSize: 15, fontWeight: 600, color: '#ebeeff'}}>{c.title}</div>
              <div style={{position: 'absolute', left: 0, right: 0, top: 83, fontSize: 10, fontWeight: 700, letterSpacing: 1.6, color: c.subC}}>{c.sub}</div>
              <div style={{position: 'absolute', left: 12, right: 12, top: 104, fontSize: 11.8, lineHeight: '16.5px', color: '#858899'}}>{c.desc}</div>
              <div
                style={{
                  position: 'absolute',
                  left: 0,
                  right: 0,
                  top: c.id === 'sk' || c.id === 'mem' ? 145 : 130,
                  display: 'flex',
                  justifyContent: 'center',
                  gap: 7,
                }}
              >
                {c.tags.map((g) => (
                  <div
                    key={g}
                    style={{
                      height: 19,
                      padding: '0 9px',
                      borderRadius: 10,
                      border: `1px solid ${c.green ? '#24605a' : '#2c3042'}`,
                      background: c.green ? 'rgba(20,70,60,0.18)' : 'transparent',
                      fontSize: 10,
                      lineHeight: '18px',
                      color: c.green ? '#5ccfb5' : '#7d8092',
                    }}
                  >
                    {g}
                  </div>
                ))}
              </div>
            </div>
          );
        })}
        {/* carte APEX */}
        {(() => {
          const c = {x: C2, y: 372, w: CW, h: 186};
          const h = hoverOf(c);
          return (
            <div
              style={{
                position: 'absolute',
                left: c.x,
                top: c.y,
                width: c.w,
                height: c.h,
                borderRadius: 12,
                boxSizing: 'border-box',
                background: 'linear-gradient(180deg, #372f5a 0%, #2d1e45 45%, #1c1235 100%)',
                border: `1.5px solid rgba(${80 + h * 40},${62 + h * 30},${140 + h * 40},1)`,
                transform: `scale(${1 + h * 0.03})`,
                textAlign: 'center',
                zIndex: 1,
              }}
            >
              <div
                style={{
                  position: 'absolute',
                  left: c.w / 2 - 27,
                  top: 43,
                  width: 54,
                  height: 54,
                  borderRadius: 27,
                  background: 'radial-gradient(circle at 40% 35%, #c49aff 0%, #a26bff 45%, #8a3cf0 100%)',
                  boxShadow: '0 0 22px rgba(160,90,255,0.55)',
                  fontSize: 20,
                  lineHeight: '54px',
                }}
              >
                🧠
              </div>
              <div style={{position: 'absolute', left: 0, right: 0, top: 107, fontSize: 17, fontWeight: 700, color: '#eef0ff', letterSpacing: 0.3}}>APEX</div>
              <div style={{position: 'absolute', left: 0, right: 0, top: 130, fontSize: 10, fontWeight: 600, letterSpacing: 2, color: '#7c6fb0'}}>LE CERVEAU</div>
            </div>
          );
        })()}
        {/* curseur */}
        <div style={{position: 'absolute', left: cx - 4, top: cy - 4, zIndex: 5}}>
          <Arrow />
        </div>
      </div>
      {/* bouton CTA */}
      <div
        style={{
          position: 'absolute',
          left: 410,
          top: 878,
          width: 1100,
          height: 123,
          borderRadius: 22,
          background: 'linear-gradient(100deg, #5070b0 0%, #4760a0 30%, #3e4b88 65%, #3a3c74 100%)',
          boxShadow: '0 10px 40px rgba(0,0,0,0.45), inset 0 1px 0 rgba(255,255,255,0.08)',
          opacity: btn,
          transform: `translateY(${(1 - btn) * 70}px)`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            position: 'absolute',
            left: 0,
            right: 0,
            top: 22,
            textAlign: 'center',
            fontSize: 65,
            lineHeight: '78px',
            fontWeight: 700,
            letterSpacing: 0,
            color: '#63fdff',
            textShadow: '0 0 18px rgba(80,240,255,0.65), 0 0 4px rgba(120,255,255,0.5)',
            whiteSpace: 'nowrap',
          }}
        >
          {t < 2.1 ? <Words words={W1} t={t} inAt={W1in} outAt={W1out} /> : <Words words={W2} t={t} inAt={W2in} />}
        </div>
      </div>
    <SfxTrack cues={CUES} />
    </AbsoluteFill>
  );
};

export default Comp;

// Signaux sonores exportés pour la bibliothèque (cloud/cues_globaux.py).
export const cues = CUES;
