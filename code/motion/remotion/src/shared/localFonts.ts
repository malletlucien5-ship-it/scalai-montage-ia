import {continueRender, delayRender, staticFile} from './rt';

// Polices servies depuis public/fonts : même rendu en local et sur Lambda, sans Google Fonts.
export const INTER_L = 'InterL';
export const PLAYFAIR_L = 'PlayfairL';
export const MONO_L = 'MonoL';
// Substituts métriquement compatibles des polices système absentes sur Lambda (pas de glyphe manquant) :
// Gelasio pour Georgia, Arimo pour Arial/Helvetica, GFS Didot pour Didot. Fontes variables (graisses 400-700).
export const GEORGIA_L = 'GeorgiaL';
export const ARIAL_L = 'ArialL';
export const DIDOT_L = 'DidotL';

const FILES: [string, string, string, string][] = [];
for (const w of ['400', '500', '600', '700', '800', '900']) {
  FILES.push([INTER_L, 'normal', w, `Inter-normal-${w}`]);
}
for (const w of ['400', '500', '600']) {
  FILES.push([PLAYFAIR_L, 'italic', w, `PlayfairDisplay-italic-${w}`]);
}
for (const w of ['400', '500', '700']) {
  FILES.push([MONO_L, 'normal', w, `JetBrainsMono-normal-${w}`]);
}

// [famille, style, graisses, fichier sans sous-ensemble, sous-ensembles disponibles]
const VARIABLES: [string, string, string, string, string[]][] = [
  [GEORGIA_L, 'normal', '400 700', 'Gelasio-normal', ['latin', 'latin-ext']],
  [GEORGIA_L, 'italic', '400 700', 'Gelasio-italic', ['latin', 'latin-ext']],
  [ARIAL_L, 'normal', '400 700', 'Arimo-normal', ['latin', 'latin-ext']],
  [DIDOT_L, 'normal', '400', 'GFSDidot-normal', ['latin']],
];
const ENTREES: [string, string, string, string, string[]][] = [
  ...FILES.map(([f, st, w, b]) => [f, st, w, b, ['latin', 'latin-ext']] as [string, string, string, string, string[]]),
  ...VARIABLES,
];

let started = false;
export const ensureLocalFonts = () => {
  if (started || typeof document === 'undefined') return;
  started = true;
  const handle = delayRender('polices locales');
  const faces: Promise<FontFace>[] = [];
  for (const [family, style, weight, base, subsets] of ENTREES) {
    for (const subset of subsets) {
      const face = new FontFace(family, `url(${staticFile(`fonts/${base}-${subset}.woff2`)}) format('woff2')`, {
        style,
        weight,
        unicodeRange:
          subset === 'latin'
            ? 'U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD'
            : 'U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+0304, U+0308, U+0329, U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C0, U+2113, U+2C60-2C7F, U+A720-A7FF',
      });
      faces.push(face.load().then((f) => {
        (document.fonts as unknown as {add: (face: FontFace) => void}).add(f);
        return f;
      }));
    }
  }
  Promise.all(faces).then(() => continueRender(handle)).catch((e) => {
    console.error(e);
    continueRender(handle);
  });
};
ensureLocalFonts();
