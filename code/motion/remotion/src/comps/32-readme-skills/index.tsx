import React from 'react';
import {AbsoluteFill, Img, staticFile, useCurrentFrame} from '../../shared/rt';
import {INTER} from '../../shared/fonts';
import {SfxTrack, SfxCue} from '../../shared/Sfx';

// 32 : README des skills qui défile (style GitHub sombre).
// Plage de référence 454,59 s à 460,86 s (188 images).
// Chaque bloc est posé à sa position relevée dans la référence (coordonnée « document » D = y écran + défilement).
export const meta = {id: '32-readme-skills', durationInFrames: 188, fps: 30,
  occurrences: [{ref: [454.59, 460.86], from: 0, durationInFrames: 188, mode: 'plein'}],
};

const MONO = 'Menlo, "SF Mono", Monaco, monospace';
const TXT = '#E6EDF3';
const LINK = '#4493F8';
const RULE = '#21262D';
const BG = '#0B0F17';

// défilement relevé (s -> px)
const SCROLL_T = [0, 0.41, 1.41, 2.41, 2.91, 3.61, 4.41, 5.21, 5.71, 6.21, 6.27];
const SCROLL_Y = [-25, 0, 232, 628, 819, 1214, 1677, 2105, 2266, 2274, 2274];

// Interpolation cubique monotone (Fritsch-Carlson) : vitesse continue,
// accélération puis freinage comme dans l'original, sans rebond.
const monotone = (xs: number[], ys: number[]) => {
  const n = xs.length;
  const d = xs.slice(0, -1).map((x, i) => (ys[i + 1] - ys[i]) / (xs[i + 1] - x));
  const m = xs.map((_, i) => (i === 0 ? d[0] : i === n - 1 ? d[n - 2] : d[i - 1] * d[i] <= 0 ? 0 : (d[i - 1] + d[i]) / 2));
  for (let i = 0; i < n - 1; i++) {
    if (d[i] === 0) {
      m[i] = 0;
      m[i + 1] = 0;
      continue;
    }
    const a = m[i] / d[i];
    const b = m[i + 1] / d[i];
    const h = a * a + b * b;
    if (h > 9) {
      const k = 3 / Math.sqrt(h);
      m[i] = k * a * d[i];
      m[i + 1] = k * b * d[i];
    }
  }
  return (x: number) => {
    if (x <= xs[0]) return ys[0];
    if (x >= xs[n - 1]) return ys[n - 1];
    let i = 0;
    while (x > xs[i + 1]) i++;
    const hh = xs[i + 1] - xs[i];
    const u = (x - xs[i]) / hh;
    const h00 = 2 * u ** 3 - 3 * u ** 2 + 1;
    const h10 = u ** 3 - 2 * u ** 2 + u;
    const h01 = -2 * u ** 3 + 3 * u ** 2;
    const h11 = u ** 3 - u ** 2;
    return h00 * ys[i] + h10 * hh * m[i] + h01 * ys[i + 1] + h11 * hh * m[i + 1];
  };
};
const scrollAt = monotone(SCROLL_T, SCROLL_Y);

const X = 443 - 404; // marge gauche du texte dans la colonne
const W = 1027; // largeur du texte

const Code: React.FC<{children: React.ReactNode}> = ({children}) => (
  <span style={{fontFamily: MONO, fontSize: 16.5, background: '#1D232B', borderRadius: 6, padding: '2px 6px'}}>{children}</span>
);
const A: React.FC<{children: React.ReactNode}> = ({children}) => <span style={{color: LINK, textDecoration: 'underline', textUnderlineOffset: 4}}>{children}</span>;
const CodeLink: React.FC<{children: React.ReactNode}> = ({children}) => (
  <span style={{fontFamily: MONO, fontSize: 16.5, background: '#1D232B', borderRadius: 6, padding: '2px 6px', color: LINK, textDecoration: 'underline'}}>{children}</span>
);

// Paragraphe : y = centre de la première ligne
const P: React.FC<{y: number; children: React.ReactNode; x?: number; w?: number}> = ({y, children, x = X, w = W}) => (
  <div style={{position: 'absolute', left: x, top: y - 15, width: w, fontSize: 19.5, lineHeight: '29.5px', color: TXT}}>{children}</div>
);
const H2: React.FC<{y: number; rule: number; children: React.ReactNode}> = ({y, rule, children}) => (
  <>
    <div style={{position: 'absolute', left: X, top: y - 24, fontSize: 38, fontWeight: 700, color: TXT, letterSpacing: -0.4, lineHeight: '48px'}}>{children}</div>
    <div style={{position: 'absolute', left: X, top: rule, width: W, height: 1.5, background: RULE}} />
  </>
);
const H3: React.FC<{y: number; rule: number; children: React.ReactNode}> = ({y, rule, children}) => (
  <>
    <div style={{position: 'absolute', left: X, top: y - 18, fontSize: 27.5, fontWeight: 700, color: TXT, letterSpacing: -0.2, lineHeight: '36px'}}>{children}</div>
    <div style={{position: 'absolute', left: X, top: rule, width: W, height: 1.5, background: RULE}} />
  </>
);
const Li: React.FC<{y: number; children: React.ReactNode; n?: string}> = ({y, children, n}) => (
  <>
    <div style={{position: 'absolute', left: X + (n ? 17 : 20), top: y - 15, fontSize: 19.5, lineHeight: '29.5px', color: TXT}}>{n ?? '•'}</div>
    <P y={y} x={X + 39} w={W - 39}>
      {children}
    </P>
  </>
);
const CopyIcon: React.FC<{y: number}> = ({y}) => (
  <svg style={{position: 'absolute', left: 1440 - 404 - 10, top: y - 10}} width={20} height={20} viewBox="0 0 24 24" fill="none" stroke="#9198A1" strokeWidth={1.8}>
    <rect x={8} y={8} width={13} height={13} rx={2} />
    <path d="M16 8V5a2 2 0 00-2-2H5a2 2 0 00-2 2v9a2 2 0 002 2h3" />
  </svg>
);
const Block: React.FC<{top: number; bottom: number; lines: {y: number; node: React.ReactNode}[]; copy?: number}> = ({top, bottom, lines, copy}) => (
  <>
    <div style={{position: 'absolute', left: X, top, width: W, height: bottom - top, background: '#141A24', borderRadius: 6}} />
    {lines.map((l, i) => (
      <div key={i} style={{position: 'absolute', left: X + 19, top: l.y - 12, fontFamily: MONO, fontSize: 16.8, lineHeight: '24px', color: TXT, whiteSpace: 'pre'}}>
        {l.node}
      </div>
    ))}
    {copy !== undefined ? <CopyIcon y={copy} /> : null}
  </>
);

const HASH = '#3B7BE0';
const DASH = '#F0A36B';
const KEY = '#7EE787';
const VAL = '#A5D6FF';

const Doc: React.FC = () => (
  <>
    <H2 y={139} rule={174}>À propos de ce dépôt</H2>
    <P y={209}>
      Ce dépôt contient des skills qui montrent ce que permet le système de skills de Claude. Ils vont des applications créatives (art,
      musique, design) aux tâches techniques (tests d’applis web, génération de serveurs MCP) jusqu’aux flux de travail d’entreprise
      (communication, image de marque, etc.).
    </P>
    <P y={316}>
      Chaque skill tient dans son propre dossier avec un fichier <Code>SKILL.md</Code> qui contient les instructions et les métadonnées
      utilisées par Claude. Parcours ces skills pour t’inspirer ou pour comprendre les différents modèles et approches.
    </P>
    <P y={424}>
      Beaucoup de skills de ce dépôt sont open source (Apache 2.0). Nous avons aussi inclus les skills de création et d’édition de
      documents qui font tourner les <A>capacités documentaires de Claude</A>, dans les dossiers <CodeLink>skills/docx</CodeLink>,{' '}
      <CodeLink>skills/pdf</CodeLink>, <CodeLink>skills/pptx</CodeLink> et <CodeLink>skills/xlsx</CodeLink>. Leur code source est
      consultable sous licence propriétaire, et nous les partageons comme référence de skills complexes utilisés en production.
    </P>

    <H3 y={575} rule={602}>Avertissement</H3>
    <P y={637}>
      <b>Ces skills sont fournis à des fins de démonstration et de formation uniquement.</b> Certaines de ces capacités existent peut-être
      dans Claude, mais les implémentations et les comportements que Claude te renvoie peuvent différer de ces skills. Ils illustrent des
      modèles et des possibilités. Teste toujours les skills dans ton propre environnement avant de t’y fier pour des tâches critiques.
    </P>

    <H2 y={795} rule={830}>Jeux de skills</H2>
    <Li y={865}>
      <A>./skills</A> : exemples de skills pour Création et design, Développement et technique, Entreprise et communication, et
      Documents
    </Li>
    <Li y={929}>
      <A>./spec</A> : la spécification des Agent Skills
    </Li>
    <Li y={963}>
      <A>./template</A> : modèle de skill
    </Li>

    <H2 y={1032} rule={1068}>Essayer dans Claude Code, Claude.ai et l’API</H2>
    <H3 y={1117} rule={1144}>Claude Code</H3>
    <P y={1179}>
      Tu peux enregistrer ce dépôt comme marketplace de plugins Claude Code en lançant la commande suivante dans Claude
      Code :
    </P>
    <Block top={1243} bottom={1305} copy={1269} lines={[{y: 1273, node: '/plugin marketplace add anthropics/skills'}]} />
    <P y={1340}>Ensuite, pour installer un jeu de skills précis :</P>
    <Li y={1389} n="1.">
      Choisis <Code>Browse and install plugins</Code>
    </Li>
    <Li y={1423} n="2.">
      Choisis <Code>anthropic-agent-skills</Code>
    </Li>
    <Li y={1457} n="3.">
      Choisis <Code>document-skills</Code> ou <Code>example-skills</Code>
    </Li>
    <Li y={1491} n="4.">
      Choisis <Code>Install now</Code>
    </Li>
    <P y={1540}>Tu peux aussi installer directement l’un des deux plugins :</P>
    <Block
      top={1576}
      bottom={1661}
      copy={1601}
      lines={[
        {y: 1605, node: '/plugin install document-skills@anthropic-agent-skills'},
        {y: 1629, node: '/plugin install example-skills@anthropic-agent-skills'},
      ]}
    />
    <P y={1696}>
      Une fois le plugin installé, il suffit de mentionner le skill. Par exemple, si tu installes le plugin <Code>document-</Code>
      <br />
      <Code>skills</Code> depuis la marketplace, tu peux demander à Claude Code : « Utilise le skill PDF pour extraire les champs du
      formulaire de <Code>path/to/some-file.pdf</Code> »
    </P>

    <H3 y={1817} rule={1844}>Claude.ai</H3>
    <P y={1879}>Tous ces skills d’exemple sont déjà disponibles dans les offres payantes de Claude.ai.</P>
    <P y={1928}>
      Pour utiliser un skill de ce dépôt ou importer les tiens, suis <A>Utiliser les skills dans Claude</A>.
    </P>

    <H3 y={1991} rule={2018}>API Claude</H3>
    <P y={2053}>
      Tu utilises les skills d’Anthropic et les tiens via l’API Claude. Consulte le <A>guide de démarrage de l’API Skills</A>
      <br />
      pour en savoir plus.
    </P>

    <H2 y={2152} rule={2187}>Créer un skill de base</H2>
    <P y={2222}>
      Un skill se crée simplement : un dossier avec un fichier <Code>SKILL.md</Code> qui contient un en-tête YAML et des instructions. Tu
      peux partir du <b>template-skill</b> de ce dépôt :
    </P>
    <Block
      top={2285}
      bottom={2711}
      copy={2321}
      lines={[
        {y: 2316, node: <span style={{color: VAL}}>---</span>},
        {y: 2340, node: <><span style={{color: KEY}}>name</span>: <span style={{color: VAL}}>mon-skill</span></>},
        {y: 2365, node: <><span style={{color: KEY}}>description</span>: <span style={{color: VAL}}>Une description claire de ce que fait ce skill et du moment où l’utiliser</span></>},
        {y: 2389, node: <span style={{color: VAL}}>---</span>},
        {y: 2437, node: <span style={{color: HASH, fontWeight: 700}}># Nom de mon skill</span>},
        {y: 2485, node: '[Ajoute ici les instructions que Claude suivra quand ce skill est actif]'},
        {y: 2534, node: <span style={{color: HASH, fontWeight: 700}}>## Exemples</span>},
        {y: 2558, node: <><span style={{color: DASH}}>-</span> Exemple d’usage 1</>},
        {y: 2582, node: <><span style={{color: DASH}}>-</span> Exemple d’usage 2</>},
        {y: 2630, node: <span style={{color: HASH, fontWeight: 700}}>## Consignes</span>},
        {y: 2654, node: <><span style={{color: DASH}}>-</span> Consigne 1</>},
        {y: 2678, node: <><span style={{color: DASH}}>-</span> Consigne 2</>},
      ]}
    />
    <P y={2746}>L’en-tête n’exige que deux champs :</P>
    <Li y={2795}>
      <Code>name</Code> : identifiant unique de ton skill (minuscules, tirets à la place des espaces)
    </Li>
    <Li y={2830}>
      <Code>description</Code> : description complète de ce que fait le skill et du moment où l’utiliser
    </Li>
    <P y={2879}>
      Le contenu markdown contient les instructions, exemples et consignes que Claude suivra. Pour en savoir plus, vois{' '}
      <A>Créer des skills personnalisés</A>.
    </P>

    <H2 y={2977} rule={3012}>Skills partenaires</H2>
    <P y={3047}>
      Les skills sont un excellent moyen d’apprendre à Claude à mieux utiliser un logiciel précis. Quand nous verrons passer de bons
      skills d’exemple chez nos partenaires, nous en présenterons certains ici :
    </P>
    <Li y={3126}>
      <b>Notion</b> - <A>Skills Notion pour Claude</A>
    </Li>
  </>
);

export default function ReadmeSkills() {
  const f = useCurrentFrame();
  const t = f / 30;
  const s = scrollAt(t);
  const COL_L = 404;
  const COL_W = 1105;
  return (
    <AbsoluteFill style={{fontFamily: INTER}}>
      <SfxTrack cues={cuesExportees} />
      <Img src={staticFile('32/bg.jpg')} style={{position: 'absolute', width: 1920, height: 1080}} />
      {/* fenêtre */}
      <div
        style={{
          position: 'absolute',
          left: 194,
          top: 73,
          width: 1535,
          height: 940,
          borderRadius: 22,
          border: '1.5px solid rgba(215,220,230,0.7)',
          background: BG,
          overflow: 'hidden',
          boxShadow: '0 20px 60px rgba(0,0,0,0.5)',
        }}
      >
        {/* colonne README, décalée par le défilement */}
        <div style={{position: 'absolute', left: COL_L - 194, top: -73 - s, width: COL_W, height: 3180 + 73}}>
          {/* cadre de la colonne : bords gauche/droite + bas */}
          <div style={{position: 'absolute', left: 0, top: 0, width: COL_W, height: 3180 - 0, borderLeft: '1.5px solid #262A33', borderRight: '1.5px solid #262A33', borderBottom: '1.5px solid #262A33', borderRadius: '0 0 8px 8px', boxSizing: 'border-box'}} />
          <Doc />
        </div>
        {/* en-tête README fixe */}
        <div style={{position: 'absolute', left: COL_L - 194, top: 0, width: COL_W, height: 56, background: BG, borderLeft: '1.5px solid #262A33', borderRight: '1.5px solid #262A33', borderBottom: '1.5px solid #262A33', boxSizing: 'border-box'}}>
          <svg style={{position: 'absolute', left: 19, top: 18}} width={21} height={20} viewBox="0 0 24 22" fill="none" stroke="#E6EDF3" strokeWidth={1.8} strokeLinejoin="round">
            <path d="M2 3h6a4 4 0 014 4v13a3 3 0 00-3-3H2z M22 3h-6a4 4 0 00-4 4v13a3 3 0 013-3h7z" />
          </svg>
          <div style={{position: 'absolute', left: 48, top: 16, color: TXT, fontSize: 16.5, fontWeight: 700}}>README</div>
          <div style={{position: 'absolute', left: 9, top: 53, width: 123, height: 3, borderRadius: 2, background: '#F78166'}} />
          <svg style={{position: 'absolute', left: 1017, top: 17}} width={20} height={20} viewBox="0 0 24 24" fill="none" stroke="#9198A1" strokeWidth={1.8} strokeLinejoin="round">
            <path d="M16.5 3.5l4 4L8 20H4v-4z" />
          </svg>
          <svg style={{position: 'absolute', left: 1064, top: 17}} width={21} height={20} viewBox="0 0 24 24" fill="none" stroke="#9198A1" strokeWidth={1.8} strokeLinecap="round">
            <path d="M9 6h12M9 12h12M9 18h12M4 6h.01M4 12h.01M4 18h.01" />
          </svg>
        </div>
      </div>
    </AbsoluteFill>
  );
}

// Signaux sonores exportés pour la bibliothèque (cloud/cues_globaux.py).
const cuesExportees: SfxCue[] = [{frame: 0, name: 'whoosh-transition'}];
export const cues = cuesExportees;
