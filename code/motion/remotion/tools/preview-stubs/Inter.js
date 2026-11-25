// Aperçu local uniquement (LOCAL_PREVIEW=1) : Chromium local ne passe pas le proxy TLS vers Google Fonts.
export const loadFont = () => ({fontFamily: 'InterL', fonts: {}, unicodeRanges: {}, waitUntilDone: () => Promise.resolve()});
export const getInfo = () => ({fontFamily: 'InterL', fonts: {}});
