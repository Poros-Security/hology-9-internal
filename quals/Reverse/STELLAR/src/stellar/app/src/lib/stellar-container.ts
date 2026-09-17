export interface StellarFrame { delay: number; disposal: number; left: number; top: number; width: number; height: number; rgba: Uint8Array }
export interface StellarAnimation { width: number; height: number; loopCount: number; frames: StellarFrame[]; metadata: Record<string,string>|null }
export function parseStellarContainer(data:ArrayBuffer):StellarAnimation {
  const b=new Uint8Array(data),v=new DataView(data);if(v.getUint32(0,true)!==0x2ac75391||v.getUint16(4,true)!==1)throw new Error("Invalid archive animation");
  const width=v.getUint16(6,true),height=v.getUint16(8,true),count=v.getUint16(10,true),loopCount=v.getUint16(12,true),metaLen=v.getUint32(14,true);let p=18;const frames:StellarFrame[]=[];
  for(let i=0;i<count;i++){const delay=v.getUint16(p,true),disposal=b[p+2],left=v.getUint16(p+4,true),top=v.getUint16(p+6,true),fw=v.getUint16(p+8,true),fh=v.getUint16(p+10,true),n=v.getUint32(p+12,true);p+=16;if(n!==width*height*4||p+n>b.length)throw new Error("Corrupt STELLAR frame");frames.push({delay,disposal,left,top,width:fw,height:fh,rgba:b.slice(p,p+n)});p+=n}
  let metadata:Record<string,string>|null=null;if(metaLen&&p+metaLen<=b.length){try{metadata=JSON.parse(new TextDecoder().decode(b.slice(p,p+metaLen)))}catch{metadata=null}}
  return{width,height,loopCount,frames,metadata};
}
