import React from 'react';
import {AbsoluteFill, useCurrentFrame} from '../../shared/rt';
import {ease, Cursor, ScreenBg} from './ui';
import {Gmail, Calendar, Drive, Slack, Notion} from './apps';
import {HomeScreen, CustomizeScreen, ConnectorsScreen, AfternoonScreen} from './claude23';
import {SfxTrack, SfxCue} from '../../shared/Sfx';

// Occurrence 1 : 270,0 s à 280,0 s (300 images). Pause neutre 0,5 s. Occurrence 2 : 302,0 s à 305,0 s (90 images).
export const meta = {id: '23-apps-connecteurs', durationInFrames: 405, fps: 30, defaultProps: {showPlate: true},
  occurrences: [
    {ref: [270.1, 280.0], from: 3, durationInFrames: 297, mode: 'plein'},
    {ref: [302.0, 305.0], from: 315, durationInFrames: 90, mode: 'plein'},
  ],
};

// Bruitages calés sur le minutage de l'animation (règles : SFX-REGLES.md).
const SFX: SfxCue[] = [
  {frame: 3, name: 'whoosh-transition'},
  {frame: 39, name: 'whoosh-transition'},
  {frame: 63, name: 'whoosh-transition'},
  {frame: 84, name: 'whoosh-transition'},
  {frame: 105, name: 'whoosh-transition'},
  {frame: 129, name: 'whoosh-transition'},
  {frame: 158, name: 'clic'},
  {frame: 185, name: 'clic'},
  {frame: 254, name: 'clic'},
  {frame: 285, name: 'clic'},
  {frame: 318, name: 'whoosh-transition'},
  {frame: 336, name: 'clic'},
  {frame: 345, name: 'pop'},
  {frame: 355, name: 'clic'},
  {frame: 366, name: 'pop'},
  {frame: 373, name: 'clic'},
  {frame: 384, name: 'pop'},
  {frame: 390, name: 'clic'},
  {frame: 396, name: 'pop'},
];

const path = (f: number, pts: [number, number, number][]) => {
  if (f <= pts[0][0]) return [pts[0][1], pts[0][2]];
  for (let i = 1; i < pts.length; i++) if (f <= pts[i][0]) {
    const p = ease(f, pts[i - 1][0], pts[i][0]);
    return [pts[i - 1][1] + (pts[i][1] - pts[i - 1][1]) * p, pts[i - 1][2] + (pts[i][2] - pts[i - 1][2]) * p];
  }
  const l = pts[pts.length - 1];
  return [l[1], l[2]];
};

// Fenêtre centrée (cx, cy) de largeur affichée W, contenu natif w x h.
const Frame: React.FC<{W: number; w: number; h: number; cx: number; cy: number; bg: string; r?: number; children: React.ReactNode}> = ({W, w, h, cx, cy, bg, r = 16, children}) => {
  const s = W / w;
  return (
    <div style={{position: 'absolute', left: cx - w / 2, top: cy - h / 2, width: w, height: h, transform: `scale(${s})`, transformOrigin: 'center', borderRadius: r, overflow: 'hidden', background: bg,
      boxShadow: `0 0 0 ${1.5 / s}px rgba(205,205,200,0.5), 0 30px 90px rgba(0,0,0,0.6)`}}>{children}</div>
  );
};

const Part1: React.FC<{f: number; showPlate: boolean}> = ({f, showPlate}) => {
  if (f < 3) return showPlate ? <AbsoluteFill style={{background: '#0E0E10'}} /> : null;
  const t = 270 + f / 30;
  if (f < 129) {
    const W = 1363 + 10.6 * (t - 270.6);
    const apps: [number, React.ReactNode, number, number, string][] = [
      [3, <Gmail />, 1363, 840, '#151817'], [39, <Calendar />, 1372, 851, '#fff'], [63, <Drive />, 1384, 858, '#fff'], [84, <Slack />, 1391, 863, '#1a1d21'], [105, <Notion />, 1398, 873, '#fff'],
    ];
    let k = 0; apps.forEach((a, i) => { if (f >= a[0]) k = i; });
    const [, node, w, h, bg] = apps[k];
    return <Frame W={W} w={w} h={h} cx={960} cy={540} bg={bg} r={22}>{node}</Frame>;
  }
  // écrans Claude : 1652 x 765 de base
  const W = f < 168 ? 1652 + (f - 138) * (8 / 30) : f < 210 ? 1660 + (f - 168) * (10 / 42) : 1670 + (f - 210) * (21 / 75);
  const s = W / 1652;
  let screen: React.ReactNode;
  if (f < 159) screen = <HomeScreen tip={f >= 148 ? ease(f, 148, 151) : 0} />;
  else if (f < 186) screen = <CustomizeScreen />;
  else if (f < 255) screen = <ConnectorsScreen mode="github" detail={1} offDim={0.45} />;
  else screen = <ConnectorsScreen mode="gcal" detail={ease(f, 255, 262)} offDim={0.55 + 0.35 * ease(f, 255, 265)} />;
  const [cx, cy] = path(f, [
    [129, 280, 500], [135, 245, 455], [141, 205, 428], [147, 180, 405], [152, 165, 398], [160, 180, 403], [165, 185, 405], [168, 240, 360], [171, 270, 315], [174, 290, 300], [177, 292, 292],
    [234, 292, 292], [237, 355, 345], [240, 515, 435], [243, 605, 485], [246, 635, 505], [249, 650, 505], [270, 650, 505], [273, 895, 565], [276, 1175, 605], [279, 1305, 625], [282, 1355, 628], [300, 1368, 632],
  ]);
  const hand = (f >= 150 && f < 159) || (f >= 180 && f < 234) || f >= 276;
  return (
    <>
      <Frame W={W} w={1652} h={765} cx={969} cy={544} bg="#1e1e1c" r={16}>{screen}</Frame>
      <div style={{position: 'absolute', inset: 0}}><Cursor x={cx} y={cy} kind={hand ? 'hand' : 'arrow'} scale={1.05 * s} /></div>
    </>
  );
};

const Part2: React.FC<{f: number}> = ({f}) => {
  const W = 1625 + 31 * Math.min(1, f / 84);
  const o = ease(f, 3, 6);
  const [cx, cy] = path(f, [[3, 1010, 620], [12, 700, 840], [18, 515, 902], [26, 515, 905], [90, 520, 910]]);
  const press = f >= 21 && f < 27 ? ease(f, 21, 23) * (1 - ease(f, 24, 27)) : 0;
  if (f < 3) return null;
  return (
    <div style={{position: 'absolute', inset: 0, opacity: o}}>
      <Frame W={W} w={1656} h={914} cx={961} cy={540} bg="#1f1d1c" r={24}><AfternoonScreen f={f} /></Frame>
      {press > 0 && <div style={{position: 'absolute', left: cx - 16, top: cy - 16, width: 32, height: 32, borderRadius: 16, border: '2px solid rgba(255,255,255,0.7)', opacity: press}} />}
      {f < 40 && <Cursor x={cx} y={cy} kind="arrow" scale={0.7} />}
    </div>
  );
};

const AppsConnecteurs: React.FC<{showPlate?: boolean}> = ({showPlate = true}) => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill style={{background: showPlate ? '#000' : 'transparent'}}>
      {f >= 3 && <ScreenBg />}
      {f < 300 ? <Part1 f={f} showPlate={showPlate} /> : f >= 315 ? <Part2 f={f - 315} /> : null}
      <SfxTrack cues={SFX} />
    </AbsoluteFill>
  );
};
export default AppsConnecteurs;

// Signaux sonores exportés pour la bibliothèque (cloud/cues_globaux.py).
export const cues = SFX;
