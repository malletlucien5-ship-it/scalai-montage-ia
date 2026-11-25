import React from 'react';
import {AbsoluteFill, Easing, interpolate, useCurrentFrame} from '../../shared/rt';
import {Plate} from '../../shared/Plate';
import {SfxTrack, SfxCue} from '../../shared/Sfx';

// Référence : 18,0 s à 23,4 s. Deux cartes teal à icône au trait.
// Carte 1 en bas à gauche, carte 2 en bas à droite. Mesures en px 1920x1080.
export const meta = {
  id: '06-icone-coin',
  durationInFrames: 162,
  fps: 30,
  defaultProps: {showPlate: true},
  occurrences: [{ref: [18.0, 23.4], from: 0, durationInFrames: 162, mode: 'overlay'}],
};

// Bruitages : une grave-apparition à l'image où chaque carte entre dans le cadre.
const SFX: SfxCue[] = [
  {frame: 9, name: 'grave-apparition'},
  {frame: 75, name: 'grave-apparition'},
];

const W = 459;
const H = 294;
const STROKE = '#95DFFB';

const enterP = (t: number) => {
  if (t <= 0) return 0;
  const k = 0.123;
  return Math.min(1, (1 - Math.exp(-k * t)) / (1 - Math.exp(-k * 38)));
};

const Card: React.FC<{
  x: number;
  y: number;
  enter: number;
  exit: number;
  children: React.ReactNode;
}> = ({x, y, enter, exit, children}) => {
  const f = useCurrentFrame();
  const te = f - enter;
  const tx = f - exit;
  if (te < 0) return null;
  const dropIn = (1 - enterP(te)) * 362;
  const dropOut = interpolate(tx, [0, 21], [0, 372], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.bezier(0.55, 0.02, 0.85, 0.45),
  });
  if (dropOut >= 370) return null;
  const settle = interpolate(te, [24, 36], [1, 0.982], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.inOut(Easing.quad),
  });
  const unsettle = interpolate(tx, [0, 4], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const scale = settle + (1 - settle) * unsettle;
  return (
    <div
      style={{
        position: 'absolute',
        left: x,
        top: y,
        width: W,
        height: H,
        transform: `translateY(${dropIn + dropOut}px) scale(${scale})`,
        borderRadius: 17,
        border: '2px solid #62CBE0',
        boxSizing: 'border-box',
        overflow: 'hidden',
        background:
          'linear-gradient(158deg, #07324b 0%, #11435e 30%, #0e3e58 45%, #072841 75%, #031a2d 100%)',
        boxShadow: '0 0 10px rgba(98,203,224,0.35), 0 10px 30px rgba(0,0,0,0.45)',
      }}
    >
      <svg
        width={W}
        height={H}
        viewBox={`0 0 ${W} ${H}`}
        style={{position: 'absolute', left: -2, top: -2, filter: 'drop-shadow(0 0 1.5px rgba(120,215,255,0.65)) drop-shadow(0 0 6px rgba(60,180,240,0.3))'}}
        fill="none"
        stroke={STROKE}
        strokeWidth={6}
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        {children}
      </svg>
    </div>
  );
};

const ThinkingAtDesk: React.FC = () => (
  <>
    {/* nuage de pensée emmêlé : cercles entrelacés relevés sur l'original */}
    <g strokeWidth={4.8}>
      <ellipse cx={190} cy={48} rx={25} ry={20} transform="rotate(-10 190 48)" />
      <ellipse cx={222} cy={42} rx={26} ry={19} transform="rotate(10 222 42)" />
      <ellipse cx={242} cy={57} rx={18} ry={20} />
      <ellipse cx={179} cy={63} rx={18} ry={15} />
      <ellipse cx={212} cy={70} rx={28} ry={20} transform="rotate(-5 212 70)" />
      <ellipse cx={205} cy={57} rx={31} ry={14} transform="rotate(28 205 57)" />
      <ellipse cx={217} cy={57} rx={31} ry={14} transform="rotate(-32 217 57)" />
    </g>
    {/* point d'interrogation */}
    <path d="M258 86 C258 76 276 74 277 85 C278 93 267 94 267 104" strokeWidth={4} />
    <circle cx={267} cy={117} r={2.5} fill={STROKE} strokeWidth={2} />
    {/* tête */}
    <circle cx={180} cy={126} r={27} />
    {/* buste et bras */}
    <path d="M127 223 V190 Q127 160 158 158 H182 Q206 160 213 184 L221 206 H236" />
    <path d="M152 196 V212 H236" />
    {/* ordinateur portable */}
    <path d="M252 153 H322 Q327 153 326 158 L311 219 Q310 223 305 223 H240 Q235 223 236 218 L248 157 Q249 153 252 153 Z" />
    <circle cx={280} cy={188} r={7} />
    <path d="M196 224 H312" />
    {/* bureau */}
    <rect x={102} y={225} width={255} height={17} rx={6} />
    <path d="M122 242 V282 M337 242 V282" />
  </>
);

const Box: React.FC<{cx: number; children?: React.ReactNode}> = ({cx, children}) => (
  <>
    <rect x={cx - 36} y={187} width={72} height={66} rx={8} />
    {children}
  </>
);

const gearPath = (cx: number, cy: number) => {
  const pts: string[] = [];
  const teeth = 8;
  for (let i = 0; i < teeth * 2; i++) {
    const a0 = (i / (teeth * 2)) * Math.PI * 2;
    const a1 = ((i + 1) / (teeth * 2)) * Math.PI * 2;
    const r = i % 2 === 0 ? 19 : 14;
    pts.push(`${cx + r * Math.cos(a0)},${cy + r * Math.sin(a0)}`);
    pts.push(`${cx + r * Math.cos(a1)},${cy + r * Math.sin(a1)}`);
  }
  return 'M' + pts.join(' L') + ' Z';
};

const AgentTree: React.FC = () => {
  const cols = [77, 179, 282, 386];
  return (
    <>
      {/* antenne */}
      <circle cx={232} cy={31} r={5} fill={STROKE} />
      <path d="M232 36 V49" />
      {/* tête du robot */}
      <rect x={189} y={49} width={85} height={68} rx={14} />
      <rect x={176} y={72} width={13} height={25} rx={4} />
      <rect x={274} y={72} width={13} height={25} rx={4} />
      <circle cx={215} cy={79} r={5.5} fill={STROKE} />
      <circle cx={249} cy={79} r={5.5} fill={STROKE} />
      <path d="M218 96 Q232 107 246 96" />
      {/* arbre */}
      <path d={`M232 117 V147 M${cols[0]} 178 V147 H${cols[3]} V178`} strokeWidth={5} />
      {cols.slice(1, 3).map((c) => (
        <path key={c} d={`M${c} 147 V178`} strokeWidth={5} />
      ))}
      {cols.map((c) => (
        <path key={'a' + c} d={`M${c - 6} 173 L${c} 181 L${c + 6} 173`} strokeWidth={5} />
      ))}
      {/* modules */}
      <Box cx={cols[0]}>
        <path d={gearPath(cols[0], 220)} strokeWidth={4.5} fill="none" />
        <circle cx={cols[0]} cy={220} r={6.5} strokeWidth={4.5} />
      </Box>
      <Box cx={cols[1]}>
        <g strokeWidth={5}>
          <ellipse cx={cols[1]} cy={202} rx={20} ry={7} />
          <path d={`M${cols[1] - 20} 202 V238 Q${cols[1]} 250 ${cols[1] + 20} 238 V202`} />
          <path d={`M${cols[1] - 20} 214 Q${cols[1]} 226 ${cols[1] + 20} 214`} />
          <path d={`M${cols[1] - 20} 226 Q${cols[1]} 238 ${cols[1] + 20} 226`} />
        </g>
      </Box>
      <Box cx={cols[2]}>
        {/* graphique : 5 barres, ligne brisée et flèche, relevés sur l'original */}
        <g strokeWidth={0} fill={STROKE}>
          {[
            [-21.4, 7.1, 228.8],
            [-12, 7.1, 224.4],
            [-3, 7.5, 224.4],
            [6.5, 8, 222.3],
            [16.8, 7.9, 215.6],
          ].map(([dx, w, top]) => (
            <rect key={dx} x={cols[2] + dx} y={top} width={w} height={243.8 - top} rx={1} />
          ))}
          <path d={`M${cols[2] + 24.9} 198 L${cols[2] + 12.5} 201 L${cols[2] + 22.6} 211.5 Z`} strokeWidth={1.5} stroke={STROKE} strokeLinejoin="round" />
        </g>
        <path d={`M${cols[2] - 20} 223.8 L${cols[2] - 6.4} 211.3 L${cols[2] + 3} 218.8 L${cols[2] + 19} 204.5`} strokeWidth={3.6} />
      </Box>
      <Box cx={cols[3]}>
        <path d={`M${cols[3] - 19} 221 L${cols[3] - 6} 234 L${cols[3] + 19} 206`} strokeWidth={9} />
      </Box>
    </>
  );
};

const IconeCoin: React.FC<{showPlate?: boolean}> = ({showPlate = true}) => (
  <AbsoluteFill>
    <Plate show={showPlate} />
    <SfxTrack cues={SFX} />
    <Card x={73} y={727} enter={8} exit={47}>
      <ThinkingAtDesk />
    </Card>
    <Card x={1391} y={732} enter={74} exit={135}>
      <AgentTree />
    </Card>
  </AbsoluteFill>
);

export default IconeCoin;

// Signaux sonores exportés pour la bibliothèque (cloud/cues_globaux.py).
export const cues = SFX;
