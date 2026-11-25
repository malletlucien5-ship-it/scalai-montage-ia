import React from 'react';
import {AbsoluteFill, Easing, Img, interpolate, Sequence, staticFile, useCurrentFrame} from '../../shared/rt';
import {INTER_L} from '../../shared/localFonts';
import {SfxTrack, SfxCue} from '../../shared/Sfx';

// d218 (plein cadre) : fond bleu nuit, couverture noire « AI OPERATING SYSTEM » (gros « AI » blanc condensé,
// carnet bleu lumineux) qui monte du bas, puis trois pages de document qui s'étalent en éventail derrière.
// Réf. occ. 1 : 729,93 s montée de la couverture (rapide puis lente), pages gauches 731,03 / 731,10 s,
//   page droite 731,43 s (~9 images chacune), zoom flou de sortie 732,87 -> 733,07 s (enchaîne sur d219).
// Réf. occ. 2 : 1246,0 -> 1251,9 s, même animation.
// Géométrie (1920x1080) : couverture x 693..1227, y 192..880 ; pages 420 x 554, pivots bas-centre
//   (832, 847) -22°, (895, 816) -12,7°, (1088, 822) +15,4°.
// Personnalisation : « AI OPERATING SYSTEM » remplace « AI COMPANY OS », logo montagne retiré (image retouchée).
const FPS = 30;
const GAP = 15;

type Occ = {ref: [number, number]; at: number; end: number};
const OCC: Occ[] = [
  // « J'appelle ça l'AI Operating System. ... Si vous le voulez, » -> relais par d219 sur « simplement »
  {ref: [729.93, 733.07], at: 785.2, end: 792.3},
  // « si vous voulez mon AI Operating System, avec toute la façon ... entreprises, » -> d219 sur « vous avez »
  {ref: [1246.0, 1251.9], at: 1329.05, end: 1334.25},
];

const plan = (() => {
  let from = 0;
  return OCC.map((o) => {
    const dur = Math.round((o.end - o.at) * FPS);
    const r = {o, from, dur};
    from += dur + GAP;
    return r;
  });
})();

const COVER = {x: 693, y: 192, w: 534, h: 688};
// Montée de la couverture : décalage vertical (px) relevé image par image.
const RISE_F = [0, 1, 2, 3, 4, 5, 8, 11, 14, 17, 22, 30, 45, 75];
const RISE_Y = [420, 336, 276, 204, 168, 156, 110, 60, 36, 22, 12, 8, 4, 0];

const PAGE = {w: 420, h: 554};
const PAGES = [
  {px: 832, py: 847, rot: -22, start: 33, kind: 'doc' as const},
  {px: 895, py: 816, rot: -12.7, start: 35, kind: 'doc' as const},
  {px: 1088, py: 822, rot: 15.4, start: 45, kind: 'blank' as const},
];
const SPREAD = 9;
const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

const Background: React.FC = () => (
  <AbsoluteFill
    style={{
      background: 'radial-gradient(ellipse 62% 62% at 50% 52%, #00224f 0%, #031a33 35%, #02101c 62%, #000611 85%, #00030b 100%)',
    }}
  >
    <AbsoluteFill
      style={{
        backgroundImage:
          'linear-gradient(rgba(90,150,255,0.035) 1px, transparent 1px), linear-gradient(90deg, rgba(90,150,255,0.035) 1px, transparent 1px)',
        backgroundSize: '64px 64px',
      }}
    />
  </AbsoluteFill>
);

const Line: React.FC<{w: number; c: string; h?: number; mt?: number; ml?: number}> = ({w, c, h = 7, mt = 11, ml = 0}) => (
  <div style={{width: w, height: h, background: c, borderRadius: 4, marginTop: mt, marginLeft: ml}} />
);

const DocPage: React.FC<{kind: 'doc' | 'blank'}> = ({kind}) => {
  const G = '#c9c9cc';
  const B = '#3d7be0';
  const Y = '#f2d360';
  return (
    <div
      style={{
        width: PAGE.w,
        height: PAGE.h,
        background: '#fafafa',
        borderRadius: 10,
        overflow: 'hidden',
        boxShadow: '0 12px 28px rgba(0,0,0,0.45)',
      }}
    >
      {kind === 'doc' ? (
        <div style={{padding: '24px 30px'}}>
          <div style={{display: 'flex', alignItems: 'center', gap: 10}}>
            <div style={{width: 20, height: 26, borderRadius: 3, background: '#2f6fe0'}} />
            <div style={{fontFamily: INTER_L, fontWeight: 600, fontSize: 17, color: '#3a3a3c'}}>AI Operating System</div>
          </div>
          <Line w={330} c="#111" h={13} mt={32} />
          {[
            [B, 300, 0], [G, 320, 18], [G, 300, 18], [B, 150, 0], [G, 330, 18], [Y, 280, 18], [G, 310, 18], [G, 260, 18],
            [B, 180, 0], [G, 320, 18], [G, 290, 18], [Y, 300, 18], [G, 250, 18], [B, 210, 0], [G, 320, 18], [G, 280, 18], [G, 300, 18],
          ].map(([c, w, ml], i) => (
            <div key={i} style={{display: 'flex', alignItems: 'center'}}>
              {ml ? <div style={{width: 8, height: 8, borderRadius: 4, background: B, marginTop: 11, marginRight: 10}} /> : null}
              <Line w={w as number} c={c as string} mt={11} />
            </div>
          ))}
        </div>
      ) : (
        <>
          <div style={{height: 46, background: '#ececee'}} />
          <div style={{padding: '40px 34px'}}>
            {[300, 260, 330, 280, 0, 310, 250, 320, 290, 0, 300, 270, 180].map((w, i) =>
              w ? <Line key={i} w={w} c="#cfcfd2" mt={13} /> : <div key={i} style={{height: 22}} />,
            )}
          </div>
        </>
      )}
    </div>
  );
};

const CoverArt: React.FC = () => (
  <div style={{position: 'absolute', inset: 0, background: '#000', overflow: 'hidden'}}>
    <Img
      src={staticFile('d218/couverture.jpg')}
      style={{position: 'absolute', left: 0, top: -6, width: 600, height: 745}}
    />
    {/* partie gauche noire derrière le titre */}
    <div style={{position: 'absolute', inset: 0, background: 'linear-gradient(90deg, #000 0%, #000 34%, rgba(0,0,0,0.6) 46%, rgba(0,0,0,0) 58%)'}} />
    <svg width={COVER.w} height={COVER.h} style={{position: 'absolute', inset: 0}}>
      {/* « AI » : x 45..189, capitales 95..345 */}
      <text x={45} y={345} fontFamily={INTER_L} fontWeight={900} fontSize={344} fill="#fff" textLength={144} lengthAdjust="spacingAndGlyphs">
        AI
      </text>
      {/* « OPERATING » : capitales 366..414 */}
      <text x={46} y={414} fontFamily={INTER_L} fontWeight={900} fontSize={66} fill="#fff" textLength={196} lengthAdjust="spacingAndGlyphs">
        OPERATING
      </text>
      {/* « SYSTEM » : capitales 434..516 */}
      <text x={45} y={516} fontFamily={INTER_L} fontWeight={900} fontSize={113} fill="#fff" textLength={198} lengthAdjust="spacingAndGlyphs">
        SYSTEM
      </text>
    </svg>
  </div>
);

const Scene: React.FC<{dur: number}> = ({dur}) => {
  const f = useCurrentFrame();
  const dy = interpolate(f, RISE_F, RISE_Y, clamp);
  // Sortie : zoom avant flou sur 6 images, dernière image noire.
  const ex0 = dur - 7;
  const z = interpolate(f, [ex0, dur - 1], [0, 1], {...clamp, easing: Easing.in(Easing.quad)});
  const scale = 1 + z * 1.1;
  const blackout = interpolate(f, [dur - 2, dur - 1], [0, 1], clamp);
  const content = (
    <>
      {PAGES.map((p, i) => {
        const t = interpolate(f, [p.start, p.start + SPREAD], [0, 1], {...clamp, easing: Easing.out(Easing.cubic)});
        if (t <= 0) return null;
        const cx = interpolate(t, [0, 1], [960, p.px]);
        const cy = interpolate(t, [0, 1], [COVER.y + COVER.h - 20 + dy, p.py]);
        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: cx - PAGE.w / 2,
              top: cy - PAGE.h,
              transformOrigin: '50% 100%',
              transform: `rotate(${p.rot * t}deg)`,
            }}
          >
            <DocPage kind={p.kind} />
          </div>
        );
      })}
      <div style={{position: 'absolute', left: COVER.x, top: COVER.y + dy, width: COVER.w, height: COVER.h, boxShadow: '0 20px 40px rgba(0,0,0,0.5)'}}>
        <CoverArt />
      </div>
    </>
  );
  return (
    <AbsoluteFill style={{overflow: 'hidden'}}>
      <AbsoluteFill style={{transform: `scale(${1 + z * 0.4})`}}>
        <Background />
      </AbsoluteFill>
      <AbsoluteFill style={{transform: `scale(${scale})`, filter: z > 0 ? `blur(${(z * 14).toFixed(2)}px)` : undefined}}>{content}</AbsoluteFill>
      {z > 0 &&
        [1.08, 1.18].map((k, i) => (
          <AbsoluteFill key={i} style={{transform: `scale(${scale * (1 + (k - 1) * z)})`, opacity: 0.35 * z, filter: `blur(${(z * 20).toFixed(1)}px)`}}>
            {content}
          </AbsoluteFill>
        ))}
      <AbsoluteFill style={{background: '#000', opacity: blackout}} />
    </AbsoluteFill>
  );
};

const CUES: SfxCue[] = plan.flatMap(({from}) => [
  {frame: from + 1, name: 'whoosh-transition' as const},
  {frame: from + PAGES[0].start + 1, name: 'grave-apparition' as const},
  {frame: from + PAGES[2].start + 1, name: 'grave-apparition' as const, gain: 0.7},
]);

const EbookAios: React.FC<{showPlate?: boolean}> = () => (
  <AbsoluteFill style={{background: '#000'}}>
    {plan.map(({from, dur}, i) => (
      <Sequence key={i} from={from} durationInFrames={dur} layout="none">
        <Scene dur={dur} />
      </Sequence>
    ))}
    <SfxTrack cues={CUES} />
  </AbsoluteFill>
);

export const meta = {
  id: 'd218-ebook-aios',
  fps: FPS,
  durationInFrames: plan[plan.length - 1].from + plan[plan.length - 1].dur,
  defaultProps: {showPlate: true},
  occurrences: plan.map(({o, from, dur}) => ({ref: o.ref, at: o.at, from, durationInFrames: dur, mode: 'plein' as const})),
};
export default EbookAios;

// Signaux sonores exportés pour la bibliothèque (cloud/cues_globaux.py).
export const cues = CUES;
