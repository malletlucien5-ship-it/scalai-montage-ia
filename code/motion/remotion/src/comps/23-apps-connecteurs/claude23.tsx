// Écrans Claude de l'ID 23 : accueil, Personnaliser, Connecteurs, et accueil « après-midi » avec menu Outils.
import React from 'react';
import {Img, staticFile} from '../../shared/rt';
import {SANS, SERIF, ClaudeStar, IPlus, IChats, IProjects, IBriefcase, IPalette, IChevron, IBuilding, IPen, IChart, IBulb, ISearch, IWave, ease} from './ui';
import {IPanel, IDownload, IArrowL} from './claude';
import {GmailLogo, DriveLogo, CalLogo, SlackLogo, GithubLogo, NotionLogo, ZapierLogo, GranolaLogo, RelayLogo, OtterLogo} from './logos';

const Tx: React.FC<{x: number; y: number; s: number; c: string; w?: number; ff?: string; children: React.ReactNode; style?: React.CSSProperties}> = ({x, y, s, c, w = 400, ff = SANS, children, style}) => (
  <div style={{position: 'absolute', left: x, top: y - s * 0.62, fontSize: s, color: c, fontWeight: w, fontFamily: ff, whiteSpace: 'nowrap', lineHeight: 1.2, ...style}}>{children}</div>
);

type IP = {size?: number; color?: string; sw?: number; style?: React.CSSProperties};
const Svg: React.FC<IP & {children: React.ReactNode}> = ({size = 24, color = '#cfcfcc', sw = 1.7, style, children}) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={sw} strokeLinecap="round" strokeLinejoin="round" style={style}>{children}</svg>
);
const IScroll: React.FC<IP> = (p) => <Svg {...p}><path d="M7 4h11a2 2 0 0 1 2 2v1h-4M7 4a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h9a2 2 0 0 0 2-2V7M7 4a2 2 0 0 1 2 2v1M9 11h6M9 15h6" /></Svg>;
const IPlug: React.FC<IP> = (p) => <Svg {...p}><rect x="4" y="11" width="9" height="9" rx="1.5" /><rect x="14" y="4" width="6" height="6" rx="1.5" /><path d="M8.5 11V8a1 1 0 0 1 1-1h4.5M17 10v4a1 1 0 0 1-1 1h-3" /></Svg>;
const IGhost: React.FC<IP> = (p) => <Svg {...p}><path d="M5 20V11a7 7 0 0 1 14 0v9l-2.3-1.6L14.3 20 12 18.4 9.7 20l-2.4-1.6z" /><path d="M9.5 11h.01M14.5 11h.01" /></Svg>;
const IKebabV: React.FC<IP> = (p) => <Svg {...p}><path d="M12 5h.01M12 12h.01M12 19h.01" strokeWidth={3} /></Svg>;
const IToolbox: React.FC<IP> = (p) => (
  <svg width={p.size} height={(p.size ?? 24) * 0.82} viewBox="0 0 110 90" fill="none" stroke={p.color} strokeWidth={4} strokeLinejoin="round" style={p.style}>
    <path d="M40 20v-10a6 6 0 0 1 6-6h18a6 6 0 0 1 6 6v10" /><rect x="3" y="20" width="104" height="67" rx="10" />
    <path d="M3 48h26M47 48h16M81 48h26" /><rect x="29" y="40" width="18" height="17" rx="3" /><rect x="63" y="40" width="18" height="17" rx="3" />
  </svg>
);

// Barre latérale de l'accueil Claude (8 icônes).
const Side: React.FC<{hl?: number}> = ({hl = -1}) => {
  const ic = [IPanel, IPlus, ISearch, IChats, IProjects, IBriefcase, IPalette, IChevron];
  const ys = [26, 81, 118, 156, 194, 232, 270, 308];
  return (
    <div style={{position: 'absolute', left: 0, top: 0, width: 45, height: 765, borderRight: '1.5px solid #292927'}}>
      {ic.map((I, i) => (
        <div key={i} style={{position: 'absolute', left: 3, top: ys[i] - 17, width: 34, height: 34, borderRadius: i === 1 ? 17 : 8,
          background: i === 1 ? '#33332f' : i === hl ? '#2d2d2a' : 'transparent', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
          <I size={i === 1 ? 15 : i === 0 ? 18 : i === 7 ? 15 : 19} color={i === 0 || i === 7 ? '#8e8c87' : '#cfcdc8'} sw={1.6} />
        </div>
      ))}
      <IDownload size={19} color="#cfcdc8" sw={1.6} style={{position: 'absolute', left: 10, top: 666}} />
      <div style={{position: 'absolute', left: 0, top: 713, width: 40, height: 40}}>
        <Img src={staticFile('lucien-rond.png')} style={{width: 40, height: 40, borderRadius: 20}} />
        <div style={{position: 'absolute', right: -3, bottom: -3, width: 15, height: 15, borderRadius: 4, background: '#2b2b28', border: '1px solid #444', display: 'flex', alignItems: 'center', justifyContent: 'center'}}><IBuilding size={10} color="#bbb" sw={1.6} /></div>
      </div>
    </div>
  );
};

export const HomeScreen: React.FC<{tip: number}> = ({tip}) => {
  const chips: [number, number, React.ReactNode, string][] = [
    [505, 94, <IPen size={17} color="#a9a7a2" sw={1.5} />, 'Écrire'], [606, 130, <IChart size={17} color="#a9a7a2" sw={1.5} />, 'Stratégie'],
    [743, 120, <IBriefcase size={17} color="#a9a7a2" sw={1.5} />, 'Carrière'], [870, 196, <IBulb size={17} color="#a9a7a2" sw={1.5} />, 'Au choix de Claude'],
    [1073, 150, <GmailLogo size={15} />, 'Depuis Gmail'],
  ];
  return (
    <div style={{position: 'absolute', inset: 0, fontFamily: SANS}}>
      <Side hl={tip > 0 ? 5 : -1} />
      <IGhost size={21} color="#bdbbb6" style={{position: 'absolute', left: 1620, top: 18}} />
      <div style={{position: 'absolute', left: 779, top: 151, height: 39, padding: '0 12px 0 11px', borderRadius: 7, background: '#141413', display: 'flex', alignItems: 'center', gap: 8, fontSize: 16.5, color: '#bdbbb6'}}>
        <IBuilding size={17} color="#a9a7a2" sw={1.5} />Mallet Media
      </div>
      <div style={{position: 'absolute', left: 0, right: 0, top: 227, display: 'flex', justifyContent: 'center', paddingLeft: 45, gap: 12, alignItems: 'center'}}>
        <ClaudeStar size={40} /><span style={{fontFamily: SERIF, fontSize: 46, color: '#e8e6e1', fontWeight: 300, letterSpacing: -0.6}}>Te revoilà, Lucien</span>
      </div>
      <div style={{position: 'absolute', left: 469, top: 327, width: 771, height: 138, borderRadius: 20, background: '#2b2b28', border: '1.5px solid #353532', boxSizing: 'border-box'}}>
        <Tx x={24} y={35} s={18} c="#8e8c87"><span style={{borderLeft: '1.5px solid #ddd', marginRight: 1}} />Tape / pour les skills</Tx>
        <IPlus size={21} color="#cfcdc8" style={{position: 'absolute', left: 27, top: 92}} />
        <Tx x={600} y={103} s={16} c="#c6c4bf">Sonnet 4.6 <span style={{fontSize: 11}}>⌄</span></Tx>
        <IWave size={22} color="#cfcdc8" style={{position: 'absolute', left: 725, top: 92}} />
      </div>
      {chips.map(([x, w, ic, t], i) => (
        <div key={i} style={{position: 'absolute', left: x, top: 484, width: w, height: 36, borderRadius: 8, border: '1px solid #353532', background: '#232321',
          display: 'flex', alignItems: 'center', gap: 7, paddingLeft: 11, boxSizing: 'border-box', fontSize: 15.5, color: '#c9c7c2', whiteSpace: 'nowrap'}}>{ic}{t}</div>
      ))}
      {tip > 0 && (
        <div style={{position: 'absolute', left: 48, top: 218, height: 27, padding: '0 9px', borderRadius: 6, background: '#fff', color: '#111', fontSize: 14, fontWeight: 500,
          display: 'flex', alignItems: 'center', opacity: tip}}>Personnaliser</div>
      )}
    </div>
  );
};

const Nav: React.FC<{sel: number}> = ({sel}) => (
  <>
    <div style={{position: 'absolute', left: 45, top: 0, width: 296, height: 765, borderRight: '1.5px solid #292927'}} />
    <IArrowL size={19} color="#d9d7d2" style={{position: 'absolute', left: 70, top: 20}} />
    <Tx x={106} y={30} s={17.5} c="#eceae5" w={600}>Personnaliser</Tx>
    {sel === 1 && <div style={{position: 'absolute', left: 55, top: 107, width: 276, height: 37, borderRadius: 8, background: '#111110'}} />}
    <IScroll size={19} color="#cfcdc8" style={{position: 'absolute', left: 75, top: 77}} />
    <Tx x={110} y={87} s={16} c="#e3e1dc">Skills</Tx>
    <IPlug size={19} color="#cfcdc8" style={{position: 'absolute', left: 75, top: 115}} />
    <Tx x={110} y={125} s={16} c="#e3e1dc" w={sel === 1 ? 500 : 400}>Connecteurs</Tx>
  </>
);

export const CustomizeScreen: React.FC = () => (
  <div style={{position: 'absolute', inset: 0, fontFamily: SANS}}>
    <Side hl={5} />
    <Nav sel={0} />
    <IToolbox size={110} color="#f0eee9" style={{position: 'absolute', left: 949, top: 168}} />
    <Tx x={1004} y={304} s={29} c="#eceae5" ff={SERIF} style={{transform: 'translateX(-50%)'}}>Personnaliser Claude</Tx>
    <Tx x={1004} y={352} s={15.5} c="#c2c0bb" style={{transform: 'translateX(-50%)'}}>Skills, connecteurs et plugins façonnent ta façon de travailler avec Claude.</Tx>
    {[[410, <IPlug size={18} color="#e3e1dc" />, 'Connecte tes apps', 'Laisse Claude lire et écrire dans les outils que tu utilises déjà.'],
      [519, <IScroll size={18} color="#e3e1dc" />, 'Crée de nouveaux skills', 'Apprends à Claude tes process, les normes de ton équipe et ton expertise.']].map(([y, ic, a, b]: any, i) => (
      <div key={i} style={{position: 'absolute', left: 701, top: y, width: 608, height: 95, borderRadius: 20, background: '#262624', border: '1.5px solid #30302e'}}>
        <div style={{position: 'absolute', left: 21, top: 29, width: 38, height: 38, borderRadius: 19, background: '#1a1a18', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>{ic}</div>
        <Tx x={77} y={36} s={16} c="#eceae5" w={500}>{a}</Tx>
        <Tx x={77} y={61} s={15.5} c="#c2c0bb">{b}</Tx>
      </div>
    ))}
  </div>
);

type Row = [React.ReactNode, string, boolean?];
const WEB: Row[] = [
  [<GithubLogo size={17} color="#fff" />, 'Intégration GitHub'], [<GmailLogo size={16} />, 'Gmail'], [<GranolaLogo size={16} />, 'Granola'], [<RelayLogo size={16} />, 'Relay', true],
];
const OFF: Row[] = [
  [<CalLogo size={16} />, 'Google Agenda'], [<DriveLogo size={16} />, 'Google Drive'], [<NotionLogo size={15} color="#fff" />, 'Notion'], [<OtterLogo size={16} />, 'Otter.ai'],
  [<SlackLogo size={15} />, 'Slack'], [<ZapierLogo size={16} />, 'Zapier', true],
];
export const ConnectorsScreen: React.FC<{mode: 'github' | 'gcal'; detail: number; offDim: number}> = ({mode, detail, offDim}) => {
  const row = ([ic, t, custom]: Row, y: number, sel: boolean, dim: number, k: number) => (
    <div key={k}>
      {sel && <div style={{position: 'absolute', left: 355, top: y - 20, width: 383, height: 40, borderRadius: 8, background: '#111110'}} />}
      <div style={{position: 'absolute', left: 376, top: y - 12, width: 24, height: 24, borderRadius: 6, background: '#2d2d2b', display: 'flex', alignItems: 'center', justifyContent: 'center', opacity: dim}}>{ic}</div>
      <Tx x={416} y={y} s={16.5} c={dim < 1 && !sel ? '#9d9b96' : '#eceae5'} style={{filter: dim < 0.8 && !sel ? 'blur(0.6px)' : undefined}}>
        {t}{custom && <span style={{marginLeft: 9, padding: '2px 5px', borderRadius: 4, background: '#2d2d2b', fontSize: 10.5, color: '#b5b3ae', letterSpacing: 0.4, verticalAlign: 2}}>PERSONNALISÉ</span>}
      </Tx>
    </div>
  );
  return (
    <div style={{position: 'absolute', inset: 0, fontFamily: SANS}}>
      <Side hl={5} />
      <Nav sel={1} />
      <div style={{position: 'absolute', left: 757, top: 0, width: 1.5, height: 765, background: '#292927'}} />
      <Tx x={370} y={32} s={18} c="#eceae5" w={600}>Connecteurs</Tx>
      <ISearch size={20} color="#d9d7d2" style={{position: 'absolute', left: 666, top: 22}} />
      <IPlus size={21} color="#d9d7d2" style={{position: 'absolute', left: 703, top: 22}} />
      <Tx x={372} y={74} s={14} c="#a3a19c">⌄ &nbsp;Web</Tx>
      {WEB.map((r, i) => row(r, 113 + i * 43, mode === 'github' && i === 0, 1, i))}
      <div style={{position: 'absolute', left: 372, top: 277, width: 354, height: 1.5, background: '#2d2d2b'}} />
      <Tx x={372} y={301} s={14} c="#a3a19c">⌄ &nbsp;Non connectés</Tx>
      {OFF.map((r, i) => row(r, 341 + i * 43, mode === 'gcal' && i === 0, mode === 'gcal' && i === 0 ? 1 : offDim, 10 + i))}
      {mode === 'github' ? (
        <>
          <GithubLogo size={30} color="#fff" style={{position: 'absolute', left: 788, top: 17}} />
          <Tx x={837} y={32} s={18} c="#eceae5" w={500}>Intégration GitHub</Tx>
          <div style={{position: 'absolute', left: 1522, top: 14, width: 130, height: 36, borderRadius: 7, background: '#3a3a38', color: '#eceae5', fontSize: 15.5, fontWeight: 500,
            display: 'flex', alignItems: 'center', justifyContent: 'center'}}>Déconnecter</div>
          <Tx x={786} y={103} s={16} c="#d9d7d2">Connecte ton compte GitHub pour ouvrir tes dépôts à Claude, dans tous ses produits.</Tx>
          {[['Chat', 'joins des fichiers d’un dépôt quand tu poses une question à Claude.'], ['Projets', 'synchronise les fichiers d’un dépôt pour que Claude ait toujours ton code en contexte.'],
            ['Claude Code', 'choisis tes dépôts, parcours les branches et suis les pull requests à distance.'], ['Et plus', 'la sélection des dépôts alimente la revue de code, l’admin et d’autres fonctions.']].map(([a, b], i) => (
            <div key={i}>
              <div style={{position: 'absolute', left: 797, top: 137 + i * 27, width: 5, height: 5, borderRadius: 3, background: '#d9d7d2'}} />
              <Tx x={813} y={140 + i * 27} s={16} c="#d9d7d2"><b style={{color: '#f0eee9', fontWeight: 600}}>{a}</b> : {b}</Tx>
            </div>
          ))}
        </>
      ) : (
        <div style={{opacity: detail}}>
          <IKebabV size={22} color="#d9d7d2" style={{position: 'absolute', left: 1629, top: 20}} />
          <div style={{position: 'absolute', left: 1181, top: 306, width: 64, height: 64, borderRadius: 13, background: '#2d2d2b', border: '1.5px solid #3a3a37', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
            <CalLogo size={36} />
          </div>
          <Tx x={1213} y={403} s={17.5} c="#bdbbb6" style={{transform: 'translateX(-50%)'}}>Tu n’es pas encore connecté à Google Agenda.</Tx>
          <div style={{position: 'absolute', left: 1156, top: 434, width: 114, height: 37, borderRadius: 8, background: '#f3f2ee', color: '#111', fontSize: 16, fontWeight: 600,
            display: 'flex', alignItems: 'center', justifyContent: 'center'}}>Connecter</div>
        </div>
      )}
    </div>
  );
};

// ---------- 23b : accueil « après-midi » (fenêtre 1656 x 914) ----------
const Toggle: React.FC<{on: number}> = ({on}) => (
  <div style={{position: 'absolute', right: 25, top: -15, width: 50, height: 30, borderRadius: 15, background: `rgba(${58 - 2 * on * 0},${132},${245},${on})`, boxShadow: `inset 0 0 0 30px rgba(70,70,68,${1 - on})`}}>
    <div style={{position: 'absolute', left: 4 + 20 * on, top: 4, width: 22, height: 22, borderRadius: 11, background: '#fff'}} />
  </div>
);
export const AfternoonScreen: React.FC<{f: number}> = ({f}) => {
  const greet = ease(f, 4, 22);
  const hov = ease(f, 16, 19) * (1 - ease(f, 30, 34));
  const rows: [React.ReactNode, string, number, number][] = [
    [<GmailLogo size={27} />, 'Gmail', 30, 40], [<DriveLogo size={27} />, 'Google Drive', 51, 58], [<SlackLogo size={25} />, 'Slack', 69, 75], [<NotionLogo size={26} color="#000" />, 'Notion', 80, 999],
  ];
  const K = rows.reduce((a, r) => a + ease(f, r[2], r[2] + 5), 0);
  const open = ease(f, 28, 34);
  const y0 = 718 - 69 * (K - 1);
  return (
    <div style={{position: 'absolute', inset: 0, fontFamily: SANS}}>
      <div style={{position: 'absolute', left: 0, right: 0, top: 283, display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 10, opacity: greet, paddingRight: 10}}>
        <svg width="30" height="30" viewBox="0 0 24 24"><g stroke="#e0775a" strokeWidth="2.4" strokeLinecap="round">{[0, 45, 90, 135].map((a) => <path key={a} d="M12 3v18" transform={`rotate(${a} 12 12)`} />)}</g></svg>
        <span style={{fontFamily: SERIF, fontSize: 40, color: '#f0eee9', fontWeight: 400, letterSpacing: -0.4}}>Bon après-midi, Lucien</span>
      </div>
      <Tx x={840} y={351} s={19} c="#b9b7b2" style={{transform: 'translateX(-50%)', opacity: greet}}>Sur quoi veux-tu que Claude travaille aujourd’hui ?</Tx>
      <div style={{position: 'absolute', left: 319, top: 725, width: 1045, height: 139, borderRadius: 18, background: '#252523', border: '1.5px solid #30302e', boxSizing: 'border-box'}}>
        <Tx x={26} y={38} s={19} c="#8e8c87">Comment puis-je t’aider aujourd’hui ?</Tx>
        <div style={{position: 'absolute', left: 23, top: 82, width: 50, height: 42, borderRadius: 9, border: '1px solid #353532', background: `rgba(224,119,90,${0.55 * hov})`}}><IPlus size={20} color="#cfcdc8" style={{position: 'absolute', left: 14, top: 10}} /></div>
        <div style={{position: 'absolute', left: 86, top: 82, width: 94, height: 42, borderRadius: 9, border: '1px solid #353532', display: 'flex', alignItems: 'center', gap: 8, paddingLeft: 13, boxSizing: 'border-box', fontSize: 17, color: '#d9d7d2'}}>
          <svg width="17" height="17" viewBox="0 0 24 24" stroke="#d9d7d2" strokeWidth="2" strokeLinecap="round"><path d="M4 7h16M4 12h16M4 17h10" /></svg>Outils
        </div>
        <Tx x={889} y={104} s={16} c="#9a9893">Sonnet 4.6</Tx>
        <div style={{position: 'absolute', left: 981, top: 83, width: 40, height: 40, borderRadius: 9, background: '#e0775a', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
          <svg width="20" height="20" viewBox="0 0 24 24" stroke="#fff" strokeWidth="2.6" strokeLinecap="round" fill="none"><path d="M12 19V5M6 11l6-6 6 6" /></svg>
        </div>
      </div>
      {open > 0 && (
        <div style={{position: 'absolute', left: 364, top: y0 - 77, width: 526, height: 764 - (y0 - 77), borderRadius: 12, background: '#252523', border: '1.5px solid #353532', overflow: 'hidden',
          boxShadow: '0 12px 40px rgba(0,0,0,0.55)', opacity: open, filter: open < 1 ? `blur(${(1 - open) * 6}px)` : undefined}}>
          <Tx x={24} y={29} s={14.5} c="#8e8c87" w={500} style={{letterSpacing: 1}}>CONNECTEURS</Tx>
          {rows.map(([ic, t, a, on], i) => {
            const vis = i === 3 ? 0.35 * ease(f, a + 2, a + 12) : ease(f, a, a + 10);
            if (f < a) return null;
            return (
              <div key={i} style={{position: 'absolute', left: 0, right: 0, top: 77 + 69 * i + 12 * (1 - ease(f, a, a + 7)), opacity: vis}}>
                <div style={{position: 'absolute', left: 24, top: -21, width: 42, height: 42, borderRadius: 9, background: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>{ic}</div>
                <Tx x={83} y={1} s={19} c="#f0eee9" w={500}>{t}</Tx>
                <Toggle on={ease(f, on, on + 5)} />
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
