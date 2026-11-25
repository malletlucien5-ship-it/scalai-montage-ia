import React from 'react';
import {AbsoluteFill, Easing, Img, interpolate, staticFile, useCurrentFrame} from '../../shared/rt';
import {siClaude, siOpenai} from 'simple-icons';
import {INTER_L} from '../../shared/localFonts';
import {Plate} from '../../shared/Plate';
import {SfxTrack, SfxCue} from '../../shared/Sfx';

// d221 : carte vidéo YouTube en haut à droite (vignette + titre + durée).
// Réf. : apparition 1009,2 s (flou + fondu + montée ~40 px, ~12 images), coupe franche 1013,17 s.
// Géométrie à 1011,0 s (1920x1080) : vignette x 1170..1865, y 93..484 (695 x 391, rayon 16),
//   titre 2 lignes à x 1170, lignes centrées ~530 et ~573, menu « ⋮ » à x 1845.
// Cible : « J'avais même fait des vidéos entières pour apprendre aux gens comment migrer d'un outil à un autre. »
//   apparition sur « J'avais » (1080,99 s), fin après « autre. » (1084,17 s).
const FPS = 30;
const AT = 1081.0;
const END = 1084.3;
const DUR = Math.round((END - AT) * FPS);
const IN = 12;

const TH = {x: 1170, y: 93, w: 695, h: 391};

// Tuile Claude orange qui s'écrase sur le logo ChatGPT fendu.
const Smash: React.FC = () => (
  <svg width={TH.w} height={TH.h} viewBox={`0 0 ${TH.w} ${TH.h}`} style={{position: 'absolute', inset: 0}}>
    <defs>
      <filter id="d221dust" x="-50%" y="-50%" width="200%" height="200%">
        <feGaussianBlur stdDeviation="14" />
      </filter>
      <filter id="d221soft" x="-50%" y="-50%" width="200%" height="200%">
        <feGaussianBlur stdDeviation="3" />
      </filter>
      <linearGradient id="d221green" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stopColor="#5ED3A8" />
        <stop offset="0.5" stopColor="#1FA878" />
        <stop offset="1" stopColor="#006941" />
      </linearGradient>
      <linearGradient id="d221orange" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0" stopColor="#FF9A3C" />
        <stop offset="0.5" stopColor="#F2641E" />
        <stop offset="1" stopColor="#C8380F" />
      </linearGradient>
    </defs>
    {/* poussière */}
    <g filter="url(#d221dust)" opacity={0.9}>
      <ellipse cx={380} cy={185} rx={80} ry={55} fill="#cfcfcf" />
      <ellipse cx={440} cy={120} rx={55} ry={45} fill="#dedede" />
      <ellipse cx={330} cy={225} rx={60} ry={30} fill="#d4d4d4" />
      <ellipse cx={600} cy={215} rx={60} ry={28} fill="#dadada" />
    </g>
    {/* fissures au sol */}
    <g stroke="#3a3a3a" strokeWidth={1.6} fill="none" opacity={0.75}>
      <path d="M300 250 L360 244 L400 256 L452 248 L520 262 L590 252 L660 266 L690 262" />
      <path d="M330 272 L390 262 L440 276 L500 268 L560 282 L630 274" />
      <path d="M400 256 L392 280 M452 248 L470 285 M520 262 L512 288 M590 252 L612 280 M360 244 L340 268" />
    </g>
    {/* éclats */}
    {[
      [356, 78, 7], [330, 120, 5], [300, 160, 4], [620, 150, 6], [655, 175, 9], [640, 110, 4], [470, 60, 3], [560, 240, 7], [610, 235, 8], [470, 245, 5],
    ].map(([x, y, r], i) => (
      <circle key={i} cx={x} cy={y} r={r} fill={i % 3 ? '#555' : '#9a9a9a'} />
    ))}
    {/* logo ChatGPT : tuile verte fendue, vue en perspective */}
    <g transform="translate(490 205) scale(1 0.62) rotate(-8)">
      <rect x={-78} y={-66} width={156} height={132} rx={34} fill="#004d30" transform="translate(0 16)" />
      <rect x={-78} y={-66} width={156} height={132} rx={34} fill="url(#d221green)" />
      <g transform="translate(-50 -50) scale(4.2)" opacity={0.95}>
        <path d={siOpenai.path} fill="#dff5ea" />
      </g>
      <path d="M-20 -66 L-8 -30 L-26 0 L-6 30 L-14 66" stroke="#0a3a25" strokeWidth={4} fill="none" />
      <path d="M-8 -30 L30 -18 L52 -40 M-26 0 L-60 12" stroke="#0a3a25" strokeWidth={3} fill="none" />
    </g>
    {/* tuile Claude orange qui s'abat */}
    <g transform="translate(552 108) rotate(14) scale(0.88)">
      <rect x={-88} y={-80} width={176} height={176} rx={34} fill="#8a2408" transform="translate(6 10)" filter="url(#d221soft)" />
      <rect x={-88} y={-88} width={176} height={176} rx={34} fill="url(#d221orange)" stroke="#ffb27a" strokeWidth={3} />
      <rect x={-76} y={-80} width={152} height={50} rx={24} fill="rgba(255,255,255,0.22)" />
      <g transform="translate(-56 -56) scale(4.66)">
        <path d={siClaude.path} fill="#ffffff" />
      </g>
    </g>
  </svg>
);

const Carte: React.FC = () => (
  <>
    <div
      style={{
        position: 'absolute',
        left: TH.x,
        top: TH.y,
        width: TH.w,
        height: TH.h,
        borderRadius: 16,
        overflow: 'hidden',
        background: 'linear-gradient(180deg, #ffffff 0%, #f7f7f7 60%, #eeeeee 100%)',
      }}
    >
      {/* photo de Lucien à gauche, fondue dans le fond blanc */}
      <div
        style={{
          position: 'absolute',
          left: 0,
          top: 0,
          width: 380,
          height: TH.h,
          overflow: 'hidden',
          WebkitMaskImage: 'linear-gradient(90deg, #000 70%, transparent 100%)',
          maskImage: 'linear-gradient(90deg, #000 70%, transparent 100%)',
        }}
      >
        <Img src={staticFile('lucien-photo.png')} style={{position: 'absolute', left: -150, top: -50, width: 690, height: 461}} />
      </div>
      <Smash />
      {/* bandeau noir du titre */}
      <div style={{position: 'absolute', left: 0, right: 0, top: 250, bottom: 0, background: 'linear-gradient(180deg, rgba(3,5,8,0) 0%, rgba(3,5,8,0.85) 30%, #030508 55%)'}} />
      <div
        style={{
          position: 'absolute',
          left: 0,
          width: TH.w,
          top: 282,
          height: 80,
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          fontFamily: INTER_L,
          fontWeight: 900,
          fontSize: 78,
          letterSpacing: -3,
          lineHeight: 1,
          color: '#fff',
          whiteSpace: 'nowrap',
        }}
      >
        <div style={{display: 'flex', alignItems: 'center', transform: 'scaleX(0.84)'}}>
          <span style={{textShadow: '0 3px 6px rgba(0,0,0,0.6)'}}>CHATGPT EST</span>
          <span style={{marginLeft: 16, background: '#FF0F0F', padding: '4px 12px 2px 10px', borderRadius: 2}}>MORT</span>
        </div>
      </div>
      {/* durée */}
      <div
        style={{
          position: 'absolute',
          right: 10,
          top: 347,
          height: 33,
          padding: '0 8px',
          borderRadius: 6,
          background: 'rgba(0,0,0,0.82)',
          color: '#fff',
          fontFamily: INTER_L,
          fontWeight: 600,
          fontSize: 23,
          lineHeight: '33px',
        }}
      >
        16:07
      </div>
      {/* barre de lecture */}
      <div style={{position: 'absolute', left: 0, right: 0, bottom: 0, height: 6, background: '#70706e'}} />
      <div style={{position: 'absolute', left: 0, width: 70, bottom: 0, height: 6, background: '#FF172D'}} />
    </div>
    <div
      style={{
        position: 'absolute',
        left: TH.x,
        top: 510,
        width: 660,
        fontFamily: INTER_L,
        fontWeight: 600,
        fontSize: 27.5,
        lineHeight: '43px',
        letterSpacing: -0.2,
        color: '#fff',
        textShadow: '0 1px 4px rgba(0,0,0,0.5)',
        whiteSpace: 'nowrap',
      }}
    >
      Pourquoi je suis passé de ChatGPT à Claude
      <br />
      (sans rien perdre)
    </div>
    <div style={{position: 'absolute', left: 1840, top: 520}}>
      {[0, 1, 2].map((i) => (
        <div key={i} style={{width: 7, height: 7, borderRadius: 4, background: '#fff', marginBottom: 5}} />
      ))}
    </div>
  </>
);

const CarteYoutube: React.FC<{showPlate?: boolean}> = ({showPlate = true}) => {
  const f = useCurrentFrame();
  const p = interpolate(f, [0, IN], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic)});
  return (
    <AbsoluteFill style={{overflow: 'hidden'}}>
      <Plate show={showPlate} />
      <AbsoluteFill
        style={{
          opacity: p,
          transform: `translateY(${(40 * (1 - p)).toFixed(2)}px)`,
          filter: p < 1 ? `blur(${((1 - p) * 18).toFixed(2)}px)` : undefined,
        }}
      >
        <Carte />
      </AbsoluteFill>
      <SfxTrack cues={cuesExportees} />
    </AbsoluteFill>
  );
};

export const meta = {
  id: 'd221-carte-youtube',
  fps: FPS,
  durationInFrames: DUR,
  defaultProps: {showPlate: true},
  occurrences: [{ref: [1009.2, 1013.17] as [number, number], at: AT, from: 0, durationInFrames: DUR, mode: 'plein' as const}],
};
export default CarteYoutube;

// Signaux sonores exportés pour la bibliothèque (cloud/cues_globaux.py).
const cuesExportees: SfxCue[] = [{frame: 1, name: 'grave-apparition'}];
export const cues = cuesExportees;
