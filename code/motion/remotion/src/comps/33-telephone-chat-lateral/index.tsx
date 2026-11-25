import React from 'react';
import {AbsoluteFill, Easing, interpolate, useCurrentFrame} from '../../shared/rt';
import {siClaude} from 'simple-icons';
import {INTER} from '../../shared/fonts';
import {SfxTrack, SfxCue} from '../../shared/Sfx';

// 33 : écran mobile Claude à droite du speaker, message du soir.
// Plage de référence 514,68 s à 523,66 s (269 images).
export const meta = {id: '33-telephone-chat-lateral', durationInFrames: 269, fps: 30, defaultProps: {showPlate: true},
  occurrences: [{ref: [514.68, 523.66], from: 0, durationInFrames: 269, mode: 'overlay'}],
};

const BLUE = '#1E8BFF';
const t0 = {shade: [1.7, 2.25], panel: [2.0, 2.65], dots: 2.3, msg: [4.4, 4.6]};

const Star: React.FC<{s: number}> = ({s}) => (
  <svg width={s} height={s} viewBox="0 0 24 24">
    <path d={siClaude.path} fill="#E07A5F" />
  </svg>
);

const LINES = [
  'Bonsoir. Voici ta journée de demain :',
  '',
  '• 8 h 30 : closing avec les LP',
  '• 11 h 00 : point CEO hebdo, Portfolio Co. n° 3',
  '• 13 h 30 : revue de term sheet, cible d’acquisition',
  '• 16 h 00 : enregistrement du podcast',
  '',
  '2 e-mails urgents de ton CFO. Vol privé',
  'confirmé, jeudi 6 h 00.',
];

export default function TelephoneChatLateral({showPlate = true}: {showPlate?: boolean}) {
  const f = useCurrentFrame();
  const t = f / 30;
  const cl = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
  const shade = interpolate(t, t0.shade, [0, 1], {...cl, easing: Easing.inOut(Easing.quad)});
  const p = interpolate(t, t0.panel, [0, 1], cl);
  const msg = interpolate(t, t0.msg, [0, 1], cl);
  const dotsOn = t >= t0.dots ? interpolate(t, [t0.msg[0] - 0.2, t0.msg[0]], [1, 0], cl) : 0;

  // panneau relevé à 519,5 s : x 1151-1682, y 51-1023
  const L = 1151, TOP = 51, PW = 531, PH = 972;
  return (
    <AbsoluteFill style={{fontFamily: INTER}}>
      <SfxTrack cues={cuesExportees} />
      {/* speaker retiré : fond neutre en aperçu, transparent en alpha */}
      {showPlate ? <AbsoluteFill style={{background: '#0E0E10'}} /> : null}
      {/* assombrissement à droite */}
      <AbsoluteFill
        style={{
          opacity: shade,
          background: 'linear-gradient(90deg, rgba(0,0,0,0) 45%, rgba(0,0,0,0.55) 62%, rgba(0,0,0,0.9) 82%, #000 100%)',
        }}
      />
      <div
        style={{
          position: 'absolute',
          left: L,
          top: TOP,
          width: PW,
          height: PH,
          opacity: p,
          filter: `blur(${(1 - p) * 6}px)`,
          transform: `translateY(${(1 - p) * 16}px) scale(${1 + (1 - p) * 0.01})`,
          borderRadius: 24,
          border: '1.5px solid rgba(235,235,240,0.75)',
          background: '#1A1A1A',
          overflow: 'hidden',
          boxShadow: '0 20px 60px rgba(0,0,0,0.5)',
        }}
      >
        {/* en-tête */}
        <div style={{position: 'absolute', left: 0, top: 0, width: PW, height: 84, background: '#1D1D1D', borderBottom: '1px solid #2A2A2A'}} />
        <svg style={{position: 'absolute', left: 17, top: 31}} width={18} height={24} viewBox="0 0 18 24">
          <path d="M13 3L4 12l9 9" stroke={BLUE} strokeWidth={2.6} fill="none" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
        <div style={{position: 'absolute', left: 48, top: 23}}>
          <Star s={42} />
        </div>
        <div style={{position: 'absolute', left: 104, top: 26, color: '#fff', fontSize: 17, fontWeight: 600}}>Claude</div>
        <div style={{position: 'absolute', left: 105, top: 47, color: '#7C7C80', fontSize: 11}}>Assistant IA</div>
        <svg style={{position: 'absolute', left: 452, top: 31}} width={24} height={24} viewBox="0 0 24 24">
          <path d="M5 3.5h3.2l1.6 4.2-2 1.4a11 11 0 006 6l1.4-2 4.3 1.6v3.2A2 2 0 0117.4 20 15 15 0 013 5.6 2 2 0 015 3.5z" fill="none" stroke={BLUE} strokeWidth={1.9} strokeLinejoin="round" />
        </svg>
        {[0, 1, 2].map((i) => (
          <div key={i} style={{position: 'absolute', left: 493 + i * 6.5, top: 42, width: 4, height: 4, borderRadius: 2, background: BLUE}} />
        ))}

        {/* indicateur de frappe */}
        {dotsOn > 0 ? (
          <div style={{opacity: dotsOn}}>
            <div style={{position: 'absolute', left: 25, top: 849 + 0}}>
              <Star s={36} />
            </div>
            <div style={{position: 'absolute', left: 77, top: 844, width: 72, height: 38, borderRadius: 19, background: '#2A292E'}}>
              {[0, 1, 2].map((i) => {
                const ph = ((t - t0.dots) * 30) / 18 * Math.PI * 2 - i * 1.1;
                const lift = Math.max(0, Math.sin(ph)) * 4;
                const a = 0.45 + Math.max(0, Math.sin(ph)) * 0.45;
                return (
                  <div
                    key={i}
                    style={{position: 'absolute', left: 21 + i * 14, top: 15 - lift, width: 8, height: 8, borderRadius: 4, background: `rgba(200,200,205,${a})`}}
                  />
                );
              })}
            </div>
          </div>
        ) : null}

        {/* message */}
        {msg > 0 ? (
          <div style={{opacity: msg}}>
            <div style={{position: 'absolute', left: 24, top: 634}}>
              <Star s={36} />
            </div>
            <div style={{position: 'absolute', left: 77, top: 630, width: 408, height: 244, borderRadius: 16, background: '#29282D'}}>
              {LINES.map((l, i) => (
                <div key={i} style={{position: 'absolute', left: 17, top: 16 + i * 24, color: '#E4E4E6', fontSize: 14.6, whiteSpace: 'nowrap'}}>
                  {l}
                </div>
              ))}
            </div>
            <div style={{position: 'absolute', left: 79, top: 880, color: '#5E5E62', fontSize: 9}}>20:00 · Distribué</div>
          </div>
        ) : null}

        {/* barre de saisie */}
        <div style={{position: 'absolute', left: 0, top: 905, width: PW, height: 1, background: '#2A2A2A'}} />
        <svg style={{position: 'absolute', left: 17, top: 928}} width={24} height={24} viewBox="0 0 24 24">
          <circle cx={12} cy={12} r={10} fill="none" stroke="#8A8A8E" strokeWidth={1.6} />
          <path d="M12 7v10M7 12h10" stroke="#8A8A8E" strokeWidth={1.6} strokeLinecap="round" />
        </svg>
        <div style={{position: 'absolute', left: 52, top: 922, width: 375, height: 37, borderRadius: 19, background: '#29282B'}}>
          <div style={{position: 'absolute', left: 17, top: 10, color: '#6E6E73', fontSize: 13}}>Message</div>
        </div>
        <svg style={{position: 'absolute', left: 438, top: 928}} width={24} height={24} viewBox="0 0 24 24">
          <path d="M12 3a3 3 0 00-3 3v6a3 3 0 006 0V6a3 3 0 00-3-3z M6 11a6 6 0 0012 0 M12 17v4" stroke="#8A8A8E" strokeWidth={1.7} fill="none" strokeLinecap="round" />
        </svg>
        <div style={{position: 'absolute', left: 471, top: 919, width: 42, height: 42, borderRadius: 21, background: '#00A1FC', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
          <svg width={20} height={20} viewBox="0 0 24 24">
            <path d="M12 19V5M6 11l6-6 6 6" stroke="#fff" strokeWidth={2.6} fill="none" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>
      </div>
    </AbsoluteFill>
  );
}

// Signaux sonores exportés pour la bibliothèque (cloud/cues_globaux.py).
const cuesExportees: SfxCue[] = [
        {frame: 69, name: 'grave-apparition'}, // écran mobile visible
        {frame: 135, name: 'notification'}, // message du soir
      ];
export const cues = cuesExportees;
