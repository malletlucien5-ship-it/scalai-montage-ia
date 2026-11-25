import React from 'react';
import {SfxTrack, SfxCue} from '../../shared/Sfx';
import {AbsoluteFill, Easing, interpolate, useCurrentFrame} from '../../shared/rt';
import {INTER} from '../../shared/fonts';

// Réf 790.29 à 795.16 s. Carte « Agent principal » puis 4 sous-agents reliés.
export const meta = {
  id: '43-organigramme-agent',
  durationInFrames: 146,
  fps: 30,
  occurrences: [{ref: [790.29, 795.16] as [number, number], from: 0, durationInFrames: 146, mode: 'plein' as const}],
};

const FPS = 30;
const ease = Easing.out(Easing.cubic);
const ramp = (t: number, a: number, b: number, e = ease) =>
  interpolate(t, [a, b], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: e});

const SUB_X = [345, 755, 1165, 1575];
const SW = 326;
const SH = 240;
const SY = 678;
const BUS_Y = 631;

const SUBS = [
  {name: 'Agent Recherche', tags: 'WEB · DOCS · DONNÉES', icon: 'people'},
  {name: 'Agent Contenu', tags: 'RÉDIGER · ÉDITER · FORMATER', icon: 'screen'},
  {name: 'Agent Analyse', tags: 'SUIVI · RAPPORTS · INSIGHTS', icon: 'target'},
  {name: 'Agent Action', tags: 'EXÉCUTER · AUTOMATISER', icon: 'grid'},
];

// icônes relevées au pixel sur l'original (coordonnées écran dans une case de 80 px, trait 2 px)
const SubIcon: React.FC<{k: string; color: string}> = ({k, color}) => {
  const p = {fill: 'none', stroke: color, strokeWidth: 2, strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const};
  return (
    <svg width={80} height={80} viewBox="0 0 80 80" style={{position: 'absolute', left: 0, top: 0}}>
      {k === 'people' && (
        <g {...p}>
          <circle cx={31.8} cy={32.5} r={5.4} />
          <path d="M24 52.5 C24 47.5 27.5 44.5 32.6 44.5 C37.7 44.5 41.2 47.5 41.2 52.5" />
          <line x1={44.8} y1={32.5} x2={55} y2={32.5} />
          <line x1={44.8} y1={39.3} x2={52.5} y2={39.3} />
          <line x1={44.8} y1={46} x2={49.5} y2={46} />
        </g>
      )}
      {k === 'screen' && (
        <g {...p}>
          <rect x={24} y={27.6} width={31.5} height={18.8} rx={3} />
          <line x1={30.2} y1={36.6} x2={38.6} y2={36.6} />
          <line x1={30.2} y1={41.6} x2={41.2} y2={41.6} />
          <line x1={31.4} y1={46.5} x2={31.4} y2={51.8} />
          <line x1={48} y1={46.5} x2={48} y2={51.8} />
          <line x1={26.4} y1={52.4} x2={52.4} y2={52.4} />
        </g>
      )}
      {k === 'target' && (
        <g {...p}>
          <circle cx={40} cy={40.5} r={7.4} />
          <circle cx={40} cy={40.5} r={3.1} fill={color} stroke="none" opacity={0.85} />
          <line x1={40} y1={25} x2={40} y2={32.6} />
          <line x1={40} y1={48.4} x2={40} y2={55.6} />
          <line x1={24.6} y1={40.5} x2={32.4} y2={40.5} />
          <line x1={47.6} y1={40.5} x2={55.4} y2={40.5} />
        </g>
      )}
      {k === 'grid' && (
        <g {...p}>
          <rect x={26.3} y={26.3} width={11.7} height={11.7} rx={2.4} />
          <rect x={43} y={26.3} width={11.5} height={11.7} rx={2.4} />
          <rect x={26.3} y={42.5} width={11.7} height={11.5} rx={2.4} />
          <rect x={43} y={42.5} width={11.5} height={11.5} rx={2.4} />
        </g>
      )}
    </svg>
  );
};

// soleil de l'agent principal : anneau r 12,3, point plein r 5, 8 rayons de r 13 à r 21
const MainIcon: React.FC<{color: string}> = ({color}) => (
  <svg width={114} height={112} viewBox="0 0 114 112" style={{position: 'absolute', left: 0, top: 0}}>
    <g fill="none" stroke={color} strokeWidth={2.2} strokeLinecap="round">
      <circle cx={56.4} cy={55.6} r={12.3} />
      {Array.from({length: 8}).map((_, i) => {
        const a = (i * Math.PI) / 4;
        return <line key={i} x1={56.4 + Math.cos(a) * 13.6} y1={55.6 + Math.sin(a) * 13.6} x2={56.4 + Math.cos(a) * 21} y2={55.6 + Math.sin(a) * 21} />;
      })}
    </g>
    <circle cx={56.4} cy={55.6} r={5.2} fill="#a89ff2" />
  </svg>
);

// bruitages calés sur les images où chaque élément devient visible (SFX-REGLES.md)
const CUES: SfxCue[] = [
  {frame: 6, name: 'grave-apparition'}, // titre « Ton agent principal »
  {frame: 26, name: 'whoosh-transition'}, // carte principale
  {frame: 79, name: 'grave-apparition'}, // sous-agent 01
  {frame: 88, name: 'grave-apparition'}, // sous-agent 02
  {frame: 97, name: 'grave-apparition'}, // sous-agent 03
  {frame: 106, name: 'grave-apparition'}, // sous-agent 04
];

const Comp: React.FC = () => {
  const f = useCurrentFrame();
  const t = f / FPS;
  const bg = ramp(t, 0, 0.25);
  const title = ramp(t, 0.05, 0.6, Easing.inOut(Easing.quad));
  const main = ramp(t, 0.8, 1.2);
  const stem = ramp(t, 1.85, 2.1, Easing.inOut(Easing.quad));
  const bus = ramp(t, 2.15, 2.55, Easing.inOut(Easing.quad));

  return (
    <AbsoluteFill style={{background: '#000', fontFamily: INTER}}>
      <AbsoluteFill
        style={{
          opacity: bg,
          background:
            'radial-gradient(ellipse 1100px 560px at 50% 58%, #031845 0%, #021034 30%, #010a22 60%, #000510 85%, #000105 100%)',
        }}
      />
      {/* titre */}
      <div
        style={{
          position: 'absolute',
          left: 0,
          right: 0,
          top: 128,
          textAlign: 'center',
          fontSize: 82,
          fontWeight: 700,
          letterSpacing: -1.5,
          color: '#f7fbff',
          textShadow: '0 0 30px rgba(170,140,255,0.28)',
          opacity: title,
          transform: `translateY(${(1 - title) * -14}px)`,
        }}
      >
        Ton <span style={{color: '#a980fb', textShadow: '0 0 26px rgba(160,110,255,0.75)'}}>agent</span> principal
      </div>
      {/* carte principale */}
      <div
        style={{
          position: 'absolute',
          left: 785,
          top: 298,
          width: 350,
          height: 270,
          borderRadius: 30,
          boxSizing: 'border-box',
          background: 'linear-gradient(180deg, #111a4f 0%, #0d1a4e 100%)',
          border: '2px solid #3c42a0',
          boxShadow: '0 0 60px rgba(70,60,220,0.35), 0 0 22px rgba(90,80,255,0.25)',
          opacity: main,
          transform: `scale(${0.94 + 0.06 * main})`,
        }}
      >
        <div
          style={{
            position: 'absolute',
            left: 118,
            top: 37,
            width: 114,
            height: 112,
            borderRadius: 22,
            background: '#2b2677',
            boxShadow: '0 0 20px rgba(90,70,220,0.35)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <MainIcon color="#b8b3ff" />
        </div>
        <div style={{position: 'absolute', left: 0, right: 0, top: 166, textAlign: 'center', fontSize: 26, fontWeight: 700, color: '#ebf3ff'}}>Agent principal</div>
        <div style={{position: 'absolute', left: 0, right: 0, top: 216, textAlign: 'center', fontSize: 15.5, fontWeight: 500, letterSpacing: 2.6, color: '#6a6cb4'}}>
          ORCHESTRATEUR
        </div>
      </div>
      {/* tige et bus */}
      <div style={{position: 'absolute', left: 959, top: 568, width: 2, height: (BUS_Y - 568) * stem, background: '#44478c'}} />
      <div
        style={{
          position: 'absolute',
          left: 960 - (960 - 181) * bus,
          top: BUS_Y - 1,
          width: (1737 - 181) * bus,
          height: 2,
          background: '#2d3570',
          boxShadow: '0 0 6px rgba(70,80,200,0.35)',
          opacity: stem >= 1 ? 1 : 0,
        }}
      />
      {SUBS.map((s, i) => {
        const st = 2.72 + i * 0.3;
        const drop = ramp(t, st - 0.12, st + 0.05);
        const card = ramp(t, st, st + 0.3);
        const cx = SUB_X[i];
        return (
          <React.Fragment key={i}>
            <div
              style={{
                position: 'absolute',
                left: cx - SW / 2,
                top: SY,
                width: SW,
                height: SH,
                borderRadius: 24,
                boxSizing: 'border-box',
                background: 'linear-gradient(180deg, #070d38 0%, #050722 100%)',
                border: '1.5px solid #141b4e',
                boxShadow: '0 0 40px rgba(40,40,160,0.18)',
                opacity: card,
                transform: `translateY(${(1 - card) * 18}px)`,
              }}
            >
              <div
                style={{
                  position: 'absolute',
                  left: SW / 2 - 40,
                  top: 57,
                  width: 80,
                  height: 80,
                  borderRadius: 16,
                  background: '#1d175a',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <SubIcon k={s.icon} color="#b2acef" />
              </div>
              <div style={{position: 'absolute', left: 0, right: 0, top: 152, textAlign: 'center', fontSize: 20.5, fontWeight: 700, color: '#e3e8fe'}}>{s.name}</div>
              <div style={{position: 'absolute', left: 0, right: 0, top: 193, textAlign: 'center', fontSize: 14, fontWeight: 500, letterSpacing: 2, color: '#4a4c78'}}>{s.tags}</div>
            </div>
            <div style={{position: 'absolute', left: cx - 1, top: BUS_Y, width: 2, height: 34 * drop, background: '#3a3f86'}} />
            <div
              style={{
                position: 'absolute',
                left: cx - 18,
                top: 683 - 18,
                width: 36,
                height: 36,
                borderRadius: 18,
                background: '#7a58e8',
                boxShadow: '0 0 14px rgba(130,90,255,0.7)',
                color: '#fff',
                fontSize: 13.5,
                fontWeight: 700,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                opacity: drop,
                transform: `scale(${0.6 + 0.4 * drop})`,
              }}
            >
              0{i + 1}
            </div>
          </React.Fragment>
        );
      })}
    <SfxTrack cues={CUES} />
    </AbsoluteFill>
  );
};

export default Comp;

// Signaux sonores exportés pour la bibliothèque (cloud/cues_globaux.py).
export const cues = CUES;
