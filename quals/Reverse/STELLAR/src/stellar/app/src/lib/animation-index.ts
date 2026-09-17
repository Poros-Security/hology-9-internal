import {generatedAnimationTokens,generatedFlagAnimationToken} from "./generated-animation-index";
import {mediaCopy} from "./suisei-content";

export const animations=generatedAnimationTokens.map((token,index)=>({
  name:token,
  title:mediaCopy[index]?.title??`Archive Motion ${String(index+1).padStart(2,"0")}`,
  note:mediaCopy[index]?.caption??`Fan archive loop ${String(index+1).padStart(2,"0")}`,
  era:mediaCopy[index]?.era??"Fan archive",
  credit:mediaCopy[index]?.credit??"Contributor credit pending",
  source:mediaCopy[index]?.source??"#/about"
}));

export const featuredAnimation=animations.find(item=>item.name!==generatedFlagAnimationToken)??animations[0];
export const labAnimation=animations[4]??featuredAnimation;
export const midnightAnimation=animations.find(item=>item.name===generatedFlagAnimationToken)??animations.at(-1)!;
