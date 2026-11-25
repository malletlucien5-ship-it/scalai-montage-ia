import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame} from '../../shared/rt';
import {Camera, CamKey, Cursor, CurKey, camBlur, curAt} from '../../shared/ecranMac';
import {SfxCue, SfxTrack} from '../../shared/Sfx';
import {EcranChatGPT, ZOOM, ZX, ZY, zVersLarge} from './ChatGPTApp';

// d242 : interface ChatGPT sombre (notes v3 de Ruben, 02:39-02:50 : barre latérale, profil en bas,
// « Where should we begin? », champ de saisie, navigation). Écran de Dan réf. 177,8-178,95 s :
// vue large de l'application, clic sur le profil, zoom vers le bas gauche (0,45 s), survol de « Settings ».
// Le plan de Dan dure 1,15 s ; la note couvre 11 s : la vue large est tenue pendant que le curseur parcourt
// l'interface (champ de saisie, barre latérale), puis l'action de Dan est jouée à sa vitesse.
// Profil : nom de Lucien. Suite directe : d243-computer-use (clic sur « Settings »).
const FPS = 30;
const DUREE = 330;
const CLIC = 266; // clic sur le profil (réf. 177,8)

const LARGE: [number, number, number] = [1, 0, 0];
const Z1: [number, number, number] = [ZOOM, -ZX, -ZY];
const CAM: CamKey[] = [
  [0, ...LARGE],
  [CLIC, ...LARGE],
  [CLIC + 13, ...Z1, 'out'], // zoom mesuré 177,8 -> 178,25
];

const settings = zVersLarge(255, 888); // pointe sur « Settings » (réf. 178,9)
const CUR: CurKey[] = [
  [0, 1240, 640],
  [24, 1240, 640],
  [62, 1010, 487], // champ « Ask ChatGPT »
  [100, 1010, 487],
  [140, 330, 155], // « New chat »
  [165, 330, 158],
  [196, 300, 236], // « Explore »
  [214, 300, 236],
  [CLIC - 4, 348, 1006], // profil
  [CLIC + 30, 348, 1008],
  [CLIC + 50, settings[0], settings[1]],
];

const ChatGPTSombre: React.FC<{nom?: string; initiales?: string}> = ({nom = 'Lucien Mallet', initiales = 'LM'}) => {
  const f = useCurrentFrame();
  const menu = interpolate(f, [CLIC, CLIC + 5], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const c = curAt(CUR, f);
  const surv = f >= 140 && f < 190 ? 'New chat' : f >= 196 && f < 222 ? 'Explore' : undefined;
  const survolMenu = f >= CLIC + 44 ? 3 : -1;
  const press = interpolate(f, [CLIC - 2, CLIC, CLIC + 3], [0, 1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const vitesse = Math.hypot(curAt(CUR, f + 0.5).x - curAt(CUR, f - 0.5).x, curAt(CUR, f + 0.5).y - curAt(CUR, f - 0.5).y);
  return (
    <AbsoluteFill style={{background: '#03142b', overflow: 'hidden'}}>
      <Camera keys={CAM} f={f}>
        <EcranChatGPT
          e={{
            vue: 'accueil', nom, initiales, menu, survolMenu,
            survolProfil: f >= CLIC - 6 ? 1 : 0,
            survolAccueil: surv,
            curseurTexte: Math.floor(f / 16) % 2 === 0 ? 1 : 0,
          }}
        >
          <Cursor x={c.x} y={c.y} h={52} press={press} blur={Math.min(6, vitesse * 0.12) + camBlur(CAM, f) * 0} />
        </EcranChatGPT>
      </Camera>
    </AbsoluteFill>
  );
};

const CUES: SfxCue[] = [
  {frame: 0, name: 'whoosh-transition'},
  {frame: CLIC, name: 'clic'},
];

// Temps cible (`at`) : convention dan2 (référence -> voix coupée par interpolation entre d208 et d209).
export const meta = {
  id: 'd242-chatgpt-sombre',
  fps: FPS,
  durationInFrames: DUREE,
  defaultProps: {nom: 'Lucien Mallet', initiales: 'LM'},
  occurrences: [{ref: [177.8, 178.95] as [number, number], at: 180.42, from: 0, durationInFrames: DUREE, mode: 'plein' as const}],
};

const AvecSons: React.FC<{nom?: string; initiales?: string}> = (p) => (
  <>
    <ChatGPTSombre {...p} />
    <SfxTrack cues={CUES} />
  </>
);
export default AvecSons;
export const cues = CUES;
