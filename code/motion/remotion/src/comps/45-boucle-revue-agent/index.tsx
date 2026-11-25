import React from 'react';
import {AbsoluteFill, Easing, Img, interpolate, staticFile, useCurrentFrame} from '../../shared/rt';
import {INTER} from '../../shared/fonts';
import {SfxTrack, SfxCue} from '../../shared/Sfx';

// 45 : speaker en carte à gauche, fenêtre « Boucle d'agent IA », notes de revue qui s'écrivent.
// Plage de référence 837,77 s à 848,08 s (309 images).
export const meta = {id: '45-boucle-revue-agent', durationInFrames: 309, fps: 30, defaultProps: {showPlate: true},
  occurrences: [{ref: [837.77, 848.08], from: 0, durationInFrames: 309, mode: 'overlay'}],
};

// Chemin « evenodd » : tout l'écran moins un rectangle arrondi (trou transparent en alpha)
const holePath = (x: number, y: number, w: number, h: number, r: number) =>
  `path(evenodd, 'M0 0H1920V1080H0Z M${x + r} ${y}H${x + w - r}A${r} ${r} 0 0 1 ${x + w} ${y + r}V${y + h - r}A${r} ${r} 0 0 1 ${x + w - r} ${y + h}H${x + r}A${r} ${r} 0 0 1 ${x} ${y + h - r}V${y + r}A${r} ${r} 0 0 1 ${x + r} ${y}Z')`;

const cl = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

const B1 = 'Relis ce brouillon d’e-mail commercial. Trouve tous les points faibles.';
const NOTES_TITLE = 'Notes sur ton brouillon :';
const NOTES = [
  'L’accroche est générique. Aucun hook, aucune tension.',
  'La proposition de valeur arrive ligne 6. Remonte-la ligne 1.',
  'Le CTA dit « cliquez ici » : trop vague, aucune urgence.',
  'Le paragraphe 3 passe des bénéfices aux fonctionnalités.',
  'L’objet ne crée aucune curiosité. Le taux d’ouverture va chuter.',
];
const B3 = 'Je réécris avec tes notes. Nouveau brouillon dans 30 secondes.';

// Texte qui apparaît mot par mot (chaque mot passe de faible à plein en 0,12 s)
const Words: React.FC<{text: string; t: number; start: number; per: number; offset?: number}> = ({text, t, start, per, offset = 0}) => {
  const words = text.split(' ');
  return (
    <>
      {words.map((w, i) => {
        const a = start + (i + offset) * per;
        const o = t < a ? 0 : interpolate(t, [a, a + 0.12], [0.35, 1], cl);
        return (
          <span key={i} style={{opacity: o}}>
            {w}
            {i < words.length - 1 ? ' ' : ''}
          </span>
        );
      })}
    </>
  );
};

const UserIcon: React.FC<{x: number; y: number; op: number}> = ({x, y, op}) => (
  <div
    style={{
      position: 'absolute',
      left: x - 27,
      top: y - 27,
      width: 54,
      height: 54,
      borderRadius: 27,
      background: '#0B274E',
      border: '1px solid #1C416F',
      opacity: op,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
    }}
  >
    <svg width={26} height={26} viewBox="0 0 24 24" fill="none" stroke="#3FA9E6" strokeWidth={1.7} strokeLinecap="round">
      <circle cx={12} cy={8} r={4} />
      <path d="M4.5 20.5a7.5 7.5 0 0115 0" />
    </svg>
  </div>
);

const bubble: React.CSSProperties = {
  position: 'absolute',
  height: 70,
  borderRadius: 16,
  background: '#0E2345',
  border: '1px solid #16305A',
  color: '#E4ECF7',
  fontSize: 17.2,
  fontWeight: 600,
  display: 'flex',
  alignItems: 'center',
  padding: '0 28px',
  whiteSpace: 'nowrap',
  boxSizing: 'border-box',
};

export default function BoucleRevueAgent({showPlate = true}: {showPlate?: boolean}) {
  const f = useCurrentFrame();
  const t = f / 30;
  const card = interpolate(t, [0.03, 0.4], [0, 1], {...cl, easing: Easing.out(Easing.cubic)});
  const b1 = interpolate(t, [0, 0.25], [0, 1], cl);
  const notes = interpolate(t, [2.4, 2.75], [0, 1], cl);
  const b3 = interpolate(t, [8.2, 8.45], [0, 1], cl);

  // mots des notes enchaînés sur une seule horloge
  const perN = 0.075;
  const counts = [NOTES_TITLE, ...NOTES].map((s) => s.split(' ').length);
  const offs = counts.map((_, i) => counts.slice(0, i).reduce((a, b) => a + b, 0));

  return (
    <AbsoluteFill style={{fontFamily: INTER}}>
      <SfxTrack cues={cuesExportees} />
      <Img src={staticFile('45/bg.jpg')} style={{position: 'absolute', width: 1920, height: 1080, clipPath: showPlate ? undefined : holePath(34, 277, 450, 495, 14)}} />

      {/* carte speaker */}
      <div
        style={{
          position: 'absolute',
          left: 34,
          top: 277,
          width: 450,
          height: 495,
          borderRadius: 14,
          overflow: 'hidden',
          border: '1.5px solid rgba(225,228,235,0.7)',
          background: showPlate ? '#1A1A1C' : 'transparent',
          opacity: card,
          filter: `blur(${(1 - card) * 10}px)`,
          transform: `translateX(${(1 - card) * 20}px) scale(${1 + (1 - card) * 0.03})`,
        }}
      >
        <Img src={staticFile('45/speaker.jpg')} style={{width: '100%', height: '100%', objectFit: 'cover', objectPosition: '50% 50%'}} />
      </div>

      {/* fenêtre */}
      <div
        style={{
          position: 'absolute',
          left: 500,
          top: 241,
          width: 1382,
          height: 584,
          borderRadius: 20,
          border: '1.5px solid rgba(215,222,235,0.62)',
          background: '#0F171E',
          overflow: 'hidden',
          boxShadow: '0 20px 60px rgba(0,0,0,0.45)',
        }}
      >
        <div style={{position: 'absolute', left: 0, right: 0, top: 47, height: 1, background: '#1A242E'}} />
        {['#E0443E', '#DEA123', '#1AAB29'].map((c, i) => (
          <div key={c} style={{position: 'absolute', left: 29 + i * 23.5, top: 13, width: 14, height: 14, borderRadius: 7, background: c}} />
        ))}
        <div style={{position: 'absolute', left: 0, right: 0, top: 11, textAlign: 'center', color: '#7F8A97', fontSize: 15.5, fontWeight: 600, letterSpacing: 0.8}}>
          Boucle d’agent IA
        </div>

        {/* message 1 */}
        <UserIcon x={73} y={121} op={b1} />
        <div style={{...bubble, left: 121, top: 93, opacity: b1}}>
          <span>
            <Words text={B1} t={t} start={0.25} per={0.095} />
          </span>
        </div>

        {/* notes du critique */}
        {notes > 0 ? (
          <>
            <div
              style={{
                position: 'absolute',
                left: 1308,
                top: 204,
                width: 54,
                height: 54,
                borderRadius: 27,
                background: '#0B2438',
                border: '1px solid #21486A',
                opacity: interpolate(t, [2.3, 2.5], [0, 1], cl),
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <svg width={28} height={28} viewBox="0 0 24 24" fill="none" stroke="#5CC9EE" strokeWidth={1.6} strokeLinejoin="round">
                <path d="M12 3l2.7 5.6 6.1.8-4.5 4.2 1.1 6-5.4-2.9-5.4 2.9 1.1-6-4.5-4.2 6.1-.8z" />
              </svg>
            </div>
            <div
              style={{
                position: 'absolute',
                right: 1382 - 1287,
                top: 205,
                height: 222,
                borderRadius: 16,
                background: '#0B1530',
                border: '1px solid #1C2F52',
                opacity: notes,
                padding: '23px 28px 0 27px',
                boxSizing: 'border-box',
                color: '#E4ECF7',
                fontSize: 17.2,
                fontWeight: 600,
                whiteSpace: 'nowrap',
              }}
            >
              <div style={{height: 29}}>
                <Words text={NOTES_TITLE} t={t} start={2.75} per={perN} offset={offs[0]} />
              </div>
              <div style={{height: 8}} />
              {NOTES.map((n, i) => {
                const a = 2.75 + offs[i + 1] * perN;
                return (
                  <div key={i} style={{height: 29, opacity: t < a ? 0 : 1}}>
                    <span style={{opacity: t < a ? 0 : interpolate(t, [a, a + 0.12], [0.35, 1], cl)}}>•&nbsp;</span>
                    <Words text={n} t={t} start={2.75} per={perN} offset={offs[i + 1]} />
                  </div>
                );
              })}
            </div>
          </>
        ) : null}

        {/* message 3 */}
        {b3 > 0 ? (
          <>
            <UserIcon x={73} y={495} op={b3} />
            <div style={{...bubble, left: 121, top: 468, opacity: b3}}>
              <span>
                <Words text={B3} t={t} start={8.45} per={0.1} />
              </span>
            </div>
          </>
        ) : null}
      </div>
    </AbsoluteFill>
  );
}

// Signaux sonores exportés pour la bibliothèque (cloud/cues_globaux.py).
const cuesExportees: SfxCue[] = [
        {frame: 0, name: 'whoosh-transition'}, // entrée carte et fenêtre
        {frame: 83, name: 'frappe-clavier', durationInFrames: 121}, // notes de revue (2,75 s à 6,8 s)
      ];
export const cues = cuesExportees;
