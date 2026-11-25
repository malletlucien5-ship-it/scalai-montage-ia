import React from 'react';
import {AbsoluteFill, useCurrentFrame, Easing} from '../../shared/rt';
import {SANS, ease, Cursor, ScreenBg, IPlus, IMic, IWave, IChevron} from './ui';
import {SfxTrack, SfxCue} from '../../shared/Sfx';

// Occurrence 1 : 318,0 s à 321,0 s (90 images). Pause 0,5 s. Occurrence 2 : 593,0 s à 595,0 s (60 images).
export const meta = {id: '25-artefacts-dashboards', durationInFrames: 165, fps: 30, defaultProps: {showPlate: true},
  occurrences: [
    {ref: [318.133, 321.0], from: 4, durationInFrames: 86, mode: 'plein'},
    {ref: [593.4, 595.0], from: 117, durationInFrames: 48, mode: 'plein'},
  ],
};

// Bruitages calés sur le minutage de l'animation (règles : SFX-REGLES.md).
const SFX: SfxCue[] = [
  {frame: 5, name: 'grave-apparition'},
  {frame: 31, name: 'grave-apparition'},
  {frame: 50, name: 'grave-apparition'},
  {frame: 117, name: 'notification'},
  {frame: 144, name: 'notification'},
];

const Tx: React.FC<{x: number; y: number; s: number; c: string; w?: number; ls?: number; children: React.ReactNode; style?: React.CSSProperties}> = ({x, y, s, c, w = 400, ls = 0, children, style}) => (
  <div style={{position: 'absolute', left: x, top: y - s * 0.62, fontSize: s, color: c, fontWeight: w, letterSpacing: ls, whiteSpace: 'nowrap', lineHeight: 1.2, ...style}}>{children}</div>
);

// Fond mesuré sur 318,25 s : deux lueurs bleu-teal (bas gauche et bas centre) sur noir.
const GlowBg: React.FC = () => (
  <AbsoluteFill style={{background: [
    'radial-gradient(ellipse 330px 250px at 440px 880px, rgba(31,63,86,1) 0%, rgba(24,52,72,0.85) 45%, rgba(0,0,0,0) 100%)',
    'radial-gradient(ellipse 360px 190px at 1040px 980px, rgba(28,56,72,0.9) 0%, rgba(20,44,58,0.7) 45%, rgba(0,0,0,0) 100%)',
    'radial-gradient(ellipse 1100px 260px at 700px 1080px, rgba(30,50,62,0.9) 0%, rgba(0,0,0,0) 100%)',
    'radial-gradient(ellipse 160px 380px at 0px 760px, rgba(10,24,34,1) 0%, rgba(0,0,0,0) 100%)',
    'radial-gradient(ellipse 200px 500px at 1920px 700px, rgba(6,16,22,1) 0%, rgba(0,0,0,0) 100%)',
    '#000'].join(',')}} />
);

// Zone « Écris un message… » en bas des fenêtres de chat.
const ChatBar: React.FC<{y: number}> = ({y}) => (
  <div style={{position: 'absolute', left: 12, top: y, width: 724, height: 120, borderRadius: 16, background: '#30302e'}}>
    <Tx x={20} y={31} s={15.5} c="#8e8c87">Écris un message…</Tx>
    <IPlus size={18} color="#cfcdc8" style={{position: 'absolute', left: 25, top: 59}} />
    <Tx x={509} y={68} s={13} c="#c6c4bf">Sonnet 4.6 <span style={{color: '#8e8c87'}}>Bas</span></Tx>
    <IChevron size={11} color="#8e8c87" style={{position: 'absolute', left: 617, top: 63}} />
    <IMic size={17} color="#cfcdc8" style={{position: 'absolute', left: 646, top: 59}} />
    <IWave size={19} color="#cfcdc8" style={{position: 'absolute', left: 684, top: 58}} />
  </div>
);
const DownBtn: React.FC<{x: number; y: number}> = ({x, y}) => (
  <div style={{position: 'absolute', left: x - 17, top: y - 17, width: 34, height: 34, borderRadius: 17, background: '#30302e', border: '1px solid #3d3d3a', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
    <svg width="16" height="16" viewBox="0 0 24 24" stroke="#d9d7d2" strokeWidth="2" fill="none" strokeLinecap="round"><path d="M12 5v14M6 13l6 6 6-6" /></svg>
  </div>
);
const ChatWin: React.FC<{x: number; y: number; o: React.CSSProperties; children: React.ReactNode}> = ({x, y, o, children}) => (
  <div style={{position: 'absolute', left: x, top: y, width: 747, height: 450, borderRadius: 12, background: '#262624', overflow: 'hidden', fontFamily: SANS,
    boxShadow: '0 0 0 1.5px rgba(205,205,200,0.55), 0 30px 80px rgba(0,0,0,0.6)', ...o}}>{children}</div>
);

// ---------- Graphique MRR ----------
const MRR = [345, 339, 333, 328, 318, 308, 295, 284, 268, 250, 231, 206].map((v) => v - 66);
const TGT = [341, 334, 327, 319, 310, 299, 287, 273, 257, 240, 212, 184].map((v) => v - 66);
const MONTHS = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Juin', 'Juil', 'Août', 'Sep', 'Oct', 'Nov', 'Déc'];
const LineChart: React.FC = () => {
  const px = (i: number) => 72 + i * 57.5;
  const line = MRR.map((y, i) => `${i ? 'L' : 'M'}${px(i)} ${y}`).join(' ');
  return (
    <>
      <Tx x={27} y={19} s={13} c="#c9c7c2">Revenu mensuel récurrent</Tx>
      <Tx x={27} y={43} s={25} c="#f3f2ee" w={700}>84 200 $</Tx>
      <div style={{position: 'absolute', left: 580, top: 36, height: 22, padding: '0 9px', borderRadius: 5, background: '#16361f', border: '1px solid #1f5a2c', color: '#4ad07a', fontSize: 11.5, display: 'flex', alignItems: 'center'}}>↑ 23 % vs mois dernier</div>
      <div style={{position: 'absolute', left: 28, top: 76, width: 9, height: 9, borderRadius: 2, background: '#22b07d'}} /><Tx x={42} y={81} s={12} c="#c9c7c2">MRR</Tx>
      <div style={{position: 'absolute', left: 84, top: 80, width: 9, height: 2, background: '#c9c7c2'}} /><Tx x={98} y={81} s={12} c="#c9c7c2">Objectif</Tx>
      {['100 k$', '90 k$', '80 k$', '70 k$', '60 k$', '50 k$', '40 k$', '30 k$', '20 k$', '10 k$'].map((t, i) => <Tx key={i} x={27} y={109 + i * 19.35} s={10.5} c="#8e8c87">{t}</Tx>)}
      {MONTHS.map((m, i) => <Tx key={i} x={px(i) - 11} y={300} s={10.5} c="#8e8c87">{m}</Tx>)}
      <svg width="747" height="330" style={{position: 'absolute', left: 0, top: 0}}>
        <defs><linearGradient id="g1" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stopColor="#1f7a58" stopOpacity="0.45" /><stop offset="1" stopColor="#1f7a58" stopOpacity="0.05" /></linearGradient></defs>
        {Array.from({length: 10}, (_, i) => <line key={i} x1="68" x2="708" y1={108 + i * 19.35} y2={108 + i * 19.35} stroke="#33332f" strokeWidth="1" />)}
        <path d={`${line} L${px(11)} 282 L${px(0)} 282 Z`} fill="url(#g1)" />
        <path d={TGT.map((y, i) => `${i ? 'L' : 'M'}${px(i)} ${y}`).join(' ')} stroke="#d9d7d2" strokeWidth="1.3" strokeDasharray="4 3" fill="none" />
        <path d={line} stroke="#26b884" strokeWidth="2" fill="none" />
        {MRR.map((y, i) => <circle key={i} cx={px(i)} cy={y} r="3.4" fill="#26b884" />)}
      </svg>
      <div style={{position: 'absolute', left: 30, top: 330, width: 690, height: 1, background: '#3a3a37'}} />
      <DownBtn x={372} y={311} />
      <ChatBar y={348} />
    </>
  );
};

// ---------- Histogramme ----------
const BARS = [[32, 18, 9], [41, 24, 14], [55, 31, 22], [72, 43, 35]];
const COLS = ['#7b6be0', '#1fa37a', '#f0a030'];
const BarChart: React.FC = () => (
  <>
    <Tx x={27} y={11} s={12.5} c="#c9c7c2">Revenu par canal</Tx>
    <Tx x={27} y={34} s={18} c="#f3f2ee" w={700}>Répartition T1 à T4</Tx>
    {['Organique', 'Payant', 'Parrainage'].map((t, i) => (
      <div key={i}><div style={{position: 'absolute', left: 28 + [0, 90, 164][i], top: 63, width: 9, height: 9, borderRadius: 2, background: COLS[i]}} /><Tx x={42 + [0, 90, 164][i]} y={68} s={12} c="#c9c7c2">{t}</Tx></div>
    ))}
    {['80 k$', '70 k$', '60 k$', '50 k$', '40 k$', '30 k$', '20 k$', '10 k$', '0 k$'].map((t, i) => <Tx key={i} x={27} y={96 + i * 24.25} s={10.5} c="#8e8c87">{t}</Tx>)}
    <svg width="747" height="330" style={{position: 'absolute', left: 0, top: 0}}>
      {Array.from({length: 9}, (_, i) => <line key={i} x1="68" x2="712" y1={96 + i * 24.25} y2={96 + i * 24.25} stroke="#30302d" strokeWidth="1" />)}
      {BARS.map((g, q) => g.map((v, k) => {
        const x = 147 + q * 163 - 64 + k * 44; const h = v * 2.425;
        return <path key={`${q}${k}`} d={`M${x} 290 V${290 - h + 3} q0 -3 3 -3 h33 q3 0 3 3 V290 Z`} fill={COLS[k]} />;
      }))}
    </svg>
    {['T1', 'T2', 'T3', 'T4'].map((t, q) => <Tx key={q} x={140 + q * 163} y={306} s={10.5} c="#8e8c87">{t}</Tx>)}
    <div style={{position: 'absolute', left: 30, top: 337, width: 690, height: 1, background: '#3a3a37'}} />
    <DownBtn x={372} y={312} />
    <ChatBar y={350} />
  </>
);

// ---------- Tableau de bord du matin ----------
const Morning: React.FC = () => {
  const kpi: [string, string, string, string][] = [['MRR', '84,2 k$', '↑ 23 %', '#4ad07a'], ['Utilisateurs actifs', '3 841', '↑ 11 %', '#4ad07a'], ['Taux de churn', '2,1 %', '↓ 0,4 %', '#4ad07a'], ['Nouveaux deals', '18', '↑ 3 cette semaine', '#e0a53a']];
  const todo = ['Relire le point investisseurs T3', 'Appel avec le lead Série A à 14h', 'Valider le texte de la landing page', 'Point d’équipe hebdo à 10h'];
  return (
    <>
      <div style={{position: 'absolute', left: 25, top: 0, width: 697, height: 340, background: '#232321'}} />
      <Tx x={46} y={26} s={16.5} c="#f3f2ee" w={600}>Bonjour Lucien 👋</Tx>
      <Tx x={46} y={46} s={12.5} c="#b5b3ae">Voici ce qui se passe aujourd’hui</Tx>
      <div style={{position: 'absolute', left: 598, top: 20, width: 100, height: 31, borderRadius: 6, border: '1px solid #45453f', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6, fontSize: 13, color: '#eceae5'}}>⤓ Exporter</div>
      <Tx x={690} y={14} s={14} c="#8e8c87">···</Tx>
      {kpi.map(([a, b, c, col], i) => (
        <div key={i} style={{position: 'absolute', left: 46 + i * 165.5, top: 74, width: 154, height: 86, borderRadius: 6, background: '#2d2d2b'}}>
          <Tx x={13} y={19} s={11.5} c="#c9c7c2">{a}</Tx>
          <Tx x={13} y={43} s={20} c="#f6f5f1" w={600}>{b}</Tx>
          <Tx x={13} y={67} s={10} c={col}>{c}</Tx>
        </div>
      ))}
      <div style={{position: 'absolute', left: 46, top: 178, width: 651, height: 150, borderRadius: 6, background: '#2d2d2b'}}>
        <Tx x={15} y={21} s={12.5} c="#f3f2ee" w={600}>Priorités du jour</Tx>
        {todo.map((t, i) => (
          <div key={i}>
            <div style={{position: 'absolute', left: 16, top: 42 + i * 26, width: 12, height: 12, borderRadius: 7, border: `1.5px solid ${i === 0 ? '#3fbf6f' : '#bdbbb6'}`}}>
              {i === 0 && <svg width="12" height="12" viewBox="0 0 24 24" style={{position: 'absolute', left: 0, top: 0}}><path d="M6 12l4 4 8-8" stroke="#3fbf6f" strokeWidth="3" fill="none" /></svg>}
            </div>
            <Tx x={41} y={49 + i * 26} s={12.5} c={i === 0 ? '#8e8c87' : '#eceae5'} style={{textDecoration: i === 0 ? 'line-through' : undefined}}>{t}</Tx>
          </div>
        ))}
      </div>
      <ChatBar y={348} />
    </>
  );
};

// ---------- Fenêtres « app » (occurrence 2) ----------
const MacWin: React.FC<{x: number; y: number; w: number; h: number; title: string; tb: number; children: React.ReactNode}> = ({x, y, w, h, title, tb, children}) => (
  <div style={{position: 'absolute', left: x, top: y, width: w, height: h, borderRadius: 22, background: '#1b1b1b', overflow: 'hidden', fontFamily: SANS,
    boxShadow: '0 0 0 1.5px rgba(210,210,205,0.6), 0 30px 90px rgba(0,0,0,0.6)'}}>
    <div style={{position: 'absolute', left: 0, top: 0, width: w, height: tb, borderBottom: '1px solid #2a2a2a', background: '#1d1d1d'}} />
    {['#ff5f57', '#febc2e', '#28c840'].map((c, i) => <div key={i} style={{position: 'absolute', left: 15 + i * 24, top: tb / 2 - 7, width: 14, height: 14, borderRadius: 7, background: c}} />)}
    <Tx x={w / 2} y={tb / 2 + 1} s={15} c="#9a9a9a" style={{transform: 'translateX(-50%)'}}>{title}</Tx>
    {children}
  </div>
);
type Deal = [string, string, string, string, string];
const DEALS: Deal[][] = [
  [['Axiom Health', 'Sarah Chen · VP Opérations', '48 k$', 'il y a 3 j', 'SC'], ['NovaTech Labs', 'James Park · CTO', '72 k$', 'il y a 1 j', 'JP'], ['Vanta Systems', 'Lisa Moore · CEO', '35 k$', 'il y a 5 j', 'LM']],
  [['Redwood Capital', 'Mark Heller · DAF', '124 k$', 'il y a 2 j', 'MH'], ['Orbit Logistics', 'Amy Torres · COO', '89 k$', 'il y a 4 j', 'AT']],
  [['Stratum Financial', 'David Wu · DSI', '210 k$', 'il y a 1 j', 'DW'], ['Crest Medical', 'Rachel Kim · Directrice', '185 k$', 'il y a 6 j', 'RK']],
  [['Apex Ventures', 'Tom Grant · CEO', '340 k$', 'Aujourd’hui', 'TG'], ['Luminos AI', 'Priya Sharma · VP Tech', '275 k$', 'il y a 1 j', 'PS']],
];
const COLH: [string, string, string][] = [['PROSPECTION', '#7fa6f5', '6'], ['QUALIFIÉ', '#6f7ff2', '5'], ['PROPOSITION', '#eaa23a', '4'], ['CLOSING', '#37c48c', '3']];
const Pipeline: React.FC = () => (
  <>
    <div style={{position: 'absolute', left: 0, top: 45, width: 291, height: 660, background: '#161616', borderRight: '1px solid #262626'}} />
    <Tx x={16} y={76} s={11} c="#6f6f6f" ls={2}>ESPACE</Tx>
    <div style={{position: 'absolute', left: 8, top: 96, width: 267, height: 39, borderRadius: 7, background: '#1d2440'}} />
    <svg width="16" height="16" viewBox="0 0 16 16" style={{position: 'absolute', left: 22, top: 108}}>{[[0, 0], [9, 0], [0, 9], [9, 9]].map(([a, b], i) => <rect key={i} x={a} y={b} width="7" height="7" rx="1" fill="#6f86f5" />)}</svg>
    <Tx x={50} y={116} s={15} c="#f2f2f2">Pipeline</Tx>
    <div style={{position: 'absolute', left: 255, top: 112, width: 7, height: 7, borderRadius: 4, background: '#6f86f5'}} />
    {['Contacts', 'Activités', 'Analyses'].map((t, i) => <Tx key={i} x={50} y={159 + i * 43.5} s={15} c="#bdbdbd">{t}</Tx>)}
    <Tx x={321} y={77} s={17} c="#f2f2f2" w={600}>Pipeline T2 grands comptes</Tx>
    <Tx x={321} y={98} s={12.5} c="#6f6f6f">23 deals actifs · 1,84 M$ au total</Tx>
    <div style={{position: 'absolute', left: 1446, top: 70, width: 68, height: 31, borderRadius: 6, background: '#262626', border: '1px solid #333', fontSize: 13, color: '#bdbdbd', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>Filtrer</div>
    <div style={{position: 'absolute', left: 1526, top: 70, width: 106, height: 31, borderRadius: 6, background: '#27346f', border: '1px solid #3a4a9a', fontSize: 13, color: '#aebdff', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>+ Ajouter</div>
    <div style={{position: 'absolute', left: 292, top: 126, width: 1360, height: 1, background: '#262626'}} />
    {COLH.map(([t, c, n], k) => {
      const x = 318 + k * 334;
      return (
        <div key={k}>
          <Tx x={x} y={155} s={13} c={c} w={700} ls={2}>{t}</Tx>
          <div style={{position: 'absolute', left: x + 290, top: 145, width: 24, height: 20, borderRadius: 10, background: '#262626', color: '#6f6f6f', fontSize: 11, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>{n}</div>
          {DEALS[k].map(([a, b, v, d, ini], j) => (
            <div key={j} style={{position: 'absolute', left: x, top: 185 + j * 120, width: 318, height: 108, borderRadius: 9, background: '#212121', border: '1px solid #2c2c2c'}}>
              <Tx x={17} y={25} s={14.5} c="#f2f2f2" w={600}>{a}</Tx>
              <Tx x={17} y={45} s={12} c="#7a7a7a">{b}</Tx>
              <Tx x={17} y={78} s={14} c={c} w={700}>{v}</Tx>
              <Tx x={146} y={78} s={11} c="#6a6a6a">{d}</Tx>
              <div style={{position: 'absolute', left: 274, top: 66, width: 25, height: 25, borderRadius: 13, background: c, color: '#10131c', fontSize: 9.5, fontWeight: 700, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>{ini}</div>
            </div>
          ))}
        </div>
      );
    })}
    <div style={{position: 'absolute', left: 292, top: 632, width: 1360, height: 1, background: '#262626'}} />
    {[['VALEUR PIPELINE', '1,84 M$', 321], ['VALEUR PONDÉRÉE', '684 k$', 488], ['DEAL MOYEN', '148 k$', 667], ['TAUX DE CLOSING', '31 %', 828]].map(([a, b, x]: any, i) => (
      <div key={i}><Tx x={x} y={652} s={11} c="#5f5f5f" ls={1.6}>{a}</Tx><Tx x={x} y={673} s={17} c={i === 3 ? '#37c48c' : '#f2f2f2'} w={600}>{b}</Tx></div>
    ))}
  </>
);
const Campaign: React.FC = () => {
  const kpi: [string, string, string, string, boolean][] = [['REVENU TOTAL', '284,7', 'k', '+18,4 % vs mois dernier', true], ['NOUVEAU MRR', '62,3', 'k', '+11,2 % vs mois dernier', true], ['LEADS QUALIFIÉS', '1847', '', '+24 % vs mois dernier', true], ['TAUX DE CONV.', '11,7', '%', '-1,3 % vs mois dernier', false]];
  const tr: [string, number, string][] = [['Recherche organique', 38, '#5b6cf0'], ['Social payant', 27, '#2bb38a'], ['E-mail', 19, '#f0a030'], ['Parrainage', 11, '#8fb8f0'], ['Direct', 5, '#5f5f5f']];
  const fu: [string, string, number, string][] = [['Visiteurs', '48 210', 1, '#5b6cf0'], ['Inscriptions', '9 644', 0.2, '#5b6cf0'], ['Essais lancés', '3 856', 0.08, '#2bb38a'], ['Convertis', '1 124', 0.023, '#2bb38a']];
  return (
    <>
      <Tx x={28} y={101} s={21} c="#f2f2f2" w={600}>Performance des campagnes</Tx>
      <Tx x={28} y={128} s={13.5} c="#7a7a7a" ls={0.5}>30 derniers jours · Actualisation auto</Tx>
      <div style={{position: 'absolute', left: 1400, top: 97, width: 88, height: 28, borderRadius: 14, background: '#14291f', border: '1px solid #1f4a33', color: '#3fbf7f', fontSize: 12.5, letterSpacing: 1.5, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>EN DIRECT</div>
      <div style={{position: 'absolute', left: 1499, top: 97, width: 168, height: 28, borderRadius: 7, background: '#1f1f1f', border: '1px solid #2e2e2e', color: '#8a8a8a', fontSize: 12.5, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>1er au 30 juin 2025</div>
      {kpi.map(([a, b, u, d, up], i) => (
        <div key={i} style={{position: 'absolute', left: 29 + i * 414, top: 170, width: 395, height: 145, borderRadius: 12, background: '#1f1f1f', border: '1px solid #2c2c2c'}}>
          <Tx x={27} y={31} s={12} c="#8a8a8a" ls={2.2}>{a}</Tx>
          <Tx x={27} y={76} s={40} c="#f5f5f5" w={700}>{b}<span style={{fontSize: 13, color: '#6a6a6a', fontWeight: 400}}>{u}</span></Tx>
          <Tx x={27} y={113} s={13} c={up ? '#3fbf8f' : '#e05a6a'}>{up ? '▲' : '▼'} {d}</Tx>
        </div>
      ))}
      <div style={{position: 'absolute', left: 29, top: 342, width: 944, height: 285, borderRadius: 12, background: '#1f1f1f', border: '1px solid #2c2c2c'}}>
        <Tx x={27} y={34} s={13} c="#8a8a8a" ls={2.4}>TRAFIC PAR CANAL</Tx>
        {tr.map(([t, p, c], i) => (
          <div key={i}>
            <Tx x={27} y={74 + i * 34.3} s={14.5} c="#d0d0d0">{t}</Tx>
            <div style={{position: 'absolute', left: 174, top: 71 + i * 34.3, width: 666, height: 6, borderRadius: 3, background: '#2c2c2c'}}><div style={{width: 666 * p / 100, height: 6, borderRadius: 3, background: c}} /></div>
            <Tx x={917} y={75 + i * 34.3} s={13.5} c="#8a8a8a" style={{transform: 'translateX(-100%)'}}>{p} %</Tx>
          </div>
        ))}
      </div>
      <div style={{position: 'absolute', left: 992, top: 342, width: 674, height: 285, borderRadius: 12, background: '#1f1f1f', border: '1px solid #2c2c2c'}}>
        <Tx x={27} y={34} s={13} c="#8a8a8a" ls={2.4}>ENTONNOIR DE CONVERSION</Tx>
        {fu.map(([t, n, p, c], i) => (
          <div key={i}>
            <Tx x={27} y={73 + i * 49} s={14} c="#d0d0d0">{t}</Tx>
            <Tx x={647} y={73 + i * 49} s={13.5} c="#8a8a8a" style={{transform: 'translateX(-100%)'}}>{n}</Tx>
            <div style={{position: 'absolute', left: 27, top: 89 + i * 49, width: 620, height: 7, borderRadius: 4, background: '#2c2c2c'}}><div style={{width: Math.max(14, 620 * p), height: 7, borderRadius: 4, background: c}} /></div>
          </div>
        ))}
      </div>
    </>
  );
};

// Entrée par flou, fondu et léger grossissement.
const pop = (f: number, a: number): React.CSSProperties => {
  const p = ease(f, a, a + 11, 0, 1, Easing.out(Easing.quad));
  return {opacity: p, filter: p < 1 ? `blur(${(1 - p) * 18}px)` : undefined, transform: `scale(${0.97 + 0.03 * p})`};
};

const ArtefactsDashboards: React.FC<{showPlate?: boolean}> = ({showPlate = true}) => {
  const f = useCurrentFrame();
  const g = f - 105;
  return (
    <AbsoluteFill style={{background: showPlate ? '#000' : 'transparent'}}>
      {!(f < 4 || (g >= 0 && g < 12)) && <GlowBg />}
      {f < 90 && (f < 4 ? (showPlate ? <AbsoluteFill style={{background: '#0E0E10'}} /> : null) : (
        <>
          <ChatWin x={112} y={66} o={pop(f, 3)}><LineChart /></ChatWin>
          {f >= 29 && <ChatWin x={1062} y={67} o={pop(f, 29)}><BarChart /></ChatWin>}
          {f >= 48 && <ChatWin x={590} y={571} o={pop(f, 48)}><Morning /></ChatWin>}
          {f >= 58 && <Cursor x={686} y={674} kind="arrow" scale={0.8} />}
        </>
      ))}
      {g >= 0 && (g < 12 ? (showPlate ? <AbsoluteFill style={{background: '#0E0E10'}} /> : null) : g < 39 ? (
        <AbsoluteFill style={{transform: `scale(${1 + 0.01 * (g - 12) / 30})`, transformOrigin: '960px 539px'}}>
          <MacWin x={134} y={192} w={1652} h={694} title="Pipeline de deals : ventes grands comptes" tb={44}><Pipeline /></MacWin>
        </AbsoluteFill>
      ) : (
        <AbsoluteFill style={{transform: `scale(${1 + 0.01 * (g - 39) / 30})`, transformOrigin: '960px 539px'}}>
          <MacWin x={112} y={206} w={1696} h={666} title="Tableau de croissance : T2 2025" tb={47}><Campaign /></MacWin>
        </AbsoluteFill>
      ))}
      <SfxTrack cues={SFX} />
    </AbsoluteFill>
  );
};
export default ArtefactsDashboards;

// Signaux sonores exportés pour la bibliothèque (cloud/cues_globaux.py).
export const cues = SFX;
