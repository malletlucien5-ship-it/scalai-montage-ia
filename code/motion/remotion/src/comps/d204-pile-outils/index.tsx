import React from 'react';
import {AbsoluteFill, Sequence, interpolate, useCurrentFrame} from '../../shared/rt';
import {INTER_L} from '../../shared/localFonts';
import {SfxTrack, SfxCue} from '../../shared/Sfx';
import {Face, Tile, TileLook} from './Tiles';

const FPS = 30;
const GAP = 15;

// Écran plein cadre « pile d'outils ». Mesures sur l'original 1920x1080 (réf. 28.76-33.03, 40.31-46.91,
// 57.62-60.29, 328.80-330.76, 747.48-749.45, 986.82-988.79).
const TITLE = 'Comment construire la stack IA parfaite';
const ANNOTATION: [string, string] = ['Un système pour exploiter', "n'importe quel outil IA"];

// Textes personnalisables par placement (props `titre`, `annotation`). Défaut : textes dan2.
type Textes = {titre: string; annotation: [string, string]};
const TextesCtx = React.createContext<Textes>({titre: TITLE, annotation: ANNOTATION});

// Position finale des 4 tuiles (centres, échelle relative à la tuile 1).
const CX = 959.5;
const CY = [370, 554.5, 736, 901];
const SC = [1, 0.97, 0.946, 0.922];

type Occ = {
  ref: [number, number];
  at: number; // début dans la voix coupée (s)
  end: number; // fin (s)
  kind: 'intro' | 'systeme' | 'outil';
  icons?: number; // nombre de tuiles déjà remplacées par une icône à l'ouverture
  add?: number; // tuile qui reçoit son icône + libellé pendant l'occurrence (1..4)
  addAt?: number; // instant (s, voix coupée) de l'arrivée ; défaut = ouverture
  beam: number; // intensité du faisceau de fond
  titleY?: number;
};

const OCC: Occ[] = [
  // « Dans cette vidéo, je vais vous présenter les meilleurs outils d'IA que j'utilise au quotidien, »
  {ref: [28.76, 33.03], at: 23.64, end: 27.28, kind: 'intro', beam: 1},
  // « Et restez bien jusqu'à la fin parce que je vais vous montrer comment construire le système … à la pointe. »
  {ref: [40.31, 46.91], at: 31.88, end: 39.35, kind: 'systeme', beam: 1},
  // « … tchao GPT de retour. Le dernier modèle de chat GPT, Astra, »
  {ref: [57.62, 60.29], at: 49.1, end: 51.61, kind: 'outil', icons: 0, add: 1, beam: 0.5},
  // « C'est là qu'intervient Grogbot. »
  {ref: [328.8, 330.76], at: 355.83, end: 357.67, kind: 'outil', icons: 1, add: 2, beam: 0.5, titleY: 108.5},
  // « Mais la vraie astuce, … les faites enfin travailler ensemble. » (libellé sur « et que vous les faites enfin »)
  {ref: [747.48, 749.45], at: 802.32, end: 807.55, kind: 'outil', icons: 2, add: 3, addAt: 805.1, beam: 0.5, titleY: 108.5},
  // « parce que si vous ne faites pas ça, … tant que vous ne lui avez pas donné tout le contexte nécessaire. »
  {ref: [986.82, 988.79], at: 1056.02, end: 1063.0, kind: 'outil', icons: 3, add: 4, addAt: 1060.7, beam: 0.5, titleY: 108.5},
];

const FACES: Face[] = ['openai', 'grok', 'handoff', 'brain'];
const LABELS = ['ChatGPT Astra', 'Grok Bot', 'Déléguer, pas changer', 'Le cerveau'];

const plan = (() => {
  let from = 0;
  return OCC.map((o) => {
    const dur = Math.round((o.end - o.at) * FPS);
    const p = {o, from, dur};
    from += dur + GAP;
    return p;
  });
})();

// ---------- Mesures image par image de l'entrée (occ. 1), temps relatifs à la coupe réf. 28.76 ----------
const lerpTable = (t: number, ts: number[], vs: number[]) =>
  interpolate(t, ts, vs, {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
// Titre : centre vertical (px).
const TT = [0, 0.07, 0.14, 0.21, 0.27, 0.34, 0.41, 0.47, 0.54, 0.61, 0.67, 0.74, 0.81, 0.87, 0.94, 1.01, 1.08, 1.14, 1.21, 1.28, 1.34, 1.41, 1.48, 1.64];
const TY = [528, 524, 516, 504, 484, 455, 414, 366, 320, 282, 252, 227, 207, 191, 178, 168, 160, 152, 147, 143, 140, 138, 136, 135];
// Pile : haut de la tuile 1 et bas de la tuile 4 (px), opacité.
const ST_T = [0.71, 0.77, 0.84, 0.91, 0.97, 1.04, 1.11, 1.17, 1.24, 1.31, 1.38, 1.44, 1.51, 1.58, 1.64, 1.71, 1.78, 1.84, 1.94, 2.04];
const ST_TOP = [800, 760, 692, 628, 572, 526, 484, 448, 416, 390, 368, 350, 334, 322, 312, 302, 296, 290, 286, 282];
const ST_BOT = [1022, 1020, 1018, 1008, 1000, 994, 990, 988, 986, 985, 984, 983, 982, 982, 982, 982, 982, 982, 982, 982];
const HALF_TOP = 88;
const HALF_BOT = 81;

// Apparition d'un libellé (flou + montée + fondu), mesurée sur 57.62-58.4 et 328.8-329.4.
const labelAnim = (f: number, rise = 84) => {
  if (f < 0) return {o: 0, y: rise, b: 6};
  return {o: 1 - 0.6 * Math.exp(-0.2 * f), y: rise * Math.exp(-0.16 * f), b: 6 * Math.exp(-0.35 * f)};
};

const Background: React.FC<{beam: number; t: number}> = ({beam, t}) => {
  const dx = 35 * t; // le faisceau dérive vers la droite (~35 px/s mesuré sur 28.8-32.5)
  const blob = (x: number, y: number, w: number, h: number, c: string, rot = 0): React.CSSProperties => ({
    position: 'absolute',
    left: x - w / 2,
    top: y - h / 2,
    width: w,
    height: h,
    transform: `rotate(${rot}deg)`,
    background: `radial-gradient(closest-side, ${c} 0%, ${c.replace(/[\d.]+\)$/, '0.45)')} 50%, rgba(0,0,0,0) 100%)`,
  });
  return (
    <AbsoluteFill style={{background: '#000103'}}>
      <AbsoluteFill style={{opacity: beam}}>
        <div style={blob(1120 + dx, 60, 460, 640, 'rgba(8,64,82,1)', 12)} />
        <div style={blob(1030 + dx, 430, 400, 720, 'rgba(0,50,64,1)', 10)} />
        <div style={blob(950 + dx, 780, 380, 560, 'rgba(0,38,56,1)', 12)} />
        <div style={blob(680 + dx * 0.5, 1040, 620, 380, 'rgba(12,44,84,1)', -8)} />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

const coupeTitre = (t: string): string[] => {
  if (t.length * 45 <= 1840) return [t];
  const mots = t.split(' ');
  let best: string[] = [t];
  let ecart = Infinity;
  for (let i = 1; i < mots.length; i++) {
    const a = mots.slice(0, i).join(' ');
    const b = mots.slice(i).join(' ');
    const e = Math.max(a.length, b.length);
    if (e < ecart) {
      ecart = e;
      best = [a, b];
    }
  }
  return best;
};

const Title: React.FC<{y: number; v?: number; sc?: number}> = ({y, v = 0, sc = 1}) => {
  const {titre} = React.useContext(TextesCtx);
  // Taille visuelle de Dan conservée (corps 90 : capitale 65 px, mesurée réf. 31,3). Un titre trop long pour une ligne
  // (≈ 45 px par signe, 1840 px utiles) passe sur deux lignes équilibrées au lieu de rétrécir.
  const lignes = coupeTitre(titre);
  const taille = Math.min(90, (1840 / 45) * 90 / Math.max(...lignes.map((l) => l.length)) );
  // v = vitesse verticale (px/image) : traînée de flou de mouvement comme dans la réf.
  const m = Math.min(12, Math.abs(v) * 0.45);
  const trail = m > 0.5 ? `, 0 ${m}px 2px rgba(255,255,255,0.5), 0 ${-m}px 2px rgba(255,255,255,0.5)` : '';
  return (
  <div
    style={{
      position: 'absolute',
      left: 0,
      width: 1932,
      top: y - 60 * lignes.length,
      height: 120 * lignes.length,
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      lineHeight: lignes.length > 1 ? '100px' : undefined,
      justifyContent: 'center',
      fontFamily: INTER_L,
      fontWeight: 700,
      fontSize: taille,
      letterSpacing: 2,
      color: '#ffffff',
      whiteSpace: 'nowrap',
      transform: `scale(${sc})`,
      textShadow: `0 0 4px rgba(255,255,255,0.55), 0 0 14px rgba(255,255,255,0.45)${trail}`,
    }}
  >
    {lignes.map((l, i) => (
      <div key={i}>{l}</div>
    ))}
  </div>
  );
};

const Label: React.FC<{text: string; cy: number; f: number}> = ({text, cy, f}) => {
  const a = labelAnim(f);
  if (a.o <= 0) return null;
  return (
    <div
      style={{
        position: 'absolute',
        left: 1150,
        top: cy + 5 - 45 + a.y,
        height: 90,
        display: 'flex',
        alignItems: 'center',
        fontFamily: INTER_L,
        fontWeight: 700,
        fontSize: 64,
        letterSpacing: -0.5,
        color: '#ffffff',
        whiteSpace: 'nowrap',
        opacity: a.o,
        filter: a.b > 0.2 ? `blur(${a.b}px)` : undefined,
      }}
    >
      {text}
    </div>
  );
};

// Occurrence 2 : pastille + trait sur la tuile 4, libellé, allumage bleu/violet.
const SYS_DOT = 1.12; // « je vais vous montrer » (33.00)
const SYS_TXT = 1.4; // « montrer » (33.28)

const OccView: React.FC<{o: Occ}> = ({o}) => {
  const {annotation} = React.useContext(TextesCtx);
  const frame = useCurrentFrame();
  const t = frame / FPS;

  // Pile
  let centers = CY;
  let stackOp = 1;
  // Titre : centre 135 px (occ. 1-3), 108.5 px (occ. 4-6) ; léger zoom lent pendant l'occ. 2 (1 -> 1,016).
  let titleY = o.titleY ?? 135;
  let titleV = 0;
  let titleSc = 1;
  if (o.kind === 'systeme') {
    const p = t / ((o.end - o.at) || 1);
    titleY = 135 - 6 * p;
    titleSc = 1 + 0.016 * p;
  }
  if (o.kind === 'intro') {
    titleY = lerpTable(t, TT, TY);
    titleV = titleY - lerpTable(t - 1 / FPS, TT, TY);
    const top = lerpTable(t, ST_T, ST_TOP);
    const bot = lerpTable(t, ST_T, ST_BOT);
    const c1 = top + HALF_TOP;
    const c4 = bot - HALF_BOT;
    const q = (c4 - c1) / (CY[3] - CY[0]);
    centers = CY.map((c) => c4 - (CY[3] - c) * q);
    stackOp = interpolate(t, [0.69, 1.11], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  }

  // Allumage (occ. 2)
  let lit = 0;
  if (o.kind === 'systeme') {
    const ramp = interpolate(t, [SYS_TXT, SYS_TXT + 1.1], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
    lit = ramp * (0.88 + 0.12 * Math.sin((t - SYS_TXT) * 5.2));
  }
  const chrome = o.kind === 'intro' ? 0 : o.kind === 'systeme' ? 0.6 + 0.4 * Math.min(1, lit) : 1;

  const addF = o.add ? Math.round(((o.addAt ?? o.at) - o.at) * FPS) : 0;
  const swapIn = o.addAt ? interpolate(frame, [addF, addF + 5], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}) : 1;

  const tiles = [0, 1, 2, 3].map((i) => {
    const n = i + 1;
    const look: TileLook = {chrome, lit, purple: n === 4};
    let face: Face = 'num';
    let faceIn = 1;
    if (o.kind === 'outil') {
      if (n <= (o.icons ?? 0)) face = FACES[i];
      else if (n === o.add) {
        face = FACES[i];
        faceIn = swapIn;
      }
    }
    const pop = o.addAt && n === o.add ? 1 + 0.05 * Math.sin(Math.PI * Math.min(1, Math.max(0, (frame - addF) / 8))) : 1;
    return <Tile key={n} cx={CX} cy={centers[i]} sc={SC[i] * pop} n={n} face={face} look={look} frame={frame} faceIn={faceIn} />;
  });

  // Libellés
  const labels: React.ReactNode[] = [];
  if (o.kind === 'outil') {
    for (let i = 0; i < 4; i++) {
      const n = i + 1;
      if (n <= (o.icons ?? 0)) labels.push(<Label key={n} text={LABELS[i]} cy={CY[i]} f={999} />);
      else if (n === o.add) labels.push(<Label key={n} text={LABELS[i]} cy={CY[i]} f={frame - addF - 1 - (o.addAt ? 0 : 0)} />);
    }
  }

  let sys: React.ReactNode = null;
  if (o.kind === 'systeme') {
    const fd = frame - Math.round(SYS_DOT * FPS);
    const ft = frame - Math.round(SYS_TXT * FPS);
    if (fd >= 0) {
      const lineW = interpolate(fd, [0, 5], [0, 133], {extrapolateRight: 'clamp', easing: (x) => 1 - Math.pow(1 - x, 3)});
      const dotS = fd < 4 ? 0.6 + 0.1 * fd : interpolate(fd, [4, 6, 9], [1, 1.6, 1], {extrapolateRight: 'clamp'});
      const a = labelAnim(ft, 40);
      const y = CY[3] + 9;
      sys = (
        <>
          <div style={{position: 'absolute', left: 1135, top: y - 1, width: lineW, height: 2.2, background: '#f2f2f2'}} />
          <div
            style={{
              position: 'absolute',
              left: 1128 - 7,
              top: y - 7,
              width: 14,
              height: 14,
              borderRadius: 7,
              border: '2.5px solid #f4f4f4',
              boxSizing: 'border-box',
              background: '#0a0f14',
              transform: `scale(${dotS})`,
            }}
          />
          {ft >= 0 ? (
            <div
              style={{
                position: 'absolute',
                left: 1280,
                top: y - 55 + a.y,
                height: 110,
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'center',
                fontFamily: INTER_L,
                fontWeight: 700,
                fontSize: Math.min(42, (42 * ANNOTATION[0].length) / Math.max(1, annotation[0].length, annotation[1].length)),
                lineHeight: 1.18,
                letterSpacing: -0.3,
                color: '#ffffff',
                whiteSpace: 'nowrap',
                opacity: a.o,
                filter: a.b > 0.2 ? `blur(${a.b}px)` : undefined,
              }}
            >
              <div>{annotation[0]}</div>
              <div>{annotation[1]}</div>
            </div>
          ) : null}
        </>
      );
    }
  }

  return (
    <AbsoluteFill style={{overflow: 'hidden'}}>
      <Background beam={o.beam + (o.kind === 'systeme' ? 0.15 * lit : 0)} t={t} />
      <Title y={titleY} v={titleV} sc={titleSc} />
      {lit > 0.01 ? (
        <AbsoluteFill style={{opacity: lit}}>
          <div style={{position: 'absolute', left: 960 - 330, top: 640 - 520, width: 660, height: 1040, background: 'radial-gradient(closest-side, rgba(28,104,255,0.42), rgba(28,104,255,0.16) 55%, rgba(0,0,0,0) 100%)'}} />
          <div style={{position: 'absolute', left: 960 - 240, top: 905 - 150, width: 480, height: 300, background: 'radial-gradient(closest-side, rgba(120,70,255,0.40), rgba(0,0,0,0) 100%)'}} />
        </AbsoluteFill>
      ) : null}
      <AbsoluteFill style={{opacity: stackOp}}>{tiles}</AbsoluteFill>
      {labels}
      {sys}
    </AbsoluteFill>
  );
};

// Bruitages (SFX-REGLES.md) : whoosh à l'entrée de chaque plein écran ; grave-apparition sur la pile (occ. 1),
// sur le libellé (occ. 2) et sur chaque icône + libellé arrivant en cours d'occurrence ; pop sur la pastille.
const CUES: SfxCue[] = plan.flatMap(({o, from}) => {
  const c: SfxCue[] = [{frame: from, name: 'whoosh-transition'}];
  if (o.kind === 'intro') c.push({frame: from + 22, name: 'grave-apparition'});
  if (o.kind === 'systeme') {
    c.push({frame: from + Math.round(SYS_DOT * FPS), name: 'pop'});
    c.push({frame: from + Math.round(SYS_TXT * FPS), name: 'grave-apparition'});
  }
  if (o.kind === 'outil' && o.addAt) c.push({frame: from + Math.round((o.addAt - o.at) * FPS), name: 'grave-apparition'});
  return c;
});

const PileOutils: React.FC<{showPlate?: boolean; titre?: string; annotation?: [string, string]}> = ({titre = TITLE, annotation = ANNOTATION}) => (
  <TextesCtx.Provider value={{titre, annotation}}>
  <AbsoluteFill style={{backgroundColor: '#0E0E10', overflow: 'hidden'}}>
    {plan.map(({o, from, dur}, i) => (
      <Sequence key={i} from={from} durationInFrames={dur} layout="none">
        <OccView o={o} />
      </Sequence>
    ))}
    <SfxTrack cues={CUES} />
  </AbsoluteFill>
  </TextesCtx.Provider>
);

export const meta = {
  id: 'd204-pile-outils',
  fps: FPS,
  durationInFrames: plan[plan.length - 1].from + plan[plan.length - 1].dur,
  defaultProps: {showPlate: true},
  occurrences: plan.map(({o, from, dur}) => ({ref: o.ref, at: o.at, from, durationInFrames: dur, mode: 'plein' as const})),
};
export default PileOutils;

// Signaux sonores exportés pour la bibliothèque (cloud/cues_globaux.py).
export const cues = CUES;
