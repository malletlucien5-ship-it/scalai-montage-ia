import {SfxTrack, SfxCue} from '../../shared/Sfx';
import React from 'react';
import {AbsoluteFill, Img, staticFile, useCurrentFrame} from '../../shared/rt';
import {
  SANS, SERIF, K, ease, TealBg, SpeakerCard, roundRectPath, Cursor, typed, ClaudeStar,
  IPlus, IX, IChats, IProjects, IStack, IShapes, IBriefcase, IPalette, IBuilding, ILock, IMic, IWave, IPen, IChart, IBulb, IChevron,
} from './ui';

// Référence : 102,567 s à 112,03 s (284 images).
export const meta = {id: '15-pip-ecran', durationInFrames: 284, fps: 30, defaultProps: {showPlate: true},
  occurrences: [{ref: [102.567, 112.033], from: 0, durationInFrames: 284, mode: 'overlay'}],
};

// Bruitages calés sur le minutage de l'animation (règles : SFX-REGLES.md).
const SFX: SfxCue[] = [
  {frame: 0, name: 'whoosh-transition'},
  {frame: 104, name: 'clic'},
  {frame: 109, name: 'whoosh-transition'},
  {frame: 124, name: 'clic'},
  {frame: 128, name: 'frappe-clavier', durationInFrames: 30},
  {frame: 181, name: 'clic'},
  {frame: 186, name: 'frappe-clavier', durationInFrames: 76},
];

const NAME = 'Projet 01';
const GOAL = 'Tu es un assistant marketing. Aide-moi sur le copywriting, les idées de campagne et la stratégie de contenu.';

// ---------- Phase 1 : accueil Claude ----------
const Home: React.FC<{f: number; sp: boolean}> = ({f, sp}) => {
  const tip = ease(f, 26, 30);
  const side = [
    {I: IPlus, y: 205, circle: true},
    {I: IChats, y: 250},
    {I: IProjects, y: 293, hl: true},
    {I: IStack, y: 338},
    {I: IShapes, y: 382},
    {I: IBriefcase, y: 426},
    {I: IPalette, y: 527},
  ];
  const chip = (x: number, w: number, I: React.FC<any>, label: string) => (
    <div style={{position: 'absolute', left: x, top: 499, width: w, height: 41, borderRadius: 9, background: '#2e2e2b', border: '1px solid #3a3a37',
      display: 'flex', alignItems: 'center', gap: 8, paddingLeft: 11, boxSizing: 'border-box', color: '#c9c7c2', fontSize: 20, fontWeight: 500, whiteSpace: 'nowrap'}}>
      <I size={22} color="#a9a7a2" sw={1.5} />{label}
    </div>
  );
  return (
    <AbsoluteFill style={{fontFamily: SANS}}>
      <Img src={staticFile('15/speaker.jpg')} style={{position: 'absolute', left: 40, top: 208, width: 431, height: 471, borderRadius: 14, objectFit: 'cover', objectPosition: '50% 50%'}} />
      <SpeakerCard x={40} y={208} w={431} h={471} radius={14} fill={false} />
      <div style={{position: 'absolute', left: 500, top: 155, width: 1389, height: 592, background: K.win, borderRadius: 6,
        boxShadow: '0 0 0 1.5px #4a4a47, 0 30px 80px rgba(0,0,0,0.6)', overflow: 'hidden'}}>
        <div style={{position: 'absolute', left: 53, top: 0, bottom: 0, width: 1.5, background: '#2b2b29'}} />
        {side.map(({I, y, circle, hl}, i) => (
          <div key={i} style={{position: 'absolute', left: 23 - 16, top: y - 155 - 16, width: 32, height: 32, borderRadius: 16,
            background: circle ? '#2f2f2c' : hl ? '#2a2a28' : 'transparent', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
            <I size={circle ? 18 : 23} color="#cfcdc8" sw={1.6} />
          </div>
        ))}
        {/* pastille organisation */}
        <div style={{position: 'absolute', left: 787, top: 112, height: 42, padding: '0 14px 0 11px', borderRadius: 8, background: '#141413',
          display: 'flex', alignItems: 'center', gap: 9, color: '#bdbbb6', fontSize: 20, fontWeight: 500}}>
          <IBuilding size={21} color="#a9a7a2" sw={1.5} />Mallet Media
        </div>
        <ClaudeStar size={46} style={{position: 'absolute', left: 694, top: 208}} />
        <span style={{position: 'absolute', left: 755, top: 193, fontFamily: SERIF, fontSize: 53, lineHeight: '76px', color: '#e8e6e1', letterSpacing: -0.8, fontWeight: 300, whiteSpace: 'nowrap'}}>Lucien revient !</span>
        {/* zone de saisie */}
        <div style={{position: 'absolute', left: 426, top: 314, width: 898, height: 162, borderRadius: 24, background: '#2a2a27', border: '1.5px solid #3b3b38', boxSizing: 'border-box'}}>
          <div style={{position: 'absolute', left: 26, top: 24, fontSize: 22, color: '#8b8984'}}>
            <span style={{borderLeft: '1.5px solid #ddd', marginRight: 1}} />Tape / pour les skills
          </div>
          <IPlus size={26} color="#cfcdc8" sw={1.6} style={{position: 'absolute', left: 30, top: 107}} />
          <div style={{position: 'absolute', right: 140, top: 107, fontSize: 20, color: '#bdbbb6', display: 'flex', alignItems: 'center', gap: 8}}>
            Sonnet 4.6 <span style={{color: '#8b8984'}}>Bas</span><IChevron size={14} color="#8b8984" />
          </div>
          <IMic size={24} color="#cfcdc8" style={{position: 'absolute', right: 83, top: 107}} />
          <IWave size={26} color="#cfcdc8" style={{position: 'absolute', right: 28, top: 106}} />
        </div>
        {chip(557, 110, IPen, 'Écrire')}
        {chip(678, 143, IChart, 'Stratégie')}
        {chip(833, 148, IBriefcase, 'Carrière')}
        {chip(993, 222, IBulb, 'Au choix de Claude')}
      </div>
      {/* info-bulle Projets */}
      <div style={{position: 'absolute', left: 541, top: 279, height: 32, padding: '0 11px', borderRadius: 7, background: '#fff', color: '#111',
        fontSize: 19, fontWeight: 500, display: 'flex', alignItems: 'center', opacity: tip, transform: `scale(${0.96 + 0.04 * tip})`, transformOrigin: 'left center'}}>
        Projets
      </div>
      <Cursor x={568 - 30 * ease(f, 14, 24)} y={322 - 16 * ease(f, 14, 24)} kind={f < 20 ? 'arrow' : 'hand'} scale={0.9} />
    </AbsoluteFill>
  );
};

// ---------- Phase 2 : formulaire « Créer un projet » ----------
const focusRing = (on: number): React.CSSProperties => ({
  boxShadow: on ? `0 0 0 2px rgba(58,120,235,${on}), 0 0 8px rgba(58,120,235,${0.5 * on})` : 'none',
  background: on ? '#2b2b29' : K.field,
});

const Form: React.FC<{f: number; sp: boolean}> = ({f, sp}) => {
  const name = typed(NAME, f, 128, 9);
  const nameFocus = f < 181 ? 1 : 0;
  const goalFocus = f >= 181 ? 1 : 0;
  const goalCps = GOAL.length / ((262 - 186) / 30);
  const goal = typed(GOAL, f, 186, goalCps);
  const blink = Math.floor(f / 16) % 2 === 0;
  // curseur
  const mv = ease(f, 163, 177);
  const cx = 1195 + (950 - 1195) * mv;
  const cy = 283 + (440 - 283) * mv;
  const kind = f >= 171 ? 'ibeam' : 'hand';
  const cursorOn = f < 186;
  const label: React.CSSProperties = {position: 'absolute', left: 50, fontSize: 29, fontWeight: 500, color: K.label};
  const desc: React.CSSProperties = {position: 'absolute', left: 99, fontSize: 27, color: K.muted};
  const caret = (on: boolean) => (on && blink ? <span style={{display: 'inline-block', width: 2, height: 30, background: '#eee', verticalAlign: -5, marginLeft: 1}} /> : null);
  return (
    <AbsoluteFill style={{fontFamily: SANS}}>
      <Img src={staticFile('15/speaker.jpg')} style={{position: 'absolute', left: 116, top: 233, width: 575, height: 627, borderRadius: 18, objectFit: 'cover', objectPosition: '50% 50%'}} />
      <SpeakerCard x={116} y={233} w={575} h={627} radius={18} fill={false} />
      <div style={{position: 'absolute', left: 766, top: 45, width: 1046, height: 996, borderRadius: 22, background: K.modal,
        boxShadow: '0 0 0 2px rgba(190,190,188,0.55), 0 30px 90px rgba(0,0,0,0.7)', overflow: 'hidden'}}>
        <div style={{position: 'absolute', left: 50, top: 38, fontSize: 47, fontWeight: 600, color: '#f3f3f1', letterSpacing: -0.3}}>Créer un projet</div>
        <IX size={32} color="#f0f0ee" sw={2} style={{position: 'absolute', left: 984, top: 51}} />
        <div style={{...label, top: 144}}>Sur quoi travailles-tu ?</div>
        <div style={{position: 'absolute', left: 50, top: 195, width: 967, height: 65, borderRadius: 12, ...focusRing(nameFocus)}}>
          <div style={{position: 'absolute', left: 25, top: 14, fontSize: 28, color: name ? K.fieldText : K.placeholder}}>
            {name ? <>{name}{caret(nameFocus === 1)}</> : <>{caret(nameFocus === 1)}Nomme ton projet</>}
          </div>
        </div>
        <div style={{...label, top: 312}}>Qu'essaies-tu d'accomplir ?</div>
        <div style={{position: 'absolute', left: 50, top: 363, width: 967, height: 155, borderRadius: 12, ...focusRing(goalFocus)}}>
          <div style={{position: 'absolute', left: 25, top: 17, right: 40, fontSize: 28, lineHeight: '41px', color: goal ? K.fieldText : K.placeholder}}>
            {goal ? <>{goal}{caret(goalFocus === 1)}</> : <>{caret(goalFocus === 1)}Décris ton projet, tes objectifs, ton sujet, etc...</>}
          </div>
          <svg width="12" height="12" style={{position: 'absolute', right: 5, bottom: 5}}><path d="M11 3L3 11M11 7.5L7.5 11" stroke="#8a8a87" strokeWidth="1.2" /></svg>
        </div>
        <div style={{...label, top: 576}}>Visibilité</div>
        <div style={{position: 'absolute', left: 50, top: 646, width: 32, height: 32, borderRadius: 16, border: '2px solid #6d6d6a', boxSizing: 'border-box'}} />
        <IBuilding size={26} color="#e8e8e6" sw={1.7} style={{position: 'absolute', left: 101, top: 649}} />
        <div style={{position: 'absolute', left: 140, top: 642, fontSize: 29, color: K.label}}>Mallet Media</div>
        <div style={{...desc, top: 689}}>Tout le monde dans ton organisation peut voir et utiliser ce projet</div>
        <div style={{position: 'absolute', left: 50, top: 747, width: 32, height: 32, borderRadius: 16, background: '#2f6ee6', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
          <div style={{width: 12, height: 12, borderRadius: 6, background: '#fff'}} />
        </div>
        <ILock size={26} color="#e8e8e6" sw={1.7} style={{position: 'absolute', left: 101, top: 749}} />
        <div style={{position: 'absolute', left: 140, top: 743, fontSize: 29, color: K.label}}>Privé</div>
        <div style={{...desc, top: 790}}>Seuls les membres invités peuvent voir et utiliser ce projet</div>
        <div style={{position: 'absolute', left: 598, top: 886, width: 145, height: 64, borderRadius: 12, background: '#535350', color: '#f0f0ee',
          fontSize: 29, fontWeight: 500, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>Annuler</div>
        <div style={{position: 'absolute', left: 769, top: 886, width: 247, height: 64, borderRadius: 12, background: '#fff', color: '#111',
          fontSize: 29, fontWeight: 500, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>Créer le projet</div>
      </div>
      {cursorOn && <Cursor x={cx} y={cy} kind={kind as any} scale={1} />}
    </AbsoluteFill>
  );
};

// Trou dans le fond à l'emplacement de la carte speaker (rendu alpha).
const hole = (f: number, outP: number, inP: number) => {
  const [x, y, w, h, r, sc] = f < 109 ? [40, 208, 431, 471, 14, 1 + 0.04 * outP] : [116, 233, 575, 627, 18, 1.03 - 0.03 * inP];
  return roundRectPath(960 + (x - 960) * sc, 540 + (y - 540) * sc, w * sc, h * sc, r * sc);
};

const PipEcran: React.FC<{showPlate?: boolean}> = ({showPlate = true}) => {
  const f = useCurrentFrame();
  // fondu flou entre les deux écrans (106,07 s à 106,37 s)
  const outP = ease(f, 105, 111);
  const inP = ease(f, 107, 115);
  return (
    <AbsoluteFill style={{background: showPlate ? '#000' : 'transparent'}}>
      <TealBg hole={showPlate ? undefined : hole(f, outP, inP)} />
      {f < 112 && (
        <AbsoluteFill style={{opacity: 1 - outP, filter: `blur(${outP * 22}px)`, transform: `scale(${1 + 0.04 * outP})`}}>
          <Home f={f} sp={showPlate} />
        </AbsoluteFill>
      )}
      {f >= 107 && (
        <AbsoluteFill style={{opacity: inP, filter: inP < 1 ? `blur(${(1 - inP) * 22}px)` : undefined, transform: `scale(${1.03 - 0.03 * inP})`}}>
          <Form f={f} sp={showPlate} />
        </AbsoluteFill>
      )}
      <SfxTrack cues={SFX} />
    </AbsoluteFill>
  );
};
export default PipEcran;

// Signaux sonores exportés pour la bibliothèque (cloud/cues_globaux.py).
export const cues = SFX;
