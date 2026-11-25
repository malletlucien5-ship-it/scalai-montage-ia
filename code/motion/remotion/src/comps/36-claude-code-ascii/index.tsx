import React from 'react';
import {AbsoluteFill, useCurrentFrame} from '../../shared/rt';
import {Bg, Camera, MacWindow, keys, FONT} from './kit';
import {SfxTrack, SfxCue} from '../../shared/Sfx';

// Référence : 606,71 à 609,08 s (2,37 s).
export const meta = {
  id: '36-claude-code-ascii', durationInFrames: 71, fps: 30,
  occurrences: [{ref: [606.71, 609.08], from: 0, durationInFrames: 71, mode: 'plein'}],
};

// Police figlet « ANSI Shadow ».
const G: Record<string, string[]> = {
  C: [' ██████╗', '██╔════╝', '██║     ', '██║     ', '╚██████╗', ' ╚═════╝'],
  L: ['██╗     ', '██║     ', '██║     ', '██║     ', '███████╗', '╚══════╝'],
  A: [' █████╗ ', '██╔══██╗', '███████║', '██╔══██║', '██║  ██║', '╚═╝  ╚═╝'],
  U: ['██╗   ██╗', '██║   ██║', '██║   ██║', '██║   ██║', '╚██████╔╝', ' ╚═════╝ '],
  D: ['██████╗ ', '██╔══██╗', '██║  ██║', '██║  ██║', '██████╔╝', '╚═════╝ '],
  E: ['███████╗', '██╔════╝', '█████╗  ', '██╔══╝  ', '███████╗', '╚══════╝'],
  O: [' ██████╗ ', '██╔═══██╗', '██║   ██║', '██║   ██║', '╚██████╔╝', ' ╚═════╝ '],
};
const word = (w: string) => [0, 1, 2, 3, 4, 5].map((r) => w.split('').map((c) => G[c][r]).join(''));
const LINES = [...word('CLAUDE'), ...word('CODE')];

const OR = '#D67756';
const LN = '#D98A70';
const CW = 17.95; // largeur d'une cellule
const CH = 40.2; // hauteur d'une ligne
const X0 = 329; // bord gauche de la 1re cellule (coordonnées finales)
const Y0 = 378; // haut de la 1re ligne
const lineY = (i: number) => Y0 + (i < 6 ? i : i + 0.02) * CH;

const Cell: React.FC<{c: string; x: number; y: number}> = ({c, x, y}) => {
  const cx = x + CW / 2;
  const cy = y + CH / 2;
  const d = 2.9;
  const r = x + CW;
  const b = y + CH;
  let p = '';
  switch (c) {
    case '█':
      return <rect x={x} y={y + 6} width={CW + 0.3} height={28} fill={OR} />;
    case '═':
      p = `M${x} ${cy - d} H${r} M${x} ${cy + d} H${r}`;
      break;
    case '║':
      p = `M${cx - d} ${y} V${b} M${cx + d} ${y} V${b}`;
      break;
    case '╗':
      p = `M${x} ${cy - d} H${cx + d} V${b} M${x} ${cy + d} H${cx - d} V${b}`;
      break;
    case '╔':
      p = `M${r} ${cy - d} H${cx - d} V${b} M${r} ${cy + d} H${cx + d} V${b}`;
      break;
    case '╝':
      p = `M${x} ${cy + d} H${cx + d} V${y} M${x} ${cy - d} H${cx - d} V${y}`;
      break;
    case '╚':
      p = `M${r} ${cy + d} H${cx - d} V${y} M${r} ${cy - d} H${cx + d} V${y}`;
      break;
    default:
      return null;
  }
  return <path d={p} fill="none" stroke={LN} strokeWidth={1.7} />;
};

// Bruitages : entrée de la fenêtre, frappe pendant l'impression du logo (images 0 à 41).
const CUES: SfxCue[] = [
  {frame: 0, name: 'whoosh-transition'},
  {frame: 0, name: 'frappe-clavier', durationInFrames: 41},
];

const Comp: React.FC = () => {
  const f = useCurrentFrame();
  const t = f / 30;
  const s = keys(t, [[0, 0.95], [2.333, 1]]);
  // Impression relevée image par image sur l'original : chaque cellule apparaît à S[ligne] + colonne x K.
  // Les lignes se chevauchent (vague en diagonale), d'où les lettres incomplètes du début.
  const S = [-1.2, 2.5, 6, 8.5, 11.5, 13, 16.5, 20.5, 23, 25.5, 28.5, 31];
  const shown = LINES.map((l, i) => {
    const K = i < 6 ? 0.17 : 0.2;
    let n = 0;
    for (let c = 0; c < l.length; c++) if (f >= S[i] + c * K) n = c + 1;
    return n;
  });
  return (
    <AbsoluteFill style={{backgroundColor: '#000', fontFamily: FONT}}>
      <SfxTrack cues={CUES} />
      <Bg id="36" />
      <Camera scale={s} ox={1000} oy={545}>
        <MacWindow x={288} y={172} w={1419} h={746} r={26} titleH={65} titleBg="#373639" bodyBg="#1E1E1F" title="" dotX={36} dotGap={44.5} dotR={12.5} sep="#2A2A2C" />
        <svg width={1920} height={1080} style={{position: 'absolute', left: 0, top: 0}}>
          {LINES.map((l, i) => {
            const cells = [...l].slice(0, shown[i]);
            // blocs pleins fusionnés par plages pour éviter les coutures
            const runs: [number, number][] = [];
            cells.forEach((c, j) => {
              if (c !== '█') return;
              const last = runs[runs.length - 1];
              if (last && last[1] === j) last[1] = j + 1;
              else runs.push([j, j + 1]);
            });
            return (
              <React.Fragment key={i}>
                {runs.map(([a, b]) => <rect key={`r${a}`} x={X0 + a * CW} y={lineY(i) + 6} width={(b - a) * CW} height={28} fill={OR} />)}
                {cells.map((c, j) => (c === '█' ? null : <Cell key={`${i}-${j}`} c={c} x={X0 + j * CW} y={lineY(i)} />))}
              </React.Fragment>
            );
          })}
        </svg>
      </Camera>
    </AbsoluteFill>
  );
};
export default Comp;

// Signaux sonores exportés pour la bibliothèque (cloud/cues_globaux.py).
export const cues = CUES;
