import React from 'react';
import {AbsoluteFill, Composition} from 'remotion';

// Même contrat que PanneauV4 : props {plan, images: [f]}, l'image 0 montre l'image f de la timeline.
const Panneau: React.FC<{images: number[]}> = ({images}) => (
  <AbsoluteFill style={{background: images[0] % 2 ? '#202080' : '#208020'}} />
);

export const Racine: React.FC = () => (
  <Composition id="PanneauV4" component={Panneau} width={320} height={270} fps={50} durationInFrames={1} defaultProps={{images: [0]}} />
);
