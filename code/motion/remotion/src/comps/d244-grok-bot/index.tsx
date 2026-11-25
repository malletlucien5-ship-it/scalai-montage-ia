import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame} from '../../shared/rt';
import {Cursor, CurKey, FondMac, curAt} from '../../shared/ecranMac';
import {SfxCue, SfxTrack} from '../../shared/Sfx';
import {Ico} from '../d242-chatgpt-sombre/icones';
import {Blob, FenetreGrok, GRIS, ROSE, TXT, ligne} from './GrokApp';

// d244 : création d'un Grok Bot (notes v3 de Ruben, 08:19-08:23). Écran de Dan, deux plans joués image pour image :
// - réf. 484,77-486,95 s : menu « To: Search or create Bots » ouvert, clic sur « Create new Bot » (485,5),
//   bot « New Bot · Creating… » dans la barre latérale, puis conversation « New Bot » ;
// - réf. 489,45-492,9 s : « Hey Lucien — good to meet you. », question et catégories « Work & projects »,
//   « Calendar & follow-ups », « Slack & Notion », « Something else », frappe « Chief of Staff », « Submit » (492,05).
// Dan coupe sur sa caméra entre les deux plans (486,95-489,45) : la composition les enchaîne en coupe franche.
// Les tuiles 1-2-3-4 posées sur ce plan chez Dan sont la composition d215 (calque séparé), non reprises ici.
const FPS = 30;
const P1 = [484.77, 486.95];
const P2 = [489.45, 492.9];
const N1 = Math.round((P1[1] - P1[0]) * FPS);
const DUREE = N1 + Math.round((P2[1] - P2[0]) * FPS);
const tDan = (f: number) => (f < N1 ? P1[0] + f / FPS : P2[0] + (f - N1) / FPS);

const MENU: [React.ReactNode, string, number][] = [
  [<div style={{width: 40, height: 40, borderRadius: 20, background: '#3a3a3a', display: 'flex', alignItems: 'center', justifyContent: 'center'}}><Ico n="plus" s={22} c="#cfcfcf" w={1.8} /></div>, 'Create new Bot', 237],
  [<div style={{width: 40, height: 40, borderRadius: 20, background: '#333', display: 'flex', alignItems: 'center', justifyContent: 'center'}}><Ico n="person" s={22} c="#bdbdbd" w={1.6} /></div>, 'Create group chat', 305],
  [<Blob d={42} c="#8a5a35" forme="nuage" />, 'Chief of Staff', 372],
  [<Blob d={40} c="#0aa58f" />, 'New Bot', 440],
  [<Blob d={42} c="#e0338a" forme="triangle" />, 'Flo - Motion Designer', 508],
  [<Blob d={40} c="#f29a0a" />, 'Motion Build', 575],
  [<Blob d={42} c="#7b5536" forme="nuage" />, 'New Bot', 643],
  [<Blob d={40} c="#e08a0b" />, 'New Bot', 711],
  [<Blob d={42} c="#c8102e" forme="pilule" />, 'Kale - Chef', 778],
];

const OPTIONS: [string, string, number][] = [
  ['A', 'Work & projects', 509],
  ['B', 'Calendar & follow-ups', 577],
  ['C', 'Slack & Notion', 646],
  ['D', 'Something else', 714],
];

const FRAPPE: [number, string][] = [
  [489.65, 'C'],
  [489.78, 'Ch'],
  [489.88, 'Chi'],
  [489.98, 'Chie'],
  [490.05, 'Chief'],
  [490.12, 'Chief '],
  [490.35, 'Chief o'],
  [490.5, 'Chief of'],
  [490.65, 'Chief of '],
  [490.95, 'Chief of S'],
  [491.15, 'Chief of St'],
  [491.35, 'Chief of Sta'],
  [491.5, 'Chief of Staf'],
  [491.65, 'Chief of Staff'],
];
const SUBMIT = 492.05;

const CUR: CurKey[] = [
  [0, 820, 120],
  [5, 745, 232],
  [12, 752, 240],
  [22, 930, 236],
  [30, 944, 232],
  [N1 - 1, 944, 232],
  [N1, 1500, 1032],
];

const GrokBot: React.FC<{prenom?: string; role?: string}> = ({prenom = 'Lucien', role = 'Chief of Staff'}) => {
  const f = useCurrentFrame();
  const t = tDan(f);
  const c = curAt(CUR, f);
  const cree = t >= 485.55;
  const conv = t >= 486.55;
  const plan2 = f >= N1;
  const tape = FRAPPE.filter(([tt]) => t >= tt).pop()?.[1] ?? '';
  const texte = role === 'Chief of Staff' ? tape : role.slice(0, Math.round((tape.length / 14) * role.length));
  const envoye = t >= SUBMIT;
  const press = interpolate(f, [14, 16, 19], [0, 1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const v = Math.hypot(curAt(CUR, f + 0.5).x - curAt(CUR, f - 0.5).x, curAt(CUR, f + 0.5).y - curAt(CUR, f - 0.5).y);
  const caret = Math.floor(f / 15) % 2 === 0;

  const sidebar = (
    <>
      {cree && (
        <>
          <div style={{position: 'absolute', left: 70, top: 271, width: 422, height: 96, borderRadius: 14, background: '#262626'}} />
          {conv ? (
            <>
              <div style={{position: 'absolute', left: 86, top: 289}}><Blob d={60} c={ROSE} /></div>
              <div style={ligne(163, 319, 30, {fontSize: 23, color: TXT})}>New Bot</div>
            </>
          ) : (
            <>
              <div style={{position: 'absolute', left: 92, top: 295, width: 48, height: 48, borderRadius: 24, background: '#333', display: 'flex', alignItems: 'center', justifyContent: 'center'}}><Ico n="person" s={26} c="#8a8a8a" w={1.6} /></div>
              <div style={ligne(163, 305, 28, {fontSize: 22, color: GRIS})}>New Bot</div>
              <div style={ligne(163, 333, 26, {fontSize: 19, color: '#6a6a6a'})}>Creating…</div>
            </>
          )}
        </>
      )}
      <div style={ligne(85, cree ? 414 : 311, 28, {fontSize: 21, color: GRIS})}>Hidden Bots</div>
      <div style={ligne(463, cree ? 414 : 311, 28, {fontSize: 21, color: GRIS})}>8</div>
    </>
  );

  return (
    <AbsoluteFill style={{background: '#03142b', overflow: 'hidden'}}>
      <FondMac />
      <FenetreGrok sidebar={sidebar}>
        {!conv ? (
          <>
            <div style={ligne(537, 158, 32, {fontSize: 23, gap: 12})}>
              <span style={{color: GRIS}}>To:</span>
              {caret && <span style={{width: 1.6, height: 26, background: '#e0e0e0', marginRight: -10}} />}
              <span style={{color: '#8a8a8a'}}>Search or create Bots</span>
            </div>
            <div style={{position: 'absolute', left: 516, top: 200, width: 1500, height: 1, background: '#1b1b1b'}} />
          </>
        ) : (
          <>
            <div style={{position: 'absolute', left: 541, top: 138}}><Blob d={33} c={ROSE} /></div>
            <div style={ligne(583, 155, 32, {fontSize: 23, color: TXT})}>New Bot</div>
            <div style={ligne(1551, 247, 30, {fontSize: 21, color: GRIS})}>Today 9:32 AM</div>
          </>
        )}
        {!cree && (
          <div style={{position: 'absolute', left: 572, top: 193, width: 995, height: 627, borderRadius: 20, background: '#262626', boxShadow: 'inset 0 0 0 1px #333, 0 18px 40px rgba(0,0,0,0.55)', overflow: 'hidden', WebkitMaskImage: 'linear-gradient(180deg, #000 0%, #000 62%, rgba(0,0,0,0.55) 88%, rgba(0,0,0,0.3) 100%)'}}>
            <div style={{position: 'absolute', left: 12, top: 13, width: 972, height: 62, borderRadius: 12, background: '#444'}} />
            {MENU.map(([ic, txt, y]) => (
              <React.Fragment key={txt + y}>
                <div style={{position: 'absolute', left: 599 - 572, top: y - 193 - 21, width: 42, height: 42, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>{ic}</div>
                <div style={ligne(655 - 572, y - 193, 32, {fontSize: 23, color: TXT})}>{txt}</div>
              </React.Fragment>
            ))}
          </div>
        )}
        {conv && !plan2 && <div style={{position: 'absolute', left: 560, top: 388, width: 7, height: 7, borderRadius: 4, background: ROSE}} />}
        {plan2 && (
          <>
            <div style={{...ligne(544, 324, 63, {fontSize: 23.5, color: TXT}), padding: '0 22px', borderRadius: 32, background: '#262626'}}>
              Hey {prenom} — good to meet you.
            </div>
            <div style={{position: 'absolute', left: 544, top: 364, width: 1137, height: envoye ? 158 : 481, borderRadius: 26, background: '#232323'}} />
            <div style={ligne(566, 403, 32, {fontSize: 23.5, fontWeight: 500, color: '#f0f0f0'})}>What do you mainly want me helping with?</div>
            {!envoye ? (
              <>
                <div style={ligne(566, 439, 30, {fontSize: 22.5, color: GRIS})}>Pick the closest fit — we can refine from there.</div>
                <Ico n="close" s={22} c="#bdbdbd" w={1.8} style={{position: 'absolute', left: 1631, top: 392}} />
                <div style={{position: 'absolute', left: 566, top: 475, width: 1094, height: 273, borderRadius: 14, background: '#2c2c2c', boxShadow: 'inset 0 0 0 1px #363636'}} />
                {OPTIONS.map(([k, txt, y], i) => (
                  <React.Fragment key={k}>
                    {i > 0 && <div style={{position: 'absolute', left: 567, top: y - 34, width: 1092, height: 1.5, background: '#383838'}} />}
                    <div style={{...ligne(582, y, 32, {fontSize: 18, color: '#a8a8a8', justifyContent: 'center'}), width: 32, borderRadius: 7, background: '#3b3b3b'}}>{k}</div>
                    <div style={ligne(628, y, 34, {fontSize: 24.5, color: TXT})}>{txt}</div>
                  </React.Fragment>
                ))}
                <div style={{position: 'absolute', left: 566, top: 768, width: 963, height: 55, borderRadius: 12, background: '#030303', boxShadow: 'inset 0 0 0 2px #2f6fd8'}} />
                <div style={ligne(585, 795, 34, {fontSize: 24, color: texte ? TXT : '#6a6a6a'})}>
                  {caret && <span style={{width: 1.8, height: 28, background: '#f0f0f0', order: texte ? 2 : 0, marginLeft: texte ? 2 : 0}} />}
                  <span style={{order: 1, whiteSpace: 'pre'}}>{texte || 'Type your own answer'}</span>
                </div>
                <div style={{...ligne(1545, 795, 55, {fontSize: 23, fontWeight: 500, color: '#111', justifyContent: 'center'}), width: 115, borderRadius: 12, background: '#fafafa'}}>Submit</div>
                <Ico n="smile" s={26} c={GRIS} w={1.6} style={{position: 'absolute', left: 1701, top: 592}} />
                <Ico n="back" s={26} c={GRIS} w={1.6} style={{position: 'absolute', left: 1747, top: 592}} />
                <Ico n="dots" s={26} c={GRIS} w={1.6} style={{position: 'absolute', left: 1793, top: 592}} />
              </>
            ) : (
              <div style={{opacity: interpolate(t, [SUBMIT, SUBMIT + 0.3], [0.3, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'})}}>
                <div style={{position: 'absolute', left: 566, top: 438, width: 1094, height: 68, borderRadius: 12, background: '#2a2a2a'}} />
                <div style={ligne(585, 472, 32, {fontSize: 22.5, color: '#8a8a8a'})}>{role}</div>
                <svg width={22} height={22} viewBox="0 0 24 24" style={{position: 'absolute', left: 1627, top: 461}}><path d="m5 12.5 4.5 4.5L19 7.5" stroke="#9a9a9a" strokeWidth={2} fill="none" strokeLinecap="round" /></svg>
                {t >= SUBMIT + 0.4 && <div style={{position: 'absolute', left: 561, top: 545}}><Blob d={40} c={ROSE} /></div>}
              </div>
            )}
          </>
        )}
      </FenetreGrok>
      <Cursor x={c.x} y={c.y} h={66} press={press} blur={Math.min(7, v * 0.1)} />
    </AbsoluteFill>
  );
};

const CUES: SfxCue[] = [
  {frame: 0, name: 'whoosh-transition'},
  {frame: 16, name: 'clic'},
  {frame: N1 + Math.round((489.65 - P2[0]) * FPS), name: 'frappe-clavier', durationInFrames: Math.round(2.0 * FPS)},
  {frame: N1 + Math.round((SUBMIT - P2[0]) * FPS), name: 'clic'},
];

export const meta = {
  id: 'd244-grok-bot',
  fps: FPS,
  durationInFrames: DUREE,
  defaultProps: {prenom: 'Lucien', role: 'Chief of Staff'},
  occurrences: [{ref: [484.77, 492.9] as [number, number], at: 531.02, from: 0, durationInFrames: DUREE, mode: 'plein' as const}],
};

const AvecSons: React.FC<{prenom?: string; role?: string}> = (p) => (
  <>
    <GrokBot {...p} />
    <SfxTrack cues={CUES} />
  </>
);
export default AvecSons;
export const cues = CUES;
