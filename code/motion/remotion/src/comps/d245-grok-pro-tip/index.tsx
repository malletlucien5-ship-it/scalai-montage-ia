import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame} from '../../shared/rt';
import {Camera, CamKey, Cursor, CurKey, FondMac, curAt} from '../../shared/ecranMac';
import {SfxCue, SfxTrack} from '../../shared/Sfx';
import {Ico} from '../d242-chatgpt-sombre/icones';
import {INTER_L} from '../../shared/localFonts';
import {GlossyPill, GlossySpec} from '../d209-pro-tip/GlossyPill';
import {GRIS, TXT, ligne} from '../d244-grok-bot/GrokApp';

// d245 : astuce Grok Bot (notes v3 de Ruben, 10:03-10:09). Écran de Dan réf. 587,17-591,85 s joué image pour image :
// zoom d'entrée (587,17-587,5), suggestions « What's on my plate today », « Catch up on Slack », « Notion / projects »,
// « Set how we work », champ « Type your own answer », clic sur « + » (588,45) : menu « Attach files » / « Teach a task »,
// clic sur « Teach a task » (589,9), écran « Connecting ». Le plan de Dan dure 4,7 s ; la note couvre 6 s :
// l'écran « Connecting » est tenu jusqu'à la fin. Bouton astuce en bas à droite (même bouton que d209).
// Coordonnées : vue zoomée de la réf. 589,4 s. Vue large (587,17 s) = zoomée / 1,37 décalée (bas gauche de la fenêtre fixe).
const FPS = 30;
const T0 = 587.17;
const fr = (t: number) => Math.round((t - T0) * FPS);
const DUREE = 180;

const K = 1.37;
const CAM: CamKey[] = [
  [0, 1 / K, 253 / K, 385 / K],
  [fr(587.5), 1, 0, 0, 'out'],
];

const CLIC_PLUS = fr(588.38);
const CLIC_TEACH = fr(589.9);
const CONNECT = fr(590.0);

const CUR: CurKey[] = [
  [0, 985, 720],
  [fr(587.4), 300, 975],
  [fr(587.6), 105, 990],
  [CLIC_PLUS, 100, 985],
  [fr(589.2), 102, 990],
  [fr(589.45), 190, 980],
  [fr(589.75), 268, 912],
  [CLIC_TEACH + 3, 270, 915],
  [fr(590.3), 250, 918],
];

const OPTIONS: [string, string, number][] = [
  ['A', "What's on my plate today", 96],
  ['B', 'Catch up on Slack', 166],
  ['C', 'Notion / projects', 236],
  ['D', 'Set how we work', 306],
];

const PILL: GlossySpec = {text: 'Astuce', right: 1886, bottom: 984, h: 116, size: 56, padX: 66, radius: 24};

const Conversation: React.FC<{f: number}> = ({f}) => {
  const menu = interpolate(f, [CLIC_PLUS + 2, CLIC_PLUS + 5], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const survolTeach = f >= fr(589.7);
  return (
    <>
      {/* fil au-dessus de la question (visible pendant le zoom d'entrée) */}
      <div style={{position: 'absolute', left: 59, top: -385, width: 1161, height: 116, borderRadius: 26, background: '#232323'}} />
      <div style={ligne(80, -350, 30, {fontSize: 22.5, fontWeight: 500, color: '#f0f0f0'})}>What do you mainly want me helping with?</div>
      <div style={{position: 'absolute', left: 80, top: -326, width: 1118, height: 46, borderRadius: 10, background: '#2a2a2a'}} />
      <div style={ligne(98, -303, 30, {fontSize: 21, color: '#8a8a8a'})}>Chief of Staff</div>
      <div style={ligne(1035, -221, 30, {fontSize: 21, fontStyle: 'italic', color: '#8a8a8a'})}>Renamed to Chief of Staff</div>
      <div style={{position: 'absolute', left: 59, top: -166, width: 1161, height: 89, borderRadius: 26, background: '#232323'}} />
      <div style={ligne(80, -137, 28, {fontSize: 22, color: TXT})}>Got it — I&apos;ll act as your Chief of Staff: triage, keep things moving, draft follow-ups, and</div>
      <div style={ligne(80, -106, 28, {fontSize: 22, color: TXT})}>coordinate across your other bots.</div>
      {/* question */}
      <div style={{position: 'absolute', left: 55, top: -49, width: 1160, height: 487, borderRadius: 26, background: '#232323'}} />
      <div style={ligne(76, -14, 30, {fontSize: 23, fontWeight: 500, color: '#f0f0f0'})}>Where should we start?</div>
      <Ico n="close" s={20} c="#8a8a8a" w={1.8} style={{position: 'absolute', left: 1172, top: -24}} />
      <div style={ligne(76, 24, 30, {fontSize: 22.5, color: GRIS})}>Whatever you pick, I&apos;ll dig in from there.</div>
      <div style={{position: 'absolute', left: 76, top: 61, width: 1117, height: 279, borderRadius: 12, background: '#2e2e2e', boxShadow: 'inset 0 0 0 1px #363636'}} />
      {OPTIONS.map(([k, t, y], i) => (
        <React.Fragment key={k}>
          {i > 0 && <div style={{position: 'absolute', left: 77, top: y - 35, width: 1115, height: 1.5, background: '#3a3a3a'}} />}
          <div style={{...ligne(92, y, 32, {fontSize: 18, color: '#a8a8a8', justifyContent: 'center'}), width: 32, borderRadius: 7, background: '#3b3b3b'}}>{k}</div>
          <div style={ligne(140, y, 34, {fontSize: 24.5, color: TXT})}>{t}</div>
        </React.Fragment>
      ))}
      <div style={{position: 'absolute', left: 76, top: 361, width: 1117, height: 54, borderRadius: 10, background: '#080808', boxShadow: 'inset 0 0 0 1px #262626'}} />
      <div style={ligne(96, 388, 32, {fontSize: 23, color: '#7a7a7a'})}>Type your own answer</div>
      {/* barre de message */}
      <div style={{position: 'absolute', left: 55, top: 935, width: 2400, height: 77, borderRadius: 38, background: '#2d2d2d'}} />
      <div style={{position: 'absolute', left: 69, top: 947, width: 50, height: 50, borderRadius: 25, background: '#3a3a3a', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
        <Ico n="plus" s={26} c="#d8d8d8" w={1.8} />
      </div>
      {menu < 0.5 && Math.floor(f / 15) % 2 === 0 && <div style={{position: 'absolute', left: 134, top: 959, width: 1.8, height: 27, background: '#e0e0e0'}} />}
      <div style={ligne(135, 972, 32, {fontSize: 24, color: '#6a6a6a'})}>Message Chief of Staff</div>
      {menu > 0 && (
        <div style={{position: 'absolute', left: 69, top: 806 + (1 - menu) * 8, width: 362, height: 132, borderRadius: 14, background: '#161616', boxShadow: 'inset 0 0 0 1px #262626, 0 10px 24px rgba(0,0,0,0.5)', opacity: menu}}>
          {survolTeach && <div style={{position: 'absolute', left: 8, top: 72, width: 346, height: 48, borderRadius: 10, background: '#262626'}} />}
          <Ico n="clip" s={22} c="#cfcfcf" w={1.7} style={{position: 'absolute', left: 30, top: 27}} />
          <div style={ligne(66, 38, 30, {fontSize: 23, color: TXT})}>Attach files</div>
          <div style={{position: 'absolute', left: 30, top: 85, width: 22, height: 22, borderRadius: 11, boxShadow: 'inset 0 0 0 2.4px #fb2338', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
            <div style={{width: 11, height: 11, borderRadius: 6, background: '#fb2338'}} />
          </div>
          <div style={ligne(66, 96, 30, {fontSize: 23, color: TXT})}>Teach a task</div>
        </div>
      )}
    </>
  );
};

const Connecting: React.FC<{f: number}> = ({f}) => {
  const k = f - CONNECT;
  const r = 6 * Math.sin(k / 7);
  return (
    <>
      <div style={{position: 'absolute', left: 884, top: 209, width: 74, height: 74, transform: `rotate(${r}deg)`}}>
        <svg width={74} height={74} viewBox="0 0 74 74">
          <circle cx="37" cy="37" r="37" fill="#fdfdfd" />
          <rect x="44" y="14" width="5" height="12" rx="2.5" fill="#111" transform="rotate(-28 46 20)" />
          <rect x="54" y="18" width="5" height="12" rx="2.5" fill="#111" transform="rotate(-28 56 24)" />
        </svg>
      </div>
      <div style={ligne(0, 327, 30, {width: 1842, justifyContent: 'center', fontSize: 21, color: '#8a8a8a', letterSpacing: 0.4})}>Connecting</div>
    </>
  );
};

const GrokAstuce: React.FC<{libelle?: string; astuce?: boolean}> = ({libelle = 'Pro Tip', astuce = true}) => {
  const f = useCurrentFrame();
  const c = curAt(CUR, f);
  const press = Math.max(
    interpolate(f, [CLIC_PLUS - 2, CLIC_PLUS, CLIC_PLUS + 3], [0, 1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}),
    interpolate(f, [CLIC_TEACH - 2, CLIC_TEACH, CLIC_TEACH + 3], [0, 1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}),
  );
  const v = Math.hypot(curAt(CUR, f + 0.5).x - curAt(CUR, f - 0.5).x, curAt(CUR, f + 0.5).y - curAt(CUR, f - 0.5).y);
  return (
    <AbsoluteFill style={{background: '#03142b', overflow: 'hidden'}}>
      <Camera keys={CAM} f={f} blurGain={0.05}>
        <FondMac />
        <div style={{position: 'absolute', left: 35, top: -1400, width: 2400, height: 2440, borderRadius: 22, overflow: 'hidden', background: '#030303', fontFamily: INTER_L, boxShadow: '0 0 0 1px rgba(255,255,255,0.06), 0 30px 80px rgba(0,0,0,0.6)'}}>
          <div style={{position: 'absolute', left: -35, top: 1400}}>{f < CONNECT ? <Conversation f={f} /> : <Connecting f={f} />}</div>
          {f >= CONNECT && <div style={{position: 'absolute', left: 0, top: 2425, width: 2400, height: 15, background: '#101010'}} />}
        </div>
        <Cursor x={c.x} y={c.y} h={96} press={press} blur={Math.min(8, v * 0.1)} />
      </Camera>
      {astuce && <GlossyPill p={{...PILL, text: libelle}} frame={f} />}
    </AbsoluteFill>
  );
};

const CUES: SfxCue[] = [
  {frame: 0, name: 'grave-apparition'},
  {frame: CLIC_PLUS, name: 'clic'},
  {frame: CLIC_TEACH, name: 'clic'},
];

export const meta = {
  id: 'd245-grok-pro-tip',
  fps: FPS,
  durationInFrames: DUREE,
  defaultProps: {libelle: 'Pro Tip', astuce: true},
  occurrences: [{ref: [587.17, 591.85] as [number, number], at: 641.86, from: 0, durationInFrames: DUREE, mode: 'plein' as const}],
};

const AvecSons: React.FC<{libelle?: string; astuce?: boolean}> = (p) => (
  <>
    <GrokAstuce {...p} />
    <SfxTrack cues={CUES} />
  </>
);
export default AvecSons;
export const cues = CUES;
