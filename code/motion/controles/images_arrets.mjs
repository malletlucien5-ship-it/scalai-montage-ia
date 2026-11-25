// Images fixes du panneau, avant tout rendu vidéo. Lancé par controles/arrets.py.
// node controles/images_arrets.mjs PLAN.json REMOTION_DIR SORTIE COMPOSITION f1,f2,...
// Contrat de la composition : props {plan, images: [f]}, l'image 0 montre l'image f de la timeline. Sortie : SORTIE/f.png.
import {createRequire} from 'node:module';
import fs from 'node:fs';
import path from 'node:path';
import {pathToFileURL} from 'node:url';

const [planF, remotion, sortie, composition, liste] = process.argv.slice(2);
const racine = path.resolve(remotion);
const depuis = createRequire(path.join(racine, 'package.json'));
const charger = (nom) => import(pathToFileURL(depuis.resolve(nom)).href);
const {bundle} = await charger('@remotion/bundler');
const {renderStill, selectComposition} = await charger('@remotion/renderer');

const plan = JSON.parse(fs.readFileSync(planF, 'utf8'));
fs.mkdirSync(sortie, {recursive: true});
const serveUrl = await bundle({entryPoint: path.join(racine, 'src/index.ts'), publicDir: path.join(racine, 'public')});
for (const f of liste.split(',').map(Number)) {
  const p = plan.plans.find((x) => f >= x.debut && f < x.fin);
  const inputProps = {plan: {...plan, plans: [p]}, images: [f]};
  const comp = await selectComposition({serveUrl, id: composition, inputProps});
  await renderStill({composition: comp, serveUrl, frame: 0, output: path.join(sortie, `${f}.png`), inputProps, imageFormat: 'png',
    chromiumOptions: {gl: 'swangle'}, timeoutInMilliseconds: 180000});
  console.log('image', f);
}
