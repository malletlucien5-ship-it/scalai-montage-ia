import React from 'react';
import {AbsoluteFill, Sequence, interpolate} from '../../shared/rt';
import {
  Bg, Camera, MacWindow, ClaudeMark, Cursor, Caret, Mic, ArrowUp, Chevron, Plus,
  useT, samples, fade, keys, typedN, FONT, CL, easeInOut,
} from './kit';
import {SfxTrack, SfxCue} from '../../shared/Sfx';

const ID = '11';
const A = 115; // 29,83 à 33,67 s
const B = 132; // 57,52 à 61,93 s
const C = 160; // 127,33 à 132,67 s
const GAP = 15;

export const meta = {
  id: '11-fenetre-claude-chat', durationInFrames: A + GAP + B + GAP + C, fps: 30,
  occurrences: [
    {ref: [29.83, 33.67], from: 0, durationInFrames: A, mode: 'plein'},
    {ref: [57.52, 61.93], from: A + GAP, durationInFrames: B, mode: 'plein'},
    {ref: [127.33, 132.67], from: A + GAP + B + GAP, durationInFrames: C, mode: 'plein'},
  ],
};

// ---------- Occurrence A : « Comment économiser plus d'argent ? » ----------
const ZA = [0.8682,0.8682,0.8682,0.8688,0.8699,0.8716,0.8751,0.8785,0.8842,0.8917,0.9009,0.9106,0.9203,0.9301,0.9381,0.9456,0.9519,0.9576,0.9622,0.9668,0.9708,0.9742,0.9777,0.9799,0.9828,0.9857,0.9868,0.9891,0.9914,0.9926,0.9937,0.9948,0.9960,0.9971,0.9983,0.9989,0.9994,1.0];
const QA = 'Comment épargner davantage ?';
// Coupure de ligne à la même place que l'original (après « is going »).
const RA1 = 'Note chaque dépense pendant une semaine. Tu verras vite où part ton argent :';
const RA2 = 'supprimer une ou deux habitudes fait souvent gagner des centaines par mois.';
const RA = RA1 + RA2;
// Curseur relevé image par image (coordonnées finales) : [image, x, y].
const CURA: [number, number, number][] = [[26,1730,889],[27,1718,859],[42,1707,830],[44,1708,831],[46,1708,830],[50,1708,831],[60,1709,832],[64,1708,832],[66,1709,832],[76,1708,832],[78,1710,832],[82,1594,787],[84,1415,715],[86,1112,594],[87,1017,557],[88,768,457],[89,638,405],[90,484,346],[91,385,304],[92,254,252],[93,197,230],[94,145,209],[95,123,199],[96,117,200],[97,116,199],[115,119,200]];

// Points de réflexion relevés : un seul passage, chaque point s'allume 3 images après le précédent.
const Dots: React.FC<{f: number}> = ({f}) => (
  <>
    {[0, 1, 2].map((i) => {
      const pk = 45 + i * 3;
      const k = interpolate(f, [pk - 3, pk, pk + 3, pk + 6], [0, 1, 1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
      const lum = Math.round(61 + 67 * k);
      const d = 12.6 + 3.4 * k;
      return <div key={i} style={{position: 'absolute', left: 307 - 261 + i * 19 - d / 2, top: 613 - 576 - d / 2 + 0.5, width: d, height: d, borderRadius: d, background: `rgb(${lum},${lum - 2},${lum - 4})`}} />;
    })}
  </>
);

const SceneA: React.FC = () => {
  const t = useT();
  const s = samples(t, ZA);
  const sent = t >= 1.05;
  const nq = typedN(QA.length - 6, t, 0, 0.62) + 6;
  const bubbleOp = fade(t, 1.05, 0.15);
  const respOp = fade(t, 1.3, 0.1);
  const streaming = t >= 2.0;
  const nr = typedN(RA.length, t, 2.0, 2.45);
  // hauteur de la réponse : points (87) puis deux lignes (150)
  const boxH = keys(t, [[2.2, 87], [2.3, 150]], easeInOut);
  const boxBottom = 663;
  const boxTop = boxBottom - boxH;
  const hasResp = t >= 1.3;
  const bubbleBottom = hasResp ? boxTop - 67 : keys(t, [[1.05, 663], [1.3, 663]]);
  const bubbleTop = bubbleBottom - 93;
  // curseur : sur le bouton d'envoi, puis vers la pastille rouge
  const f = t * 30;
  const cx = interpolate(f, CURA.map((c) => c[0]), CURA.map((c) => c[1]), {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const cy = interpolate(f, CURA.map((c) => c[0]), CURA.map((c) => c[2]), {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return (
    <AbsoluteFill>
      <Bg id={ID} />
      <Camera scale={s} ox={960} oy={516}>
        <MacWindow x={74} y={164} w={1744} h={766} r={26} titleH={55} titleBg="#13100F" bodyBg="#1A1716" dotX={37} dotGap={30} dotR={9}>
          {/* bulle utilisateur */}
          {sent && (
            <div style={{position: 'absolute', right: 74 + 1744 - 1664, top: bubbleTop - 164, opacity: bubbleOp}}>
              <div style={{height: 93, padding: '0 34px', borderRadius: 24, background: '#2D2825', color: CL.text, fontSize: 27.5, lineHeight: '93px', whiteSpace: 'nowrap'}}>{QA}</div>
            </div>
          )}
          {sent && (
            <div style={{position: 'absolute', left: 1711 - 74 - 29, top: bubbleBottom - 28 - 29 - 164, width: 58, height: 58, borderRadius: 29, background: '#372E29', opacity: bubbleOp, color: '#CFC6C0', fontSize: 16, fontWeight: 700, lineHeight: '58px', textAlign: 'center'}}>JS</div>
          )}
          {/* réponse de Claude */}
          {hasResp && (
            <div style={{opacity: respOp}}>
              <div style={{position: 'absolute', left: 261 - 74, top: boxTop - 17 - 10 - 164, fontSize: 15, fontWeight: 600, color: CL.label, letterSpacing: 0.3}}>Claude</div>
              <ClaudeMark x={208 - 74} y={boxTop + 32 - 164} size={48} />
              <div style={{position: 'absolute', left: 261 - 74, top: boxTop - 164, width: 1270, height: boxH, borderRadius: 24, border: '1px solid #2A2724', boxSizing: 'border-box'}}>
                {!streaming ? (
                  <Dots f={t * 30} />
                ) : (
                  <div style={{position: 'absolute', left: 34, top: 21, width: 1200, fontSize: 27.5, lineHeight: '49px', color: CL.text}}>
                    {RA1.slice(0, nr)}
                    {nr > RA1.length && <br />}
                    {nr > RA1.length && RA2.slice(0, nr - RA1.length)}
                    {nr < RA.length && <Caret h={30} />}
                  </div>
                )}
              </div>
            </div>
          )}
          {/* champ de saisie */}
          <div style={{position: 'absolute', left: 142 - 74, top: 690 - 164, width: 1635, height: 195, borderRadius: 34, background: '#29231E', border: '1.5px solid #3E3936', boxSizing: 'border-box'}}>
            {!sent && (
              <div style={{position: 'absolute', left: 36, top: 744 - 690 - 20, fontSize: 27.5, lineHeight: '40px', color: CL.text, whiteSpace: 'nowrap'}}>
                {QA.slice(0, nq)}
                <Caret h={30} on={Math.floor(t * 2.2) % 2 === 0 || nq < QA.length} />
              </div>
            )}
            <div style={{position: 'absolute', left: 210 - 142 - 31, top: 824 - 690 - 31, width: 62, height: 62, borderRadius: 31, border: '1.5px solid #4D4843', boxSizing: 'border-box', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
              <Plus size={28} />
            </div>
            <ClaudeMark x={1422 - 142} y={824 - 690} size={27} color="#B0634F" glow={false} />
            <div style={{position: 'absolute', left: 1444 - 142, top: 824 - 690 - 15, fontSize: 22, lineHeight: '30px', color: '#8A847F', display: 'flex', alignItems: 'center', gap: 6}}>
              Sonnet 4.6 <Chevron size={24} />
            </div>
            <Mic x={1620 - 142} y={824 - 690} h={40} color="#77716C" />
            <div style={{position: 'absolute', left: 1704 - 142 - 37, top: 824 - 690 - 37, width: 74, height: 74, borderRadius: 37, background: CL.send, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
              <ArrowUp size={36} stroke={3.2} />
            </div>
          </div>
        </MacWindow>
        {t * 30 >= 26 && <Cursor x={cx - 1} y={cy - 1} size={30} />}
      </Camera>
    </AbsoluteFill>
  );
};

// ---------- Occurrence B : e-mail commercial, questions numérotées ----------
const ZB = [0.7874,0.7874,0.7885,0.7896,0.7908,0.7952,0.7997,0.8075,0.8186,0.8319,0.8486,0.8653,0.8809,0.8954,0.9087,0.9199,0.9288,0.9377,0.9444,0.9510,0.9566,0.9622,0.9666,0.9711,0.9744,0.9777,0.9811,0.9833,0.9855,0.9878,0.9900,0.9922,0.9933,0.9944,0.9955,0.9967,0.9978,0.9978,0.9989,0.9989,1.0,1.0];
const HB = 'Avec plaisir. Quelques questions rapides d’abord :';
const IB = [
  'Qui est le destinataire : quel est son rôle, et connaît-il bien ton offre ?',
  'Quelle objection ou hésitation principale a-t-il exprimée jusqu’ici ?',
  'Y a-t-il une vraie échéance ou urgence, une raison d’agir maintenant ?',
  'Quel résultat veux-tu obtenir : une réponse, un appel, un contrat signé ?',
];
const ITEM_T = [1.7, 2.3, 2.8, 3.4];

const SceneB: React.FC = () => {
  const t = useT();
  const s = samples(t, ZB);
  const nh = typedN(HB.length - 7, t, 0, 1.45) + 7;
  const vis = ITEM_T.map((ti) => keys(t, [[ti, 0], [ti + 0.2, 1]], easeInOut));
  const n = vis.reduce((a, b) => a + b, 0);
  const boxH = n <= 1 ? 144 + n * 41 : 185 + (n - 1) * 59;
  const boxBottom = 907;
  const boxTop = boxBottom - boxH;
  const bubbleBottom = boxTop - 65;
  const bubbleTop = bubbleBottom - 182;
  const blur = keys(t, [[4.18, 0], [4.41, 26]]);
  const bright = keys(t, [[4.18, 1], [4.41, 1.45]]);
  const W = {x: 62, y: 111};
  return (
    <AbsoluteFill>
      <Bg id={ID} />
      <Camera scale={s} ox={959.5} oy={497} blur={blur} bright={bright}>
        <MacWindow x={62} y={111} w={1797} h={856} r={28} titleH={53} titleBg="#1C1A18" bodyBg="#13100F" sep="#282524" dotX={30} dotGap={28} dotR={9.5}>
          <div style={{position: 'absolute', left: 848 - W.x, top: bubbleTop - W.y, width: 877, height: 182, borderRadius: 26, background: '#2D2825', boxSizing: 'border-box', padding: '25px 36px', color: CL.text, fontSize: 25.5, lineHeight: '44px', whiteSpace: 'nowrap'}}>
            Aide-moi à rédiger un e-mail pour signer un gros contrat.<br />
            Avant de répondre, pose-moi toutes les questions utiles pour bien faire<br />
            ce travail.
          </div>
          <div style={{position: 'absolute', left: 1773 - 31 - W.x, top: bubbleBottom + 2 - 62 - W.y, width: 62, height: 62, borderRadius: 31, background: '#3A2F2A', color: '#CFC6C0', fontSize: 17, fontWeight: 700, lineHeight: '62px', textAlign: 'center'}}>LM</div>
          <div style={{position: 'absolute', left: 202 - W.x, top: boxTop - 18 - 10 - W.y, fontSize: 15, fontWeight: 600, color: CL.label, letterSpacing: 0.3}}>Claude</div>
          <ClaudeMark x={146 - W.x} y={boxTop + 32 - W.y} size={52} />
          <div style={{position: 'absolute', left: 202 - W.x, top: boxTop - W.y, width: 1313, height: boxH, borderRadius: 26, border: '1px solid #282523', background: '#1A1716', boxSizing: 'border-box', overflow: 'hidden'}}>
            <div style={{position: 'absolute', left: 36, top: 36, fontSize: 25.5, lineHeight: '34px', color: CL.text, whiteSpace: 'nowrap'}}>
              {HB.slice(0, nh)}
              {nh < HB.length && <Caret h={28} />}
            </div>
            {IB.map((txt, i) => (
              <div key={i} style={{position: 'absolute', left: 36, top: 119 + i * 59 - 20, height: 40, display: 'flex', alignItems: 'center', opacity: vis[i], whiteSpace: 'nowrap'}}>
                <div style={{width: 34, height: 34, borderRadius: 17, border: '1.5px solid #4C312A', background: '#2A1D18', boxSizing: 'border-box', color: '#C8704F', fontSize: 13, fontWeight: 700, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>{i + 1}</div>
                <div style={{marginLeft: 19, fontSize: 25.5, color: CL.text}}>{txt}</div>
              </div>
            ))}
          </div>
        </MacWindow>
      </Camera>
    </AbsoluteFill>
  );
};

// ---------- Occurrence C : interview pour le master prompt ----------
const ZC = [0.9177,0.9177,0.9189,0.9189,0.9189,0.9202,0.9215,0.9227,0.9240,0.9253,0.9265,0.9278,0.9291,0.9303,0.9329,0.9341,0.9367,0.9379,0.9405,0.9430,0.9443,0.9468,0.9493,0.9519,0.9538,0.9557,0.9582,0.9607,0.9633,0.9658,0.9671,0.9696,0.9721,0.9747,0.9759,0.9785,0.9810,0.9823,0.9848,0.9861,0.9886,0.9899,0.9911,0.9924,0.9937,0.9949,0.9962,0.9975,0.9987,0.9987,1.0,1.0,1.0];

const UserIcon: React.FC<{x: number; y: number}> = ({x, y}) => (
  // relevé sur l'original : tête pleine et épaules en arche
  <div style={{position: 'absolute', left: x - 27.5, top: y - 27.5, width: 55, height: 55, borderRadius: 28, background: '#2A2826', border: '1px solid #3A3735', boxSizing: 'border-box'}}>
    <svg viewBox="0 0 55 55" width={55} height={55} style={{position: 'absolute', left: -1, top: -1}}>
      <circle cx="27.5" cy="22.2" r="4.6" fill="#A9A6A3" />
      <path d="M17 37.2 C17 30 21.5 26.7 27.5 26.7 C33.5 26.7 38 30 38 37.2" fill="none" stroke="#C9C6C2" strokeWidth="3" strokeLinecap="round" />
    </svg>
  </div>
);

const pop = (t: number, t0: number) => ({opacity: fade(t, t0, 0.15), transform: `translateY(${interpolate(fade(t, t0, 0.2), [0, 1], [8, 0])}px)`});

const SceneC: React.FC = () => {
  const t = useT();
  const s = samples(t, ZC);
  const W = {x: 171, y: 106};
  const box = (bg: string, border: string): React.CSSProperties => ({position: 'absolute', borderRadius: 18, background: bg, border: `1px solid ${border}`, boxSizing: 'border-box', color: CL.text, fontSize: 21, whiteSpace: 'nowrap'});
  return (
    <AbsoluteFill>
      <Bg id={ID} />
      <Camera scale={s} ox={959.5} oy={488}>
        <MacWindow x={171} y={106} w={1578} h={875} r={30} titleH={65} titleBg="#191615" bodyBg="#13100F" sep="#262322" dotX={35} dotGap={29} dotR={9} titleSpacing={1.2}>
          <div style={pop(t, 0.05)}>
            <div style={{...box('#292423', '#383634'), right: 1749 - 1642, top: 208 - W.y, height: 73, padding: '0 27px', lineHeight: '71px'}}>Interroge-moi pour créer un prompt maître de marketeur.</div>
            <UserIcon x={1685 - W.x} y={253 - W.y} />
          </div>
          <div style={pop(t, 1.0)}>
            <div style={{...box('#1C1A18', '#252220'), left: 278 - W.x, top: 302 - W.y, height: 207, padding: '0 27px', lineHeight: '67.5px', paddingTop: 2}}>
              Q1 : Qui est ta cible et quelle est ton offre principale ?<br />
              Q2 : Quel ton colle à ta marque : direct, inspirant ou factuel ?<br />
              Q3 : Quel est le résultat n°1 de tes clients en 90 jours ?
            </div>
            <ClaudeMark x={234 - W.x} y={483 - W.y} size={58} glow />
          </div>
          <div style={pop(t, 2.2)}>
            <div style={{...box('#292423', '#383634'), right: 1749 - 1642, top: 532 - W.y, height: 208, padding: '0 27px', lineHeight: '67.5px', paddingTop: 2}}>
              1. Patrons de petites entreprises. Les faire grandir par l’e-mailing.<br />
              2. Amical mais professionnel. Conversationnel.<br />
              3. Ils gagnent leurs 1 000 premiers abonnés en 60 jours.
            </div>
            <UserIcon x={1685 - W.x} y={713 - W.y} />
          </div>
          <div style={pop(t, 3.05)}>
            <div style={{...box('#1C1A18', '#282523'), left: 278 - W.x, top: 762 - W.y, width: 355, height: 98}}>
              <div style={{position: 'absolute', left: 26, top: 17, width: 54, height: 63, borderRadius: 8, background: '#292725', border: '1px solid #34312F', boxSizing: 'border-box', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
                <svg viewBox="0 0 24 24" width={24} height={24}>
                  <path d="M6 3 H14 L19 8 V21 H6 Z M14 3 V8 H19 M9 13 H16 M9 17 H16" fill="none" stroke="#6468C8" strokeWidth="1.7" strokeLinejoin="round" />
                </svg>
              </div>
              <div style={{position: 'absolute', left: 97, top: 26, fontSize: 19, fontWeight: 600, color: '#E8E4E0', lineHeight: '24px'}}>prompt_maitre.txt</div>
              <div style={{position: 'absolute', left: 97, top: 51, fontSize: 16, color: '#6F6A66', lineHeight: '22px'}}>2,1 Ko · Document texte</div>
              <div style={{position: 'absolute', left: 310 - 18, top: 49 - 18, width: 36, height: 36, borderRadius: 18, background: '#262B48', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
                <svg viewBox="0 0 24 24" width={16} height={16}><path d="M12 5 V15 M7.5 11 L12 15.5 L16.5 11 M7 19 H17" fill="none" stroke="#6A6FE0" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" /></svg>
              </div>
            </div>
            <ClaudeMark x={234 - W.x} y={834 - W.y} size={58} glow />
          </div>
          {/* pied : champ de message */}
          <div style={{position: 'absolute', left: 0, top: 885 - W.y, width: 1578, height: 1, background: '#1F1C1B'}} />
          <div style={{position: 'absolute', left: 202 - W.x, top: 908 - W.y, width: 1455, height: 52, borderRadius: 10, background: '#1B1917', border: '1px solid #262322', boxSizing: 'border-box', color: '#6A6560', fontSize: 19, lineHeight: '50px', paddingLeft: 21}}>Écrire à Claude...</div>
          <div style={{position: 'absolute', left: 1674 - W.x, top: 911 - W.y, width: 44, height: 46, borderRadius: 8, background: '#64311D', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
            <svg viewBox="0 0 24 24" width={20} height={20}><path d="M5 12 H19 M13 6 L19 12 L13 18" fill="none" stroke="#E0A080" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" /></svg>
          </div>
        </MacWindow>
      </Camera>
    </AbsoluteFill>
  );
};

// Bruitages (images de la composition). A : 0, B : 130, C : 277.
const CUES: SfxCue[] = [
  {frame: 0, name: 'whoosh-transition'},
  {frame: 0, name: 'frappe-clavier', durationInFrames: 19},
  {frame: 31, name: 'clic'},
  {frame: 60, name: 'notification'},
  {frame: 130, name: 'whoosh-transition'},
  {frame: 134, name: 'notification'},
  {frame: 181, name: 'pop'},
  {frame: 199, name: 'pop'},
  {frame: 214, name: 'pop'},
  {frame: 232, name: 'pop'},
  {frame: 255, name: 'whoosh-transition'},
  {frame: 277, name: 'whoosh-transition'},
  {frame: 307, name: 'notification'},
  {frame: 343, name: 'pop'},
  {frame: 369, name: 'pop'},
];

const Comp: React.FC = () => (
  <AbsoluteFill style={{backgroundColor: '#000', fontFamily: FONT}}>
      <SfxTrack cues={CUES} />
    <Bg id={ID} />
    <Sequence durationInFrames={A}><SceneA /></Sequence>
    <Sequence from={A + GAP} durationInFrames={B}><SceneB /></Sequence>
    <Sequence from={A + GAP + B + GAP} durationInFrames={C}><SceneC /></Sequence>
  </AbsoluteFill>
);
export default Comp;

// Signaux sonores exportés pour la bibliothèque (cloud/cues_globaux.py).
export const cues = CUES;
