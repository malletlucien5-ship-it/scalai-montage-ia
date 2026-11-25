import React from 'react';
import {AbsoluteFill} from './rt';

// Le speaker est retiré (décision du 23/09/2026).
// show=true : fond neutre pour l'aperçu mp4. show=false : transparent pour le rendu alpha.
export const Plate: React.FC<{src?: string; show?: boolean}> = ({show = true}) =>
  show ? <AbsoluteFill style={{background: '#0E0E10'}} /> : null;
