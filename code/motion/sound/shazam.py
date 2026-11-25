import asyncio, sys, glob
from shazamio import Shazam
async def main():
    sh = Shazam()
    for f in sorted(glob.glob('music/m_*.wav'), key=lambda x:int(x.split('_')[1].split('.')[0])):
        try:
            r = await sh.recognize(f)
            t = r.get('track') or {}
            print(f, '->', t.get('title'), '|', t.get('subtitle'))
        except Exception as e:
            print(f, 'erreur', e)
asyncio.run(main())
