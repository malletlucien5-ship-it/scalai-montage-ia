import React from 'react';
import {INTER_L, MONO_L} from '../../shared/localFonts';
import {FondMac} from '../../shared/ecranMac';
import {AppTile, ChromeLogo, Ico} from './icones';

// Application ChatGPT pour macOS, thème sombre, telle que filmée par Dan (réf. 177,8-184,4 s).
// Deux repères de mesure :
// - « large » : l'écran 1920x1080 de la réf. 177,8 s (fenêtre x 176-1744, y 50-1030) ;
// - « Z » : la vue zoomée des réf. 178,3-181,8 s, soit large x 1,6 - (231,6 ; 618).
// L'accueil est écrit en coordonnées large ; le menu et les réglages en coordonnées Z (mesurées image par image).
export const ZOOM = 1.6;
export const ZX = 231.6;
export const ZY = 618;
export const zVersLarge = (x: number, y: number): [number, number] => [(x + ZX) / ZOOM, (y + ZY) / ZOOM];
// Vue « Computer use » (réf. 182,6-184,4 s) : même zoom, décalée de (-678 ; +369) par rapport à Z.
export const C2X = -678;
export const C2Y = 369;
export const c2VersZ = (x: number, y: number): [number, number] => [x - C2X, y - C2Y];

const WX = 176;
const WY = 50;
const WW = 1568;
const WH = 980;

const TXT = '#ececec';
const GRIS = '#9b9b9b';

export type EtatApp = {
  vue: 'accueil' | 'reglages';
  nom: string;
  initiales: string;
  menu?: number; // ouverture du menu profil 0..1
  survolMenu?: number; // ligne survolée du menu (0 Usage … 4 Log out), -1 sinon
  survolProfil?: number; // 0..1
  survolAccueil?: string; // ligne survolée de la barre latérale d'accueil
  survolReglage?: string; // ligne survolée de la barre latérale des réglages
  actifReglage?: string; // ligne active
  panneau?: 'general' | 'computer';
  anyOn?: number; // interrupteur Any App 0..1
  survolAny?: number;
  infobulle?: number;
  toast?: number;
  curseurTexte?: number; // barre de saisie clignotante (0/1)
};

const Avatar: React.FC<{d: number; ini: string}> = ({d, ini}) => (
  <div style={{width: d, height: d, borderRadius: d / 2, background: 'radial-gradient(circle at 35% 30%, #f6b44a, #e38d1c)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: INTER_L, fontWeight: 600, fontSize: d * 0.36, color: 'rgba(120,60,0,0.75)', flexShrink: 0}}>
    {ini}
  </div>
);

const abs = (l: number, t: number, extra?: React.CSSProperties): React.CSSProperties => ({position: 'absolute', left: l, top: t, ...extra});
const ligne = (l: number, cy: number, h: number, extra?: React.CSSProperties): React.CSSProperties => ({position: 'absolute', left: l, top: cy - h / 2, height: h, display: 'flex', alignItems: 'center', whiteSpace: 'nowrap', ...extra});

// ---------- Accueil (coordonnées relatives à la fenêtre, repère large) ----------
const ITEMS_ACCUEIL: [string, string, number][] = [
  ['edit', 'New chat', 105],
  ['images', 'Images', 137],
  ['clock', 'Scheduled', 169],
  ['plugin', 'Plugins', 201],
  ['dots', 'Explore', 233],
];

const Accueil: React.FC<{e: EtatApp}> = ({e}) => {
  const ph = e.survolProfil ?? 0;
  return (
    <div style={{position: 'absolute', inset: 0, fontFamily: INTER_L}}>
      {/* barre latérale */}
      <div style={{position: 'absolute', left: 0, top: 0, width: 285, height: WH, background: '#232323', borderRight: '1px solid #2b2b2b'}} />
      <Ico n="sidebar" s={16} c="#a8a8a8" style={abs(15, 16)} />
      <Ico n="back" s={16} c="#a8a8a8" style={abs(48, 16)} />
      <Ico n="fwd" s={16} c="#5e5e5e" style={abs(81, 16)} />
      <div style={ligne(17, 65, 22, {fontSize: 16.5, fontWeight: 600, color: TXT, gap: 4})}>
        ChatGPT <Ico n="chevD" s={13} c="#bdbdbd" w={2} />
      </div>
      <Ico n="search" s={15} c="#b0b0b0" style={abs(224, 57)} />
      <Ico n="bell" s={15} c="#b0b0b0" style={abs(252, 57)} />
      {ITEMS_ACCUEIL.map(([ic, t, y]) => (
        <React.Fragment key={t}>
          {(t === 'New chat' || e.survolAccueil === t) && (
            <div style={{position: 'absolute', left: 9, top: y - 15, width: 267, height: 30, borderRadius: 8, background: t === 'New chat' ? '#353535' : '#2d2d2d'}} />
          )}
          <Ico n={ic} s={15} c="#d6d6d6" style={abs(17, y - 7.5)} />
          <div style={ligne(41, y, 20, {fontSize: 15, color: TXT})}>{t}</div>
        </React.Fragment>
      ))}
      {[['Pinned', 278], ['Projects', 321], ['Recents', 363]].map(([t, y]) => (
        <div key={t as string} style={ligne(17, y as number, 20, {fontSize: 14.5, color: '#8f8f8f', gap: 6})}>
          {t} <Ico n="chevR" s={12} c="#8f8f8f" w={2} />
        </div>
      ))}
      {/* profil */}
      {ph > 0 && <div style={{position: 'absolute', left: 8.75, top: 941, width: 225, height: 31, borderRadius: 7.5, background: '#2c2c2c', opacity: ph}} />}
      <div style={abs(15.5, 946.5)}><Avatar d={19} ini={e.initiales} /></div>
      <div style={ligne(43, 956, 20, {fontSize: 15, color: TXT})}>{e.nom}</div>
      <Ico n="help" s={16} c="#a0a0a0" style={abs(252, 948)} />
      {/* zone principale */}
      <div style={{position: 'absolute', left: 810, top: 8, width: 231, height: 36, borderRadius: 18, background: '#262626'}} />
      <div style={{position: 'absolute', left: 810, top: 8, width: 124, height: 36, borderRadius: 18, background: '#383838'}} />
      <div style={ligne(810, 26, 20, {width: 124, justifyContent: 'center', fontSize: 14, fontWeight: 600, color: '#f4f4f4'})}>Chat</div>
      <div style={ligne(934, 26, 20, {width: 107, justifyContent: 'center', fontSize: 14, fontWeight: 500, color: '#cfcfcf'})}>Work</div>
      <Ico n="refresh" s={17} c="#a0a0a0" style={abs(1536, 16)} />
      <div style={ligne(0, 372, 40, {width: 1852, justifyContent: 'center', fontSize: 28.5, color: '#f2f2f2', letterSpacing: -0.2})}>Where should we begin?</div>
      <div style={{position: 'absolute', left: 595, top: 412, width: 663, height: 45, borderRadius: 23, background: '#2f2f2f', boxShadow: 'inset 0 0 0 1px #393939'}} />
      <Ico n="plus" s={17} c="#d0d0d0" w={2} style={abs(609, 426)} />
      {(e.curseurTexte ?? 1) > 0.5 && <div style={{position: 'absolute', left: 637, top: 426, width: 1.4, height: 18, background: '#d8d8d8'}} />}
      <div style={ligne(639, 435, 20, {fontSize: 15, color: '#8e8e8e'})}>Ask ChatGPT</div>
      <div style={ligne(1115, 435, 20, {fontSize: 14.5, color: '#b5b5b5', gap: 7})}>
        High <Ico n="chevD" s={11} c="#9a9a9a" w={2} />
      </div>
      <Ico n="mic" s={16} c="#c8c8c8" style={abs(1190, 427)} />
      <div style={{position: 'absolute', left: 1220, top: 419.5, width: 30, height: 30, borderRadius: 15, background: '#2f6fe0', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1.6}}>
        {[5, 10, 14, 10, 5].map((h, i) => (
          <div key={i} style={{width: 1.8, height: h, borderRadius: 1, background: '#fff'}} />
        ))}
      </div>
    </div>
  );
};

// ---------- Menu profil (coordonnées Z) ----------
const MENU: [string, string, number][] = [
  ['gauge', 'Usage remaining', 737],
  ['pet', 'Hide pet', 784],
  ['send', 'Invite a friend', 831],
  ['gear', 'Settings', 879],
  ['logout', 'Log out', 926],
];

const MenuProfil: React.FC<{e: EtatApp}> = ({e}) => {
  const m = e.menu ?? 0;
  if (m <= 0) return null;
  return (
    <div style={{position: 'absolute', left: 0, top: 0, opacity: Math.min(1, m * 1.4), transform: `translateY(${(1 - m) * 10}px) scale(${0.97 + 0.03 * m})`, transformOrigin: '250px 950px', fontFamily: INTER_L}}>
      <div style={{position: 'absolute', left: 65, top: 622, width: 427, height: 333, borderRadius: 22, background: '#262626', boxShadow: 'inset 0 0 0 1.5px #383838, 0 10px 30px rgba(0,0,0,0.45)'}} />
      <div style={abs(85, 650)}><Avatar d={28} ini={e.initiales} /></div>
      <div style={ligne(124, 652, 26, {fontSize: 20.5, color: TXT})}>{e.nom}</div>
      <div style={ligne(124, 679, 24, {fontSize: 18.5, color: GRIS})}>Plus</div>
      <div style={{position: 'absolute', left: 85, top: 706, width: 387, height: 1.5, background: '#3a3a3a'}} />
      {MENU.map(([ic, t, y], i) => (
        <React.Fragment key={t}>
          {e.survolMenu === i && <div style={{position: 'absolute', left: 75, top: y - 21, width: 407, height: 42, borderRadius: 11, background: '#353535'}} />}
          <Ico n={ic} s={23} c="#cfcfcf" w={1.6} style={abs(86, y - 11.5)} />
          <div style={ligne(121, y, 28, {fontSize: 21, color: TXT})}>{t}</div>
        </React.Fragment>
      ))}
      <Ico n="chevR" s={18} c="#9a9a9a" w={2} style={abs(451, 728)} />
      <div style={ligne(446, 879, 24, {fontSize: 17, color: GRIS})}>⌘,</div>
    </div>
  );
};

// ---------- Réglages (coordonnées Z) ----------
const SIDEBAR_REGLAGES: [string, string, number][] = [
  ['person', 'Parental controls', 17],
  ['person', 'Trusted contact', 69],
  ['mic', 'Voice', 120],
  ['shield', 'Configuration', 171],
  ['smile', 'Personalization', 222],
  ['pet', 'Pets', 274],
  ['keyboard', 'Keyboard shortcuts', 325],
  ['gauge', 'Usage & billing', 376],
  ['openai', 'Account', 427],
  ['pointer', 'Computer use', 545],
  ['dashed', 'Appshots', 596],
  ['plugin', 'Plugins', 647],
  ['browser', 'Browser', 698],
  ['anchor', 'Hooks', 815],
  ['globe', 'Connections', 867],
  ['branch', 'Git', 918],
  ['monitor', 'Environments', 969],
  ['worktree', 'Worktrees', 1020],
];
const AU_DESSUS: [string, string, number][] = [
  ['gear', 'General', -290],
  ['smile', 'Appearance', -239],
  ['bell', 'Notifications', -188],
  ['person', 'Data controls', -137],
  ['shield', 'Security', -86],
  ['person', 'Memory', -35],
];

const Interrupteur: React.FC<{cx: number; cy: number; on: number}> = ({cx, cy, on}) => (
  <div style={{position: 'absolute', left: cx - 26, top: cy - 15, width: 52, height: 30, borderRadius: 15, background: on > 0.5 ? '#2f7cf6' : '#3a3a3a', boxShadow: on > 0.5 ? undefined : 'inset 0 0 0 1px #4a4a4a'}}>
    <div style={{position: 'absolute', left: 3 + 22 * on, top: 3, width: 24, height: 24, borderRadius: 12, background: '#fdfdfd', boxShadow: '0 1px 3px rgba(0,0,0,0.4)'}} />
  </div>
);

const Carte: React.FC<{l: number; t: number; w: number; h: number; children?: React.ReactNode}> = ({l, t, w, h, children}) => (
  <div style={{position: 'absolute', left: l, top: t, width: w, height: h, borderRadius: 22, background: '#212121', boxShadow: 'inset 0 0 0 1.5px #2c2c2c', overflow: 'hidden'}}>{children}</div>
);

const PanneauGeneral: React.FC = () => {
  const rows: [string, string, string | null, number][] = [
    ['Projectless task folder', 'The location where tasks started outside', 'of projects store their data by default.', 266],
    ['Default file open destination', 'Where files and folders open by default', null, 392],
    ['Language', 'Language for the app UI', null, 492],
    ['Show in menu bar', 'Keep ChatGPT in the macOS menu bar when the main window is closed', null, 592],
    ['Bottom panel', 'Show the bottom panel control in the app header', null, 692],
    ['Default terminal location', 'Choose where the terminal shortcut and environment actions open terminal tabs', null, 792],
    ['Prevent sleep while running', 'Keep your computer awake while ChatGPT is running a task', null, 893],
    ['Speed', 'Choose how quickly ChatGPT runs across chats, subagents, and compaction', null, 993],
  ];
  return (
    <>
      <Carte l={884} t={-160} w={1640} h={246} />
      {[
        ['When ChatGPT runs with full access, it can edit any file on your computer and run', 0],
        ['commands with network, without your approval. This significantly increases the', 26],
        ['risk of data loss, leaks, or unexpected behavior.\u00a0', 52],
      ].map(([t, y], i) => (
        <div key={i} style={ligne(911, y as number, 26, {fontSize: 20, color: '#c4c4c4'})}>
          {t}
          {i === 2 && (
            <>
              <span style={{color: '#4a9cf5', whiteSpace: 'pre'}}>Learn more</span>
              <span style={{whiteSpace: 'pre'}}>{'\u00a0about elevated risks.'}</span>
            </>
          )}
        </div>
      ))}
      <div style={ligne(883, 186, 28, {fontSize: 21, color: '#e6e6e6'})}>General</div>
      <Carte l={884} t={230} w={1640} h={900} />
      {rows.map(([t, d1, d2, y], i) => (
        <React.Fragment key={t}>
          {i > 0 && <div style={{position: 'absolute', left: 911, top: y - 37, width: 1590, height: 1.5, background: '#2d2d2d'}} />}
          <div style={ligne(911, y, 26, {fontSize: 20.5, fontWeight: 500, color: TXT})}>{t}</div>
          <div style={ligne(911, y + 32, 26, {fontSize: 19.5, color: GRIS})}>{d1}</div>
          {d2 && <div style={ligne(911, y + 58, 26, {fontSize: 19.5, color: GRIS})}>{d2}</div>}
        </React.Fragment>
      ))}
      <div style={ligne(1686, 293, 26, {fontFamily: MONO_L, fontSize: 19, color: '#c8c8c8'})}>/Users/lucien…uments</div>
      <div style={{position: 'absolute', left: 1895, top: 385, width: 160, height: 44, borderRadius: 12, background: '#2c2c2c'}} />
    </>
  );
};

const PanneauComputer: React.FC<{e: EtatApp}> = ({e}) => {
  const on = e.anyOn ?? 0;
  const sa = e.survolAny ?? 0;
  const tb = e.infobulle ?? 0;
  const to = e.toast ?? 0;
  const apps: [React.ReactNode, string, number][] = [
    [<ChromeLogo s={44} />, 'Google Chrome', 508],
    [<div style={{width: 48, height: 48, borderRadius: 10, background: '#001e36', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: INTER_L, fontWeight: 700, fontSize: 25, color: '#31a8ff'}}>Ps</div>, 'Adobe Photoshop 2026', 607],
    [<div style={{width: 48, height: 48, borderRadius: 10, background: '#00005b', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: INTER_L, fontWeight: 700, fontSize: 25, color: '#9999ff'}}>Pr</div>, 'Adobe Premiere', 706],
    [<div style={{width: 48, height: 48, borderRadius: 24, background: 'radial-gradient(circle, #9a9a9a 0%, #5d5d5d 60%, #c9c9c9 100%)', display: 'flex', alignItems: 'center', justifyContent: 'center'}}><Ico n="gear" s={34} c="#2f2f2f" w={2} /></div>, 'System Settings', 805],
    [<div style={{width: 48, height: 48, borderRadius: 11, background: 'linear-gradient(135deg, #8b5cf6, #6d28d9)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: INTER_L, fontWeight: 700, fontSize: 17, color: '#fff', letterSpacing: -1}}>⊞0</div>, 'logioptionsplus', 904],
    [<div style={{width: 48, height: 48, borderRadius: 11, background: 'linear-gradient(180deg, #7ed957, #3fae2a)', display: 'flex', alignItems: 'center', justifyContent: 'center'}}><Ico n="plus" s={26} c="#fff" w={3} /></div>, '4K Video Downloader+', 1003],
  ];
  return (
    <>
      <div style={ligne(884, -321, 44, {fontSize: 32, color: '#f0f0f0', letterSpacing: -0.3})}>Computer use</div>
      <div style={ligne(884, -270, 28, {fontSize: 20.5, color: GRIS})}>Manage how ChatGPT uses other applications on your computer</div>
      <div style={ligne(884, -167, 28, {fontSize: 21, color: '#e6e6e6'})}>Control</div>
      <Carte l={885} t={-123} w={1266} h={317}>
        {sa > 0 && <div style={{position: 'absolute', left: 0, top: 0, width: 1266, height: 106, background: '#2c2c2c', opacity: sa}} />}
      </Carte>
      <div style={abs(913, -100)}><AppTile s={62} kind="any" /></div>
      <div style={ligne(998, -85, 28, {fontSize: 21, color: TXT})}>Any App</div>
      <div style={ligne(998, -53, 28, {fontSize: 19.5, color: GRIS})}>Let ChatGPT control apps on your computer</div>
      <Interrupteur cx={2098} cy={-69} on={on} />
      <div style={{position: 'absolute', left: 912, top: -17, width: 1212, height: 1.5, background: '#2d2d2d'}} />
      <div style={abs(913, 5)}><AppTile s={62} kind="chrome" /></div>
      <div style={ligne(998, 21, 28, {fontSize: 21, color: TXT})}>Google Chrome</div>
      <div style={{position: 'absolute', left: 998, top: 47, width: 12, height: 12, borderRadius: 6, background: '#fd6564'}} />
      <div style={ligne(1024, 54, 28, {fontSize: 19.5, color: GRIS})}>Browser extension not installed</div>
      <div style={{...ligne(2035, 37, 40, {fontSize: 21, color: TXT, justifyContent: 'center'}), width: 89, borderRadius: 10, background: '#2c2c2c'}}>Install</div>
      <div style={{position: 'absolute', left: 912, top: 89, width: 1212, height: 1.5, background: '#2d2d2d'}} />
      <div style={abs(913, 111)}><AppTile s={62} kind="excel" /></div>
      <div style={ligne(998, 127, 28, {fontSize: 21, color: TXT})}>Microsoft Excel</div>
      <div style={ligne(998, 159, 28, {fontSize: 19.5, color: GRIS})}>Let ChatGPT use Microsoft Excel add-in for additional control</div>
      <Interrupteur cx={2098} cy={142} on={1} />
      <Carte l={885} t={208} w={1266} h={106} />
      <div style={abs(915, 231)}><AppTile s={60} kind="locked" /></div>
      <div style={ligne(998, 246, 28, {fontSize: 21, color: TXT})}>Locked use</div>
      <div style={ligne(998, 278, 28, {fontSize: 19.5, color: GRIS})}>
        Let ChatGPT use your Mac when it&apos;s locked.&nbsp;<span style={{color: '#4a9cf5'}}>Learn more</span>
      </div>
      <Interrupteur cx={2098} cy={261} on={0} />
      <div style={ligne(884, 415, 28, {fontSize: 21, color: '#e6e6e6'})}>Always-allowed apps</div>
      <Carte l={885} t={459} w={1266} h={700} />
      {apps.map(([ic, t, y], i) => (
        <React.Fragment key={t}>
          {i > 0 && <div style={{position: 'absolute', left: 912, top: y - 50, width: 1212, height: 1.5, background: '#2d2d2d'}} />}
          <div style={{position: 'absolute', left: 916, top: y - 24, width: 48, height: 48, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>{ic}</div>
          <div style={ligne(990, y, 28, {fontSize: 21, color: TXT})}>{t}</div>
          <div style={{position: 'absolute', left: 2075, top: y - 24, width: 48, height: 48, borderRadius: 11, background: '#3a2627', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
            <Ico n="trash" s={26} c="#ef5b5f" w={1.8} />
          </div>
        </React.Fragment>
      ))}
      {tb > 0 && (
        <div style={{...ligne(1980, -114, 32, {fontSize: 17, color: '#f2f2f2', justifyContent: 'center'}), width: 234, borderRadius: 7, background: '#1d1d1d', boxShadow: 'inset 0 0 0 1px #3c3c3c', opacity: tb}}>
          Enable Computer Use
        </div>
      )}
      {to > 0 && (
        <div style={{position: 'absolute', left: 1305, top: -374 - (1 - to) * 18, width: 443, height: 67, borderRadius: 14, background: '#0b2614', boxShadow: 'inset 0 0 0 1.5px #1f5c33', opacity: to, display: 'flex', alignItems: 'center', gap: 14, paddingLeft: 23, boxSizing: 'border-box'}}>
          <Ico n="check" s={24} c="#3fcf77" w={1.8} />
          <span style={{fontFamily: INTER_L, fontSize: 23.5, color: '#45d07c', whiteSpace: 'nowrap'}}>Computer Use plugin enabled</span>
          <Ico n="close" s={18} c="#45d07c" w={2} style={{marginLeft: 12}} />
        </div>
      )}
    </>
  );
};

const Reglages: React.FC<{e: EtatApp}> = ({e}) => (
  <div style={{position: 'absolute', inset: 0, fontFamily: INTER_L}}>
    <div style={{position: 'absolute', left: 50, top: -538, width: 455, height: 1568, background: '#232323', borderRight: '1.5px solid #2b2b2b'}} />
    {[...AU_DESSUS, ...SIDEBAR_REGLAGES].map(([ic, t, y]) => {
      const actif = e.actifReglage === t;
      const survol = e.survolReglage === t;
      return (
        <React.Fragment key={t}>
          {(actif || survol) && <div style={{position: 'absolute', left: 63, top: y - 25, width: 409, height: 50, borderRadius: 12, background: actif ? '#353535' : '#303030'}} />}
          <Ico n={ic} s={24} c="#cfcfcf" w={1.6} style={abs(77, y - 12)} />
          <div style={ligne(116, y, 30, {fontSize: 22.5, color: TXT})}>{t}</div>
        </React.Fragment>
      );
    })}
    <Ico n="arrowUR" s={20} c="#9a9a9a" w={1.8} style={abs(436, 417)} />
    <div style={ligne(77, 496, 28, {fontSize: 21.5, color: '#8a8a8a'})}>Integrations</div>
    <div style={ligne(77, 767, 28, {fontSize: 21.5, color: '#8a8a8a'})}>Coding</div>
    <div style={{position: 'absolute', left: 490, top: -200, width: 8, height: 1093, borderRadius: 4, background: '#3d3d3d'}} />
    {e.panneau === 'computer' ? <PanneauComputer e={e} /> : <PanneauGeneral />}
  </div>
);

// Écran complet (repère large). Le parent applique la caméra.
export const EcranChatGPT: React.FC<{e: EtatApp; children?: React.ReactNode}> = ({e, children}) => (
  <div style={{position: 'absolute', left: 0, top: 0, width: 1920, height: 1080}}>
    <FondMac />
    <div style={{position: 'absolute', left: WX, top: WY, width: WW, height: WH, borderRadius: 12, overflow: 'hidden', background: '#161616', boxShadow: '0 0 0 1px rgba(255,255,255,0.08), 0 30px 80px rgba(0,0,0,0.55)'}}>
      {e.vue === 'accueil' && <Accueil e={e} />}
      {/* calque Z : 1 px Z = 1/1,6 px large ; origine = coin haut gauche de la fenêtre (Z 50 ; -538) */}
      <div style={{position: 'absolute', left: 0, top: 0, width: WW * ZOOM, height: WH * ZOOM, transform: `scale(${1 / ZOOM})`, transformOrigin: '0 0'}}>
        <div style={{position: 'absolute', left: -50, top: 538, width: 0, height: 0}}>
          {e.vue === 'reglages' && <Reglages e={e} />}
          {e.vue === 'accueil' && <MenuProfil e={e} />}
        </div>
      </div>
    </div>
    {children}
  </div>
);
