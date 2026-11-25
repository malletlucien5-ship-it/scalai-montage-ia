import React from 'react';

// Pictogrammes au trait de l'application ChatGPT pour macOS (relevés sur la réf. 177,8-184,4 s), viewBox 24.
const P: Record<string, React.ReactNode> = {
  sidebar: <><rect x="3.5" y="5" width="17" height="14" rx="2.5" /><path d="M9 5v14" /></>,
  back: <path d="M19 12H5m6-6-6 6 6 6" />,
  fwd: <path d="M5 12h14m-6-6 6 6-6 6" />,
  search: <><circle cx="11" cy="11" r="6" /><path d="m20 20-4.5-4.5" /></>,
  bell: <><path d="M6 16V11a6 6 0 0 1 12 0v5l1.5 2h-15z" /><path d="M10 20.5a2 2 0 0 0 4 0" /></>,
  edit: <><path d="M12 4H6.5A2.5 2.5 0 0 0 4 6.5v11A2.5 2.5 0 0 0 6.5 20h11a2.5 2.5 0 0 0 2.5-2.5V12" /><path d="m9 15 1-4 8.5-8.5 3 3L13 14z" /></>,
  images: <><rect x="7" y="3.5" width="13.5" height="13.5" rx="3" /><path d="M3.5 8v9.5A3 3 0 0 0 6.5 20.5H16" /><circle cx="11.5" cy="8" r="1.4" /><path d="m7.5 15 4-3.5 3 2.5 2.5-2 3.5 3" /></>,
  clock: <><circle cx="12" cy="12" r="8.5" /><path d="M12 7v5l3 2" /></>,
  plugin: <><circle cx="12" cy="12" r="8.5" /><circle cx="12" cy="12" r="3.2" /><path d="M15.2 12v1.6a2.4 2.4 0 0 0 4.8 0" /></>,
  dots: <><circle cx="5" cy="12" r="1.2" fill="currentColor" /><circle cx="12" cy="12" r="1.2" fill="currentColor" /><circle cx="19" cy="12" r="1.2" fill="currentColor" /></>,
  chevR: <path d="m9 6 6 6-6 6" />,
  chevD: <path d="m6 9 6 6 6-6" />,
  plus: <path d="M12 5v14M5 12h14" />,
  mic: <><rect x="9" y="3.5" width="6" height="11" rx="3" /><path d="M5.5 11.5a6.5 6.5 0 0 0 13 0M12 18v2.5" /></>,
  refresh: <><path d="M19 12a7 7 0 1 1-2.1-5" /><path d="M19 4.5V8h-3.5" /></>,
  help: <><circle cx="12" cy="12" r="8.5" /><path d="M9.6 9.6a2.5 2.5 0 1 1 3.4 2.3c-.6.3-1 .8-1 1.5v.6" /><circle cx="12" cy="16.8" r=".6" fill="currentColor" /></>,
  gauge: <><path d="M4.5 16a8 8 0 1 1 15 0" /><path d="m12 13 3.5-3.5" /><circle cx="12" cy="13.5" r="1" fill="currentColor" /></>,
  pet: <><path d="M12 3.5c4 0 7 3.5 7 8.5s-3 8.5-7 8.5-7-3.5-7-8.5 3-8.5 7-8.5z" /><path d="M10 11v1.5M14 11v1.5" /></>,
  send: <path d="M20.5 3.5 3.5 10.5l7 2.5 2.5 7zM10.5 13l4-4" />,
  gear: <><circle cx="12" cy="12" r="3" /><path d="M12 2.8v2.4M12 18.8v2.4M2.8 12h2.4M18.8 12h2.4M5.5 5.5l1.7 1.7M16.8 16.8l1.7 1.7M5.5 18.5l1.7-1.7M16.8 7.2l1.7-1.7" /><circle cx="12" cy="12" r="6.6" /></>,
  logout: <><path d="M10 4.5H6.5a2 2 0 0 0-2 2v11a2 2 0 0 0 2 2H10" /><path d="M14 8l4 4-4 4M18 12H9" /></>,
  person: <><circle cx="12" cy="12" r="8.5" /><circle cx="12" cy="10" r="3" /><path d="M6.5 18c1.5-2.2 3.4-3 5.5-3s4 .8 5.5 3" /></>,
  shield: <><path d="M12 3.5 19 6v6c0 4.5-3 7.5-7 8.5-4-1-7-4-7-8.5V6z" /><path d="M9.5 12h5" /></>,
  smile: <><circle cx="12" cy="12" r="8.5" /><path d="M8.5 13.5a4 4 0 0 0 7 0" /><path d="M9 9.5v.5M15 9.5v.5" /></>,
  keyboard: <><rect x="3.5" y="3.5" width="17" height="17" rx="3.5" /><path d="m13.5 7-3 5h3l-3 5" /></>,
  openai: <><circle cx="12" cy="12" r="8.5" /><path d="M8 7.5c2-1.5 6-1.5 8 0M7 12c0-2.5 2-4.5 5-4.5M17 12c0 2.5-2 4.5-5 4.5M8 16.5c2 1.5 6 1.5 8 0" /></>,
  arrowUR: <path d="M7 17 17 7M9 7h8v8" />,
  pointer: <path d="m5 4 14 6-6 2-2 6z" />,
  dashed: <path d="M4 8V6a2 2 0 0 1 2-2h2M16 4h2a2 2 0 0 1 2 2v2M20 16v2a2 2 0 0 1-2 2h-2M8 20H6a2 2 0 0 1-2-2v-2M11 4h2M11 20h2M4 11v2M20 11v2" />,
  browser: <><rect x="3.5" y="4.5" width="17" height="15" rx="2.5" /><path d="M3.5 9h17" /></>,
  anchor: <><circle cx="12" cy="5.5" r="2" /><path d="M12 7.5V20M8 11h8M4.5 13.5a7.5 7.5 0 0 0 15 0" /></>,
  globe: <><circle cx="12" cy="12" r="8.5" /><path d="M3.5 12h17M12 3.5c2.5 2.5 3.5 5.5 3.5 8.5s-1 6-3.5 8.5c-2.5-2.5-3.5-5.5-3.5-8.5s1-6 3.5-8.5z" /></>,
  branch: <><circle cx="6.5" cy="5.5" r="2" /><circle cx="6.5" cy="18.5" r="2" /><circle cx="17.5" cy="7.5" r="2" /><path d="M6.5 7.5v9M17.5 9.5c0 4-6 3-11 7" /></>,
  monitor: <><rect x="3.5" y="5" width="17" height="13" rx="2.5" /><path d="M7 14h4" /></>,
  worktree: <path d="M4 18h5l7-12h4M4 12h6M16 18h4" />,
  check: <><circle cx="12" cy="12" r="8.5" /><path d="m8.5 12.2 2.4 2.4 4.8-5" /></>,
  close: <path d="M6.5 6.5l11 11M17.5 6.5l-11 11" />,
  trash: <><path d="M5 7h14M10 7V5h4v2M7 7l1 12.5h8L17 7" /><path d="M10.5 10.5v6M13.5 10.5v6" /></>,
  clip: <path d="M15.5 7.5 9 14a2 2 0 0 0 2.8 2.8l7-7a4 4 0 0 0-5.6-5.6l-7 7a6 6 0 0 0 8.5 8.5l5.3-5.3" />,
};

export const Ico: React.FC<{n: string; s: number; c?: string; w?: number; style?: React.CSSProperties}> = ({n, s, c = 'currentColor', w = 1.7, style}) => (
  <svg width={s} height={s} viewBox="0 0 24 24" style={{display: 'block', color: c, overflow: 'visible', ...style}} fill="none" stroke={c} strokeWidth={w} strokeLinecap="round" strokeLinejoin="round">
    {P[n]}
  </svg>
);

// Logo Chrome (géométrie officielle : trois secteurs, anneau blanc, disque bleu).
export const ChromeLogo: React.FC<{s: number}> = ({s}) => {
  const r = 12;
  const sec = (a0: number, a1: number) => {
    const p = (a: number, rr: number) => [12 + rr * Math.cos((a * Math.PI) / 180), 12 + rr * Math.sin((a * Math.PI) / 180)];
    const [x0, y0] = p(a0, r);
    const [x1, y1] = p(a1, r);
    return `M12 12 L${x0} ${y0} A${r} ${r} 0 0 1 ${x1} ${y1} Z`;
  };
  return (
    <svg width={s} height={s} viewBox="0 0 24 24" style={{display: 'block'}}>
      <path d={sec(-150, -30)} fill="#db4437" />
      <path d={sec(-30, 90)} fill="#f4c20d" />
      <path d={sec(90, 210)} fill="#0f9d58" />
      <circle cx="12" cy="12" r="5.6" fill="#fff" />
      <circle cx="12" cy="12" r="4.4" fill="#4285f4" />
    </svg>
  );
};

// Tuile d'application macOS (fond clair arrondi) avec badge curseur ChatGPT, comme dans la liste « Control ».
export const AppTile: React.FC<{s: number; kind: 'any' | 'chrome' | 'excel' | 'locked'}> = ({s, kind}) => {
  const badge = (
    <div style={{position: 'absolute', right: -s * 0.06, bottom: -s * 0.06, width: s * 0.42, height: s * 0.42, borderRadius: s * 0.12, background: '#fff', boxShadow: '0 1px 3px rgba(0,0,0,0.35)', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
      <svg width={s * 0.3} height={s * 0.3} viewBox="0 0 24 24"><path d="m5 3 14 7-6.5 2L10 19z" fill="#fff" stroke="#333" strokeWidth={2} strokeLinejoin="round" /></svg>
    </div>
  );
  if (kind === 'any') {
    return (
      <div style={{width: s, height: s, borderRadius: s * 0.24, background: 'linear-gradient(135deg, #8fd3ff 0%, #b49bff 45%, #ff9bd8 100%)', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: 'inset 0 0 0 1px rgba(255,255,255,0.4)'}}>
        <svg width={s * 0.62} height={s * 0.62} viewBox="0 0 24 24"><path d="m4 3 17 8-7.5 2.5L10 21z" fill="rgba(255,255,255,0.92)" stroke="#fff" strokeWidth={1.2} strokeLinejoin="round" /></svg>
      </div>
    );
  }
  if (kind === 'locked') {
    return (
      <div style={{width: s, height: s, position: 'relative'}}>
        <div style={{position: 'absolute', left: s * 0.12, top: s * 0.2, width: s * 0.62, height: s * 0.42, borderRadius: s * 0.05, background: 'linear-gradient(180deg, #6cc2ff, #2d7ff0)', border: `${s * 0.03}px solid #d8dde3`}} />
        <div style={{position: 'absolute', left: s * 0.08, top: s * 0.6, width: s * 0.7, height: s * 0.05, borderRadius: 2, background: '#c9ced4'}} />
        <div style={{position: 'absolute', left: s * 0.6, top: s * 0.55, width: s * 0.3, height: s * 0.28, borderRadius: s * 0.05, background: '#f2a43a'}} />
        <div style={{position: 'absolute', left: s * 0.64, top: s * 0.42, width: s * 0.22, height: s * 0.2, borderRadius: `${s * 0.11}px ${s * 0.11}px 0 0`, border: `${s * 0.035}px solid #d9d9d9`, borderBottom: 'none'}} />
      </div>
    );
  }
  return (
    <div style={{width: s, height: s, position: 'relative', borderRadius: s * 0.22, background: kind === 'chrome' ? '#fff' : '#fbfbfb', boxShadow: '0 0 0 1px rgba(0,0,0,0.25)'}}>
      {kind === 'chrome' ? (
        <div style={{position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center'}}><ChromeLogo s={s * 0.98} /></div>
      ) : (
        <div style={{position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center'}}><ExcelLogo s={s * 0.7} /></div>
      )}
      {badge}
    </div>
  );
};

// Logo Excel (dalle verte et feuille, « X » blanc).
export const ExcelLogo: React.FC<{s: number}> = ({s}) => (
  <svg width={s} height={s} viewBox="0 0 24 24" style={{display: 'block'}}>
    <rect x="7" y="2.5" width="15" height="19" rx="2" fill="#21a366" />
    <rect x="7" y="2.5" width="15" height="6.3" fill="#33c481" />
    <rect x="7" y="15" width="15" height="6.5" fill="#107c41" />
    <rect x="2" y="6.5" width="11" height="11" rx="1.6" fill="#185c37" />
    <path d="m4.6 9.2 2.4 2.8-2.4 2.8M9.6 9.2 7.2 12l2.4 2.8" stroke="#fff" strokeWidth={1.6} fill="none" strokeLinecap="round" />
  </svg>
);
