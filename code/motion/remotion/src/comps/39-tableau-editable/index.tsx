import React from 'react';
import {AbsoluteFill, useCurrentFrame} from '../../shared/rt';
import {SANS, SERIF, ease, Cursor, ScreenBg} from './ui';
import {SfxTrack, SfxCue} from '../../shared/Sfx';

// Référence : 638,0 s à 643,0 s (150 images).
export const meta = {id: '39-tableau-editable', durationInFrames: 150, fps: 30,
  occurrences: [{ref: [638.0, 643.0], from: 0, durationInFrames: 150, mode: 'plein'}],
};

// Bruitages calés sur le minutage de l'animation (règles : SFX-REGLES.md).
const SFX: SfxCue[] = [
  {frame: 0, name: 'whoosh-transition'},
  {frame: 14, name: 'clic'},
  {frame: 54, name: 'clic'},
  {frame: 90, name: 'clic'},
  {frame: 120, name: 'clic'},
];

const Tx: React.FC<{x: number; y: number; s: number; c: string; w?: number; ff?: string; children: React.ReactNode; style?: React.CSSProperties}> = ({x, y, s, c, w = 400, ff = SANS, children, style}) => (
  <div style={{position: 'absolute', left: x, top: y - s * 0.62, fontSize: s, color: c, fontWeight: w, fontFamily: ff, whiteSpace: 'nowrap', lineHeight: 1.2, ...style}}>{children}</div>
);
const Chev: React.FC<{x: number; y: number; c?: string}> = ({x, y, c = '#d9d7d2'}) => (
  <svg width="11" height="11" viewBox="0 0 24 24" style={{position: 'absolute', left: x, top: y - 5.5}} fill="none" stroke={c} strokeWidth="3.4" strokeLinecap="round" strokeLinejoin="round"><path d="M6 9l6 6 6-6" /></svg>
);

type Row = [string, string, string, string, string, string];
const ROWS: Row[] = [
  ['Mia Chen', 'Gagné', 'Enterprise', '84', 'Nord', '100'], ['James Oka', 'Négociation', 'Pro Plan', '32', 'Europe', '70'],
  ['Sofia Reyes', 'Proposition', 'Starter Pack', '85', 'LATAM', '50'], ['Liam Park', 'Gagné', 'Enterprise', '120', 'APAC', '100'],
  ['Mia Chen', 'Perdu', 'Pro Plan', '170', 'Nord', '0'], ['Dev Anand', 'Qualifié', 'API Add-on', '94', 'Moyen-Orient', '40'],
  ['James Oka', 'Prospection', 'Starter Pack', '42', 'Europe', '20'], ['Sofia Reyes', 'Gagné', 'API Add-on', '22', 'LATAM', '100'],
  ['Liam Park', 'Proposition', 'Pro Plan', '28', 'APAC', '60'], ['Dev Anand', 'Négociation', 'Enterprise', '66', 'Moyen-Orient', '70'],
];
const OPTS = ['Tous les statuts', 'Gagné', 'Perdu', 'Négociation', 'Proposition', 'Prospection', 'Qualifié'];
const STATS: Record<number, string[]> = {0: ['420 k$', '226 k$', '7', '27 %'], 1: ['226 k$', '226 k$', '0', '100 %'], 2: ['17 k$', '0 k$', '0', '0 %']};

const Cell: React.FC<{x: number; y: number; w: number; t: string; sel?: boolean; date?: boolean}> = ({x, y, w, t, sel, date}) => (
  <div style={{position: 'absolute', left: x, top: y - 20, width: w, height: 40, borderRadius: 5, background: '#393937', border: '1px solid #454542', overflow: 'hidden', boxSizing: 'border-box'}}>
    <Tx x={14} y={20} s={17.5} c="#f0eee9" style={{width: sel ? w - 34 : w - 14, overflow: 'hidden', textOverflow: 'clip'}}>{date ? '20' : t}</Tx>
    {sel && <Chev x={w - 17} y={21} />}
    {date && <svg width="15" height="15" viewBox="0 0 24 24" style={{position: 'absolute', left: 30, top: 12}} fill="none" stroke="#f0eee9" strokeWidth="2.4"><rect x="4" y="5" width="16" height="15" rx="2" /><path d="M4 10h16M8 3v4M16 3v4" /></svg>}
  </div>
);

const Sheet: React.FC<{filter: number; focus: boolean}> = ({filter, focus}) => {
  const rows = filter === 0 ? ROWS : filter === 1 ? [ROWS[0], ROWS[3], ROWS[7]] : [ROWS[4]];
  const st = STATS[filter];
  const bottom = 377 + rows.length * 56.5 + 16;
  const label = OPTS[filter];
  const txt: React.CSSProperties = {fontFamily: SERIF, fontSize: 18.5, lineHeight: '27px', color: '#e2e0da'};
  return (
    <div style={{position: 'absolute', inset: 0, fontFamily: SANS}}>
      {['Pipeline total', 'Gagnés', 'Deals ouverts', 'Taux de réussite'].map((a, i) => (
        <div key={i} style={{position: 'absolute', left: 242 + i * 203, top: 40, width: 191, height: 68, borderRadius: 5, background: '#252523'}}>
          <Tx x={15} y={20} s={13} c="#c9c7c2">{a}</Tx>
          <Tx x={15} y={45} s={21} c="#f5f4f0" w={600}>{st[i]}</Tx>
        </div>
      ))}
      <Tx x={1010} y={52} s={15} c="#bdbbb6">···</Tx>
      <div style={{position: 'absolute', left: 242, top: 136, width: 579, height: 40, borderRadius: 5, background: '#383836', border: '1px solid #444441', boxSizing: 'border-box'}}>
        <Tx x={14} y={20} s={17} c="#8e8c87">Rechercher…</Tx>
      </div>
      <div style={{position: 'absolute', left: 242, top: 185, width: 579, height: 40, borderRadius: 5, background: '#383836', boxSizing: 'border-box',
        border: focus ? '2px solid #3b73d9' : '1px solid #444441', boxShadow: focus ? '0 0 0 1px rgba(59,115,217,0.35)' : undefined}}>
        <Tx x={17} y={20} s={17.5} c="#f0eee9">{label}</Tx><Chev x={560} y={19} />
      </div>
      <div style={{position: 'absolute', left: 242, top: 234, width: 579, height: 40, borderRadius: 5, background: '#383836', border: '1px solid #444441', boxSizing: 'border-box'}}>
        <Tx x={17} y={21} s={17.5} c="#f0eee9">Tous les commerciaux</Tx><Chev x={560} y={19} />
      </div>
      <div style={{position: 'absolute', left: 242, top: 285, height: 40, padding: '0 14px', borderRadius: 5, border: '1px solid #4a4a47', display: 'flex', alignItems: 'center', gap: 7, fontSize: 16, color: '#f0eee9', fontWeight: 500}}>⤓ Exporter en CSV</div>
      <div style={{position: 'absolute', left: 419, top: 285, height: 40, padding: '0 14px', borderRadius: 5, border: '1px solid #4a4a47', display: 'flex', alignItems: 'center', gap: 7, fontSize: 16, color: '#f0eee9', fontWeight: 500}}>＋ Ajouter une ligne</div>
      <div style={{position: 'absolute', left: 242, top: 339, width: 800, height: bottom - 339, borderRadius: 6, border: '1px solid #353533', overflow: 'hidden'}}>
        {[['#', 14], ['Commercial', 45], ['Statut', 189], ['Produit', 306], ['Valeur', 451], ['Région', 540], ['Clôture', 634], ['Prob.', 723]].map(([t, x]: any, i) => (
          <Tx key={i} x={x} y={19} s={13} c="#c9c7c2" w={600}>{t}</Tx>
        ))}
        <div style={{position: 'absolute', left: 0, top: 37, width: 800, height: 1, background: '#353533'}} />
        {rows.map((r, i) => {
          const y = 66 + i * 56.5;
          return (
            <div key={i}>
              <Tx x={14} y={y} s={11} c="#bdbbb6">{i + 1}</Tx>
              <Cell x={45} y={y} w={122} t={r[0]} />
              <Cell x={189} y={y} w={94} t={r[1]} sel />
              <Cell x={306} y={y} w={122} t={r[2]} />
              <Cell x={451} y={y} w={66} t={r[3]} />
              <Cell x={540} y={y} w={72} t={r[4]} sel />
              <Cell x={634} y={y} w={66} t="" date />
              <Cell x={723} y={y} w={90} t={r[5]} />
              {i < rows.length - 1 && <div style={{position: 'absolute', left: 0, top: y + 28, width: 800, height: 1, background: '#2e2e2c'}} />}
            </div>
          );
        })}
        <div style={{position: 'absolute', left: 4, top: bottom - 339 - 12, width: 631, height: 7, borderRadius: 4, background: '#5a5a57'}} />
      </div>
      <div style={{position: 'absolute', left: 251, top: bottom + 18, width: 770, ...txt}}>
        {/* Coupures de ligne calquées sur l'original (2 lignes, 2 lignes, 2 lignes, puis 1 ligne par puce, la dernière sur 2). */}
        <div style={{whiteSpace: 'nowrap'}}>Voici ton tableau de ventes ! Chaque cellule se modifie : clique sur un champ pour la changer.<br />Voici ce qu’il contient :</div>
        <div style={{marginTop: 13, whiteSpace: 'nowrap'}}><b>Colonnes :</b> commercial, statut, produit, valeur, région, date de clôture prévue, probabilité de gain<br />en %, et notes.</div>
        <div style={{marginTop: 13}}><b>Fonctionnalités :</b></div>
        <ul style={{margin: '13px 0 0 0', paddingLeft: 36, whiteSpace: 'nowrap'}}>
          {[<>Clique sur une cellule pour la modifier (menus pour le statut et la région, calendrier pour la<br />date)</>, 'Ajoute des lignes avec le bouton « + Ajouter une ligne »',
            'Supprime une ligne avec le bouton ×', 'Filtre par statut ou par commercial, et cherche dans tous les champs', 'Trie chaque colonne en cliquant sur son en-tête',
            'Exporte la vue actuelle en CSV', <>Statistiques en direct (pipeline total, gagnés, deals ouverts, taux de réussite) mises à jour<br />à chaque modification</>].map((t, i) => (
            <li key={i} style={{marginBottom: 5}}>{t}</li>
          ))}
        </ul>
      </div>
    </div>
  );
};

// Liste déroulante native macOS.
const Menu: React.FC<{checked: number; hl: number; o: number}> = ({checked, hl, o}) => (
  <div style={{position: 'absolute', left: 234, top: 188 - checked * 28.9, width: 577, height: 211, borderRadius: 6, background: 'rgba(218,216,213,0.97)', boxShadow: '0 8px 24px rgba(0,0,0,0.45)',
    opacity: o, fontFamily: SANS, padding: '4px 5px', boxSizing: 'border-box'}}>
    {OPTS.map((t, i) => (
      <div key={i} style={{position: 'relative', height: 28.9, borderRadius: 4, background: i === hl ? '#1c63d8' : 'transparent', color: i === hl ? '#fff' : '#2b2b2b', fontSize: 16.5, lineHeight: '28.9px', paddingLeft: 19}}>
        {i === checked && <span style={{position: 'absolute', left: 5, fontSize: 13}}>✓</span>}{t}
      </div>
    ))}
  </div>
);

const pts: [number, number, number][] = [[0, 1210, 375], [3, 1170, 360], [6, 1135, 335], [9, 1125, 330], [12, 1117, 318], [30, 1100, 330], [36, 1075, 340], [54, 1070, 345], [60, 1065, 348], [81, 1068, 345], [87, 1070, 328], [96, 1066, 330], [102, 1065, 340], [120, 1063, 345], [150, 1060, 345]];

const TableauEditable: React.FC = () => {
  const f = useCurrentFrame();
  const t = 638 + f / 30;
  const W = 1254 + 13.9 * (t - 638.6);
  const s = W / 1274;
  const inP = ease(f, 0, 3);
  const blurP = ease(f, 0, 8);
  const filter = f < 54 ? 0 : f < 120 ? 1 : 2;
  const menu1 = f >= 15 && f < 57;
  const menu2 = f >= 90 && f < 123;
  const hl = menu1 ? (f < 33 ? 0 : 1) : f < 99 ? 1 : 2;
  const mo = menu1 ? 1 - ease(f, 54, 57) : menu2 ? ease(f, 90, 92) * (1 - ease(f, 120, 123)) : 0;
  let a = pts[0], b = pts[0];
  pts.forEach((p) => { if (p[0] <= f) a = p; });
  b = pts.find((p) => p[0] > f) ?? a;
  const pp = a === b ? 0 : ease(f, a[0], b[0]);
  const cx = a[1] + (b[1] - a[1]) * pp, cy = a[2] + (b[2] - a[2]) * pp;
  const hand = (f >= 6 && f < 56) || (f >= 84 && f < 122);
  return (
    <AbsoluteFill style={{background: '#000'}}>
      <ScreenBg />
      <div style={{position: 'absolute', left: 976 - 637, top: 538.5 - 453.5, width: 1274, height: 907, transform: `scale(${s * (0.985 + 0.015 * inP)})`, transformOrigin: 'center',
        borderRadius: 34, background: '#1f1f1d', overflow: 'hidden', opacity: inP, filter: blurP < 1 ? `blur(${(1 - blurP) * 10}px)` : undefined,
        boxShadow: '0 0 0 1.5px rgba(205,205,200,0.55), 0 30px 90px rgba(0,0,0,0.6)'}}>
        <Sheet filter={filter} focus={f >= 6} />
        {mo > 0 && <Menu checked={menu1 ? 0 : 1} hl={hl} o={mo} />}
      </div>
      <Cursor x={cx} y={cy} kind={hand ? 'hand' : 'arrow'} scale={1.25} opacity={inP} />
      <SfxTrack cues={SFX} />
    </AbsoluteFill>
  );
};
export default TableauEditable;

// Signaux sonores exportés pour la bibliothèque (cloud/cues_globaux.py).
export const cues = SFX;
