#!/usr/bin/env node
// Extrait meta.occurrences sans lancer Remotion Studio.

import {
  existsSync,
  mkdirSync,
  readdirSync,
  rmSync,
  writeFileSync,
} from 'node:fs';
import {createRequire} from 'node:module';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

function value(flag, fallback = null) {
  const position = process.argv.indexOf(flag);
  return position >= 0 ? process.argv[position + 1] : fallback;
}

const remotion = path.resolve(value('--remotion', process.cwd()));
const output = path.resolve(
  value('--output', path.join(remotion, '..', 'edit', 'occurrences.json')),
);
const comps = path.join(remotion, 'src', 'comps');
const temp = path.join(remotion, '.occurrences-tmp');

if (!existsSync(comps)) {
  throw new Error(`dossier de compositions absent: ${comps}`);
}

mkdirSync(temp, {recursive: true});
mkdirSync(path.dirname(output), {recursive: true});
const require = createRequire(path.join(remotion, 'package.json'));
const {build} = require('esbuild');
const stubFonts = {
  name: 'stub-fonts',
  setup(builder) {
    builder.onResolve({filter: /^@remotion\/google-fonts/}, (args) => ({
      path: args.path,
      namespace: 'stub',
    }));
    builder.onLoad({filter: /.*/, namespace: 'stub'}, () => ({
      contents:
        'export const loadFont = () => ({fontFamily: "stub", waitUntilDone: () => Promise.resolve()});',
      loader: 'js',
    }));
  },
};

const result = {};
for (const directory of readdirSync(comps).sort()) {
  const entry = path.join(comps, directory, 'index.tsx');
  if (!existsSync(entry)) continue;
  const compiled = path.join(temp, `${directory}.cjs`);
  try {
    await build({
      entryPoints: [entry],
      bundle: true,
      platform: 'node',
      format: 'cjs',
      outfile: compiled,
      external: ['react', 'react-dom', 'remotion', '@remotion/*'],
      plugins: [stubFonts],
      logLevel: 'silent',
      loader: {
        '.png': 'empty',
        '.jpg': 'empty',
        '.jpeg': 'empty',
        '.webp': 'empty',
        '.svg': 'text',
        '.ttf': 'empty',
      },
    });
    delete require.cache[compiled];
    const moduleValue = require(compiled);
    const meta = moduleValue.meta ?? {};
    const id = meta.id ?? directory;
    result[id] = {
      durationInFrames: meta.durationInFrames ?? null,
      fps: meta.fps ?? null,
      description: meta.description ?? null,
      occurrences: meta.occurrences ?? null,
    };
  } catch (error) {
    result[directory] = {
      error: String(error.message).split('\n')[0],
      occurrences: null,
    };
  }
}

writeFileSync(output, `${JSON.stringify(result, null, 2)}\n`);
rmSync(temp, {recursive: true, force: true});
const missing = Object.entries(result).filter(([, item]) => !item.occurrences);
console.log(
  JSON.stringify({
    compositions: Object.keys(result).length,
    sans_occurrences: missing.map(([id]) => id),
    output,
  }),
);
