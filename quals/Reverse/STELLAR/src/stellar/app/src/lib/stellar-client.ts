import { parseStellarContainer, type StellarAnimation } from "./stellar-container";
export async function requestAnimation(token:string,key?:string):Promise<StellarAnimation>{
  const query=key?`?k=${key}`:"";
  const response=await fetch(`stellar://localhost/a/${encodeURIComponent(token)}${query}`);
  if(!response.ok)throw new Error("Archive renderer rejected the selected entry");return parseStellarContainer(await response.arrayBuffer());
}

const mask=(1n<<64n)-1n;
const rol=(value:bigint,shift:number)=>((value<<BigInt(shift))|(value>>BigInt(64-shift)))&mask;
export function interactionKey(animation:StellarAnimation,token:string):string{
  let state=(BigInt(`0x${token}`)^0x8f4219d7c6a5e30bn)&mask;
  state^=(BigInt(animation.width)<<48n)|(BigInt(animation.height)<<32n);
  animation.frames.forEach((frame,index)=>{
    const value=BigInt(frame.delay)|(BigInt(frame.disposal)<<16n)|(BigInt(frame.left)<<24n)|(BigInt(frame.top)<<40n);
    state=rol(state^value,(index&31)+7);
    state=(state*0x9e3779b185ebca87n)&mask;
    state^=state>>27n;
  });
  state^=(BigInt(animation.frames.length)*0x100000001b3n)&mask;
  return (state&mask).toString(16).padStart(16,"0");
}
