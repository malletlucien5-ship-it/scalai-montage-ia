import React from 'react';
import {AbsoluteFill, Easing, Img, interpolate, Sequence, staticFile, useCurrentFrame} from '../../shared/rt';
import {SfxTrack, SfxCue} from '../../shared/Sfx';
import {loadFont as anton} from '@remotion/google-fonts/Anton';
import {INTER} from '../../shared/fonts';
import {ARIAL_L} from '../../shared/localFonts';

// 21 : couverture « PLAYBOOK IA » qui monte du bas, puis 4 pages qui s'étalent derrière vers la gauche.
// Occurrence 1 : 240,84-244,54 s (111 i), entrée. Occurrence 2 : 883,58-885,78 s (66 i), sortie inverse.
const ANTON = anton('normal', {weights: ['400']}).fontFamily;

const COVER = {x: 902, y: 125, w: 673, h: 835};
const PAGE = {y: 127, h: 826, w: 600};
const PAGE_LEFT = [318, 451, 609, 755]; // bords gauches finaux, du fond vers l'avant

// Montée de la couverture : décalage vertical relevé image par image (px).
const RISE_F = [0, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24];
const RISE_Y = [1100, 950, 864, 716, 572, 464, 380, 316, 260, 216, 180, 148, 124, 100, 80, 64, 52, 40, 28, 20, 12, 8, 4, 0];
// Étalement d'une page (progression 0..1), relevé sur la première page.
const SPREAD_T = [0, 2, 4, 6, 8, 10, 12, 14, 16, 18];
const SPREAD_P = [0, 0.21, 0.52, 0.71, 0.83, 0.9, 0.94, 0.97, 0.99, 1];
const STAGGER = 7;
// Sortie (occurrence 2) : repli des pages puis chute de la couverture.
const FOLD_F = [11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27];
const FOLD_P = [1, 0.98, 0.93, 0.878, 0.81, 0.714, 0.625, 0.55, 0.45, 0.356, 0.285, 0.21, 0.14, 0.1, 0.058, 0.024, 0];
const FALL_F = [33, 36, 39, 42, 45, 48, 51, 54, 57, 60, 62, 64];
const FALL_Y = [0, 8, 24, 44, 76, 120, 180, 264, 388, 588, 796, 1100];

const Background: React.FC = () => (
  <AbsoluteFill style={{background: '#000'}}>
    <AbsoluteFill style={{filter: 'blur(60px)'}}>
      <div style={{position: 'absolute', left: -100, top: 640, width: 1000, height: 380, borderRadius: '50%', background: 'rgba(32,70,96,0.85)', transform: 'rotate(12deg)'}} />
      <div style={{position: 'absolute', left: 820, top: 840, width: 900, height: 300, borderRadius: '50%', background: 'rgba(28,62,86,0.8)'}} />
      <div style={{position: 'absolute', left: 250, top: 930, width: 700, height: 260, borderRadius: '50%', background: 'rgba(48,66,80,0.7)'}} />
      <div style={{position: 'absolute', left: 1650, top: 250, width: 400, height: 800, borderRadius: '50%', background: 'rgba(8,18,26,0.6)'}} />
      <div style={{position: 'absolute', left: 620, top: 560, width: 520, height: 380, borderRadius: '50%', background: '#000'}} />
      <div style={{position: 'absolute', left: -300, top: 980, width: 500, height: 300, borderRadius: '50%', background: '#000'}} />
    </AbsoluteFill>
  </AbsoluteFill>
);

// Pages du playbook : vrai texte français, corps flouté comme l'original, titres nets.
// Positions relevées sur la référence (px depuis le haut de la page, texte à 75 px du bord gauche).
type El =
  | {t: 'p'; y: number; lines: string[]; blur?: boolean; size?: number; bold?: boolean; italic?: boolean; color?: string}
  | {t: 'h'; y: number; lines: string[]; size?: number}
  | {t: 'note'; y: number; text: string}
  | {t: 'link'; y: number; text: string}
  | {t: 'hl'; y: number; lines: string[]}
  | {t: 'table'; y: number; rows: number[]; cells: [string, string][]}
  | {t: 'bullets'; y: number; items: string[]; step?: number};

const BODY = `Arial, Helvetica, ${ARIAL_L}, sans-serif`;
const blurTxt = 'blur(2.1px) contrast(1.6)';

const P1: El[] = [
  {t: 'note', y: 92, text: 'Ce document fait partie de mon programme Elite Coaching.'},
  {t: 'p', y: 112, blur: true, lines: ["Vous allez découvrir le système exact que j'utilise pour intégrer", "l'IA dans chacune de mes entreprises, étape par étape."]},
  {t: 'p', y: 154, blur: true, lines: ['Il a été testé sur des équipes de 5 à 500 personnes, dans', 'des secteurs très différents, avec des résultats mesurés.']},
  {t: 'p', y: 197, blur: true, lines: ['Chaque partie contient les outils, les prompts et les', 'procédures à copier. Commencez par la partie 1, puis', 'avancez à votre rythme sans sauter les étapes clés.']},
  {t: 'p', y: 261, blur: true, lines: ['Temps nécessaire : environ 90 minutes par partie.']},
  {t: 'p', y: 290, blur: true, lines: ['Besoin d\'aide ? Rejoignez la communauté du programme.']},
  {t: 'link', y: 316, text: 'https://www.lucien-ia.com/programme'},
  {t: 'h', y: 356, lines: ["LE SYSTÈME D'EXPLOITATION IA", "DES CHEFS D'ENTREPRISE"]},
  {t: 'p', y: 431, blur: true, lines: ['Un cadre simple pour passer des tests isolés à un vrai système.']},
  {t: 'p', y: 460, blur: true, lines: ['Il se déploie en quatre parties, dans cet ordre précis.']},
  {t: 'p', y: 497, blur: true, bold: true, size: 15, lines: ['Ce que vous obtenez']},
  {t: 'bullets', y: 530, step: 15, items: ['Le plan de déploiement complet', 'Les prompts maîtres par fonction', 'Les modèles de procédures', 'La grille de suivi hebdomadaire']},
  {t: 'h', y: 615, lines: ['Le playbook IA en 4 parties']},
  {t: 'p', y: 663, blur: true, bold: true, lines: ['Partie 1 : Fondations']},
  {t: 'p', y: 694, blur: true, lines: ['Clarifiez vos objectifs, vos données et vos accès avant', "de choisir le moindre outil d'automatisation."]},
  {t: 'p', y: 736, blur: true, lines: ['Durée : une semaine, avec un point de contrôle.']},
];
const P2: El[] = [
  {t: 'h', y: 76, lines: ['Étape 2 : Choisir le bon', 'workflow']},
  {t: 'p', y: 155, bold: true, italic: true, size: 14, color: '#111', lines: ["Objectif : intégrer l'IA à vos process existants, même s'ils sont", 'chaotiques.']},
  {t: 'p', y: 204, blur: true, lines: ['Partez de ce qui existe déjà dans votre entreprise.']},
  {t: 'p', y: 232, blur: true, lines: ['Choisissez un workflow répétitif et mesurable.']},
  {t: 'p', y: 261, blur: true, bold: true, lines: ['Outil recommandé par fonction']},
  {t: 'table', y: 280, rows: [26, 46, 46, 46, 50, 30, 30, 30], cells: [['Fonction', 'Outil conseillé'], ['Contenu et marketing', 'Claude + Notion'], ['Administration', 'Claude Cowork'], ['Suivi client', 'CRM + Claude'], ['Finances et reporting', 'Claude + Sheets'], ['Ventes', 'Claude Projects'], ['Recrutement', 'Claude + Gmail'], ['Opérations', 'Claude Code']]},
  {t: 'p', y: 625, blur: true, bold: true, lines: ['Avant de passer à la suite']},
  {t: 'p', y: 654, blur: true, lines: ['Validez le workflow avec votre équipe.']},
  {t: 'bullets', y: 684, step: 30, items: ['Qui le fait aujourd\'hui ?', 'Combien de temps par semaine ?']},
];
const P3: El[] = [
  {t: 'bullets', y: 76, step: 0, items: ['Marque et stratégie']},
  {t: 'p', y: 106, blur: true, bold: true, lines: ['3. Positionnement et offre']},
  {t: 'p', y: 134, blur: true, lines: ['Définissez votre offre principale et', 'les promesses que vous tenez.']},
  {t: 'p', y: 179, blur: true, lines: ['Un seul message par canal.']},
  {t: 'h', y: 220, lines: ['Prêt à déployer ?']},
  {t: 'p', y: 259, blur: true, lines: ['Vérifiez les accès de chaque outil.']},
  {t: 'p', y: 289, blur: true, lines: ['Nommez un responsable par workflow.']},
  {t: 'p', y: 319, blur: true, lines: ['Planifiez une revue chaque semaine.']},
  {t: 'p', y: 349, blur: true, lines: ['Mesurez le temps gagné dès le départ.']},
  {t: 'p', y: 379, blur: true, lines: ['Documentez les prompts qui marchent', 'dans votre base de connaissances.']},
  {t: 'p', y: 424, blur: true, lines: ['Formez une personne référente.']},
  {t: 'p', y: 456, blur: true, lines: ['Ajoutez un contrôle humain final.']},
  {t: 'p', y: 486, blur: true, lines: ['Gardez une trace de chaque version.']},
  {t: 'p', y: 516, blur: true, lines: ['Supprimez les étapes inutiles.']},
  {t: 'p', y: 551, blur: true, bold: true, size: 15, lines: ["Contexte de l'entreprise"]},
  {t: 'p', y: 584, blur: true, lines: ['Taille, secteur, équipe, outils actuels.']},
  {t: 'p', y: 614, blur: true, lines: ['Objectifs à 90 jours et indicateurs.']},
  {t: 'hl', y: 640, lines: ['Point de vigilance majeur', 'données']},
  {t: 'p', y: 699, blur: true, lines: ['Relisez tout avant diffusion au client', 'et archivez la version finale.']},
];
const P4: El[] = [
  {t: 'bullets', y: 76, step: 0, items: ['Opérations']},
  {t: 'p', y: 106, blur: true, bold: true, lines: ['4. Tableau de suivi']},
  {t: 'table', y: 137, rows: [30, 30, 32, 44, 26], cells: [['Indicateur', 'Cible'], ['Temps gagné', '5 h'], ['Taux', '80 %'], ['Workflows actifs', '6 par équipe'], ['Coût', '0']]},
  {t: 'p', y: 329, blur: true, bold: true, lines: ['5. Revue mensuelle']},
  {t: 'p', y: 359, blur: true, lines: ['Faites le point avec votre équipe']},
  {t: 'p', y: 389, blur: true, lines: ['Gardez les meilleurs prompts']},
  {t: 'p', y: 419, blur: true, lines: ['Retirez ce qui ne sert plus']},
  {t: 'h', y: 459, lines: ["Étape 4 : Passer à l'échelle"]},
  {t: 'p', y: 507, bold: true, italic: true, size: 14, color: '#111', lines: ['Objectif : transformer les réussites en système reproductible.']},
  {t: 'p', y: 537, size: 12.5, color: '#111', lines: ["Voici comment vous passez d'un succès isolé à toute l'équipe."]},
  {t: 'p', y: 566, bold: true, size: 14, color: '#111', lines: ['1. Standardiser']},
  {t: 'p', y: 593, size: 12.5, color: '#111', lines: ['Transformez chaque workflow réussi en procédure.', 'Documentez-le dans Notion avec ses prompts.', "L'IA devient ainsi reproductible par toute l'équipe."]},
  {t: 'p', y: 653, blur: true, bold: true, lines: ['2. Déléguer à un agent']},
  {t: 'bullets', y: 686, step: 30, items: ['Tâches récurrentes', 'Revue humaine']},
];

const Elem: React.FC<{e: El}> = ({e}) => {
  const base: React.CSSProperties = {position: 'absolute', left: 0, top: e.y, whiteSpace: 'nowrap', fontFamily: BODY};
  if (e.t === 'h')
    return (
      <div style={{...base, fontWeight: 700, fontSize: e.size ?? 25, lineHeight: '32px', color: '#0c0c0c'}}>
        {e.lines.map((l, i) => (
          <div key={i}>{l}</div>
        ))}
      </div>
    );
  if (e.t === 'note')
    return (
      <div style={{...base, fontSize: 12, lineHeight: '15px', color: '#111'}}>
        <span style={{background: '#f7f700', fontWeight: 700}}>NOTE :</span>
        <span style={{background: '#f7f700'}}> {e.text}</span>
      </div>
    );
  if (e.t === 'link') return <div style={{...base, fontSize: 12.5, color: '#2a55c9', textDecoration: 'underline'}}>{e.text}</div>;
  if (e.t === 'hl')
    return (
      <div style={{...base, fontSize: 12, lineHeight: '17px', color: '#333', filter: blurTxt}}>
        {e.lines.map((l, i) => (
          <div key={i}>
            <span style={{background: i === 0 ? '#dfe63a' : 'transparent'}}>{l}</span>
          </div>
        ))}
      </div>
    );
  if (e.t === 'bullets')
    return (
      <div style={{...base, left: 22, fontSize: 12, color: '#1a1a1a', filter: blurTxt}}>
        {e.items.map((it, i) => (
          <div key={i} style={{position: 'absolute', top: i * (e.step ?? 15), whiteSpace: 'nowrap'}}>
            ▪ {it}
          </div>
        ))}
      </div>
    );
  if (e.t === 'table') {
    let acc = 0;
    return (
      <div style={{...base, width: 440, border: '2px solid #c8c8c8', filter: 'blur(0.8px)', fontSize: 11.5, color: '#1a1a1a'}}>
        {e.rows.map((h, i) => {
          const top = acc;
          acc += h;
          return (
            <div key={i} style={{position: 'absolute', top, left: 0, width: '100%', height: h, borderTop: i ? '2px solid #d0d0d0' : 'none', display: 'flex'}}>
              <div style={{width: 150, padding: '5px 8px', borderRight: '2px solid #d0d0d0', fontWeight: i ? 600 : 700, whiteSpace: 'normal', lineHeight: '14px', filter: blurTxt}}>{e.cells[i]?.[0]}</div>
              <div style={{flex: 1, padding: '5px 8px', fontWeight: i ? 600 : 700, filter: blurTxt}}>{e.cells[i]?.[1]}</div>
            </div>
          );
        })}
        <div style={{height: acc}} />
      </div>
    );
  }
  return (
    <div
      style={{
        ...base,
        fontSize: e.size ?? 12,
        lineHeight: '15px',
        fontWeight: e.bold ? 700 : 400,
        fontStyle: e.italic ? 'italic' : 'normal',
        color: e.color ?? (e.blur ? '#1a1a1a' : '#333'),
        WebkitTextStroke: e.blur ? '0.6px #1a1a1a' : undefined,
        filter: e.blur ? blurTxt : undefined,
      }}
    >
      {e.lines.map((l, i) => (
        <div key={i}>{l}</div>
      ))}
    </div>
  );
};

const PAGES: El[][] = [P1, P2, P3, P4];

const Page: React.FC<{left: number; children: React.ReactNode}> = ({left, children}) => (
  <div
    style={{
      position: 'absolute',
      left,
      top: PAGE.y,
      width: PAGE.w,
      height: PAGE.h,
      background: '#fff',
      borderRadius: 3,
      boxShadow: '-14px 0 22px rgba(0,0,0,0.18)',
      overflow: 'hidden',
    }}
  >
    <div style={{position: 'absolute', left: 75, top: 0, width: 500, height: '100%'}}>{children}</div>
    <div style={{position: 'absolute', left: 75, top: 774, fontFamily: BODY, fontSize: 12.5, color: '#2a55c9', textDecoration: 'underline'}}>lucien-ia.com</div>
  </div>
);

const Cover: React.FC<{dy: number}> = ({dy}) => (
  <div style={{position: 'absolute', left: COVER.x, top: COVER.y + dy, width: COVER.w, height: COVER.h, background: '#000', overflow: 'hidden'}}>
    <Img src={staticFile('21/couverture.png')} style={{width: '100%', height: '100%', objectFit: 'cover'}} />
    <svg width={COVER.w} height={COVER.h} style={{position: 'absolute', left: 0, top: 0}}>
      {/* « IA » : boîte relevée x 26..225, capitales 61..486 */}
      <text x={26} y={486} fontFamily={ANTON} fontSize={503} fill="#fff" textLength={199} lengthAdjust="spacingAndGlyphs">
        IA
      </text>
      {/* « PLAYBOOK » : boîte x 28..318, capitales 507..646 */}
      <text x={28} y={646} fontFamily={ANTON} fontSize={165} fill="#fff" textLength={290} lengthAdjust="spacingAndGlyphs">
        PLAYBOOK
      </text>
    </svg>
  </div>
);

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

const Entree: React.FC = () => {
  const f = useCurrentFrame();
  const dy = interpolate(f, RISE_F, RISE_Y, clamp);
  return (
    <AbsoluteFill>
      <Background />
      {PAGE_LEFT.map((l, i) => {
        const p = interpolate(f - 29 - i * STAGGER, SPREAD_T, SPREAD_P, clamp);
        return p > 0 ? (
          <Page key={i} left={COVER.x - (COVER.x - l) * p}>
            {PAGES[i].map((e, j) => (
              <Elem key={j} e={e} />
            ))}
          </Page>
        ) : null;
      })}
      <Cover dy={dy} />
    </AbsoluteFill>
  );
};

const Sortie: React.FC = () => {
  const f = useCurrentFrame();
  const p = interpolate(f, FOLD_F, FOLD_P, clamp);
  const dy = interpolate(f, FALL_F, FALL_Y, clamp);
  return (
    <AbsoluteFill>
      <Background />
      {p > 0 &&
        PAGE_LEFT.map((l, i) => (
          <Page key={i} left={COVER.x - (COVER.x - l) * p}>
            {PAGES[i].map((e, j) => (
              <Elem key={j} e={e} />
            ))}
          </Page>
        ))}
      <Cover dy={dy} />
    </AbsoluteFill>
  );
};

export const meta = {
  id: '21-ai-playbook',
  durationInFrames: 111 + 15 + 66,
  fps: 30,
  occurrences: [
    {ref: [240.84, 244.54], from: 0, durationInFrames: 111, mode: 'plein'},
    {ref: [883.58, 885.78], from: 126, durationInFrames: 66, mode: 'plein'},
  ],
};

export default function AiPlaybook() {
  return (
    <AbsoluteFill style={{background: '#000'}}>
      <Sequence durationInFrames={111}>
        <Entree />
      </Sequence>
      <Sequence from={126} durationInFrames={66}>
        <Sortie />
      </Sequence>
      {/* Bruitages. Entrée : montée de la couverture (image 2), étalement des pages (image 29).
          Sortie (début 126) : repli des pages (137), chute de la couverture (159). */}
      <SfxTrack
        cues={cuesExportees}
      />
    </AbsoluteFill>
  );
}

// Signaux sonores exportés pour la bibliothèque (cloud/cues_globaux.py).
const cuesExportees: SfxCue[] = [
          {frame: 2, name: 'whoosh-transition'},
          {frame: 29, name: 'grave-apparition'},
          {frame: 137, name: 'grave-apparition'},
          {frame: 159, name: 'whoosh-transition'},
        ];
export const cues = cuesExportees;
