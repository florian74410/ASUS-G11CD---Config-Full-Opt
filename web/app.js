const $=id=>document.getElementById(id);
const state={items:[],categories:[],page:"dashboard",filters:{q:"",status:"all",category:"all"},errors:[],listings:[]};
const euros=n=>typeof n==="number"?new Intl.NumberFormat("fr-FR",{style:"currency",currency:"EUR"}).format(n):"—";
const esc=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const readable=n=>n==null||n===""?"—":String(n);
const price=d=>d.pricing||{};
const acquired=d=>typeof price(d).acquisition_eur==="number";
const cost=d=>acquired(d)?price(d).acquisition_eur+(price(d).shipping_eur||0):null;
const status=d=>'<span class="tag '+esc(d.status||"")+'">'+esc(d.status||"unknown")+'</span>';
const card=d=>'<article class="item-card" data-id="'+esc(d.id)+'"><div class="item-photo">'+(d._photo?'<img loading="lazy" src="'+esc(d._photo)+'" alt="'+esc(d.full_name)+'" onerror="this.style.display=\'none\';this.parentNode.textContent=\'⬡\'">':'⬡')+'</div><div class="kicker">'+esc(d.category)+'</div><h3>'+esc(d.full_name)+'</h3><div class="item-meta">'+status(d)+' · '+esc(d.manufacturer||"")+'</div><div class="item-prices"><div><small>Occasion</small><strong>'+euros(price(d).used_eur)+'</strong></div><div><small>Acquisition</small><strong>'+euros(price(d).acquisition_eur)+'</strong></div></div></article>';
const cardgrid=items=>items.length?'<div class="grid">'+items.map(card).join("")+'</div>':'<div class="empty">Aucun composant dans cette sélection. Ajoute un JSON pour commencer.</div>';
const sum=(items,fn)=>items.reduce((s,d)=>s+fn(d),0);
function navigate(page){state.page=page;document.querySelectorAll(".page").forEach(x=>x.classList.add("hidden"));$("category").classList.toggle("hidden",!state.categories.includes(page));if($(page))$(page).classList.remove("hidden");const name=state.categories.includes(page)?page:({dashboard:"Tableau de bord",inventory:"Inventaire",budget:"Budget",marketplace:"Marketplace"}[page]||page);$("title").textContent=name;document.querySelectorAll("nav button").forEach(b=>b.classList.toggle("active",b.dataset.page===page));render();}
function nav(){const svgPaths={
cpu:'<rect x="5" y="5" width="14" height="14" rx="2"/><path d="M9 2v3m6-3v3M9 19v3m6-3v3M2 9h3m-3 6h3m14-6h3m-3 6h3"/><rect x="9" y="9" width="6" height="6" rx="1"/>',
gpu:'<rect x="2" y="6" width="20" height="12" rx="2"/><circle cx="9" cy="12" r="3"/><path d="M16 9h3m-3 3h3m-3 3h3M5 18v2m14-2v2"/>',
memory:'<rect x="2" y="7" width="20" height="10" rx="1"/><path d="M6 10v4m4-4v4m4-4v4m4-4v4M6 17v2m4-2v2m4-2v2m4-2v2"/>',
clock:'<circle cx="12" cy="12" r="9"/><path d="M12 7v5l4 2"/>',
cores:'<rect x="4" y="4" width="16" height="16" rx="3"/><rect x="8" y="8" width="3" height="3"/><rect x="13" y="8" width="3" height="3"/><rect x="8" y="13" width="3" height="3"/><rect x="13" y="13" width="3" height="3"/>',
threads:'<path d="M4 6h7l3 4h6M4 12h16M4 18h7l3-4h6"/><circle cx="4" cy="6" r="1"/><circle cx="4" cy="18" r="1"/>',
socket:'<rect x="3" y="3" width="18" height="18" rx="3"/><circle cx="12" cy="12" r="5"/><path d="M12 7v10m-5-5h10"/>',
board:'<rect x="3" y="3" width="18" height="18" rx="2"/><rect x="7" y="7" width="8" height="8" rx="1"/><path d="M18 6v5m0 3v4M6 18h7"/>',
storage:'<rect x="3" y="4" width="18" height="16" rx="3"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1"/><path d="M5 19h14"/>',
speed:'<path d="M4 17a9 9 0 1 1 16 0"/><path d="m12 14 5-6"/><circle cx="12" cy="14" r="1"/><path d="M4 19h16"/>',
power:'<path d="m13 2-9 12h7l-1 8 10-13h-7z"/>',
temperature:'<path d="M10 14V5a2 2 0 0 1 4 0v9a5 5 0 1 1-4 0z"/><path d="M12 10v7"/>',
security:'<path d="m12 2 8 4v6c0 5-3 8-8 10-5-2-8-5-8-10V6z"/><path d="m8 12 3 3 5-6"/>',
network:'<rect x="9" y="2" width="6" height="5" rx="1"/><rect x="2" y="17" width="6" height="5" rx="1"/><rect x="16" y="17" width="6" height="5" rx="1"/><path d="M12 7v6M5 17v-4h14v4"/>',
wifi:'<path d="M2 9a16 16 0 0 1 20 0M5 12a11 11 0 0 1 14 0m-11 3a6 6 0 0 1 8 0"/><circle cx="12" cy="19" r="1"/>',
audio:'<path d="M5 9v6h4l5 4V5L9 9zM18 8a6 6 0 0 1 0 8"/>',
display:'<rect x="3" y="4" width="18" height="13" rx="2"/><path d="M12 17v4m-5 0h10"/>',
usb:'<path d="M12 21V3m0 0-3 3m3-3 3 3M12 12H6l-2-2m8 6h6l2-2"/><circle cx="4" cy="10" r="1"/><rect x="18" y="12" width="4" height="4"/>',
fan:'<circle cx="12" cy="12" r="2"/><path d="M12 10c-4-8 6-9 6-3 0 2-2 4-4 5m0 0c8-4 9 6 3 6-2 0-4-2-5-4m0 0c4 8-6 9-6 3 0-2 2-4 4-5m0 0c-8 4-9-6-3-6 2 0 4 2 5 4"/>',
case:'<rect x="6" y="2" width="12" height="20" rx="2"/><circle cx="12" cy="17" r="1"/><path d="M9 6h6v6H9z"/>',
size:'<path d="M4 9V4h5m6 0h5v5m0 6v5h-5M9 20H4v-5"/>',
price:'<path d="M17 5a8 8 0 1 0 0 14M4 10h11M4 14h11"/>',
info:'<circle cx="12" cy="12" r="9"/><path d="M12 11v6m0-10v1"/>',
performance:'<path d="M3 17h4l3-8 4 6 3-4h4"/>',
technology:'<circle cx="12" cy="12" r="3"/><path d="M12 2v3m0 14v3M2 12h3m14 0h3M5 5l2 2m10 10 2 2M19 5l-2 2M7 17l-2 2"/>',
system:'<rect x="3" y="4" width="18" height="15" rx="2"/><path d="m7 9 3 3-3 3m5 0h5"/>',
default:'<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="3"/>'
};
const icons=Object.fromEntries(Object.entries(svgPaths).map(([k,p])=>[k,'<svg class="hw-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'+p+'</svg>']));
const iconNames={
cores:"cores",cuda_cores:"gpu",cuda_or_shader_cores:"gpu",rt_cores:"gpu",tensor_cores:"gpu",threads:"threads",socket:"socket",form_factor:"board",case_form_factor:"case",chipset:"board",memory_type:"memory",memory_slots:"memory",memory_channels:"memory",memory_speed_mts:"speed",speed_mts:"speed",cas_latency_cycles:"clock",vram_gb:"gpu",vram_type:"memory",memory_bus_bits:"memory",capacity_gb:"storage",cache_l2_mb:"memory",cache_l3_mb:"memory",base_ghz:"clock",boost_ghz:"clock",base_mhz:"clock",boost_mhz:"clock",pcie_gen:"speed",pcie_minimum_generation:"speed",pcie_slots:"board",m2_slots:"storage",sata_ports:"storage",nominal_w:"power",tdp_w:"power",tgp_w:"power",graphics_power_w:"power",recommended_psu_w:"power",temperature_limit_c:"temperature",max_temperature_c:"temperature",sequential_read_mbs:"speed",sequential_write_mbs:"speed",rpm:"fan",wifi:"wifi",bluetooth:"network",lan:"network",audio:"audio",rear_usb:"usb",rear_video:"display",hdmi:"display",displayport:"display",dimensions_mm:"size",length_mm:"size",height_mm:"size",thickness_slots:"size",architecture:"cpu",codename:"cpu",process_nm:"cpu",integrated_graphics:"gpu",certification:"security",modular:"power",rgb:"display"
};
const specIcon=k=>icons[iconNames[k]||(/aes|encrypt|security|tpm/i.test(k)?"security":/freq|clock|boost/i.test(k)?"clock":/ram|memory/i.test(k)?"memory":/nvidia|amd|gpu/i.test(k)?"gpu":"default")];
const techTiles=data=>'<div class="tech-tiles">'+Object.entries(data||{}).filter(([,v])=>v!==null&&v!==undefined&&v!==""&&!(Array.isArray(v)&&!v.length)).map(([k,v])=>'<div class="tech-tile"><span class="tech-icon" aria-hidden="true">'+specIcon(k)+'</span><div><small>'+esc(fieldName(k))+'</small><strong>'+esc(fieldValue(v))+'</strong></div></div>').join("")+'</div>';
function galleryViewLabel(i){return activeGallery[i]?.label||viewNames[i]||"Vue "+(i+1)}
function galleryDisplay(){
 const img=$("gallery-image"),stage=$("gallery-stage"),count=$("gallery-count"),caption=$("gallery-caption");
 if(!stage)return;
 const entry=activeGallery[galleryIndex];
 if(img){img.hidden=!entry;img.src=entry?.url||"";img.alt=entry?galleryViewLabel(galleryIndex):"";img.style.transform="scale("+galleryZoom+")";}
 stage.classList.toggle("no-image",!entry);
 if(count)count.textContent=entry?(galleryIndex+1)+" / "+activeGallery.length:"0 / 0";
 if(caption)caption.textContent=entry?galleryViewLabel(galleryIndex):"Photo indisponible";
 document.querySelectorAll(".gallery-thumb").forEach((el,i)=>{el.classList.toggle("active",i===galleryIndex);el.setAttribute("aria-pressed",String(i===galleryIndex));});
 if($("gallery-zoom-value"))$("gallery-zoom-value").textContent=Math.round(galleryZoom*100)+" %";
}
function galleryChoose(i){if(!activeGallery.length)return;galleryIndex=(i+activeGallery.length)%activeGallery.length;galleryZoom=1;galleryDisplay()}
function galleryAdjust(factor){galleryZoom=Math.min(4,Math.max(1,galleryZoom*factor));galleryDisplay()}
function setGalleryMode(mode){
 galleryMode=mode;const el=$("gallery-stage");if(!el)return;
 el.classList.toggle("rotation-mode",mode==="rotation");
 $("gallery-mode-label").textContent=mode==="rotation"?"Rotation multi-vues simulée • pas de modèle 3D":"Galerie photographique";
 $("gallery-mode").textContent=mode==="rotation"?"▣ Revenir aux photos":"⬡ Rotation multi-vues";
}
function bindGallery(){
 const prev=$("gallery-prev"),next=$("gallery-next"),zoomIn=$("gallery-zoom-in"),zoomOut=$("gallery-zoom-out"),reset=$("gallery-reset"),mode=$("gallery-mode"),stage=$("gallery-stage");
 prev.onclick=()=>galleryChoose(galleryIndex-1);next.onclick=()=>galleryChoose(galleryIndex+1);
 zoomIn.onclick=()=>galleryAdjust(1.25);zoomOut.onclick=()=>galleryAdjust(.8);
 reset.onclick=()=>{galleryZoom=1;galleryDisplay()};
 mode.onclick=()=>setGalleryMode(galleryMode==="rotation"?"photos":"rotation");
 document.querySelectorAll(".gallery-thumb").forEach(el=>el.onclick=()=>galleryChoose(Number(el.dataset.index)));
 let startX=null;
 stage.addEventListener("pointerdown",e=>{if(e.target.closest("button"))return;startX=e.clientX;});
 stage.addEventListener("pointerup",e=>{if(startX===null)return;const delta=e.clientX-startX;startX=null;if(Math.abs(delta)>45)galleryChoose(galleryIndex+(delta<0?1:-1));});
 stage.addEventListener("wheel",e=>{if(e.ctrlKey){e.preventDefault();galleryAdjust(e.deltaY<0?1.12:1/1.12)}},{passive:false});
 galleryDisplay();
}
const technologyExplanations={
 "socket":"Le socket détermine la famille de processeurs physiquement compatible avec une carte mère.",
 "chipset":"Le chipset gère certaines fonctions d’entrée/sortie, les lignes PCIe et les possibilités d’extension de la plateforme.",
 "pcie_gen":"La génération PCI Express influe sur la bande passante maximale disponible par ligne ; elle n’indique pas à elle seule les performances réelles.",
 "pcie_minimum_generation":"Cette génération représente le niveau minimal prévu pour l’interface PCI Express.",
 "memory_type":"La génération de mémoire impose une compatibilité entre processeur, carte mère et modules.",
 "vram_gb":"La capacité de mémoire vidéo aide à stocker textures, buffers et ressources ; elle n’est pas une mesure directe des images par seconde.",
 "memory_bus_bits":"La largeur du bus participe au débit mémoire, avec la fréquence effective et la compression.",
 "cores":"Les cœurs physiques permettent d’exécuter plusieurs travaux de calcul en parallèle.",
 "threads":"Les threads logiques exposent les contextes d’exécution simultanés ; leur nombre ne correspond pas forcément à celui des cœurs physiques.",
 "boost_ghz":"La fréquence Boost est une pointe conditionnelle liée aux limites de température, de puissance et à la charge.",
 "tdp_w":"Le TDP décrit une enveloppe thermique de référence ; ce n’est pas toujours la consommation électrique maximale.",
 "sequential_read_mbs":"Le débit de lecture séquentielle concerne les gros transferts continus, sans garantir les performances en accès aléatoires.",
 "sequential_write_mbs":"Le débit d’écriture séquentielle dépend notamment du cache, du contrôleur et du remplissage.",
 "cas_latency_cycles":"Le CAS (CL) exprime une latence en cycles : pour comparer des kits DDR4, il faut aussi connaître leur fréquence."
};
function explainTech(d){
 const specs=d.specifications||{},list=[];
 for(const key of Object.keys(specs)){if(specs[key]!==null&&specs[key]!==undefined&&technologyExplanations[key])list.push('<div class="explain-row"><strong><span class="explain-icon" aria-hidden="true">'+specIcon(key)+'</span>'+esc(fieldName(key))+'</strong><p>'+esc(technologyExplanations[key])+'</p></div>');}
 if(Array.isArray(d.technologies))for(const t of d.technologies){
 const explanations={AES:"AES accélère certaines opérations de chiffrement matériel.",SMT:"SMT permet à un cœur physique de gérer plusieurs threads logiques.",AVX2:"AVX2 étend les instructions vectorielles utilisées par des applications compatibles.", "AMD-V":"AMD-V prend en charge la virtualisation matérielle sur les systèmes compatibles.","64 bits":"Une architecture 64 bits permet l'exécution de logiciels x86-64 et l'adressage mémoire associé."};
 const key=String(t).split(" ")[0];if(explanations[key])list.push('<div class="explain-row"><strong><span class="explain-icon" aria-hidden="true">'+(/AES|64 bits/i.test(t)?icons.security:icons.technology)+'</span>'+esc(t)+'</strong><p>'+esc(explanations[key])+'</p></div>');
 }
 return list.length?'<div class="explanations">'+list.join("")+'</div>':'<p class="muted">Technologies détaillées à documenter pour cette référence.</p>';
}
function openDetail(id){
 const d=state.items.find(x=>x.id===id);if(!d)return;previousFocus=document.activeElement;
 const p=price(d),raw=d._photos||(d._photo?[d._photo]:[]);
 activeGallery=raw.map((v,i)=>typeof v==="string"?{url:v,label:viewNames[i]||"Vue "+(i+1)}:v).filter(v=>v.url);
 galleryIndex=0;galleryZoom=1;galleryMode="photos";
 const sourceLinks=(d.sources||[]).map((x,i)=>{const url=typeof x==="string"?x:x.url;return typeof url==="string"&&(url.startsWith("https://")||url.startsWith("http://"))?'<a href="'+esc(url)+'" rel="noopener noreferrer" target="_blank">Source '+(i+1)+' ↗</a>':""}).join(" ");
 const pricing=[["Neuf",p.new_eur],["Occasion",p.used_eur],["Acquisition",p.acquisition_eur],["Livraison",p.shipping_eur]].map(([k,v])=>'<div class="tech-price"><small><span class="mini-icon" aria-hidden="true">'+icons.price+'</span>'+k+'</small><strong>'+esc(euros(v))+'</strong></div>').join("");
 const thumb=activeGallery.map((entry,i)=>'<button class="gallery-thumb" type="button" data-index="'+i+'" aria-label="Voir '+esc(entry.label)+'"><img src="'+esc(entry.url)+'" alt="" loading="lazy"><span>'+esc(entry.label)+'</span></button>').join("");
 $("modal-content").innerHTML=
 '<div class="component-breadcrumb">⌂ &nbsp; Composants <span>›</span> '+esc(d.category)+' <span>›</span> '+esc(d.model||d.id)+'</div>'+
 '<div class="component-hero"><div class="component-header"><div class="kicker">'+esc(d.manufacturer||"")+' / '+esc(d.category)+'</div><h2>'+esc(d.full_name)+'</h2><div class="component-header-tags">'+status(d)+'<span class="tech-pill">'+esc(d.specifications?.socket||d.specifications?.form_factor||"Fiche catalogue")+'</span><span class="tech-pill">'+activeGallery.length+' photo(s)</span></div></div></div>'+
 '<div class="component-layout"><section class="showcase"><div class="gallery-stage" id="gallery-stage"><div class="gallery-grid"></div><img id="gallery-image" alt=""><span class="gallery-placeholder">⬡<small>Photo de cette référence non disponible</small></span><button type="button" id="gallery-prev" class="gallery-arrow left" aria-label="Vue précédente">‹</button><button type="button" id="gallery-next" class="gallery-arrow right" aria-label="Vue suivante">›</button><span id="gallery-count" class="gallery-count"></span><span id="gallery-caption" class="gallery-caption"></span></div>'+
 '<div class="gallery-thumbs">'+thumb+'</div><div class="gallery-toolbar"><button type="button" id="gallery-mode">⬡ Rotation multi-vues</button><span id="gallery-mode-label">Galerie photographique</span><div class="gallery-zoom"><button type="button" id="gallery-zoom-out" aria-label="Réduire">−</button><span id="gallery-zoom-value">100 %</span><button type="button" id="gallery-zoom-in" aria-label="Agrandir">+</button><button type="button" id="gallery-reset">↺</button></div></div><p class="gallery-note">Rotation simulée à partir des photos disponibles : les vues manquantes ne sont pas inventées.</p></section>'+
 '<div class="component-info"><section class="tech-panel"><h3><span class="section-symbol">'+icons.board+'</span> Informations générales</h3>'+detailsGrid({Fabricant:d.manufacturer,Modèle:d.model,Référence:d.id,Catégorie:d.category,Compatibilité:d.compatibility?.status})+'</section>'+
 '<section class="tech-panel"><h3><span class="section-symbol">'+icons.technology+'</span> Spécifications techniques</h3>'+techTiles(d.specifications)+'</section></div></div>'+
 '<div class="component-secondary"><section class="tech-panel"><h3>◉ Prix et acquisition</h3><div class="tech-prices">'+pricing+'</div></section>'+
 '<section class="tech-panel"><h3><span class="section-symbol">'+icons.performance+'</span> Performances</h3>'+(Object.values(d.performance||{}).some(v=>Array.isArray(v)?v.length:!!v)?techTiles(d.performance):'<p class="muted">Aucun benchmark mesuré pour cette référence.</p>')+'</section>'+
 '<section class="tech-panel"><h3><span class="section-symbol">'+icons.info+'</span> Description technique</h3><p class="technical-prose">'+esc(d.technical_description||d.description_technical||d.notes||"Description complète à documenter pour cette référence.")+'</p>'+(d.technologies?.length?'<div class="tech-pills">'+d.technologies.map(t=>'<span>'+esc(t)+'</span>').join('')+'</div>':'')+'<h4 class="tech-subheading">Technologies embarquées</h4>'+explainTech(d)+'<div class="source-links">'+sourceLinks+'</div><small class="spec-path">'+esc(d._json||"")+'</small></section></div>';
 $("modal").classList.remove("hidden");document.body.classList.add("detail-open");bindGallery();$("closemodal").focus();
}
$("closemodal").onclick=$("closeback").onclick=()=>{ $("modal").classList.add("hidden");document.body.classList.remove("detail-open");previousFocus?.focus?.(); };
document.addEventListener("keydown",e=>{if($("modal").classList.contains("hidden"))return;if(e.key==="Escape")$("closemodal").click();if(e.key==="ArrowRight")galleryChoose(galleryIndex+1);if(e.key==="ArrowLeft")galleryChoose(galleryIndex-1);});
async function load(){try{const r=await fetch("/api/components?time="+Date.now(),{cache:"no-store"});if(!r.ok)throw Error("HTTP "+r.status);const data=await r.json();state.items=data.components;state.categories=data.categories;state.errors=data.errors;nav();$("warnings").innerHTML=data.errors.length?'<div class="notice">'+data.errors.map(esc).join("<br>")+'</div>':"";$("syncstatus").textContent=state.items.length+" références · actualisé "+new Date().toLocaleTimeString("fr-FR");render();if(state.page==="marketplace")renderMarketplace();}catch(e){$("syncstatus").textContent="Erreur de lecture";$("warnings").innerHTML='<div class="notice">'+esc(e.message)+'</div>';}}
$("refresh").onclick=load;load();

/* Marketplace module. No external libraries. */
const statuses={spotted:"Repérée",negotiating:"Négociation",accepted:"Prix accepté",purchased:"Payée",declined:"Abandonnée",expired:"Expirée"};
const moneyInput=(k,label,value)=>'<div><label for="m-'+k+'">'+label+'</label><input type="number" min="0" step="0.01" id="m-'+k+'" name="'+k+'" value="'+esc(value??"")+'"></div>';
function listingForm(d={}){
  const p=d.pricing||{};
  const select=(key,values,current)=>'<select name="'+key+'">'+values.map(([k,label])=>'<option value="'+esc(k)+'" '+(current===k?"selected":"")+'>'+esc(label)+'</option>').join("")+'</select>';
  return '<h2>'+(d.listing_id?"Modifier l’annonce":"Nouvelle annonce")+'</h2><form id="marketform" class="market-form">'+
  '<div><label>Plateforme</label>'+select("platform",[["Leboncoin","Leboncoin"],["eBay","eBay"],["Autre","Autre"]],d.platform||"Leboncoin")+'</div>'+
  '<div><label>Statut</label>'+select("status",Object.entries(statuses),d.status||"spotted")+'</div>'+
  '<div class="wide"><label>Référence / composant *</label><input name="component_name" required maxlength="180" value="'+esc(d.component_name||"")+'" list="knowncomponents"><datalist id="knowncomponents">'+state.items.map(x=>'<option value="'+esc(x.full_name)+'"></option>').join("")+'</datalist></div>'+
  '<div><label>ID technique (si existant)</label><select name="component_id"><option value="">Non associé</option>'+state.items.map(x=>'<option value="'+esc(x.id)+'" '+(d.component_id===x.id?"selected":"")+'>'+esc(x.full_name)+'</option>').join("")+'</select></div>'+
  '<div><label>État annoncé</label><input name="condition" maxlength="100" value="'+esc(d.condition||"")+'" placeholder="Bon état, à réparer…"></div>'+
  '<div class="wide"><label>URL de l’annonce</label><input name="url" type="url" maxlength="1000" value="'+esc(d.url||"")+'" placeholder="https://..."></div>'+
  moneyInput("seller_asking","Prix vendeur *",p.seller_asking)+moneyInput("shipping_estimated","Livraison estimée",p.shipping_estimated)+
  moneyInput("our_offer","Notre proposition",p.our_offer)+moneyInput("agreed_price","Prix accepté",p.agreed_price)+
  moneyInput("paid_price","Prix réellement payé (uniquement après paiement)",p.paid_price)+moneyInput("shipping_paid","Livraison réellement payée",p.shipping_paid)+
  '<div class="wide"><label>Notes</label><textarea name="notes" rows="3" maxlength="5000">'+esc(d.notes||"")+'</textarea></div>'+
  '<button class="primary" type="submit">Enregistrer le JSON</button></form><p id="marketfeedback" class="feedback"></p>'+
  (d.listing_id?'<h3>Historique des offres</h3><div id="events">'+(d.negotiation||[]).map(e=>'<p>'+esc(e.actor==="buyer"?"Notre offre":"Offre vendeur")+' : '+euros(e.amount)+' · '+esc(e.date)+'</p>').join("")+'</div><div class="market-form"><div><label>Montant de la nouvelle offre</label><input type="number" min="0" step="0.01" id="eventamount"></div><div><label>Provenance</label><select id="eventactor"><option value="buyer">Acheteur</option><option value="seller">Vendeur</option></select></div><button class="small-action" type="button" id="saveevent">Ajouter à l’historique</button></div>':"");
}
async function fetchListings(){const r=await fetch("/api/listings",{cache:"no-store"});if(!r.ok)throw Error("Lecture annonces HTTP "+r.status);const d=await r.json();state.listings=d.listings;return d;}
async function renderMarketplace(){
  const area=$("marketplace");if(!area)return;
  try{const data=await fetchListings();const a=state.listings;
   const purchased=a.filter(x=>x.status==="purchased"&&typeof x.pricing?.paid_price==="number");
   const total=purchased.reduce((v,x)=>v+x.pricing.paid_price+(x.pricing.shipping_paid||0),0);
   area.innerHTML='<div class="cards">'+[["Annonces",a.length],["Négociations",a.filter(x=>x.status==="negotiating").length],["Achats payés",purchased.length],["Dépenses Marketplace",euros(total)]].map(([k,v])=>'<div class="stat"><div class="label">'+k+'</div><div class="value">'+v+'</div></div>').join("")+'</div>'+
   '<div class="market-actions"><span class="muted">Offres, prix et négociations · JSON locaux</span><button id="addlisting" class="primary">＋ Nouvelle annonce</button></div>'+
   (data.errors.length?'<div class="notice">'+data.errors.map(esc).join("<br>")+'</div>':"")+
   (a.length?'<div class="listing-grid">'+a.map(x=>'<article class="listing"><div class="kicker">'+esc(x.platform)+'</div><h3>'+esc(x.component_name)+'</h3><span class="tag">'+esc(statuses[x.status]||x.status)+'</span><div class="listing-stats"><div><small>Prix vendeur</small><strong>'+euros(x.pricing?.seller_asking)+'</strong></div><div><small>Prix accepté</small><strong>'+euros(x.pricing?.agreed_price)+'</strong></div></div><button class="small-action editlisting" data-listing="'+esc(x.listing_id)+'">Voir / Modifier</button></article>').join("")+'</div>':'<div class="empty">Aucune annonce. Clique sur « Nouvelle annonce » pour créer ta première fiche.</div>');
   $("addlisting").onclick=()=>openListing();
   area.querySelectorAll(".editlisting").forEach(b=>b.onclick=()=>openListing(a.find(x=>x.listing_id===b.dataset.listing)));
  }catch(e){area.innerHTML='<div class="notice">'+esc(e.message)+'</div>';}
}
function openListing(d){
  $("modal-content").innerHTML=listingForm(d||{});
  $("modal").classList.remove("hidden");
  $("marketform").onsubmit=async e=>{
    e.preventDefault();const f=new FormData(e.target);
    const p={};for(const k of ["seller_asking","shipping_estimated","our_offer","agreed_price","paid_price","shipping_paid"]){const v=f.get(k);p[k]=v===""?null:Number(v);}
    const payload={component_name:f.get("component_name").trim(),component_id:f.get("component_id"),platform:f.get("platform"),url:f.get("url"),condition:f.get("condition"),status:f.get("status"),notes:f.get("notes"),pricing:p,negotiation:d?.negotiation||[]};
    if(payload.status==="purchased"&&p.paid_price===null){$("marketfeedback").textContent="Précise le prix réellement payé.";return;}
    const id=d?.listing_id;try{
      const res=await fetch(id?"/api/listings/"+id:"/api/listings",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)});
      const response=await res.json();if(!res.ok)throw Error(response.error||"Erreur");
      $("modal").classList.add("hidden");await renderMarketplace();
    }catch(err){$("marketfeedback").textContent=err.message;}
  };
  if(d?.listing_id)$("saveevent").onclick=async()=>{
    const amount=Number($("eventamount").value);
    if($("eventamount").value===""||!Number.isFinite(amount)||amount<0)return alert("Montant invalide");
    const form=$("marketform");const newHistory=[...(d.negotiation||[]),{actor:$("eventactor").value,amount,date:new Date().toISOString()}];
    const payload=structuredClone(d);payload.negotiation=newHistory;
    try{const res=await fetch("/api/listings/"+d.listing_id,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)});const response=await res.json();if(!res.ok)throw Error(response.error);await renderMarketplace();openListing(response);}catch(e){$("marketfeedback").textContent=e.message;}
  };
}

/* Appearance V1: theme choice is stored locally and never sent to server. */
(function(){
  const themes=new Set(["native","dark","classic","hardware","matrix","cyberpunk"]);
  const selector=document.getElementById("theme-select");
  function apply(value){
    const theme=themes.has(value)?value:"classic";
    document.documentElement.dataset.theme=theme;
    if(selector) selector.value=theme;
    try{localStorage.setItem("g11cd-theme",theme);}catch(e){}
    if(typeof initMatrixRain==="function")initMatrixRain();
  }
  apply(document.documentElement.dataset.theme);
  if(selector)selector.addEventListener("change",()=>apply(selector.value));
})();

/* Lightweight Matrix code rain, isolated behind the UI. */
function initMatrixRain(){
 const host=document.getElementById("matrix-rain");if(!host)return;
 host.replaceChildren();
 if(document.documentElement.dataset.theme!=="matrix")return;
 const reduced=window.matchMedia&&window.matchMedia("(prefers-reduced-motion: reduce)").matches;
 const count=Math.min(70,Math.max(14,Math.floor(window.innerWidth/34)));
 const fragment=document.createDocumentFragment();
 for(let i=0;i<count;i++){
   const el=document.createElement("span");el.className="matrix-rain-column";
   let bin="";const length=18+(i*7%25);
   for(let j=0;j<length;j++)bin+=((i*17+j*13+j*j)%7<3?"1":"0")+"\n";
   el.textContent=bin;
   el.style.left=(i+.5)/count*100+"%";
   el.style.animationDuration=(10+(i*7%16))+"s";
   el.style.animationDelay=(-((i*13)%23))+"s";
   el.style.opacity=String(.22+((i*3)%6)/20);
   if(reduced)el.style.animation="none";
   fragment.appendChild(el);
 }
 host.appendChild(fragment);
}
let matrixResizeTimeout;
window.addEventListener("resize",()=>{clearTimeout(matrixResizeTimeout);matrixResizeTimeout=setTimeout(initMatrixRain,200)});
initMatrixRain();

/* Matrix / Cyberpunk themed atmospheric interactions. Local only, no network. */
(function(){
 const title=document.getElementById("cipher-title"),rabbit=document.getElementById("white-rabbit");
 const original="Base de Données Composants";
 const reduce=window.matchMedia("(prefers-reduced-motion: reduce)");
 let step=0;
 function renderCipher(){
   if(!title)return;
   if(reduce.matches||!["matrix","cyberpunk"].includes(document.documentElement.dataset.theme)){title.textContent=original;return;}
   const mode=step%3;
   const letters=Array.from(original);
   const transformed=letters.map((ch,i)=>{
     if(ch===" ")return " ";
     const n=ch.codePointAt(0);
     return mode===0?ch:mode===1?n.toString(16).toUpperCase().padStart(2,"0"):n.toString(2).padStart(8,"0");
   }).join(mode===0?"":" ");
   title.textContent="";
   const chars=Array.from(transformed);let i=0;
   function type(){
     if(!title||document.documentElement.dataset.theme==="classic")return;
     title.textContent=chars.slice(0,i).join("");
     if(i++<chars.length)setTimeout(type,Math.max(12,Math.min(50,2400/chars.length)));
   }
   type();step++;
 }
 renderCipher();setInterval(renderCipher,11500);
 // Occasional rabbit: small decorative silhouette, never captures pointer events.
 if(rabbit){
   rabbit.textContent="🐇";
   let hop=0;
   function visit(){
     if(reduce.matches||document.documentElement.dataset.theme!=="matrix"){rabbit.classList.remove("rabbit-active");return;}
     rabbit.style.left=(20+(hop*31)%65)+"%";
     rabbit.style.top=(32+(hop*17)%50)+"%";
     rabbit.classList.remove("rabbit-active");
     void rabbit.offsetWidth;
     rabbit.classList.add("rabbit-active");
     hop++;
     setTimeout(()=>rabbit.classList.remove("rabbit-active"),4300);
   }
   setInterval(visit,26000);
 }
})();
