import React from 'react';
import {AbsoluteFill, Sequence} from '../../shared/rt';
import {loadFont} from '@remotion/google-fonts/Newsreader';
import {Bg, Camera, Cursor, ClaudeMark, Mic, Chevron, ArrowUp, useT, samples, keys, fade, typedN, FONT, easeInOut} from './kit';
import {SfxTrack, SfxCue} from '../../shared/Sfx';
import {ARIAL_L, GEORGIA_L} from '../../shared/localFonts';

const SERIF = loadFont('normal', {weights: ['400', '500', '600']}).fontFamily;
const SERIF_I = loadFont('italic', {weights: ['400']}).fontFamily;

// Référence : 381,68 à 387,19 s (conversation) puis 387,19 à 393,06 s (tableur).
const A = 165;
const B = 176;
export const meta = {
  id: '29-excel-claude-chrome', durationInFrames: A + B, fps: 30,
  occurrences: [
    {ref: [381.68, 387.19], from: 0, durationInFrames: A, mode: 'plein'},
    {ref: [387.19, 393.06], from: A, durationInFrames: B, mode: 'plein'},
  ],
};

const Z1 = [0.9529,0.9541,0.9547,0.9553,0.9565,0.9571,0.9583,0.9589,0.9600,0.9606,0.9618,0.9624,0.9636,0.9642,0.9648,0.9660,0.9666,0.9678,0.9684,0.9696,0.9702,0.9714,0.9720,0.9726,0.9738,0.9744,0.9756,0.9761,0.9773,0.9779,0.9791,0.9797,0.9809,0.9815,0.9821,0.9833,0.9839,0.9851,0.9857,0.9869,0.9875,0.9887,0.9893,0.9905,0.9911,0.9917,0.9928,0.9934,0.9946,0.9952,0.9964,0.9970,0.9976,0.9988,1.0];
const Z2 = [0.9776,0.9776,0.9784,0.9784,0.9784,0.9793,0.9802,0.9802,0.9802,0.9810,0.9819,0.9819,0.9819,0.9819,0.9836,0.9836,0.9836,0.9836,0.9853,0.9853,0.9853,0.9853,0.9871,0.9871,0.9871,0.9871,0.9879,0.9888,0.9888,0.9888,0.9897,0.9905,0.9905,0.9905,0.9914,0.9922,0.9922,0.9922,0.9931,0.9931,0.9940,0.9940,0.9948,0.9948,0.9957,0.9957,0.9966,0.9966,0.9966,0.9974,0.9983,0.9983,0.9983,0.9991,0.9991,1.0,1.0];

const TXT = '#ECE9E6';
const DIM = '#8A8783';

const Ico: React.FC<{x: number; y: number; d: string; s?: number; c?: string; w?: number}> = ({x, y, d, s = 22, c = '#B8B5B0', w = 1.7}) => (
  <svg viewBox="0 0 24 24" width={s} height={s} style={{position: 'absolute', left: x - s / 2, top: y - s / 2}}>
    <path d={d} fill="none" stroke={c} strokeWidth={w} strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

const Hand: React.FC<{x: number; y: number; s?: number}> = ({x, y, s = 1}) => (
  <svg viewBox="0 0 24 26" width={34 * s} height={37 * s} style={{position: 'absolute', left: x - 12 * s, top: y - 3 * s}}>
    <path d="M9 13 V3.5 a1.6 1.6 0 0 1 3.2 0 V11 V9.5 a1.6 1.6 0 0 1 3.2 0 V11.5 V10.5 a1.6 1.6 0 0 1 3.2 0 V12 a1.6 1.6 0 0 1 3.2 0 V17 c0 4 -2.5 7 -6.5 7 h-2 c-2.6 0 -4 -1.2 -5.4 -3.2 L3.4 15.6 a1.7 1.7 0 0 1 2.7 -2 Z" fill="#fff" stroke="#111" strokeWidth="1.3" strokeLinejoin="round" />
    <path d="M12.2 17 V13.5 M15.4 17 V13.5 M18.6 17 V13.5" stroke="#111" strokeWidth="1" strokeLinecap="round" />
  </svg>
);

const IBeam: React.FC<{x: number; y: number}> = ({x, y}) => (
  <svg viewBox="0 0 14 30" width={12} height={26} style={{position: 'absolute', left: x - 6, top: y - 13}}>
    <path d="M2 2 Q7 2 7 6 V24 Q7 28 2 28 M12 2 Q7 2 7 6 M7 24 Q7 28 12 28 M4 15 H10" fill="none" stroke="#fff" strokeWidth="3.4" strokeLinecap="round" />
    <path d="M2 2 Q7 2 7 6 V24 Q7 28 2 28 M12 2 Q7 2 7 6 M7 24 Q7 28 12 28 M4 15 H10" fill="none" stroke="#111" strokeWidth="1.5" strokeLinecap="round" />
  </svg>
);

// ---------------- Conversation (coordonnées finales, fenêtre 120,131 1674x796) ----------------
const Q1 = 'Je suis mes leads dans Excel. Je veux retrouver ceux qui n’ont pas été contactés depuis plus de 7 jours et les marquer à relancer. Comment faire ?';
const Q2 = 'Écris-moi les instructions. Je les colle dans Claude dans mon navigateur.';
const STEPS: React.ReactNode[] = [
  <>Clique sur l’en-tête de la colonne <b>Dernier contact</b> pour la sélectionner</>,
  <>Va dans <b>Données → Filtrer</b> → filtre par date : <i style={{fontFamily: SERIF_I}}>avant il y a 7 jours</i></>,
  <>Sélectionne toutes les lignes visibles de la colonne <b>Statut</b></>,
  <>Tape <i style={{fontFamily: SERIF_I}}>« À relancer »</i> puis <b>Ctrl + Entrée</b> pour remplir la sélection</>,
  <>Enregistre le fichier avec <b>Ctrl + S</b></>,
];

const ChatWin: React.FC<{t: number}> = ({t}) => {
  const X = 120, Y = 131;
  const P = (x: number, y: number): React.CSSProperties => ({position: 'absolute', left: x - X, top: y - Y});
  const sent = t >= 3.1;
  const n2 = typedN(Q2.length, t, 0.1, 2.95);
  const introN = typedN(85, t, 3.7, 3.95);
  const stepsOp = STEPS.map((_, i) => fade(t, 3.95 + i * 0.1, 0.12));
  const headOp = fade(t, 3.9, 0.12);
  const iconsOp = fade(t, 4.4, 0.15);
  const intro = 'Voilà : copie ceci et colle-le dans Claude in Chrome avec ton fichier Excel ouvert :';
  const logoY = !sent ? 596 : t < 3.7 ? 290 : t < 4.4 ? keys(t, [[3.7, 340], [3.95, 400], [4.4, 610]]) : 692;
  const serif: React.CSSProperties = {fontFamily: SERIF, fontSize: 21.5, color: TXT, lineHeight: '36px'};
  return (
    <div style={{position: 'absolute', left: X, top: Y, width: 1674, height: 796, borderRadius: 22, background: '#1E1E1C', overflow: 'hidden', boxShadow: '0 40px 90px rgba(0,0,0,0.55)'}}>
      {/* rail */}
      <div style={{position: 'absolute', left: 0, top: 0, width: 53, height: 796, borderRight: '1px solid #30302D'}} />
      <div style={{position: 'absolute', left: 0, top: 0}}>
        <Ico x={23} y={26} d="M10 3.8 a6.3 5.8 0 0 0 -5.6 8.6 L3.6 15.6 L6.9 14.6 A6.3 5.8 0 1 0 10 3.8 Z M16.6 9.4 a5.4 5 0 0 1 3 8.4 L20.4 20.6 L17.3 19.8 a5.4 5 0 0 1 -6.4 -1.2" s={23} />
        <Ico x={23} y={71} d="M8.5 3.6 H15.5 M6.3 6.6 H17.7 M4.2 9.6 H19.8 L18.6 19 a1.6 1.6 0 0 1 -1.6 1.4 H7 a1.6 1.6 0 0 1 -1.6 -1.4 Z" s={23} />
        <Ico x={23} y={116} d="M6.4 12.2 a5.6 5.6 0 0 1 10.8 -2.3 M7.2 13.6 a3.8 3.8 0 1 0 0.01 0 Z M12.8 11.2 H18.6 a1.4 1.4 0 0 1 1.4 1.4 V19.4 a1.4 1.4 0 0 1 -1.4 1.4 H12.8 a1.4 1.4 0 0 1 -1.4 -1.4 V12.6 a1.4 1.4 0 0 1 1.4 -1.4 Z" s={23} />
        <Ico x={23} y={161} d="M4.6 8 H19.4 a1.4 1.4 0 0 1 1.4 1.4 V18.6 a1.4 1.4 0 0 1 -1.4 1.4 H4.6 a1.4 1.4 0 0 1 -1.4 -1.4 V9.4 A1.4 1.4 0 0 1 4.6 8 Z M8.8 8 V5.4 a1 1 0 0 1 1 -1 H14.2 a1 1 0 0 1 1 1 V8 M3.2 13.6 H20.8" s={23} />
        <Ico x={23} y={265} d="M7.5 7.5 L3 12 L7.5 16.5 M16.5 7.5 L21 12 L16.5 16.5 M13.8 4.5 L10.2 19.5" s={23} />
        <Ico x={23} y={310} d="M12 3 a9 9 0 1 0 0 18 c1.5 0 2 -1 1.5 -2.2 c-0.6 -1.4 0.3 -2.8 2 -2.8 H18 a3 3 0 0 0 3 -3 A9 9 0 0 0 12 3 Z M7.5 11 h.01 M10 7 h.01 M15 7.5 h.01" />
        <Ico x={23} y={691} d="M12 4 V14.5 M7.6 10.2 L12 14.6 L16.4 10.2 M4.2 16.4 V20 H19.8 V16.4" s={21} />
        <div style={{position: 'absolute', left: 30 - 4, top: 677 - 4, width: 8, height: 8, borderRadius: 4, background: '#4C8BF5'}} />
        <div style={{position: 'absolute', left: 1, top: 737, width: 44, height: 44, borderRadius: 22, background: '#D9D6D0', color: '#2A2927', fontSize: 20, fontWeight: 500, textAlign: 'center', lineHeight: '44px'}}>L</div>
      </div>

      {!sent ? (
        <>
          <div style={{...P(644, 161), width: 834, height: 93, borderRadius: 12, background: '#111111', boxSizing: 'border-box', padding: '15px 20px 0 20px', fontSize: 20.8, lineHeight: '31px', color: TXT}}>{Q1}</div>
          <div style={{...P(507, 310), width: 900, ...serif}}>
            Facile. Tu filtres ton tableau sur la colonne « Dernier contact », tu isoles tout ce qui dépasse 7 jours et tu passes leur statut à « À relancer ».
          </div>
          <div style={{...P(507, 401), width: 900, ...serif}}>
            Ouvre le fichier Excel dans ton navigateur et je peux le faire pour toi : donne les étapes à Claude in Chrome en les collant.
          </div>
          <IconsRow x={517} y={513} />
        </>
      ) : (
        <>
          <div style={{position: 'absolute', right: 1674 + X - 1478, top: 160 - Y, height: 62, borderRadius: 12, background: '#111111', padding: '0 21px', lineHeight: '62px', fontSize: 20.8, color: TXT, whiteSpace: 'nowrap', opacity: fade(t, 3.1, 0.1)}}>{Q2}</div>
          <div style={{...P(507, 278), ...serif, whiteSpace: 'nowrap'}}>{intro.slice(0, introN)}</div>
          <div style={{...P(509, 332), width: 3, height: 238, background: '#3A3835', opacity: headOp}} />
          <div style={{...P(534, 331), ...serif, fontWeight: 500, opacity: headOp}}>Claude in Chrome : tâche Excel</div>
          {STEPS.map((st, i) => (
            <div key={i} style={{...P(546, 367 + i * 38.2), ...serif, opacity: stepsOp[i], whiteSpace: 'nowrap'}}>
              <span style={{display: 'inline-block', width: 32}}>{i + 1}.</span>{st}
            </div>
          ))}
          <div style={{opacity: iconsOp}}>
            {t >= 4.85 && <div style={{...P(499, 590), width: 36, height: 36, borderRadius: 7, background: '#2F2F2D'}} />}
            <IconsRow x={517} y={608} copied={t >= 5.0} />
          </div>
          {t >= 4.8 && (
            <div style={{...P(478, 548), padding: '0 9px', height: 28, borderRadius: 6, background: '#F2F1EE', color: '#1E1E1C', fontSize: 14, lineHeight: '28px', opacity: keys(t, [[4.8, 0], [5.08, 1], [5.35, 1], [5.45, 0]])}}>Copier</div>
          )}
        </>
      )}
      <ClaudeMark x={527 - X} y={logoY - Y} size={46} glow={false} opacity={sent && t < 3.25 ? 0 : 1} />

      {/* saisie */}
      <div style={{...P(474, 751), width: 1030, height: 139, borderRadius: 20, background: '#2B2B29', border: '1px solid #3A3835', boxSizing: 'border-box'}}>
        {!sent ? (
          <div style={{position: 'absolute', left: 28, top: 28, fontSize: 21, color: TXT, whiteSpace: 'nowrap'}}>
            {Q2.slice(0, n2)}<span style={{display: 'inline-block', width: 1.5, height: 24, background: TXT, verticalAlign: 'middle', marginLeft: 1}} />
          </div>
        ) : (
          <div style={{position: 'absolute', left: 28, top: 28, fontSize: 21, color: DIM}}>Écris un message…</div>
        )}
        <Ico x={44} y={97} d="M12 4 V20 M4 12 H20" s={22} c="#D0CDC8" w={2} />
        <div style={{position: 'absolute', left: sent ? 724 : 717, top: 84, fontSize: 18.5, color: '#D0CDC8', display: 'flex', alignItems: 'center', gap: 8}}>Sonnet 4.6 <span style={{color: DIM}}>Faible</span><Chevron size={14} color={DIM} /></div>
        {!sent ? (
          <>
            <Mic x={918} y={87} h={22} color="#D0CDC8" />
            <div style={{position: 'absolute', left: 950, top: 67, width: 43, height: 43, borderRadius: 9, background: '#C5603C', display: 'flex', alignItems: 'center', justifyContent: 'center'}}><ArrowUp size={20} stroke={2.6} /></div>
          </>
        ) : (
          <>
            <Mic x={931} y={97} h={22} color="#D0CDC8" />
            <Ico x={986} y={97} d="M3 10 V14 M7 7 V17 M11 4 V20 M15 8 V16 M19 10 V14" s={26} c="#D0CDC8" w={1.8} />
          </>
        )}
      </div>
      <div style={{position: 'absolute', left: 0, width: 1674, top: 902 - Y, textAlign: 'center', fontSize: 15, color: '#7A7773', marginLeft: 987 - 120 - 837}}>Claude est une IA et peut se tromper. Vérifie ses réponses.</div>
      <div style={{position: 'absolute', inset: 0, borderRadius: 22, border: '1.6px solid rgba(214,214,214,0.8)'}} />
    </div>
  );
};

const IconsRow: React.FC<{x: number; y: number; copied?: boolean}> = ({x, y, copied}) => (
  <>
    {[
      copied ? 'M5 12.5 L10 17 L19 7' : 'M8 8 H18 V18 H8 Z M5 15 V5 H15',
      'M7 5 L18 12 L7 19 Z',
      'M7 11 V20 H4 V11 Z M7 11 L11 4 c1.5 0 2.3 1 2 2.5 L12.5 10 H18 a2 2 0 0 1 2 2.3 L18.8 18 a2.5 2.5 0 0 1 -2.5 2 H7',
      'M7 13 V4 H4 V13 Z M7 13 L11 20 c1.5 0 2.3 -1 2 -2.5 L12.5 14 H18 a2 2 0 0 0 2 -2.3 L18.8 6 a2.5 2.5 0 0 0 -2.5 -2 H7',
      'M20 12 a8 8 0 1 1 -2.4 -5.7 M20 4 V8 H16',
    ].map((d, i) => (
      <Ico key={i} x={x - 120 + i * 43.8} y={y - 131} d={d} s={22} c="#9C9994" w={1.6} />
    ))}
  </>
);

const SceneChat: React.FC = () => {
  const t = useT();
  const s = samples(t, Z1);
  const cx = keys(t, [[0, 1536], [2.8, 1530], [3.0, 1452], [3.3, 1452], [4.45, 1452], [4.85, 515]], easeInOut);
  const cy = keys(t, [[0, 888], [2.8, 886], [3.0, 846], [3.3, 846], [4.45, 846], [4.85, 616]], easeInOut);
  return (
    <AbsoluteFill>
      <Bg id="29" />
      <Camera scale={s} ox={957} oy={550}>
        <ChatWin t={t} />
        {t >= 4.8 ? <Hand x={cx} y={cy} /> : <Cursor x={cx - 3} y={cy - 3} size={42} />}
      </Camera>
    </AbsoluteFill>
  );
};

// ---------------- Tableur + panneau Claude in Chrome (fenêtre 376,61 1160x953) ----------------
const ROWS = [
  ['1', 'Sarah Johnson', 'Acme Corp', 'sarah@acme.com', '604-111-2222', '2026-06-06'],
  ['2', 'James Lee', 'TechNova', 'james@technova.io', '604-222-3333', '2026-05-30'],
  ['3', 'Mia Patel', 'Brightwave', 'mia@brightwave.ca', '778-333-4444', '2026-06-07'],
  ['4', 'Carlos Rivera', 'Nexus Media', 'carlos@nexus.com', '604-444-5555', '2026-05-25'],
  ['5', 'Emily Chen', 'Orion Labs', 'emily@orion.com', '778-555-6666', '2026-06-03'],
  ['6', 'David Kim', 'Apex Solutions', 'david@apex.ca', '604-666-7777', '2026-05-31'],
  ['7', 'Aisha Nwosu', 'Clearpath', 'aisha@clearpath.io', '778-777-8888', '2026-06-05'],
  ['8', 'Tom Huang', 'Skyline Inc', 'tom@skyline.com', '604-888-9999', '2026-05-18'],
  ['9', 'Nina Rossi', 'Vortex Studio', 'nina@vortex.ca', '778-999-0000', '2026-06-02'],
  ['10', 'Liam Okafor', 'Polaris Group', 'liam@polaris.com', '604-100-2020', '2026-05-29'],
];
const HEAD = ['ID', 'Nom', 'Entreprise', 'E-mail', 'Téléphone', 'Dernier contact'];
const COLX = [406, 458, 613, 769, 994, 1132, 1238];
const PASTE_LINES: React.ReactNode[] = [
  <>Claude in Chrome : tâche Excel</>,
  <>Clique sur l’en-tête de la colonne <b>Dernier contact</b> pour la sélectionner</>,
  <>Va dans <b>Données → Filtrer</b> → filtre par date : <i>avant il y a 7 jours</i></>,
  <>Sélectionne toutes les lignes visibles de la colonne <b>Statut</b></>,
  <>Tape <i>« À relancer »</i> puis <b>Ctrl + Entrée</b> pour remplir la sélection</>,
  <>Enregistre le fichier avec <b>Ctrl + S</b></>,
];
const PLAIN = [
  'Claude in Chrome : tâche Excel',
  'Clique sur l’en-tête de la colonne Dernier contact pour la sélectionner',
  'Va dans Données → Filtrer → filtre par date : avant il y a 7 jours',
  'Sélectionne toutes les lignes visibles de la colonne Statut',
  'Tape « À relancer » puis Ctrl + Entrée pour remplir la sélection',
  'Enregistre le fichier avec Ctrl + S',
];
const MENU2: (string | null)[] = ['Emoji et symboles', null, '~Annuler', '~Rétablir', null, '~Couper', '~Copier', 'Coller', 'Coller et adapter le style', 'Tout sélectionner', null, 'Réglages de langue', 'Sens de l’écriture ›', null, 'Inspecter', null, 'Remplissage auto ›'];

const Sheet: React.FC<{t: number}> = ({t}) => {
  const X = 376, Y = 61;
  const P = (x: number, y: number): React.CSSProperties => ({position: 'absolute', left: x - X, top: y - Y});
  const menuOp = keys(t, [[1.35, 0], [1.4, 1], [2.3, 1], [2.38, 0]]);
  const hlItem = t < 1.4 ? '' : t < 1.75 ? 'Réglages de langue' : 'Coller';
  const pasted = t >= 2.4;
  const sentMsg = t >= 4.0;
  const focused = t >= 0.95;
  const inputH = pasted && !sentMsg ? 250 : 68;
  return (
    <div style={{position: 'absolute', left: X, top: Y, width: 1160, height: 953, borderRadius: 22, overflow: 'hidden', background: '#FFFFFF', boxShadow: '0 40px 90px rgba(0,0,0,0.55)', fontFamily: `Arial, Helvetica, ${ARIAL_L}, sans-serif`}}>
      {/* barre de titre du visualiseur */}
      <div style={{...P(376, 61), width: 862, height: 44, background: '#2B2B29'}}>
        <div style={{position: 'absolute', left: 23, top: 0, lineHeight: '38px', fontSize: 17, color: '#CFCBC7', fontFamily: FONT}}>Relance_leads <span style={{color: '#8A8783'}}>· XLSX</span></div>
        <div style={{position: 'absolute', left: 1092 - 376 - 17, top: 2, width: 34, height: 34, borderRadius: 7, background: '#3A3A38', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
          <svg viewBox="0 0 24 24" width={20} height={20}><path d="M8 3 H16 L22 14 H14 Z" fill="#FBBC04" /><path d="M8 3 L2 14 L6 21 L12 10 Z" fill="#0F9D58" /><path d="M6 21 H18 L22 14 H10 Z" fill="#4285F4" /></svg>
        </div>
        <svg viewBox="0 0 24 24" width={22} height={22} style={{position: 'absolute', left: 1131 - 376 - 11, top: 8}}><path d="M12 4 V15 M7 10 L12 15 L17 10 M5 20 H19" fill="none" stroke="#E0DDD8" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /></svg>
        <svg viewBox="0 0 24 24" width={22} height={22} style={{position: 'absolute', left: 1171 - 376 - 11, top: 8}}><path d="M20 12 a8 8 0 1 1 -2.4 -5.7 M20 4 V8 H16" fill="none" stroke="#E0DDD8" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /></svg>
        <svg viewBox="0 0 24 24" width={20} height={20} style={{position: 'absolute', left: 1210 - 376 - 10, top: 9}}><path d="M5 5 L19 19 M19 5 L5 19" fill="none" stroke="#E0DDD8" strokeWidth="2" strokeLinecap="round" /></svg>
      </div>
      <div style={{...P(376, 105), width: 862, height: 40, background: '#FFF', borderBottom: '1px solid #E3E3E3'}}>
        <div style={{position: 'absolute', left: 9, top: 11, fontStyle: 'italic', fontSize: 14, color: '#9A9A9A', fontFamily: `Georgia, ${GEORGIA_L}, serif`}}>fx</div>
      </div>
      {/* en-têtes de colonnes */}
      <div style={{...P(376, 145), width: 862, height: 23, background: '#F3F3F3', borderBottom: '1px solid #D6D6D6'}} />
      {['A', 'B', 'C', 'D', 'E', 'F'].map((c, i) => (
        <div key={c} style={{...P(COLX[i], 145), width: COLX[i + 1] - COLX[i], height: 23, textAlign: 'center', lineHeight: '23px', fontSize: 15, color: '#555', borderLeft: '1px solid #D9D9D9', boxSizing: 'border-box'}}>{c}</div>
      ))}
      <div style={{...P(376, 145), width: 30, height: 828, background: '#F3F3F3', borderRight: '1px solid #D6D6D6'}} />
      {/* ligne d'en-tête bleu marine */}
      <div style={{...P(406, 168), width: 832, height: 44, background: '#1E3766'}} />
      {HEAD.map((h, i) => (
        <div key={h} style={{...P(COLX[i], 168), width: COLX[i + 1] - COLX[i], height: 44, textAlign: 'center', lineHeight: '44px', fontSize: 15, fontWeight: 700, color: '#FFF', whiteSpace: 'nowrap', overflow: 'hidden', borderLeft: '1px solid #2E4A7E', boxSizing: 'border-box'}}>{h}</div>
      ))}
      {ROWS.map((r, j) => {
        const y = 212 + j * 35.3;
        return (
          <React.Fragment key={j}>
            <div style={{...P(406, y), width: 832, height: 35.3, background: j % 2 === 0 ? '#F3F4FB' : '#FFFFFF', borderBottom: '1px solid #E4E4E4', boxSizing: 'border-box'}} />
            {r.map((v, i) => (
              <div key={i} style={{...P(COLX[i], y), width: COLX[i + 1] - COLX[i], height: 35.3, lineHeight: '35px', fontSize: 15, color: '#222', paddingLeft: i === 0 ? 0 : 5, textAlign: i === 0 ? 'center' : 'left', borderLeft: '1px solid #E0E0E0', boxSizing: 'border-box', whiteSpace: 'nowrap', overflow: 'hidden'}}>{v}</div>
            ))}
          </React.Fragment>
        );
      })}
      {Array.from({length: 16}).map((_, j) => {
        const y = 565 + j * 25.7;
        return (
          <React.Fragment key={j}>
            <div style={{...P(406, y), width: 832, height: 25.7, borderBottom: '1px solid #E4E4E4', boxSizing: 'border-box'}} />
            {COLX.slice(1, 6).map((x) => <div key={x} style={{...P(x, y), width: 1, height: 25.7, background: '#E4E4E4'}} />)}
          </React.Fragment>
        );
      })}
      {Array.from({length: 27}).map((_, j) => {
        const y = j === 0 ? 168 : j <= 10 ? 212 + (j - 1) * 35.3 : 565 + (j - 11) * 25.7;
        const h = j === 0 ? 44 : j <= 10 ? 35.3 : 25.7;
        return <div key={j} style={{...P(376, y), width: 30, height: h, textAlign: 'center', lineHeight: `${j <= 10 ? h + 18 : h}px`, fontSize: 14, color: '#666'}}>{j + 1}</div>;
      })}
      <div style={{...P(376, 972), width: 862, height: 42, background: '#F7F7F7', borderTop: '1px solid #DDD'}}>
        <div style={{position: 'absolute', left: 8, top: 0, width: 80, height: 40, background: '#FFF', textAlign: 'center', lineHeight: '42px', fontSize: 15, color: '#333'}}>Leads</div>
      </div>

      {/* panneau Claude in Chrome : cadre brun mesuré (#4E3627), contenu #252523 à coin arrondi */}
      <div style={{...P(1238, 61), width: 298, height: 953, background: '#4E3627', fontFamily: FONT}}>
        <ClaudeMark x={22} y={8} size={11} color="#C96B5A" glow={false} />
        <div style={{position: 'absolute', left: 34, top: -1, lineHeight: '20px', fontSize: 11.5, fontWeight: 600, color: '#E3D2C8'}}>Claude</div>
        <svg viewBox="0 0 24 24" width={11} height={11} style={{position: 'absolute', left: 266 - 5.5, top: 3}}><path d="M9 3 H15 M10 3 V9 L7 13 H17 L14 9 V3 M12 13 V21" fill="none" stroke="#D8C6BC" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" /></svg>
        <div style={{position: 'absolute', left: 8, top: 22, right: 0, bottom: 0, background: '#252523', borderTopLeftRadius: 12, boxShadow: '-1.5px 0 0 #3A241A, -3px 0 0 #2B251E inset'}}>
          <div style={{position: 'absolute', left: 16, top: 14, fontSize: 12.5, color: '#CFCBC7', display: 'flex', alignItems: 'center', gap: 3, fontFamily: SERIF}}>Sonnet 4.6 <Chevron size={10} color="#8A8783" /></div>
          <svg viewBox="0 0 24 24" width={13} height={13} style={{position: 'absolute', left: 1490 - 1246 - 6.5, top: 17}}><path d="M6.2 17.2 A7.6 7.6 0 1 1 9 19.3 L4.6 20.2 Z" fill="none" stroke="#9A9793" strokeWidth="2" strokeLinejoin="round" /><circle cx="12.3" cy="11.8" r="2.3" fill="none" stroke="#9A9793" strokeWidth="2" /></svg>
          <svg viewBox="0 0 24 24" width={12} height={12} style={{position: 'absolute', left: 1519 - 1246 - 6, top: 17.5}}><circle cx="12" cy="5" r="1.8" fill="#9A9793" /><circle cx="12" cy="12" r="1.8" fill="#9A9793" /><circle cx="12" cy="19" r="1.8" fill="#9A9793" /></svg>
        </div>
        {sentMsg && (
          <>
            <div style={{position: 'absolute', left: 1299 - 1238, top: 133 - 61, width: 220, borderRadius: 10, background: '#131310', padding: '9px 12px', boxSizing: 'border-box', fontSize: 11.2, color: '#E8E5E0', lineHeight: '16.2px', opacity: fade(t, 4.0, 0.12)}}>
              {PLAIN.map((l, i) => <div key={i}>{l}</div>)}
            </div>
            <ClaudeMark x={1272 - 1238} y={350 - 61} size={16} glow={false} opacity={0.6 + 0.4 * Math.abs(Math.sin(t * 5))} />
          </>
        )}
        {/* saisie du panneau */}
        <div style={{position: 'absolute', left: 17, bottom: 44, width: 268, height: inputH, borderRadius: 12, background: '#2D2D2B', border: '1px solid #3A3A37', boxSizing: 'border-box'}}>
          {pasted && !sentMsg ? (
            <div style={{position: 'absolute', left: 12, top: 12, width: 244, fontSize: 11.2, color: '#E8E5E0', lineHeight: '16.2px'}}>
              {PASTE_LINES.map((l, i) => <div key={i} style={{fontWeight: i === 0 ? 600 : 400}}>{l}</div>)}
            </div>
          ) : (
            <div style={{position: 'absolute', left: 13, top: 12, fontSize: 11.5, color: '#77746F'}}>
              {sentMsg ? <><span style={{display: 'inline-block', width: 1, height: 13, background: '#DDD', verticalAlign: 'middle'}} />Réponds à Claude</> : focused ? 'Tape / pour les commandes' : 'Comment puis-je t’aider aujourd’hui ?'}
            </div>
          )}
          <div style={{position: 'absolute', left: 13, bottom: 12, fontSize: 9.5, color: '#A3A09C', display: 'flex', alignItems: 'center', gap: 4}}>
            <svg viewBox="0 0 24 24" width={11} height={11}><circle cx="12" cy="12" r="10" fill="none" stroke="#A3A09C" strokeWidth="1.8" /><path d="M8.5 14 V9.5 a1.2 1.2 0 0 1 2.4 0 V12 V8 a1.2 1.2 0 0 1 2.4 0 V12 V9 a1.2 1.2 0 0 1 2.4 0 V14.5 a3.6 3.6 0 0 1 -7.2 0 Z" fill="#A3A09C" /></svg>
            Demander avant d’agir <Chevron size={8} color="#77746F" />
          </div>
          <svg viewBox="0 0 24 24" width={13} height={13} style={{position: 'absolute', left: 187 - 6.5, bottom: 11}}><path d="M10 9 L19 13 L15 14.5 L13.5 18.5 Z M6 3 V6 M2.5 6.5 H5.5 M3.5 3.5 L5.5 5.5 M9.5 3.5 L8 5" fill="none" stroke="#A3A09C" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" /></svg>
          <svg viewBox="0 0 24 24" width={12} height={12} style={{position: 'absolute', left: 216 - 6, bottom: 11.5}}><path d="M12 4 V20 M4 12 H20" stroke="#A3A09C" strokeWidth="2.2" strokeLinecap="round" /></svg>
          <div style={{position: 'absolute', left: 246 - 11, bottom: 7, width: 22, height: 21, borderRadius: 6, background: pasted && !sentMsg ? '#C5603C' : sentMsg ? '#2F2F2D' : '#7A4A36', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
            {sentMsg ? <svg viewBox="0 0 24 24" width={13} height={13}><circle cx="12" cy="12" r="8" fill="none" stroke="#D6D3CF" strokeWidth="2.2" /><circle cx="12" cy="12" r="3.6" fill="#D6D3CF" /></svg> : <ArrowUp size={12} stroke={2.6} color={pasted ? '#fff' : '#C9A493'} />}
          </div>
        </div>
        <div style={{position: 'absolute', left: 8, right: 0, bottom: 12, textAlign: 'center', fontSize: 8.5, color: '#6F6C68', lineHeight: '12px'}}>Claude est une IA et peut se tromper. Vérifie<br />ses réponses.</div>
      </div>
      {/* menu contextuel (sombre) */}
      {menuOp > 0 && (
        <div style={{position: 'absolute', left: 1324 - X, top: 742 - Y, width: 156, padding: '5px 4px', borderRadius: 6, background: '#252525', border: '1px solid #444', boxShadow: '0 8px 24px rgba(0,0,0,0.5)', opacity: menuOp, fontSize: 11, fontWeight: 600, color: '#EEE', fontFamily: FONT}}>
          {MENU2.map((m, i) =>
            m === null ? (
              <div key={i} style={{height: 1, background: '#444', margin: '3px 6px'}} />
            ) : (
              <div key={i} style={{height: 17.5, lineHeight: '17.5px', padding: '0 6px', borderRadius: 3, background: m === hlItem ? '#1F5FD6' : 'transparent', color: m.startsWith('~') ? '#777' : '#EEE', display: 'flex', justifyContent: 'space-between'}}>
                <span>{m.replace('~', '').replace(' ›', '')}</span>{m.endsWith('›') && <span>›</span>}
              </div>
            ),
          )}
        </div>
      )}
      <div style={{position: 'absolute', inset: 0, borderRadius: 22, border: '1.6px solid rgba(214,214,214,0.8)', pointerEvents: 'none'}} />
    </div>
  );
};

const SceneSheet: React.FC = () => {
  const t = useT();
  const s = samples(t, Z2);
  // curseur : zone de saisie, clic droit, « Coller », puis envoi
  const cx = keys(t, [[0, 1330], [0.8, 1325], [0.95, 1300], [1.35, 1300], [1.55, 1335], [1.8, 1340], [2.4, 1340], [3.3, 1505], [3.6, 1512], [4.6, 1512]], easeInOut);
  const cy = keys(t, [[0, 960], [0.8, 930], [0.95, 925], [1.35, 925], [1.55, 915], [1.8, 862], [2.4, 862], [3.3, 950], [3.6, 955], [4.6, 955]], easeInOut);
  const ibeam = t >= 0.9 && t < 1.35;
  const hand = t >= 2.6;
  return (
    <AbsoluteFill>
      <Bg id="29" />
      <Camera scale={s} ox={957} oy={494}>
        <Sheet t={t} />
        {ibeam ? <IBeam x={cx} y={cy} /> : hand ? <Hand x={cx} y={cy} s={1.2} /> : <Cursor x={cx - 3} y={cy - 3} size={46} />}
      </Camera>
    </AbsoluteFill>
  );
};

// Bruitages. Conversation : 0, tableur : 165.
const CUES: SfxCue[] = [
  {frame: 0, name: 'whoosh-transition'},
  {frame: 3, name: 'frappe-clavier', durationInFrames: 86},
  {frame: 92, name: 'clic'},
  {frame: 111, name: 'notification'},
  {frame: 147, name: 'clic'},
  {frame: 165, name: 'whoosh-transition'},
  {frame: 207, name: 'clic'},
  {frame: 235, name: 'clic'},
  {frame: 285, name: 'clic'},
];

const Comp: React.FC = () => (
  <AbsoluteFill style={{backgroundColor: '#000', fontFamily: FONT}}>
      <SfxTrack cues={CUES} />
    <Sequence durationInFrames={A}><SceneChat /></Sequence>
    <Sequence from={A} durationInFrames={B}><SceneSheet /></Sequence>
  </AbsoluteFill>
);
export default Comp;

// Signaux sonores exportés pour la bibliothèque (cloud/cues_globaux.py).
export const cues = CUES;
