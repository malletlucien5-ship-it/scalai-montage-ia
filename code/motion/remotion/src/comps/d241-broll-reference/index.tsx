import React from 'react';
import {AbsoluteFill, OffthreadVideo} from '../../shared/rt';

// d241 : plan de la vidéo de référence, repris tel quel (b-roll réutilisable).
// Le clip est extrait par cloud/extraire_reference.py dans outputs/<projet>/brolls-reference/.
// props.s3 (URI s3://) est présigné en props.src par render_lambda_final.py au rendu.
// `debut` : seconde du clip où commence la lecture (0 pour un clip déjà coupé à la plage).
type Props = {src: string; debut: number; nom?: string};

const BrollReference: React.FC<Props> = ({src, debut}) => (
  <AbsoluteFill style={{backgroundColor: 'black'}}>
    {src ? (
      <OffthreadVideo
        src={src}
        trimBefore={Math.round((debut || 0) * 30)}
        muted
        toneMapped={false}
        delayRenderTimeoutInMilliseconds={600000}
        delayRenderRetries={2}
        style={{width: '100%', height: '100%', objectFit: 'cover'}}
      />
    ) : null}
  </AbsoluteFill>
);

export const meta = {
  id: 'd241-broll-reference',
  fps: 30,
  durationInFrames: 1800,
  defaultProps: {src: '', debut: 0},
  occurrences: [],
};
export default BrollReference;
