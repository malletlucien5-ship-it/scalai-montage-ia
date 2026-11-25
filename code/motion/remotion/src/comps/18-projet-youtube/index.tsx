import React from 'react';
import {AbsoluteFill, Sequence} from '../../shared/rt';
import {Bg, Camera, MacWindow, ClaudeMark, Mic, ArrowUp, Chevron, useT, samples, fade, FONT} from './kit';
import {INTER} from '../../shared/fonts';
import {SfxTrack, SfxCue} from '../../shared/Sfx';

// Référence : 184,42 à 189,99 s puis 194,33 à 198,33 s.
const A = 167;
const B = 120;
const GAP = 15;
export const meta = {
  id: '18-projet-youtube', durationInFrames: A + GAP + B, fps: 30,
  occurrences: [
    {ref: [184.42, 189.99], from: 0, durationInFrames: A, mode: 'plein'},
    {ref: [194.33, 198.33], from: A + GAP, durationInFrames: B, mode: 'plein'},
  ],
};

const ZA = [0.9290,0.9297,0.9303,0.9303,0.9303,0.9316,0.9316,0.9329,0.9342,0.9342,0.9355,0.9368,0.9382,0.9395,0.9408,0.9421,0.9447,0.9460,0.9473,0.9486,0.9512,0.9525,0.9544,0.9564,0.9577,0.9603,0.9616,0.9642,0.9655,0.9674,0.9694,0.9714,0.9733,0.9753,0.9766,0.9785,0.9805,0.9818,0.9837,0.9850,0.9870,0.9883,0.9896,0.9909,0.9922,0.9935,0.9948,0.9961,0.9961,0.9974,0.9980,0.9987,0.9987,1.0,1.0];
const ZB = [0.8960,0.8960,0.8973,0.8980,0.8993,0.9013,0.9027,0.9053,0.9073,0.9100,0.9133,0.9160,0.9193,0.9227,0.9260,0.9300,0.9340,0.9380,0.9413,0.9453,0.9487,0.9527,0.9567,0.9607,0.9647,0.9687,0.9713,0.9753,0.9780,0.9820,0.9847,0.9873,0.9900,0.9920,0.9940,0.9960,0.9973,0.9987,0.9993,1.0];

// Coordonnées de conception = état final de l'occurrence A (fenêtre 199,71 1535x936).
const W = {x: 199, y: 71, w: 1535, h: 936};
const SIDE_X = 1333;
const FILES = [
  {name: 'Document_voix', lines: '284'},
  {name: 'Charte_marque', lines: '421'},
  {name: 'Exemples_scripts', lines: '135'},
];
const OUTLINE: [string, string][] = [
  ['Accroche', 'ouvre sur le problème : on utilise l’IA comme Google'],
  ['Le déclic', 'les projets donnent à Claude contexte et mémoire'],
  ['Démo live', 'montre ton projet YouTube en action'],
  ['Résultats', 'idées plus rapides, voix constante, rien à réexpliquer'],
  ['Appel à l’action', 'crée ton premier projet aujourd’hui'],
];

const DocIcon: React.FC<{size?: number}> = ({size = 17}) => (
  <svg viewBox="0 0 24 24" width={size} height={size}>
    <path d="M7 3.5 H13.5 L18.5 8.5 V19 a1.5 1.5 0 0 1 -1.5 1.5 H7 a1.5 1.5 0 0 1 -1.5 -1.5 V5 a1.5 1.5 0 0 1 1.5 -1.5 Z" fill="none" stroke="#6A6FF0" strokeWidth="1.7" strokeLinejoin="round" />
    <path d="M13.5 3.5 V8.5 H18.5 Z" fill="#6A6FF0" />
  </svg>
);

const Avatar: React.FC<{x: number; y: number}> = ({x, y}) => (
  // relevé sur l'original : tête pleine et épaules en arche, gris clair
  <div style={{position: 'absolute', left: x - 17.5, top: y - 17.5, width: 35, height: 35, borderRadius: 18, background: '#262422', border: '1px solid #3A3836', boxSizing: 'border-box'}}>
    <svg viewBox="0 0 35 35" width={35} height={35} style={{position: 'absolute', left: -1, top: -1}}>
      <circle cx="17.5" cy="13" r="3" fill="#C4C1BD" />
      <path d="M11 23.5 C11 18.2 13.6 16.4 17.5 16.4 C21.4 16.4 24 18.2 24 23.5" fill="none" stroke="#D2CFCB" strokeWidth="2.1" strokeLinecap="round" />
    </svg>
  </div>
);

const FileCard: React.FC<{f: typeof FILES[0]; bottom: number; op: number}> = ({f, bottom, op}) => (
  <div style={{opacity: op}}>
    <div style={{position: 'absolute', right: W.x + W.w - 1252, top: bottom - 61 - W.y, height: 61, borderRadius: 10, background: '#1C1A18', border: '1px solid #2E2B29', boxSizing: 'border-box', display: 'flex', alignItems: 'center', padding: '0 15px 0 14px'}}>
      <div style={{width: 34, height: 40, borderRadius: 6, background: '#262422', border: '1px solid #33302E', boxSizing: 'border-box', display: 'flex', alignItems: 'center', justifyContent: 'center'}}><DocIcon /></div>
      <div style={{marginLeft: 12}}>
        <div style={{fontSize: 13.5, fontWeight: 600, color: '#ECE9E6', lineHeight: '17px'}}>{f.name}</div>
        <div style={{fontSize: 11, fontWeight: 600, color: '#77716C', lineHeight: '15px'}}>DOCX · {f.lines} lignes</div>
      </div>
    </div>
    <Avatar x={1281 - W.x} y={bottom - 16 - W.y} />
  </div>
);

const Ui: React.FC<{t: number; mode: 'A' | 'B'}> = ({t, mode}) => {
  // apparition des cartes fichier (A) ; en B tout est déjà là
  // Instants relevés image par image (30 i/s) : la pile saute d'un coup, le contenu apparaît en fondu de 4 images.
  const cardT = mode === 'A' ? [7 / 30, 67 / 30, 127 / 30] : [-9, -9, -9];
  const cardOp = cardT.map((c) => fade(t, c, 4 / 30));
  const promptOp = mode === 'B' ? fade(t, 21 / 30, 4 / 30) : 0;
  const respOp = mode === 'B' ? fade(t, 38 / 30, 3 / 30) : 0;
  const GAPY = 13;
  const RESP_H = 191;
  const PROMPT_H = 50;
  // pile ancrée en bas (898) : hauteur animée de chaque élément
  const hResp = mode === 'B' && t >= 38 / 30 ? RESP_H + GAPY : 0;
  const hPrompt = mode === 'B' && t >= 21 / 30 ? PROMPT_H + GAPY : 0;
  const hCard = cardT.map((c, i) => (t >= c ? (i === 0 ? 61 : 61 + 14) : 0));
  const base = 898;
  const respBottom = base;
  const promptBottom = base - hResp;
  const c3 = promptBottom - hPrompt;
  const c2 = c3 - hCard[2];
  const c1 = c2 - hCard[1];
  const cardBottoms = [c1, c2, c3];
  const header = 'Voici le plan de ta vidéo :';
  const nh = t >= 66 / 30 ? header.length : 0;
  const itemOp = [69, 72, 75, 78.5, 82].map((fr) => fade(t, fr / 30, 3 / 30));
  const skel = t < 61 / 30 ? 1 : 0;
  const label: React.CSSProperties = {position: 'absolute', left: 1355 - W.x, fontSize: 12.5, fontWeight: 600, letterSpacing: 1.1, color: '#8A8581'};
  return (
    <MacWindow x={W.x} y={W.y} w={W.w} h={W.h} r={24} titleH={51} titleBg="#161412" bodyBg="#1A1716" sep="#22201E"
      title="PROJET VIDÉO YOUTUBE" titleSize={14.5} titleColor="#95918D" titleSpacing={2.4} dotX={22} dotGap={22} dotR={7} font={INTER}>
      {/* barre latérale */}
      <div style={{position: 'absolute', left: SIDE_X - W.x, top: 52, width: W.x + W.w - SIDE_X, height: W.h - 52, background: '#151311', borderLeft: '1px solid #22201E'}} />
      <div style={{...label, top: 153 - 9 - W.y}}>MÉMOIRE</div>
      <div style={{position: 'absolute', left: 1355 - W.x, top: 172 - W.y, width: 352, height: 60, borderRadius: 8, background: '#1F1C1B', border: '1px solid #2A2725', boxSizing: 'border-box', padding: '11px 14px'}}>
        <div style={{fontSize: 12.5, fontWeight: 600, color: '#C9C4C0', lineHeight: '18px'}}>Mémoire</div>
        <div style={{fontSize: 11, fontWeight: 600, color: '#6A6562', lineHeight: '18px', whiteSpace: 'nowrap'}}>La mémoire du projet apparaîtra après quelques chats.</div>
      </div>
      <div style={{...label, top: 262 - 9 - W.y}}>INSTRUCTIONS</div>
      <div style={{position: 'absolute', left: 1355 - W.x, top: 281 - W.y, width: 352, height: 57, borderRadius: 8, background: '#1F1C1B', border: '1px solid #2A2725', boxSizing: 'border-box', padding: '11px 14px', fontSize: 11, fontWeight: 600, color: '#77716C', lineHeight: '17px'}}>
        Tu es stratège de contenu YouTube pour Lucien Mallet.<br />Reprends sa voix, son format et son style.
      </div>
      <div style={{...label, top: 367 - 9 - W.y}}>FICHIERS</div>
      <div style={{position: 'absolute', left: 1355 - W.x, top: 386 - W.y, width: 352, height: 2.5, borderRadius: 2, background: '#2A2826'}}>
        <div style={{width: 13, height: 2.5, borderRadius: 2, background: '#6065C8'}} />
      </div>
      <div style={{position: 'absolute', left: 1355 - W.x, top: 400 - 7 - W.y, fontSize: 10, fontWeight: 600, color: '#5F5A57', lineHeight: '14px'}}>1 % de la capacité du projet utilisée</div>
      {FILES.map((f, i) => {
        const x = i === 1 ? 1536 : 1355;
        const y = i === 2 ? 504 : 418;
        return (
          <div key={i} style={{position: 'absolute', left: x - W.x, top: y - W.y, width: 172, height: 77, borderRadius: 7, background: '#181B26', border: '1px solid #2B2F45', boxSizing: 'border-box', padding: '11px 13px'}}>
            <div style={{fontSize: 12.5, fontWeight: 600, color: '#D8D6EC', lineHeight: '16px'}}>{f.name}</div>
            <div style={{fontSize: 9.5, fontWeight: 600, color: '#646884', lineHeight: '14px', marginTop: 3}}>{f.lines} lignes</div>
            <div style={{display: 'inline-block', marginTop: 5, padding: '1px 6px', borderRadius: 3, background: '#2A2E42', fontSize: 8.5, fontWeight: 700, color: '#8A8FB0', letterSpacing: 0.8, lineHeight: '12px'}}>DOCX</div>
          </div>
        );
      })}
      {/* en-tête de la conversation */}
      <div style={{position: 'absolute', left: 225 - W.x, top: 157 - 13 - W.y, fontSize: 19.5, fontWeight: 700, color: '#F2EFEC', lineHeight: '26px'}}>Projet vidéo YouTube</div>
      <div style={{position: 'absolute', left: 225 - W.x, top: 180 - 8 - W.y, fontSize: 12.5, fontWeight: 600, color: '#77716C', lineHeight: '16px'}}>Nouvelle conversation</div>
      <div style={{position: 'absolute', left: 213 - W.x, top: 207 - W.y, width: SIDE_X - 213 - 3, height: 1, background: '#211E1D'}} />
      {/* messages */}
      {FILES.map((f, i) => (cardOp[i] > 0 ? <FileCard key={i} f={f} bottom={cardBottoms[i]} op={cardOp[i]} /> : null))}
      {promptOp > 0 && (
        <div style={{opacity: promptOp}}>
          <div style={{position: 'absolute', right: W.x + W.w - 1252, top: promptBottom - PROMPT_H - W.y, height: PROMPT_H, borderRadius: 12, background: '#211E1C', border: '1px solid #2E2B29', boxSizing: 'border-box', padding: '0 22px', lineHeight: '48px', fontSize: 14.8, fontWeight: 600, color: '#ECE9E6', whiteSpace: 'nowrap'}}>
            Crée le plan YouTube de ma vidéo sur les projets Claude.
          </div>
          <Avatar x={1281 - W.x} y={promptBottom - 25 - W.y} />
        </div>
      )}
      {respOp > 0 && (
        <div style={{opacity: respOp}}>
          <ClaudeMark x={240 - W.x} y={respBottom - RESP_H + 15 - W.y} size={26} />
          <div style={{position: 'absolute', left: 278 - W.x, top: respBottom - RESP_H - W.y, width: 554, height: RESP_H, borderRadius: 10, background: '#1E1B19', boxSizing: 'border-box'}}>
            <div style={{opacity: skel}}>
              {[[0.21, 18], [0.87, 34], [0.62, 50], [0.87, 66], [0.46, 82]].map(([w, y], i) => (
                <div key={i} style={{position: 'absolute', left: 19, top: y - 3, width: 518 * w, height: 5, borderRadius: 3, background: '#34312F'}} />
              ))}
            </div>
            <div style={{position: 'absolute', left: 19, top: 25 - 9, fontSize: 13.3, fontWeight: 700, color: '#ECE9E6', lineHeight: '18px', whiteSpace: 'nowrap'}}>{header.slice(0, nh)}</div>
            {OUTLINE.map(([a, b], i) => (
              <div key={i} style={{position: 'absolute', left: 19, top: 52.5 + i * 26.6 - 9, opacity: itemOp[i], fontSize: 13.1, fontWeight: 600, color: '#DCD8D4', lineHeight: '18px', whiteSpace: 'nowrap'}}>
                <span style={{color: '#6F6A66', fontWeight: 500, display: 'inline-block', width: 27}}>{`0${i + 1}`}</span>
                <span style={{color: '#F2EFEC', fontWeight: 700}}>{a}</span> : {b}
              </div>
            ))}
          </div>
        </div>
      )}
      {/* saisie */}
      <div style={{position: 'absolute', left: 213 - W.x, top: 939 - W.y, width: 1097, height: 63, borderRadius: 12, background: '#211E1C', border: '1px solid #2E2B29', boxSizing: 'border-box'}}>
        <div style={{position: 'absolute', left: 16, top: 0, lineHeight: '62px', fontSize: 15.3, fontWeight: 600, color: '#5F5A57'}}>Comment puis-je t’aider aujourd’hui ?</div>
        <div style={{position: 'absolute', left: 931, top: 0, lineHeight: '62px', fontSize: 12.5, fontWeight: 600, color: '#A09A96', display: 'flex', alignItems: 'center', gap: 3}}>Sonnet 4.6 <Chevron size={13} color="#6F6A66" /></div>
        <Mic x={1029} y={31} h={20} color="#77716C" />
        <div style={{position: 'absolute', left: 1049, top: 15, width: 32, height: 32, borderRadius: 7, background: '#CE5B30', display: 'flex', alignItems: 'center', justifyContent: 'center'}}><ArrowUp size={17} stroke={2.6} /></div>
      </div>
    </MacWindow>
  );
};

const SceneA: React.FC = () => {
  const t = useT();
  return (
    <AbsoluteFill>
      <Bg id="18" />
      <Camera scale={samples(t, ZA)} ox={959} oy={511}><Ui t={t} mode="A" /></Camera>
    </AbsoluteFill>
  );
};

// Occurrence B : même interface, 0,977 fois plus petite, centrée en (966, 534).
const SceneB: React.FC = () => {
  const t = useT();
  const k = 0.977;
  return (
    <AbsoluteFill>
      <Bg id="18" />
      <Camera scale={samples(t, ZB)} ox={957} oy={543}>
        <AbsoluteFill style={{transform: `translate(0px, ${534 - 539.5}px) scale(${k})`, transformOrigin: '966px 539.5px'}}>
          <Ui t={t} mode="B" />
        </AbsoluteFill>
      </Camera>
    </AbsoluteFill>
  );
};

// Bruitages. A : 0, B : 182. Les 5 puces du plan arrivent à moins de 0,12 s d'écart : un seul pop.
const CUES: SfxCue[] = [
  {frame: 0, name: 'whoosh-transition'},
  {frame: 7, name: 'pop'},
  {frame: 67, name: 'pop'},
  {frame: 127, name: 'pop'},
  {frame: 182, name: 'whoosh-transition'},
  {frame: 203, name: 'pop'},
  {frame: 220, name: 'notification'},
  {frame: 251, name: 'pop'},
];

const Comp: React.FC = () => (
  <AbsoluteFill style={{backgroundColor: '#000', fontFamily: FONT}}>
      <SfxTrack cues={CUES} />
    <Bg id="18" />
    <Sequence durationInFrames={A}><SceneA /></Sequence>
    <Sequence from={A + GAP} durationInFrames={B}><SceneB /></Sequence>
  </AbsoluteFill>
);
export default Comp;

// Signaux sonores exportés pour la bibliothèque (cloud/cues_globaux.py).
export const cues = CUES;
