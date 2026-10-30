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
function nav(){const icons={CPU:"◉",GPU:"▣",Motherboard:"▤",NVMe:"◫",SDD:"▥",PSU:"⌁",Extra:"✦",Case:"▰",RAM:"▥",Cooling:"❄"};$("categories").innerHTML=state.categories.map(c=>'<button data-page="'+esc(c)+'">'+icons[c]+' <span>'+esc(c)+'</span><em>'+state.items.filter(x=>x.category===c).length+'</em></button>').join("");document.querySelectorAll("nav button").forEach(b=>b.onclick=()=>navigate(b.dataset.page));}
function filters(category){return '<div class="filters"><input id="search" placeholder="Rechercher marque, modèle, référence…" value="'+esc(state.filters.q)+'"><select id="statusfilter"><option value="all">Tous les statuts</option>'+["installed","candidate","shortlisted","purchased","rejected"].map(v=>'<option value="'+v+'" '+(state.filters.status===v?"selected":"")+'>'+v+'</option>').join("")+'</select>'+(category?"":'<select id="catfilter"><option value="all">Toutes les catégories</option>'+state.categories.map(v=>'<option value="'+v+'" '+(state.filters.category===v?"selected":"")+'>'+v+'</option>').join("")+'</select>')+'</div>'}
function filtered(category){const q=state.filters.q.toLocaleLowerCase();return state.items.filter(d=>(!category||d.category===category)&&(category||state.filters.category==="all"||d.category===state.filters.category)&&(state.filters.status==="all"||d.status===state.filters.status)&&[d.full_name,d.manufacturer,d.model,d.category].join(" ").toLocaleLowerCase().includes(q));}
function table(items){return items.length?'<div class="table-wrap"><table><thead><tr>'+["Référence","Famille","Statut","Neuf","Occasion","Acquisition","Livraison","Total payé","Compatibilité"].map(s=>'<th>'+s+'</th>').join("")+'</tr></thead><tbody>'+items.map(d=>'<tr data-id="'+esc(d.id)+'"><td><strong>'+esc(d.full_name)+'</strong></td><td>'+esc(d.category)+'</td><td>'+status(d)+'</td><td>'+euros(price(d).new_eur)+'</td><td>'+euros(price(d).used_eur)+'</td><td>'+euros(price(d).acquisition_eur)+'</td><td>'+euros(price(d).shipping_eur)+'</td><td>'+euros(cost(d))+'</td><td>'+esc(d.compatibility?.status||"—")+'</td></tr>').join("")+'</tbody></table></div>':'<div class="empty">Aucun résultat pour ces filtres.</div>'}
function render(){const items=state.items;const paid=items.filter(acquired);const subtotal=sum(paid,d=>price(d).acquisition_eur);const shipping=sum(paid,d=>price(d).shipping_eur||0);const installed=items.filter(d=>d.status==="installed").length;
$("dashboard").innerHTML='<div class="cards">'+[['Références enregistrées',items.length,'Tous les fichiers JSON'],['Composants installés',installed,'Configuration actuelle'],['Achats renseignés',paid.length,'Prix effectivement payés'],['Total connu',euros(subtotal+shipping),'Livraison incluse']].map(([a,b,c],i)=>'<div class="stat"><div class="label">'+a+'</div><div class="value '+(i===3?"green":"")+'">'+b+'</div><div class="hint">'+c+'</div></div>').join("")+'</div><div class="panels"><div class="panel"><h2>Répartition des références</h2><div class="bars">'+state.categories.map(c=>{let n=items.filter(d=>d.category===c).length;return '<div class="barrow"><span>'+esc(c)+'</span><div class="track"><div class="bar" style="width:'+(items.length?100*n/items.length:0)+'%"></div></div><b>'+n+'</b></div>'}).join("")+'</div></div><div class="panel"><h2>Budget réel</h2><div class="budget-line"><span>Composants</span><strong>'+euros(subtotal)+'</strong></div><div class="budget-line"><span>Livraison</span><strong>'+euros(shipping)+'</strong></div><div class="budget-line total"><span>Total connu</span><strong>'+euros(subtotal+shipping)+'</strong></div><p class="muted">Les acquisitions non renseignées ne sont pas intégrées au total.</p></div></div><div class="section-head"><h2>Configuration installée</h2><span class="muted">'+installed+' références</span></div>'+cardgrid(items.filter(d=>d.status==="installed"));
$("budget").innerHTML='<div class="cards">'+[['Achats connus',paid.length],['Sous-total',euros(subtotal)],['Livraisons',euros(shipping)],['Total livré',euros(subtotal+shipping)]].map(([a,b])=>'<div class="stat"><div class="label">'+a+'</div><div class="value">'+b+'</div></div>').join("")+'</div><div class="panel"><h2>Dépenses par catégorie</h2><div class="bars">'+state.categories.map(c=>{let amount=sum(paid.filter(d=>d.category===c),d=>cost(d));return '<div class="barrow"><span>'+esc(c)+'</span><div class="track"><div class="bar" style="width:'+(subtotal+shipping?100*amount/(subtotal+shipping):0)+'%"></div></div><b>'+Math.round(amount)+' €</b></div>'}).join("")+'</div></div><div class="panel"><h2>Achats comptabilisés</h2>'+table(paid)+'</div>';
$("inventory").innerHTML='<div class="section-head"><h2>Toutes les références</h2><span class="muted">'+items.length+' fiches</span></div>'+filters(null)+'<div id="filteredcontent">'+table(filtered(null))+'</div>';
if(state.categories.includes(state.page)){$("category").innerHTML='<div class="section-head"><h2>Catalogue '+esc(state.page)+'</h2><span class="muted">'+items.filter(d=>d.category===state.page).length+' références</span></div>'+filters(state.page)+'<div id="filteredcontent">'+cardgrid(filtered(state.page))+'</div>'}
document.querySelectorAll("#search").forEach(el=>el.oninput=e=>{state.filters.q=e.target.value;updateFiltered();});document.querySelectorAll("#statusfilter").forEach(el=>el.onchange=e=>{state.filters.status=e.target.value;updateFiltered();});document.querySelectorAll("#catfilter").forEach(el=>el.onchange=e=>{state.filters.category=e.target.value;updateFiltered();});
document.querySelectorAll("[data-id]").forEach(el=>el.onclick=()=>openDetail(el.dataset.id));}
function updateFiltered(){const container=document.querySelector("section:not(.hidden) #filteredcontent");if(!container)return;container.innerHTML=state.page==="inventory"?table(filtered(null)):cardgrid(filtered(state.page));container.querySelectorAll("[data-id]").forEach(el=>el.onclick=()=>openDetail(el.dataset.id));}
const names={form_factor:"Format",socket:"Socket",chipset:"Chipset",memory_type:"Mémoire",vram_gb:"VRAM (Go)",vram_type:"Type de VRAM",memory_bus_bits:"Bus mémoire (bits)",cores:"Cœurs",threads:"Threads",pcie_minimum_generation:"PCIe minimum",pcie_gen:"Génération PCIe",capacity_gb:"Capacité (Go)",sequential_read_mbs:"Lecture (Mo/s)",sequential_write_mbs:"Écriture (Mo/s)",nominal_w:"Puissance (W)",certification:"Certification",modular:"Modularité",speed_mts:"Vitesse (MT/s)",cas_latency_cycles:"Latence CAS",rgb:"RGB",rpm:"Tours par minute",length_mm:"Longueur (mm)",height_mm:"Hauteur (mm)",tgp_w:"Consommation (W)"};
const fieldName=k=>names[k]||k.replace(/_/g," ").replace(/^./,x=>x.toUpperCase());
const fieldValue=v=>v===null||v===""||v===undefined?"Non renseigné":typeof v==="boolean"?(v?"Oui":"Non"):Array.isArray(v)?v.map(fieldValue).join(", "):typeof v==="object"?Object.entries(v).map(([k,x])=>fieldName(k)+": "+fieldValue(x)).join(" · "):String(v);
const detailsGrid=(o)=>'<div class="spec-grid">'+Object.entries(o||{}).filter(([,v])=>v!==undefined&&v!==null&&v!=="").map(([k,v])=>'<div class="spec-field"><small>'+esc(fieldName(k))+'</small><strong>'+esc(fieldValue(v))+'</strong></div>').join("")+'</div>';
function openDetail(id){
 const d=state.items.find(x=>x.id===id);if(!d)return;
 const p=price(d),photos=d._photos|| (d._photo?[d._photo]:[]);
 const gallery=photos.length?'<div class="detail-gallery">'+photos.map((url,i)=>'<img loading="lazy" src="'+esc(url)+'" alt="'+esc(d.full_name)+' - vue '+(i+1)+'">').join("")+'</div>':'<div class="detail-photo-missing">▣ &nbsp; Photographie non disponible dans Assets/'+esc(d.category)+'</div>';
 const prices={Neuf:euros(p.new_eur),Occasion:euros(p.used_eur),Acquisition:euros(p.acquisition_eur),Livraison:euros(p.shipping_eur),"Total payé":euros(cost(d))};
 const perf=d.performance||{};let perfText=Object.values(perf).some(v=>Array.isArray(v)?v.length:!!v)?detailsGrid(perf):'<p class="muted">Aucune mesure de performance validée.</p>';
 const sourceLinks=(d.sources||[]).map((x,i)=>{const url=typeof x==="string"?x:x.url;return (typeof url==="string"&&(url.startsWith("https://")||url.startsWith("http://")))?'<a href="'+esc(url)+'" rel="noopener noreferrer" target="_blank">Source '+(i+1)+' ↗</a>':""}).join(" ");
 $("modal-content").innerHTML='<div class="kicker">'+esc(d.category)+' · '+esc(d.manufacturer||"")+'</div><h2>'+esc(d.full_name)+'</h2>'+status(d)+gallery+
 '<h3 class="spec-title">Informations générales</h3>'+detailsGrid({Fabricant:d.manufacturer,Modèle:d.model,Référence:d.id,Statut:d.status,Compatibilité:d.compatibility?.status})+
 '<h3 class="spec-title">Caractéristiques techniques</h3>'+detailsGrid(d.specifications)+
 '<h3 class="spec-title">Prix</h3>'+detailsGrid(prices)+
 '<h3 class="spec-title">Performances</h3>'+perfText+
 '<h3 class="spec-title">Notes et sources</h3><p class="muted">'+esc(d.notes||"Aucune note")+'</p><div class="source-links">'+sourceLinks+'</div><p class="muted spec-path">'+esc(d._json||"")+'</p>';
 $("modal").classList.remove("hidden");
}
$("closemodal").onclick=$("closeback").onclick=()=>$("modal").classList.add("hidden");
document.addEventListener("keydown",e=>{if(e.key==="Escape")$("modal").classList.add("hidden")});
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
  }
  apply(document.documentElement.dataset.theme);
  if(selector)selector.addEventListener("change",()=>apply(selector.value));
})();
