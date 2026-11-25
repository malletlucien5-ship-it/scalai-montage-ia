import React from 'react';
import {AbsoluteFill} from '../../shared/rt';
import {loadFont} from '@remotion/google-fonts/Newsreader';
import {Bg, Camera, Cursor, Mic, Chevron, useT, samples, keys, FONT, easeInOut} from './kit';
import {SfxTrack, SfxCue} from '../../shared/Sfx';

const SERIF = loadFont('normal', {weights: ['400', '500']}).fontFamily;

// Référence : 222,99 à 229,80 s (6,81 s).
export const meta = {
  id: '20-instructions-projet', durationInFrames: 204, fps: 30,
  occurrences: [{ref: [222.99, 229.8], from: 0, durationInFrames: 204, mode: 'plein'}],
};

const Z = [0.9262,0.9262,0.9262,0.9262,0.9274,0.9274,0.9279,0.9285,0.9296,0.9296,0.9308,0.9319,0.9330,0.9336,0.9342,0.9353,0.9364,0.9381,0.9393,0.9410,0.9421,0.9432,0.9449,0.9461,0.9478,0.9495,0.9506,0.9523,0.9540,0.9557,0.9574,0.9586,0.9608,0.9620,0.9637,0.9654,0.9665,0.9688,0.9699,0.9722,0.9733,0.9745,0.9767,0.9779,0.9796,0.9813,0.9824,0.9835,0.9852,0.9869,0.9881,0.9892,0.9904,0.9915,0.9926,0.9938,0.9943,0.9955,0.9960,0.9972,0.9977,0.9983,0.9989,0.9994,0.9994,1.0,1.0,1.0];

// Coordonnées finales (fenêtre 68,124 1763x825).
const WX = 68;
const WY = 124;
const TXT = '#ECE9E6';
const DIM = '#8A8783';
const P = (x: number, y: number): React.CSSProperties => ({position: 'absolute', left: x - WX, top: y - WY});

const Ico: React.FC<{x: number; y: number; d: string; s?: number; c?: string; w?: number}> = ({x, y, d, s = 22, c = '#B8B5B0', w = 1.7}) => (
  <svg viewBox="0 0 24 24" width={s} height={s} style={{position: 'absolute', left: x - s / 2 - WX, top: y - s / 2 - WY}}>
    <path d={d} fill="none" stroke={c} strokeWidth={w} strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

const Lock: React.FC = () => (
  <svg viewBox="0 0 24 24" width="0.95em" height="0.95em" style={{verticalAlign: '-0.1em', marginRight: 2}}>
    <path d="M6 11 H18 V20 H6 Z M8.5 11 V8 a3.5 3.5 0 0 1 7 0 V11" fill="none" stroke="currentColor" strokeWidth="2" strokeLinejoin="round" />
  </svg>
);

const Hand: React.FC<{x: number; y: number}> = ({x, y}) => (
  <svg viewBox="0 0 24 26" width={34} height={37} style={{position: 'absolute', left: x - 12, top: y - 3}}>
    <path d="M9 13 V3.5 a1.6 1.6 0 0 1 3.2 0 V11 V9.5 a1.6 1.6 0 0 1 3.2 0 V11.5 V10.5 a1.6 1.6 0 0 1 3.2 0 V12 a1.6 1.6 0 0 1 3.2 0 V17 c0 4 -2.5 7 -6.5 7 h-2 c-2.6 0 -4 -1.2 -5.4 -3.2 L3.4 15.6 a1.7 1.7 0 0 1 2.7 -2 Z" fill="#fff" stroke="#111" strokeWidth="1.3" strokeLinejoin="round" />
    <path d="M12.2 17 V13.5 M15.4 17 V13.5 M18.6 17 V13.5" stroke="#111" strokeWidth="1" strokeLinecap="round" />
  </svg>
);

const TILES = [
  {n: 'Meilleurs_posts_\nLinkedIn_2.docx', l: '135 lignes', k: 'DOCX'},
  {n: 'Workflow_creati\non_contenu.md', l: '60 lignes', k: 'MD'},
  {n: 'Charte_marque.\ndocx', l: '421 lignes', k: 'DOCX'},
  {n: 'Prompt_maitre.\ndocx', l: '135 lignes', k: 'DOCX'},
  {n: 'Export_contacts\n_HubSpot_T2_20\n26.csv', l: '', k: 'CSV'},
];

const Page: React.FC<{filled: boolean}> = ({filled}) => {
  const dy = filled ? 0 : -21; // la ligne Instructions est plus courte avant l'enregistrement
  return (
    <>
      {/* rail d'icônes */}
      <div style={{position: 'absolute', left: 0, top: 0, width: 49, height: 825, borderRight: '1px solid #2F2F2C'}} />
      {/* icônes du rail relevées sur l'original (tracé 1,6 px, gris clair) */}
      <Ico x={90} y={148} d="M5 5 H19 a1.8 1.8 0 0 1 1.8 1.8 V17.2 a1.8 1.8 0 0 1 -1.8 1.8 H5 a1.8 1.8 0 0 1 -1.8 -1.8 V6.8 A1.8 1.8 0 0 1 5 5 Z M12 5 V19" s={20} />
      <div style={{...P(90 - 14, 212 - 14), width: 28, height: 28, borderRadius: 14, background: '#34332F'}} />
      <Ico x={90} y={212} d="M12 6.5 V17.5 M6.5 12 H17.5" s={18} c="#D8D5D0" />
      <Ico x={90} y={253} d="M10 3.8 a6.3 5.8 0 0 0 -5.6 8.6 L3.6 15.6 L6.9 14.6 A6.3 5.8 0 1 0 10 3.8 Z M16.6 9.4 a5.4 5 0 0 1 3 8.4 L20.4 20.6 L17.3 19.8 a5.4 5 0 0 1 -6.4 -1.2" s={23} />
      <Ico x={90} y={294} d="M8.5 3.6 H15.5 M6.3 6.6 H17.7 M4.2 9.6 H19.8 L18.6 19 a1.6 1.6 0 0 1 -1.6 1.4 H7 a1.6 1.6 0 0 1 -1.6 -1.4 Z" s={23} />
      <Ico x={90} y={335} d="M12 2.8 V4.6 M12 10.8 V12.6 M12 18.4 V21.4 M5.2 4.6 H17 L19.4 7.7 L17 10.8 H5.2 Z M18.8 12.6 H7 L4.6 15.5 L7 18.4 H18.8 Z" s={23} />
      <Ico x={90} y={376} d="M6.4 12.2 a5.6 5.6 0 0 1 10.8 -2.3 M7.2 13.6 a3.8 3.8 0 1 0 0.01 0 Z M12.8 11.2 H18.6 a1.4 1.4 0 0 1 1.4 1.4 V19.4 a1.4 1.4 0 0 1 -1.4 1.4 H12.8 a1.4 1.4 0 0 1 -1.4 -1.4 V12.6 a1.4 1.4 0 0 1 1.4 -1.4 Z" s={23} />
      <Ico x={90} y={416} d="M4.6 8 H19.4 a1.4 1.4 0 0 1 1.4 1.4 V18.6 a1.4 1.4 0 0 1 -1.4 1.4 H4.6 a1.4 1.4 0 0 1 -1.4 -1.4 V9.4 A1.4 1.4 0 0 1 4.6 8 Z M8.8 8 V5.4 a1 1 0 0 1 1 -1 H14.2 a1 1 0 0 1 1 1 V8 M3.2 13.6 H20.8" s={23} />
      <Ico x={90} y={509} d="M12 3 a9 9 0 1 0 0 18 c1.5 0 2 -1 1.5 -2.2 c-0.6 -1.4 0.3 -2.8 2 -2.8 H18 a3 3 0 0 0 3 -3 A9 9 0 0 0 12 3 Z M7.5 11 h.01 M10 7 h.01 M15 7.5 h.01" s={23} />
      <Ico x={90} y={857} d="M12 4 V14.5 M7.6 10.2 L12 14.6 L16.4 10.2 M4.2 16.4 V20 H19.8 V16.4" s={21} />
      <div style={{...P(90 - 21, 917 - 21), width: 42, height: 42, borderRadius: 21, background: '#D9D6D0', color: '#1E1E1C', fontSize: 20, fontWeight: 500, textAlign: 'center', lineHeight: '42px'}}>L</div>
      <div style={{...P(98, 917), width: 20, height: 20, borderRadius: 5, background: '#2A2A28', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
        <svg viewBox="0 0 24 24" width={15} height={15}><path d="M5 20 V7 H12 V20 M12 11 H18 V20 M3.5 20 H20.5 M8 10.5 V12 M8 15 V16.5 M15 14 V16.5" fill="none" stroke="#B8B5B0" strokeWidth="1.8" /></svg>
      </div>

      {/* colonne principale */}
      <div style={{...P(237, 219), fontSize: 17.5, color: '#B6B2AE', display: 'flex', alignItems: 'center', gap: 6}}>
        <svg viewBox="0 0 24 24" width={17} height={17}><path d="M19 12 H5 M11 6 L5 12 L11 18" fill="none" stroke="#B6B2AE" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /></svg>
        Tous les projets
      </div>
      <div style={{...P(236, 272), fontFamily: SERIF, fontSize: 32, color: TXT, lineHeight: '42px'}}>Projet 01</div>
      <div style={{...P(236, 322), fontSize: 17.2, color: '#D6D2CE', whiteSpace: 'nowrap'}}>Tu es mon assistant marketing : rédaction, idées de campagne et stratégie de contenu.</div>
      <div style={{...P(236, 356), fontSize: 14.5, color: DIM, whiteSpace: 'nowrap'}}>Créé par toi · <Lock /> Privé</div>
      <Ico x={972} y={288} d="M12 5 h.01 M12 12 h.01 M12 19 h.01" w={3} c="#D0CDC8" />
      <Ico x={1012} y={288} d="M12 3.5 L14.6 9 L20.5 9.6 L16 13.6 L17.3 19.5 L12 16.5 L6.7 19.5 L8 13.6 L3.5 9.6 L9.4 9 Z" s={21} c="#D0CDC8" />
      <div style={{...P(1039, 272), width: 72, height: 33, borderRadius: 7, background: '#302F2C', color: TXT, fontSize: 16, fontWeight: 600, textAlign: 'center', lineHeight: '33px'}}>Partager</div>
      <div style={{...P(236, 411), width: 876, height: 150, borderRadius: 18, background: '#2B2B29', border: '1px solid #353431', boxSizing: 'border-box'}}>
        <div style={{position: 'absolute', left: 25, top: 26, fontSize: 18, color: DIM}}>Comment puis-je t’aider aujourd’hui ?</div>
        <div style={{position: 'absolute', left: 30, top: 100, width: 20, height: 20}}><svg viewBox="0 0 24 24" width={20} height={20}><path d="M12 4 V20 M4 12 H20" stroke="#D0CDC8" strokeWidth="2" strokeLinecap="round" /></svg></div>
        <div style={{position: 'absolute', left: 601, top: 99, fontSize: 16, color: '#D0CDC8', display: 'flex', alignItems: 'center', gap: 7}}>Sonnet 4.6 <span style={{color: DIM}}>Faible</span><Chevron size={13} color={DIM} /></div>
        <Mic x={789} y={112} h={20} color="#D0CDC8" />
        <svg viewBox="0 0 24 24" width={24} height={24} style={{position: 'absolute', left: 827, top: 100}}><path d="M3 10 V14 M7 7 V17 M11 4 V20 M15 8 V16 M19 10 V14" stroke="#D0CDC8" strokeWidth="1.8" strokeLinecap="round" /></svg>
      </div>
      <div style={{...P(237, 600), width: 115, height: 38, borderRadius: 8, background: '#2B2B29', color: TXT, fontSize: 16, textAlign: 'center', lineHeight: '38px'}}>Tes chats</div>
      <div style={{...P(368, 600), fontSize: 16, color: DIM, lineHeight: '38px'}}>Activité</div>
      <div style={{position: 'absolute', right: WX + 1763 - 1106, top: 600 - WY, fontSize: 15, color: DIM, lineHeight: '38px', whiteSpace: 'nowrap'}}><Lock /> Tes chats restent privés jusqu’au partage</div>
      <div style={{...P(236, 660), width: 875, height: 108, borderRadius: 12, border: '1px solid #2E2D2A', boxSizing: 'border-box', textAlign: 'center', lineHeight: '106px', fontSize: 16.5, color: '#A8A5A0'}}>
        Lance un chat pour organiser tes échanges et réutiliser le savoir du projet.
      </div>

      {/* panneau de droite */}
      <div style={{...P(1172, 271), width: 544, height: 700, borderRadius: 14, border: '1px solid #2C2C29', boxSizing: 'border-box'}} />
      <div style={{...P(1198, 299), fontSize: 17, color: '#E0DDD8'}}>Mémoire</div>
      <div style={{...P(1198, 330), fontSize: 14.3, color: '#6F6C68', whiteSpace: 'nowrap'}}>La mémoire du projet s’affichera ici après quelques chats.</div>
      <div style={{...P(1584, 297), width: 105, height: 28, borderRadius: 6, border: '1px solid #353431', boxSizing: 'border-box', fontSize: 14, color: DIM, textAlign: 'center', lineHeight: '26px'}}><Lock /> Toi seul</div>
      <div style={{...P(1172, 370), width: 544, height: 1, background: '#2C2C29'}} />
      <div style={{...P(1198, 397 + (filled ? 0 : 0)), fontSize: 17, color: '#E0DDD8'}}>Instructions</div>
      {filled ? (
        <>
          <Ico x={1681} y={409} d="M4 20 L4.5 16 L15.5 5 a2 2 0 0 1 3 3 L7.5 19 Z M13.5 7 L16.5 10" s={21} c="#D0CDC8" />
          <div style={{...P(1198, 426), width: 470, fontSize: 14.3, color: '#A8A5A0', lineHeight: '21.5px', height: 43, overflow: 'hidden'}}>
            Tu es stratège growth marketing intégré à ce projet. ## Rôle Tu aides à développer le chiffre d’affaires, l’acquisition, la fidélisation et…
          </div>
        </>
      ) : (
        <>
          <Ico x={1681} y={409} d="M12 5 V19 M5 12 H19" s={21} c="#D0CDC8" />
          <div style={{...P(1198, 426), fontSize: 14.3, color: '#77746F', whiteSpace: 'nowrap'}}>Ajoute des instructions pour adapter les réponses de Claude</div>
        </>
      )}
      <div style={{position: 'absolute', left: 0, top: dy, width: 1763, height: 825}}>
        <div style={{...P(1172, 500), width: 544, height: 1, background: '#2C2C29'}} />
        <div style={{...P(1198, 523), fontSize: 17, color: '#E0DDD8'}}>Fichiers</div>
        <Ico x={1681} y={535} d="M12 5 V19 M5 12 H19" s={21} c="#D0CDC8" />
        <div style={{...P(1198, 562), width: 491, height: 7, borderRadius: 4, background: '#2A2A27'}}>
          <div style={{width: 10, height: 7, borderRadius: 4, background: '#6198E0'}} />
        </div>
        <div style={{...P(1198, 581), fontSize: 14.3, color: DIM}}>1 % de la capacité du projet utilisée</div>
        {TILES.map((tl, i) => {
          const x = [1198, 1367, 1535][i % 3];
          const y = i < 3 ? 630 : 793;
          return (
            <div key={i} style={{...P(x, y), width: 154, height: 147, borderRadius: 8, background: '#2C2C2A', border: '1px solid #353431', boxSizing: 'border-box', padding: '11px 12px'}}>
              <div style={{fontSize: 14.5, color: '#DAD7D2', lineHeight: '22.5px', whiteSpace: 'pre'}}>{tl.n}</div>
              {tl.l && <div style={{fontSize: 12, color: '#77746F', marginTop: 4}}>{tl.l}</div>}
              <div style={{position: 'absolute', left: 12, bottom: 12, padding: '0 5px', height: 22, borderRadius: 4, border: '1px solid #4A4844', fontSize: 13.5, color: '#B6B2AE', lineHeight: '21px'}}>{tl.k}</div>
            </div>
          );
        })}
      </div>
    </>
  );
};

const MENU: (string | null)[] = [
  'Emoji et symboles', 'Aide à la rédaction', null, '~Annuler', '~Rétablir', null, '~Couper', '~Copier', 'Coller', 'Coller et adapter le style', '~Tout sélectionner', 'Ouvrir en mode lecture', null,
  'Réglages de langue', 'Sens de l’écriture ›', null, '1Password : mots de passe ›', null, 'Inspecter', null, 'Remplissage auto ›',
];

const PASTED = [
  '## Ta façon de penser',
  '- Les principes premiers avant les frameworks',
  '- Remonter aux causes profondes et aux points de levier',
  '- Remettre en question les hypothèses avant d’optimiser',
  '- La stratégie avant la tactique',
  '',
  '## Ta façon de communiquer',
  '- Direct et concis',
  '- Aucun jargon d’entreprise ni mot à la mode',
  '- Si le contexte manque, pose une seule question ciblée avant d’avancer',
  '- Des puces pour les recommandations, de la prose pour la stratégie',
  '',
  '## Ce que tu évites',
  '- Les indicateurs de vanité',
  '- Les bonnes pratiques génériques hors contexte',
  '- Les recommandations impossibles à mesurer',
];

const Modal: React.FC<{t: number}> = ({t}) => {
  const menuOp = keys(t, [[3.15, 0], [3.2, 1], [4.15, 1], [4.3, 0]]);
  const hl = t >= 3.4 && t < 4.3;
  const pasted = t >= 4.35;
  const pressed = t >= 6.05 && t < 6.25;
  // zone de texte claire à l'ouverture, puis focus au clic (2,37 s)
  const focusTA = t >= 71 / 30;
  // coordonnées du modal dans la fenêtre
  const M = {x: 517, y: 208, w: 886, h: 663};
  const ta = {x: 546, y: 333, w: 829, h: 395};
  return (
    <div style={{...P(M.x, M.y), width: M.w, height: M.h, borderRadius: 14, background: '#373734', boxShadow: '0 20px 60px rgba(0,0,0,0.5)', border: '1px solid #42413E', boxSizing: 'border-box'}}>
      <div style={{position: 'absolute', left: 30, top: 29, fontSize: 28.5, fontWeight: 600, color: '#F2F0EC', letterSpacing: -0.2}}>Définir les instructions du projet</div>
      <div style={{position: 'absolute', left: 30, top: 70, width: 830, fontSize: 17.2, color: '#CFCCC7', lineHeight: '24.5px'}}>
        Donne à Claude des instructions et informations utiles pour les chats du Projet 01. Elles s’ajoutent à tes <span style={{color: '#7FA6E6', textDecoration: 'underline', textUnderlineOffset: 3}}>instructions de profil</span> et au style choisi dans un chat.
      </div>
      <div style={{position: 'absolute', left: ta.x - M.x, top: ta.y - M.y, width: ta.w, height: ta.h, borderRadius: 7, background: focusTA ? '#353533' : '#4D4D4B', border: focusTA ? '2px solid #3E63A8' : '2px solid #5A5A57', boxShadow: focusTA ? '0 0 0 1px #1D304E' : 'none', boxSizing: 'border-box', overflow: 'hidden'}}>
        {!pasted ? (
          <div style={{position: 'absolute', left: 13, top: 8, fontSize: 17.2, color: '#86837E', whiteSpace: 'nowrap'}}>
            <span style={{display: 'inline-block', width: 1.5, height: 20, background: '#DDD', verticalAlign: 'middle', opacity: focusTA && Math.floor(t * 2) % 2 === 0 ? 1 : 0}} />
            Réfléchis étape par étape et détaille ton raisonnement. Donne des exemples précis.
          </div>
        ) : (
          <>
            <div style={{position: 'absolute', left: 14, bottom: 9, fontSize: 17.2, color: '#E8E5E0', lineHeight: '24.5px', whiteSpace: 'pre'}}>
              {PASTED.join('\n')}
              <span style={{display: 'inline-block', width: 1.5, height: 20, background: '#EEE', verticalAlign: 'middle', marginLeft: 1}} />
            </div>
            <div style={{position: 'absolute', right: 3, top: 175, width: 4, height: 212, borderRadius: 2, background: '#6E6D69'}} />
          </>
        )}
      </div>
      <div style={{position: 'absolute', left: 42, top: 758 - M.y - 12, fontSize: 17, fontWeight: 600, color: '#ECE9E5'}}>Ajouter des outils</div>
      <div style={{position: 'absolute', left: 1105 - M.x - 30, top: 802 - M.y, width: 117, height: 38, borderRadius: 7, background: '#4F4F4D', color: '#ECE9E5', fontSize: 17, textAlign: 'center', lineHeight: '38px'}}>Annuler</div>
      <div style={{position: 'absolute', left: 1241 - M.x - 20, top: 802 - M.y, width: 153, height: 38, borderRadius: 7, background: pasted ? (pressed ? '#DADADA' : '#FFFFFF') : '#A2A2A2', color: '#1E1E1C', fontSize: 17, fontWeight: 500, textAlign: 'center', lineHeight: '38px', transform: pressed ? 'scale(0.97)' : undefined}}>Enregistrer</div>
      {/* menu contextuel */}
      {menuOp > 0 && (
        <div style={{position: 'absolute', left: 761 - M.x, top: 391 - M.y, width: 198, padding: '5px 4px', borderRadius: 6, background: '#E9E8E6', boxShadow: '0 8px 24px rgba(0,0,0,0.45)', opacity: menuOp, fontSize: 10.2, color: '#222'}}>
          {MENU.map((m, i) =>
            m === null ? (
              <div key={i} style={{height: 1, background: '#CFCECB', margin: '3px 6px'}} />
            ) : (
              <div key={i} style={{height: 16, lineHeight: '16px', padding: '0 7px', borderRadius: 3, background: m === 'Coller' && hl ? '#1F6FE0' : 'transparent', color: m.startsWith('~') ? '#A9A8A5' : m === 'Coller' && hl ? '#fff' : '#222', display: 'flex', justifyContent: 'space-between'}}>
                <span>{m.replace('~', '').replace(' ›', '')}</span>{m.endsWith('›') && <span>›</span>}
              </div>
            ),
          )}
        </div>
      )}
    </div>
  );
};

const IBeam: React.FC<{x: number; y: number}> = ({x, y}) => (
  <svg viewBox="0 0 14 30" width={14} height={30} style={{position: 'absolute', left: x - 7, top: y - 15}}>
    <path d="M2 2 Q7 2 7 6 V24 Q7 28 2 28 M12 2 Q7 2 7 6 M7 24 Q7 28 12 28 M4 15 H10" fill="none" stroke="#fff" strokeWidth="3.4" strokeLinecap="round" />
    <path d="M2 2 Q7 2 7 6 V24 Q7 28 2 28 M12 2 Q7 2 7 6 M7 24 Q7 28 12 28 M4 15 H10" fill="none" stroke="#111" strokeWidth="1.5" strokeLinecap="round" />
  </svg>
);

// Bruitages : fenêtre, clic sur « + », modale, clic dans la zone, clic droit, « Coller », « Enregistrer », fermeture.
const CUES: SfxCue[] = [
  {frame: 0, name: 'whoosh-transition'},
  {frame: 34, name: 'clic'},
  {frame: 38, name: 'whoosh-transition'},
  {frame: 71, name: 'clic'},
  {frame: 95, name: 'clic'},
  {frame: 129, name: 'clic'},
  {frame: 182, name: 'clic'},
  {frame: 190, name: 'whoosh-transition'},
];

const Comp: React.FC = () => {
  const t = useT();
  const s = samples(t, Z);
  const modalOp = keys(t, [[38 / 30, 0], [44 / 30, 1], [190 / 30, 1], [196 / 30, 0]]);
  const modalSc = keys(t, [[38 / 30, 0.985], [44 / 30, 1]]);
  const filled = t >= 6.35;
  // trajectoire du curseur (coordonnées finales)
  const cx = keys(t, [[0.4, 1768], [1.1, 1684], [1.9, 1684], [2.3, 763], [3.2, 763], [3.4, 797], [4.45, 797], [5.5, 1290], [5.85, 1300], [6.4, 1300], [6.8, 1276]], easeInOut);
  const cy = keys(t, [[0.4, 515], [1.1, 410], [1.9, 410], [2.3, 394], [3.2, 394], [3.4, 505], [4.45, 505], [5.5, 776], [5.85, 822], [6.4, 822], [6.8, 832]], easeInOut);
  const ibeam = t >= 1.7 && t < 3.15;
  return (
    <AbsoluteFill style={{backgroundColor: '#000', fontFamily: FONT}}>
      <SfxTrack cues={CUES} />
      <Bg id="20" />
      <Camera scale={s} ox={962} oy={516}>
        <div style={{position: 'absolute', left: WX, top: WY, width: 1763, height: 825, borderRadius: 22, background: '#1E1E1C', overflow: 'hidden', boxShadow: '0 40px 90px rgba(0,0,0,0.55)'}}>
          <div style={{position: 'absolute', inset: 0, filter: modalOp > 0 ? `blur(${3 * modalOp}px)` : undefined}}>
            <Page filled={filled} />
          </div>
          <div style={{position: 'absolute', inset: 0, background: `rgba(0,0,0,${0.55 * modalOp})`}} />
          {modalOp > 0 && (
            <div style={{position: 'absolute', inset: 0, opacity: modalOp, transform: `scale(${modalSc})`, transformOrigin: '892px 416px'}}>
              <Modal t={t} />
            </div>
          )}
          <div style={{position: 'absolute', inset: 0, borderRadius: 22, border: '1.6px solid rgba(214,214,214,0.8)'}} />
        </div>
        {ibeam ? <IBeam x={cx} y={cy} /> : (t >= 5.75 && t < 6.35) || t >= 6.7 ? <Hand x={cx} y={cy} /> : <Cursor x={cx - 3} y={cy - 3} size={42} />}
      </Camera>
    </AbsoluteFill>
  );
};
export default Comp;

// Signaux sonores exportés pour la bibliothèque (cloud/cues_globaux.py).
export const cues = CUES;
