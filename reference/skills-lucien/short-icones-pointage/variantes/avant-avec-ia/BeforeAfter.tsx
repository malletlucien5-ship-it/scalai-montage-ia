// Short « avant l'IA / avec l'IA » recopié de Dan Martell (jkSJqLsjcQ4).
// Mesures relevées sur la référence 1080x1920. Le carré blanc reste net.
// Le logo et le nom sont flous avant le geste, puis deviennent nets en 6 images avec un bip.
import React from 'react';
import {AbsoluteFill, Audio, Img, OffthreadVideo, Sequence, staticFile, useCurrentFrame} from 'remotion';

type Tool = {name: string; icon: string; reveal: number};
type Section = {title: string; from: number; to: number; before: Tool; after: Tool};
export type BAProps = {
  totalFrames: number;
  video: string;
  labels: [string, string];
  sfxGain: number;
  sections: Section[];
};

const REF = {
  titleTop: 252,
  titleH: 76,
  titleFont: 58,
  titlePadX: 16,
  titleRadius: 12,
  labelY: 430,
  labelX: [295, 828],
  labelFont: 62,
  tileCX: [300, 826],
  tileCY: 612,
  tile: 250,
  tileRadius: 14,
  logo: 200,
  nameTop: 748,
  nameFont: 50,
};
const LABEL_COLORS = ['rgb(239,0,5)', 'rgb(26,249,23)'];
const SF = '-apple-system, "SF Pro Display", "Helvetica Neue", Helvetica, Arial, sans-serif';
const LABEL_FONT = '"Helvetica Neue", Helvetica, Arial, sans-serif';
// Rampe relevée image par image sur la référence (flou en px, opacité du nom).
const IDLE_BLUR = 16;
const RAMP_BLUR = [16, 10, 7, 4, 1.5, 0];
const RAMP_NAME = [0, 0.6, 0.8, 1, 1, 1];

const textWidth = (text: string, font: string): number => {
  const ctx = document.createElement('canvas').getContext('2d');
  if (!ctx) return 0;
  ctx.font = font;
  return ctx.measureText(text).width;
};

const Title: React.FC<{text: string}> = ({text}) => {
  const w = textWidth(text, `700 ${REF.titleFont}px ${SF}`) + 2 * REF.titlePadX;
  return (
    <div
      style={{
        position: 'absolute',
        left: 540 - w / 2,
        top: REF.titleTop,
        height: REF.titleH,
        padding: `0 ${REF.titlePadX}px`,
        background: '#fff',
        borderRadius: REF.titleRadius,
        display: 'flex',
        alignItems: 'center',
        fontFamily: SF,
        fontWeight: 700,
        fontSize: REF.titleFont,
        color: '#000',
        whiteSpace: 'nowrap',
      }}
    >
      {text}
    </div>
  );
};

const Label: React.FC<{text: string; i: number}> = ({text, i}) => (
  <div
    style={{
      position: 'absolute',
      left: REF.labelX[i],
      top: REF.labelY,
      transform: 'translate(-50%, -50%)',
      fontFamily: LABEL_FONT,
      fontWeight: 800,
      fontSize: REF.labelFont,
      letterSpacing: -1,
      color: LABEL_COLORS[i],
      WebkitTextStroke: '4px #000',
      paintOrder: 'stroke fill',
      whiteSpace: 'nowrap',
    }}
  >
    {text}
  </div>
);

const Tile: React.FC<{tool: Tool; i: number; local: number}> = ({tool, i, local}) => {
  const k = local - tool.reveal;
  const blur = k < 0 ? IDLE_BLUR : RAMP_BLUR[Math.min(k, RAMP_BLUR.length - 1)];
  const nameOpacity = k < 0 ? 0 : RAMP_NAME[Math.min(k, RAMP_NAME.length - 1)];
  const cx = REF.tileCX[i];
  const isPng = tool.icon.endsWith('.png');
  return (
    <>
      <div
        style={{
          position: 'absolute',
          left: cx - REF.tile / 2,
          top: REF.tileCY - REF.tile / 2,
          width: REF.tile,
          height: REF.tile,
          borderRadius: REF.tileRadius,
          background: '#fff',
          boxShadow: '0 0 0 1.5px rgba(0,0,0,0.25), 0 4px 10px rgba(0,0,0,0.25)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          overflow: 'hidden',
        }}
      >
        <Img
          src={staticFile(`icons/${tool.icon}`)}
          style={{
            width: REF.logo,
            height: REF.logo,
            objectFit: 'contain',
            borderRadius: isPng ? REF.logo * 0.22 : 0,
            filter: blur > 0 ? `blur(${blur}px)` : undefined,
          }}
        />
      </div>
      <div
        style={{
          position: 'absolute',
          left: cx,
          top: REF.nameTop,
          transform: 'translateX(-50%)',
          fontFamily: SF,
          fontWeight: 700,
          fontSize: REF.nameFont,
          color: '#fff',
          WebkitTextStroke: '9px #000',
          paintOrder: 'stroke fill',
          whiteSpace: 'nowrap',
          opacity: nameOpacity,
          filter: blur > 0 ? `blur(${blur}px)` : undefined,
        }}
      >
        {tool.name}
      </div>
    </>
  );
};

const SectionView: React.FC<{s: Section; labels: [string, string]; sfxGain: number}> = ({s, labels, sfxGain}) => {
  const local = useCurrentFrame();
  return (
    <AbsoluteFill>
      <Title text={s.title} />
      <Label text={labels[0]} i={0} />
      <Label text={labels[1]} i={1} />
      <Tile tool={s.before} i={0} local={local} />
      <Tile tool={s.after} i={1} local={local} />
      {[s.before, s.after].map((t) => (
        <Sequence key={t.name} from={t.reveal} layout="none">
          <Audio src={staticFile('sfx/bip.wav')} volume={sfxGain} />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};

export const BeforeAfter: React.FC<BAProps> = ({video, labels, sfxGain, sections}) => (
  <AbsoluteFill style={{backgroundColor: '#000'}}>
    <OffthreadVideo src={staticFile(video)} muted />
    {sections.map((s) => (
      <Sequence key={s.title} from={s.from} durationInFrames={s.to - s.from} layout="none">
        <SectionView s={s} labels={labels} sfxGain={sfxGain} />
      </Sequence>
    ))}
  </AbsoluteFill>
);
