import React from 'react';
import {AbsoluteFill, Easing, Img, interpolate, staticFile, useCurrentFrame} from '../../shared/rt';
import {siClaude} from 'simple-icons';
import {INTER} from '../../shared/fonts';
import {SfxTrack, SfxCue} from '../../shared/Sfx';

// 40 : terminal Claude Code et téléphone qui valide à distance.
// Plage de référence 710,68 s à 719,45 s (263 images).
export const meta = {id: '40-terminal-telephone', durationInFrames: 263, fps: 30,
  occurrences: [{ref: [710.68, 719.45], from: 0, durationInFrames: 263, mode: 'plein'}],
};

// SF Mono (police système macOS, famille masquée « .SF NS Mono ») chargée depuis une copie locale
const MONO = 'SFMonoLocal, Menlo, monospace';
const FONT_CSS = `@font-face { font-family: 'SFMonoLocal'; src: url('${staticFile('40/SFMono.ttf')}') format('truetype'); font-weight: 100 900; }`;
const cl = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

// Minutage relevé image par image (s)
const TM = {l1: 0.0, l2: 0.6, l3: 0.85, cursor: 1.4, q: 2.2, a: 3.45, ok: 4.4, gen: 5.0, code1: 6.6, code2: 7.6};

const CODE1: [string, string][] = [
  ['async function ', '#7B5CC4'],
  ['handleAuth', '#5B7BE0'],
  ['(req, res) {', '#C8C8CC'],
];
const CODE2: [string, string][] = [
  ['  const ', '#7B5CC4'],
  ['token = ', '#C8C8CC'],
  ['verifyJWT', '#5B7BE0'],
  ["(req.headers['authorization']);", '#C8C8CC'],
];

// Écrit une ligne colorée caractère par caractère
const Typed: React.FC<{parts: [string, string][]; n: number}> = ({parts, n}) => {
  let left = n;
  return (
    <>
      {parts.map(([s, c], i) => {
        const k = Math.max(0, Math.min(s.length, left));
        left -= s.length;
        return (
          <span key={i} style={{color: c}}>
            {s.slice(0, k)}
          </span>
        );
      })}
    </>
  );
};

const Star: React.FC<{s: number}> = ({s}) => (
  <svg width={s} height={s} viewBox="0 0 24 24">
    <path d={siClaude.path} fill="#E07A5F" />
  </svg>
);

export default function TerminalTelephone() {
  const f = useCurrentFrame();
  const t = f / 30;
  const fade = (a: number, d = 0.2) => interpolate(t, [a, a + d], [0, 1], cl);
  const cursorOn = t >= TM.cursor && (t - TM.cursor) % 1.0 < 0.4;
  const q = interpolate(t, [TM.q, TM.q + 0.25], [0, 1], {...cl, easing: Easing.out(Easing.cubic)});
  const a = interpolate(t, [TM.a, TM.a + 0.3], [0, 1], {...cl, easing: Easing.out(Easing.cubic)});
  const ok = fade(TM.ok);
  const gen = fade(TM.gen);
  const c1 = Math.floor(interpolate(t, [TM.code1, TM.code1 + 0.8], [0, 37], cl));
  const c2 = Math.floor(interpolate(t, [TM.code2, TM.code2 + 1.0], [0, 44], {extrapolateLeft: 'clamp'}));

  const line = (y: number, op: number, children: React.ReactNode) => (
    <div style={{position: 'absolute', left: 30, top: y - 11, fontFamily: MONO, fontSize: 16.4, fontWeight: 300, opacity: op, whiteSpace: 'pre'}}>{children}</div>
  );

  return (
    <AbsoluteFill style={{fontFamily: INTER}}>
      <SfxTrack cues={cuesExportees} />
      <style>{FONT_CSS}</style>
      <Img src={staticFile('40/bg.jpg')} style={{position: 'absolute', width: 1920, height: 1080}} />

      {/* ---------- terminal ---------- */}
      <div
        style={{
          position: 'absolute',
          left: 34,
          top: 230,
          width: 1385,
          height: 618,
          borderRadius: 18,
          border: '1.5px solid rgba(215,218,225,0.72)',
          background: '#121212',
          overflow: 'hidden',
          boxShadow: '0 20px 60px rgba(0,0,0,0.5)',
        }}
      >
        <div style={{position: 'absolute', left: 0, top: 0, right: 0, height: 40, background: '#252525', borderBottom: '1px solid #333'}} />
        {['#E0443E', '#DEA123', '#1AAB29'].map((c, i) => (
          <div key={c} style={{position: 'absolute', left: 16 + i * 21.5, top: 12, width: 12, height: 12, borderRadius: 6, background: c}} />
        ))}
        <div style={{position: 'absolute', left: 0, right: 0, top: 11, textAlign: 'center', color: '#8E8E93', fontSize: 13.5}}>claude-code · bash</div>

        {/* contenu, coordonnées locales = écran - (34, 230) */}
        {line(78, fade(TM.l1), (
          <>
            <span style={{color: '#5E5E62'}}>$ </span>
            <span style={{color: '#5F63D8'}}>claude</span>
            <span style={{color: '#C8C8CC'}}> --remote-control </span>
            <span style={{color: '#5F63D8'}}>/remote</span>
          </>
        ))}
        {line(115, fade(TM.l2), <span style={{color: '#56565A'}}>› Connecté à l’app Claude sur ton téléphone</span>)}
        {line(152, fade(TM.l3), <span style={{color: '#56565A'}}>› En attente de validation...</span>)}

        {/* ligne du curseur : elle descend sous la validation */}
        {t >= TM.cursor ? (
          line(t >= TM.ok ? 279 : 189, 1, (
            <>
              <span style={{color: '#5E5E62'}}>›</span>
              {cursorOn ? <span style={{display: 'inline-block', width: 7, height: 15, marginLeft: 9, background: '#E8E8EA', verticalAlign: 'middle'}} /> : null}
            </>
          ))
        ) : null}

        {/* validation */}
        {ok > 0 ? (
          <div style={{position: 'absolute', left: 29, top: 214, width: 1332, height: 43, background: '#15241B', opacity: ok}}>
            <div style={{position: 'absolute', left: 0, top: 0, width: 4, height: 43, background: '#27A566'}} />
            <div style={{position: 'absolute', left: 19, top: 11, fontFamily: MONO, fontSize: 16.4, fontWeight: 300, color: '#D6D6DA', whiteSpace: 'pre'}}>
              Validé par l’utilisateur : « Oui, continue d’écrire le module d’auth. »
            </div>
          </div>
        ) : null}

        {/* génération */}
        {gen > 0 ? (
          <div style={{opacity: gen}}>
            {[0, 1, 2].map((i) => {
              const ph = ((t - TM.gen) / 0.6) * Math.PI * 2 - i * 2.1;
              const b = 0.3 + 0.7 * Math.max(0, Math.sin(ph));
              return (
                <div
                  key={i}
                  style={{position: 'absolute', left: 276, top: 328 + i * 24, width: 8, height: 8, borderRadius: 4, background: '#5B5FD6', opacity: b}}
                />
              );
            })}
            <div style={{position: 'absolute', left: 161, top: 422, fontFamily: MONO, fontSize: 16.4, fontWeight: 300, color: '#5A5FD0'}}>Génération du code</div>
          </div>
        ) : null}

        {c1 > 0 ? line(495, 1, <Typed parts={CODE1} n={c1} />) : null}
        {c2 > 0 ? line(522, 1, <Typed parts={CODE2} n={c2} />) : null}
      </div>

      {/* ---------- téléphone ---------- */}
      <div
        style={{
          position: 'absolute',
          left: 1447,
          top: 130,
          width: 439,
          height: 835,
          borderRadius: 58,
          border: '2.5px solid rgba(238,238,242,0.9)',
          background: 'linear-gradient(180deg, #161616 0%, #121212 60%, #141111 100%)',
          overflow: 'hidden',
          boxShadow: '0 20px 60px rgba(0,0,0,0.5)',
        }}
      >
        {/* reflet orangé bas droite */}
        <div style={{position: 'absolute', right: -60, bottom: -40, width: 160, height: 220, background: 'radial-gradient(closest-side, rgba(200,80,40,0.14), rgba(200,80,40,0))'}} />
        <div style={{position: 'absolute', left: 176, top: 18, width: 94, height: 20, borderRadius: 10, background: '#0A0A0A'}} />
        <div style={{position: 'absolute', left: 28, top: 56}}>
          <Star s={32} />
        </div>
        <div style={{position: 'absolute', left: 73, top: 58, color: '#F2F2F4', fontSize: 21, fontWeight: 600}}>Claude</div>
        <div style={{position: 'absolute', left: 408, top: 65, width: 14, height: 14, borderRadius: 7, background: '#1F9E6E'}} />
        <div style={{position: 'absolute', left: 0, right: 0, top: 104, height: 1, background: '#2A2A2A'}} />

        {q > 0 ? (
          <div
            style={{
              position: 'absolute',
              left: 22,
              top: 132,
              width: 320,
              height: 91,
              borderRadius: 28,
              border: '1.5px solid #4A4A4E',
              background: '#191919',
              opacity: q,
              transform: `translateY(${(1 - q) * 14}px)`,
              color: '#F2F2F4',
              fontSize: 18.5,
              lineHeight: '29px',
              padding: '15px 22px',
              boxSizing: 'border-box',
            }}
          >
            Je continue d’écrire le module d’auth ?
          </div>
        ) : null}

        {a > 0 ? (
          <div
            style={{
              position: 'absolute',
              left: 102,
              top: 306,
              width: 324,
              height: 90,
              borderRadius: 26,
              background: 'linear-gradient(135deg, #6A86F7 0%, #4F68EA 100%)',
              boxShadow: '0 0 30px rgba(80,110,240,0.35)',
              opacity: a,
              transform: `translateX(${(1 - a) * -150}px)`,
              color: '#fff',
              fontSize: 18.5,
              lineHeight: '29px',
              padding: '15px 22px',
              boxSizing: 'border-box',
            }}
          >
            Oui, continue d’écrire le module d’auth.
          </div>
        ) : null}

        <div style={{position: 'absolute', left: 0, right: 0, top: 756, height: 1, background: '#262626'}} />
        {t < TM.a + 0.1 ? (
          <div style={{position: 'absolute', left: 20, top: 774, width: 345, height: 45, borderRadius: 23, border: '1.5px solid #3A3A3C', background: '#161616'}}>
            <div style={{position: 'absolute', left: 22, top: 11, color: '#6A6A6E', fontSize: 18}}>Message</div>
          </div>
        ) : (
          <div style={{position: 'absolute', left: 20, top: 784, width: 345, height: 25, borderRadius: 13, border: '1.5px solid #3A3A3C', background: '#161616'}} />
        )}
        <div style={{position: 'absolute', left: 380, top: 773, width: 48, height: 48, borderRadius: 24, background: '#C0502A', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
          <svg width={22} height={22} viewBox="0 0 24 24">
            <path d="M12 19V5M6 11l6-6 6 6" stroke="#fff" strokeWidth={2.4} fill="none" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>
      </div>
    </AbsoluteFill>
  );
}

// Signaux sonores exportés pour la bibliothèque (cloud/cues_globaux.py).
const cuesExportees: SfxCue[] = [
        {frame: 70, name: 'notification'}, // question sur le téléphone
        {frame: 104, name: 'clic'}, // validation envoyée depuis le téléphone
        {frame: 199, name: 'frappe-clavier', durationInFrames: 23}, // ligne de code 1 (6,62 s à 7,4 s)
        {frame: 229, name: 'frappe-clavier', durationInFrames: 29}, // ligne de code 2 (7,62 s à 8,6 s)
      ];
export const cues = cuesExportees;
