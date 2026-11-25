// Tableau « Bad / Good / Best » recopié du short Dan Martell (UH0pqsq2i80).
// Titre : même taille et même place que chez Dan, centré en x.
// Étiquettes et icônes : une seule position pour toute la vidéo, comme chez Dan.
// Chaque icône démarre floutée
// et se révèle en 2 images quand le doigt arrive.
import React from 'react';
import {AbsoluteFill, OffthreadVideo, Img, Sequence, staticFile, useCurrentFrame} from 'remotion';

type Tool = {name: string; icon: string; reveal: number};
type Tip = {x: number; y: number};
type Section = {title: string; from: number; to: number; tools: Tool[]; tips: Tip[]};
export type BoardProps = {
  totalFrames: number;
  video: string | null;
  labels: string[];
  sections: Section[];
};

// Mesures de la référence (px, image 1080x1920).
const REF = {
  pillCenterX: 540,
  pillTop: 360,
  pillH: 106,
  pillPadX: 19,
  pillFont: 82,
  pillRadius: 16,
  labelFont: 40,
  iconSize: 188,
  nameFont: 30,
  nameGap: 8,
};
// Place de l'étiquette par rapport au bout du doigt, relevée sur Dan.
const TIP_TO_LABEL = {dx: 25, dy: 10};
const LABEL_TO_ICON = 14;
const ICON_OFFSET_Y = 30;
const RIGHT_MARGIN = 30;
const LABEL_COLORS = ['rgb(239,0,5)', 'rgb(247,242,18)', 'rgb(26,249,23)'];
const SF = '-apple-system, "SF Pro Display", "Helvetica Neue", Helvetica, Arial, sans-serif';
const LABEL_FONT = '"Helvetica Neue", Helvetica, Arial, sans-serif';
// Flou avant révélation puis rampe relevée image par image : 20 px, 8 px, net.
const BLUR_IDLE = 20;
const BLUR_RAMP = [20, 8, 0];

// Largeur de texte mesurée de façon synchrone.
const textWidth = (text: string, font: string): number => {
  const ctx = document.createElement('canvas').getContext('2d');
  if (!ctx) return 0;
  ctx.font = font;
  return ctx.measureText(text).width;
};

type Layout = {
  labels: {left: number; y: number}[];
  iconX: number;
  iconSize: number;
  iconY: number[];
};

// Position unique pour toute la vidéo, calquée sur Dan.
// Dan : étiquettes y = 563 / 785 / 998, icônes 188 px sous chaque étiquette.
// Lucien (30/09) : étiquettes sur ses croix, alignées à droite pour un écart court et identique
// avec les icônes. Icônes espacées régulièrement, 44 px sous chaque étiquette comme la première de Dan.
const LABEL_RIGHT = 800;
const LABEL_Y = [674, 996, 1318];
const ICON_BELOW_LABEL = 44;

const layoutFor = (labels: string[]): Layout => {
  const widths = labels.map((l) => textWidth(l, `800 ${REF.labelFont}px ${LABEL_FONT}`) + 6);
  const iconSize = REF.iconSize;
  const colLeft = LABEL_RIGHT + LABEL_TO_ICON;
  return {
    labels: LABEL_Y.map((y, i) => ({left: LABEL_RIGHT - widths[i], y})),
    iconX: colLeft + iconSize / 2,
    iconSize,
    iconY: LABEL_Y.map((y) => y + ICON_BELOW_LABEL),
  };
};

const Pill: React.FC<{text: string}> = ({text}) => {
  const w = textWidth(text, `700 ${REF.pillFont}px ${SF}`) + 2 * REF.pillPadX;
  return (
    <div
      style={{
        position: 'absolute',
        left: REF.pillCenterX - w / 2,
        top: REF.pillTop,
        height: REF.pillH,
        padding: `0 ${REF.pillPadX}px`,
        background: '#fff',
        borderRadius: REF.pillRadius,
        display: 'flex',
        alignItems: 'center',
        fontFamily: SF,
        fontSize: REF.pillFont,
        fontWeight: 700,
        color: '#000',
        whiteSpace: 'nowrap',
      }}
    >
      {text}
    </div>
  );
};

const Label: React.FC<{text: string; i: number; left: number; y: number}> = ({text, i, left, y}) => (
  <div
    style={{
      position: 'absolute',
      left,
      top: y,
      transform: 'translateY(-50%)',
      fontFamily: LABEL_FONT,
      fontWeight: 800,
      fontSize: REF.labelFont,
      letterSpacing: -1.5,
      color: LABEL_COLORS[i],
      WebkitTextStroke: '5px #000',
      paintOrder: 'stroke fill',
      whiteSpace: 'nowrap',
    }}
  >
    {text}
  </div>
);

const Icon: React.FC<{tool: Tool; local: number; cx: number; cy: number; s: number}> = ({
  tool,
  local,
  cx,
  cy,
  s,
}) => {
  const k = local - tool.reveal;
  const blur = k < 0 ? BLUR_IDLE : BLUR_RAMP[Math.min(k, BLUR_RAMP.length - 1)];
  const shown = k >= BLUR_RAMP.length - 1;
  const logo = s * 0.66;
  return (
    <>
      <div
        style={{
          position: 'absolute',
          left: cx - s / 2,
          top: cy - s / 2,
          width: s,
          height: s,
          borderRadius: s * 0.235,
          background: '#fff',
          boxShadow: '0 0 0 2.5px rgba(40,40,40,0.55), 0 3px 8px rgba(0,0,0,0.18)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          filter: blur > 0 ? `blur(${blur}px)` : undefined,
        }}
      >
        <Img src={staticFile(`icons/${tool.icon}.svg`)} style={{width: logo, height: logo}} />
      </div>
      {shown && (
        <div
          style={{
            position: 'absolute',
            left: cx,
            top: cy + s / 2 + REF.nameGap,
            transform: 'translateX(-50%)',
            fontFamily: SF,
            fontWeight: 500,
            fontSize: REF.nameFont,
            color: '#000',
            whiteSpace: 'nowrap',
          }}
        >
          {tool.name}
        </div>
      )}
    </>
  );
};

const SectionBoard: React.FC<{section: Section; labels: string[]}> = ({section, labels}) => {
  const local = useCurrentFrame();
  const L = layoutFor(labels);
  return (
    <AbsoluteFill>
      <Pill text={section.title} />
      {labels.map((l, i) => (
        <Label key={l} text={l} i={i} left={L.labels[i].left} y={L.labels[i].y} />
      ))}
      {section.tools.map((t, i) => (
        <Icon key={t.name} tool={t} local={local} cx={L.iconX} cy={L.iconY[i]} s={L.iconSize} />
      ))}
    </AbsoluteFill>
  );
};

export const Board: React.FC<BoardProps> = ({video, labels, sections}) => (
  <AbsoluteFill style={{backgroundColor: video ? '#000' : 'transparent'}}>
    {video && <OffthreadVideo src={staticFile(video)} />}
    {sections.map((s) => (
      <Sequence key={s.title} from={s.from} durationInFrames={s.to - s.from} layout="none">
        <SectionBoard section={s} labels={labels} />
      </Sequence>
    ))}
  </AbsoluteFill>
);
