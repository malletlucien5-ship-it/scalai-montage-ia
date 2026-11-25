import React from 'react';
import {Composition} from 'remotion';

// Chaque dossier src/comps/<id>/index.tsx exporte `meta` et `default`.
// Aucun fichier central à éditer : les compositions sont découvertes ici.
// La prop `fps` choisit la cadence du rendu (30 par défaut, 50 pour la 4K 50p).
// Les compositions gardent leurs durées à 30 i/s : src/shared/rt.tsx convertit le temps.
const BASE_FPS = 30;

const avecCadence = (m: any, original: any) => async (options: any) => {
  const resultat = original ? await original(options) : {};
  const fps = Number(options.props?.fps ?? BASE_FPS);
  const duree = resultat.durationInFrames ?? m.durationInFrames;
  return {...resultat, fps, durationInFrames: Math.ceil((duree * fps) / BASE_FPS)};
};

const ctx = (require as any).context('./comps', true, /^\.\/[^/]+\/index\.tsx$/);

export const RemotionRoot: React.FC = () => (
  <>
    {ctx.keys().sort().map((k: string) => {
      const mod = ctx(k);
      const m = mod.meta;
      return (
        <Composition
          key={m.id}
          id={m.id}
          component={mod.default}
          durationInFrames={m.durationInFrames}
          fps={m.fps ?? BASE_FPS}
          width={1920}
          height={1080}
          defaultProps={m.defaultProps ?? {}}
          calculateMetadata={avecCadence(m, mod.calculateMetadata ?? m.calculateMetadata)}
        />
      );
    })}
  </>
);
