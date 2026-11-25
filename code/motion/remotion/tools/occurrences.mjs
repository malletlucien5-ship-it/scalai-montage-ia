// Lit le champ meta.occurrences de chaque composition et l'écrit dans ../edit/occurrences.json.
// Aucun rendu : esbuild compile chaque index.tsx pour Node, les polices Google sont remplacées par un bouchon.
import {build} from 'esbuild';
import {readdirSync, writeFileSync, mkdirSync} from 'node:fs';
import {createRequire} from 'node:module';
import path from 'node:path';

const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const comps = path.join(root, 'src/comps');
const tmp = path.join(root, '.occ-tmp');
mkdirSync(tmp, {recursive: true});
const require = createRequire(import.meta.url);

const stubFonts = {
  name: 'stub-fonts',
  setup(b) {
    b.onResolve({filter: /^@remotion\/google-fonts/}, (a) => ({path: a.path, namespace: 'stub'}));
    b.onLoad({filter: /.*/, namespace: 'stub'}, () => ({
      contents: 'export const loadFont = () => ({fontFamily: "stub", waitUntilDone: () => Promise.resolve()});',
      loader: 'js',
    }));
  },
};

const out = {};
for (const dir of readdirSync(comps).sort()) {
  const entry = path.join(comps, dir, 'index.tsx');
  const file = path.join(tmp, `${dir}.cjs`);
  try {
    await build({
      entryPoints: [entry], bundle: true, platform: 'node', format: 'cjs', outfile: file,
      external: ['react', 'react-dom', 'remotion', '@remotion/*'], plugins: [stubFonts], logLevel: 'silent',
      loader: {'.png': 'empty', '.jpg': 'empty', '.svg': 'text', '.ttf': 'empty'},
    });
    const m = require(file);
    out[m.meta.id] = {durationInFrames: m.meta.durationInFrames, occurrences: m.meta.occurrences ?? null};
  } catch (e) {
    out[dir] = {erreur: String(e.message).split('\n')[0]};
  }
}
writeFileSync(path.join(root, '../edit/occurrences.json'), JSON.stringify(out, null, 1));
const bad = Object.entries(out).filter(([, v]) => !v.occurrences);
console.log(Object.keys(out).length, 'compositions ;', bad.length, 'sans occurrences :', bad.map(([k, v]) => k + (v.erreur ? ` (${v.erreur})` : '')).join(', '));
