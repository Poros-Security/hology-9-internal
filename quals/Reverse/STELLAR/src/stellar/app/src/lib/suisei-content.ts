export type MediaItem = {
  name: string;
  title: string;
  caption: string;
  era: string;
  credit: string;
  source: string;
};

export const officialSite = "https://hoshimachi-suisei.jp/";
export const officialProfile = "https://hololive.hololivepro.com/talents/hoshimachi-suisei/";

export const albums = [
  { title: "Still Still Stellar", year: "2021", image: new URL("../assets/images/still-still-stellar.jpg", import.meta.url).href, note: "The first full album." },
  { title: "AWAKE", year: "2024", image: new URL("../assets/images/specter.jpg", import.meta.url).href, note: "A vivid single with an unmistakable visual world." },
  { title: "新星目録", year: "2025", image: new URL("../assets/images/shinsei-mokuroku.jpg", import.meta.url).href, note: "The third album, released in January 2025." }
];

export const mediaCopy: Array<Omit<MediaItem, "name">> = [
  { title: "On Stage", caption: "A quick turn beneath the blue stage lights.", era: "3D performance", credit: "Community GIF via Tenor", source: "https://tenor.com/view/hololive-hoshimachi-suisei-tspin-3d-gif-16595806" },
  { title: "Hoshiyomi Energy", caption: "Light stick ready; the show is about to begin.", era: "Fan reaction", credit: "Community GIF via Tenor", source: "https://tenor.com/view/hoshimachi-suisei-hololive-suisei-suisei-hoshimachi-gif-23662693" },
  { title: "Keep Moving", caption: "A bright little loop with unstoppable momentum.", era: "Fan remix", credit: "Community GIF via Tenor", source: "https://tenor.com/view/suisei-suisei-hathaway-hololive-gif-25522178" },
  { title: "After Midnight", caption: "Suisei in a deep-blue scene from her official website.", era: "Official portrait", credit: "Official site artwork · © COVER", source: officialSite },
  { title: "A Small Smile", caption: "One of those quiet expressions worth saving.", era: "Favorite moment", credit: "Community repost; creator unverified", source: "https://www.pinterest.com/pin/1149332767405018696/" },
  { title: "新星目録", caption: "The vivid cover of Suisei's third album.", era: "2025 release", credit: "Official discography artwork · © COVER", source: officialSite }
];

export const milestones = [
  { year: "2018", title: "First broadcast", copy: "Hoshimachi Suisei began her activities on March 22, 2018." },
  { year: "2020", title: "NEXT COLOR PLANET", copy: "A defining original song and an enduring point of entry for new listeners." },
  { year: "2021", title: "Still Still Stellar", copy: "Her first full album gathered the sound of an artist firmly in motion." },
  { year: "2023", title: "Specter", copy: "The second album moved into darker, more dramatic territory." },
  { year: "2024", title: "BIBBIDIBA", copy: "A playful, instantly recognizable release that reached far beyond the usual audience." },
  { year: "2025", title: "新星目録", copy: "A third album opening another chapter in Suisei's catalogue." }
];
