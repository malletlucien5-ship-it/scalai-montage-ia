import React from 'react';
import {AbsoluteFill, Easing, Sequence, interpolate, useCurrentFrame} from '../../shared/rt';
import {INTER_L} from '../../shared/localFonts';
import {Plate} from '../../shared/Plate';
import {SfxTrack, SfxCue} from '../../shared/Sfx';

// d226 : pilule de verre fumé centrée en bas « Cliquez sur le lien en description. » (sans le QR code de Dan).
// Réf. 1180,4 s : le bas de l'image s'assombrit (même dégradé que les sous-titres), puis à 1180,87 s la pilule
// monte depuis le bas du cadre (décroissance x0,87 par image) ; coupe franche à ~1185,1 s.
// Géométrie relevée à 1183 s (1920x1080) : boîte 305..1615 x 838..975 (137 px), centrée, rayon ~28,
// liseré clair 1,5 px ; texte gras blanc capitale 36 px (~50 px), marges ~46 px.
// Dégradé vertical relevé : #737881 en haut, creux #131C28 à 57 %, #454B56 en bas ; côté droit plus bleu (#264254).
// Cible : « il y a un lien dans la description » (1262,47) -> fin de « ... vous et moi, » (1266,25).
const FPS = 30;
const OCC = {ref: [1180.4, 1185.1] as [number, number], start: 1262.1, end: 1266.3};
const DUR = Math.round((OCC.end - OCC.start) * FPS);
const PILL_IN = 11; // image d'apparition de la pilule après le début de l'assombrissement (~1262,47)
const TOP = 838;
const H = 137;

const GRADIENT =
  'linear-gradient(180deg, rgba(0,0,0,0) 50%, rgba(0,0,0,0.04) 55.5%, rgba(0,0,0,0.09) 60%, rgba(0,0,0,0.15) 65%, rgba(0,0,0,0.23) 69.5%, rgba(0,0,0,0.31) 74%, rgba(0,0,0,0.38) 78.7%, rgba(0,0,0,0.42) 83.3%, rgba(0,0,0,0.5) 88%, rgba(0,0,0,0.54) 92.6%, rgba(0,0,0,0.58) 97.2%, rgba(0,0,0,0.6) 100%)';

const Cta: React.FC = () => {
  const f = useCurrentFrame();
  const g = interpolate(f, [0, 20], [0, 1], {extrapolateRight: 'clamp', easing: Easing.out(Easing.quad)});
  const fp = f - PILL_IN;
  const dy = fp >= 0 ? (1080 - TOP + 8) * Math.pow(0.87, fp) : 0;
  const blur = fp >= 0 && fp < 5 ? 2.5 * (1 - fp / 5) : 0;
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{background: GRADIENT, opacity: g}} />
      {fp >= 0 ? (
        <div style={{position: 'absolute', left: 0, right: 0, top: TOP, display: 'flex', justifyContent: 'center', transform: `translateY(${dy}px)`, filter: blur > 0.1 ? `blur(${blur}px)` : undefined}}>
          <div
            style={{
              height: H,
              boxSizing: 'border-box',
              padding: '0 48px 0 46px',
              display: 'flex',
              alignItems: 'center',
              borderRadius: 28,
              border: '1.5px solid rgba(200,206,214,0.72)',
              background:
                'linear-gradient(90deg, rgba(0,0,0,0) 55%, rgba(30,70,100,0.35) 100%), linear-gradient(180deg, #7D828B 0%, #737881 5%, #646D74 12%, #4E575E 20%, #414A51 26%, #363F49 33%, #2A343D 41%, #1E2730 49%, #131C28 57%, #1C252F 63%, #282E38 70%, #313742 78%, #3B414B 88%, #454B56 100%)',
              boxShadow: '0 0 0 1px rgba(0,0,0,0.35), inset 0 1px 0 rgba(255,255,255,0.2), 0 8px 24px rgba(0,0,0,0.35)',
            }}
          >
            <span style={{fontFamily: INTER_L, fontWeight: 800, fontSize: 50, lineHeight: 1, color: '#FFFFFF', whiteSpace: 'pre', letterSpacing: '-0.005em', textShadow: '0 2px 4px rgba(0,0,0,0.45)'}}>
              Cliquez sur le lien en description.
            </span>
          </div>
        </div>
      ) : null}
    </AbsoluteFill>
  );
};

// grave-apparition sur la première image où la pilule dépasse du bas du cadre.
const CUES: SfxCue[] = [{frame: PILL_IN, name: 'grave-apparition'}];

const CtaLien: React.FC<{showPlate?: boolean}> = ({showPlate = true}) => (
  <AbsoluteFill style={{overflow: 'hidden'}}>
    <Plate show={showPlate} />
    <Sequence from={0} durationInFrames={DUR} layout="none">
      <Cta />
    </Sequence>
    <SfxTrack cues={CUES} />
  </AbsoluteFill>
);

export const meta = {
  id: 'd226-cta-lien',
  fps: FPS,
  durationInFrames: DUR,
  defaultProps: {showPlate: true},
  occurrences: [{ref: OCC.ref, at: OCC.start, from: 0, durationInFrames: DUR, mode: 'plein' as const}],
};
export default CtaLien;

// Signaux sonores exportés pour la bibliothèque (cloud/cues_globaux.py).
export const cues = CUES;
