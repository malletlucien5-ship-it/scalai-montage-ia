import React from 'react';
import {AbsoluteFill, useCurrentFrame} from '../../shared/rt';
import {SANS, SERIF, ease, Cursor, ScreenBg, IPlus} from './ui';
import {Sidebar, ChatInput, IArrowL, IKebab, IStar, IImage, ILockS, IDoc, ICodeDoc} from './claude';
import {SfxTrack, SfxCue} from '../../shared/Sfx';

// Référence : 151,0 s à 165,0 s (420 images).
export const meta = {id: '17-fichiers-projet', durationInFrames: 420, fps: 30, defaultProps: {showPlate: true},
  occurrences: [
    {ref: [151.1, 155.2], from: 3, durationInFrames: 123, mode: 'plein'},
    {ref: [158.2, 165.0], from: 216, durationInFrames: 204, mode: 'plein'},
  ],
};

// Bruitages calés sur le minutage de l'animation (règles : SFX-REGLES.md).
const SFX: SfxCue[] = [
  {frame: 3, name: 'whoosh-transition'},
  {frame: 30, name: 'clic'},
  {frame: 69, name: 'pop'},
  {frame: 216, name: 'whoosh-transition'},
  {frame: 225, name: 'pop'},
  {frame: 267, name: 'pop'},
  {frame: 303, name: 'pop'},
  {frame: 333, name: 'pop'},
  {frame: 372, name: 'pop'},
  {frame: 408, name: 'pop'},
];

const T = {
  back: 'Tous les projets',
  title: 'Projet 01',
  desc: 'Tu es un assistant marketing. Aide-moi sur le copywriting, les idées de campagne et la stratégie de contenu.',
  created: 'Créé par toi',
  priv: 'Privé',
  share: 'Partager',
  ask: "Comment puis-je t'aider aujourd'hui ?",
  chats: 'Tes chats',
  activity: 'Activité',
  privNote: "Tes chats restent privés jusqu'au partage",
  empty: 'Lance un chat pour organiser tes conversations et réutiliser les connaissances du projet.',
  memory: 'Mémoire',
  memorySub: 'La mémoire du projet apparaîtra ici après quelques chats.',
  only: 'Toi seul',
  instr: 'Instructions',
  instrSub: 'Ajoute des instructions pour adapter les réponses de Claude',
  files: 'Fichiers',
  filesEmpty: ['Ajoute des PDF, des documents ou d’autres textes', 'à consulter dans ce projet.'],
  dropChat: 'Dépose tes fichiers ici pour les ajouter au chat',
  dropKnow: 'Dépose tes fichiers ici pour enrichir le projet',
  capacity: '1 % de la capacité du projet utilisée',
};

type Card = {name: string; lines: string; kind: string};
const MASTER: Card = {name: 'Prompt maitre.docx', lines: '135 lignes', kind: 'DOCX'};
// Retours à la ligne calqués sur l'original (mêmes coupures, mêmes longueurs).
const GRID: Card[] = [
  {name: 'Posts_LinkedIn_\nPerformants\n2.docx', lines: '135 lignes', kind: 'DOCX'},
  {name: 'Creation_Contenu\n_Workflow.md', lines: '60 lignes', kind: 'MD'},
  {name: 'Charte_de_marque.\ndocx', lines: '421 lignes', kind: 'DOCX'},
  {name: 'Prompt\nmaitre.docx', lines: '135 lignes', kind: 'DOCX'},
  {name: 'Export_Contacts\n_HubSpot_T2_202\n6.csv', lines: '', kind: 'CSV'},
];

// Carte de fichier du panneau.
const FileCard: React.FC<{x: number; y: number; w: number; h: number; c: Card; fs: number}> = ({x, y, w, h, c, fs}) => (
  <div style={{position: 'absolute', left: x, top: y, width: w, height: h, borderRadius: 9, background: '#2b2b29', border: '1.5px solid #3a3a37', boxSizing: 'border-box'}}>
    <div style={{position: 'absolute', left: 12, top: 10, right: 8, fontSize: fs, lineHeight: `${fs * 1.45}px`, color: '#e6e4df', whiteSpace: 'pre'}}>
      {c.name}
      {c.lines && <div style={{fontSize: fs * 0.78, color: '#8f8d88', marginTop: 4}}>{c.lines}</div>}
    </div>
    <div style={{position: 'absolute', left: 11, bottom: 10, padding: '2px 5px', borderRadius: 4, border: '1.5px solid #4a4a47', fontSize: fs * 0.9, color: '#c8c6c1', fontWeight: 500}}>{c.kind}</div>
  </div>
);

// Page projet, dans les unités « contenu » ; L fixe les colonnes.
type Layout = {W: number; H: number; sb: number; sbY: number[]; sbB: number[]; mx: number; mw: number; px: number; pw: number};
const LA: Layout = {W: 1484, H: 694, sb: 47, sbY: [22, 84, 124, 163, 202, 241, 281, 370], sbB: [604, 661], mx: 85, mw: 812, px: 952, pw: 500};
const LB: Layout = {W: 1722, H: 806, sb: 47, sbY: [22, 85, 126, 165, 205, 245, 284, 376], sbB: [714, 773], mx: 168, mw: 857, px: 1081, pw: 533};

const Page: React.FC<{L: Layout; drop: number; dropL?: number; filesMode: 'empty' | 'loading' | 'one' | 'grid'; red?: React.ReactNode}> = ({L, drop, dropL = drop, filesMode, red}) => {
  const {mx, mw, px, pw} = L;
  const panelH = filesMode === 'grid' ? 660 : filesMode === 'empty' ? 471 : 490;
  return (
    <div style={{position: 'absolute', inset: 0, fontFamily: SANS}}>
      <Sidebar w={L.sb} h={L.H} ys={L.sbY} bottom={L.sbB} />
      {/* colonne principale */}
      <div style={{position: 'absolute', left: mx, top: 91, display: 'flex', alignItems: 'center', gap: 7, fontSize: 18, color: '#d9d7d2'}}>
        <IArrowL size={17} color="#d9d7d2" />{T.back}
      </div>
      <div style={{position: 'absolute', left: mx, top: 142, fontFamily: SERIF, fontSize: 32, color: '#ecebe6', letterSpacing: -0.3}}>{T.title}</div>
      <div style={{position: 'absolute', left: mx, top: 192, fontSize: 17, color: '#dddbd6', whiteSpace: 'nowrap'}}>{T.desc}</div>
      <div style={{position: 'absolute', left: mx, top: 226, fontSize: 14.5, color: '#9c9a95', display: 'flex', alignItems: 'center', gap: 6}}>
        {T.created} · <ILockS size={14} color="#9c9a95" sw={1.8} />{T.priv}
      </div>
      <IKebab size={22} color="#d9d7d2" style={{position: 'absolute', left: mx + mw - 170, top: 148}} />
      <IStar size={21} color="#d9d7d2" style={{position: 'absolute', left: mx + mw - 131, top: 149}} />
      <div style={{position: 'absolute', left: mx + mw - 96, top: 142, width: 94, height: 35, borderRadius: 7, background: '#3b3b39', color: '#eeede8',
        fontSize: 16.5, fontWeight: 500, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>{T.share}</div>
      <div style={{opacity: 1 - dropL}}>
        <ChatInput x={mx} y={279} w={mw} h={147} placeholder={T.ask} fs={19} caret />
      </div>
      {dropL > 0 && (
        <div style={{position: 'absolute', left: mx - 2, top: 277, width: mw + 4, height: 151, borderRadius: 22, opacity: dropL, background: 'rgb(26,42,64)',
          border: '1.5px dashed rgb(78,114,158)', boxSizing: 'border-box', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 12,
          fontSize: 18.5, color: 'rgb(118,150,192)'}}>
          <IImage size={21} color="rgb(118,150,192)" sw={1.5} />{T.dropChat}
        </div>
      )}
      <div style={{position: 'absolute', left: mx, top: 465, width: 104, height: 36, borderRadius: 9, background: '#2e2e2b', color: '#eeede8', fontSize: 17, fontWeight: 500,
        display: 'flex', alignItems: 'center', justifyContent: 'center'}}>{T.chats}</div>
      <div style={{position: 'absolute', left: mx + 128, top: 472, fontSize: 17, color: '#a3a19c'}}>{T.activity}</div>
      <div style={{position: 'absolute', right: L.W - (mx + mw) + 8, top: 474, fontSize: 15, color: '#a3a19c', display: 'flex', alignItems: 'center', gap: 7}}>
        <ILockS size={15} color="#a3a19c" sw={1.8} />{T.privNote}
      </div>
      <div style={{position: 'absolute', left: mx, top: 523, width: mw, height: 107, borderRadius: 12, border: '1.5px solid #333330', boxSizing: 'border-box',
        display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 16.5, color: '#bcbab5'}}>{T.empty}</div>
      {/* panneau de droite */}
      <div style={{position: 'absolute', left: px, top: 142, width: pw, height: panelH, borderRadius: 16, border: '1.5px solid #2e2e2c', background: '#1c1c1a',
        boxSizing: 'border-box', opacity: 1 - drop}}>
        <div style={{position: 'absolute', left: 26, top: 28, fontSize: 17, color: '#e3e1dc', fontWeight: 500}}>{T.memory}</div>
        <div style={{position: 'absolute', left: 26, top: 58, fontSize: 14, color: '#8a8883'}}>{T.memorySub}</div>
        <div style={{position: 'absolute', right: 26, top: 25, height: 29, padding: '0 9px', borderRadius: 7, border: '1.5px solid #353532', display: 'flex', alignItems: 'center',
          gap: 5, fontSize: 14.5, color: '#b5b3ae'}}><ILockS size={14} color="#b5b3ae" sw={1.8} />{T.only}</div>
        <div style={{position: 'absolute', left: 0, right: 0, top: 96, height: 1.5, background: '#2a2a28'}} />
        <div style={{position: 'absolute', left: 26, top: 125, fontSize: 17, color: '#e3e1dc', fontWeight: 500}}>{T.instr}</div>
        <div style={{position: 'absolute', left: 26, top: 153, fontSize: 14, color: '#8a8883'}}>{T.instrSub}</div>
        <IPlus size={21} color="#d9d7d2" style={{position: 'absolute', right: 24, top: 126}} />
        <div style={{position: 'absolute', left: 0, right: 0, top: 203, height: 1.5, background: '#2a2a28'}} />
        <div style={{position: 'absolute', left: 26, top: 227, fontSize: 17, color: '#e3e1dc', fontWeight: 500}}>{T.files}</div>
        {filesMode === 'loading' ? (
          <div style={{position: 'absolute', right: 27, top: 231, width: 15, height: 15, borderRadius: 8, border: '2px solid #6a6a67', borderTopColor: '#2a2a28'}} />
        ) : (
          <IPlus size={21} color="#d9d7d2" style={{position: 'absolute', right: 24, top: 228}} />
        )}
        {filesMode === 'empty' && (
          <div style={{position: 'absolute', left: 26, right: 26, top: 256, height: 190, borderRadius: 12, background: '#161614'}}>
            <svg width="130" height="66" viewBox="0 0 130 66" style={{position: 'absolute', left: '50%', top: 30, marginLeft: -65}}>
              {[[0, 22, 34, 34], [40, 22, 34, 34], [68, 2, 40, 44]].map(([x, y, w, h], i) => (
                <g key={i}><rect x={x + 2} y={y + 2} width={w} height={h} rx="5" fill="#2a2a28" stroke="#5e5e5a" strokeWidth="1.3" />
                  <path d={`M${x + 8} ${y + 12}h${w - 12}M${x + 8} ${y + 18}h${w - 16}M${x + 8} ${y + 24}h${w - 14}`} stroke="#6d6d69" strokeWidth="1.2" /></g>
              ))}
              <rect x="84" y="46" width="30" height="18" rx="4" fill="none" stroke="#4d4d4a" strokeDasharray="3 2" />
            </svg>
            <div style={{position: 'absolute', left: 0, right: 0, top: 118, textAlign: 'center', fontSize: 15, lineHeight: '21px', color: '#c3c1bc'}}>
              {T.filesEmpty[0]}<br />{T.filesEmpty[1]}
            </div>
          </div>
        )}
        {filesMode !== 'empty' && filesMode !== 'loading' && (
          <>
            <div style={{position: 'absolute', left: 26, right: 26, top: 261, height: 7, borderRadius: 4, background: '#2c2c2a'}}>
              <div style={{width: 8, height: 7, borderRadius: 4, background: '#3c7be0'}} />
            </div>
            <div style={{position: 'absolute', left: 26, top: 282, fontSize: 14.5, color: '#a3a19c'}}>{T.capacity}</div>
          </>
        )}
        {filesMode === 'loading' && (
          <div style={{position: 'absolute', left: 26, top: 318, width: 216, height: 142, borderRadius: 9, border: '1.5px solid #383835', boxSizing: 'border-box'}}>
            <div style={{position: 'absolute', left: 12, top: 14, width: 190, height: 11, borderRadius: 4, background: '#4a4a47'}} />
            <div style={{position: 'absolute', left: 12, top: 33, width: 128, height: 11, borderRadius: 4, background: '#4a4a47'}} />
            <div style={{position: 'absolute', left: 12, top: 108, width: 56, height: 18, borderRadius: 4, background: '#4a4a47'}} />
          </div>
        )}
        {filesMode === 'one' && <FileCard x={26} y={325} w={216} h={142} c={MASTER} fs={15} />}
        {filesMode === 'grid' &&
          GRID.map((c, i) => <FileCard key={i} x={27 + (i % 3) * 164} y={332 + Math.floor(i / 3) * 159} w={150} h={143} c={c} fs={14.5} />)}
      </div>
      {drop > 0 && (
        <div style={{position: 'absolute', left: px - 4, top: 138, width: pw + 8, height: 484, borderRadius: 16, opacity: drop, background: 'rgb(4,41,85)',
          border: '1.5px dashed rgb(70,110,160)', boxSizing: 'border-box'}}>
          <div style={{position: 'absolute', left: 0, right: 0, top: 186, display: 'flex', justifyContent: 'center', gap: 4}}>
            <IDoc size={30} color="rgb(100,138,190)" sw={1.4} /><ICodeDoc size={30} color="rgb(100,138,190)" sw={1.4} />
          </div>
          <div style={{position: 'absolute', left: 0, right: 0, top: 228, textAlign: 'center', fontFamily: SERIF, fontSize: 20.5, color: 'rgb(110,150,205)'}}>{T.dropKnow}</div>
        </div>
      )}
      {red}
    </div>
  );
};

// Cadre rouge de surbrillance (unités contenu).
const RedBox: React.FC<{x: number; y: number; w: number; h: number; o: number}> = ({x, y, w, h, o}) => (
  <div style={{position: 'absolute', left: x, top: y, width: w, height: h, borderRadius: 13, border: '3.5px solid rgb(205,20,28)', opacity: o,
    transform: `scale(${1.03 - 0.03 * o})`, boxSizing: 'border-box'}} />
);

// Icône de fichier glissé (vignette + nom surligné) et badge vert de copie.
const Dragged: React.FC<{x: number; y: number; o: number}> = ({x, y, o}) => (
  <div style={{position: 'absolute', left: x - 30, top: y - 42, opacity: o}}>
    <svg width="34" height="40" viewBox="0 0 34 40" style={{position: 'absolute', left: 13, top: 0}}>
      <path d="M2 2h20l10 10v26H2z" fill="#f4f4f2" stroke="#b9b9b6" strokeWidth="1" />
      <path d="M7 14h18M7 18h18M7 22h14M7 26h18" stroke="#9a9a97" strokeWidth="1" />
    </svg>
    <div style={{position: 'absolute', left: 0, top: 43, padding: '0 3px', background: '#2458d6', borderRadius: 3, fontFamily: SANS, fontSize: 9, color: '#fff', whiteSpace: 'nowrap'}}>Prompt mait…</div>
  </div>
);
const Plus: React.FC<{x: number; y: number}> = ({x, y}) => (
  <div style={{position: 'absolute', left: x + 4, top: y + 28, width: 40, height: 40, borderRadius: 20, background: 'radial-gradient(circle at 40% 35%, #5bd65b, #1f9e2a)',
    boxShadow: '0 2px 5px rgba(0,0,0,0.5)', border: '1.5px solid #e8ffe8', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
    <svg width="24" height="24" viewBox="0 0 24 24"><path d="M12 4v16M4 12h16" stroke="#fff" strokeWidth="4" strokeLinecap="round" /></svg>
  </div>
);

const lerpPath = (f: number, pts: [number, number, number][]) => {
  if (f <= pts[0][0]) return [pts[0][1], pts[0][2]];
  for (let i = 1; i < pts.length; i++) {
    if (f <= pts[i][0]) {
      const p = ease(f, pts[i - 1][0], pts[i][0]);
      return [pts[i - 1][1] + (pts[i][1] - pts[i - 1][1]) * p, pts[i - 1][2] + (pts[i][2] - pts[i - 1][2]) * p];
    }
  }
  const l = pts[pts.length - 1];
  return [l[1], l[2]];
};

const FichiersProjet: React.FC<{showPlate?: boolean}> = ({showPlate = true}) => {
  const f = useCurrentFrame();
  const inA = f >= 3 && f < 126;
  const inB = f >= 216;

  // Écran A : fenêtre 1632x763 centrée (962, 529), poussée caméra lente.
  const sA = 1 + (0.0207 * (f - 9)) / 30;
  const drop = f < 34 ? 0 : f < 69 ? ease(f, 34, 39) : 0;
  const modeA = f < 69 ? 'empty' : f < 87 ? 'loading' : 'one';
  const [cx, cy] = lerpPath(f, [[30, 1720, 930], [36, 1640, 865], [39, 1590, 825], [42, 1555, 780], [46, 1527, 738], [66, 1518, 725], [72, 1540, 745], [100, 1575, 860], [126, 1592, 892]]);

  // Écran B : fenêtre 1722x806 centrée (950, 533).
  const sB = (1760 - 250 * Math.exp(-(f - 216) / 78)) / 1722;
  const cardBox = (i: number) => ({x: 1081 + 27 + (i % 3) * 164 - 6, y: 142 + 332 + Math.floor(i / 3) * 159 - 6, w: 162, h: 155});
  const seq: [number, number, number][] = [[225, 267, 4], [267, 303, 0], [303, 333, 2], [333, 372, 1]];
  const reds: React.ReactNode[] = [];
  seq.forEach(([a, b, i], k) => {
    if (f >= a && f < b) {
      const bx = cardBox(i);
      reds.push(<RedBox key={k} {...bx} o={ease(f, a, a + 3)} />);
    }
  });
  if (f >= 372) reds.push(<RedBox key="p" x={1071} y={358} w={544} h={440} o={ease(f, 372, 375)} />);
  if (f >= 408) reds.push(<RedBox key="m" {...cardBox(3)} o={ease(f, 408, 411)} />);

  return (
    <AbsoluteFill style={{background: showPlate ? '#000' : 'transparent'}}>
      {(inA || inB) && <ScreenBg />}
      {!inA && !inB && showPlate && <AbsoluteFill style={{background: '#0E0E10'}} />}
      {inA && (
        <AbsoluteFill style={{transform: `scale(${sA})`, transformOrigin: '962px 529px'}}>
          <div style={{position: 'absolute', left: 146, top: 148, width: 1632, height: 763, borderRadius: 14, background: '#1e1e1c', overflow: 'hidden',
            boxShadow: '0 0 0 1.5px rgba(205,205,200,0.5), 0 30px 90px rgba(0,0,0,0.6)'}}>
            <div style={{position: 'absolute', left: 0, top: 0, width: LA.W, height: LA.H, transform: 'scale(1.1)', transformOrigin: '0 0'}}>
              <Page L={LA} drop={drop} dropL={f < 34 ? 0 : ease(f, 34, 39)} filesMode={modeA as any} />
            </div>
          </div>
        </AbsoluteFill>
      )}
      {inA && f >= 30 && (
        <>
          {f < 69 && <Dragged x={cx} y={cy} o={ease(f, 30, 33)} />}
          <Cursor x={cx} y={cy} kind="arrow" scale={1.05} />
          <Plus x={cx} y={cy} />
        </>
      )}
      {inB && (
        <AbsoluteFill style={{transform: `scale(${sB})`, transformOrigin: '951px 531px'}}>
          <div style={{position: 'absolute', left: 89, top: 130, width: 1722, height: 806, borderRadius: 14, background: '#1e1e1c', overflow: 'hidden',
            boxShadow: '0 0 0 1.5px rgba(205,205,200,0.5), 0 30px 90px rgba(0,0,0,0.6)'}}>
            <Page L={LB} drop={0} filesMode="grid" red={<>{reds}</>} />
          </div>
        </AbsoluteFill>
      )}
      {inB && <Cursor x={1122 + 0 * f} y={866} kind="arrow" scale={1.2} />}
      <SfxTrack cues={SFX} />
    </AbsoluteFill>
  );
};
export default FichiersProjet;

// Signaux sonores exportés pour la bibliothèque (cloud/cues_globaux.py).
export const cues = SFX;
