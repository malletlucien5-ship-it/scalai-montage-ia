import React from 'react';
import {Audio, Sequence, getInputProps, interpolate, staticFile} from './rt';

// Kit de bruitages Epidemic Sound. Règles de placement : ~/CODE/martell-motion/SFX-REGLES.md
export type SfxName =
  | 'nappe-ecran-titre'
  | 'impact-chapitre'
  | 'montee-chapitre'
  | 'whoosh-transition'
  | 'grave-apparition'
  | 'clic'
  | 'frappe-clavier'
  | 'pop'
  | 'notification';

const VOLUME: Record<SfxName, number> = {
  'impact-chapitre': 0.9,
  'nappe-ecran-titre': 0.7,
  'montee-chapitre': 0.6,
  'whoosh-transition': 0.5,
  'grave-apparition': 0.55,
  notification: 0.45,
  pop: 0.4,
  clic: 0.5,
  'frappe-clavier': 0.3,
};

// frame : image de départ dans la composition. durationInFrames : coupe le son (utile pour la frappe).
export type SfxCue = {frame: number; name: SfxName; durationInFrames?: number; gain?: number};

// sfxBibliotheque (input props du rendu) : les bruitages viennent de la bibliothèque validée, mixés dans le
// conteneur depuis les `cues` exportées (cloud/cues_globaux.py). Les pistes internes se taisent, sauf `force`.
const bibliothequeActive = (): boolean => {
  try {
    return Boolean((getInputProps() as {sfxBibliotheque?: boolean}).sfxBibliotheque);
  } catch {
    return false;
  }
};

// Placement muet (prop `sansBruitages` dans 00-montage-final) : les sons viennent des notes du monteur.
export const SfxMuetCtx = React.createContext(false);

export const SfxTrack: React.FC<{cues: SfxCue[]; force?: boolean}> = ({cues, force}) =>
  React.useContext(SfxMuetCtx) || (bibliothequeActive() && !force) ? null : (
  <>
    {cues.map((c, i) => {
      const vol = VOLUME[c.name] * (c.gain ?? 1);
      const d = c.durationInFrames;
      return (
        <Sequence key={i} from={Math.max(0, Math.round(c.frame))} durationInFrames={d} layout="none">
          <Audio
            src={staticFile(`sfx/${c.name}.wav`)}
            volume={d ? (f) => interpolate(f, [0, Math.max(1, d - 2), d], [vol, vol, 0], {extrapolateRight: 'clamp'}) : vol}
          />
        </Sequence>
      );
    })}
  </>
  );
