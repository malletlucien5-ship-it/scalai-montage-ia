// Éléments d'interface Claude (sombre) partagés dans ce dossier.
import React from 'react';
import {Img, staticFile} from '../../shared/rt';
import {SANS, SERIF, IBuilding, IPlus, IChats, IProjects, IStack, IShapes, IBriefcase, IPalette, IChevron, IMic, IWave} from './ui';

type IP = {size?: number; color?: string; sw?: number; style?: React.CSSProperties};
const Svg: React.FC<IP & {children: React.ReactNode}> = ({size = 24, color = '#cfcfcc', sw = 1.7, style, children}) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={sw} strokeLinecap="round" strokeLinejoin="round" style={style}>{children}</svg>
);
export const IPanel: React.FC<IP> = (p) => <Svg {...p}><rect x="3.5" y="4.5" width="17" height="15" rx="2" /><path d="M9 4.5v15" /></Svg>;
export const IDownload: React.FC<IP> = (p) => <Svg {...p}><path d="M12 4v11M7.5 10.5L12 15l4.5-4.5M4.5 19.5h15" /></Svg>;
export const IArrowL: React.FC<IP> = (p) => <Svg {...p}><path d="M19 12H5M11 6l-6 6 6 6" /></Svg>;
export const IKebab: React.FC<IP> = (p) => <Svg {...p}><circle cx="12" cy="5" r="0.9" fill={p.color} /><circle cx="12" cy="12" r="0.9" fill={p.color} /><circle cx="12" cy="19" r="0.9" fill={p.color} /></Svg>;
export const IStar: React.FC<IP> = (p) => <Svg {...p}><path d="M12 3.5l2.6 5.3 5.9.9-4.3 4.1 1 5.8L12 16.9l-5.2 2.7 1-5.8-4.3-4.1 5.9-.9z" /></Svg>;
export const IImage: React.FC<IP> = (p) => <Svg {...p}><rect x="3.5" y="4.5" width="17" height="15" rx="2" /><circle cx="9" cy="9.5" r="1.6" /><path d="M20.5 15.5l-5-5-9 9" /></Svg>;
export const ILockS: React.FC<IP> = (p) => <Svg {...p}><rect x="5" y="10.5" width="14" height="10" rx="2" /><path d="M8 10.5V7.5a4 4 0 0 1 8 0v3" /></Svg>;
export const IDoc: React.FC<IP> = (p) => <Svg {...p}><path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z" /><path d="M14 3v5h5M9 13h6M9 16.5h6" /></Svg>;
export const ICodeDoc: React.FC<IP> = (p) => <Svg {...p}><path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z" /><path d="M14 3v5h5M10 12l-2 2.5 2 2.5M14 12l2 2.5-2 2.5" /></Svg>;

// Barre latérale d'icônes de Claude. y = centres des icônes (unités contenu).
export const Sidebar: React.FC<{w: number; h: number; ys: number[]; bottom: number[]; color?: string}> = ({w, h, ys, bottom, color = '#cfcdc8'}) => {
  const icons = [IPanel, IPlus, IChats, IProjects, IStack, IShapes, IBriefcase, IPalette];
  return (
    <div style={{position: 'absolute', left: 0, top: 0, width: w, height: h, borderRight: '1.5px solid #2a2a28'}}>
      {icons.map((I, i) => (
        <div key={i} style={{position: 'absolute', left: w / 2 - 14, top: ys[i] - 14, width: 28, height: 28, borderRadius: 14,
          background: i === 1 ? '#34342f' : 'transparent', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
          <I size={i === 1 ? 15 : i === 0 ? 18 : 20} color={i === 0 ? '#9d9b96' : color} sw={1.6} />
        </div>
      ))}
      <IDownload size={20} color={color} sw={1.6} style={{position: 'absolute', left: w / 2 - 10, top: bottom[0] - 10}} />
      <div style={{position: 'absolute', left: w / 2 - 20, top: bottom[1] - 20, width: 40, height: 40}}>
        <Img src={staticFile('lucien-rond.png')} style={{width: 40, height: 40, borderRadius: 20}} />
        <div style={{position: 'absolute', right: -3, bottom: -3, width: 15, height: 15, borderRadius: 4, background: '#2b2b28', border: '1px solid #444', display: 'flex', alignItems: 'center', justifyContent: 'center'}}><IBuilding size={10} color="#bbb" sw={1.6} /></div>
      </div>
    </div>
  );
};

// Zone de saisie Claude.
export const ChatInput: React.FC<{x: number; y: number; w: number; h: number; placeholder: string; fs?: number; model?: string; caret?: boolean}> = ({x, y, w, h, placeholder, fs = 19, model = 'Sonnet 4.6', caret = false}) => (
  <div style={{position: 'absolute', left: x, top: y, width: w, height: h, borderRadius: 22, background: '#2b2b28', border: '1.5px solid #353532', boxSizing: 'border-box', fontFamily: SANS}}>
    <div style={{position: 'absolute', left: 25, top: h * 0.2, fontSize: fs, color: '#8e8c87'}}>
      {caret && <span style={{borderLeft: '1.5px solid #ddd', marginRight: 1}} />}{placeholder}
    </div>
    <IPlus size={fs + 3} color="#cfcdc8" sw={1.6} style={{position: 'absolute', left: 30, top: h * 0.74 - (fs + 3) / 2}} />
    <div style={{position: 'absolute', right: 116, top: h * 0.74 - fs * 0.62, fontSize: fs * 0.95, color: '#c6c4bf', display: 'flex', alignItems: 'center', gap: 8}}>
      {model} <span style={{color: '#8e8c87'}}>Bas</span><IChevron size={13} color="#8e8c87" />
    </div>
    <IMic size={fs + 2} color="#cfcdc8" style={{position: 'absolute', right: 66, top: h * 0.74 - (fs + 2) / 2}} />
    <IWave size={fs + 4} color="#cfcdc8" style={{position: 'absolute', right: 22, top: h * 0.74 - (fs + 4) / 2}} />
  </div>
);

export {SERIF, SANS};
