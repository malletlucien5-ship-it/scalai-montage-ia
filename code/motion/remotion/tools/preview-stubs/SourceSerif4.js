// Aperçu local uniquement (LOCAL_PREVIEW=1) : Chromium local ne passe pas le proxy TLS vers Google Fonts.
export const loadFont = () => ({fontFamily: 'SourceSerif', fonts: {}, unicodeRanges: {}, waitUntilDone: () => Promise.resolve()});
export const getInfo = () => ({fontFamily: 'SourceSerif', fonts: {}});
