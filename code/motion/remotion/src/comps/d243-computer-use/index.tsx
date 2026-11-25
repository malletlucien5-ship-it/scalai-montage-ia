import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame} from '../../shared/rt';
import {Camera, CamKey, Cursor, CurKey, curAt} from '../../shared/ecranMac';
import {SfxCue, SfxTrack} from '../../shared/Sfx';
import {EcranChatGPT, C2X, C2Y, ZOOM, ZX, ZY, c2VersZ, zVersLarge} from '../d242-chatgpt-sombre/ChatGPTApp';
import {GlossyPill, GlossySpec} from '../d209-pro-tip/GlossyPill';

// d243 : Computer use + bouton astuce (notes v3 de Ruben, 02:54-02:57). Écran de Dan réf. 178,75-184,4 s,
// joué image pour image : clic sur « Settings » (179,0), survol de la barre latérale jusqu'à « Computer use »
// (clic 180,85), panneau des applications (Google Chrome, Microsoft Excel), panoramique vers le panneau (181,85-182,55),
// infobulle « Enable Computer Use », activation de « Any App » (183,1), notification verte (183,35).
// Bouton astuce en bas à droite (même bouton que d209, réf. 187 s). Profil : nom de Lucien.
const FPS = 30;
const T0 = 178.75;
const fr = (t: number) => Math.round((t - T0) * FPS);
const DUREE = fr(184.42);

const Z1: [number, number, number] = [ZOOM, -ZX, -ZY];
const C2: [number, number, number] = [ZOOM, -ZX + C2X, -ZY + C2Y];
const CAM: CamKey[] = [
  [0, ...Z1],
  [fr(181.85), ...Z1],
  [fr(182.3), ...C2, 'out'],
];

const L = (x: number, y: number) => zVersLarge(x, y);
const LC = (x: number, y: number) => {
  const [zx, zy] = c2VersZ(x, y);
  return zVersLarge(zx, zy);
};
const CLIC_SETTINGS = fr(179.0);
const CLIC_CU = fr(180.85);
const CLIC_ANY = fr(183.08);
const CUR: CurKey[] = [
  [0, ...L(255, 888)],
  [fr(179.4), ...L(255, 888)],
  [fr(180.15), ...L(328, 562)],
  [fr(180.7), ...L(332, 566)],
  [fr(181.4), ...L(375, 567)],
  [fr(181.85), ...L(560, 567)],
  [fr(182.25), ...LC(1515, 453)],
  [fr(182.45), ...LC(1491, 399)],
  [fr(182.75), ...LC(1431, 333)],
  [fr(183.0), ...LC(1418, 303)],
];

const PILL: GlossySpec = {text: 'Astuce', right: 1886, bottom: 984, h: 116, size: 56, padX: 66, radius: 24};

const ComputerUse: React.FC<{nom?: string; initiales?: string; libelle?: string; astuce?: boolean}> = ({
  nom = 'Lucien Mallet', initiales = 'LM', libelle = 'Pro Tip', astuce = true,
}) => {
  const f = useCurrentFrame();
  const c = curAt(CUR, f);
  const reglages = f >= CLIC_SETTINGS + 1;
  const computer = f >= CLIC_CU + 1;
  const press = (k: number) => interpolate(f, [k - 2, k, k + 3], [0, 1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const v = Math.hypot(curAt(CUR, f + 0.5).x - curAt(CUR, f - 0.5).x, curAt(CUR, f + 0.5).y - curAt(CUR, f - 0.5).y);
  const survol = !reglages ? undefined : f < fr(179.75) ? 'Connections' : f < fr(179.9) ? undefined : 'Computer use';
  return (
    <AbsoluteFill style={{background: '#03142b', overflow: 'hidden'}}>
      <Camera keys={CAM} f={f}>
        <EcranChatGPT
          e={{
            vue: reglages ? 'reglages' : 'accueil', nom, initiales,
            menu: 1, survolMenu: 3, survolProfil: 1,
            survolReglage: survol, actifReglage: computer ? 'Computer use' : undefined,
            panneau: computer ? 'computer' : 'general',
            anyOn: interpolate(f, [CLIC_ANY + 1, CLIC_ANY + 7], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}),
            survolAny: interpolate(f, [fr(182.55), fr(182.65)], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}),
            infobulle: f >= fr(182.65) && f < CLIC_ANY + 2 ? 1 : 0,
            toast: interpolate(f, [fr(183.3), fr(183.45)], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}),
          }}
        >
          <Cursor x={c.x} y={c.y} h={52} press={Math.max(press(CLIC_SETTINGS), press(CLIC_CU), press(CLIC_ANY))} blur={Math.min(6, v * 0.12)} />
        </EcranChatGPT>
      </Camera>
      {astuce && <GlossyPill p={{...PILL, text: libelle}} frame={f} />}
    </AbsoluteFill>
  );
};

const CUES: SfxCue[] = [
  {frame: 0, name: 'grave-apparition'},
  {frame: CLIC_SETTINGS, name: 'clic'},
  {frame: CLIC_CU, name: 'clic'},
  {frame: fr(181.85), name: 'whoosh-transition', gain: 0.6},
  {frame: CLIC_ANY, name: 'clic'},
  {frame: fr(183.3), name: 'notification'},
];

export const meta = {
  id: 'd243-computer-use',
  fps: FPS,
  durationInFrames: DUREE,
  defaultProps: {nom: 'Lucien Mallet', initiales: 'LM', libelle: 'Pro Tip', astuce: true},
  occurrences: [{ref: [178.75, 184.42] as [number, number], at: 182.0, from: 0, durationInFrames: DUREE, mode: 'plein' as const}],
};

const AvecSons: React.FC<{nom?: string; initiales?: string; libelle?: string; astuce?: boolean}> = (p) => (
  <>
    <ComputerUse {...p} />
    <SfxTrack cues={CUES} />
  </>
);
export default AvecSons;
export const cues = CUES;
