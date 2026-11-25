// Images fixes de faq3-v4 avec un seul bundle : node tools/stills-faq3v4.mjs PROPS.json DOSSIER t1 t2 ...
import {bundle} from '@remotion/bundler';
import {renderStill, selectComposition} from '@remotion/renderer';
import fs from 'node:fs';
import path from 'node:path';

const [propsPath, out, ...ts] = process.argv.slice(2);
const inputProps = JSON.parse(fs.readFileSync(propsPath, 'utf8'));
fs.mkdirSync(out, {recursive: true});
const serveUrl = await bundle({entryPoint: path.resolve('src/index.ts')});
const composition = await selectComposition({serveUrl, id: 'faq3-v4', inputProps});
for (const t of ts) {
  const frame = Math.min(composition.durationInFrames - 1, Math.round(Number(t) * inputProps.fps));
  const output = path.join(out, `t${Number(t).toFixed(2).padStart(7, '0')}.png`);
  await renderStill({serveUrl, composition, frame, output, inputProps, scale: 0.5});
  console.log(output);
}
