import React from 'react';
import {AbsoluteFill, interpolate} from '../../shared/rt';
import {Bg, Camera, MacWindow, useT, samples, keys, FONT} from './kit';
import {SfxTrack, SfxCue} from '../../shared/Sfx';

// Référence : 135,17 à 144,38 s (9,21 s).
export const meta = {
  id: '16-master-prompt-doc', durationInFrames: 276, fps: 30,
  occurrences: [{ref: [135.17, 144.38], from: 0, durationInFrames: 276, mode: 'plein'}],
};

const Z = [0.9125,0.9114,0.9125,0.9125,0.9125,0.9137,0.9137,0.9148,0.9148,0.9160,0.9171,0.9171,0.9182,0.9194,0.9205,0.9216,0.9216,0.9228,0.9239,0.9250,0.9262,0.9273,0.9284,0.9296,0.9307,0.9330,0.9341,0.9353,0.9364,0.9375,0.9387,0.9409,0.9421,0.9432,0.9443,0.9466,0.9478,0.9489,0.9500,0.9523,0.9534,0.9546,0.9568,0.9580,0.9591,0.9602,0.9625,0.9637,0.9648,0.9659,0.9682,0.9693,0.9705,0.9716,0.9739,0.9750,0.9761,0.9773,0.9784,0.9796,0.9807,0.9818,0.9835,0.9847,0.9858,0.9864,0.9875,0.9886,0.9898,0.9909,0.9920,0.9932,0.9932,0.9943,0.9955,0.9955,0.9966,0.9966,0.9977,0.9977,0.9989,0.9989,0.9989,0.9989,1.0];

const CYAN = '#6CE3EC';
const WHITE = '#E8E5E2';
const BLUE = '#3A90C8';

type Seg = [string, boolean?];
const SECTIONS: {label: string; y: number; lines: number[]; seg: Seg[]; tl: number; t0: number; t1: number}[] = [
  {label: 'RÔLE', y: 193, lines: [235, 272], tl: 1.0, t0: 1.15, t1: 2.35, seg: [
    ['Tu es un stratège en '], ['marketing', true], [' digital spécialisé dans la croissance par '], ['e-mail', true],
    [' pour les dirigeants de petites entreprises. Ton audience : des commerces locaux et en ligne qui veulent créer leur premier vrai canal '],
    ['marketing', true], ['.'],
  ]},
  {label: 'COMMENT TU TRAVAILLES', y: 378, lines: [418], tl: 2.6, t0: 2.75, t1: 3.5, seg: [
    ['Amical mais pro. Ton conversationnel. Reste simple. Tes clients ne sont pas technophiles. Explique le pourquoi avant le comment.'],
  ]},
  {label: 'TON ÉQUIPE', y: 524, lines: [564], tl: 3.85, t0: 4.0, t1: 4.75, seg: [
    ['Une équipe de 3 : un rédacteur e-mail, un expert automatisation, une responsable client. Point hebdo, tout est suivi dans '],
    ['Notion.', true],
  ]},
  {label: 'TES OUTILS', y: 670, lines: [711], tl: 5.1, t0: 5.25, t1: 5.85, seg: [
    ['Mailchimp, Klaviyo, Notion, Zapier, Loom,', true], [' Google '], ['Analytics.', true], [' Rapports clients exportés chaque semaine en PDF.'],
  ]},
  {label: 'RÈGLES DE RÉPONSE', y: 816, lines: [858], tl: 6.1, t0: 6.25, t1: 7.3, seg: [
    ['Écris pour un niveau collège. Des exemples concrets, jamais de théorie abstraite. Termine chaque réponse par une action faisable aujourd’hui.'],
  ]},
];
const SEPS = [330, 476, 622, 769];

// Squelette de chargement (coordonnées finales).
const SKEL: {y: number; w: number[]}[] = [
  {y: 200, w: [1, 0.93, 0.62]},
  {y: 330, w: [1, 0.9, 0.62]},
  {y: 463, w: [1, 0.8]},
  {y: 568, w: [1, 0.8]},
  {y: 676, w: [1, 0.95, 0.62]},
];

const FADE = 16;

const Reveal: React.FC<{seg: Seg[]; p: number}> = ({seg, p}) => {
  let i = 0;
  const out: React.ReactNode[] = [];
  seg.forEach(([txt, k], si) => {
    for (const ch of txt) {
      const op = Math.max(0, Math.min(1, (p - i) / FADE));
      out.push(<span key={`${si}-${i}`} style={{opacity: op, color: k ? CYAN : WHITE}}>{ch}</span>);
      i++;
    }
  });
  return <>{out}</>;
};

// Bruitages : entrée de la fenêtre, puis frappe pendant le remplissage de chaque section.
const CUES: SfxCue[] = [
  {frame: 0, name: 'whoosh-transition'},
  {frame: 35, name: 'frappe-clavier', durationInFrames: 36},
  {frame: 83, name: 'frappe-clavier', durationInFrames: 22},
  {frame: 120, name: 'frappe-clavier', durationInFrames: 23},
  {frame: 158, name: 'frappe-clavier', durationInFrames: 18},
  {frame: 188, name: 'frappe-clavier', durationInFrames: 31},
];

const Comp: React.FC = () => {
  const t = useT();
  const s = t < 0.4 ? Z[0] : samples(t, Z, 0.1, 0.4);
  // entrée : flou + surexposition qui retombent
  const blur = keys(t, [[0, 26], [0.1, 16], [0.2, 6], [0.33, 0]]);
  const bright = keys(t, [[0, 0.75], [0.1, 1.1], [0.2, 1.45], [0.3, 1.2], [0.4, 1]]);
  const skel = keys(t, [[0.45, 1], [0.7, 0]]);
  const W = {x: 80, y: 86};
  return (
    <AbsoluteFill style={{backgroundColor: '#000', fontFamily: FONT}}>
      <SfxTrack cues={CUES} />
      <Bg id="16" />
      <Camera scale={s} ox={959.5} oy={486} blur={blur} bright={bright}>
        <MacWindow x={80} y={86} w={1760} h={903} r={30} titleH={55} titleBg="#181514" bodyBg="#0F0D0E" sep="#0B0909"
          title={<span style={{fontWeight: 600}}>PROMPT MAÎTRE</span>} titleSize={16} titleColor="#8E8B88" titleSpacing={2.2} dotX={37} dotGap={25} dotR={8.5}>
          {/* squelette */}
          <div style={{opacity: skel, filter: 'blur(1.5px)'}}>
            {SKEL.map((sk, i) => (
              <React.Fragment key={i}>
                <div style={{position: 'absolute', left: 138 - W.x, top: sk.y - 3 - W.y, width: 120, height: 6, borderRadius: 3, background: '#252321'}} />
                {sk.w.map((w, j) => (
                  <div key={j} style={{position: 'absolute', left: 138 - W.x, top: sk.y + 27 + j * 24 - 3.5 - W.y, width: 1644 * w, height: 7, borderRadius: 3.5, background: '#252321'}} />
                ))}
              </React.Fragment>
            ))}
          </div>
          {SEPS.map((y, i) => (
            <div key={i} style={{position: 'absolute', left: 136 - W.x, top: y - W.y, width: 1648, height: 1, background: '#1A1718', opacity: keys(t, [[SECTIONS[i + 1].tl - 0.1, 0], [SECTIONS[i + 1].tl + 0.1, 1]])}} />
          ))}
          {SECTIONS.map((sec, i) => {
            const n = sec.seg.reduce((a, x) => a + [...x[0]].length, 0);
            const p = interpolate(t, [sec.t0, sec.t1], [0, n + FADE], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
            return (
              <React.Fragment key={i}>
                <div style={{position: 'absolute', left: 136 - W.x, top: sec.y - 10 - W.y, height: 20, lineHeight: '20px', fontFamily: FONT, fontSize: 12.8, fontWeight: 700, letterSpacing: 3.0, color: BLUE, opacity: keys(t, [[sec.tl, 0], [sec.tl + 0.15, 1]])}}>
                  {sec.label}
                </div>
                <div style={{position: 'absolute', left: 136 - W.x, top: sec.lines[0] - 18.5 - W.y, width: 1650, fontFamily: FONT, fontSize: 21.4, fontWeight: 650, lineHeight: '37px', letterSpacing: 0.82}}>
                  <Reveal seg={sec.seg} p={p} />
                </div>
              </React.Fragment>
            );
          })}
          <div style={{position: 'absolute', left: 0, top: 968 - W.y, width: 1760, height: 1, background: '#1D1D1B'}} />
        </MacWindow>
      </Camera>
    </AbsoluteFill>
  );
};
export default Comp;

// Signaux sonores exportés pour la bibliothèque (cloud/cues_globaux.py).
export const cues = CUES;
