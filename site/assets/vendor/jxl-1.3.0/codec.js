/* Imoplace adapter: pinned @jsquash/jxl 1.3.0, single-thread libjxl. See LICENSE. */
import encoderFactory from './codec/enc/jxl_enc.js';
import {defaultOptions} from './meta.js';
let enc;
async function moduleFor(factory,relative){
 const url=new URL(relative,import.meta.url);
 let bytes;
 if(typeof process!=='undefined'&&process.versions?.node){const fs=await import('node:fs/promises');bytes=await fs.readFile(url);}
 else {const response=await fetch(url);if(!response.ok)throw Error('Codificador JXL indisponível: '+response.status);bytes=new Uint8Array(await response.arrayBuffer());}
 return factory({wasmBinary:bytes,noInitialRun:true});
}
export async function encodeLossless(data){
 const m=await(enc??=moduleFor(encoderFactory,'./codec/enc/jxl_enc.wasm'));
 const result=m.encode(data.data,data.width,data.height,{...defaultOptions,quality:100,lossless:true,lossyModular:false,lossyPalette:false,effort:3});
 if(!result)throw Error('Falha ao gerar JXL sem perdas');
 return result.slice().buffer;
}
