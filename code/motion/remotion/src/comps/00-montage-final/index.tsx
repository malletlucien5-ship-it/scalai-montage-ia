import React from 'react';
import {
  AbsoluteFill,
  CalculateMetadataFunction,
  OffthreadVideo,
  Sequence,
  useCurrentFrame,
} from '../../shared/rt';
import {echelleZoom, Zoom} from './zoom';
import {SfxMuetCtx} from '../../shared/Sfx';
import {StudioAVideo} from '../../shared/StudioAVideo';
import {STUDIO_A_SHA256} from '../../shared/studio-a-data';

// 00 : montage final en un seul rendu Lambda.
// Couche de base : les coupes du monteur, lues image par image dans les rushs caméra.
// Zooms : sur la couche de base seulement. Motions : les compositions du catalogue, au-dessus.
// Vidéo muette : l'audio est mixé dans le conteneur par render_lambda_final.py.
//
// Temps : les props `segments` et `images` sont en images réelles (50 i/s).
// La couche rt compte à 30 i/s : `versRt` convertit, rt arrondit, l'image reste exacte.
// Les placements gardent leurs durées à 30 i/s, comme placements.json.

const BASE_FPS = 30;

export type SegmentMontage = {
  sortie: number; // première image de sortie
  images: number; // nombre d'images
  rush: number; // index dans `rushs`, -1 pour du noir
  debut: number; // première image lue dans le rush
};

export type PlacementMontage = {
  id: string;
  from: number; // image de départ dans la composition, à 30 i/s
  dur: number; // durée à 30 i/s
  at: number; // départ dans la timeline, en secondes
  mode: string; // 'overlay' : calque transparent, sinon plein cadre
  props?: Record<string, unknown>;
  duree?: number; // durée propre de la composition, résolue par calculateMetadata
};

export type MontageProps = {
  fps: number;
  images: number;
  rushs: string[];
  segments: SegmentMontage[];
  zooms: Zoom[];
  placements: PlacementMontage[];
  // true : seulement les motions, pour rendre leurs bruitages en audio seul.
  audioSeul?: boolean;
  // false : couche caméra sans l'étalonnage standard (actif par défaut).
  etalonnage?: boolean;
  etalonnageProfil?: string;
  etalonnageSha256?: string;
};

// Registre des compositions, chargé à la demande : esbuild (occurrences.mjs) ne connaît pas
// require.context, et le montage ne doit pas s'importer lui-même.
let registre: any = null;
const composition = (id: string): any => {
  if (!registre) {
    const ctx = (require as any).context('..', true, /^\.\/(?!00-montage-final\/)[^/]+\/index\.tsx$/);
    registre = {};
    for (const cle of ctx.keys()) {
      const mod = ctx(cle);
      if (mod?.meta?.id) registre[mod.meta.id] = mod;
    }
  }
  const mod = registre[id];
  if (!mod) throw new Error(`Composition inconnue dans les placements : ${id}`);
  return mod;
};

const propsPlacement = (p: PlacementMontage) => {
  const mod = composition(p.id);
  const props: Record<string, unknown> = {...(mod.meta.defaultProps ?? {}), ...(p.props ?? {})};
  if (p.mode === 'overlay') props.showPlate = false;
  return props;
};

const Base: React.FC<{props: MontageProps}> = ({props}) => {
  const k = props.fps / BASE_FPS;
  const versRt = (images: number) => images / k;
  const image = Math.round(useCurrentFrame() * k);
  const zoom = echelleZoom(props.zooms, image / props.fps);
  const etalonne = props.etalonnage !== false;
  if (etalonne && props.etalonnageProfil && props.etalonnageProfil !== 'studio-a') throw new Error('Profil caméra inconnu.');
  if (etalonne && props.etalonnageSha256 && props.etalonnageSha256 !== STUDIO_A_SHA256) throw new Error('Site Lambda Studio A à redéployer.');
  const VideoCamera = etalonne ? StudioAVideo : OffthreadVideo;
  const style: React.CSSProperties =
    zoom.echelle === 1
      ? {}
      : {
          transform: `scale(${zoom.echelle})`,
          transformOrigin: `${zoom.point[0] * 100}% ${zoom.point[1] * 100}%`,
        };
  return (
    <AbsoluteFill style={{...style, backgroundColor: 'black'}}>
      {props.segments.map((s, i) =>
        s.rush < 0 ? null : (
          <Sequence key={i} from={versRt(s.sortie)} durationInFrames={versRt(s.images)}>
            <VideoCamera
              src={props.rushs[s.rush]}
              trimBefore={versRt(s.debut)}
              muted
              toneMapped={false}
              delayRenderTimeoutInMilliseconds={600000}
              delayRenderRetries={2}
              style={{
                width: '100%',
                height: '100%',
                objectFit: 'contain',
              }}
            />
          </Sequence>
        ),
      )}
    </AbsoluteFill>
  );
};

const MontageFinal: React.FC<MontageProps> = (props) => {
  // Plein cadre d'abord, calques ensuite : un plein cadre ne masque jamais un calque.
  const ordre = [...props.placements].sort(
    (a, b) => Number(a.mode === 'overlay') - Number(b.mode === 'overlay'),
  );
  // Sous un plein cadre, la couche de base est invisible : on ne la lit pas (1 s par image en 4K).
  // Bornes arrondies comme rt.Sequence.
  const k = props.fps / BASE_FPS;
  const image = Math.round(useCurrentFrame() * k);
  const sousPleinCadre = props.placements.some((p) => {
    const debut = Math.round(p.at * BASE_FPS * k);
    return p.mode !== 'overlay' && image >= debut && image < debut + Math.round(p.dur * k);
  });
  return (
    <AbsoluteFill style={{backgroundColor: 'black'}}>
      {props.audioSeul || sousPleinCadre ? null : <Base props={props} />}
      {ordre.map((p, i) => {
        const Comp = composition(p.id).default;
        const duree = p.duree ?? composition(p.id).meta.durationInFrames;
        return (
          <Sequence key={i} from={p.at * BASE_FPS} durationInFrames={p.dur} name={p.id}>
            <Sequence from={-p.from} durationInFrames={duree}>
              <SfxMuetCtx.Provider value={Boolean(p.props?.sansBruitages)}>
                <Comp {...propsPlacement(p)} />
              </SfxMuetCtx.Provider>
            </Sequence>
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};

// Durée exacte en images réelles. Root.tsx multiplie par fps/30 puis arrondit au-dessus :
// on retire un millième d'image pour que l'arrondi retombe sur `images`.
// Les compositions à calculateMetadata (01b, 05b) sont résolues ici, une fois.
export const calculateMetadata: CalculateMetadataFunction<MontageProps> = async ({
  props,
  abortSignal,
  compositionId,
  isRendering,
}) => {
  const fps = Number(props.fps ?? BASE_FPS);
  const placements = await Promise.all(
    props.placements.map(async (p) => {
      const mod = composition(p.id);
      const calcul = mod.calculateMetadata ?? mod.meta.calculateMetadata;
      if (!calcul) return p;
      const brut = propsPlacement(p);
      const r = await calcul({props: brut, defaultProps: brut, abortSignal, compositionId, isRendering});
      return {...p, props: {...brut, ...(r?.props ?? {})}, duree: r?.durationInFrames ?? mod.meta.durationInFrames};
    }),
  );
  return {
    durationInFrames: ((props.images - 0.001) * BASE_FPS) / fps,
    props: {...props, placements},
  };
};

export const meta = {
  id: '00-montage-final',
  durationInFrames: 50,
  fps: BASE_FPS,
  description: 'Montage final 4K : coupes du monteur, zooms et motions en un seul rendu',
  defaultProps: {fps: 50, images: 50, rushs: [], segments: [], zooms: [], placements: []} as MontageProps,
  calculateMetadata,
};

export default MontageFinal;
