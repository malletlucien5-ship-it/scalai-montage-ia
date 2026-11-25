import React from 'react';
import {Composition} from 'remotion';
import {Board, BoardProps} from './Board';
import props from '../props.json';

const FPS = 30000 / 1001;

export const RemotionRoot: React.FC = () => (
  <Composition
    id="bad-good-best"
    component={Board}
    durationInFrames={(props as BoardProps).totalFrames}
    fps={FPS}
    width={1080}
    height={1920}
    defaultProps={props as BoardProps}
  />
);
