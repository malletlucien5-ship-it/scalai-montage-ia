import React from 'react';
import {AbsoluteFill, Easing, interpolate, useCurrentFrame} from '../../shared/rt';
import {INTER_L} from '../../shared/localFonts';
import {Plate} from '../../shared/Plate';
import {SfxCue, SfxTrack} from '../../shared/Sfx';

// iPhone cadre orange à droite, réglages sombres ChatGPT (réf. 851.1-860.1).
// Géométrie mesurée sur des images 1920x1080 (réf. 853.5 et 858) : cadre x 1389→1811, y 112→997, rayon 75,
// bande orange ~9 px, écran x 1400→1800, y 124→986. Cartes x 1418→1783 (#252525, rayon 30), lignes de 65 px.
// Réf. : entrée par le bas (fondu + flou, ~15 images) ; flèche « < » sur « Remote control » ; poussée iOS vers
// la page « Remote control » ; flèche sur « Add connection » ; menu « Pair a new device / SSH » ; coupe franche.
const FPS = 30;
const AT = 916.3; // « s'appelle Remote Access »
const END = 924.15; // fin de « je parle directement à mon téléphone »
const DUR = Math.round((END - AT) * FPS);

// Étapes calées sur la voix de Lucien (s, voix coupée)
const f = (t: number) => Math.round((t - AT) * FPS);
const F_ARROW1 = f(917.1); // « Access »
const F_PUSH = f(919.96); // « dessus »
const F_ARROW2 = f(920.36); // « connectez »
const F_MENU = f(921.0); // « ordinateur »

const SX = 1400;
const SY = 124;
const SW = 400;
const SH = 862;
const x = (v: number) => v - SX;
const y = (v: number) => v - SY;

const TXT = '#F2F2F2';
const GREY = '#9B9B9B';
const CARD = '#252525';
const BG = '#181818';

const Icon: React.FC<{d: string; cx: number; cy: number; color?: string}> = ({d, cx, cy, color = '#E6E6E6'}) => (
  <svg
    width={26}
    height={26}
    viewBox="0 0 24 24"
    fill="none"
    stroke={color}
    strokeWidth={1.8}
    strokeLinecap="round"
    strokeLinejoin="round"
    style={{position: 'absolute', left: x(cx) - 13, top: y(cy) - 13}}
  >
    <path d={d} />
  </svg>
);

const ICONS = {
  contact: 'M12 3a9 9 0 1 0 0 18a9 9 0 1 0 0-18M12 8a4 4 0 1 0 0 8a4 4 0 1 0 0-8M5.6 5.6l3.6 3.6M18.4 5.6l-3.6 3.6M5.6 18.4l3.6-3.6M18.4 18.4l-3.6-3.6',
  safety: 'M4 5l6-2v6c0 3.5-2.6 5.7-6 6.5M10 9h8a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2h-6a2 2 0 0 1-2-2zM15 13v3',
  lock: 'M6 11h12v10H6zM8.5 11V7.5a3.5 3.5 0 0 1 7 0V11M12 15v2',
  monitor: 'M3 5h18v11H3zM9 20h6M12 16v4',
  storage: 'M3 8h18v10H3zM3 12h18M5 8l2-3h10l2 3',
  data: 'M12 3l8 3v5c0 5-3.4 8.4-8 10c-4.6-1.6-8-5-8-10V6zM12 9a2.5 2.5 0 1 0 0 5a2.5 2.5 0 1 0 0-5M8.5 17c.8-1.6 2-2.4 3.5-2.4s2.7.8 3.5 2.4',
  ads: 'M4 10v4h3l7 4V6l-7 4zM17.5 9.5c1 .7 1.5 1.5 1.5 2.5s-.5 1.8-1.5 2.5M7 14l1 5h2.5l-1-4.5',
  flag: 'M5 21V4M5 4h11l-2 4l2 4H5',
  help: 'M12 3a9 9 0 1 0 0 18a9 9 0 1 0 0-18M9.6 9.4a2.5 2.5 0 0 1 4.8.9c0 1.7-2.4 2-2.4 3.7M12 17h.01',
  privacy: 'M4 5l6-2v6c0 3.5-2.6 5.7-6 6.5M10 9h8a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2h-6a2 2 0 0 1-2-2zM13 14.5l1.5 1.5l3-3',
  info: 'M12 3a9 9 0 1 0 0 18a9 9 0 1 0 0-18M12 11v6M12 7.5h.01',
  link: 'M10 14a4 4 0 0 0 5.7 0l3.3-3.3a4 4 0 0 0-5.7-5.7l-1.3 1.3M14 10a4 4 0 0 0-5.7 0L5 13.3a4 4 0 0 0 5.7 5.7l1.3-1.3',
  term: 'M4 4h16v16H4zM8 9l3 3l-3 3M13 15h3',
};

const Chevron: React.FC<{cx: number; cy: number}> = ({cx, cy}) => (
  <svg width={10} height={16} viewBox="0 0 10 16" fill="none" stroke="#6E6E6E" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" style={{position: 'absolute', left: x(cx) - 5, top: y(cy) - 8}}>
    <path d="M2 2l6 6l-6 6" />
  </svg>
);

const Label: React.FC<{lx: number; cy: number; children: React.ReactNode; color?: string; size?: number; weight?: number; lh?: number}> = ({
  lx,
  cy,
  children,
  color = TXT,
  size = 21,
  weight = 400,
  lh = 27,
}) => (
  <div
    style={{
      position: 'absolute',
      left: x(lx),
      top: y(cy),
      transform: 'translateY(-50%)',
      fontSize: size,
      fontWeight: weight,
      lineHeight: `${lh}px`,
      color,
      whiteSpace: 'nowrap',
    }}
  >
    {children}
  </div>
);

const Card: React.FC<{top: number; bottom: number; left?: number; right?: number; radius?: number; bg?: string}> = ({
  top,
  bottom,
  left = 1418,
  right = 1783,
  radius = 30,
  bg = CARD,
}) => <div style={{position: 'absolute', left: x(left), top: y(top), width: right - left, height: bottom - top, borderRadius: radius, background: bg}} />;

const Divider: React.FC<{yy: number; x0?: number; x1?: number}> = ({yy, x0 = 1482, x1 = 1765}) => (
  <div style={{position: 'absolute', left: x(x0), top: y(yy), width: x1 - x0, height: 1.5, background: '#333333'}} />
);

const Toggle: React.FC<{cy: number}> = ({cy}) => (
  <div style={{position: 'absolute', left: x(1687), top: y(cy) - 17, width: 78, height: 34, borderRadius: 17, background: '#3A3A3A'}}>
    <div style={{position: 'absolute', left: 3, top: 3, width: 46, height: 28, borderRadius: 14, background: '#FFFFFF'}} />
  </div>
);

// Page 1 : réglages
const SettingsPage: React.FC = () => {
  const rows: [keyof typeof ICONS, string][] = [
    ['safety', 'Protection'],
    ['lock', 'Sécurité et connexion'],
    ['monitor', 'Accès à distance'],
    ['storage', 'Stockage'],
    ['data', 'Gestion des données'],
    ['ads', 'Publicités'],
  ];
  const rows2: [keyof typeof ICONS, string][] = [
    ['flag', 'Signaler un problème'],
    ['help', "Centre d'aide"],
    ['privacy', 'Confidentialité'],
    ['info', 'À propos'],
  ];
  return (
    <AbsoluteFill style={{background: BG}}>
      <div style={{opacity: 0.35}}>
        <Label lx={1482} cy={176} color={GREY}>
          Contrôle parental
        </Label>
      </div>
      <Card top={208} bottom={663} />
      <Icon d={ICONS.contact} cx={1451} cy={241} color="#8A8A8A" />
      <Label lx={1482} cy={241} color={GREY}>
        Contact de confiance
      </Label>
      <Divider yy={273} />
      {rows.map(([ic, t], i) => {
        const cy = 306 + i * 65;
        return (
          <React.Fragment key={t}>
            <Icon d={ICONS[ic]} cx={1451} cy={cy} />
            <Label lx={1482} cy={cy}>
              {t}
            </Label>
            <Chevron cx={1755} cy={cy} />
            {i < rows.length - 1 ? <Divider yy={cy + 32} /> : null}
          </React.Fragment>
        );
      })}
      <Label lx={1437} cy={710} color={GREY}>
        Aide
      </Label>
      <Card top={737} bottom={1030} />
      {rows2.map(([ic, t], i) => {
        const cy = 768 + i * 65;
        return (
          <React.Fragment key={t}>
            <Icon d={ICONS[ic]} cx={1451} cy={cy} />
            <Label lx={1482} cy={cy}>
              {t}
            </Label>
            <Chevron cx={1755} cy={cy} />
            {i < rows2.length - 1 ? <Divider yy={cy + 32} /> : null}
          </React.Fragment>
        );
      })}
      {/* Bouton fermer */}
      <div
        style={{
          position: 'absolute',
          left: x(1755) - 28,
          top: y(223) - 28,
          width: 56,
          height: 56,
          borderRadius: 28,
          background: '#2A2A2A',
          border: '1.5px solid #454545',
          boxSizing: 'border-box',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <svg width={20} height={20} viewBox="0 0 20 20" stroke="#FFFFFF" strokeWidth={2.2} strokeLinecap="round">
          <path d="M3 3l14 14M17 3L3 17" />
        </svg>
      </div>
      {/* Barre de défilement */}
      <div style={{position: 'absolute', left: x(1796), top: y(660), width: 3.5, height: 230, borderRadius: 2, background: '#5A5A5A'}} />
    </AbsoluteFill>
  );
};

// Page 2 : Accès à distance
const RemotePage: React.FC<{menu: number; pillOpacity: number}> = ({menu, pillOpacity}) => (
  <AbsoluteFill style={{background: BG}}>
    <div
      style={{
        position: 'absolute',
        left: x(1444) - 28,
        top: y(222) - 28,
        width: 56,
        height: 56,
        borderRadius: 28,
        background: '#1F1F1F',
        border: '1.5px solid #3C3C3C',
        boxSizing: 'border-box',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      <svg width={12} height={20} viewBox="0 0 12 20" fill="none" stroke="#FFFFFF" strokeWidth={2.4} strokeLinecap="round" strokeLinejoin="round">
        <path d="M10 2L2 10l8 8" />
      </svg>
    </div>
    <div style={{position: 'absolute', left: 0, width: SW, top: y(222), transform: 'translateY(-50%)', textAlign: 'center', fontSize: 21, fontWeight: 600, color: '#FFFFFF'}}>
      Accès à distance
    </div>
    <Card top={308} bottom={376} />
    <div style={{position: 'absolute', left: x(1452) - 15, top: y(342) - 15, width: 30, height: 30, borderRadius: 15, background: '#000000'}} />
    <Label lx={1480} cy={342}>
      Profil
    </Label>
    <Chevron cx={1755} cy={342} />
    <Label lx={1437} cy={424} color={GREY}>
      Connexions
    </Label>
    <Card top={450} bottom={530} />
    <div style={{opacity: pillOpacity}}>
      <Card top={466} bottom={514} left={1437} right={1765} radius={24} bg="#2F2F2F" />
      <svg width={20} height={20} viewBox="0 0 20 20" stroke="#3E8BFF" strokeWidth={2.2} strokeLinecap="round" style={{position: 'absolute', left: x(1467) - 10, top: y(490) - 10}}>
        <path d="M10 1v18M1 10h18" />
      </svg>
      <Label lx={1494} cy={490} color="#3E8BFF">
        Ajouter une connexion
      </Label>
    </div>
    <Card top={580} bottom={666} />
    <Label lx={1437} cy={623} lh={27}>
      Ouvrir l'accès
      <br />
      automatiquement
    </Label>
    <Toggle cy={624} />
    <Label lx={1437} cy={688} color="#8A8A8A" size={15}>
      Ouvrir directement l'accès à distance.
    </Label>
    <Label lx={1437} cy={740} color={GREY}>
      Saisie
    </Label>
    <Card top={766} bottom={918} />
    <Label lx={1437} cy={809}>
      Afficher l'utilisation
      <br />
      du contexte
    </Label>
    <Toggle cy={810} />
    <Divider yy={853} x0={1437} />
    <Label lx={1437} cy={887}>
      Relances
    </Label>
    <div
      style={{
        position: 'absolute',
        left: x(1653),
        top: y(866),
        width: 110,
        height: 42,
        borderRadius: 21,
        background: '#333333',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 6,
        fontSize: 19,
        color: '#A8A8A8',
      }}
    >
      File
      <svg width={10} height={16} viewBox="0 0 10 16" fill="none" stroke="#A8A8A8" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round">
        <path d="M2 6l3-3l3 3M2 10l3 3l3-3" />
      </svg>
    </div>
    <Label lx={1437} cy={966} color={GREY}>
      Comportement
    </Label>
    {/* Menu contextuel */}
    {menu > 0 ? (
      <div
        style={{
          position: 'absolute',
          left: x(1441),
          top: y(469),
          width: 317,
          height: 126,
          borderRadius: 32,
          background: '#262626',
          border: '1.5px solid #4A4A4A',
          boxSizing: 'border-box',
          boxShadow: '0 10px 30px rgba(0,0,0,0.5)',
          opacity: menu,
          transform: `scale(${0.9 + 0.1 * menu})`,
          transformOrigin: '50% 30%',
          filter: menu < 1 ? `blur(${(1 - menu) * 6}px)` : undefined,
        }}
      >
        <Icon d={ICONS.link} cx={1490 - 1441 + SX} cy={506 - 469 + SY} color="#FFFFFF" />
        <Label lx={1520 - 1441 + SX} cy={506 - 469 + SY}>
          Associer un appareil
        </Label>
        <Icon d={ICONS.term} cx={1490 - 1441 + SX} cy={557 - 469 + SY} color="#FFFFFF" />
        <Label lx={1520 - 1441 + SX} cy={557 - 469 + SY}>
          SSH
        </Label>
      </div>
    ) : null}
  </AbsoluteFill>
);

const Arrow: React.FC<{tipX: number; cy: number; s: number}> = ({tipX, cy, s}) =>
  s <= 0 ? null : (
    <svg
      width={44}
      height={66}
      viewBox="0 0 44 66"
      fill="none"
      stroke="#FFFFFF"
      strokeWidth={10}
      strokeLinecap="round"
      strokeLinejoin="round"
      style={{
        position: 'absolute',
        left: x(tipX) - 4,
        top: y(cy) - 33,
        transform: `scale(${s})`,
        transformOrigin: '10% 50%',
        filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.45))',
      }}
    >
      <path d="M36 6L8 33l28 27" />
    </svg>
  );

const StatusBar: React.FC = () => (
  <div style={{position: 'absolute', left: 0, top: 0, width: SW, height: 46, background: '#000000'}}>
    <div style={{position: 'absolute', left: x(1440), top: y(143), transform: 'translateY(-50%)', fontSize: 18, fontWeight: 600, color: '#FFFFFF'}}>1:20</div>
    <div style={{position: 'absolute', left: x(1505), top: 3, width: 183, height: 35, borderRadius: 18, background: '#000000', boxShadow: 'inset 0 0 0 1px rgba(120,20,20,0.35)'}} />
    <svg width={16} height={12} viewBox="0 0 16 12" style={{position: 'absolute', left: x(1699), top: y(143) - 6}}>
      <rect x={0} y={9} width={2.6} height={3} rx={0.8} fill="#FFFFFF" />
      <rect x={4.4} y={6.5} width={2.6} height={5.5} rx={0.8} fill="#6A6A6A" />
      <rect x={8.8} y={3.5} width={2.6} height={8.5} rx={0.8} fill="#6A6A6A" />
      <rect x={13.2} y={0} width={2.6} height={12} rx={0.8} fill="#6A6A6A" />
    </svg>
    <div style={{position: 'absolute', left: x(1721), top: y(143), transform: 'translateY(-50%)', fontSize: 13, fontWeight: 700, color: '#FFFFFF'}}>LTE</div>
    <div
      style={{
        position: 'absolute',
        left: x(1749),
        top: y(143) - 7,
        width: 25,
        height: 14,
        borderRadius: 4,
        background: '#8E8E8E',
        fontSize: 10,
        fontWeight: 700,
        color: '#000000',
        textAlign: 'center',
        lineHeight: '14px',
      }}
    >
      36
    </div>
  </div>
);

const Phone: React.FC = () => {
  const frame = useCurrentFrame();

  // Poussée iOS : 7 images
  const push = interpolate(frame, [F_PUSH, F_PUSH + 7], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic)});
  const menu = interpolate(frame, [F_MENU, F_MENU + 4], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const pop = (f0: number) => interpolate(frame, [f0, f0 + 3, f0 + 6], [0.2, 1.12, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const a1 = frame >= F_ARROW1 && frame < F_PUSH ? pop(F_ARROW1) : 0;
  const a2 =
    frame >= F_ARROW2 && frame < F_MENU
      ? Math.min(pop(F_ARROW2), interpolate(frame, [F_MENU - 3, F_MENU], [1, 0.3], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}))
      : 0;

  return (
    <AbsoluteFill style={{fontFamily: INTER_L}}>
      {/* Boutons latéraux */}
      {[
        [271, 301],
        [342, 402],
        [435, 496],
      ].map(([t, b]) => (
        <div key={t} style={{position: 'absolute', left: 1380, top: t, width: 12, height: b - t, borderRadius: 3, background: 'linear-gradient(90deg,#B8481A,#F07A2A)'}} />
      ))}
      {[
        [280, 358],
        [582, 637],
      ].map(([t, b]) => (
        <div key={t} style={{position: 'absolute', left: 1808, top: t, width: 13, height: b - t, borderRadius: 3, background: 'linear-gradient(90deg,#F07A2A,#B8481A)'}} />
      ))}
      {/* Cadre orange */}
      <div
        style={{
          position: 'absolute',
          left: 1389,
          top: 112,
          width: 422,
          height: 885,
          borderRadius: 75,
          background: 'linear-gradient(90deg, #C24A1B 0%, #F58329 3%, #FB8A2E 50%, #F58329 97%, #C24A1B 100%)',
          boxShadow: '0 20px 50px rgba(0,0,0,0.45)',
        }}
      />
      <div style={{position: 'absolute', left: 1397, top: 121, width: 406, height: 868, borderRadius: 67, background: '#000000'}} />
      {/* Indicateur d'accueil (posé sur le bas du cadre, comme dans la réf.) */}
      <div style={{position: 'absolute', left: 1553, top: 986, width: 94, height: 6, borderRadius: 3, background: '#9E2E00', zIndex: 2}} />
      {/* Écran */}
      <div style={{position: 'absolute', left: SX, top: SY, width: SW, height: SH, borderRadius: 64, overflow: 'hidden', background: '#000000'}}>
        <div style={{position: 'absolute', left: 0, top: 44, width: SW, height: SH - 44, borderRadius: '34px 34px 0 0', overflow: 'hidden'}}>
          <div style={{position: 'absolute', left: 0, top: -44, width: SW, height: SH}}>
            <div style={{position: 'absolute', inset: 0, transform: `translateX(${-120 * push}px)`}}>
              <SettingsPage />
              <AbsoluteFill style={{background: '#000000', opacity: 0.35 * push}} />
            </div>
            {push > 0 ? (
              <div style={{position: 'absolute', inset: 0, transform: `translateX(${(1 - push) * SW}px)`, boxShadow: '-10px 0 30px rgba(0,0,0,0.5)'}}>
                <RemotePage menu={menu} pillOpacity={1 - menu} />
              </div>
            ) : null}
            <Arrow tipX={1664} cy={436} s={a1} />
            <Arrow tipX={1722} cy={490} s={a2} />
          </div>
        </div>
        <StatusBar />
      </div>
    </AbsoluteFill>
  );
};

const CUES: SfxCue[] = [
  {frame: 1, name: 'whoosh-transition'},
  {frame: F_ARROW1, name: 'pop'},
  {frame: F_PUSH, name: 'clic'},
  {frame: F_ARROW2, name: 'pop'},
  {frame: F_MENU, name: 'clic'},
];

const TelephoneRemote: React.FC<{showPlate?: boolean}> = ({showPlate = true}) => {
  const frame = useCurrentFrame();
  // Entrée : montée par le bas + fondu + flou (réf. 851.15 → 851.65)
  const p = interpolate(frame, [0, 15], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic)});
  const opacity = interpolate(frame, [0, 11], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return (
    <AbsoluteFill style={{overflow: 'hidden'}}>
      <Plate show={showPlate} />
      <AbsoluteFill style={{transform: `translateY(${(1 - p) * 70}px)`, opacity, filter: p < 1 ? `blur(${(1 - p) * 10}px)` : undefined}}>
        <Phone />
      </AbsoluteFill>
      <SfxTrack cues={CUES} />
    </AbsoluteFill>
  );
};

export const meta = {
  id: 'd227-telephone-remote',
  fps: FPS,
  durationInFrames: DUR,
  defaultProps: {showPlate: true},
  occurrences: [{ref: [851.1, 860.1] as [number, number], at: AT, from: 0, durationInFrames: DUR, mode: 'plein' as const}],
};
export default TelephoneRemote;

// Signaux sonores exportés pour la bibliothèque (cloud/cues_globaux.py).
export const cues = CUES;
