// Maquettes Gmail, Google Agenda, Google Drive, Slack et Notion, données fictives en français.
// Coordonnées locales mesurées sur la référence (origine = coin haut gauche de la fenêtre).
import React from 'react';
import {loadFont as roboto} from '@remotion/google-fonts/Roboto';
import {GmailLogo, DriveLogo, CalLogo, NotionLogo} from './logos';
import {SANS} from './ui';
import {ARIAL_L} from '../../shared/localFonts';

export const ROBOTO = roboto('normal', {weights: ['400', '500', '700']}).fontFamily;

const A: React.FC<{x: number; y: number; children?: React.ReactNode; style?: React.CSSProperties}> = ({x, y, children, style}) => (
  <div style={{position: 'absolute', left: x, top: y, whiteSpace: 'nowrap', ...style}}>{children}</div>
);
// Texte centré verticalement sur y.
const Tx: React.FC<{x: number; y: number; s: number; c: string; w?: number; ff?: string; children: React.ReactNode; style?: React.CSSProperties}> = ({x, y, s, c, w = 400, ff, children, style}) => (
  <div style={{position: 'absolute', left: x, top: y - s * 0.62, fontSize: s, color: c, fontWeight: w, fontFamily: ff, whiteSpace: 'nowrap', lineHeight: 1.2, ...style}}>{children}</div>
);
const Ico: React.FC<{x: number; y: number; s?: number; c: string; d: string; sw?: number}> = ({x, y, s = 20, c, d, sw = 1.8}) => (
  <svg width={s} height={s} viewBox="0 0 24 24" style={{position: 'absolute', left: x - s / 2, top: y - s / 2}} fill="none" stroke={c} strokeWidth={sw} strokeLinecap="round" strokeLinejoin="round"><path d={d} /></svg>
);
const D = {
  menu: 'M4 6h16M4 12h16M4 18h16',
  search: 'M11 4a7 7 0 1 0 0 14 7 7 0 0 0 0-14zM20 20l-4-4',
  help: 'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18zM9.5 9.5a2.5 2.5 0 1 1 3.5 2.3c-.7.3-1 .9-1 1.7M12 16.5v.5',
  gear: 'M12 8.8a3.2 3.2 0 1 0 0 6.4 3.2 3.2 0 0 0 0-6.4zM10.2 3h3.6l.5 2.4 1.7 1 2.3-.8 1.8 3.1-1.8 1.6v2l1.8 1.6-1.8 3.1-2.3-.8-1.7 1-.5 2.4h-3.6l-.5-2.4-1.7-1-2.3.8-1.8-3.1 1.8-1.6v-2L3.9 9.5l1.8-3.1 2.3.8 1.7-1z',
  apps: 'M5 5h.01M12 5h.01M19 5h.01M5 12h.01M12 12h.01M19 12h.01M5 19h.01M12 19h.01M19 19h.01',
  back: 'M19 12H5M11 6l-6 6 6 6',
  fwd: 'M5 12h14M13 6l6 6-6 6',
  reload: 'M20 12a8 8 0 1 1-2.3-5.7M20 4v5h-5',
  star: 'M12 3.5l2.6 5.3 5.9.9-4.3 4.1 1 5.8L12 16.9l-5.2 2.7 1-5.8-4.3-4.1 5.9-.9z',
  plus: 'M12 5v14M5 12h14',
  chevR: 'M9 6l6 6-6 6',
  chevL: 'M15 6l-6 6 6 6',
  chevD: 'M6 9l6 6 6-6',
  kebab: 'M12 5h.01M12 12h.01M12 19h.01',
  x: 'M6 6l12 12M18 6L6 18',
  pen: 'M4 20l1-4.5L16 4.5a2 2 0 0 1 3 3L8 18.5zM14 6.5l3 3',
  inbox: 'M4 4h16v16H4zM4 14h5l1.5 2h3L15 14h5',
  clock: 'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18zM12 7v5l3 2',
  send: 'M4 4l16 8-16 8 3-8z',
  file: 'M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8zM14 3v5h5',
  mail: 'M3 5h18v14H3zM3 5l9 7 9-7',
  spam: 'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18zM12 7v6M12 16.5v.5',
  archive: 'M4 4h16v4H4zM5 8v12h14V8M10 12h4',
  refresh: 'M20 12a8 8 0 1 1-2.3-5.7M20 4v5h-5',
  sliders: 'M4 7h10M18 7h2M4 17h4M12 17h8M14 5v4M8 15v4',
  lock: 'M6 11h12v9H6zM8.5 11V8a3.5 3.5 0 0 1 7 0v3',
  home: 'M4 11l8-7 8 7v9h-5v-6H9v6H4z',
  people: 'M9 11a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7zM2.5 20a6.5 6.5 0 0 1 13 0M16 4.5a3.5 3.5 0 0 1 0 6.5M18 14a5.5 5.5 0 0 1 3.5 6',
  trash: 'M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13',
  cloud: 'M7 18a5 5 0 1 1 1-9.9A6 6 0 0 1 19.5 10 4 4 0 0 1 18 18z',
  info: 'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18zM12 11v6M12 7.5v.5',
  list: 'M8 6h12M8 12h12M8 18h12M4 6h.01M4 12h.01M4 18h.01',
  grid: 'M4 4h7v7H4zM13 4h7v7h-7zM4 13h7v7H4zM13 13h7v7h-7z',
  folder: 'M3 6a1 1 0 0 1 1-1h5l2 2h9a1 1 0 0 1 1 1v10a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1z',
  hash: 'M5 9h14M5 15h14M10 4L8 20M16 4l-2 16',
  bell: 'M6 16V11a6 6 0 0 1 12 0v5l1.5 2h-15zM10 20.5a2 2 0 0 0 4 0',
  dots: 'M5 12h.01M12 12h.01M19 12h.01',
  msg: 'M4 5h16v11H9l-5 4z',
  threads: 'M4 5h16v11H9l-5 4zM8 9h8M8 12h5',
  headph: 'M4 15v-3a8 8 0 0 1 16 0v3M4 15h3v5H4zM17 15h3v5h-3z',
  edit: 'M4 20h4L19 9l-4-4L4 16zM13 7l4 4',
  cal: 'M4 6h16v14H4zM4 10h16M8 3v4M16 3v4',
  check: 'M5 12l4.5 4.5L19 7',
  doc: 'M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8zM14 3v5h5M9 13h6M9 16.5h6',
  link: 'M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1',
  code: 'M9 7l-5 5 5 5M15 7l5 5-5 5',
  smile: 'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18zM8.5 14a4 4 0 0 0 7 0M9 9.5h.01M15 9.5h.01',
  at: 'M16 12a4 4 0 1 1-1.2-2.8V13a2 2 0 0 0 4 0v-1a7 7 0 1 0-2.8 5.6',
  video: 'M3 7h13v10H3zM16 10.5l5-3v9l-5-3',
  mic: 'M9 4a3 3 0 0 1 6 0v7a3 3 0 0 1-6 0zM5.5 11a6.5 6.5 0 0 0 13 0M12 17.5V21',
  target: 'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18zM12 7a5 5 0 1 0 0 10 5 5 0 0 0 0-10zM12 11a1 1 0 1 0 0 2 1 1 0 0 0 0-2z',
};

// Barre Chrome sombre : onglet + barre d'adresse.
const Chrome: React.FC<{W: number; tab: string; icon: React.ReactNode; url: [string, string]}> = ({W, tab, icon, url}) => (
  <>
    <div style={{position: 'absolute', left: 0, top: 0, width: W, height: 38, background: '#1c1c1c'}} />
    {['#ff5f57', '#febc2e', '#28c840'].map((c, i) => <div key={i} style={{position: 'absolute', left: 13 + i * 18, top: 12, width: 12, height: 12, borderRadius: 6, background: c}} />)}
    <div style={{position: 'absolute', left: 80, top: 5, width: 208, height: 33, borderRadius: '9px 9px 0 0', background: '#2d2d2d'}}>
      <div style={{position: 'absolute', left: 9, top: 9}}>{icon}</div>
      <Tx x={30} y={17} s={11.5} c="#e8e8e8" ff={ROBOTO} style={{width: 140, overflow: 'hidden', WebkitMaskImage: 'linear-gradient(90deg,#000 80%,transparent)'}}>{tab}</Tx>
      <Ico x={190} y={17} s={12} c="#cfcfcf" d={D.x} />
    </div>
    <Ico x={303} y={19} s={16} c="#cfcfcf" d={D.plus} />
    <div style={{position: 'absolute', left: 0, top: 38, width: W, height: 38, background: '#2d2d2d'}} />
    <Ico x={20} y={57} s={16} c="#bdbdbd" d={D.back} />
    <Ico x={50} y={57} s={16} c="#8a8a8a" d={D.fwd} />
    <Ico x={80} y={57} s={16} c="#bdbdbd" d={D.reload} />
    <div style={{position: 'absolute', left: 120, top: 44, width: W - 225, height: 27, borderRadius: 14, background: '#1f1f1f'}}>
      <Ico x={16} y={13.5} s={12} c="#bdbdbd" d={D.lock} />
      <Tx x={30} y={14} s={12.5} c="#9a9a9a" ff={ROBOTO}><span style={{color: '#e8e8e8'}}>{url[0]}</span>{url[1]}</Tx>
      <Ico x={W - 250} y={13.5} s={15} c="#bdbdbd" d={D.star} />
    </div>
    <Ico x={W - 78} y={57} s={15} c="#bdbdbd" d={D.chevR} />
    <Ico x={W - 51} y={57} s={15} c="#bdbdbd" d={D.file} />
    <Ico x={W - 20} y={57} s={15} c="#bdbdbd" d={D.kebab} sw={2.6} />
  </>
);

const Avatar: React.FC<{x: number; y: number; s: number}> = ({x, y, s}) => (
  <div style={{position: 'absolute', left: x - s / 2, top: y - s / 2, width: s, height: s, borderRadius: s / 2, overflow: 'hidden',
    background: 'radial-gradient(circle at 50% 38%, #e2b89a 0 28%, #3b2c24 29% 36%, #e9e9ea 37%)', border: '1.5px solid #fff'}}>
    <div style={{position: 'absolute', left: s * 0.2, top: s * 0.68, width: s * 0.6, height: s * 0.5, borderRadius: '50% 50% 0 0', background: '#2f3b4f'}} />
  </div>
);

const Rail: React.FC<{x: number; y0: number; gap: number; maps?: boolean; dark?: boolean; noCal?: boolean}> = ({x, y0: y1, gap, maps, dark, noCal}) => {
  const y0 = noCal ? y1 - gap : y1;
  return (
  <>
    {!noCal && <div style={{position: 'absolute', left: x - 9, top: y0 - 9}}><CalLogo size={18} /></div>}
    <svg width="18" height="18" viewBox="0 0 24 24" style={{position: 'absolute', left: x - 9, top: y0 + gap - 9}}><rect x="3" y="2" width="18" height="20" rx="2.5" fill="#FBBC04" /><path d="M12 7a3.6 3.6 0 0 0-2 6.6V15h4v-1.4A3.6 3.6 0 0 0 12 7zM10.4 17h3.2" stroke="#fff" strokeWidth="1.5" fill="none" /></svg>
    <svg width="18" height="18" viewBox="0 0 24 24" style={{position: 'absolute', left: x - 9, top: y0 + 2 * gap - 9}}><circle cx="12" cy="12" r="9" fill="none" stroke="#1A73E8" strokeWidth="2.6" /><path d="M8 12.2l2.7 2.7L17 8.6" stroke="#1A73E8" strokeWidth="2.6" fill="none" /><path d="M16.5 3.8L21 3" stroke={dark ? '#1f2121' : '#fff'} strokeWidth="3" /></svg>
    <svg width="18" height="18" viewBox="0 0 24 24" style={{position: 'absolute', left: x - 9, top: y0 + 3 * gap - 9}}><circle cx="12" cy="12" r="10" fill="#1A73E8" /><circle cx="12" cy="9.5" r="3.2" fill="#fff" /><path d="M6 17.5a6.5 4.5 0 0 1 12 0z" fill="#fff" /></svg>
    {maps && <svg width="18" height="18" viewBox="0 0 24 24" style={{position: 'absolute', left: x - 9, top: y0 + 4 * gap - 9}}><path d="M12 2a7 7 0 0 0-7 7c0 5.2 7 13 7 13s7-7.8 7-13a7 7 0 0 0-7-7z" fill="#34A853" /><path d="M12 2a7 7 0 0 1 7 7c0 1.3-.4 2.7-1 4L9 4.6A7 7 0 0 1 12 2z" fill="#4285F4" /><path d="M5 9a7 7 0 0 1 2-4.9l5.3 5.3L6 15.2C5.4 13.1 5 11 5 9z" fill="#FBBC04" /><circle cx="12" cy="9" r="2.4" fill="#EA4335" /></svg>}
  </>
  );
};

// ---------------- Gmail (fenêtre 1363 x 840) ----------------
const MAILS: [string, string, string, string, boolean, boolean][] = [
  ['Sarah Chen (Invest…)', 'Point investisseurs T2 : Novateur', 'Salut Alex, voici le deck du T2 pour notre prochaine…', '9:41', true, false],
  ['David, Acme Corp', 'Contrat signé : accord de partenariat', 'Bonne nouvelle ! L’accord a été signé…', '8:22', true, false],
  ['Rapport hebdo équipe', 'Rapport hebdo : semaine 24', 'Salut Alex, voici l’avancement de l’équipe cette semaine.', '7:15', true, false],
  ['Emily Rogers', 'Retours client : plateforme Novateur', 'Salut Alex, je te partage des retours reçus de…', '6:45', false, true],
  ['finance@novateur.co', 'Tableau de bord du CA : mai 2026', 'Alex, voici ton récapitulatif mensuel du chiffre d’affaires.', '27 mai', false, false],
  ['Michael Lee', 'Nouveau partenariat : collaboration possible', 'Salut Alex, j’aimerais te présenter…', '27 mai', false, true],
  ['Google Agenda', '📅 Point d’équipe hebdo | 28 mai 2026 à 10:00', 'Tu as été invité à l’événement suivant…', '27 mai', false, false],
  ['Slack', 'Résumé des notifications Slack', 'Tu as 12 nouveaux messages et 5 mentions dans 3 canaux.', '27 mai', false, false],
  ['Notion', 'Nouveautés de l’espace Novateur HQ', 'Découvre les nouveautés de ton espace cette semaine.', '26 mai', false, false],
  ['Stripe', 'Virement Stripe confirmé : 86 923,41 $', 'Ton virement du 26 mai 2026 a été…', '26 mai', false, false],
  ['Alex Johnson (mentor)', 'Petit point', 'Je voulais savoir comment ça avance. Dis-moi si tu as besoin…', '26 mai', false, true],
  ['LinkedIn', '5 nouvelles invitations', 'Découvre qui veut entrer en contact avec toi.', '25 mai', false, false],
  ['Product Hunt', 'Ton produit est en tendance !', 'Novateur fait parler de lui aujourd’hui 🚀', '25 mai', false, false],
  ['Jane, Stripe', 'Mises à jour du tableau de bord Stripe', 'Des changements importants à connaître.', '25 mai', false, true],
  ['Amazon Web Services', 'Facture AWS : mai 2026', 'Ta facture est disponible.', '24 mai', false, false],
  ['Google Workspace', 'Alerte sécurité : connexion sur MacBook Pro', 'Ton compte a été utilisé sur un nouvel appareil.', '24 mai', false, false],
  ['Équipe RH', 'Intégration : nouvelles recrues', 'Merci de relire le plan d’intégration des nouveaux.', '23 mai', false, false],
  ['Support', 'Synthèse support : rapport hebdo', 'Voici le résumé des tickets clients…', '23 mai', false, false],
  ['Équipe marketing', 'Résultats de campagne : mai 2026', 'Les derniers chiffres de campagne sont prêts.', '22 mai', false, false],
  ['Conseil d’administration', 'Conseil : 3 juin 2026', 'Merci de confirmer ta présence à la prochaine réunion.', '22 mai', false, true],
];
export const Gmail: React.FC = () => {
  const W = 1363;
  const nav: [string, string, string?, boolean?][] = [
    [D.inbox, 'Boîte de réception', '12', true], [D.star, 'Suivis'], [D.clock, 'En attente'], [D.send, 'Envoyés'], [D.file, 'Brouillons', '3', true],
    [D.mail, 'Tous les messages'], [D.spam, 'Spam', '7', true], [D.archive, 'Archives'], [D.chevD, 'Plus'],
  ];
  const labels: [string, string][] = [['#4a86e8', 'Clients'], ['#16a765', 'Investisseurs'], ['#ff7537', 'Produit'], ['#b99aff', 'Équipe'], ['#fad165', 'Perso']];
  return (
    <div style={{position: 'absolute', inset: 0, background: '#151817', fontFamily: ROBOTO, overflow: 'hidden'}}>
      <Chrome W={W} tab="Boîte de réception (12) - alex@novateur.co" icon={<GmailLogo size={14} />} url={['mail.google.com', '/mail/u/0/#inbox']} />
      <Ico x={32} y={108} s={20} c="#c4c7c5" d={D.menu} />
      <GmailLogo size={32} style={{position: 'absolute', left: 58, top: 96}} />
      <Tx x={98} y={109} s={21} c="#e3e3e3">Gmail</Tx>
      <div style={{position: 'absolute', left: 240, top: 86, width: 641, height: 44, borderRadius: 22, background: '#373a3a'}}>
        <Ico x={24} y={22} s={19} c="#c4c7c5" d={D.search} />
        <Tx x={47} y={23} s={16} c="#c4c7c5">Rechercher dans les messages</Tx>
        <Ico x={615} y={22} s={19} c="#c4c7c5" d={D.sliders} />
      </div>
      <div style={{position: 'absolute', left: 1031, top: 91, width: 104, height: 34, borderRadius: 17, background: '#1e2120', border: '1px solid #2c2f2e'}}>
        <div style={{position: 'absolute', left: 14, top: 12, width: 10, height: 10, borderRadius: 5, border: '2px solid #6dd58c'}} />
        <Tx x={33} y={17} s={15} c="#e3e3e3" w={500}>Actif</Tx>
        <Ico x={88} y={17} s={13} c="#c4c7c5" d={D.chevD} />
      </div>
      <Ico x={1185} y={108} s={21} c="#c4c7c5" d={D.help} />
      <Ico x={1230} y={108} s={21} c="#c4c7c5" d={D.gear} />
      <Ico x={1274} y={108} s={21} c="#c4c7c5" d={D.apps} sw={3.2} />
      <Avatar x={1329} y={108} s={34} />
      <div style={{position: 'absolute', left: 9, top: 146, width: 134, height: 51, borderRadius: 16, background: '#f8f8f8', boxShadow: '0 1px 3px rgba(0,0,0,0.4)'}}>
        <Ico x={24} y={25} s={18} c="#1f1f1f" d={D.pen} />
        <Tx x={45} y={26} s={14.5} c="#1f1f1f" w={500}>Nouveau</Tx>
      </div>
      {nav.map(([d, t, n, b], i) => (
        <div key={i}>
          {i === 0 && <div style={{position: 'absolute', left: 0, top: 213, width: 225, height: 29, borderRadius: '0 15px 15px 0', background: '#383b3b'}} />}
          <Ico x={32} y={227 + i * 29} s={16} c="#c4c7c5" d={d} />
          <Tx x={57} y={227 + i * 29} s={14} c="#e3e3e3" w={b ? 700 : 400}>{t}</Tx>
          {n && <Tx x={200} y={227 + i * 29} s={12} c="#e3e3e3" w={700}>{n}</Tx>}
        </div>
      ))}
      <Tx x={22} y={506} s={16.5} c="#e3e3e3" w={500}>Libellés</Tx>
      <Ico x={208} y={506} s={17} c="#c4c7c5" d={D.plus} />
      {labels.map(([c, t], i) => (
        <div key={i}>
          <div style={{position: 'absolute', left: 25, top: 539 + i * 30, width: 13, height: 10, borderRadius: '2px 5px 5px 2px', background: c}} />
          <Tx x={55} y={544 + i * 30} s={13.5} c="#e3e3e3">{t}</Tx>
        </div>
      ))}
      <Ico x={32} y={693} s={14} c="#c4c7c5" d={D.chevD} />
      <Tx x={55} y={693} s={13.5} c="#e3e3e3">Plus</Tx>
      {/* liste */}
      <div style={{position: 'absolute', left: 240, top: 140, width: 1068, height: 700, borderRadius: '16px 16px 0 0', background: '#1f2121'}}>
        <div style={{position: 'absolute', left: 18, top: 17, width: 14, height: 14, border: '2px solid #aaa', borderRadius: 2}} />
        <Ico x={45} y={25} s={12} c="#aaa" d={D.chevD} />
        <Ico x={80} y={24} s={17} c="#c4c7c5" d={D.refresh} />
        <Ico x={118} y={24} s={17} c="#c4c7c5" d={D.kebab} sw={2.6} />
        <Tx x={940} y={24} s={12} c="#c4c7c5">1-20 sur 642</Tx>
        <Ico x={1033} y={24} s={15} c="#777" d={D.chevL} />
        <Ico x={1067} y={24} s={15} c="#c4c7c5" d={D.chevR} />
        {MAILS.map(([from, subj, snip, date, unread, star], i) => {
          const y = 66 + i * 31.3;
          return (
            <div key={i}>
              <div style={{position: 'absolute', left: 0, top: y - 15.6, width: 1068, height: 31.3, borderBottom: '1px solid #262828', background: unread ? '#1f2121' : '#1f2121'}} />
              <div style={{position: 'absolute', left: 19, top: y - 7, width: 13, height: 13, border: '1.8px solid #9a9a9a', borderRadius: 2}} />
              <svg width="17" height="17" viewBox="0 0 24 24" style={{position: 'absolute', left: 331 - 240 - 30, top: y - 8.5}}>
                <path d={D.star} fill={star ? '#fcc934' : 'none'} stroke={star ? '#fcc934' : '#8a8a8a'} strokeWidth="1.8" strokeLinejoin="round" />
              </svg>
              <Tx x={89} y={y} s={14.2} c="#e3e3e3" w={400}>
                {from}{unread && <span style={{marginLeft: 8, padding: '1px 5px', borderRadius: 4, background: '#2f6fe6', color: '#fff', fontSize: 10.5, fontWeight: 500, verticalAlign: 1.5}}>Nouveau</span>}
              </Tx>
              <div style={{position: 'absolute', left: 314, top: y - 9, width: 660, overflow: 'hidden', whiteSpace: 'nowrap', textOverflow: 'ellipsis', fontSize: 14.2, color: '#b5b8b7', lineHeight: 1.2}}>
                <span style={{color: '#e3e3e3', fontWeight: unread || i < 20 ? 500 : 400}}>{subj}</span> - {snip}
              </div>
              <Tx x={1041} y={y} s={13} c="#e3e3e3" w={i < 4 ? 700 : 400} style={{transform: 'translateX(-100%)'}}>{date}</Tx>
            </div>
          );
        })}
      </div>
      {/* rail droit */}
      <Rail x={1335} y0={166} gap={51} dark />
      <Ico x={1336} y={380} s={18} c="#c4c7c5" d={D.plus} />
    </div>
  );
};

// ---------------- Google Agenda (fenêtre 1372 x 851) ----------------
type Ev = [number, number, number, string, string, string];
const CAL = {blue: ['#d3e3fd', '#1c3a6b', '#3b78e7', '#aecbfa'], green: ['#e0f1e6', '#174a2e', '#5fb883', '#b7dfc6'], pink: ['#f8d9d8', '#5c1a17', '#e06666', '#f2b8b6'], purple: ['#e6ddf7', '#3a2a66', '#9a7fd6', '#cfc0ef'], yellow: ['#fcefc8', '#5a4506', '#f2c14e', '#f5dc98']};
const EVENTS: Ev[] = [
  [0, 7, 8, 'Routine du matin', '7h - 8h', 'green'], [0, 9, 10, 'Planning hebdo', '9h - 10h', 'blue'], [0, 11, 12, 'Revue produit', '11h - 12h', 'purple'],
  [0, 12, 13, 'Déjeuner', '12h - 13h', 'green'], [0, 13, 15, 'Prépa point investisseurs', '13h - 15h', 'blue'], [0, 15, 17, 'Temps de focus', '15h - 17h', 'pink'], [0, 19, 20, 'Dîner en famille', '19h - 20h', 'purple'],
  [1, 8, 8.7, 'Point d’équipe', '8h - 8h30', 'blue'], [1, 9, 10.7, 'Synchro direction', '9h - 10h30', 'blue'], [1, 11, 12, 'Bloc de travail', '11h - 12h', 'yellow'], [1, 12, 13, 'Déjeuner', '12h - 13h', 'green'],
  [1, 13, 14, 'Revue marketing', '13h - 14h', 'blue'], [1, 14, 14.7, 'Tête-à-tête Sarah', '14h - 14h30', 'blue'], [1, 15, 17, 'Stratégie de croissance', '15h - 17h', 'blue'], [1, 18, 19, 'Sport', '18h - 19h', 'pink'],
  [2, 8, 8.7, 'Point d’équipe', '8h - 8h30', 'blue'], [2, 9, 10.7, 'Roadmap produit', '9h - 10h30', 'blue'], [2, 11, 12, 'Appel client : Acme', '11h - 12h', 'purple'], [2, 12, 13, 'Déjeuner', '12h - 13h', 'green'],
  [2, 13, 14, 'Synchro technique', '13h - 14h', 'blue'], [2, 14, 15, 'Revue du board deck', '14h - 15h', 'blue'], [2, 15, 17, 'Temps de focus', '15h - 17h', 'pink'], [2, 19, 20, 'Veille : tendances IA', '19h - 20h', 'blue'],
  [3, 8, 8.7, 'Point d’équipe', '8h - 8h30', 'blue'], [3, 9, 10, 'Revue du pipeline', '9h - 10h', 'blue'], [3, 10.5, 11.5, 'Bloc de travail', '10h30 - 11h30', 'yellow'], [3, 12, 13, 'Déjeuner', '12h - 13h', 'green'],
  [3, 13, 14, 'Appel partenaire', '13h - 14h', 'blue'], [3, 14, 15, 'Revue financière', '14h - 15h', 'blue'], [3, 15, 16, 'Comité recrutement', '15h - 16h', 'blue'], [3, 16, 18, 'Temps de focus', '16h - 18h', 'pink'],
  [4, 8, 8.7, 'Point d’équipe', '8h - 8h30', 'blue'], [4, 9, 10, 'Suivi succès client', '9h - 10h', 'blue'], [4, 11, 12, 'Démo : bêta-testeurs', '11h - 12h', 'purple'], [4, 12, 13, 'Déjeuner', '12h - 13h', 'green'],
  [4, 13, 14, 'Retours produit', '13h - 14h', 'blue'], [4, 14, 15.7, 'Stratégie marketing', '14h - 15h30', 'blue'], [4, 16, 18, 'Temps de focus', '16h - 18h', 'pink'], [4, 19, 21, 'Dîner fondateurs', '19h - 21h', 'purple'],
  [5, 7, 8, 'Routine du matin', '7h - 8h', 'green'], [5, 9, 10, 'Réunion générale', '9h - 10h', 'blue'], [5, 10.5, 11.5, 'Bloc de travail', '10h30 - 11h30', 'yellow'], [5, 12, 13, 'Déjeuner', '12h - 13h', 'green'],
  [5, 13, 14, 'Revue des KPI T2', '13h - 14h', 'blue'], [5, 14, 15, 'Rétro d’équipe', '14h - 15h', 'blue'], [5, 15, 17, 'Temps de focus', '15h - 17h', 'pink'],
  [6, 8.8, 12, 'Rando', '8h - 12h', 'green'], [6, 13, 17, 'Temps perso', '13h - 17h', 'purple'],
];
export const Calendar: React.FC = () => {
  const W = 1372;
  const dayX = (i: number) => 291 + i * 147;
  const hy = (h: number) => 247 + (h - 7) * 44.6;
  const days = ['DIM.', 'LUN.', 'MAR.', 'MER.', 'JEU.', 'VEN.', 'SAM.'];
  const nums = ['26', '27', '28', '29', '30', '31', '1'];
  const mini = [['26', '27', '28', '29', '30', '1', '2'], ['3', '4', '5', '6', '7', '8', '9'], ['10', '11', '12', '13', '14', '15', '16'], ['17', '18', '19', '20', '21', '22', '23'], ['24', '25', '26', '27', '28', '29', '30'], ['31', '1', '2', '3', '4', '5', '6']];
  const cals: [string, string][] = [['#4285f4', 'Alex Johnson'], ['#8e63ce', 'Tâches'], ['#33b679', 'Anniversaires'], ['#f6bf26', 'Rappels'], ['#e67c73', 'Temps de focus']];
  return (
    <div style={{position: 'absolute', inset: 0, background: '#fff', fontFamily: ROBOTO, overflow: 'hidden'}}>
      <Chrome W={W} tab="Google Agenda - Semaine du 26 mai" icon={<CalLogo size={14} day="" />} url={['calendar.google.com', '/calendar/u/0/r/week/2026/5/26']} />
      <Ico x={32} y={108} s={20} c="#444746" d={D.menu} />
      <CalLogo size={29} style={{position: 'absolute', left: 61, top: 93}} />
      <Tx x={100} y={109} s={21} c="#1f1f1f">Agenda</Tx>
      <div style={{position: 'absolute', left: 236, top: 90, width: 88, height: 37, borderRadius: 19, border: '1px solid #c4c7c5', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 14, color: '#1f1f1f', fontWeight: 500}}>Aujourd’hui</div>
      <Ico x={346} y={108} s={16} c="#444746" d={D.chevL} sw={2.2} />
      <Ico x={376} y={108} s={16} c="#444746" d={D.chevR} sw={2.2} />
      <Tx x={409} y={109} s={21} c="#1f1f1f">Mai - juin 2026</Tx>
      <Ico x={952} y={108} s={20} c="#444746" d={D.search} />
      <Ico x={993} y={108} s={20} c="#444746" d={D.help} />
      <Ico x={1036} y={108} s={20} c="#444746" d={D.gear} />
      <div style={{position: 'absolute', left: 1065, top: 90, width: 92, height: 37, borderRadius: 19, border: '1px solid #c4c7c5', fontSize: 14, color: '#1f1f1f', fontWeight: 500}}>
        <Tx x={16} y={18} s={14} c="#1f1f1f" w={500}>Semaine</Tx><Ico x={75} y={18} s={12} c="#444" d={D.chevD} />
      </div>
      <div style={{position: 'absolute', left: 1162, top: 90, width: 106, height: 37, borderRadius: 19, border: '1px solid #c4c7c5', overflow: 'hidden'}}>
        <div style={{position: 'absolute', left: 0, top: 0, width: 53, height: 37, background: '#c2e7ff'}} />
        <Ico x={27} y={18.5} s={17} c="#001d35" d={D.cal} />
        <Ico x={80} y={18.5} s={17} c="#444746" d={D.check} />
      </div>
      <Ico x={1294} y={108} s={20} c="#444746" d={D.apps} sw={3.2} />
      <Avatar x={1339} y={108} s={33} />
      <div style={{position: 'absolute', left: 12, top: 150, width: 131, height: 48, borderRadius: 14, background: '#fff', boxShadow: '0 1px 3px rgba(0,0,0,0.3), 0 1px 1px rgba(0,0,0,0.1)'}}>
        <svg width="22" height="22" viewBox="0 0 24 24" style={{position: 'absolute', left: 13, top: 13}}><path d="M12 3v18" stroke="#4285f4" strokeWidth="2.6" /><path d="M3 12h18" stroke="#ea4335" strokeWidth="2.6" /><path d="M12 12v9" stroke="#34a853" strokeWidth="2.6" /><path d="M3 12h9" stroke="#fbbc04" strokeWidth="2.6" /></svg>
        <Tx x={49} y={24} s={14} c="#1f1f1f" w={500}>Créer</Tx><Ico x={112} y={24} s={12} c="#444" d={D.chevD} />
      </div>
      <Tx x={24} y={232} s={13.5} c="#1f1f1f" w={500}>Mai 2026</Tx>
      <Ico x={168} y={232} s={13} c="#444" d={D.chevL} sw={2.2} /><Ico x={196} y={232} s={13} c="#444" d={D.chevR} sw={2.2} />
      {['L', 'M', 'M', 'J', 'V', 'S', 'D'].map((d, i) => <Tx key={i} x={27 + i * 27.6} y={257} s={10} c="#444">{d}</Tx>)}
      {mini.map((r, j) => r.map((d, i) => {
        const x = 30 + i * 27.6; const y = 281 + j * 24.6;
        const sel = j === 4 && i === 2; const lt = j === 4 && (i === 3 || i === 4);
        return (
          <div key={`${j}${i}`}>
            {(sel || lt) && <div style={{position: 'absolute', left: x - 12, top: y - 12, width: 24, height: 24, borderRadius: 12, background: sel ? '#0b57d0' : '#d3e3fd'}} />}
            <div style={{position: 'absolute', left: x - 12, top: y - 7, width: 24, textAlign: 'center', fontSize: 10, color: sel ? '#fff' : (j === 0 && i < 5) || (j === 5 && i > 0) ? '#777' : '#1f1f1f', fontWeight: sel ? 500 : 400}}>{d}</div>
          </div>
        );
      }))}
      <Tx x={24} y={438} s={13.5} c="#1f1f1f">Rencontrer…</Tx>
      <div style={{position: 'absolute', left: 24, top: 454, width: 181, height: 32, borderRadius: 4, background: '#f0f4f9'}}>
        <Ico x={20} y={16} s={15} c="#444" d={D.people} /><Tx x={36} y={17} s={13} c="#444">Rechercher des personnes</Tx>
      </div>
      <Tx x={24} y={516} s={13.5} c="#1f1f1f" w={500}>Mes agendas</Tx><Ico x={195} y={516} s={14} c="#444" d="M6 15l6-6 6 6" sw={2.2} />
      {cals.map(([c, t], i) => (
        <div key={i}>
          <div style={{position: 'absolute', left: 25, top: 537 + i * 26.6, width: 15, height: 15, borderRadius: 3, background: c}}>
            <svg width="15" height="15" viewBox="0 0 24 24"><path d="M5 12l4.5 4.5L19 7" stroke="#fff" strokeWidth="3.2" fill="none" /></svg>
          </div>
          <Tx x={48} y={545 + i * 26.6} s={13} c="#1f1f1f">{t}</Tx>
        </div>
      ))}
      <Tx x={24} y={687} s={13.5} c="#1f1f1f" w={500}>Autres agendas</Tx>
      <Ico x={167} y={687} s={15} c="#444" d={D.plus} /><Ico x={195} y={687} s={14} c="#444" d="M6 15l6-6 6 6" sw={2.2} />
      <div style={{position: 'absolute', left: 25, top: 709, width: 15, height: 15, borderRadius: 3, background: '#0b8043'}}>
        <svg width="15" height="15" viewBox="0 0 24 24"><path d="M5 12l4.5 4.5L19 7" stroke="#fff" strokeWidth="3.2" fill="none" /></svg>
      </div>
      <Tx x={48} y={717} s={12.5} c="#1f1f1f">Jours fériés en France</Tx>
      {/* grille */}
      {days.map((d, i) => (
        <div key={i}>
          <div style={{position: 'absolute', left: dayX(i), top: 150, width: 147, textAlign: 'center', fontSize: 10.5, color: i === 2 ? '#0b57d0' : '#444', fontWeight: 500}}>{d}</div>
          {i === 2 && <div style={{position: 'absolute', left: dayX(i) + 73.5 - 21, top: 166, width: 42, height: 42, borderRadius: 21, background: '#0b57d0'}} />}
          <div style={{position: 'absolute', left: dayX(i), top: 174, width: 147, textAlign: 'center', fontSize: 22, color: i === 2 ? '#fff' : '#1f1f1f'}}>{nums[i]}</div>
          <div style={{position: 'absolute', left: dayX(i), top: 220, width: 1, height: 640, background: '#e5e5e5'}} />
        </div>
      ))}
      <Tx x={248} y={217} s={9.5} c="#666">UTC+2</Tx>
      {Array.from({length: 14}, (_, k) => (
        <div key={k}>
          <div style={{position: 'absolute', left: 285, top: hy(7 + k), width: 1030, height: 1, background: '#ececec'}} />
          <Tx x={253} y={hy(7 + k)} s={9.5} c="#666">{`${7 + k}:00`}</Tx>
        </div>
      ))}
      {EVENTS.map(([d, a, b, t, tm, c], i) => {
        const [bg, fg, edge, line] = (CAL as any)[c];
        return (
          <div key={i} style={{position: 'absolute', left: dayX(d) + 6, top: hy(a) + 2, width: 130, height: (b - a) * 44.6 - 3, borderRadius: 4, background: bg, border: `1px solid ${line}`, borderLeft: `3px solid ${edge}`,
            padding: '3px 6px', boxSizing: 'border-box', overflow: 'hidden', color: fg, fontSize: 10.5, lineHeight: '13px'}}>
            <div style={{fontWeight: 500, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis'}}>{t}</div>
            <div>{tm}</div>
          </div>
        );
      })}
      <div style={{position: 'absolute', left: 1322, top: 140, width: 50, height: 720, background: '#fff', borderLeft: '1px solid #eee'}} />
      <Rail x={1347} y0={166} gap={52} maps noCal />
      <div style={{position: 'absolute', left: 1332, top: 373, width: 30, height: 1, background: '#dadce0'}} />
      <Ico x={1347} y={398} s={18} c="#444" d={D.plus} />
    </div>
  );
};

// ---------------- Google Drive (fenêtre 1384 x 858) ----------------
// Icônes de type de fichier Google (Docs, Sheets, Slides, PDF).
const FileIco: React.FC<{c: string; x: number; y: number; s?: number}> = ({c, x, y, s = 14}) => {
  const k = c === '#4285f4' ? 'doc' : c === '#0f9d58' ? 'sheet' : c === '#f4b400' ? 'slide' : 'pdf';
  return (
    <svg width={s} height={s} viewBox="0 0 24 24" style={{position: 'absolute', left: x, top: y}}>
      <rect x="3" y="2" width="18" height="20" rx="2.5" fill={c} />
      {k === 'doc' && <path d="M7 8h10M7 12h10M7 16h7" stroke="#fff" strokeWidth="1.8" />}
      {k === 'sheet' && <path d="M7 8h10v9H7zM7 12.5h10M12 8v9" stroke="#fff" strokeWidth="1.6" fill="none" />}
      {k === 'slide' && <rect x="7" y="9" width="10" height="7" rx="1" fill="none" stroke="#fff" strokeWidth="1.8" />}
      {k === 'pdf' && <text x="12" y="15.5" textAnchor="middle" fontSize="7" fontWeight="700" fill="#fff" fontFamily={`Arial, ${ARIAL_L}, sans-serif`}>PDF</text>}
    </svg>
  );
};
const Waves: React.FC = () => (
  <svg width="180" height="116" viewBox="0 0 180 116" style={{position: 'absolute', left: 0, top: 0}}>
    {[0, 1, 2, 3, 4, 5, 6].map((k) => <path key={k} d={`M40 ${122 - k * 3} C 90 ${108 - k * 6}, 130 ${72 - k * 5}, 185 ${28 + k * 6}`} stroke="#3fae7a" strokeOpacity={0.55 - k * 0.06} fill="none" strokeWidth="1" />)}
  </svg>
);
const Thumb: React.FC<{kind: 'deck' | 'chart' | 'road' | 'pitch' | 'white' | 'sheet' | 'prop' | 'res'; title: string; sub?: string}> = ({kind, title, sub}) => {
  const dark = kind === 'deck' || kind === 'road' || kind === 'pitch' || kind === 'res';
  const small = kind === 'chart' || kind === 'sheet';
  return (
    <div style={{position: 'absolute', inset: 0, background: dark ? 'linear-gradient(135deg,#1c2a34,#15212a 60%,#1c3530)' : '#fff', overflow: 'hidden', color: dark ? '#fff' : '#1f1f1f'}}>
      {dark && <Waves />}
      {kind === 'res' && (
        <svg width="70" height="90" viewBox="0 0 70 90" style={{position: 'absolute', right: 2, bottom: 0}}>
          <ellipse cx="38" cy="30" rx="11" ry="13" fill="#c99478" /><path d="M26 26c0-12 24-14 24 2 0-8-6-12-12-12s-12 4-12 10z" fill="#2a1d17" />
          <path d="M8 90c2-24 14-36 30-36s28 12 30 36z" fill="#1e1e22" /><path d="M31 54l7 14 7-14z" fill="#e8e3dc" />
        </svg>
      )}
      <div style={{position: 'absolute', left: 13, top: small ? 9 : kind === 'road' ? 18 : 36, fontSize: small ? 8.5 : 12.5, fontWeight: 600, lineHeight: 1.25, width: 140, whiteSpace: 'pre-line'}}>
        {title}
        {sub && <div style={{fontSize: 7.5, fontWeight: 400, marginTop: 5, opacity: 0.85}}>{sub}</div>}
      </div>
      {kind === 'chart' && (
        <>
          <div style={{position: 'absolute', left: 13, top: 44, fontSize: 7, fontWeight: 700}}>2,45 M$</div>
          <svg width="167" height="60" viewBox="0 0 167 60" style={{position: 'absolute', left: 0, bottom: 4}}>
            {[6, 10, 8, 16, 22, 27, 33, 40, 46, 54].map((h, k) => <rect key={k} x={24 + k * 13} y={58 - h} width="6" height={h} fill={k > 4 ? '#1e7e3e' : '#9fd6ad'} />)}
            <path d="M16 10v48h146" stroke="#ddd" strokeWidth="0.8" fill="none" />
          </svg>
        </>
      )}
      {kind === 'road' && (
        <svg width="167" height="40" viewBox="0 0 167 40" style={{position: 'absolute', left: 0, top: 58}}>
          {[0, 1, 2].map((r) => <path key={r} d={`M13 ${8 + r * 8}h${60 + r * 30}`} stroke="#2e4050" strokeWidth="2.5" />)}
          <path d="M13 26h141" stroke="url(#rg)" strokeWidth="3" /><defs><linearGradient id="rg"><stop offset="0" stopColor="#4f7df0" /><stop offset="0.5" stopColor="#3fae7a" /><stop offset="1" stopColor="#f0b43a" /></linearGradient></defs>
          {[28, 70, 112, 150].map((x, k) => <circle key={k} cx={x} cy="26" r="3" fill="#fff" />)}
          {['T2 2026', 'T3 2026', 'T4 2026'].map((t, k) => <text key={k} x={20 + k * 48} y="37" fontSize="5" fill="#9aa">{t}</text>)}
        </svg>
      )}
      {kind === 'sheet' && (
        <svg width="167" height="90" viewBox="0 0 167 90" style={{position: 'absolute', left: 0, top: 26}}>
          {Array.from({length: 9}, (_, k) => <path key={k} d={`M10 ${k * 9 + 4}h147`} stroke="#e6e6e6" strokeWidth="0.8" />)}
          {Array.from({length: 8}, (_, k) => [0, 1, 2, 3].map((c) => <rect key={`${k}${c}`} x={12 + c * 38} y={k * 9 + 7} width={[26, 18, 14, 10][c]} height="2.4" fill={k === 0 ? '#888' : '#c9c9c9'} />))}
        </svg>
      )}
      {kind === 'white' && <div style={{position: 'absolute', left: 0, right: 0, bottom: 0, height: 54, background: 'linear-gradient(120deg,#2b2f33 45%,#3d7550 68%,#262a2d 85%)'}} />}
      {kind === 'prop' && (
        <svg width="167" height="117" viewBox="0 0 167 117" style={{position: 'absolute', left: 0, top: 0}}>
          <path d="M40 117c10-40 50-52 80-40 20 8 34 24 47 40z" fill="#4d6b31" /><path d="M110 117c10-50 30-90 57-100v100z" fill="#a9c07c" /><path d="M70 117c20-26 60-30 97-20v20z" fill="#2c4424" />
        </svg>
      )}
    </div>
  );
};
export const Drive: React.FC = () => {
  const nav: [string, string, number][] = [[D.home, 'Accueil', 227], [D.folder, 'Mon Drive', 256], [D.grid, 'Ordinateurs', 285], [D.people, 'Partagés avec moi', 329], [D.clock, 'Récents', 358], [D.star, 'Suivis', 387], [D.spam, 'Spam', 430], [D.trash, 'Corbeille', 459], [D.cloud, 'Stockage', 488]];
  const folders = ['01_Opérations', '02_Finance', 'Points investisseurs', '03_Marketing', '04_Produit', 'Docs équipe', '05_Juridique & contrats', '06_RH & recrutement', 'Archives'];
  const files: [string, string, any, string, string?][] = [
    ['#4285f4', 'Point investisseurs T2', 'deck', 'T2\nPoint investisseurs', 'Mai 2026'], ['#0f9d58', 'Tableau de bord CA', 'chart', 'Tableau de bord CA', 'Mai 2026'],
    ['#f4b400', 'Roadmap produit', 'road', 'Roadmap produit', '2026'], ['#f4b400', 'NovaTech : pitch deck', 'pitch', 'NovaTech\nPitch deck', 'Mai 2026'],
    ['#4285f4', 'Stratégie marketing', 'white', 'Stratégie marketing', '2026'], ['#0f9d58', 'OKR équipe : T2', 'sheet', 'OKR équipe : T2'],
    ['#ea4335', 'Proposition partenariat', 'prop', 'Proposition de\npartenariat'], ['#4285f4', 'Étude clients', 'res', 'Synthèse\nétude clients', 'Mai 2026'],
  ];
  const det: [string, string][] = [['Type', 'Google Docs'], ['Taille', '3,2 Mo'], ['Espace utilisé', '3,2 Mo'], ['Emplacement', 'Mon Drive'], ['Propriétaire', 'moi'], ['Modifié', '28 mai 2026 par moi'], ['Ouvert', '28 mai 2026 par moi'], ['Créé', '20 mai 2026']];
  return (
    <div style={{position: 'absolute', inset: 0, background: '#fff', fontFamily: ROBOTO, overflow: 'hidden'}}>
      <Chrome W={1384} tab="Drive - NovaTech" icon={<DriveLogo size={14} />} url={['drive.google.com', '/drive/u/0/my-drive']} />
      <div style={{position: 'absolute', left: 0, top: 76, width: 1384, height: 790, background: '#f8fafd'}} />
      <DriveLogo size={32} style={{position: 'absolute', left: 21, top: 97}} />
      <Tx x={62} y={112} s={21} c="#1f1f1f">Drive</Tx>
      <div style={{position: 'absolute', left: 222, top: 93, width: 654, height: 39, borderRadius: 20, background: '#e9eef6'}}>
        <Ico x={23} y={19.5} s={17} c="#444" d={D.search} /><Tx x={47} y={20} s={14.5} c="#444">Rechercher dans Drive</Tx>
      </div>
      <Ico x={1130} y={112} s={20} c="#444" d={D.help} /><Ico x={1170} y={112} s={20} c="#444" d={D.gear} /><Ico x={1220} y={112} s={20} c="#444" d={D.apps} sw={3.2} />
      <Tx x={1262} y={112} s={14.5} c="#1f1f1f">NovaTech</Tx><Avatar x={1350} y={111} s={32} />
      <div style={{position: 'absolute', left: 14, top: 150, width: 93, height: 41, borderRadius: 12, background: '#fff', boxShadow: '0 1px 3px rgba(0,0,0,0.25)'}}>
        <Ico x={24} y={20.5} s={18} c="#1f1f1f" d={D.plus} /><Tx x={46} y={21} s={14} c="#1f1f1f" w={500}>Nouveau</Tx>
      </div>
      {nav.map(([d, t, y], i) => (
        <div key={i}>
          {i === 1 && <div style={{position: 'absolute', left: 16, top: y - 14, width: 182, height: 28, borderRadius: 14, background: '#c2e7ff'}} />}
          <Ico x={38} y={y} s={15} c="#1f1f1f" d={d} />
          <Tx x={60} y={y} s={13} c={i === 1 ? '#001d35' : '#1f1f1f'} w={i === 1 ? 500 : 400}>{t}</Tx>
        </div>
      ))}
      <div style={{position: 'absolute', left: 26, top: 512, width: 145, height: 3, borderRadius: 2, background: '#e1e3e1'}}><div style={{width: 38, height: 3, background: '#0b57d0'}} /></div>
      <Tx x={26} y={530} s={12} c="#444">45,6 Go utilisés sur 200 Go</Tx>
      <div style={{position: 'absolute', left: 26, top: 549, width: 134, height: 30, borderRadius: 15, border: '1px solid #747775', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 12.5, color: '#0b57d0', fontWeight: 500}}>Plus d’espace</div>
      <div style={{position: 'absolute', left: 218, top: 140, width: 810, height: 718, borderRadius: 16, background: '#fff'}} />
      <Tx x={236} y={170} s={21} c="#1f1f1f">Mon Drive <span style={{fontSize: 14}}>▾</span></Tx>
      {[['Type', 236, 74], ['Personnes', 320, 102], ['Modifié', 413, 97]].map(([t, x, w]: any, i) => (
        <div key={i} style={{position: 'absolute', left: x, top: 200, width: w, height: 28, borderRadius: 8, border: '1px solid #747775', fontSize: 12.5, color: '#1f1f1f', fontWeight: 500, display: 'flex', alignItems: 'center', gap: 8, paddingLeft: 13, boxSizing: 'border-box'}}>{t} ▾</div>
      ))}
      <div style={{position: 'absolute', left: 850, top: 200, width: 103, height: 28, borderRadius: 14, border: '1px solid #747775', overflow: 'hidden'}}>
        <div style={{position: 'absolute', left: 51, top: 0, width: 52, height: 28, background: '#c2e7ff'}} />
        <Ico x={26} y={14} s={15} c="#444" d={D.list} /><Ico x={77} y={14} s={14} c="#0b57d0" d={D.grid} />
      </div>
      <Ico x={977} y={214} s={18} c="#444" d={D.info} />
      <Tx x={236} y={257} s={12.5} c="#1f1f1f" w={500}>Dossiers</Tx>
      <Tx x={928} y={257} s={12.5} c="#1f1f1f" w={500}>Nom</Tx><Ico x={990} y={256} s={14} c="#444" d="M12 19V5M6 11l6-6 6 6" />
      {folders.map((t, i) => {
        const x = 236 + (i % 3) * 258; const y = 274 + Math.floor(i / 3) * 53;
        return (
          <div key={i} style={{position: 'absolute', left: x, top: y, width: 240, height: 42, borderRadius: 10, background: '#f0f4f9'}}>
            <svg width="19" height="15" viewBox="0 0 24 19" style={{position: 'absolute', left: 12, top: 13}}><path d="M0 2a2 2 0 0 1 2-2h7l2 2.5h11a2 2 0 0 1 2 2V17a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2z" fill="#444746" />{i !== 3 && i !== 6 && <g fill="#fff"><circle cx="14" cy="9.5" r="2" /><path d="M10.5 15.5a3.5 3.5 0 0 1 7 0z" /></g>}</svg>
            <Tx x={44} y={21} s={12.5} c="#1f1f1f" w={500}>{t}</Tx>
            <Ico x={222} y={21} s={15} c="#444" d={D.kebab} sw={2.6} />
          </div>
        );
      })}
      <Tx x={236} y={446} s={12.5} c="#1f1f1f" w={500}>Fichiers</Tx>
      {files.map(([c, t, k, big, sub], i) => {
        const x = 236 + (i % 4) * 193; const y = 463 + Math.floor(i / 4) * 180;
        return (
          <div key={i} style={{position: 'absolute', left: x, top: y, width: 181, height: 160, borderRadius: 10, background: i === 0 ? '#c2e7ff' : '#f0f4f9'}}>
            <FileIco c={c} x={11} y={9} s={15} />
            <Tx x={36} y={17} s={11} c="#1f1f1f" w={500}>{t}</Tx>
            <Ico x={165} y={17} s={14} c="#444" d={D.kebab} sw={2.6} />
            <div style={{position: 'absolute', left: 7, top: 36, width: 167, height: 117, borderRadius: 4, overflow: 'hidden'}}><Thumb kind={k} title={big} sub={sub} /></div>
          </div>
        );
      })}
      {/* panneau détails */}
      <div style={{position: 'absolute', left: 1043, top: 140, width: 290, height: 718, borderRadius: 16, background: '#fff'}}>
        <FileIco c="#4285f4" x={19} y={20} s={20} />
        <Tx x={54} y={30} s={14.5} c="#1f1f1f" w={500}>Point investisseurs T2</Tx>
        <Ico x={254} y={30} s={17} c="#444" d={D.x} />
        <Tx x={49} y={79} s={12.5} c="#0b57d0" w={500}>Détails</Tx><Tx x={183} y={79} s={12.5} c="#444" w={500}>Activité</Tx>
        <div style={{position: 'absolute', left: 0, top: 97, width: 138, height: 3, background: '#0b57d0', borderRadius: 2}} />
        <div style={{position: 'absolute', left: 0, top: 99, width: 280, height: 1, background: '#e3e3e3'}} />
        <div style={{position: 'absolute', left: 13, top: 116, width: 252, height: 153, borderRadius: 4, overflow: 'hidden'}}><Thumb kind="deck" title={'T2\nPoint investisseurs'} sub="Mai 2026" /></div>
        <Tx x={15} y={296} s={14} c="#1f1f1f" w={500}>Qui a accès</Tx>
        {[0, 1, 2, 3, 4].map((k) => <Avatar key={k} x={25 + k * 28} y={324} s={23} />)}
        <Tx x={157} y={324} s={10} c="#444">+3</Tx>
        <Tx x={13} y={356} s={12} c="#0b57d0" w={500}>Gérer l’accès</Tx>
        <Tx x={13} y={398} s={14} c="#1f1f1f" w={500}>Détails du fichier</Tx>
        {det.map(([a, b], k) => (
          <div key={k}><Tx x={13} y={425 + k * 27.3} s={10.5} c="#444">{a}</Tx><Tx x={96} y={425 + k * 27.3} s={10.5} c="#1f1f1f">{b}</Tx></div>
        ))}
      </div>
      <div style={{position: 'absolute', left: 1351, top: 157, width: 16, height: 16}}><CalLogo size={16} /></div>
      <div style={{position: 'absolute', left: 1352, top: 204, width: 14, height: 16, borderRadius: 3, background: '#fbbc04'}} />
      <div style={{position: 'absolute', left: 1351, top: 251, width: 16, height: 16, borderRadius: 8, border: '2.5px solid #4285f4', boxSizing: 'border-box'}} />
      <div style={{position: 'absolute', left: 1351, top: 297, width: 16, height: 16, borderRadius: 8, background: '#4285f4'}} />
      <Ico x={1359} y={375} s={17} c="#444" d={D.plus} />
    </div>
  );
};

// ---------------- Slack (fenêtre 1391 x 863) ----------------
const Av: React.FC<{x: number; y: number; s: number; t: string; c?: string}> = ({x, y, s, t, c = '#7a3e8e'}) => (
  <div style={{position: 'absolute', left: x, top: y, width: s, height: s, borderRadius: s * 0.22, background: c, color: '#fff', fontSize: s * 0.44, fontWeight: 700,
    display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: SANS}}>{t}</div>
);
const React1: React.FC<{x: number; y: number; items: [string, number][]}> = ({x, y, items}) => (
  <div style={{position: 'absolute', left: x, top: y - 13, display: 'flex', gap: 6}}>
    {items.map(([e, n], i) => (
      <div key={i} style={{height: 25, padding: '0 8px', borderRadius: 13, background: '#2a2c30', display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, color: '#d1d2d3'}}>{e} {n}</div>
    ))}
    <div style={{width: 30, height: 25, borderRadius: 13, background: '#2a2c30', position: 'relative'}}><Ico x={15} y={12.5} s={14} c="#aaa" d={D.smile} /></div>
  </div>
);
export const Slack: React.FC = () => {
  const ch: [string, boolean, number?][] = [['annonces', true, 2], ['fondateurs', false], ['général', false], ['produit', false], ['marketing', false], ['ventes', false], ['technique', false], ['finance', false], ['recrutement', true]];
  const dms: [string, string, string][] = [['AJ', 'Alex Johnson (toi)', '#7a3e8e'], ['SC', 'Sara Chen', '#7a3e8e'], ['ML', 'Michael Lee', '#7a3e8e'], ['ER', 'Emily Rogers', '#7a3e8e'], ['DP', 'David Park', '#7a3e8e']];
  const txt = '#d1d2d3';
  return (
    <div style={{position: 'absolute', inset: 0, background: '#1a1d21', fontFamily: SANS, overflow: 'hidden'}}>
      <div style={{position: 'absolute', left: 0, top: 0, width: 1391, height: 43, background: '#2b1f30'}} />
      {['#ff5f57', '#febc2e', '#28c840'].map((c, i) => <div key={i} style={{position: 'absolute', left: 16 + i * 21, top: 15, width: 13, height: 13, borderRadius: 7, background: c}} />)}
      <Ico x={360} y={21} s={18} c="#c9c0cc" d={D.back} /><Ico x={393} y={21} s={18} c="#8e8492" d={D.fwd} /><Ico x={429} y={21} s={19} c="#c9c0cc" d={D.clock} />
      <div style={{position: 'absolute', left: 457, top: 7, width: 521, height: 30, borderRadius: 7, background: '#4a3f4f'}}>
        <Ico x={17} y={15} s={15} c="#e0d8e3" d={D.search} /><Tx x={33} y={15.5} s={13} c="#e0d8e3">Rechercher dans NovaTech</Tx>
      </div>
      <Ico x={1309} y={21} s={19} c="#c9c0cc" d={D.help} />
      <Av x={1338} y={4} s={33} t="AJ" c="#7a3e8e" />
      <div style={{position: 'absolute', left: 0, top: 43, width: 67, height: 830, background: '#1e1621'}} />
      <Av x={17} y={57} s={35} t="N" c="#5b2a73" />
      {[[D.home, 'Accueil', 132], [D.msg, 'Messages', 205], [D.bell, 'Activité', 276], [D.dots, 'Plus', 347]].map(([d, t, y]: any, i) => (
        <div key={i}>
          {i === 0 && <div style={{position: 'absolute', left: 16, top: y - 18, width: 36, height: 36, borderRadius: 9, background: '#4a3a52'}} />}
          <Ico x={34} y={y} s={19} c="#f2eef3" d={d} sw={i === 3 ? 3 : 1.8} />
          <div style={{position: 'absolute', left: 0, top: y + 23, width: 67, textAlign: 'center', fontSize: 11, color: '#f2eef3'}}>{t}</div>
        </div>
      ))}
      <div style={{position: 'absolute', left: 67, top: 43, width: 224, height: 830, background: '#1b1420', borderRight: '1px solid #2e2733'}} />
      <Tx x={84} y={73} s={18} c="#f2eef3" w={700}>NovaTech <span style={{fontSize: 12}}>⌄</span></Tx>
      <div style={{position: 'absolute', left: 236, top: 53, width: 40, height: 40, borderRadius: 20, background: '#5c3a6b'}}><Ico x={20} y={20} s={18} c="#fff" d={D.edit} /></div>
      {[[D.list, 'Non lus'], [D.threads, 'Fils'], [D.headph, 'Huddles'], [D.send, 'Brouillons et envois']].map(([d, t]: any, i) => (
        <div key={i}><Ico x={91} y={121 + i * 29} s={15} c="#b8adbd" d={d} /><Tx x={109} y={121 + i * 29} s={14.5} c="#c8bfcc">{t}</Tx></div>
      ))}
      <Tx x={88} y={252} s={14.5} c="#c8bfcc">▾ &nbsp;Canaux</Tx>
      {ch.map(([t, b, n], i) => {
        const y = 282 + i * 29;
        return (
          <div key={i}>
            {i === 1 && <div style={{position: 'absolute', left: 74, top: y - 14, width: 210, height: 28, borderRadius: 6, background: '#5a2d6c'}} />}
            <Tx x={88} y={y} s={14.5} c={b || i === 1 ? '#fff' : '#b8adbd'} w={b ? 700 : 400}># &nbsp; {t}</Tx>
            {n && <div style={{position: 'absolute', left: 254, top: y - 9, width: 18, height: 18, borderRadius: 9, background: '#cd2553', color: '#fff', fontSize: 11, fontWeight: 700, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>{n}</div>}
          </div>
        );
      })}
      <Tx x={88} y={542} s={14.5} c="#b8adbd">+ &nbsp; Ajouter des canaux</Tx>
      <Tx x={88} y={586} s={14.5} c="#c8bfcc">▾ &nbsp;Messages directs</Tx>
      {dms.map(([a, t], i) => (
        <div key={i}><Av x={82} y={606 + i * 28.6} s={19} t={a} /><Tx x={109} y={616 + i * 28.6} s={14.5} c="#b8adbd">{t}</Tx></div>
      ))}
      <Tx x={88} y={759} s={14.5} c="#b8adbd">+ &nbsp; Ajouter des collègues</Tx>
      {/* canal */}
      <Tx x={311} y={71} s={18} c="#fff" w={700}># fondateurs <span style={{fontSize: 12}}>⌄</span></Tx>
      <Tx x={311} y={99} s={12.5} c="#aaa">Actualités de l’entreprise et échanges entre fondateurs</Tx>
      <div style={{position: 'absolute', left: 796, top: 60, width: 72, height: 30, borderRadius: 6, border: '1px solid #3a3b3f'}}><Ico x={20} y={15} s={15} c="#ccc" d={D.people} /><Tx x={40} y={15} s={12.5} c="#ddd">14</Tx></div>
      <Ico x={903} y={78} s={16} c="#ccc" d={D.headph} /><Ico x={975} y={78} s={16} c="#ccc" d={D.file} /><Ico x={1010} y={78} s={16} c="#ccc" d={D.kebab} sw={2.6} />
      <Ico x={317} y={138} s={13} c="#bbb" d={D.plus} /><Tx x={329} y={138} s={12.5} c="#bbb">Ajouter un favori</Tx>
      <div style={{position: 'absolute', left: 290, top: 158, width: 755, height: 1, background: '#2e3034'}} />
      <div style={{position: 'absolute', left: 627, top: 168, width: 90, height: 25, borderRadius: 13, border: '1px solid #3a3b3f', background: '#1a1d21', fontSize: 12, color: '#ddd', fontWeight: 600, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>Aujourd’hui ⌄</div>
      <Av x={308} y={201} s={36} t="AJ" />
      <Tx x={354} y={209} s={14.5} c="#fff" w={700}>Alex Johnson <span style={{fontSize: 12, color: '#aaa', fontWeight: 400}}>9:02</span></Tx>
      {['Bonjour l’équipe ! ☀️', 'Voici l’ordre du jour de notre point fondateurs :', '•  Point T2 et indicateurs clés', '•  Roadmap produit', '•  Point levée de fonds', '•  Plan de recrutement'].map((t, i) => (
        <Tx key={i} x={i > 1 ? 363 : 354} y={232 + i * 23} s={14.5} c={txt}>{t}</Tx>
      ))}
      <React1 x={354} y={376} items={[['✅', 5], ['🙌', 3], ['🔥', 2]]} />
      <Av x={308} y={405} s={36} t="SC" />
      <Tx x={354} y={413} s={14.5} c="#fff" w={700}>Sara Chen <span style={{fontSize: 12, color: '#aaa', fontWeight: 400}}>9:15</span></Tx>
      <Tx x={354} y={436} s={14.5} c={txt}>Parfait ! J’ajoute le tableau de bord T2 dans un instant.</Tx>
      <React1 x={354} y={465} items={[['👍', 2]]} />
      <Av x={308} y={495} s={36} t="ML" />
      <Tx x={354} y={503} s={14.5} c="#fff" w={700}>Michael Lee <span style={{fontSize: 12, color: '#aaa', fontWeight: 400}}>9:16</span></Tx>
      <Tx x={354} y={526} s={14.5} c={txt}>J’ai finalisé la roadmap produit. Regardez le fil ci-dessous 👇</Tx>
      {['SC', 'AJ', 'ML'].map((a, i) => <Av key={i} x={354 + i * 26} y={546} s={20} t={a} />)}
      <Tx x={438} y={556} s={12.5} c="#1d9bd1" w={600}>5 réponses <span style={{color: '#aaa', fontWeight: 400}}>&nbsp; Dernière réponse aujourd’hui à 10:15</span></Tx>
      <Av x={308} y={593} s={36} t="ER" />
      <Tx x={354} y={601} s={14.5} c="#fff" w={700}>Emily Rogers <span style={{fontSize: 12, color: '#aaa', fontWeight: 400}}>10:15</span></Tx>
      <Tx x={354} y={624} s={14.5} c={txt}><span style={{color: '#1d9bd1'}}>@Alex Johnson</span> voici les derniers chiffres de la levée.</Tx>
      <div style={{position: 'absolute', left: 355, top: 644, width: 363, height: 62, borderRadius: 8, border: '1px solid #3a3b3f'}}>
        <div style={{position: 'absolute', left: 16, top: 13, width: 28, height: 36, borderRadius: 3, background: '#1e8e3e'}}><div style={{position: 'absolute', left: 6, top: 14, width: 16, height: 12, border: '2px solid #fff', boxSizing: 'border-box'}} /></div>
        <Tx x={60} y={20} s={14.5} c="#fff" w={600}>Point levée de fonds : mai 2026</Tx>
        <Tx x={60} y={42} s={12} c="#aaa">Google Sheets</Tx>
        <Ico x={340} y={31} s={14} c="#ccc" d={D.chevD} />
      </div>
      <React1 x={354} y={728} items={[['👀', 3]]} />
      <div style={{position: 'absolute', left: 308, top: 757, width: 719, height: 86, borderRadius: 8, border: '1px solid #45474b'}}>
        <Tx x={13} y={22} s={14} c="#999">Écrire dans #fondateurs</Tx>
        <Tx x={17} y={63} s={14} c="#bbb" w={700}>B</Tx><Tx x={42} y={63} s={14} c="#bbb" w={700} style={{fontStyle: 'italic'}}>I</Tx><Tx x={62} y={63} s={14} c="#bbb" w={700} style={{textDecoration: 'line-through'}}>S</Tx>
        {[[D.link, 93], [D.list, 123], [D.list, 150], [D.code, 180]].map(([d, x]: any, i) => <Ico key={i} x={x} y={63} s={15} c="#bbb" d={d} />)}
        <Tx x={505} y={63} s={14} c="#999">Aa</Tx>
        {[[D.smile, 552], [D.at, 580], [D.video, 607], [D.mic, 634], [D.send, 668]].map(([d, x]: any, i) => <Ico key={i} x={x} y={63} s={15} c="#999" d={d} />)}
      </div>
      {/* fil */}
      <div style={{position: 'absolute', left: 1045, top: 43, width: 1, height: 830, background: '#2e3034'}} />
      <Tx x={1065} y={71} s={18} c="#fff" w={700}>Fil</Tx>
      <Tx x={1065} y={96} s={13} c="#aaa">Roadmap produit</Tx>
      <Ico x={1345} y={82} s={17} c="#ccc" d={D.x} />
      {[
        ['ML', 'Michael Lee', '9:16', ['J’ai finalisé la roadmap produit.', 'Regardez le fil ci-dessous 👇'], null, 142],
        ['SC', 'Sara Chen', '9:18', ['Top ! J’ai hâte du lancement', 'des insights IA. Un blocage', 'sur le calendrier T3 ?'], ['👍', 2], 277],
        ['ML', 'Michael Lee', '9:20', ['Aucun blocage pour l’instant.', 'La technique est dans les temps.'], ['✅', 1], 421],
        ['AJ', 'Alex Johnson', '9:22', ['Super. On regarde le détail', 'pendant notre point.'], ['🙌', 1], 541],
        ['ER', 'Emily Rogers', '10:15', ['Je mets à jour le doc de roadmap', 'avec ces retours.'], ['👍', 1], 661],
      ].map(([a, n, tm, lines, r, y]: any, i) => (
        <div key={i}>
          <Av x={1064} y={y - 8} s={36} t={a} />
          <Tx x={1109} y={y} s={14.5} c="#fff" w={700}>{n} <span style={{fontSize: 12, color: '#aaa', fontWeight: 400}}>{tm}</span></Tx>
          {lines.map((l: string, k: number) => <Tx key={k} x={1109} y={y + 23 + k * 23} s={14.5} c={txt}>{l}</Tx>)}
          {r && <React1 x={1109} y={y + 23 + lines.length * 23 + 8} items={[r]} />}
          {i === 0 && <><Tx x={1065} y={237} s={12.5} c="#aaa">5 réponses</Tx><div style={{position: 'absolute', left: 1140, top: 237, width: 225, height: 1, background: '#2e3034'}} /></>}
        </div>
      ))}
      <div style={{position: 'absolute', left: 1063, top: 760, width: 295, height: 83, borderRadius: 8, border: '1px solid #45474b'}}>
        <Tx x={11} y={19} s={14} c="#999">Répondre…</Tx>
        <Tx x={11} y={60} s={14} c="#999">Aa</Tx>
        {[[D.smile, 49], [D.at, 72], [D.video, 95], [D.mic, 118]].map(([d, x]: any, i) => <Ico key={i} x={x} y={60} s={14} c="#999" d={d} />)}
      </div>
    </div>
  );
};

// ---------------- Notion (fenêtre 1398 x 873) ----------------
export const Notion: React.FC = () => {
  const ink = '#37352f'; const gray = '#91918e';
  const side: [string, string, number, boolean?][] = [
    [D.search, 'Rechercher', 107], [D.inbox, 'Boîte de réception', 134], [D.gear, 'Paramètres et membres', 161],
    ['', 'Espaces d’équipe', 206, true], ['home', 'Général', 233], ['🏠', 'Accueil entreprise', 260], ['🏛', 'Mission, vision, valeurs', 286], ['🎯', 'OKR entreprise', 312], ['📣', 'Annonces', 339],
    ['', '▸ Projets', 371, true], ['🟧', 'Roadmap produit', 397], ['🎨', 'Campagne marketing', 423], ['🌐', 'Refonte du site', 449], ['🤖', 'Initiative IA', 476],
    ['', 'Docs', 510, true], [D.doc, 'Notes de réunion', 536], [D.doc, 'Playbook stratégie', 563], [D.doc, 'Charte de marque', 589], [D.doc, 'Procédures', 616],
    ['', 'Bases de données', 651, true], [D.grid, 'Projets', 677], [D.check, 'Tâches', 703], [D.grid, 'CRM', 730], [D.cal, 'Calendrier éditorial', 756], [D.trash, 'Corbeille', 797],
  ];
  const pill = (t: string, c: string, bg: string) => <span style={{padding: '1px 5px', borderRadius: 3, background: bg, color: c, fontSize: 9.5}}>{t}</span>;
  const cards: [string, string, [string, React.ReactNode][]][] = [
    ['target', 'OKR', [['OKR entreprise T2 2026', pill('En bonne voie', '#448361', '#edf3ec')], ['OKR produit', pill('En bonne voie', '#448361', '#edf3ec')], ['OKR marketing', pill('À risque', '#d9730d', '#fbecdd')], ['OKR ventes', pill('En bonne voie', '#448361', '#edf3ec')]]],
    ['folder', 'Projets', [['Roadmap produit', pill('En cours', '#337ea9', '#e7f3f8')], ['Initiative IA', pill('En cours', '#337ea9', '#e7f3f8')], ['Refonte du site', pill('Planifié', '#9065b0', '#f4f0f7')], ['Campagne marketing', pill('En cours', '#337ea9', '#e7f3f8')]]],
    ['check', 'Tâches', [['Relire le PRD', <span style={{fontSize: 9.5}}><b>AJ</b> &nbsp;<span style={{color: '#e03e3e'}}>Aujourd’hui</span></span>], ['Landing page', <span style={{fontSize: 9.5}}><b>SC</b> &nbsp;Demain</span>], ['Deck investisseurs', <span style={{fontSize: 9.5}}><b>ML</b> &nbsp;30 mai</span>], ['Étude utilisateurs', <span style={{fontSize: 9.5}}><b>ER</b> &nbsp;30 mai</span>]]],
  ];
  const docs: [string, string, string, string][] = [['Point investisseurs T2', '28 mai 2026', 'AJ', 'Alex Johnson'], ['Spécifications produit', '27 mai 2026', 'SC', 'Sara Chen'], ['Stratégie marketing T2', '26 mai 2026', 'ER', 'Emily Rogers'], ['Brief initiative IA', '25 mai 2026', 'ML', 'Michael Lee'], ['Charte de marque v2', '24 mai 2026', 'DP', 'David Park']];
  const people: [string, string, string, string][] = [['AJ', 'Alex Johnson', 'CEO', '#9065b0'], ['SC', 'Sara Chen', 'Responsable produit', '#9065b0'], ['ML', 'Michael Lee', 'CTO', '#9065b0'], ['ER', 'Emily Rogers', 'Responsable marketing', '#d44c47'], ['DP', 'David Park', 'Responsable design', '#dfab01']];
  return (
    <div style={{position: 'absolute', inset: 0, background: '#fff', fontFamily: SANS, overflow: 'hidden', color: ink}}>
      <div style={{position: 'absolute', left: 0, top: 0, width: 1398, height: 42, background: '#f7f7f5'}} />
      {['#ff5f57', '#febc2e', '#28c840'].map((c, i) => <div key={i} style={{position: 'absolute', left: 16 + i * 21, top: 15, width: 13, height: 13, borderRadius: 7, background: c}} />)}
      <NotionLogo size={15} style={{position: 'absolute', left: 102, top: 14}} />
      <Tx x={127} y={21} s={13.5} c={ink} w={500}>NovaTech HQ ⌄</Tx><Ico x={241} y={21} s={12} c={gray} d={D.x} /><Ico x={284} y={21} s={16} c={gray} d={D.plus} />
      <div style={{position: 'absolute', left: 0, top: 42, width: 229, height: 840, background: '#f8f8f7'}} />
      <div style={{position: 'absolute', left: 22, top: 59, width: 18, height: 18, borderRadius: 4, background: '#8b5cf6', color: '#fff', fontSize: 11, fontWeight: 700, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>N</div>
      <Tx x={50} y={68} s={13} c={ink} w={600}>NovaTech HQ ⌄</Tx>
      {side.map(([ic, t, y, head], i) => (
        <div key={i}>
          {t === 'Général' && <div style={{position: 'absolute', left: 8, top: y - 12, width: 213, height: 24, borderRadius: 5, background: '#efefed'}} />}
          {head ? <Tx x={22} y={y} s={11} c={gray} w={500}>{t}</Tx> : (
            <>
              {ic === 'home' ? <div style={{position: 'absolute', left: 23, top: y - 8, width: 16, height: 16, borderRadius: 4, background: '#f5a623', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
                <svg width="11" height="11" viewBox="0 0 24 24" fill="#fff"><path d="M4 11l8-7 8 7v9h-5v-6H9v6H4z" /></svg></div>
                : ic.startsWith('M') ? <Ico x={31} y={y} s={14} c="#8f8e8a" d={ic} /> : <Tx x={30} y={y} s={11.5} c={ink}>{ic}</Tx>}
              <Tx x={i >= 5 && i <= 8 || i >= 10 && i <= 13 ? 53 : 48} y={y} s={12} c={ink} w={t === 'Général' ? 600 : 400}>{t}</Tx>
            </>
          )}
          {t === 'Boîte de réception' && <div style={{position: 'absolute', left: 195, top: y - 7, width: 15, height: 15, borderRadius: 8, background: '#e03e3e', color: '#fff', fontSize: 9.5, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>3</div>}
        </div>
      ))}
      <Tx x={1085} y={65} s={12.5} c={gray}>Modifié à l’instant</Tx>
      <Tx x={1188} y={65} s={12.5} c={ink} w={500}>Partager</Tx>
      <Ico x={1256} y={65} s={16} c="#5f5e5b" d={D.msg} /><Ico x={1295} y={65} s={16} c="#5f5e5b" d={D.clock} /><Ico x={1333} y={65} s={16} c="#5f5e5b" d={D.star} /><Ico x={1372} y={65} s={16} c="#5f5e5b" d={D.dots} sw={3} />
      <div style={{position: 'absolute', left: 280, top: 116, fontSize: 52, lineHeight: '60px'}}>🏠</div>
      <Tx x={360} y={151} s={28} c={ink} w={700}>Accueil entreprise</Tx>
      <div style={{position: 'absolute', left: 274, top: 188, width: 792, height: 74, borderRadius: 4, background: '#f7f7f5'}}>
        <Tx x={14} y={24} s={15} c={ink}>👋</Tx><Tx x={42} y={24} s={13.5} c={ink} w={600}>Bienvenue chez NovaTech !</Tx>
        <Tx x={42} y={50} s={12} c={ink}>Notre espace central pour la stratégie, les projets et les nouvelles de l’entreprise.</Tx>
      </div>
      <Tx x={274} y={291} s={14.5} c={ink} w={600}>Actions rapides</Tx>
      {[[D.check, 'Nouvelle tâche', 274, 126], [D.folder, 'Nouveau projet', 418, 144], [D.doc, 'Nouveau doc', 581, 128], [D.cal, 'Nouvelle réunion', 726, 152], [D.target, 'Nouvel OKR', 895, 115]].map(([ic, t, x, w]: any, i) => (
        <div key={i} style={{position: 'absolute', left: x, top: 312, width: w, height: 32, borderRadius: 5, border: '1px solid #e9e9e7', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 7, fontSize: 11.5, color: ink}}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#37352f" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d={ic} /></svg>{t}
        </div>
      ))}
      <Tx x={274} y={383} s={14.5} c={ink} w={600}>Tableau de bord équipe</Tx>
      {cards.map(([ic, t, rows], i) => {
        const x = [274, 536, 797][i]; const w = [246, 245, 259][i];
        return (
          <div key={i} style={{position: 'absolute', left: x, top: 405, width: w, height: 202, borderRadius: 5, border: '1px solid #e9e9e7'}}>
            {ic === 'target' ? <Tx x={12} y={21} s={11.5} c={ink}>🎯</Tx> : <Ico x={19} y={21} s={13} c={ink} d={(D as any)[ic]} />}<Tx x={32} y={21} s={11.5} c={ink} w={600}>{t}</Tx><Ico x={w - 14} y={21} s={11} c={gray} d={D.chevR} />
            {rows.map(([a, b], k) => (
              <div key={k}><Tx x={12} y={51 + k * 29.6} s={11} c={ink}>{a}</Tx><div style={{position: 'absolute', right: 12, top: 44 + k * 29.6}}>{b}</div></div>
            ))}
            <div style={{position: 'absolute', left: 10, top: 168, padding: '2px 6px', borderRadius: 4, border: '1px solid #e9e9e7', fontSize: 10.5, color: ink}}>➔ Tout voir</div>
          </div>
        );
      })}
      <Ico x={283} y={638} s={11} c={gray} d={D.list} /><Tx x={292} y={638} s={11} c={gray}>Docs récents</Tx><Tx x={614} y={638} s={11} c={gray}>Modifié le ⌄</Tx><Tx x={763} y={638} s={11} c={gray}>Modifié par</Tx>
      {docs.map(([t, d, a, n], i) => (
        <div key={i}>
          <div style={{position: 'absolute', left: 274, top: 654 + i * 32, width: 792, height: 1, background: '#efefed'}} />
          <Ico x={286} y={670 + i * 32} s={13} c="#8a8986" d={D.doc} />
          <Tx x={305} y={670 + i * 32} s={11.5} c={ink} w={500}>{t}</Tx><Tx x={614} y={670 + i * 32} s={11.5} c={ink}>{d}</Tx>
          <Tx x={766} y={670 + i * 32} s={11} c={ink} w={700}>{a}</Tx><Tx x={801} y={670 + i * 32} s={11.5} c={ink}>{n}</Tx>
        </div>
      ))}
      <Ico x={1113} y={150} s={14} c="#8f8e8a" d={D.cal} /><Tx x={1127} y={150} s={14} c={ink} w={600}>Aujourd’hui</Tx>
      <div style={{position: 'absolute', left: 1105, top: 168, width: 273, height: 153, borderRadius: 5, border: '1px solid #efefed'}}>
        {[['Point d’équipe', '9:00 - 9:30'], ['Synchro produit', '10:00 - 11:00'], ['Revue marketing', '14:00 - 15:00']].map(([a, b], k) => (
          <div key={k}><Tx x={12} y={17 + k * 50.5} s={11} c={ink} w={500}>{a}</Tx><Tx x={12} y={34 + k * 50.5} s={10.5} c="#6b6a67">{b}</Tx></div>
        ))}
      </div>
      <Tx x={1110} y={342} s={11} c={ink}>▸ Voir l’agenda</Tx>
      <Tx x={1105} y={396} s={13} c={ink}>📣</Tx><Tx x={1127} y={396} s={14} c={ink} w={600}>Annonces</Tx>
      <div style={{position: 'absolute', left: 1105, top: 416, width: 273, height: 107, borderRadius: 5, border: '1px solid #efefed'}}>
        <Tx x={12} y={20} s={11} c={ink} w={600}>Réunion générale T2</Tx><Tx x={12} y={40} s={10.5} c="#6b6a67">3 juin 2026 à 10:00</Tx>
        <Tx x={12} y={65} s={10.5} c={ink}>On présentera nos résultats du T2 et</Tx><Tx x={12} y={85} s={10.5} c={ink}>nos priorités du T3. Restez à l’écoute !</Tx>
      </div>
      <Tx x={1110} y={540} s={11} c={ink}>➔ Toutes les annonces</Tx>
      <Ico x={1113} y={592} s={14} c="#8f8e8a" d={D.people} /><Tx x={1127} y={592} s={14} c={ink} w={600}>Équipe</Tx>
      {people.map(([a, n, r, c], i) => (
        <div key={i}>
          <div style={{position: 'absolute', left: 1107, top: 607 + i * 35.6, width: 24, height: 24, borderRadius: 12, background: c, color: '#fff', fontSize: 9, fontWeight: 700, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>{a}</div>
          <Tx x={1139} y={613 + i * 35.6} s={11} c={ink} w={500}>{n}</Tx><Tx x={1139} y={628 + i * 35.6} s={10} c="#6b6a67">{r}</Tx>
        </div>
      ))}
      <Tx x={1110} y={808} s={11} c={ink}>▸ Toute l’équipe</Tx>
    </div>
  );
};
