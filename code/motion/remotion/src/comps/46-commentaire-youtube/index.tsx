import React from 'react';
import {AbsoluteFill, Easing, Img, interpolate, staticFile, useCurrentFrame} from '../../shared/rt';
import {loadFont} from '@remotion/google-fonts/Roboto';
import {SfxTrack, SfxCue} from '../../shared/Sfx';

// 46 : vignette vidéo en haut, champ de commentaire YouTube qui se tape.
// Plage de référence 881,15 s à 883,58 s (73 images).
export const meta = {id: '46-commentaire-youtube', durationInFrames: 73, fps: 30, defaultProps: {showPlate: true},
  occurrences: [{ref: [881.15, 883.58], from: 0, durationInFrames: 73, mode: 'overlay'}],
};

const ROBOTO = loadFont('normal', {weights: ['400', '500', '700']}).fontFamily;
// Chemin « evenodd » : tout l'écran moins un rectangle arrondi (trou transparent en alpha)
const holePath = (x: number, y: number, w: number, h: number, r: number) =>
  `path(evenodd, 'M0 0H1920V1080H0Z M${x + r} ${y}H${x + w - r}A${r} ${r} 0 0 1 ${x + w} ${y + r}V${y + h - r}A${r} ${r} 0 0 1 ${x + w - r} ${y + h}H${x + r}A${r} ${r} 0 0 1 ${x} ${y + h - r}V${y + r}A${r} ${r} 0 0 1 ${x + r} ${y}Z')`;

const cl = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const TEXT = 'Quel outil vas-tu utiliser pendant les 30 prochains jours ?';

export default function CommentaireYoutube({showPlate = true}: {showPlate?: boolean}) {
  const f = useCurrentFrame();
  const t = f / 30;
  const p = interpolate(t, [0, 0.5], [0, 1], {...cl, easing: Easing.out(Easing.quad)});
  const op = interpolate(t, [0, 0.12], [0, 1], cl);
  const n = Math.floor(interpolate(t, [0.08, 0.35, 1.0, 1.9], [0, 0.19, 0.62, 1], cl) * TEXT.length);

  return (
    <AbsoluteFill style={{fontFamily: ROBOTO}}>
      <SfxTrack cues={cuesExportees /* commentaire (0,1 s à 1,9 s) */} />
      <Img src={staticFile('46/bg.jpg')} style={{position: 'absolute', width: 1920, height: 1080, clipPath: showPlate ? undefined : holePath(370, 65, 1132, 603, 18)}} />

      {/* vignette vidéo */}
      <div
        style={{
          position: 'absolute',
          left: 370,
          top: 65,
          width: 1132,
          height: 603,
          borderRadius: 18,
          overflow: 'hidden',
          border: '1.5px solid rgba(235,225,215,0.75)',
          background: showPlate ? '#1A1A1C' : 'transparent',
        }}
      >
        <Img src={staticFile('46/speaker.jpg')} style={{width: '100%', height: '100%', objectFit: 'cover', objectPosition: '50% 50%'}} />
      </div>

      {/* champ de commentaire */}
      <div
        style={{
          position: 'absolute',
          left: 46,
          top: 731,
          width: 1827,
          height: 285,
          borderRadius: 18,
          background: `rgba(11,11,12,${0.45 + 0.55 * p})`,
          border: '1.5px solid rgba(205,210,220,0.72)',
          opacity: op,
          filter: `blur(${(1 - p) * 14}px)`,
          transform: `scale(${1 + (1 - p) * 0.03})`,
        }}
      >
        <Img
          src={staticFile('lucien-rond.png')}
          style={{position: 'absolute', left: 52, top: 57, width: 94, height: 94, borderRadius: 47, objectFit: 'cover'}}
        />
        <div style={{position: 'absolute', left: 183, top: 60, fontSize: 30, color: '#F1F1F1', whiteSpace: 'pre'}}>
          {TEXT.slice(0, n)}
          {n < TEXT.length ? <span style={{display: 'inline-block', width: 2, height: 32, background: '#F1F1F1', verticalAlign: 'middle', marginLeft: 1}} /> : null}
        </div>
        <div style={{position: 'absolute', left: 183, top: 112, width: 1609, height: 3, background: '#F1F1F1'}} />
        <div
          style={{
            position: 'absolute',
            left: 164,
            top: 130,
            width: 84,
            height: 84,
            borderRadius: 42,
            background: '#272727',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <svg width={52} height={52} viewBox="0 0 24 24" fill="none" stroke="#F1F1F1" strokeWidth={1.6} strokeLinecap="round">
            <circle cx={12} cy={12} r={9} />
            <path d="M7.5 9.5l2 1-2 1M16.5 9.5l-2 1 2 1" />
            <path d="M7.5 14h9a4.5 4.5 0 01-9 0z" fill="#F1F1F1" />
          </svg>
        </div>
        <div style={{position: 'absolute', left: 1369, width: 200, top: 152, textAlign: 'center', fontSize: 30, fontWeight: 700, color: '#F1F1F1'}}>
          Annuler
        </div>
        <div
          style={{
            position: 'absolute',
            left: 1575,
            top: 131,
            width: 217,
            height: 83,
            borderRadius: 42,
            background: '#3EA6FF',
            color: '#0F0F0F',
            fontSize: 30,
            fontWeight: 500,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          Commenter
        </div>
      </div>
    </AbsoluteFill>
  );
}

// Signaux sonores exportés pour la bibliothèque (cloud/cues_globaux.py).
const cuesExportees: SfxCue[] = [{frame: 3, name: 'frappe-clavier', durationInFrames: 54}];
export const cues = cuesExportees;
