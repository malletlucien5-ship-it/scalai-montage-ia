import React, {useLayoutEffect, useMemo, useRef} from 'react';
import {AbsoluteFill, useCurrentFrame} from '../../shared/rt';
import {INTER_L} from '../../shared/localFonts';
import {SfxTrack, SfxCue} from '../../shared/Sfx';

// d225 (plein cadre) : sphère de milliers de points blancs/bleus sur fond bleu nuit, qui tourne lentement
// et grossit (« en formation »), interface d'app sobre autour (libellé, boutons, pilule d'état, barre de saisie).
// Réf. : coupe franche 1124,43 s -> 1127,77 s. Sphère centrée (960, 535), rayon ~318 px à 1124,5 s puis +25 px/s.
// Personnalisation : « APEX VEGA » et « Ask Apex Vega anything » retirés -> « SECOND CERVEAU », « Posez votre question… ».
// Cible : « Chaque réunion, chaque conversation, chaque commentaire, chaque décision, chaque raisonnement, chaque rapport. »
//   (1200,26 -> 1204,22 s).
const FPS = 30;
const AT = 1200.24;
const END = 1204.4;
const DUR = Math.round((END - AT) * FPS);
const N = 5200;

const rng = (seed: number) => () => {
  seed = (seed * 1664525 + 1013904223) % 4294967296;
  return seed / 4294967296;
};

type P = {x: number; y: number; z: number; s: number; b: number};

const Sphere: React.FC = () => {
  const f = useCurrentFrame();
  const ref = useRef<HTMLCanvasElement>(null);
  const pts = useMemo<P[]>(() => {
    const r = rng(20250925);
    const out: P[] = [];
    for (let i = 0; i < N; i++) {
      const u = r() * 2 - 1;
      const th = r() * Math.PI * 2;
      const shell = r() < 0.62;
      const rad = shell ? 0.8 + 0.2 * Math.sqrt(r()) : Math.cbrt(r()) * 0.85;
      const q = Math.sqrt(1 - u * u);
      out.push({x: q * Math.cos(th) * rad, y: u * rad, z: q * Math.sin(th) * rad, s: 0.55 + r() * 1.0, b: 0.55 + r() * 0.45});
    }
    return out;
  }, []);

  useLayoutEffect(() => {
    const c = ref.current;
    if (!c) return;
    const ctx = c.getContext('2d');
    if (!ctx) return;
    const t = f / FPS;
    const R = 318 + 13 * t;
    const cx = 960;
    const cy = 535;
    ctx.clearRect(0, 0, 1920, 1080);
    // halo bleu interne
    const g = ctx.createRadialGradient(cx, cy, 0, cx, cy, R * 1.05);
    g.addColorStop(0, 'rgba(50,62,160,0.5)');
    g.addColorStop(0.55, 'rgba(38,50,150,0.35)');
    g.addColorStop(1, 'rgba(20,26,90,0)');
    ctx.fillStyle = g;
    ctx.beginPath();
    ctx.arc(cx, cy, R * 1.05, 0, Math.PI * 2);
    ctx.fill();
    const a = 0.35 + t * 0.14;
    const tilt = 0.28;
    const ca = Math.cos(a);
    const sa = Math.sin(a);
    const ct = Math.cos(tilt);
    const st = Math.sin(tilt);
    const proj = pts.map((p) => {
      const x1 = p.x * ca + p.z * sa;
      const z1 = -p.x * sa + p.z * ca;
      const y2 = p.y * ct - z1 * st;
      const z2 = p.y * st + z1 * ct;
      const k = 1 + z2 * 0.08;
      return {X: cx + x1 * R * k, Y: cy + y2 * R * k, z: z2, p};
    });
    proj.sort((m, n) => m.z - n.z);
    for (const q of proj) {
      const depth = (q.z + 1) / 2; // 0 fond, 1 devant
      const size = q.p.s * (0.9 + depth * 1.3);
      const alpha = Math.min(1, q.p.b * (0.6 + depth * 0.55));
      ctx.fillStyle = `rgba(190,205,255,${(alpha * 0.1).toFixed(3)})`;
      ctx.beginPath();
      ctx.arc(q.X, q.Y, size * 2.2, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = `rgba(${Math.round(215 + 40 * depth)},${Math.round(225 + 30 * depth)},255,${alpha.toFixed(3)})`;
      ctx.beginPath();
      ctx.arc(q.X, q.Y, size, 0, Math.PI * 2);
      ctx.fill();
    }
    // noyau lumineux central
    const n = ctx.createRadialGradient(cx, cy, 0, cx, cy, 16);
    n.addColorStop(0, 'rgba(255,255,255,1)');
    n.addColorStop(0.4, 'rgba(235,238,255,0.9)');
    n.addColorStop(1, 'rgba(200,210,255,0)');
    ctx.fillStyle = n;
    ctx.beginPath();
    ctx.arc(cx, cy, 16, 0, Math.PI * 2);
    ctx.fill();
  }, [f, pts]);

  return <canvas ref={ref} width={1920} height={1080} style={{position: 'absolute', inset: 0}} />;
};

const Icon: React.FC<{d: string}> = ({d}) => (
  <svg width={18} height={18} viewBox="0 0 24 24" fill="none" stroke="rgba(220,225,235,0.75)" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round">
    <path d={d} />
  </svg>
);

const Ui: React.FC = () => (
  <>
    {/* libellé en haut à gauche */}
    <div style={{position: 'absolute', left: 104, top: 20, display: 'flex', alignItems: 'center', gap: 12, fontFamily: INTER_L, fontWeight: 500, fontSize: 16, letterSpacing: 4.5, color: '#c9cdd6'}}>
      <div style={{width: 11, height: 11, borderRadius: 6, background: '#c9cdd6', boxShadow: '0 0 8px rgba(200,210,255,0.8)'}} />
      SECOND CERVEAU
    </div>
    {/* groupe de boutons en haut à droite */}
    <div style={{position: 'absolute', left: 1660, top: 7, width: 156, height: 52, borderRadius: 12, border: '1px solid rgba(255,255,255,0.16)', display: 'flex'}}>
      {[
        'M20 12a8 8 0 1 1-2.3-5.7M20 4v4h-4',
        'M4 8h16M4 16h16M9 5v6M15 13v6',
        'M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6zM19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-2.9 1.2V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-2.9-1.2l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0-1.2-2.9H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.2-2.9l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 2.9-1.2V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 2.9 1.2l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0 1.2 2.9H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5.9z',
      ].map((d, i) => (
        <div key={i} style={{flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', borderLeft: i ? '1px solid rgba(255,255,255,0.12)' : 'none'}}>
          <Icon d={d} />
        </div>
      ))}
    </div>
    {/* pilule d'état */}
    <div style={{position: 'absolute', left: 0, width: 1920, top: 917, display: 'flex', justifyContent: 'center'}}>
      <div style={{height: 34, padding: '0 17px', borderRadius: 18, border: '1.5px solid rgba(255,255,255,0.32)', display: 'flex', alignItems: 'center', fontFamily: INTER_L, fontWeight: 500, fontSize: 11.5, letterSpacing: 2.6, color: 'rgba(225,228,236,0.85)'}}>
        FORMATION · 10 000 SIGNAUX
      </div>
    </div>
    {/* barre de saisie */}
    <div
      style={{
        position: 'absolute',
        left: 515,
        top: 998,
        width: 890,
        height: 58,
        borderRadius: 18,
        border: '1.5px solid rgba(255,255,255,0.24)',
        background: 'rgba(4,6,16,0.6)',
        display: 'flex',
        alignItems: 'center',
        padding: '0 8px 0 22px',
        boxSizing: 'border-box',
        fontFamily: INTER_L,
        fontSize: 16,
        color: '#8b909a',
      }}
    >
      <div style={{flex: 1}}>Posez votre question à votre second cerveau</div>
      <div style={{marginRight: 18}}>
        <Icon d="M12 3a3 3 0 0 0-3 3v6a3 3 0 0 0 6 0V6a3 3 0 0 0-3-3zM19 11a7 7 0 0 1-14 0M12 18v3" />
      </div>
      <div style={{width: 42, height: 42, borderRadius: 10, background: '#5a5d64', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
        <svg width={18} height={18} viewBox="0 0 24 24" fill="none" stroke="#1b1d22" strokeWidth={2.2} strokeLinecap="round" strokeLinejoin="round">
          <path d="M12 19V5M5 12l7-7 7 7" />
        </svg>
      </div>
    </div>
  </>
);

const SphereParticules: React.FC<{showPlate?: boolean}> = () => (
  <AbsoluteFill style={{background: 'radial-gradient(ellipse 30% 40% at 82% 26%, #0a1a18 0%, #03060f 60%, #02030c 100%)', overflow: 'hidden'}}>
    <Sphere />
    <Ui />
    <SfxTrack cues={cuesExportees} />
  </AbsoluteFill>
);

export const meta = {
  id: 'd225-sphere-particules',
  fps: FPS,
  durationInFrames: DUR,
  defaultProps: {showPlate: true},
  occurrences: [{ref: [1124.43, 1127.77] as [number, number], at: AT, from: 0, durationInFrames: DUR, mode: 'plein' as const}],
};
export default SphereParticules;

// Signaux sonores exportés pour la bibliothèque (cloud/cues_globaux.py).
const cuesExportees: SfxCue[] = [{frame: 0, name: 'whoosh-transition'}];
export const cues = cuesExportees;
