import path from 'path';
import {Config} from '@remotion/cli/config';
Config.setVideoImageFormat('jpeg');
Config.setOverwriteOutput(true);
Config.setConcurrency(3);

// Aperçu local : remplace Google Fonts par des polices locales. Le bundle Lambda n'est pas touché.
if (process.env.LOCAL_PREVIEW === '1') {
  Config.overrideWebpackConfig((config) => {
    const stubs = path.join(process.cwd(), 'tools', 'preview-stubs');
    const alias: Record<string, string> = {};
    for (const name of ['Anton', 'BodoniModa', 'InstrumentSans', 'Inter', 'Montserrat', 'Newsreader', 'PlayfairDisplay', 'Roboto', 'SourceSerif4']) {
      alias[`@remotion/google-fonts/${name}`] = path.join(stubs, `${name}.js`);
    }
    return {...config, resolve: {...config.resolve, alias: {...(config.resolve?.alias ?? {}), ...alias}}};
  });
}
