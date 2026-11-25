// Couche de temps des compositions.
// Les compositions comptent leurs images à 30 i/s. Ce module les rend à
// n'importe quelle cadence (50 i/s pour une vidéo 4K 50p) sans toucher leur code :
// - useCurrentFrame renvoie l'image équivalente à 30 i/s, décimale entre deux images ;
// - useVideoConfig annonce 30 i/s et la durée en images à 30 i/s ;
// - Sequence, Audio et OffthreadVideo convertissent leurs bornes vers la cadence réelle.
// Importer depuis ce fichier au lieu de 'remotion' dans src/comps et src/shared.
import React from 'react';
import * as R from 'remotion';

export * from 'remotion';

export const BASE_FPS = 30;

const facteur = (fps: number) => fps / BASE_FPS;

export const useCurrentFrame = (): number => {
  const frame = R.useCurrentFrame();
  const {fps} = R.useVideoConfig();
  return frame / facteur(fps);
};

export const useVideoConfig = () => {
  const config = R.useVideoConfig();
  return {
    ...config,
    fps: BASE_FPS,
    durationInFrames: Math.round(config.durationInFrames / facteur(config.fps)),
  };
};

const versReel = (valeur: number | undefined, k: number) =>
  valeur === undefined || !Number.isFinite(valeur) ? valeur : Math.round(valeur * k);

type SequenceProps = React.ComponentProps<typeof R.Sequence>;

export const Sequence: React.FC<SequenceProps> = (props) => {
  const {fps} = R.useVideoConfig();
  const k = facteur(fps);
  const {from, durationInFrames, ...reste} = props as SequenceProps & {
    from?: number;
    durationInFrames?: number;
  };
  return (
    <R.Sequence
      {...(reste as SequenceProps)}
      from={versReel(from ?? 0, k)}
      durationInFrames={versReel(durationInFrames, k)}
    />
  );
};

type AudioProps = React.ComponentProps<typeof R.Audio>;

export const Audio: React.FC<AudioProps> = (props) => {
  const {fps} = R.useVideoConfig();
  const k = facteur(fps);
  const p = props as AudioProps & {
    trimBefore?: number;
    trimAfter?: number;
    volume?: number | ((f: number) => number);
  };
  const volume =
    typeof p.volume === 'function' ? (f: number) => (p.volume as (f: number) => number)(f / k) : p.volume;
  return (
    <R.Audio
      {...(p as AudioProps)}
      trimBefore={versReel(p.trimBefore, k)}
      trimAfter={versReel(p.trimAfter, k)}
      volume={volume as AudioProps['volume']}
    />
  );
};

type VideoProps = React.ComponentProps<typeof R.OffthreadVideo>;

export const OffthreadVideo: React.FC<VideoProps> = (props) => {
  const {fps} = R.useVideoConfig();
  const k = facteur(fps);
  const p = props as VideoProps & {trimBefore?: number; trimAfter?: number};
  return (
    <R.OffthreadVideo
      {...(p as VideoProps)}
      trimBefore={versReel(p.trimBefore, k)}
      trimAfter={versReel(p.trimAfter, k)}
    />
  );
};
