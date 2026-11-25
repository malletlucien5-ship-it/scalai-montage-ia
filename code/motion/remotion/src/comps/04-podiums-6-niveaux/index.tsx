import React from 'react';
import {AbsoluteFill, Audio, Easing, Img, interpolate, Sequence, staticFile, useCurrentFrame} from '../../shared/rt';
import {SfxTrack, SfxCue} from '../../shared/Sfx';
import {INTER} from '../../shared/fonts';
import {DIDOT_L} from '../../shared/localFonts';

// 04 : six podiums 3D (image IA unique, plan large), travelling latéral en code.
// A 14,25-17,88 s : plan large + titre serif. B 23,42-26,86 s : approche du podium 1.
// C à G : passage du niveau k au niveau k+1 (79,81 / 262,53 / 400,80 / 574,91 / 732,90 s).

// Monde = image 5504x3072 ramenée à 1920x1072, posée en (0, 4).
const WORLD = {w: 1920, h: 1072, y: 4};
// Centres des icônes dans le monde (mesurés sur l'image générée).
const ICON = [
  {x: 222, y: 670},
  {x: 508, y: 665},
  {x: 798, y: 550},
  {x: 1090, y: 525},
  {x: 1378, y: 485},
  {x: 1700, y: 420},
];
// Position écran de l'icône du niveau courant, plan posé (relevée sur la référence).
const Q = [
  {x: 972, y: 510},
  {x: 975, y: 660},
  {x: 960, y: 580},
  {x: 960, y: 690},
  {x: 985, y: 690},
  {x: 960, y: 680},
];
const S_CLOSE = 2.13;
const TITLE_LEFT = 655; // bord gauche du titre, plan posé
const TITLE_MID = 193; // milieu des capitales de la ligne 1, plan posé
const TITLE_SIZE = 84;

type Cam = {s: number; wx: number; wy: number; sx: number; sy: number}; // le point monde (wx,wy) va à l'écran (sx,sy)
const toScreen = (c: Cam, x: number, y: number) => ({x: c.sx + (x - c.wx) * c.s, y: c.sy + (y - c.wy) * c.s});
const settled = (k: number): Cam => ({s: S_CLOSE, wx: ICON[k].x, wy: ICON[k].y, sx: Q[k].x, sy: Q[k].y});
// Ancre monde du titre k : là où il se trouve à l'écran quand le plan k est posé.
const titleAnchor = (k: number) => ({
  x: ICON[k].x + (TITLE_LEFT - Q[k].x) / S_CLOSE,
  y: ICON[k].y + (TITLE_MID - Q[k].y) / S_CLOSE,
});

type W = {w: string; at: number};
const TITLES: W[][][] = [
  [[{w: '1.', at: 21}, {w: "L'Amateur", at: 45}]],
  [[{w: '2.', at: 45}, {w: "L'Habitué", at: 66}]],
  [[{w: '3.', at: 21}, {w: "L'Intégrateur", at: 42}]],
  [[{w: '4.', at: 15}, {w: "L'Opérateur", at: 30}]],
  [[{w: '5.', at: 12}, {w: 'Le', at: 24}, {w: 'Bâtisseur', at: 33}]],
  [[{w: '6.', at: 9}, {w: "L'Orchestrateur", at: 30}], [{w: "d'agents", at: 39}]],
];

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

const enter = (f: number, at: number) => {
  const t = interpolate(f, [at, at + 10], [0, 1], {...clamp, easing: Easing.out(Easing.cubic)});
  return {
    opacity: f < at ? 0 : interpolate(t, [0, 1], [0.3, 1]),
    transform: `translateY(${(1 - t) * 20}px)`,
    filter: `blur(${(1 - t) * 4}px)`,
  };
};

// Décor : image nette au centre, floue sur les bords (profondeur de champ).
const World: React.FC<{cam: Cam; dof: number; blur?: number}> = ({cam, dof, blur = 0}) => {
  const tl = toScreen(cam, 0, WORLD.y);
  const style: React.CSSProperties = {
    position: 'absolute',
    left: tl.x,
    top: tl.y,
    width: WORLD.w * cam.s,
    height: WORLD.h * cam.s,
  };
  const src = staticFile('04/podiums.jpg');
  return (
    <AbsoluteFill style={{filter: blur ? `blur(${blur}px)` : undefined}}>

      {dof > 0 ? (
        <>
          <AbsoluteFill style={{filter: `blur(${dof}px)`}}>
            <Img src={src} style={style} />
          </AbsoluteFill>
          <AbsoluteFill
            style={{
              WebkitMaskImage: 'radial-gradient(ellipse 620px 560px at 960px 600px, #000 45%, transparent 100%)',
            }}
          >
            <Img src={src} style={style} />
          </AbsoluteFill>
        </>
      ) : (
        <Img src={src} style={style} />
      )}
      <AbsoluteFill style={{background: 'radial-gradient(ellipse 75% 80% at 50% 50%, transparent 55%, rgba(0,0,0,0.55) 100%)'}} />
    </AbsoluteFill>
  );
};


// Plans rapprochés : décor en calques (fond large, 6 podiums détourés vus en caméra basse).
// Chaque podium est détouré depuis une image de référence où il est au centre (plan posé k),
// d'où sa place dans le monde : même décalage à l'icône que dans ce plan.
const CROP = [
  {x: 620, y: 330, w: 650},
  {x: 680, y: 440, w: 590},
  {x: 700, y: 330, w: 600},
  {x: 680, y: 420, w: 580},
  {x: 660, y: 440, w: 600},
  {x: 620, y: 340, w: 680},
];
const POD_SIZE = [
  [812, 1087],
  [737, 987],
  [750, 1004],
  [725, 970],
  [750, 1004],
  [850, 1138],
];
const BG = {w: 6336, h: 2688};

const Layered: React.FC<{cam: Cam}> = ({cam}) => {
  // Fond : parallaxe lente (environ un quart du déplacement des podiums).
  const p = (cam.wx - ICON[0].x) / (ICON[5].x - ICON[0].x);
  const q = (ICON[0].y - cam.wy) / (ICON[0].y - ICON[5].y);
  const zoom = 1 + (cam.s - S_CLOSE) * 0.25;
  const bh = 1242 * zoom;
  const bw = (bh * BG.w) / BG.h;
  const bgLeft = 960 - bw / 2 + (bw - 1920) * (0.5 - p) - (cam.sx - 960) * 0.25;
  const bgTop = 540 - bh / 2 - 60 + q * 120;
  return (
    <AbsoluteFill>
      <Img
        src={staticFile('04/decor-large.jpg')}
        style={{position: 'absolute', left: bgLeft, top: bgTop, width: bw, height: bh, filter: 'blur(1.5px) brightness(0.72)'}}
      />
      {CROP.map((c, k) => {
        const [iw, ih] = POD_SIZE[k];
        const wx0 = ICON[k].x + (c.x - Q[k].x) / S_CLOSE;
        const wy0 = ICON[k].y + (c.y - Q[k].y) / S_CLOSE;
        const tl = toScreen(cam, wx0, wy0);
        const w = (iw / 1.25 / S_CLOSE) * cam.s;
        const h = (ih / 1.25 / S_CLOSE) * cam.s;
        if (tl.x > 1920 || tl.x + w < 0) return null;
        const cx = tl.x + w / 2;
        const dof = Math.min(7, (Math.abs(cx - 960) / 620) * 4.5);
        return (
          <Img
            key={k}
            src={staticFile(`04/podium-${k + 1}.png`)}
            style={{position: 'absolute', left: tl.x, top: tl.y, width: w, height: h, filter: dof > 0.3 ? `blur(${dof}px)` : undefined}}
          />
        );
      })}
      <AbsoluteFill style={{background: 'radial-gradient(ellipse 75% 80% at 50% 50%, transparent 55%, rgba(0,0,0,0.55) 100%)'}} />
    </AbsoluteFill>
  );
};

const LevelTitle: React.FC<{k: number; cam: Cam; f: number; old: boolean; shown?: boolean}> = ({k, cam, f, old, shown}) => {
  const a = titleAnchor(k);
  const p = toScreen(cam, a.x, a.y);
  return (
    <div
      style={{
        position: 'absolute',
        left: p.x,
        top: p.y - TITLE_SIZE * 0.66,
        fontFamily: INTER,
        fontWeight: 700,
        fontSize: TITLE_SIZE,
        lineHeight: '104px',
        letterSpacing: -1.5,
        color: old ? '#e6e6e6' : '#fff',
        whiteSpace: 'nowrap',
        textShadow: '0 0 10px rgba(255,255,255,0.55), 0 0 26px rgba(255,255,255,0.25)',
        filter: old ? 'blur(5px)' : undefined,
        opacity: old ? 0.9 : 1,
      }}
    >
      {TITLES[k].map((line, i) => (
        <div key={i}>
          {line.map((w, j) => (
            <span key={j} style={{display: 'inline-block', marginRight: 22, ...(shown ? {} : enter(f, w.at))}}>
              {w.w}
            </span>
          ))}
        </div>
      ))}
    </div>
  );
};

// A : plan large, mise au point, titre serif mot à mot.
const SERIF: W[] = [
  {w: '6', at: 1},
  {w: 'niveaux', at: 7},
  {w: "d'usagers", at: 10},
  {w: 'de', at: 13},
  {w: 'Claude', at: 16},
];
const Ouverture: React.FC = () => {
  const f = useCurrentFrame();
  const s = interpolate(f, [0, 6], [0.965, 1], {...clamp, easing: Easing.out(Easing.quad)});
  const blur = interpolate(f, [0, 5], [22, 0], clamp);
  const cam: Cam = {s, wx: 960, wy: 540, sx: 960, sy: 540 - (1 - s) * 400};
  return (
    <AbsoluteFill style={{background: '#0d0c0c'}}>
      <World cam={cam} dof={0} blur={blur} />
      <div
        style={{
          position: 'absolute',
          left: 0,
          right: 0,
          top: 40,
          textAlign: 'center',
          fontFamily: `"Bodoni 72", ${DIDOT_L}, serif`,
          fontStyle: 'italic',
          fontWeight: 400,
          fontSize: 124,
          lineHeight: '170px',
          letterSpacing: -1.5,
          color: '#fff',
          whiteSpace: 'nowrap',
          textShadow: '0 0 12px rgba(255,255,255,0.6), 0 0 32px rgba(255,255,255,0.3)',
        }}
      >
        {SERIF.map((w, i) => (
          <span key={i} style={{display: 'inline-block', marginRight: i < SERIF.length - 1 ? 26 : 0, ...enter(f, w.at)}}>
            {w.w}
          </span>
        ))}
      </div>
    </AbsoluteFill>
  );
};

// B : approche du podium 1, zoom qui accélère, titre « 1. L'Amateur ».
const Approche: React.FC = () => {
  const f = useCurrentFrame();
  const s = interpolate(f, [0, 36, 54, 72, 90, 102], [1.62, 1.62, 1.7, 1.83, 2.1, 2.13], clamp);
  const sx = interpolate(f, [0, 102], [942, 972], clamp);
  const cam: Cam = {s, wx: ICON[0].x, wy: ICON[0].y, sx, sy: 510};
  return (
    <AbsoluteFill style={{background: '#0d0c0c'}}>
      <Layered cam={cam} />
      <LevelTitle k={0} cam={cam} f={f} old={false} />
    </AbsoluteFill>
  );
};

// C à G : travelling du niveau k vers k+1.
const Passage: React.FC<{k: number; pan: number}> = ({k, pan}) => {
  const f = useCurrentFrame();
  const e = interpolate(f, [0, pan], [0, 1], {...clamp, easing: Easing.bezier(0.33, 0, 0.2, 1)});
  const a = settled(k);
  const b = settled(k + 1);
  const cam: Cam = {
    s: S_CLOSE,
    wx: a.wx + (b.wx - a.wx) * e,
    wy: a.wy + (b.wy - a.wy) * e,
    sx: a.sx + (b.sx - a.sx) * e,
    sy: a.sy + (b.sy - a.sy) * e,
  };
  return (
    <AbsoluteFill style={{background: '#0d0c0c'}}>
      <Layered cam={cam} />
      {Array.from({length: k + 1}).map((_, j) => (
        <LevelTitle key={j} k={j} cam={cam} f={f} old={j < k || e > 0.35} shown />
      ))}
      <LevelTitle k={k + 1} cam={cam} f={f} old={false} />
    </AbsoluteFill>
  );
};

const PARTS: {d: number; el: React.ReactNode}[] = [
  {d: 109, el: <Ouverture />},
  {d: 103, el: <Approche />},
  {d: 107, el: <Passage k={0} pan={51} />},
  {d: 94, el: <Passage k={1} pan={42} />},
  {d: 107, el: <Passage k={2} pan={42} />},
  {d: 90, el: <Passage k={3} pan={39} />},
  {d: 87, el: <Passage k={4} pan={39} />},
];
const GAP = 15;
const STARTS = PARTS.map((_, i) => PARTS.slice(0, i).reduce((s, p) => s + p.d + GAP, 0));

// Le clic de référence contient une attaque à 75 ms. Deux images sont retirées
// à la source pour que la première impulsion tombe sur le numéro du niveau.
const LEVEL_CLICKS = [
  STARTS[1] + TITLES[0][0][0].at,
  STARTS[2] + TITLES[1][0][0].at,
  STARTS[3] + TITLES[2][0][0].at,
  STARTS[4] + TITLES[3][0][0].at,
  STARTS[5] + TITLES[4][0][0].at,
  STARTS[6] + TITLES[5][0][0].at,
];

// Les montées commencées dans les GAP étaient coupées par les plages rendues.
// Elles démarrent au premier plan disponible et reprennent à la bonne phase.
const RISERS = [
  {frame: STARTS[1], trimBefore: 6},
  {frame: STARTS[2] + 18, trimBefore: 0},
  {frame: STARTS[3], trimBefore: 6},
  {frame: STARTS[4], trimBefore: 12},
  {frame: STARTS[5], trimBefore: 15},
  {frame: STARTS[6], trimBefore: 18},
];

export const meta = {
  id: '04-podiums-6-niveaux',
  durationInFrames: PARTS.reduce((s, p) => s + p.d, 0) + GAP * (PARTS.length - 1),
  fps: 30,
  // Titre serif, approche du podium 1, puis passages 1>2 à 5>6. from = 0, 124, 242, 364, 473, 595, 700.
  occurrences: [
    [14.25, 17.88],
    [23.42, 26.86],
    [79.81, 83.38],
    [262.53, 265.67],
    [400.8, 404.37],
    [574.91, 577.91],
    [732.9, 735.8],
  ].map((ref, i) => ({ref, from: STARTS[i], durationInFrames: PARTS[i].d, mode: 'plein'})),
};

export default function Podiums() {
  return (
    <AbsoluteFill style={{background: '#0b0b0d'}}>
      {PARTS.map((p, i) => (
        <Sequence key={i} from={STARTS[i]} durationInFrames={p.d}>
          {p.el}
        </Sequence>
      ))}
      {/* Bruitages. Débuts des parties : A 0, B 124, C 242, D 364, E 473, F 595, G 700.
          Chaque niveau : montée 27 images (0,9 s) avant l'impact, impact à l'arrivée du numéro, whoosh au glissement. */}
      <SfxTrack
        cues={cuesExportees}
      />
      {RISERS.map((cue, i) => (
        <Sequence key={`riser-${i}`} from={cue.frame} layout="none">
          <Audio src={staticFile('sfx/montee-chapitre.wav')} trimBefore={cue.trimBefore} volume={0.6} />
        </Sequence>
      ))}
      {LEVEL_CLICKS.map((frame, i) => (
        <Sequence key={`level-click-${i}`} from={frame} layout="none">
          <Audio src={staticFile('04/clic-niveaux.mp3')} trimBefore={2} volume={0.7} />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
}

// Signaux sonores exportés pour la bibliothèque (cloud/cues_globaux.py).
const cuesExportees: SfxCue[] = [
          {frame: 0, name: 'nappe-ecran-titre'},
          {frame: 145, name: 'impact-chapitre'},
          {frame: 242, name: 'whoosh-transition'},
          {frame: 287, name: 'impact-chapitre'},
          {frame: 364, name: 'whoosh-transition'},
          {frame: 385, name: 'impact-chapitre'},
          {frame: 473, name: 'whoosh-transition'},
          {frame: 488, name: 'impact-chapitre'},
          {frame: 595, name: 'whoosh-transition'},
          {frame: 607, name: 'impact-chapitre'},
          {frame: 700, name: 'whoosh-transition'},
          {frame: 709, name: 'impact-chapitre'},
        ];
export const cues = cuesExportees;
