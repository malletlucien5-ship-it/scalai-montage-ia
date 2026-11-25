import React from 'react';
import {AbsoluteFill, Easing, interpolate, useCurrentFrame} from '../../shared/rt';
import {Plate} from '../../shared/Plate';
import {SfxTrack, SfxCue} from '../../shared/Sfx';
import {INTER} from '../../shared/fonts';

// Référence : 33,667 s (coupe) à 37,37 s. Panneau « Session Overview » qui monte du bas,
// puis MEMORY/OFF, PROJECTS/N/A, CONTEXT/N/A s'allument l'un après l'autre.
export const meta = {
  id: '07-carte-memoire',
  durationInFrames: 111,
  fps: 30,
  defaultProps: {showPlate: true},
  occurrences: [{ref: [33.667, 37.367], from: 0, durationInFrames: 111, mode: 'overlay'}],
};

// Bruitages : grave-apparition à l'arrivée du panneau, puis sur chaque N/D mis en valeur.
const SFX: SfxCue[] = [
  {frame: 3, name: 'grave-apparition'},
  {frame: 39, name: 'grave-apparition'},
  {frame: 64, name: 'grave-apparition'},
];

const P = {x: 320, y: 722, w: 1278, h: 307, bar: 66};
const COLS = [533, 959, 1385]; // centres des colonnes (px absolus)

const cl = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const eo = Easing.out(Easing.cubic);
// Flou d'apparition relevé sur l'original : chaque élément arrive flou (op 0 -> 1) et se précise.
const bl = (op: number, max = 5) => (op < 0.999 ? `blur(${(1 - op) * max}px)` : undefined);

const Label: React.FC<{cx: number; text: string; op: number}> = ({cx, text, op}) => (
  <div
    style={{
      position: 'absolute',
      left: cx - P.x - 200,
      width: 400,
      top: 845 - P.y - 5,
      textAlign: 'center',
      fontSize: 19.5,
      fontWeight: 500,
      letterSpacing: 4.6,
      color: 'rgb(123,120,118)',
      opacity: op,
      filter: bl(op),
      paddingLeft: 4.6,
    }}
  >
    {text}
  </div>
);

const NA: React.FC<{cx: number; f: number; start: number}> = ({cx, f, start}) => {
  const p = interpolate(f, [start, start + 7], [0, 1], {...cl, easing: eo});
  const glow = interpolate(f, [start + 2, start + 12], [0, 1], cl);
  return (
    <div
      style={{
        position: 'absolute',
        left: cx - P.x - 200,
        width: 400,
        top: 877 - P.y + (1 - p) * 6,
        textAlign: 'center',
        fontSize: 102,
        fontWeight: 700,
        letterSpacing: -2,
        lineHeight: '120px',
        color: 'rgb(15,170,255)',
        opacity: p,
        filter: bl(p, 6),
        textShadow: `0 0 ${10 * glow}px rgba(0,140,255,${0.5 * glow}), 0 0 ${28 * glow}px rgba(0,120,255,${0.28 * glow})`,
      }}
    >
      N/D
    </div>
  );
};

const CarteMemoire: React.FC<{showPlate?: boolean}> = ({showPlate = true}) => {
  const f = useCurrentFrame();
  const ty = interpolate(f, [2, 26], [18, 0], {...cl, easing: eo});
  const op = interpolate(f, [2, 7], [0, 1], cl);
  const bgA = interpolate(f, [3, 19], [0.12, 1], {...cl, easing: Easing.inOut(Easing.quad)});
  const head = interpolate(f, [8, 13], [0, 1], cl);
  const mem = interpolate(f, [9, 14], [0, 1], cl);
  const tog = interpolate(f, [12, 19], [0, 1], cl);
  const proj = interpolate(f, [27, 35], [0, 1], cl);
  const ctx = interpolate(f, [53, 61], [0, 1], cl);
  return (
    <AbsoluteFill style={{fontFamily: INTER}}>
      <Plate show={showPlate} />
      <SfxTrack cues={SFX} />
      <div
        style={{
          position: 'absolute',
          left: P.x,
          top: P.y,
          width: P.w,
          height: P.h,
          transform: `translateY(${ty}px)`,
          opacity: op,
          filter: bl(Math.min(1, bgA * 1.15), 4),
        }}
      >
        {/* fond : verre dépoli qui s'opacifie */}
        <div style={{position: 'absolute', inset: 0, borderRadius: 20, overflow: 'hidden', backdropFilter: 'blur(18px)'}}>
          <div style={{position: 'absolute', inset: 0, opacity: bgA, background: 'rgb(19,16,15)'}}>
            <div style={{position: 'absolute', left: 0, right: 0, top: 0, height: P.bar, background: 'rgb(15,13,9)'}} />
            <div style={{position: 'absolute', left: 0, right: 0, top: P.bar, height: 1, background: 'rgb(26,23,20)'}} />
            {[747, 1172].map((x) => (
              <div
                key={x}
                style={{
                  position: 'absolute',
                  left: x - P.x,
                  top: P.bar + 12,
                  bottom: 12,
                  width: 1.5,
                  background: 'linear-gradient(rgba(255,255,255,0.035), rgba(255,255,255,0.02))',
                }}
              />
            ))}
          </div>
        </div>
        <div style={{position: 'absolute', inset: 0, borderRadius: 20, border: '1.5px solid rgba(190,186,182,0.6)'}} />
        {/* pastilles de fenêtre */}
        {[
          [355, 'rgb(252,95,90)'],
          [376, 'rgb(253,188,44)'],
          [397, 'rgb(42,200,68)'],
        ].map(([x, c]) => (
          <div
            key={x as number}
            style={{
              position: 'absolute',
              left: (x as number) - P.x - 6.5,
              top: 753 - P.y - 6.5,
              width: 13,
              height: 13,
              borderRadius: 7,
              background: c as string,
            }}
          />
        ))}
        {/* titre */}
        <div
          style={{
            position: 'absolute',
            left: 0,
            right: 0,
            top: 742 - P.y,
            textAlign: 'center',
            fontSize: 16,
            fontWeight: 400,
            color: 'rgb(166,163,160)',
            opacity: head,
            filter: bl(head, 4),
          }}
        >
          Aperçu de session
        </div>
        {/* badge Claude */}
        <div
          style={{
            position: 'absolute',
            right: P.x + P.w - 1572,
            top: 739 - P.y,
            height: 28,
            padding: '0 13px 0 30px',
            borderRadius: 14,
            background: 'rgba(100,45,22,0.32)',
            border: '1px solid rgba(160,80,50,0.18)',
            display: 'flex',
            alignItems: 'center',
            fontSize: 15,
            fontWeight: 500,
            color: 'rgb(192,86,60)',
            opacity: head,
            filter: bl(head, 4),
          }}
        >
          <div style={{position: 'absolute', left: 13, top: 10, width: 8, height: 8, borderRadius: 4, background: 'rgb(222,104,76)'}} />
          Claude · Actif
        </div>
        <Label cx={COLS[0]} text="MÉMOIRE" op={mem} />
        <Label cx={COLS[1]} text="PROJETS" op={proj} />
        <Label cx={COLS[2]} text="CONTEXTE" op={ctx} />
        {/* interrupteur OFF */}
        <div style={{opacity: tog, filter: bl(tog, 6)}}>
          <div
            style={{
              position: 'absolute',
              left: 432 - P.x,
              top: 904 - P.y,
              width: 104,
              height: 54,
              borderRadius: 27,
              background: 'rgb(196,44,46)',
              boxShadow: '0 0 14px rgba(230,40,40,0.55), 0 0 30px rgba(200,30,30,0.25)',
            }}
          >
            <div style={{position: 'absolute', left: 6, top: 7, width: 40, height: 40, borderRadius: 20, background: '#fff'}} />
          </div>
          <div
            style={{
              position: 'absolute',
              left: 554 - P.x,
              top: 908 - P.y,
              fontSize: 40,
              fontWeight: 800,
              letterSpacing: 0.5,
              color: 'rgb(215,50,56)',
              textShadow: '0 0 12px rgba(220,40,40,0.35)',
            }}
          >
            OFF
          </div>
        </div>
        <NA cx={COLS[1]} f={f} start={39} />
        <NA cx={COLS[2]} f={f} start={64} />
      </div>
    </AbsoluteFill>
  );
};

export default CarteMemoire;

// Signaux sonores exportés pour la bibliothèque (cloud/cues_globaux.py).
export const cues = SFX;
