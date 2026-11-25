import React from 'react';
import {SfxTrack, SfxCue} from '../../shared/Sfx';
import {AbsoluteFill, Easing, interpolate, random, useCurrentFrame} from '../../shared/rt';
import {ARIAL_L} from '../../shared/localFonts';
// police de l'original : Helvetica Neue (mesurée sur les largeurs de titres)
const INTER = `"Helvetica Neue", Helvetica, Arial, ${ARIAL_L}, sans-serif`;

// Réf 544.61 à 558.06 s. Trois cartes de skills qui s'allument en séquence.
export const meta = {
  id: '35-chainage-skills',
  durationInFrames: 403,
  fps: 30,
  occurrences: [{ref: [544.61, 558.06] as [number, number], from: 0, durationInFrames: 403, mode: 'plein' as const}],
};

const FPS = 30;
const ease = Easing.out(Easing.cubic);
const ramp = (t: number, a: number, b: number, e = ease) =>
  interpolate(t, [a, b], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: e});
const mix = (a: number[], b: number[], k: number) => a.map((v, i) => Math.round(v + (b[i] - v) * k));
const rgb = (c: number[], a = 1) => `rgba(${c[0]},${c[1]},${c[2]},${a})`;

const CARD_X = [82, 717, 1351];
const CW = 487;
const CH = 310;
const CY = 429;
const LINE_Y = 583;

const CARDS = [
  {title: 'Skill Copywriting', sub: 'écrit avec ta voix', layer: 1, icon: 'pen'},
  {title: 'Skill Email', sub: 'utilise le Skill Copywriting', layer: 2, icon: 'mail'},
  {title: 'Automatisation inbox', sub: 'appelle les deux skills.', layer: 3, icon: 'sun'},
];

// fenêtres d'activation [début, fin] (s)
// les trois cartes se rallument ensemble à 10,25 s
const ACT: [number, number][][] = [
  [[1.85, 3.9], [10.25, 99]],
  [[3.9, 8.3], [10.25, 99]],
  [[8.3, 99]],
];
const ENTER = [-0.1, 0.18, 0.45];

const Icon: React.FC<{k: string; color: string}> = ({k, color}) => {
  const p = {fill: 'none', stroke: color, strokeWidth: 1.9, strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const};
  return (
    <svg width={30} height={30} viewBox="0 0 24 24">
      {k === 'pen' && (
        <g {...p}>
          <path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z" />
          <line x1={13} y1={20.5} x2={21} y2={20.5} />
        </g>
      )}
      {k === 'mail' && (
        <g {...p}>
          <rect x={2.5} y={5} width={19} height={14} rx={2.5} />
          <path d="M3 7l9 6 9-6" />
        </g>
      )}
      {k === 'sun' && (
        <g {...p}>
          <circle cx={12} cy={12} r={3} />
          {Array.from({length: 8}).map((_, i) => {
            const a = (i * Math.PI) / 4;
            return <line key={i} x1={12 + Math.cos(a) * 6} y1={12 + Math.sin(a) * 6} x2={12 + Math.cos(a) * 9} y2={12 + Math.sin(a) * 9} />;
          })}
        </g>
      )}
    </svg>
  );
};

// bruitages calés sur les images où chaque élément devient visible (SFX-REGLES.md)
const CUES: SfxCue[] = [
  {frame: 1, name: 'whoosh-transition'}, // carte 1
  {frame: 8, name: 'whoosh-transition'}, // carte 2
  {frame: 16, name: 'whoosh-transition'}, // carte 3
  {frame: 57, name: 'pop'}, // carte 1 s'allume (1,9 s)
  {frame: 118, name: 'pop'}, // carte 2 s'allume (3,95 s)
  {frame: 250, name: 'pop'}, // carte 3 s'allume (8,35 s)
  {frame: 309, name: 'pop'}, // les trois cartes s'allument (10,3 s)
];

const Comp: React.FC = () => {
  const f = useCurrentFrame();
  const t = f / FPS;
  const bg = ramp(t, 0, 0.3);
  const titleO = ramp(t, 0, 0.3);
  const lineDim = ramp(t, 0.5, 0.8);

  return (
    <AbsoluteFill style={{background: '#000', fontFamily: INTER}}>
      <AbsoluteFill
        style={{
          opacity: bg,
          background:
            'radial-gradient(ellipse 1250px 560px at 50% 38%, #06214a 0%, #041632 28%, #030b1f 58%, #010610 80%, #000103 100%)',
        }}
      />
      <div
        style={{
          position: 'absolute',
          left: 0,
          right: 0,
          top: 362,
          textAlign: 'center',
          fontSize: 15.5,
          fontWeight: 600,
          letterSpacing: 4.2,
          color: '#4f5d76',
          opacity: titleO,
        }}
      >
        CHAÎNAGE DE SKILLS · TOUT LE PIPELINE
      </div>
      {/* connecteurs */}
      {[0, 1].map((i) => {
        const x1 = CARD_X[i] + CW;
        const x2 = CARD_X[i + 1];
        const p = ramp(t, 1.0 + i * 0.35, 1.3 + i * 0.35, Easing.inOut(Easing.quad));
        return (
          <React.Fragment key={i}>
            <div style={{position: 'absolute', left: x1, top: LINE_Y - 1, width: x2 - x1, height: 2, background: '#0a1a33', opacity: lineDim}} />
            <div
              style={{
                position: 'absolute',
                left: x1,
                top: LINE_Y - 1,
                width: (x2 - x1) * p,
                height: 2,
                background: '#6a8eab',
                boxShadow: '0 0 6px rgba(40,140,255,0.9), 0 0 16px rgba(20,110,255,0.6)',
              }}
            />
            {/* flux de particules relevé sur l'original : ~14 points de 2 à 3 px par segment, ±2 px autour de la ligne, 60 à 100 px/s, scintillement */}
            {t > 10.35 &&
              Array.from({length: 14}).map((_, k) => {
                const sp = 60 + random(`sp${i}-${k}`) * 40;
                const ph = random(`ph${i}-${k}`);
                const gap = x2 - x1;
                const pos = (((t - 10.35) * sp) / gap + ph) % 1;
                const tw = 0.55 + 0.45 * Math.sin((t * (5 + random(`tw${i}-${k}`) * 6) + ph * 6.28));
                const sz = 1.8 + random(`sz${i}-${k}`) * 1.0;
                const dy = (random(`dy${i}-${k}`) - 0.5) * 4;
                return (
                  <div
                    key={k}
                    style={{
                      position: 'absolute',
                      left: x1 + gap * pos - sz / 2,
                      top: LINE_Y + dy - sz / 2,
                      width: sz,
                      height: sz,
                      borderRadius: sz,
                      background: '#b4ecff',
                      boxShadow: '0 0 4px rgba(120,220,255,0.9)',
                      opacity: ramp(t, 10.35, 10.7) * tw * Math.min(1, pos * 8, (1 - pos) * 8),
                    }}
                  />
                );
              })}
          </React.Fragment>
        );
      })}
      {CARDS.map((c, i) => {
        const e = ramp(t, ENTER[i], ENTER[i] + 0.32);
        const group = ramp(t, 10.25, 10.6);
        const on = Math.max(...ACT[i].map(([a0, a1]) => ramp(t, a0, a0 + 0.35) * (1 - ramp(t, a1, a1 + 0.35))));
        const seen = ramp(t, ACT[i][0][0], ACT[i][0][0] + 0.35); // devient « déjà vu » après activation
        const fillA = mix([17, 14, 13], [18, 30, 50], on);
        const border = rgba(mix([28, 26, 25], [40, 130, 165], on));
        const titleC = rgb(mix([155, 153, 151], [249 - group * 20, 253 - group * 18, 255 - group * 12], on));
        const subC = rgb(mix([77, 75, 73], [126, 200, 216], on));
        const dotC = on > 0.01 ? rgb(mix(seen > 0.5 ? [56, 106, 101] : [60, 57, 56], [111, 242, 247], on)) : rgb(seen > 0.5 ? [56, 106, 101] : [60, 57, 56]);
        const pillTxt = rgb(mix([75, 72, 71], [131, 194, 201], on));
        const pillBorder = rgb(mix([42, 39, 38], [47, 95, 115], on));
        const pillBg = rgba(mix([17, 14, 13], [16, 40, 58], on));
        const pillDot = rgb(mix([56, 150, 110], [111, 242, 220], on));
        const iconBg = rgb(mix([31, 28, 27], [19, 48, 78], on));
        const iconBorder = rgba(mix([40, 37, 36], [45, 110, 150], on));
        const iconC = rgb(mix([150, 220, 212], [156, 241, 255], on));
        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: CARD_X[i],
              top: CY,
              width: CW,
              height: CH,
              borderRadius: 26,
              boxSizing: 'border-box',
              background: `radial-gradient(ellipse 520px 330px at 85% 8%, ${rgb(mix(fillA, [28, 52, 82], on))} 0%, ${rgb(fillA)} 70%)`,
              border: `1.5px solid ${border}`,
              boxShadow: `0 0 ${on * 44}px rgba(10,110,255,${on * (0.55 - group * 0.22)}), 0 20px 50px rgba(0,0,0,0.5)`,
              opacity: e,
              transform: `translateY(${(1 - e) * 22}px)`,
            }}
          >
            <div
              style={{
                position: 'absolute',
                left: 49,
                top: 49,
                width: 68,
                height: 68,
                borderRadius: 15,
                background: iconBg,
                border: `1.5px solid ${iconBorder}`,
                boxSizing: 'border-box',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <Icon k={c.icon} color={iconC} />
            </div>
            <div
              style={{
                position: 'absolute',
                right: 49,
                top: 77,
                width: 13,
                height: 13,
                borderRadius: 7,
                background: dotC,
                boxShadow: on > 0.05 ? `0 0 ${10 * on}px rgba(110,240,250,${on})` : 'none',
              }}
            />
            <div style={{position: 'absolute', left: 49, top: 150, fontSize: 24, fontWeight: 700, color: titleC, letterSpacing: -0.1}}>{c.title}</div>
            <div style={{position: 'absolute', left: 49, top: 187, fontSize: 18, fontWeight: 700, color: subC, opacity: seen}}>{c.sub}</div>
            <div
              style={{
                position: 'absolute',
                left: 49,
                top: 237,
                height: 28,
                padding: '0 15px 0 12px',
                borderRadius: 14,
                border: `1.5px solid ${pillBorder}`,
                background: pillBg,
                display: 'flex',
                alignItems: 'center',
                gap: 9,
                fontSize: 13.5,
                fontWeight: 700,
                letterSpacing: 2.2,
                color: pillTxt,
              }}
            >
              <div style={{width: 8, height: 8, borderRadius: 4, background: pillDot}} />
              SKILL · NIVEAU {c.layer}
            </div>
          </div>
        );
      })}
    <SfxTrack cues={CUES} />
    </AbsoluteFill>
  );
};

function rgba(c: number[]) {
  return `rgb(${c[0]},${c[1]},${c[2]})`;
}

export default Comp;

// Signaux sonores exportés pour la bibliothèque (cloud/cues_globaux.py).
export const cues = CUES;
