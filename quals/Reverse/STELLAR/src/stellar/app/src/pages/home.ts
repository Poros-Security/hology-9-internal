import{StellarGifPlayer}from"../components/stellar-gif-player";
import{featuredAnimation}from"../lib/animation-index";
import{albums}from"../lib/suisei-content";

const hero=new URL("../assets/images/suisei-hero.jpg",import.meta.url).href;

export function home(){const node=document.createElement("div");node.className="home-page";node.innerHTML=`
  <section class="fan-hero">
    <img src="${hero}" alt="Hoshimachi Suisei seated against a deep blue night scene">
    <div class="hero-shade"></div>
    <div class="hero-copy"><p class="jp-name">星街すいせい</p><h1>Hoshimachi<br>Suisei</h1><p>An unofficial fan archive for the voice, music, and moments that keep shining long after the song ends.</p><a href="#/music">Explore the music <span>→</span></a></div>
    <p class="hero-credit">Official site artwork · © COVER</p>
  </section>
  <section class="opening-note"><p>For the Hoshiyomi</p><div><h2>A star found on her own terms.</h2><p>STELLAR is a personal celebration of Suisei’s journey—from an independent debut to stages and songs recognized around the world. It is not a database. It is a fan’s shelf of favorite sounds, images, and memories.</p></div></section>
  <section class="home-feature"><div><p class="section-label">On repeat</p><h2>${featuredAnimation.title}</h2><p>${featuredAnimation.note}</p><a class="text-link" href="#/gallery">See the gallery →</a></div><figure id="home-loop"><figcaption>${featuredAnimation.era}</figcaption></figure></section>
  <section class="album-shelf"><header><h2>Selected releases</h2><a class="text-link" href="#/music">Full selection →</a></header><div>${albums.map(album=>`<article><img src="${album.image}" alt="Cover artwork for ${album.title}"><p>${album.year}</p><h3>${album.title}</h3></article>`).join("")}</div></section>`;node.querySelector("#home-loop")?.prepend(new StellarGifPlayer(featuredAnimation.name,true,featuredAnimation.title).element);return node}
