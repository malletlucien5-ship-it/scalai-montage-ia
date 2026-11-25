import React from 'react';
import {SfxTrack, SfxCue} from '../../shared/Sfx';
import {AbsoluteFill, Easing, interpolate, spring, useCurrentFrame} from '../../shared/rt';
import {ARIAL_L} from '../../shared/localFonts';
// police de l'original : Helvetica Neue (mesurée)
const INTER = `"Helvetica Neue", Helvetica, Arial, ${ARIAL_L}, sans-serif`;

// Réf 413.65 à 420.62 s. Pipeline de 5 nœuds, coches vertes, validation humaine.
export const meta = {
  id: '30-pipeline-agents',
  durationInFrames: 209,
  fps: 30,
  occurrences: [{ref: [413.65, 420.62] as [number, number], from: 0, durationInFrames: 209, mode: 'plein' as const}],
};

const FPS = 30;
const ease = Easing.out(Easing.cubic);
const ramp = (t: number, a: number, b: number, e = ease) =>
  interpolate(t, [a, b], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: e});

const CX = [289, 624, 960, 1295, 1631];
const NW = 240;
const NH = 172;
const NY = 469; // haut des nœuds
const LINE_Y = 555;

const NODES = [
  {name: 'Agent Recherche', sub: 'Analyse du sujet', icon: 'sun'},
  {name: 'Agent Script', sub: 'Rédaction', icon: 'doc'},
  {name: 'Agent Montage', sub: 'Découpe vidéo', icon: 'video'},
  {name: 'Agent Miniature', sub: 'Design visuel', icon: 'image'},
  {name: 'Validation humaine', sub: 'Approbation finale', icon: 'user'},
];

const Icon: React.FC<{k: string; color: string}> = ({k, color}) => {
  const p = {fill: 'none', stroke: color, strokeWidth: 2, strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const};
  return (
    <svg width={30} height={30} viewBox="0 0 24 24">
      {k === 'sun' && (
        <g {...p}>
          <circle cx={12} cy={12} r={3} />
          {Array.from({length: 8}).map((_, i) => {
            const a = (i * Math.PI) / 4;
            return <line key={i} x1={12 + Math.cos(a) * 6} y1={12 + Math.sin(a) * 6} x2={12 + Math.cos(a) * 9.5} y2={12 + Math.sin(a) * 9.5} />;
          })}
        </g>
      )}
      {k === 'doc' && (
        <g {...p}>
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
          <path d="M14 2v6h6" />
          <line x1={8} y1={13} x2={16} y2={13} />
          <line x1={8} y1={17} x2={16} y2={17} />
        </g>
      )}
      {k === 'video' && (
        <g {...p}>
          <rect x={2} y={6} width={14} height={12} rx={2} />
          <path d="M16 10l6-3.5v11L16 14z" />
        </g>
      )}
      {k === 'image' && (
        <g {...p}>
          <rect x={3} y={3} width={18} height={18} rx={2} />
          <circle cx={9} cy={9} r={2} />
          <path d="M21 15l-5-5L5 21" />
        </g>
      )}
      {k === 'user' && (
        <g {...p}>
          <circle cx={12} cy={8} r={4} />
          <path d="M4 21v-1a6 6 0 0 1 6-6h4a6 6 0 0 1 6 6v1" />
        </g>
      )}
    </svg>
  );
};

const Check: React.FC<{s: number; x: number; y: number}> = ({s, x, y}) => (
  <div
    style={{
      position: 'absolute',
      left: x - 17,
      top: y - 17,
      width: 34,
      height: 34,
      borderRadius: 17,
      background: '#1f9d78',
      boxShadow: '0 0 10px rgba(30,180,130,0.45), 0 2px 6px rgba(0,0,0,0.5)',
      transform: `scale(${s})`,
      opacity: Math.min(1, s * 1.5),
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
    }}
  >
    <svg width={20} height={20} viewBox="0 0 24 24">
      <path d="M5 12.5l4.5 4.5L19 7.5" fill="none" stroke="#fff" strokeWidth={3.2} strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  </div>
);

// bruitages calés sur les images où chaque élément devient visible (SFX-REGLES.md)
const CUES: SfxCue[] = [
  {frame: 0, name: 'whoosh-transition'}, // entrée du plein écran
  {frame: 9, name: 'grave-apparition'}, // nœud 1
  {frame: 29, name: 'grave-apparition'}, // nœud 2
  {frame: 48, name: 'grave-apparition'}, // nœud 3
  {frame: 68, name: 'grave-apparition'}, // nœud 4
  {frame: 87, name: 'grave-apparition'}, // nœud humain
  {frame: 95, name: 'pop'}, // coches 1 et 2 (0,1 s d'écart : un seul son)
  {frame: 101, name: 'pop'}, // coches 3 et 4
  {frame: 123, name: 'notification'}, // panneau « Vidéo prête »
  {frame: 154, name: 'clic'}, // clic sur « Valider »
  {frame: 164, name: 'pop'}, // coche du nœud humain
  {frame: 174, name: 'pop'}, // tous les nœuds s'allument
];

const Comp: React.FC = () => {
  const f = useCurrentFrame();
  const t = f / FPS;

  // poussée caméra lente continue
  const scale = 1 + 0.0132 * (t - 4.85);
  const bg = ramp(t, 0, 0.25);
  const titleO = ramp(t, 0.1, 0.35);
  const allGlow = ramp(t, 5.75, 6.05);

  const nodeStart = (i: number) => 0.25 + i * 0.65;
  const lineStart = (i: number) => 0.62 + i * 0.65;

  // curseur
  const curPts: [number, number, number][] = [
    [4.5, 950, 990],
    [4.7, 965, 985],
    [4.8, 1040, 962],
    [4.85, 1125, 948],
    [4.92, 1380, 850],
    [5.0, 1610, 763],
    [5.1, 1680, 752],
    [5.3, 1690, 750],
  ];
  const curX = interpolate(t, curPts.map((p) => p[0]), curPts.map((p) => p[1]), {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const curY = interpolate(t, curPts.map((p) => p[0]), curPts.map((p) => p[2]), {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const curO = ramp(t, 4.45, 4.6);
  const click = interpolate(t, [5.12, 5.18, 5.3], [1, 0.8, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const panelIn = ramp(t, 4.05, 4.3);
  const panelOut = ramp(t, 5.3, 5.55);
  const panelO = panelIn * (1 - panelOut);
  const approveFlash = interpolate(t, [5.12, 5.2, 5.5], [0, 1, 0.4], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});

  return (
    <AbsoluteFill style={{background: '#000', fontFamily: INTER}}>
      <AbsoluteFill
        style={{
          opacity: bg,
          background:
            'radial-gradient(ellipse 1150px 620px at 50% 50%, #04203a 0%, #03162c 30%, #020b1a 62%, #01040b 100%)',
        }}
      />
      <AbsoluteFill style={{transform: `scale(${scale})`, transformOrigin: '960px 460px'}}>
        {/* titre */}
        <div
          style={{
            position: 'absolute',
            left: 0,
            right: 0,
            top: 379,
            textAlign: 'center',
            fontSize: 19,
            fontWeight: 500,
            letterSpacing: 6.3,
            color: '#2f6c80',
            opacity: titleO,
          }}
        >
          WORKFLOW DE PRODUCTION VIDÉO PAR IA
        </div>
        {/* lignes fantômes + lignes tracées */}
        {[0, 1, 2, 3].map((i) => {
          const x1 = CX[i] + NW / 2;
          const x2 = CX[i + 1] - NW / 2;
          const p = ramp(t, lineStart(i), lineStart(i) + 0.28, Easing.inOut(Easing.quad));
          const lit = allGlow;
          return (
            <React.Fragment key={i}>
              <div style={{position: 'absolute', left: x1, top: LINE_Y - 1.5, width: x2 - x1, height: 3, background: '#1a2a44', opacity: titleO * (p < 1 ? 1 : 0)}} />
              <div
                style={{
                  position: 'absolute',
                  left: x1,
                  top: LINE_Y - 1.5,
                  width: (x2 - x1) * p,
                  height: 3,
                  background: '#2d95d0',
                  boxShadow: `0 0 ${8 + lit * 8}px rgba(40,150,220,${0.7 + lit * 0.3})`,
                }}
              />
            </React.Fragment>
          );
        })}
        {NODES.map((n, i) => {
          const s0 = nodeStart(i);
          const appear = ramp(t, s0, s0 + 0.2);
          const human = i === 4;
          // nœud actif : de son apparition à l'apparition du suivant
          const nextS = i < 4 ? nodeStart(i + 1) : 99;
          const active = ramp(t, s0 + 0.05, s0 + 0.2) * (1 - ramp(t, nextS, nextS + 0.2));
          const lit = Math.max(active, allGlow);
          const x = CX[i] - NW / 2;
          // intensités relevées sur l'original : bordure #12263d au repos, #17425d active, #236283 finale
          const mixc = (a: number[], b: number[], k: number) => a.map((v, j) => Math.round(v + (b[j] - v) * k));
          const baseC = mixc(mixc([18, 42, 66], [34, 128, 168], active), [48, 170, 210], allGlow);
          const border = human
            ? `rgba(${120 + lit * 30},${80 + lit * 10},${230},${0.55 + lit * 0.4})`
            : `rgb(${baseC.join(',')})`;
          const glow = human
            ? `0 0 ${16 + lit * 18}px rgba(130,70,240,${0.2 + lit * 0.25})`
            : `0 0 ${14 * active + 30 * allGlow}px rgba(20,140,225,${0.3 * active + 0.55 * allGlow})`;
          const fill = human
            ? 'linear-gradient(180deg, #210a4c 0%, #1a0840 100%)'
            : `linear-gradient(180deg, rgba(3,${30 + allGlow * 20},${55 + allGlow * 25},1) 0%, rgba(1,${18 + allGlow * 16},${40 + allGlow * 20},1) 100%)`;
          const iconC = human ? '#8b62e6' : '#35a7bd';
          const checkT = human ? 5.45 : 3.15 + i * 0.1;
          const cs = spring({frame: f - checkT * FPS, fps: FPS, config: {damping: 12, stiffness: 180}});
          return (
            <React.Fragment key={i}>
              <div
                style={{
                  position: 'absolute',
                  left: x,
                  top: NY,
                  width: NW,
                  height: NH,
                  borderRadius: 16,
                  background: fill,
                  border: `2px solid ${border}`,
                  boxShadow: glow,
                  opacity: appear,
                  transform: `translateY(${(1 - appear) * 15}px) scale(${0.965 + 0.035 * appear})`,
                  filter: appear < 1 ? `blur(${(1 - appear) * 4}px)` : undefined,
                  boxSizing: 'border-box',
                }}
              >
                <div
                  style={{
                    position: 'absolute',
                    right: human ? 14 : 13,
                    top: 12,
                    height: 20,
                    padding: '0 9px',
                    borderRadius: 10,
                    border: `1.5px solid ${human ? '#4a2a8c' : '#0f4a5c'}`,
                    background: human ? '#2a1260' : '#062638',
                    color: human ? '#6f45c9' : '#2a8397',
                    fontSize: 11,
                    fontWeight: 600,
                    letterSpacing: 0.8,
                    display: 'flex',
                    alignItems: 'center',
                  }}
                >
                  {human ? 'Humain' : 'IA'}
                </div>
                <div
                  style={{
                    position: 'absolute',
                    left: NW / 2 - 33,
                    top: 26,
                    width: 62,
                    height: 62,
                    borderRadius: 31,
                    border: `2px solid ${human ? '#4b2d95' : '#13485a'}`,
                    background: human ? '#2c1463' : '#062a42',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    boxSizing: 'border-box',
                  }}
                >
                  <Icon k={n.icon} color={iconC} />
                </div>
                <div style={{position: 'absolute', left: 0, right: 0, top: 100, textAlign: 'center', fontSize: 16.5, fontWeight: 600, color: '#eef3f8'}}>{n.name}</div>
                <div style={{position: 'absolute', left: 0, right: 0, top: 132, textAlign: 'center', fontSize: 13, fontWeight: 400, letterSpacing: 0.8, color: human ? '#7a64a8' : '#56697c'}}>
                  {n.sub}
                </div>
              </div>
              {t >= checkT && <Check s={cs} x={x + NW - 7} y={NY + NH - 6} />}
            </React.Fragment>
          );
        })}
        {/* panneau vidéo prête */}
        <div
          style={{
            position: 'absolute',
            left: CX[4] - NW / 2,
            top: 669,
            width: NW,
            height: 131,
            borderRadius: 16,
            background: '#080713',
            border: '2px solid #221a4c',
            boxShadow: '0 0 18px rgba(90,60,200,0.18)',
            boxSizing: 'border-box',
            opacity: panelO,
            transform: `translateY(${(1 - panelIn) * 10}px)`,
          }}
        >
          <div style={{position: 'absolute', left: 0, right: 0, top: 22, textAlign: 'center', fontSize: 17.5, fontWeight: 500, letterSpacing: 0.6, color: '#c9c9d4'}}>Vidéo prête</div>
          <div
            style={{
              position: 'absolute',
              left: 29,
              top: 64,
              width: 84,
              height: 42,
              borderRadius: 8,
              background: '#121320',
              border: '1.5px solid #2a2b38',
              color: '#9a9aa8',
              fontSize: 16,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              letterSpacing: 0.5,
              boxSizing: 'border-box',
            }}
          >
            Rejeter
          </div>
          <div
            style={{
              position: 'absolute',
              left: 125,
              top: 64,
              width: 84,
              height: 42,
              borderRadius: 8,
              background: `rgba(${9 + approveFlash * 20},${51 + approveFlash * 60},${46 + approveFlash * 40},1)`,
              border: '1.5px solid #1f7a5e',
              boxShadow: `0 0 ${14 + approveFlash * 16}px rgba(40,200,140,${0.3 + approveFlash * 0.4})`,
              color: approveFlash > 0.5 ? '#8fe0c8' : '#4f9a88',
              fontSize: 16,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              letterSpacing: 0.5,
              boxSizing: 'border-box',
            }}
          >
            Valider
          </div>
        </div>
      </AbsoluteFill>
      {/* curseur (hors zoom) */}
      <div
        style={{
          position: 'absolute',
          left: curX - 14,
          top: curY - 14,
          width: 28,
          height: 28,
          borderRadius: 14,
          background: '#e6e8ec',
          boxShadow: '0 0 8px rgba(255,255,255,0.35), 0 2px 6px rgba(0,0,0,0.5)',
          opacity: curO,
          transform: `scale(${click})`,
        }}
      />
    <SfxTrack cues={CUES} />
    </AbsoluteFill>
  );
};

export default Comp;

// Signaux sonores exportés pour la bibliothèque (cloud/cues_globaux.py).
export const cues = CUES;
