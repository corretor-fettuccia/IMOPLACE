// Binary interchange: uint32LE width,height followed by RGBA. Never JPEG/WebP intermediate.
import fs from 'node:fs';
globalThis.ImageData ??=class{constructor(data,width,height){this.data=data;this.width=width;this.height=height;}};
const {encodeLossless}=await import('../site/assets/vendor/jxl-1.3.0/codec.js');
const [mode,input,output]=process.argv.slice(2);const bytes=fs.readFileSync(input);
if(mode==='encode'){
 const width=bytes.readUInt32LE(0),height=bytes.readUInt32LE(4);
 if(!width||!height||width*height>50e6||bytes.length!==8+width*height*4)throw Error('Dimensões RGBA inválidas');
 const result=await encodeLossless({width,height,data:new Uint8ClampedArray(bytes.buffer,bytes.byteOffset+8,bytes.length-8)});fs.writeFileSync(output,new Uint8Array(result));
}else throw Error('Use encode');
