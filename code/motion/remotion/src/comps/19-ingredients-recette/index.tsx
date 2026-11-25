import React from 'react';
import {SfxTrack, SfxCue} from '../../shared/Sfx';
import {AbsoluteFill, Easing, interpolate, useCurrentFrame} from '../../shared/rt';
import {ARIAL_L} from '../../shared/localFonts';
// police de l'original : Helvetica Neue (mesurée sur les largeurs de mots)
const HN = `"Helvetica Neue", Helvetica, Arial, ${ARIAL_L}, sans-serif`;

// Réf 208.81 à 217.32 s. Deux fenêtres « Prompt maître » / « Prompt système ».
export const meta = {
  id: '19-ingredients-recette',
  durationInFrames: 255,
  fps: 30,
  occurrences: [{ref: [208.81, 217.32] as [number, number], from: 0, durationInFrames: 255, mode: 'plein' as const}],
};

const FPS = 30;
const RED = '#e3141f';
const RED_LABEL = '#b3161f';
const CYAN = '#6cf2f0';
const CYAN_LABEL = '#5fd3cc';

const ease = Easing.out(Easing.cubic);
const fadeAt = (f: number, start: number, dur = 0.25) =>
  interpolate(f / FPS, [start, start + dur], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: ease});

type Seg = {t: string; b?: boolean};
// deux lignes par entrée, coupées comme l'original
type Item = {label: string; lines: Seg[][]};

const LEFT: Item[] = [
  {label: 'RÔLE', lines: [[{t: 'Stratège marketing SaaS B2B.', b: true}, {t: ' Cible : fondateurs de 1 M$ à 10 M$'}], [{t: 'd’ARR. Offre phare : coaching à 5 k$.'}]]},
  {label: 'TA FAÇON DE TRAVAILLER', lines: [[{t: 'Direct, assuré, zéro blabla.', b: true}, {t: ' Chiffré. Phrases courtes. Toujours concret.'}], [{t: 'Finir par une prochaine étape précise.'}]]},
  {label: 'TON ÉQUIPE', lines: [[{t: 'Opérateur solo', b: true}, {t: ' + 2 personnes au contenu. Un monteur vidéo, une'}], [{t: 'assistante. Rapide, asynchrone par défaut.'}]]},
  {label: 'TES OUTILS', lines: [[{t: 'Claude, Notion, ClickUp, Slack, Loom, Typeform. '}, {t: 'Process tous documentés', b: true}], [{t: 'dans Notion.', b: true}]]},
  {label: 'RÈGLES DE SORTIE', lines: [[{t: 'Des puces pour les actions. Jamais de jargon sans explication. Ton : '}, {t: 'direct', b: true}], [{t: 'et assuré', b: true}, {t: ', jamais corporate.'}]]},
];

const RIGHT: Item[] = [
  {label: 'CONSIGNES DE TÂCHE', lines: [[{t: 'La tâche précise', b: true}, {t: ' que tu confies à l’IA, avec ton contexte comme'}], [{t: 'fondation.'}]]},
  {label: 'PROCESSUS', lines: [[{t: 'Des instructions pas à pas', b: true}, {t: ' sur la façon d’aborder, structurer et livrer'}], [{t: 'le résultat.'}]]},
  {label: 'CONTRAINTES', lines: [[{t: 'Quoi inclure ou éviter.', b: true}, {t: ' Règles de format, longueur, ajustements de ton'}], [{t: 'propres à ce cas d’usage.'}]]},
  {label: 'FORMAT DE SORTIE', lines: [[{t: 'Exactement ce que tu veux recevoir', b: true}, {t: ' : structure, exemples, puces, longueur,'}], [{t: 'type de livrable.'}]]},
  {label: 'INJECTION DU CONTEXTE', lines: [[{t: 'Là où '}, {t: 'le prompt maître se branche', b: true}, {t: ' : rôle, voix, audience, outils guident'}], [{t: 'chaque réponse automatiquement.'}]]},
];

const Window: React.FC<{
  x: number;
  title: string;
  badge: string;
  titleA: string;
  titleB: string;
  accent: 'red' | 'cyan';
  items: Item[];
  t0: number; // apparition fenêtre (s)
}> = ({x, title, badge, titleA, titleB, accent, items, t0}) => {
  const f = useCurrentFrame();
  const win = fadeAt(f, t0, 0.3);
  const isRed = accent === 'red';
  const badgeO = fadeAt(f, t0 + 0.3, 0.2);
  const titleO = fadeAt(f, t0 + 0.4, 0.2);
  return (
    <div
      style={{
        position: 'absolute',
        left: x,
        top: 154,
        width: 805,
        height: 762,
        borderRadius: 14,
        background: '#100f16',
        border: '1.5px solid #25252e',
        boxShadow: '0 30px 80px rgba(0,0,0,0.65), 0 0 0 1px rgba(0,0,0,0.4)',
        overflow: 'hidden',
        opacity: win,
        transform: `translateY(${(1 - win) * 12}px)`,
        fontFamily: HN,
      }}
    >
      {/* barre de titre */}
      <div style={{height: 36, background: '#18181c', borderBottom: '1px solid #212128', position: 'relative'}}>
        {['#f6605c', '#f8bc2f', '#28c548'].map((c, i) => (
          <div key={i} style={{position: 'absolute', left: 17 + i * 18.5, top: 12, width: 12, height: 12, borderRadius: 6, background: c}} />
        ))}
        <div style={{position: 'absolute', left: 0, right: 0, top: 8, textAlign: 'center', fontSize: 15, fontWeight: 600, color: '#8b8a92', letterSpacing: 0.3}}>
          {title}
        </div>
      </div>
      {/* badge */}
      <div
        style={{
          position: 'absolute',
          left: 42,
          top: 74,
          height: 26,
          padding: '0 13px',
          borderRadius: 13,
          background: isRed ? '#2a0f16' : '#172b31',
          border: isRed ? '1px solid #3f1219' : '1.5px solid #3b8a8c',
          boxShadow: isRed ? '0 0 14px rgba(200,20,40,0.25)' : 'none',
          display: 'flex',
          alignItems: 'center',
          fontSize: 13,
          fontWeight: 700,
          letterSpacing: 2.2,
          color: isRed ? '#c3172a' : '#7eeee4',
          opacity: badgeO,
        }}
      >
        {badge}
      </div>
      {/* titre */}
      <div style={{position: 'absolute', left: 42, top: 121, fontSize: 38, fontWeight: 700, color: '#f2f2f4', letterSpacing: -0.4, opacity: titleO}}>
        {titleA}
        <span style={{color: isRed ? RED : CYAN}}>{titleB}</span>
      </div>
      <div style={{position: 'absolute', left: 42, right: 42, top: 191, height: 1.5, background: '#24232a', opacity: titleO}} />
      {items.map((it, i) => {
        const o = fadeAt(f, t0 + 0.55 + i * 0.2, 0.3);
        const top = 219 + i * 99;
        return (
          <div key={i} style={{position: 'absolute', left: 42, top, right: 44, opacity: o, transform: `translateY(${(1 - o) * 6}px)`}}>
            <div style={{position: 'absolute', left: 0, top: isRed ? 3 : 0, fontSize: isRed ? 13 : 15, fontWeight: 700, color: isRed ? '#34333a' : '#3a3940'}}>
              {isRed ? `${i + 1}.` : '→'}
            </div>
            <div style={{position: 'absolute', left: 37, top: 0, fontSize: 13.5, fontWeight: 700, letterSpacing: 2, color: isRed ? RED_LABEL : CYAN_LABEL}}>
              {it.label}
            </div>
            <div style={{position: 'absolute', left: 37, top: 20, fontSize: 19.6, lineHeight: '29.5px', color: '#8f8e95', fontWeight: 400, whiteSpace: 'nowrap'}}>
              {it.lines.map((ln, li) => (
                <div key={li}>
                  {ln.map((s, k) => (
                    <span key={k} style={s.b ? {color: '#f3f3f5', fontWeight: 700} : {}}>
                      {s.t}
                    </span>
                  ))}
                </div>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
};

// bruitages calés sur les images où chaque élément devient visible (SFX-REGLES.md)
const CUES: SfxCue[] = [
  {frame: 12, name: 'whoosh-transition'}, // fenêtre « Prompt maître » (0,4 s)
  {frame: 84, name: 'pop'}, // pastille « vs » (2,8 s)
  {frame: 126, name: 'whoosh-transition'}, // fenêtre « Prompt système » (4,2 s)
];

const Comp: React.FC = () => {
  const f = useCurrentFrame();
  const bg = fadeAt(f, 0, 0.35);
  const vs = fadeAt(f, 2.7, 0.3);
  return (
    <AbsoluteFill style={{background: '#000'}}>
      <AbsoluteFill
        style={{
          opacity: bg,
          background:
            'radial-gradient(ellipse 1300px 520px at 50% 108%, rgba(14,40,105,0.85) 0%, rgba(10,28,80,0.45) 45%, rgba(0,0,0,0) 100%), linear-gradient(180deg, #05060f 0%, #070a1c 40%, #08112c 100%)',
        }}
      />
      <Window x={74} title="Prompt maître" badge="PROMPT MAÎTRE" titleA="Tes " titleB="ingrédients" accent="red" items={LEFT} t0={0.3} />
      <Window x={1041} title="Prompt système" badge="PROMPT SYSTÈME" titleA="La " titleB="recette" accent="cyan" items={RIGHT} t0={4.1} />
      <div
        style={{
          position: 'absolute',
          left: 927,
          top: 503,
          width: 66,
          height: 66,
          borderRadius: 33,
          background: '#11152c',
          border: '1.5px solid #282c44',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontFamily: HN,
          fontSize: 15,
          fontWeight: 700,
          color: '#7a7e94',
          opacity: vs,
        }}
      >
        vs
      </div>
    <SfxTrack cues={CUES} />
    </AbsoluteFill>
  );
};

export default Comp;

// Signaux sonores exportés pour la bibliothèque (cloud/cues_globaux.py).
export const cues = CUES;
