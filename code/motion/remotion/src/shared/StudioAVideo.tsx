import React, {useCallback, useEffect, useRef} from 'react';
import {cancelRender, OffthreadVideo} from './rt';
import {creerStudioA} from './studio-a-gl';

export const StudioAVideo: React.FC<React.ComponentProps<typeof OffthreadVideo>> = (props) => {
  const canvas = useRef<HTMLCanvasElement>(null);
  const renderer = useRef<ReturnType<typeof creerStudioA> | null>(null);
  const draw = useCallback((source: CanvasImageSource) => {
    try {
      if (!canvas.current) throw new Error('Canvas Studio A indisponible.');
      if (!renderer.current) renderer.current = creerStudioA(canvas.current);
      renderer.current.draw(source);
    } catch (e) {cancelRender(e);}
  }, []);
  useEffect(() => () => {renderer.current?.dispose();renderer.current=null;}, []);
  return <>
    <canvas ref={canvas} style={{...props.style, position:'absolute', width:'100%', height:'100%', objectFit:'contain'}} />
    <OffthreadVideo {...props} crossOrigin="anonymous" onVideoFrame={draw}
      style={{...props.style, position:'absolute', opacity:0}} />
  </>;
};
