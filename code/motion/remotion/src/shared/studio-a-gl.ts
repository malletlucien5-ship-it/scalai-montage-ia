import {STUDIO_A_FLOAT32, STUDIO_A_SIZE} from './studio-a-data';

// LUT originale en float32. Ordre .cube : rouge, vert, bleu.
const vertex = `attribute vec2 position; varying vec2 uv;
void main(){uv=(position+1.0)*0.5;gl_Position=vec4(position,0.,1.);}`;
const fragment = `precision highp float;
varying vec2 uv; uniform sampler2D video; uniform sampler2D lut;
vec3 at(vec3 p){return texture2D(lut,vec2((p.r+0.5)/33.,(p.g+p.b*33.+0.5)/1089.)).rgb;}
vec3 grade(vec3 c){
  vec3 p=clamp(c,0.,1.)*32.; vec3 lo=floor(p); vec3 hi=min(lo+1.,32.); vec3 f=p-lo;
  vec3 a=at(lo), d=at(hi), b, e; float x,y,z;
  if(f.r>=f.g){
    if(f.g>=f.b){b=at(vec3(hi.r,lo.g,lo.b));e=at(vec3(hi.r,hi.g,lo.b));x=f.r;y=f.g;z=f.b;}
    else if(f.r>=f.b){b=at(vec3(hi.r,lo.g,lo.b));e=at(vec3(hi.r,lo.g,hi.b));x=f.r;y=f.b;z=f.g;}
    else {b=at(vec3(lo.r,lo.g,hi.b));e=at(vec3(hi.r,lo.g,hi.b));x=f.b;y=f.r;z=f.g;}
  }else{
    if(f.r>=f.b){b=at(vec3(lo.r,hi.g,lo.b));e=at(vec3(hi.r,hi.g,lo.b));x=f.g;y=f.r;z=f.b;}
    else if(f.g>=f.b){b=at(vec3(lo.r,hi.g,lo.b));e=at(vec3(lo.r,hi.g,hi.b));x=f.g;y=f.b;z=f.r;}
    else {b=at(vec3(lo.r,lo.g,hi.b));e=at(vec3(lo.r,hi.g,hi.b));x=f.b;y=f.g;z=f.r;}
  }
  return a+x*(b-a)+y*(e-b)+z*(d-e);
}
void main(){vec4 c=texture2D(video,uv);gl_FragColor=vec4(grade(c.rgb),c.a);}`;

export const creerStudioA = (canvas: HTMLCanvasElement) => {
  const gl = canvas.getContext('webgl', {preserveDrawingBuffer: true, alpha: false, antialias: false});
  if (!gl || !gl.getExtension('OES_texture_float')) throw new Error('Studio A exige WebGL et les textures float.');
  const shader = (type: number, code: string) => {
    const s = gl.createShader(type)!; gl.shaderSource(s, code); gl.compileShader(s);
    if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s)!);
    return s;
  };
  const vs = shader(gl.VERTEX_SHADER, vertex), fs = shader(gl.FRAGMENT_SHADER, fragment);
  const program = gl.createProgram()!; gl.attachShader(program, vs); gl.attachShader(program, fs); gl.linkProgram(program);
  if (!gl.getProgramParameter(program, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(program)!);
  gl.useProgram(program);
  const buffer = gl.createBuffer()!; gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1,-1,1,-1,-1,1,1,1]), gl.STATIC_DRAW);
  const pos = gl.getAttribLocation(program, 'position'); gl.enableVertexAttribArray(pos); gl.vertexAttribPointer(pos,2,gl.FLOAT,false,0,0);
  const texture = (unit: number) => {
    gl.activeTexture(gl.TEXTURE0+unit); const t=gl.createTexture()!; gl.bindTexture(gl.TEXTURE_2D,t);
    gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.NEAREST);
    gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.NEAREST);
    gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE); return t;
  };
  const lut=texture(1), binary=atob(STUDIO_A_FLOAT32);
  const bytes=Uint8Array.from(binary,(c)=>c.charCodeAt(0)), data=new DataView(bytes.buffer);
  const rgba=new Float32Array(STUDIO_A_SIZE**3*4);
  for(let i=0;i<STUDIO_A_SIZE**3;i++){
    for(let j=0;j<3;j++) rgba[i*4+j]=data.getFloat32((i*3+j)*4,true);
    rgba[i*4+3]=1;
  }
  gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,33,1089,0,gl.RGBA,gl.FLOAT,rgba);
  gl.uniform1i(gl.getUniformLocation(program,'lut'),1);
  const video=texture(0); gl.uniform1i(gl.getUniformLocation(program,'video'),0);
  return {
    draw(source: CanvasImageSource){
      const s=source as HTMLImageElement & HTMLVideoElement;
      const w=s.videoWidth || s.naturalWidth || Number(s.width), h=s.videoHeight || s.naturalHeight || Number(s.height);
      if(!w || !h) throw new Error('Image caméra vide.');
      if(canvas.width!==w || canvas.height!==h){canvas.width=w;canvas.height=h;}
      gl.viewport(0,0,w,h);gl.activeTexture(gl.TEXTURE0);gl.bindTexture(gl.TEXTURE_2D,video);
      gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL,true);
      gl.pixelStorei(gl.UNPACK_COLORSPACE_CONVERSION_WEBGL,gl.NONE);
      gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,source as TexImageSource);
      gl.drawArrays(gl.TRIANGLE_STRIP,0,4);gl.finish();
      if(gl.getError()!==gl.NO_ERROR) throw new Error('Erreur WebGL Studio A.');
    },
    dispose(){gl.deleteTexture(video);gl.deleteTexture(lut);gl.deleteBuffer(buffer);gl.deleteProgram(program);gl.deleteShader(vs);gl.deleteShader(fs);}
  };
};
