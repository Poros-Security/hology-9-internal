const links=[["/","Home"],["/profile","Profile"],["/music","Music"],["/gallery","Gallery"],["/highlights","Highlights"],["/about","About"]];
const logo=new URL("../assets/images/stellar-logo.png",import.meta.url).href;
export function navigation(){
  const node=document.createElement("nav");node.className="nav";
  node.setAttribute("aria-label","Primary navigation");
  node.innerHTML=`<a class="brand" href="#/"><img class="brand-mark" src="${logo}" alt=""><span>STELLAR<small>HOSHIMACHI SUISEI FAN ARCHIVE</small></span></a><div class="nav-links">${links.map(([url,label])=>`<a href="#${url}" data-route="${url}">${label}</a>`).join("")}</div>`;
  return node;
}
export function selectNavigation(path:string){document.querySelectorAll<HTMLElement>("[data-route]").forEach(link=>link.classList.toggle("active",link.dataset.route===path))}
