import React from 'react';
import {Composition} from 'remotion';
import {BeforeAfter, BAProps} from './BeforeAfter';
import props from '../props.json';

export const RemotionRoot: React.FC = () => (
  <Composition
    id="avant-avec-ia"
    component={BeforeAfter}
    durationInFrames={(props as BAProps).totalFrames}
    fps={30000 / 1001}
    width={1080}
    height={1920}
    defaultProps={props as BAProps}
    calculateMetadata={({props: p}) => ({durationInFrames: p.totalFrames})}
  />
);
