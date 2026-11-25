import React from 'react';
import {AbsoluteFill, useCurrentFrame, interpolate, Easing} from '../../shared/rt';
import {loadFont as serifBold} from '@remotion/google-fonts/SourceSerif4';
import {SANS, SERIF, ease, Cursor, ScreenBg, ClaudeStar} from './ui';
import {SfxTrack, SfxCue} from '../../shared/Sfx';

// Occurrence 1 : 325,0 s à 332,0 s (210 images, la fenêtre entre à 325,5 s). Pause 0,5 s.
// Occurrence 2 : 492,0 s à 497,0 s (150 images).
export const meta = {id: '26-cowork-orange', durationInFrames: 375, fps: 30,
  occurrences: [
    {ref: [325.5, 332.0], from: 15, durationInFrames: 195, mode: 'plein'},
    {ref: [492.0, 497.0], from: 225, durationInFrames: 150, mode: 'plein'},
  ],
};

// Bruitages calés sur le minutage de l'animation (règles : SFX-REGLES.md).
const SFX: SfxCue[] = [
  {frame: 15, name: 'whoosh-transition'},
  {frame: 33, name: 'whoosh-transition'},
  {frame: 45, name: 'clic'},
  {frame: 62, name: 'whoosh-transition'},
  {frame: 84, name: 'pop'},
  {frame: 94, name: 'pop'},
  {frame: 100, name: 'frappe-clavier', durationInFrames: 21},
  {frame: 134, name: 'notification'},
  {frame: 153, name: 'clic'},
  {frame: 171, name: 'clic'},
  {frame: 188, name: 'clic'},
  {frame: 225, name: 'whoosh-transition'},
  {frame: 243, name: 'clic'},
  {frame: 249, name: 'pop'},
  {frame: 260, name: 'grave-apparition'},
  {frame: 272, name: 'whoosh-transition'},
  {frame: 291, name: 'clic'},
  {frame: 300, name: 'frappe-clavier', durationInFrames: 14},
  {frame: 322, name: 'clic'},
  {frame: 327, name: 'whoosh-transition'},
  {frame: 336, name: 'clic'},
  {frame: 348, name: 'pop'},
  {frame: 362, name: 'clic'},
];

// Titre : police propriétaire (Anthropic Serif). Banc d'essai de 8 polices : Source Serif 4 en 700 est la plus proche (x-height, graisse, largeur).
const SERIF_B = serifBold('normal', {weights: ['600', '700']}).fontFamily;
const ORANGE = '#d87756';
const CREAM = '#f4f2ed';

// Images clés avec courbe douce.
const kf = (f: number, pts: [number, number][], e = Easing.bezier(0.45, 0, 0.25, 1)) =>
  interpolate(f, pts.map((p) => p[0]), pts.map((p) => p[1]), {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: e});
const lin = (f: number, pts: [number, number][]) => kf(f, pts, Easing.linear);

const Tx: React.FC<{x: number; y: number; s: number; c: string; w?: number; ff?: string; ls?: number; children: React.ReactNode; style?: React.CSSProperties}> = ({x, y, s, c, w = 400, ff = SANS, ls = 0, children, style}) => (
  <div style={{position: 'absolute', left: x, top: y - s * 0.62, fontSize: s, color: c, fontWeight: w, fontFamily: ff, letterSpacing: ls, whiteSpace: 'nowrap', lineHeight: 1.2, ...style}}>{children}</div>
);

// Icône « artefacts » : étoile, cercle, losange, carré.
const ArtIcon: React.FC<{size: number; color?: string; sw?: number; swap?: number}> = ({size, color = '#1a1a1a', sw = 2, swap = 0}) => (
  <svg width={size} height={size} viewBox="0 0 48 48" fill="none" stroke={color} strokeWidth={sw} strokeLinejoin="round">
    <g transform={swap ? 'translate(48 0) scale(-1 1)' : undefined}>
      <path d="M13 5l2.6 4.5 5.1-.5-2.2 4.6 3.1 4.1-5.1.6L13 23l-2.5-4.7-5.1-.6 3.1-4.1-2.2-4.6 5.1.5z" />
      <circle cx="34.5" cy="13.5" r="8" />
      <path d="M13 26l8.5 8.5L13 43l-8.5-8.5z" />
      <rect x="27" y="27" width="15" height="15" rx="1" />
    </g>
  </svg>
);

// ---------------- Occurrence 1 ----------------
const LightClaude: React.FC<{hl: number}> = ({hl}) => (
  <div style={{position: 'absolute', left: 0, top: 0, width: 876, height: 547, background: '#faf9f5', borderRadius: 7, overflow: 'hidden', fontFamily: SANS}}>
    <svg width="14" height="14" viewBox="0 0 24 24" style={{position: 'absolute', left: 11, top: 13}} fill="none" stroke="#555" strokeWidth="1.8"><rect x="3.5" y="4.5" width="17" height="15" rx="2" /><path d="M9 4.5v15" /></svg>
    <div style={{position: 'absolute', left: 9, top: 45, width: 18, height: 18, borderRadius: 9, background: '#c6613f', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
      <svg width="12" height="12" viewBox="0 0 24 24" stroke="#fff" strokeWidth="3" strokeLinecap="round"><path d="M12 5v14M5 12h14" /></svg>
    </div>
    <svg width="14" height="14" viewBox="0 0 24 24" style={{position: 'absolute', left: 11, top: 75}} fill="none" stroke="#333" strokeWidth="1.8"><path d="M4 9h16l-1.2 10.2a1.5 1.5 0 0 1-1.5 1.3H6.7a1.5 1.5 0 0 1-1.5-1.3zM6 6h12M8 3.5h8" /></svg>
    <svg width="14" height="14" viewBox="0 0 24 24" style={{position: 'absolute', left: 11, top: 99}} fill="none" stroke="#333" strokeWidth="1.8"><path d="M9.5 16.5a6.5 6.5 0 1 1 5.6-3.2l.9 3.2-3.2-.9a6.5 6.5 0 0 1-3.3.9z" /></svg>
    {hl > 0 && <div style={{position: 'absolute', left: 6, top: 117, width: 21, height: 21, borderRadius: 4, background: `rgba(0,0,0,${0.08 * hl})`}} />}
    <div style={{position: 'absolute', left: 11, top: 121}}><ArtIcon size={14} color="#333" sw={3} /></div>
    <div style={{position: 'absolute', left: 9, top: 517, width: 18, height: 18, borderRadius: 9, background: '#e2e0da'}} />
    <div style={{position: 'absolute', left: 0, right: 0, top: 150, display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 8}}>
      <ClaudeStar size={22} /><span style={{fontFamily: SERIF, fontSize: 27, color: '#29261b', fontWeight: 400}}>Te revoilà, Nicole !</span>
    </div>
    <div style={{position: 'absolute', left: 236, top: 208, width: 404, height: 66, borderRadius: 10, background: '#fff', boxShadow: '0 1px 5px rgba(0,0,0,0.08)', border: '1px solid #eceae4'}}>
      <Tx x={9} y={14} s={9.5} c="#77746c">Comment puis-je t’aider aujourd’hui ?</Tx>
      <Tx x={13} y={48} s={11} c="#555">+</Tx><Tx x={36} y={48} s={10} c="#555">⚟</Tx>
      <Tx x={58} y={48} s={8.5} c="#3d3a33">⌕ Recherche</Tx>
      <Tx x={287} y={48} s={8.5} c="#3d3a33" ff={SERIF}>Claude Sonnet 4 ⌄</Tx>
      <div style={{position: 'absolute', left: 377, top: 38, width: 19, height: 19, borderRadius: 4, background: '#f3c9bd'}} />
    </div>
    {[['✎ Écrire', 249, 292], ['⎔ Créer', 312, 297], ['</> Code', 386, 309]].map(([t, x, y]: any, i) => (
      <div key={i} style={{position: 'absolute', left: x, top: y - 10, padding: '3px 8px', borderRadius: 5, border: '1px solid #ebe8e0', fontSize: 9, color: '#3d3a33', background: '#fff'}}>{t}</div>
    ))}
  </div>
);

const RowNames = ['GROSSE', 'CAISSE', 'CHARLEY', 'CHARLEY O.', 'CLAP'];
const BASE: number[][] = [[0, 1, 3, 4, 6, 7, 9, 10, 12], [4, 12], [0, 2, 4, 6, 8, 10, 12, 14], [14], []];
// Boîte à rythmes, en pixels écran de 331,5 s (carte 868 x 672).
const Rhythm: React.FC<{f: number}> = ({f}) => {
  const clap: number[] = [];
  if (f >= 153) clap.push(4);
  if (f >= 171) clap.push(12);
  const playing = f >= 188;
  const step = playing ? Math.floor((f - 188) / 4.1) % 16 : -1;
  const chips: [string, number][] = [['Cloche 808', 92], ['Glitch', 62], ['Jazz fusion', 96], ['Afrobeat', 78], ['Lo-fi', 56], ['Rock de stade', 112], ['Ambient', 76]];
  let cx = 126;
  return (
    <div style={{position: 'absolute', left: 0, top: 0, width: 868, height: 672, borderRadius: 10, background: '#fff', boxShadow: '0 2px 14px rgba(0,0,0,0.08)', fontFamily: SANS, color: '#141414'}}>
      <Tx x={32} y={47} s={24} c="#141414" w={400} ls={-0.8}>BOÎTE À RYTHMES</Tx>
      <Tx x={32} y={73} s={12} c="#8a8a8a" w={500} ls={1.6}>PROPULSÉE PAR L’IA • MODÈLE 002</Tx>
      <div style={{position: 'absolute', left: 827, top: 52, width: 9, height: 9, borderRadius: 5, background: '#f06a1d', opacity: playing && step % 2 === 0 ? 1 : 0.9}} />
      <div style={{position: 'absolute', left: 32, top: 115, width: 699, height: 36, borderRadius: 6, border: '1px solid #e5e5e5'}}>
        <Tx x={14} y={18} s={13} c="#6f6f6f">Décris ton beat (ex. : « techno minimale », « batterie trap », « funk vintage »)</Tx>
      </div>
      <div style={{position: 'absolute', left: 741, top: 114, width: 94, height: 38, borderRadius: 6, background: '#16161a', color: '#fff', fontSize: 13.5, fontWeight: 600, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>Générer</div>
      <Tx x={32} y={179} s={11.5} c="#8a8a8a" w={500} ls={1.4}>ESSAIE :</Tx>
      {chips.map(([t, w], i) => {
        const x = cx; cx += w + 10;
        return <div key={i} style={{position: 'absolute', left: x, top: 164, width: w, height: 30, borderRadius: 5, background: '#f2f2f2', fontSize: 12.5, fontWeight: 500, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>{t}</div>;
      })}
      <div style={{position: 'absolute', left: 32, top: 209, width: 804, height: 1, background: '#eee'}} />
      {[[playing ? '⏸ Pause' : '▶ Lecture', 33, 95], ['▢ Stop', 138, 86], ['⌫ Effacer', 235, 94]].map(([t, x, w]: any, i) => (
        <div key={i} style={{position: 'absolute', left: x, top: 236, width: w, height: 38, borderRadius: 6, border: '1px solid #e8e8e8', fontSize: 13.5, fontWeight: 500, display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 1px 2px rgba(0,0,0,0.05)'}}>{t}</div>
      ))}
      <Tx x={350} y={256} s={12} c="#6f6f6f" ls={1.4}>TEMPO</Tx>
      <div style={{position: 'absolute', left: 410, top: 254, width: 124, height: 3, borderRadius: 2, background: '#e3e3e3'}}><div style={{width: 53, height: 3, background: '#f06a1d'}} /></div>
      <div style={{position: 'absolute', left: 457, top: 249, width: 13, height: 13, borderRadius: 7, background: '#f06a1d'}} />
      <Tx x={558} y={256} s={12} c="#141414" ff="monospace">110 BPM</Tx>
      <div style={{position: 'absolute', left: 32, top: 308, width: 804, height: 272, borderRadius: 8, background: '#f5f5f5'}}>
        {RowNames.map((n, r) => (
          <div key={r}>
            <Tx x={25} y={44 + r * 46} s={12} c="#5a5a5a" ls={1}>{n}</Tx>
            {Array.from({length: 16}, (_, c) => {
              const on = (r === 4 ? clap : BASE[r]).includes(c);
              const cur = c === step;
              const justOn = r === 4 && ((c === 4 && f >= 153 && f < 158) || (c === 12 && f >= 171 && f < 176));
              return (
                <div key={c} style={{position: 'absolute', left: 115 + c * 41.8, top: 26 + r * 46, width: 36, height: 36, borderRadius: 6,
                  background: on ? '#f06a1d' : cur ? '#fbfaf5' : '#fff', boxShadow: on ? 'none' : '0 0 0 1px #ececec', transform: cur || justOn ? 'scale(1.08)' : undefined,
                  filter: cur && on ? 'brightness(1.08)' : undefined}} />
              );
            })}
          </div>
        ))}
      </div>
      {['TECHNO', 'HOUSE', 'TRAP', 'BREAKBEAT', 'MINIMAL'].map((t, i) => (
        <div key={i} style={{position: 'absolute', left: 32 + [0, 91, 173, 245, 358][i], top: 603, width: [82, 74, 62, 104, 84][i], height: 32, borderRadius: 5, border: '1px solid #e8e8e8', fontSize: 12.5, fontWeight: 600, letterSpacing: 0.8, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>{t}</div>
      ))}
    </div>
  );
};

const Occ1: React.FC<{f: number}> = ({f}) => {
  if (f < 15) return null;
  // Largeur du cadre à l'écran (base 1171 x 658).
  const W = lin(f, [[15, 1168], [21, 1171], [48, 1187], [66, 1240], [84, 1304], [111, 1372], [150, 1410], [195, 1450], [210, 1462]]);
  const s = W / 1171;
  const cream = ease(f, 134, 139);
  const frameBg = `rgb(${216 + (244 - 216) * cream},${119 + (242 - 119) * cream},${86 + (237 - 86) * cream})`;
  // Écran Claude clair : zoom sur la barre latérale puis sortie à droite.
  const zin = ease(f, 15, 21, 0.92, 1);
  const z = kf(f, [[33, 1], [39, 2.37]]);
  const ox = kf(f, [[33, 148], [39, 492], [62, 492], [69, 1250]]);
  const oy = kf(f, [[33, 55], [39, 56]]);
  const showClaude = f < 70;
  // Tuile d'icône qui s'envole au centre.
  const tileOn = f >= 62 && f < 100;
  const tx = kf(f, [[62, 535], [69, 586]]);
  const ty = kf(f, [[62, 362], [69, 328]]);
  const tsz = kf(f, [[62, 34], [69, 175], [78, 212]], Easing.out(Easing.cubic));
  const rot = kf(f, [[80, 0], [84, -8], [88, 3], [91, 0]]);
  // Morph tuile vers champ de saisie (93 à 99), puis saisie.
  const m = ease(f, 93, 100);
  const bw = tsz + (700 - tsz) * m; const bh = tsz + (175 - tsz) * m;
  const text = 'Crée une boîte à rythmes interactive pour que je compose des beats inédits !';
  const n = Math.floor(interpolate(f, [100, 121], [0, text.length], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}));
  // Passage à la boîte à rythmes.
  const rm = ease(f, 131, 138);
  // curseur (écran)
  const cursorPts: [number, number, number][] = [
    [39, 960, 670], [45, 915, 585], [60, 908, 575],
    [150, 900, 760], [153, 860, 739], [160, 1000, 745], [166, 1125, 740], [171, 1193, 739], [177, 800, 600], [183, 655, 505], [188, 612, 462], [210, 628, 470],
  ];
  const cp = (fr: number) => {
    let a = cursorPts[0], b = cursorPts[0];
    for (let i = 0; i < cursorPts.length; i++) { if (cursorPts[i][0] <= fr) a = cursorPts[i]; }
    b = cursorPts.find((p) => p[0] > fr) ?? a;
    if (a === b || (a[0] <= 60 && b[0] >= 150)) return [a[1], a[2]];
    const p = ease(fr, a[0], b[0]);
    return [a[1] + (b[1] - a[1]) * p, a[2] + (b[2] - a[2]) * p];
  };
  const [cx, cy] = cp(f);
  const cursorOn = (f >= 39 && f < 63) || f >= 146;
  return (
    <>
      <div style={{position: 'absolute', left: 960 - 585.5, top: 540 - 329, width: 1171, height: 658, transform: `scale(${s})`, transformOrigin: 'center', borderRadius: 48,
        background: frameBg, overflow: 'hidden', boxShadow: '0 0 0 1.2px rgba(235,230,225,0.85), 0 30px 90px rgba(0,0,0,0.55)'}}>
        {showClaude && (
          <div style={{position: 'absolute', left: ox, top: oy, transform: `scale(${z * zin})`, transformOrigin: f < 33 ? '438px 273px' : '0 0'}}>
            <LightClaude hl={ease(f, 44, 47)} />
          </div>
        )}
        {tileOn && (
          <div style={{position: 'absolute', left: tx - bw / 2, top: ty - bh / 2, width: bw, height: bh, borderRadius: 20 + 8 * m, background: m > 0 ? `rgb(${244 + 11 * m},${242 + 13 * m},${237 + 18 * m})` : '#f4f2ec',
            transform: `rotate(${rot}deg)`, boxShadow: '0 4px 14px rgba(0,0,0,0.12)', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
            <div style={{opacity: 1 - m}}><ArtIcon size={tsz * 0.62} sw={2.2} swap={f >= 88 ? 1 : 0} /></div>
          </div>
        )}
        {f >= 100 && f < 139 && (
          <div style={{position: 'absolute', left: kf(f, [[131, 235.5], [138, 29]]), top: kf(f, [[131, 239.5], [138, 32.6]]), width: kf(f, [[131, 700], [138, 1113]]), height: kf(f, [[131, 175], [138, 594]]),
            borderRadius: kf(f, [[131, 28], [138, 10]]), background: rm > 0 ? '#f7f7f6' : '#fff', boxShadow: '0 4px 14px rgba(0,0,0,0.12)', overflow: 'hidden'}}>
            <div style={{position: 'absolute', left: 48, top: 48, width: 620, fontSize: 32, lineHeight: '39px', color: '#141414', fontFamily: SANS, opacity: 1 - rm}}>{text.slice(0, n)}</div>
            {rm > 0 && <div style={{position: 'absolute', left: 209 - 30 * (1 - rm), top: 27, transform: `scale(${1 / 1.238})`, transformOrigin: '0 0', opacity: rm}}><Rhythm f={f} /></div>}
          </div>
        )}
        {f >= 139 && (
          <div style={{position: 'absolute', left: 29, top: 33, width: 1113, height: 593, borderRadius: 10, background: '#f7f7f6', boxShadow: '0 0 0 1px #ebe9e4'}}>
            <div style={{position: 'absolute', left: 207, top: 24, transform: `scale(${1 / 1.238})`, transformOrigin: '0 0'}}><Rhythm f={f} /></div>
          </div>
        )}
      </div>
      {cursorOn && <Cursor x={cx} y={cy} kind={f < 150 ? 'hand' : f >= 183 && f < 190 ? 'hand' : 'arrow'} scale={f < 63 ? 1.25 : 0.85} />}
    </>
  );
};

// ---------------- Occurrence 2 ----------------
// Éclair de Cowork, relevé sur 492,85 s (boîte 100 x 100).
const BOLT = 'M99 0L18 43L42 66L0 100L81 65L58 43Z';
const BOLT_PTS: [number, number][] = [[70, 24], [40, 43], [64, 62], [29, 77]];
const Bolt: React.FC<{size: number; round?: boolean}> = ({size, round}) => (
  <svg width={size} height={size} viewBox="0 0 100 100" style={{overflow: 'visible'}}>
    <path d={BOLT} fill="#d8704e" stroke={round ? '#d8704e' : 'none'} strokeWidth={round ? 8 : 0} strokeLinejoin="round" />
    <path d={'M' + BOLT_PTS.map((p) => p.join(' ')).join('L')} stroke="#fbf8f5" strokeWidth="2.6" fill="none" strokeLinecap="round" strokeLinejoin="round" />
    {BOLT_PTS.map(([x, y], i) => <circle key={i} cx={x} cy={y} r="3.6" fill="#fbf8f5" />)}
  </svg>
);
// Morphing du logo image par image, relevé sur 492,75 s à 493,3 s (dessin irrégulier façon image par image).
// Chaque étape : chemin dans une boîte 100 x 100, taille affichée en px, rotation.
const DOT = '#fbf8f5';
const MorphStage: React.FC<{f: number}> = ({f: f0}) => {
  const f = f0 + 0.7;
  const C = '#d6704f';
  let size = 88, body: React.ReactNode = null;
  if (f < 24.5) {
    size = 22;
    body = <><circle cx="50" cy="50" r="42" fill={C} /><circle cx="50" cy="50" r="18" fill={DOT} /></>;
  } else if (f < 27.5) {
    size = 88 + (f - 24.5) * 4;
    body = <><path d="M30 12L66 9 91 34 90 66 64 90 32 91 9 64 10 33Z" fill={C} stroke={C} strokeWidth="14" strokeLinejoin="round" /><circle cx="50" cy="50" r="17" fill={DOT} /></>;
  } else if (f < 28.5) {
    size = 160;
    body = <g transform="rotate(38 50 50)"><path d="M18 30C22 12 48 10 60 20 72 10 94 18 90 42 88 60 94 80 70 88 50 94 26 90 14 70 6 54 14 44 18 30Z" fill={C} />
      <circle cx="38" cy="42" r="8" fill={DOT} /><circle cx="58" cy="56" r="8" fill={DOT} /><path d="M38 42L58 56" stroke={DOT} strokeWidth="7" /></g>;
  } else if (f < 30.5) {
    size = 240;
    body = <g transform="rotate(40 50 50)"><path d="M10 38C8 26 18 20 30 21L72 22C86 22 94 30 92 44L90 62C88 74 80 80 68 79L28 78C14 78 8 70 10 58Z" fill={C} />
      <circle cx="30" cy="50" r="6" fill={DOT} /><circle cx="70" cy="50" r="6" fill={DOT} /><path d="M30 50H70" stroke={DOT} strokeWidth="3.4" /></g>;
  } else if (f < 31.5) {
    size = 268;
    body = <><path d="M40 8C54 2 76 0 84 4 92 10 86 24 78 30L96 58C100 66 92 74 84 78L30 98C18 102 8 96 10 84 12 76 22 72 30 68L4 44C0 34 8 26 18 22Z" fill={C} />
      <path d="M30 70L60 64 38 42 64 26" stroke={DOT} strokeWidth="4" fill="none" strokeLinejoin="round" />{[[30, 70], [60, 64], [38, 42], [64, 26]].map(([x, y], i) => <circle key={i} cx={x} cy={y} r="5.5" fill={DOT} />)}</>;
  } else if (f < 32.5) {
    size = 330;
    return <div style={{width: size, height: size, marginLeft: -size / 2, marginTop: -size / 2}}><Bolt size={size} round /></div>;
  } else {
    size = 400 + (f - 32.5) * 6;
    return <div style={{width: size, height: size, marginLeft: -size / 2, marginTop: -size / 2}}><Bolt size={size} /></div>;
  }
  return <div style={{width: size, height: size, marginLeft: -size / 2, marginTop: -size / 2}}><svg width={size} height={size} viewBox="0 0 100 100">{body}</svg></div>;
};

const CardIcon: React.FC<{k: number}> = ({k}) => (
  <svg width="56" height="56" viewBox="0 0 56 56" fill="none" stroke="#9c9890" strokeWidth="1.3">
    {k === 4 ? <path d="M3 14a3 3 0 0 1 3-3h15l4 4h25a3 3 0 0 1 3 3v26a3 3 0 0 1-3 3H6a3 3 0 0 1-3-3z" fill="#fff" /> : k === 2 ? (
      <><rect x="2" y="8" width="64" height="40" rx="3" fill="#fff" /><path d="M2 16h64" /><path d="M42 30l2 16 4-5 6 7" /></>
    ) : k === 5 ? (
      <><rect x="12" y="10" width="36" height="22" rx="5" fill="#fff" /><rect x="2" y="26" width="34" height="20" rx="5" fill="#fff" /><path d="M20 20h20M8 36h20" strokeDasharray="3 2" /></>
    ) : (
      <><rect x="0" y="0" width="56" height="56" rx="6" fill="#fff" />
        {k === 0 && <path d="M6 26h44v22H6zM6 37h44M28 26v22M8 10h12M24 10h10M8 16h30" />}
        {k === 1 && <path d="M12 40l10-10 8 6 14-14M12 16v28h32" />}
        {k === 3 && <path d="M14 34a14 14 0 0 1 28 0zM10 40h36M28 12v5M14 20l3 3M42 20l-3 3" />}
      </>
    )}
  </svg>
);
const CARDS = ['Créer un fichier', 'Analyser des données', 'Créer un prototype', 'Préparer ma journée', 'Ranger des fichiers', 'Envoyer un message'];
const PROMPT = 'Résume mes réunions de la semaine et trouve les actions à mener. Où est-ce que je peux gagner en efficacité ?';
const TITLE = ['On', 'raye', 'une', 'tâche', 'de', 'ta', 'liste'];

const Finder: React.FC<{sel: boolean}> = ({sel}) => {
  const side: [string, number, boolean?][] = [['Favoris', 26, true], ['Récents', 58], ['Bureau', 92], ['Documents', 126], ['Téléchargements', 160], ['Emplacements', 200, true], ['Macintosh HD', 234], ['iCloud Drive', 268], ['Réseau', 302], ['Tags', 340, true]];
  const folders = ['Projets', 'Analyse concurrentielle', 'Transcriptions de réunions', 'Planning T4', 'Contrats', 'Dépenses'];
  return (
    <div style={{position: 'absolute', left: 0, top: 0, width: 966, height: 600, borderRadius: 12, background: '#fff', overflow: 'hidden', boxShadow: '0 20px 60px rgba(0,0,0,0.35), 0 0 0 1px rgba(0,0,0,0.12)', fontFamily: SANS}}>
      <div style={{position: 'absolute', left: 0, top: 0, width: 244, height: 600, background: '#e9e7e4'}} />
      {side.map(([t, y, h], i) => (
        <div key={i}>
          {t === 'Documents' && <div style={{position: 'absolute', left: 10, top: y - 13, width: 224, height: 26, borderRadius: 6, background: '#d6d4d1'}} />}
          <Tx x={h ? 20 : 48} y={y} s={h ? 11 : 14} c={h ? '#a3a19c' : '#2b2b2b'} w={h ? 600 : 400}>{t}</Tx>
          {!h && <div style={{position: 'absolute', left: 26, top: y - 7, width: 14, height: 14, borderRadius: 3, border: '1.6px solid #2f7cf6'}} />}
        </div>
      ))}
      <Tx x={272} y={36} s={16} c="#b5b5b5">‹ &nbsp;›</Tx>
      <div style={{position: 'absolute', left: 344, top: 25, width: 40, height: 22, borderRadius: 5, border: '1px solid #ddd'}} />
      <div style={{position: 'absolute', left: 446, top: 25, width: 292, height: 22, borderRadius: 5, border: '1px solid #ddd', fontSize: 13, color: '#2b2b2b', display: 'flex', alignItems: 'center', paddingLeft: 26}}>
        <div style={{position: 'absolute', left: 8, top: 6, width: 12, height: 9, borderRadius: 2, background: '#56a8f5'}} />Documents
        <div style={{position: 'absolute', right: 3, top: 3, width: 16, height: 16, borderRadius: 4, background: '#2f7cf6'}} />
      </div>
      <div style={{position: 'absolute', left: 780, top: 25, width: 162, height: 22, borderRadius: 5, border: '1px solid #ddd', fontSize: 12, color: '#bbb', paddingLeft: 24, lineHeight: '22px'}}>Rechercher</div>
      {folders.map((t, i) => {
        const x = [366, 594, 820][i % 3]; const y = [192, 392][Math.floor(i / 3)];
        const s = sel && i === 2;
        return (
          <div key={i}>
            <svg width="124" height="100" viewBox="0 0 124 100" style={{position: 'absolute', left: x - 62, top: y - 50}}>
              <path d="M2 14a6 6 0 0 1 6-6h34l8 8h66a6 6 0 0 1 6 6v68a6 6 0 0 1-6 6H8a6 6 0 0 1-6-6z" fill={s ? '#4a9df0' : '#67b4f7'} />
              <path d="M2 30a6 6 0 0 1 6-6h108a6 6 0 0 1 6 6v60a6 6 0 0 1-6 6H8a6 6 0 0 1-6-6z" fill={s ? '#6bb6f7' : '#8fcbfb'} />
            </svg>
            <div style={{position: 'absolute', left: x - 90, top: y + 60, width: 180, textAlign: 'center'}}>
              <span style={{fontSize: 13, color: s ? '#fff' : '#2b2b2b', background: s ? '#2f7cf6' : 'transparent', padding: '1px 5px', borderRadius: 4, whiteSpace: 'nowrap'}}>{t}</span>
            </div>
          </div>
        );
      })}
      <div style={{position: 'absolute', left: 750, top: 551, width: 80, height: 26, borderRadius: 6, background: '#f0f0f0', fontSize: 13, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#2b2b2b'}}>Annuler</div>
      <div style={{position: 'absolute', left: 848, top: 551, width: 96, height: 26, borderRadius: 6, background: '#1a7dff', fontSize: 13, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff'}}>Ouvrir</div>
    </div>
  );
};

const Occ2: React.FC<{f: number}> = ({f}) => {
  const W = 1375 + 20 * (f / 30 - 0.1);
  const s = W / 1375;
  // toggle Chat / Cowork
  const toggleOn = f < 24;
  const tw = kf(f, [[0, 380], [3, 676]]);
  const sel = ease(f, 18, 22);
  // logo
  const logoSz = f < 35.5 ? 140 : kf(f, [[35.5, 140], [45, 130], [50, 70]]);
  const logoY = f < 35.5 ? 392 : kf(f, [[35.5, 290], [45, 268], [50, 127.6], [72, 127.6], [77, 5]]);
  const logoRot = 0;
  const titleS = kf(f, [[45, 64], [50, 43]]);
  const titleY = kf(f, [[45, 405], [50, 203.6], [72, 203.6], [77, 80]]);
  const headO = 1 - ease(f, 72, 77);
  const gridO = ease(f, 47, 53);
  const up = kf(f, [[72, 0], [78, -124.6]]);
  const inputO = ease(f, 73, 79);
  const typed = PROMPT.slice(0, Math.floor(interpolate(f, [75, 89], [0, PROMPT.length], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'})));
  const clicked = f >= 66;
  const hover = f >= 49 && f < 57 ? 5 : f >= 57 && f < 60 ? 4 : f >= 62 ? 0 : -1;
  const folderO = ease(f, 102, 106) * (1 - ease(f, 113, 116));
  const chipLabel = f >= 123 ? 'Transcriptions de réunions' : 'Travailler dans un dossier';
  // caméra de zoom
  const K = kf(f, [[114, 1], [118, 2.507]]);
  const Ax = kf(f, [[114, 0], [118, -35.3], [129, -35.3], [135, -2161.7]]);
  const Ay = kf(f, [[114, 0], [118, -1033], [129, -1033], [135, -1040]]);
  // curseur (écran)
  const pts: [number, number, number][] = [
    [0, 1045, 585], [3, 1010, 625], [6, 870, 665], [9, 865, 665], [12, 1145, 635], [15, 1245, 580], [24, 1245, 575],
    [48, 1540, 825], [51, 1415, 675], [55, 1400, 670], [57, 1060, 690], [60, 945, 680], [63, 745, 565], [66, 740, 555], [72, 740, 520], [75, 740, 430],
    [90, 730, 505], [93, 620, 725], [96, 580, 755], [102, 720, 760], [105, 1235, 595], [108, 1320, 500], [111, 1325, 480], [114, 1300, 500],
    [118, 1390, 670], [123, 1200, 670], [127, 1200, 690], [129, 1275, 540], [132, 1060, 650], [135, 1030, 625], [150, 1100, 640],
  ];
  let a = pts[0], b = pts[0];
  pts.forEach((p) => { if (p[0] <= f) a = p; });
  b = pts.find((p) => p[0] > f) ?? a;
  const pp = a === b ? 0 : ease(f, a[0], b[0]);
  const cx = a[1] + (b[1] - a[1]) * pp, cy = a[2] + (b[2] - a[2]) * pp;
  const hand = (f >= 93 && f < 100) || (f >= 107 && f < 113) || f >= 135;
  const cScale = f >= 116 ? 2.6 : 1.1;
  const cursorOn = !(f >= 24 && f < 48) && !(f >= 116 && f < 118);

  return (
    <>
      <div style={{position: 'absolute', left: 960 - 687.5, top: 540 - 386, width: 1375, height: 772, transform: `scale(${s})`, transformOrigin: 'center', borderRadius: 30,
        background: '#fbf8f5', overflow: 'hidden', boxShadow: '0 0 0 1.2px rgba(235,230,225,0.8), 0 30px 90px rgba(0,0,0,0.55)', fontFamily: SANS}}>
        <div style={{position: 'absolute', left: 0, top: 0, width: 1375, height: 772, transformOrigin: '0 0', transform: `translate(${Ax}px, ${Ay}px) scale(${K})`}}>
          {f >= 36 && (
            <div style={{position: 'absolute', inset: -400, opacity: 0.55 * ease(f, 36, 44),
              backgroundImage: 'linear-gradient(#ece7e1 1px, transparent 1px), linear-gradient(90deg, #ece7e1 1px, transparent 1px)', backgroundSize: '58px 58px', backgroundPosition: '14px 20px'}} />
          )}
          {toggleOn && (
            <div style={{position: 'absolute', left: 687.5 - tw / 2, top: 330, width: tw, height: 112, borderRadius: 18, background: '#ebe9e4', boxShadow: '0 10px 26px rgba(0,0,0,0.13)', overflow: 'hidden'}}>
              <div style={{position: 'absolute', left: 4 + sel * (tw / 2 - 4), top: 4, width: tw / 2 - 4, height: 104, borderRadius: 15, background: '#fff', boxShadow: '0 1px 3px rgba(0,0,0,0.12)'}} />
              <Tx x={tw / 4} y={57} s={44} c={sel > 0.5 ? '#9b988f' : '#1b1b1b'} style={{transform: 'translateX(-50%)'}}>Chat</Tx>
              <Tx x={tw * 0.75} y={57} s={44} c={sel > 0.5 ? '#1b1b1b' : '#9b988f'} style={{transform: 'translateX(-50%)'}}>Cowork</Tx>
            </div>
          )}
          {f >= 24 && f < 78 && (
            <div style={{position: 'absolute', left: 687.5 - logoSz / 2, top: logoY - logoSz / 2 + (f >= 72 ? up : 0), width: logoSz, height: logoSz, transform: `rotate(${logoRot}deg)`, opacity: headO}}>
              {f < 35.5 ? <div style={{position: 'absolute', left: logoSz / 2, top: logoSz / 2}}><MorphStage f={f} /></div> : <Bolt size={logoSz} />}
            </div>
          )}
          {f >= 35 && f < 78 && (
            <div style={{position: 'absolute', left: 0, width: 1375, top: titleY - titleS * 0.62, display: 'flex', justifyContent: 'center', gap: titleS * 0.24, opacity: headO,
              fontFamily: SERIF_B, fontWeight: 700, fontSize: titleS, letterSpacing: -titleS * 0.035, color: '#141413', lineHeight: 1.2}}>
              {TITLE.map((w, i) => {
                const p = ease(f, 35 + i * 0.5, 39 + i * 0.5, 0, 1, Easing.out(Easing.back(1.6)));
                return <span key={i} style={{display: 'inline-block', opacity: ease(f, 35 + i * 0.5, 37 + i * 0.5), transform: `translateY(${(1 - p) * 18}px) rotate(${(1 - p) * (i % 2 ? 4 : -4)}deg)`}}>{w}</span>;
              })}
            </div>
          )}
          {f >= 47 && (
            <div style={{position: 'absolute', left: 0, top: up, width: 1375, height: 772}}>
              <div style={{position: 'absolute', left: 144, top: 283.6 + 12 * (1 - gridO), width: 1086, height: 271, borderRadius: 22, background: '#f8f5f1', border: '1px solid #ece8e2',
                boxShadow: '0 8px 30px rgba(0,0,0,0.06)', opacity: gridO}}>
                {CARDS.map((t, i) => {
                  const x = [29.6, 380.6, 730][i % 3]; const y = [30.4, 151.4][Math.floor(i / 3)];
                  const active = (clicked && i === 0) || hover === i;
                  return (
                    <div key={i} style={{position: 'absolute', left: x, top: y, width: 326.5, height: 90, borderRadius: 10, background: active ? '#ebe8e2' : '#fbf9f6', border: '1.3px solid #d9d5ce'}}>
                      <div style={{position: 'absolute', left: 31, top: 16}}><CardIcon k={i} /></div>
                      <Tx x={112} y={45} s={21.5} c="#2b2a28">{t}</Tx>
                    </div>
                  );
                })}
              </div>
              {f >= 73 && (
                <div style={{position: 'absolute', left: 144, top: 556.4 + 10 * (1 - inputO), width: 1086, height: 180, borderRadius: 26, background: '#fff', border: '1px solid #e8e4de',
                  boxShadow: '0 8px 30px rgba(0,0,0,0.07)', opacity: inputO}}>
                  <div style={{position: 'absolute', left: 25, top: 18, width: 1030, fontSize: 23.5, lineHeight: '36px', color: '#1b1b1b'}}>{typed}</div>
                  <div style={{position: 'absolute', left: 16, top: 112, display: 'flex', alignItems: 'center', gap: 22}}>
                  <div style={{height: 43, padding: '0 14px 0 12px', borderRadius: 8, border: '1.2px solid #d9d5ce', display: 'flex', alignItems: 'center', gap: 9,
                    fontSize: 18, fontWeight: f >= 123 ? 600 : 500, color: '#1b1b1b', background: '#fff'}}>
                    <svg width="18" height="16" viewBox="0 0 24 20" fill="none" stroke="#1b1b1b" strokeWidth="1.6"><path d="M1 3a2 2 0 0 1 2-2h6l2 2h10a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2z" /></svg>
                    {chipLabel}{f >= 123 && <span style={{fontSize: 14, marginLeft: 6}}>⌄</span>}
                  </div>
                  <span style={{fontSize: 30, color: '#3b3b3b', fontWeight: 300}}>+</span>
                  </div>
                  <div style={{position: 'absolute', left: 909, top: 106.9, width: 159, height: 55, borderRadius: 9, background: '#c9623f', color: '#fff', fontSize: 21, fontWeight: 600,
                    display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 9}}>C’est parti <span style={{fontSize: 22}}>→</span></div>
                </div>
              )}
            </div>
          )}
        </div>
        {folderO > 0 && (
          <>
            <div style={{position: 'absolute', inset: 0, background: `rgba(110,108,104,${0.55 * folderO})`}} />
            <div style={{position: 'absolute', left: 227, top: 100.5, transform: `scale(${(1 / 1.051) * (0.97 + 0.03 * folderO)})`, transformOrigin: '0 0', opacity: folderO}}>
              <Finder sel={f >= 111} />
            </div>
          </>
        )}
      </div>
      {cursorOn && <Cursor x={cx} y={cy} kind={hand ? 'hand' : 'arrow'} scale={cScale} />}
    </>
  );
};

const CoworkOrange: React.FC = () => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill style={{background: '#000'}}>
      <ScreenBg />
      {f < 210 ? <Occ1 f={f} /> : f >= 225 ? <Occ2 f={f - 225} /> : null}
      <SfxTrack cues={SFX} />
    </AbsoluteFill>
  );
};
export default CoworkOrange;

// Signaux sonores exportés pour la bibliothèque (cloud/cues_globaux.py).
export const cues = SFX;
