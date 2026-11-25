import React from 'react';
import {INTER_L} from '../../shared/localFonts';
import {Ico} from '../d242-chatgpt-sombre/icones';

// Application Grok (bots) en thème sombre, telle que filmée par Dan (réf. 484,8-493 s et 587,2-591,8 s).
// Coordonnées : écran 1920x1080 de la réf. 484,9 / 490,2 s (fenêtre x 49, haut 48, caméra fixe).
export const TXT = '#ececec';
export const GRIS = '#9a9a9a';

export const ligne = (l: number, cy: number, h: number, extra?: React.CSSProperties): React.CSSProperties => ({
  position: 'absolute', left: l, top: cy - h / 2, height: h, display: 'flex', alignItems: 'center', whiteSpace: 'nowrap', ...extra,
});

// Avatar « goutte » des bots Grok : forme ronde un peu irrégulière, deux yeux en haut à droite.
export const Blob: React.FC<{d: number; c: string; forme?: 'rond' | 'triangle' | 'nuage' | 'pilule'}> = ({d, c, forme = 'rond'}) => {
  const path =
    forme === 'triangle'
      ? 'M50 8 C56 8 60 14 63 20 L92 78 C96 88 90 94 80 94 L20 94 C10 94 4 88 8 78 L37 20 C40 14 44 8 50 8 Z'
      : forme === 'nuage'
        ? 'M20 80 C6 80 4 62 14 56 C10 40 24 28 36 34 C40 18 62 16 68 30 C82 26 96 40 88 54 C98 62 94 82 78 82 Z'
        : forme === 'pilule'
          ? 'M28 30 L72 30 C88 30 96 40 96 52 C96 64 88 74 72 74 L28 74 C12 74 4 64 4 52 C4 40 12 30 28 30 Z'
          : 'M50 6 C76 6 94 24 94 50 C94 76 76 94 50 94 C24 94 6 76 6 50 C6 24 24 6 50 6 Z';
  return (
    <svg width={d} height={d} viewBox="0 0 100 100" style={{display: 'block'}}>
      <path d={path} fill={c} />
      <rect x="46" y={forme === 'pilule' ? 40 : 30} width="5.5" height="12" rx="2.75" fill="rgba(0,0,0,0.75)" transform="rotate(-12 48 36)" />
      <rect x="60" y={forme === 'pilule' ? 40 : 30} width="5.5" height="12" rx="2.75" fill="rgba(0,0,0,0.75)" transform="rotate(-12 62 36)" />
    </svg>
  );
};

export const ROSE = '#d6287f';

// Fenêtre Grok : barre de titre noire, barre latérale (Search, liste, Hidden Bots), zone principale noire.
export const FenetreGrok: React.FC<{sidebar: React.ReactNode; children?: React.ReactNode; left?: number; top?: number}> = ({sidebar, children, left = 49, top = 48}) => (
  <div style={{position: 'absolute', left, top, width: 2400, height: 1400, borderRadius: 22, overflow: 'hidden', background: '#010101', boxShadow: '0 0 0 1px rgba(255,255,255,0.07), 0 30px 80px rgba(0,0,0,0.6)', fontFamily: INTER_L}}>
    <div style={{position: 'absolute', left: 0, top: 0, width: 2400, height: 67, background: '#000'}} />
    <div style={{position: 'absolute', left: 0, top: 67, width: 466, height: 1400, background: '#0d0d0d', borderRight: '1px solid #1c1c1c'}} />
    {/* éléments placés en coordonnées écran : décalage de la fenêtre retiré */}
    <div style={{position: 'absolute', left: -left, top: -top}}>
      <Ico n="plus" s={26} c="#bdbdbd" w={1.8} style={{position: 'absolute', left: 451, top: 141}} />
      <div style={{position: 'absolute', left: 70, top: 200, width: 422, height: 57, borderRadius: 12, background: '#1f1f1f', boxShadow: 'inset 0 0 0 1px #2e2e2e'}} />
      <Ico n="search" s={22} c="#a5a5a5" w={2} style={{position: 'absolute', left: 85, top: 217}} />
      <div style={ligne(117, 228, 30, {fontSize: 22.5, color: GRIS})}>Search</div>
      {sidebar}
      {children}
    </div>
  </div>
);
