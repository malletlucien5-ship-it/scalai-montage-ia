// Logos d'apps. Monochromes : simple-icons. Multicolores (Google, Slack) : SVG fidèles.
import React from 'react';
import {siGithub, siNotion, siZapier, siClaude} from 'simple-icons';
import {ARIAL_L} from '../../shared/localFonts';

type P = {size: number; style?: React.CSSProperties};

export const GmailLogo: React.FC<P> = ({size, style}) => (
  <svg width={size} height={size * 0.75} viewBox="0 0 48 36" style={style}>
    <path d="M3 36h8V16.5L0 8.2V33a3 3 0 0 0 3 3z" fill="#4285F4" />
    <path d="M37 36h8a3 3 0 0 0 3-3V8.2L37 16.5z" fill="#34A853" />
    <path d="M37 2.2v14.3L48 8.2V4.5c0-3.8-4.3-5.9-7.3-3.6z" fill="#FBBC04" />
    <path d="M11 16.5V2.2l13 9.8 13-9.8v14.3L24 26.2z" fill="#EA4335" />
    <path d="M0 4.5v3.7l11 8.3V2.2L7.3.9C4.3-1.4 0 .7 0 4.5z" fill="#C5221F" />
  </svg>
);

export const DriveLogo: React.FC<P> = ({size, style}) => (
  <svg width={size} height={size * 0.89} viewBox="0 0 87.3 78" style={style}>
    <path d="M6.6 66.85l3.85 6.65c.8 1.4 1.95 2.5 3.3 3.3L27.5 53H0c0 1.55.4 3.1 1.2 4.5z" fill="#0066DA" />
    <path d="M43.65 25L29.9 1.2c-1.35.8-2.5 1.9-3.3 3.3L1.2 48.5A9.06 9.06 0 0 0 0 53h27.5z" fill="#00AC47" />
    <path d="M73.55 76.8c1.35-.8 2.5-1.9 3.3-3.3l1.6-2.75 7.65-13.25c.8-1.4 1.2-2.95 1.2-4.5H59.8l5.85 11.5z" fill="#EA4335" />
    <path d="M43.65 25L57.4 1.2C56.05.4 54.5 0 52.9 0H34.4c-1.6 0-3.15.45-4.5 1.2z" fill="#00832D" />
    <path d="M59.8 53H27.5L13.75 76.8c1.35.8 2.9 1.2 4.5 1.2h50.8c1.6 0 3.15-.45 4.5-1.2z" fill="#2684FC" />
    <path d="M73.4 26.5L60.7 4.5c-.8-1.4-1.95-2.5-3.3-3.3L43.65 25 59.8 53h27.45c0-1.55-.4-3.1-1.2-4.5z" fill="#FFBA00" />
  </svg>
);

export const CalLogo: React.FC<P & {day?: string}> = ({size, style, day = '31'}) => (
  <svg width={size} height={size} viewBox="0 0 48 48" style={style}>
    <path d="M36 12H12v24h24z" fill="#fff" />
    <path d="M36 48l12-12H36z" fill="#EA4335" />
    <path d="M48 12H36v24h12z" fill="#FBBC04" />
    <path d="M36 36H12v12h24z" fill="#34A853" />
    <path d="M0 36v8a4 4 0 0 0 4 4h8V36z" fill="#188038" />
    <path d="M48 12V4a4 4 0 0 0-4-4h-8v12z" fill="#1967D2" />
    <path d="M36 0H4a4 4 0 0 0-4 4v32h12V12h24z" fill="#4285F4" />
    <text x="24" y="31" textAnchor="middle" fontFamily={`Arial, ${ARIAL_L}, sans-serif`} fontWeight="700" fontSize="15" fill="#4285F4">{day}</text>
  </svg>
);

export const SlackLogo: React.FC<P> = ({size, style}) => (
  <svg width={size} height={size} viewBox="0 0 54 54" style={style}>
    <path d="M19.7 0a5.4 5.4 0 0 0 0 10.8h5.4V5.4A5.4 5.4 0 0 0 19.7 0m0 14.4H5.4a5.4 5.4 0 0 0 0 10.8h14.3a5.4 5.4 0 0 0 0-10.8" fill="#36C5F0" />
    <path d="M54 19.8a5.4 5.4 0 0 0-10.8 0v5.4h5.4a5.4 5.4 0 0 0 5.4-5.4m-14.4 0V5.4a5.4 5.4 0 0 0-10.8 0v14.4a5.4 5.4 0 0 0 10.8 0" fill="#2EB67D" />
    <path d="M34.2 54a5.4 5.4 0 0 0 0-10.8h-5.4v5.4a5.4 5.4 0 0 0 5.4 5.4m0-14.4h14.4a5.4 5.4 0 0 0 0-10.8H34.2a5.4 5.4 0 0 0 0 10.8" fill="#ECB22E" />
    <path d="M0 34.2a5.4 5.4 0 0 0 10.8 0v-5.4H5.4A5.4 5.4 0 0 0 0 34.2m14.4 0v14.4a5.4 5.4 0 0 0 10.8 0V34.2a5.4 5.4 0 0 0-10.8 0" fill="#E01E5A" />
  </svg>
);

const Mono: React.FC<P & {icon: {path: string}; color: string}> = ({size, style, icon, color}) => (
  <svg width={size} height={size} viewBox="0 0 24 24" style={style}><path d={icon.path} fill={color} /></svg>
);
export const GithubLogo: React.FC<P & {color?: string}> = ({color = '#fff', ...p}) => <Mono {...p} icon={siGithub} color={color} />;
export const NotionLogo: React.FC<P & {color?: string}> = ({color = '#000', ...p}) => <Mono {...p} icon={siNotion} color={color} />;
export const ZapierLogo: React.FC<P & {color?: string}> = ({color = '#FF4F00', ...p}) => <Mono {...p} icon={siZapier} color={color} />;
export const ClaudeLogo: React.FC<P & {color?: string}> = ({color = '#D97757', ...p}) => <Mono {...p} icon={siClaude} color={color} />;

// Logos absents de simple-icons, redessinés d'après la référence.
// Granola : carré vert anis, spirale sombre.
export const GranolaLogo: React.FC<P> = ({size, style}) => (
  <svg width={size} height={size} viewBox="0 0 24 24" style={style}>
    <rect x="1" y="1" width="22" height="22" rx="1.5" fill="#C8D65B" />
    <path d="M12.4 12.6c-.2-.9.6-1.6 1.4-1.3 1.1.4 1.2 1.9.5 2.7-1 1.2-2.9 1-3.8-.2-1.2-1.6-.6-3.9 1-4.9 2-1.2 4.6-.4 5.7 1.6 1.3 2.4.2 5.4-2.2 6.5-2.8 1.3-6.1-.1-7.2-2.9-1.1-2.9.3-6.1 3-7.5" fill="none" stroke="#1d2410" strokeWidth="1.7" strokeLinecap="round" />
  </svg>
);
// Relay : carré orange vif.
export const RelayLogo: React.FC<P> = ({size, style}) => (
  <svg width={size} height={size} viewBox="0 0 24 24" style={style}><rect x="1" y="1" width="22" height="22" rx="1" fill="#FF5A0A" /></svg>
);
// Otter.ai : mot-symbole bleu « O|| + » compact.
export const OtterLogo: React.FC<P> = ({size, style}) => (
  <svg width={size} height={size} viewBox="0 0 24 24" style={style}>
    <circle cx="5.2" cy="12" r="3.1" fill="none" stroke="#2F57C9" strokeWidth="2" />
    <rect x="10" y="8.2" width="2.2" height="7.6" rx="1.1" fill="#2F57C9" />
    <rect x="13.8" y="8.2" width="2.2" height="7.6" rx="1.1" fill="#2F57C9" />
    <path d="M19.8 9.8v4.4M17.6 12h4.4" stroke="#2F57C9" strokeWidth="1.8" strokeLinecap="round" />
  </svg>
);
