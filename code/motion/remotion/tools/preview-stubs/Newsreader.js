// Aperçu local uniquement (LOCAL_PREVIEW=1) : Chromium local ne passe pas le proxy TLS vers Google Fonts.
export const loadFont = () => ({fontFamily: 'Newsreader', fonts: {}, unicodeRanges: {}, waitUntilDone: () => Promise.resolve()});
export const getInfo = () => ({fontFamily: 'Newsreader', fonts: {}});
