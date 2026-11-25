import React from 'react';
import {AbsoluteFill, Easing, interpolate, useCurrentFrame} from '../../shared/rt';
import {INTER_L} from '../../shared/localFonts';
import {Plate} from '../../shared/Plate';

// d234 : texte des notes du monteur (réf. 12,7-16,05, même emplacement que d203 occ. 0).
// Blanc, gras, apparition lettre après lettre ; « MEILLEURS DU MOMENT » souligné en bleu (couleurs d203).
// Dégradé noir du bas et ligne de base de d203 (2 lignes : 812 et 914).
const FPS = 30;
const LIGNES = ['VOUS AVEZ BESOIN DE SAVOIR LESQUELS', 'SONT LES MEILLEURS DU MOMENT'];
const SOULIGNE = 'MEILLEURS DU MOMENT';
const BASES = [812, 914];
const TAILLE = 68;
const FRAPPE: [number, number] = [8, 62]; // images : première et dernière lettre
const GRADIENT =
  'linear-gradient(180deg, rgba(0,0,0,0) 50%, rgba(0,0,0,0.09) 60%, rgba(0,0,0,0.23) 69.5%, rgba(0,0,0,0.38) 78.7%, rgba(0,0,0,0.5) 88%, rgba(0,0,0,0.6) 100%)';
const TOTAL = LIGNES.join('').length;

const Texte: React.FC = () => {
  const f = useCurrentFrame();
  const n = Math.floor(interpolate(f, FRAPPE, [1, TOTAL], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}));
  const ul = interpolate(f, [FRAPPE[1] + 2, FRAPPE[1] + 16], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic)});
  const g = interpolate(f, [0, 20], [0, 1], {extrapolateRight: 'clamp', easing: Easing.out(Easing.quad)});
  let deja = 0;
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{background: GRADIENT, opacity: g}} />
      {LIGNES.map((ligne, li) => {
        const visibles = Math.max(0, Math.min(ligne.length, n - deja));
        deja += ligne.length;
        const i = ligne.indexOf(SOULIGNE);
        const parts = i < 0 ? [ligne] : [ligne.slice(0, i), SOULIGNE, ligne.slice(i + SOULIGNE.length)];
        let k = 0;
        return (
          <div key={li} style={{position: 'absolute', left: 0, right: 0, top: BASES[li] - TAILLE * 0.97, display: 'flex', justifyContent: 'center'}}>
            <div style={{fontFamily: INTER_L, fontWeight: 800, fontSize: TAILLE, color: '#fff', whiteSpace: 'pre', letterSpacing: 0.5, textShadow: '0 3px 10px rgba(0,0,0,0.45)'}}>
              {parts.map((p, pi) => {
                const debut = k;
                k += p.length;
                const lettres = p.split('').map((c, ci) => (
                  <span key={ci} style={{opacity: debut + ci < visibles ? 1 : 0}}>{c}</span>
                ));
                if (p !== SOULIGNE) return <span key={pi}>{lettres}</span>;
                return (
                  <span key={pi} style={{position: 'relative', display: 'inline-block'}}>
                    {lettres}
                    {ul > 0 ? (
                      <span style={{position: 'absolute', left: 0, top: TAILLE * 0.97 + 13, height: 15, width: `${ul * 100}%`, minWidth: 15, borderRadius: 8, background: 'linear-gradient(180deg, #00BAEF 0%, #00C4EC 55%, #00C8EE 100%)', boxShadow: '0 3px 8px rgba(0,0,0,0.35)'}} />
                    ) : null}
                  </span>
                );
              })}
            </div>
          </div>
        );
      })}
    </AbsoluteFill>
  );
};

const TexteMeilleurs: React.FC<{showPlate?: boolean}> = ({showPlate = true}) => (
  <AbsoluteFill style={{overflow: 'hidden'}}>
    <Plate show={showPlate} />
    <Texte />
  </AbsoluteFill>
);

export const meta = {
  id: 'd234-texte-meilleurs',
  fps: FPS,
  durationInFrames: 93,
  defaultProps: {showPlate: true},
  occurrences: [{ref: [12.7, 16.05] as [number, number], from: 0, durationInFrames: 93, mode: 'overlay' as const}],
};
export default TexteMeilleurs;
