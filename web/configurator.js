/* G11CD Configurator V1 — uses the existing /api/components catalog, not a copied database.
 * Locally authenticated profiles / SQLite configuration storage / readonly sharing.
 * Does not expose hardware account data to IA-TB Auth21 or the trading runtime.
 */
(function(){
'use strict';
const $c=id=>document.getElementById(id);
const icons={CPU:'cpu',GPU:'monitor',Motherboard:'circuit-board',RAM:'memory-stick',PSU:'power',Cooling:'fan',Case:'boxes',NVMe:'hard-drive',SDD:'hard-drive',HDD:'hard-drive',Extra:'plug'};
const categories=['CPU','Motherboard','RAM','GPU','Cooling','Case','PSU','NVMe','SDD','HDD','Extra'];
const titles={CPU:'Processeur',Motherboard:'Carte mère',RAM:'Mémoire RAM',GPU:'Carte graphique',Cooling:'Refroidissement',Case:'Boîtier',PSU:'Alimentation',NVMe:'Stockage NVMe',SDD:'Stockage SSD (catégorie SDD)',HDD:'Disque dur',Extra:'Extensions'};
const ico=(name,cl='')=>'<svg class="hw-icon '+cl+'" aria-hidden="true"><use href="/assets/icons.svg#i-'+(name||'cpu')+'"></use></svg>';
const clean=s=>esc(s??'');
const euro=v=>typeof v==='number'?new Intl.NumberFormat('fr-FR',{style:'currency',currency:'EUR'}).format(v):'—';
const cstate={config:{title:'Nouvelle configuration',description:'',purpose:'gaming',budget:null,components:[]},id:null,user:null,csrf:null,configs:[],picker:null,filter:'',status:'',share:null};
const specs=d=>d?.specifications||{};
const item=id=>state.items.find(x=>x.id===id);
function entries(cat){return cstate.config.components.filter(x=>x.category===cat);}
function activeItems(){return cstate.config.components.map(x=>({line:x,product:item(x.id)}));}
function selectPrice(d,mode){const p=d?.pricing||{};return mode==='new'?p.new_eur:mode==='used'?p.used_eur:mode==='owned'?0:mode==='custom'?null:null;}
function linePrice(line){if(line.price_mode==='owned')return 0;return typeof line.price_snapshot==='number'?line.price_snapshot:null;}
function totals(){const lines=activeItems(),known=lines.filter(x=>linePrice(x.line)!==null);return {sum:known.reduce((n,x)=>n+linePrice(x.line)*x.line.quantity,0),missing:lines.length-known.length,known:known.length,total:lines.length};}
const norm=v=>String(v??'').trim().toLowerCase();
const number=(o,keys)=>{for(const k of keys){const v=o?.[k];if(typeof v==='number'&&Number.isFinite(v))return v;}return null};
function checkCompatibility(config){
 const lines=config.components.map(x=>({line:x,product:item(x.id)}));const first=c=>lines.find(x=>x.line.category===c)?.product;
 const cpu=first('CPU'),mb=first('Motherboard'),ram=first('RAM'),gpu=first('GPU'),psu=first('PSU'),box=first('Case'),cooler=first('Cooling');
 const results=[];const add=(a,b,code,label,message)=>{if(a&&b)results.push({code,label,message});};
 if(cpu&&mb){let a=norm(specs(cpu).socket),b=norm(specs(mb).socket);add(a,b,a===b?'COMPATIBLE':'INCOMPATIBLE','Socket CPU / carte mère',a===b?'Socket '+a.toUpperCase()+' identique':'Sockets différents : '+a+' / '+b);if(!a||!b)results.push({code:'UNKNOWN',label:'Socket',message:'Information absente'});}
 if(mb&&ram){
  const a=norm(specs(mb).memory_type),b=norm(specs(ram).memory_type);
  if(a&&b)results.push({code:a===b?'COMPATIBLE':'INCOMPATIBLE',label:'Mémoire',message:a+' / '+b});
  else results.push({code:'UNKNOWN',label:'Mémoire DDR',message:'Type DDR non documenté sur les deux composants'});
 }
 if(gpu&&box){const length=number(specs(gpu),['length_mm','gpu_length_mm']),max=number(specs(box),['max_gpu_length_mm','gpu_max_length_mm']);
 if(length!==null&&max!==null)results.push({code:length<=max?'COMPATIBLE':'INCOMPATIBLE',label:'Longueur GPU / boîtier',message:length+' mm / '+max+' mm disponibles'});
 else results.push({code:'UNKNOWN',label:'Encombrement GPU',message:'Longueur de GPU ou espace boîtier non renseigné'});}
 if(psu&&(cpu||gpu)){const w=number(specs(psu),['nominal_w','wattage','wattage_w']);
 const load=(number(specs(cpu),['tdp_w','base_power_w'])||0)+(number(specs(gpu),['tgp_w','tdp_w','board_power_w'])||0)+75;
 if(w!==null&&cpu&&gpu&&number(specs(cpu),['tdp_w','base_power_w'])!==null&&number(specs(gpu),['tgp_w','tdp_w','board_power_w'])!==null)
  results.push({code:w>=Math.ceil(load*1.25)?'COMPATIBLE':'WARNING',label:'Puissance PSU (estimation)',message:'Charge estimée '+load+' W + 25 % de réserve ; PSU '+w+' W. Connecteurs non validés.'});
 else results.push({code:'UNKNOWN',label:'Puissance / connecteurs PSU',message:'Informations incomplètes : aucun accord de compatibilité présumé'});}
 if(cooler&&cpu){
  const list=specs(cooler).compatible_sockets||specs(cooler).sockets;
  if(Array.isArray(list)&&specs(cpu).socket)results.push({code:list.map(norm).includes(norm(specs(cpu).socket))?'COMPATIBLE':'INCOMPATIBLE',label:'Fixation refroidisseur',message:'Socket CPU : '+specs(cpu).socket});
  else results.push({code:'UNKNOWN',label:'Fixation refroidisseur',message:'Compatibilité des fixations à vérifier'});}
 if(!results.length)results.push({code:'NOT_CHECKED',label:'Compatibilité',message:'Sélectionne CPU, carte mère, GPU, RAM et PSU pour lancer les premiers contrôles.'});
 return results;
}
function navTo(p){navigate(p);if(p==='configurator')renderConfigurator();if(p==='myconfigs')renderMyConfigs();if(p==='profile')renderProfile();}
function status(text,error=false){cstate.status=text;$c('config-feedback').textContent=text;$c('config-feedback').dataset.error=String(error);}
function parts(){
 return categories.map(cat=>{const lines=entries(cat),selected=lines.map(x=>{const d=item(x.id);return '<div class="cfg-selected">'+
  '<span class="cfg-thumb">'+(d?ico(icons[cat]):'◈')+'</span><span class="cfg-selected-name"><strong>'+clean(d?.full_name||x.id)+'</strong><small>'+x.quantity+' × '+euro(linePrice(x))+(d?'':' · Référence absente du catalogue')+'</small></span>'+
  '<label class="cfg-qty">Qté <input data-qty-id="'+clean(x.id)+'" type="number" min="1" max="16" value="'+x.quantity+'"></label><select data-price-id="'+clean(x.id)+'" aria-label="Prix de '+clean(x.id)+'">'+['new','used','owned','custom','unknown'].map(v=>'<option value="'+v+'" '+(x.price_mode===v?'selected':'')+'>'+({new:'Neuf',used:'Occasion',owned:'Déjà possédé',custom:'Prix personnel',unknown:'Prix inconnu'}[v])+'</option>').join('')+'</select>'+
  '<button type="button" class="cfg-mini" data-remove="'+clean(x.id)+'" aria-label="Retirer '+clean(x.id)+'">'+ico('minus')+'</button></div>';}).join('');
 return '<section class="cfg-part"><div class="cfg-part-head">'+ico(icons[cat])+'<strong>'+titles[cat]+'</strong><span class="cfg-count">'+lines.length+'</span><button type="button" data-pick="'+cat+'">'+ico('plus')+' Ajouter</button></div>'+selected+'</section>';}).join('');
}
function summary(){
 const t=totals(),tests=checkCompatibility(cstate.config),bad=tests.filter(x=>x.code==='INCOMPATIBLE').length,warning=tests.filter(x=>['WARNING','UNKNOWN'].includes(x.code)).length;
 return '<section class="cfg-summary"><div class="cfg-overline">'+ico('calculator')+' RÉCAPITULATIF</div><strong class="cfg-total">'+euro(t.sum)+'</strong><div class="cfg-muted">Sous-total connu · '+t.missing+' ligne(s) sans prix vérifié</div>'+
 (typeof cstate.config.budget==='number'?'<div class="cfg-budget">Budget : '+euro(cstate.config.budget)+' · '+(cstate.config.budget-t.sum>=0?'Reste':'Dépassement')+' '+euro(Math.abs(cstate.config.budget-t.sum))+'</div>':'')+
 '<div class="cfg-kpis"><span>'+t.total+' composants</span><span>'+bad+' incompatibilités</span><span>'+warning+' à vérifier</span></div><h3>'+ico('shield-check')+' Compatibilité</h3>'+
 tests.map(x=>'<div class="cfg-check '+x.code.toLowerCase()+'"><strong>'+clean(x.code)+' · '+clean(x.label)+'</strong><small>'+clean(x.message)+'</small></div>').join('')+
 '<div class="cfg-actions"><button class="primary" id="cfg-save">'+ico('save')+' Enregistrer</button><button id="cfg-export">'+ico('download')+' Export JSON</button><button id="cfg-share" '+(!cstate.id||!cstate.user?'disabled':'')+'>'+ico('share-2')+' Partager</button></div>'+
 '<div id="config-feedback" class="cfg-feedback" role="status">'+clean(cstate.status)+'</div><p class="cfg-hint">Les informations manquantes restent inconnues. Le partage URL est local tant que le serveur utilise 127.0.0.1.</p></section>';
}
function renderConfigurator(){
 const root=$c('configurator');if(!root)return;
 root.innerHTML='<div class="section-head"><h2>'+ico('circuit-board')+' Configurateur PC</h2><span class="muted">Catalogue JSON · zéro prix inventé</span></div>'+
 '<div class="cfg-head"><label>Nom <input id="cfg-title" maxlength="100" value="'+clean(cstate.config.title)+'"></label><label>Utilisation <select id="cfg-purpose">'+['gaming','workstation','office','mini-pc','custom'].map(x=>'<option value="'+x+'" '+(x===cstate.config.purpose?'selected':'')+'>'+({gaming:'Gaming',workstation:'Workstation',office:'Bureautique','mini-pc':'Mini-PC',custom:'Personnalisée'}[x])+'</option>').join('')+'</select></label><label>Budget (€) <input id="cfg-budget" type="number" min="0" max="1000000" step="1" value="'+(cstate.config.budget??'')+'"></label><button id="cfg-new">'+ico('plus')+' Nouvelle</button><button id="cfg-import">'+ico('upload')+' Importer JSON</button><input id="cfg-import-file" type="file" accept=".json,application/json" hidden></div>'+
 '<div class="cfg-layout"><div class="cfg-parts">'+parts()+'</div>'+summary()+'</div>';
 root.querySelectorAll('[data-pick]').forEach(b=>b.onclick=()=>openPicker(b.dataset.pick));
 root.querySelectorAll('[data-remove]').forEach(b=>b.onclick=()=>{cstate.config.components=cstate.config.components.filter(x=>x.id!==b.dataset.remove);renderConfigurator();});
 root.querySelectorAll('[data-price-id]').forEach(s=>s.onchange=()=>{const l=cstate.config.components.find(x=>x.id===s.dataset.priceId);l.price_mode=s.value;l.price_snapshot=selectPrice(item(l.id),s.value);if(s.value==='custom'){const input=prompt('Prix personnalisé vérifié (€) :','');if(input===null){l.price_mode='unknown';l.price_snapshot=null;}else{const v=Number(input.replace(',','.'));if(!Number.isFinite(v)||v<0||v>500000){l.price_mode='unknown';l.price_snapshot=null;}else l.price_snapshot=v;}}renderConfigurator();});
 root.querySelectorAll('[data-qty-id]').forEach(q=>q.onchange=()=>{const l=cstate.config.components.find(x=>x.id===q.dataset.qtyId);l.quantity=Math.max(1,Math.min(16,Math.floor(Number(q.value)||1)));renderConfigurator();});
 $c('cfg-title').onchange=e=>cstate.config.title=e.target.value;
 $c('cfg-purpose').onchange=e=>cstate.config.purpose=e.target.value;
 $c('cfg-budget').onchange=e=>{cstate.config.budget=e.target.value===''?null:Number(e.target.value);renderConfigurator();};
 $c('cfg-new').onclick=()=>{cstate.id=null;cstate.config={title:'Nouvelle configuration',description:'',purpose:'gaming',budget:null,components:[]};status('Nouvelle configuration créée.');renderConfigurator();};
 $c('cfg-import').onclick=()=>$c('cfg-import-file').click();
 $c('cfg-import-file').onchange=async e=>{const file=e.target.files?.[0];if(!file)return;if(file.size>131072){status('Fichier trop volumineux.',true);return;}try{const data=JSON.parse(await file.text());if(!data||typeof data.title!=='string'||!Array.isArray(data.components)||data.components.length>64||data.components.some(x=>!x||typeof x.id!=='string'||!categories.includes(x.category))){throw Error('Schéma de configuration incompatible');}cstate.id=null;cstate.config={title:data.title.slice(0,100),description:String(data.description||'').slice(0,1500),purpose:String(data.purpose||'custom').slice(0,60),budget:typeof data.budget==='number'?data.budget:null,components:data.components.map(x=>({id:x.id,category:x.category,quantity:Math.max(1,Math.min(16,Math.floor(Number(x.quantity)||1))),price_mode:['new','used','owned','custom','unknown'].includes(x.price_mode)?x.price_mode:'unknown',price_snapshot:typeof x.price_snapshot==='number'&&x.price_snapshot>=0?x.price_snapshot:null}))};status('Configuration JSON importée localement. Enregistre-la dans ton profil si nécessaire.');renderConfigurator();}catch(err){status('Import impossible : '+err.message,true);}};
 $c('cfg-save').onclick=saveConfig;
 $c('cfg-export').onclick=exportConfig;
 $c('cfg-share').onclick=shareConfig;
}
function openPicker(cat){
 cstate.picker=cat;cstate.filter='';renderPicker();
}
function renderPicker(){
 const modal=$c('cfg-picker'),cat=cstate.picker;
 const all=state.items.filter(d=>d.category===cat&&[d.full_name,d.manufacturer,d.model,d.id].join(' ').toLowerCase().includes(cstate.filter.toLowerCase()));
 modal.classList.remove('hidden');
 modal.innerHTML='<div class="cfg-picker-box" role="dialog" aria-modal="true" aria-label="Sélectionner '+titles[cat]+'"><div class="cfg-picker-top"><strong>'+ico(icons[cat])+' Choisir : '+titles[cat]+'</strong><button id="cfg-picker-close" aria-label="Fermer">✕</button></div><input id="cfg-picker-search" placeholder="Rechercher marque, modèle, référence…" value="'+clean(cstate.filter)+'"><div class="cfg-picker-items">'+all.slice(0,120).map(d=>'<button class="cfg-option" data-component="'+clean(d.id)+'"><span class="cfg-small-img">'+(d._photo?'<img loading="lazy" src="'+clean(d._photo)+'" alt="">':ico(icons[cat]))+'</span><span><strong>'+clean(d.full_name)+'</strong><small>'+clean([specs(d).socket,specs(d).memory_type,specs(d).vram_gb?'VRAM '+specs(d).vram_gb+' Go':''].filter(Boolean).join(' · ')||'Spécifications à vérifier')+'</small></span><span class="cfg-price">'+euro(d.pricing?.used_eur)+'</span></button>').join('')+'</div><small class="cfg-muted">'+all.length+' références · affichage limité aux 120 premiers résultats, utiliser la recherche</small></div>';
 $c('cfg-picker-close').onclick=closePicker;
 $c('cfg-picker-search').oninput=e=>{cstate.filter=e.target.value;renderPicker();$c('cfg-picker-search').focus();$c('cfg-picker-search').setSelectionRange(cstate.filter.length,cstate.filter.length);};
 modal.querySelectorAll('[data-component]').forEach(b=>b.onclick=()=>{const d=item(b.dataset.component);if(!d)return;
 // Single-instance categories can be replaced; storage/RAM/Extra allow multiple choices.
 if(!['RAM','NVMe','SDD','HDD','Extra'].includes(cat))cstate.config.components=cstate.config.components.filter(x=>x.category!==cat);
 if(!cstate.config.components.some(x=>x.id===d.id))cstate.config.components.push({id:d.id,category:cat,quantity:1,price_mode:'used',price_snapshot:selectPrice(d,'used')});
 closePicker();renderConfigurator();});
}
function closePicker(){$c('cfg-picker').classList.add('hidden');cstate.picker=null;}
function exportConfig(){
 const blob=new Blob([JSON.stringify({...cstate.config,schema_version:1},null,2)],{type:'application/json'});
 const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='G11CD-configuration.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),500);
}
async function api(url,method='GET',data){
 const headers={'Content-Type':'application/json'};
 if(method!=='GET'&&cstate.csrf)headers['X-CSRF-Token']=cstate.csrf;
 const r=await fetch(url,{method,headers,credentials:'same-origin',cache:'no-store',body:data===undefined?undefined:JSON.stringify(data)});
 const j=await r.json().catch(()=>({error:'Réponse non JSON'}));
 if(!r.ok)throw Error(j.error||'Erreur HTTP '+r.status);
 return j;
}
async function authRefresh(){try{const x=await api('/api/auth/me');cstate.user=x.user;cstate.csrf=x.csrf;}catch(e){cstate.user=null;cstate.csrf=null;}}
async function saveConfig(){
 cstate.config.title=$c('cfg-title').value.trim();cstate.config.purpose=$c('cfg-purpose').value;
 if(!cstate.user){status('Connecte-toi dans « Mon profil » pour enregistrer. L’export JSON fonctionne sans compte.',true);return;}
 try{const res=await api(cstate.id?'/api/configurations/'+cstate.id:'/api/configurations','POST',cstate.config);cstate.id=res.configuration.id;status('Configuration sauvegardée dans ton profil.');}
 catch(e){status(e.message,true);}
 renderConfigurator();
}
async function shareConfig(){
 if(!cstate.user||!cstate.id){status('Enregistre et connecte-toi avant le partage.',true);return;}
 try{const result=await api('/api/configurations/'+cstate.id+'/share','POST',{enabled:true});const url=location.origin+'/?share='+encodeURIComponent(result.token);
 cstate.share={url,expires_at:result.expires_at};await navigator.clipboard.writeText(url).catch(()=>{});
 status('Lien en lecture seule généré (accès depuis ce serveur uniquement).');showShareDialog();}
 catch(e){status(e.message,true);}
}
function showShareDialog(){
 const x=cstate.share;if(!x)return;
 $c('cfg-sharing').classList.remove('hidden');
 $c('cfg-sharing').innerHTML='<div class="cfg-picker-box cfg-share-dialog" role="dialog" aria-modal="true"><h3>'+ico('share-2')+' Partage de la configuration</h3><p>Le lien permet la lecture seule, pendant 30 jours, depuis ce serveur. Si tu utilises localhost, il n’est PAS accessible à Internet.</p><input id="cfg-share-url" readonly value="'+clean(x.url)+'"><div class="cfg-actions"><button id="cfg-copy">Copier le lien</button><button id="cfg-revoke">Révoquer</button><button id="cfg-share-close">Fermer</button></div></div>';
 $c('cfg-copy').onclick=()=>navigator.clipboard.writeText(x.url);
 $c('cfg-share-close').onclick=()=>$c('cfg-sharing').classList.add('hidden');
 $c('cfg-revoke').onclick=async()=>{await api('/api/configurations/'+cstate.id+'/share','POST',{enabled:false});$c('cfg-sharing').classList.add('hidden');status('Lien révoqué.');};
}
function renderProfile(){
 const root=$c('profile');if(!root)return;
 if(cstate.user){root.innerHTML='<div class="section-head"><h2>'+ico('users-round')+' Mon profil</h2></div><div class="panel cfg-account"><h3>'+clean(cstate.user.username)+'</h3><p>Profil local privé. Tes configurations sont enregistrées sur ce serveur.</p><div class="cfg-actions"><button id="cfg-logout">Déconnexion</button><button id="cfg-account-delete">Supprimer mon compte</button></div><p id="cfg-auth-feedback" role="status"></p></div>';
 $c('cfg-logout').onclick=async()=>{await api('/api/auth/logout','POST',{});cstate.user=null;cstate.csrf=null;renderProfile();};
 $c('cfg-account-delete').onclick=async()=>{const confirmName=prompt('Suppression définitive du compte et de ses configurations : écrire exactement '+cstate.user.username);if(confirmName!==cstate.user.username)return;try{await api('/api/auth/delete-account','POST',{confirm:confirmName});cstate.user=null;cstate.csrf=null;renderProfile();}catch(e){$c('cfg-auth-feedback').textContent=e.message;}};
 return;}
 root.innerHTML='<div class="section-head"><h2>'+ico('users-round')+' Connexion Hardware Lab</h2></div><div class="panel cfg-account"><h3>Un profil pour retrouver tes configurations</h3><p>Les comptes sont locaux à Hardware Lab, indépendants d’IA-TB Auth21.</p><label>Identifiant <input id="cfg-user" autocomplete="username" minlength="3" maxlength="48"></label><label>Mot de passe <input id="cfg-pass" type="password" autocomplete="current-password" minlength="12"></label><div class="cfg-actions"><button id="cfg-login" class="primary">Connexion</button><button id="cfg-register">Créer mon compte</button></div><p id="cfg-auth-feedback" role="status"></p></div>';
 async function submit(action){try{const result=await api('/api/auth/'+action,'POST',{username:$c('cfg-user').value,password:$c('cfg-pass').value});cstate.user=result.user;cstate.csrf=result.csrf;renderProfile();}catch(e){$c('cfg-auth-feedback').textContent=e.message;}}
 $c('cfg-login').onclick=()=>submit('login');$c('cfg-register').onclick=()=>submit('register');
}
async function renderMyConfigs(){
 const root=$c('myconfigs');if(!root)return;
 if(!cstate.user){root.innerHTML='<div class="panel"><h2>Mes configurations</h2><p>Connecte-toi dans « Mon profil » pour retrouver tes configurations enregistrées.</p><button id="cfg-to-login">Connexion</button></div>';$c('cfg-to-login').onclick=()=>navTo('profile');return;}
 root.innerHTML='<div class="section-head"><h2>'+ico('save')+' Mes configurations</h2><span class="muted">Compte : '+clean(cstate.user.username)+'</span></div><div id="cfg-saved-list" class="grid"></div>';
 try{const x=await api('/api/configurations');cstate.configs=x.configurations;const box=$c('cfg-saved-list');
 box.innerHTML=x.configurations.map(c=>'<div class="item-card cfg-saved-card"><strong>'+clean(c.title)+'</strong><small>'+c.components.length+' composants · '+new Date(c.updated_at*1000).toLocaleDateString('fr-FR')+'</small><div class="cfg-actions"><button data-open="'+c.id+'">Ouvrir</button><button data-copy="'+c.id+'">Dupliquer</button><button data-delete="'+c.id+'">Supprimer</button></div></div>').join('')||'<div class="panel">Aucune configuration enregistrée.</div>';
 box.querySelectorAll('[data-open]').forEach(b=>b.onclick=()=>{const c=cstate.configs.find(x=>x.id===b.dataset.open);cstate.id=c.id;cstate.config={title:c.title,description:c.description,purpose:c.purpose,budget:c.budget,components:c.components.map(x=>({...x}))};navTo('configurator');});
 box.querySelectorAll('[data-copy]').forEach(b=>b.onclick=async()=>{await api('/api/configurations/'+b.dataset.copy+'/duplicate','POST',{});renderMyConfigs();});
 box.querySelectorAll('[data-delete]').forEach(b=>b.onclick=async()=>{if(!confirm('Supprimer définitivement cette configuration ?'))return;await api('/api/configurations/'+b.dataset.delete,'POST',{_delete:true});renderMyConfigs();});
 }catch(e){$c('cfg-saved-list').textContent=e.message;}
}
async function loadPublicShare(){
 const token=new URLSearchParams(location.search).get('share');if(!token)return;
 try{const x=await api('/api/shared/'+encodeURIComponent(token)),c=x.configuration;
 const root=$c('publicconfig');root.classList.remove('hidden');
 root.innerHTML='<div class="panel"><h2>'+ico('share-2')+' Configuration partagée (lecture seule)</h2><h3>'+clean(c.title)+'</h3><p>'+clean(c.description||'')+'</p><div class="cfg-public-parts">'+c.components.map(l=>{const d=item(l.id);return '<div class="cfg-public-line"><strong>'+clean(d?.full_name||l.id)+'</strong><span>'+l.quantity+' × '+euro(l.price_snapshot)+'</span></div>'}).join('')+'</div><p>Les prix proviennent des snapshots sélectionnés lors de la sauvegarde ; leur fraîcheur n’est pas garantie.</p><button id="cfg-public-close">Fermer</button></div>';
 $c('cfg-public-close').onclick=()=>{root.classList.add('hidden');history.replaceState(null,'',location.pathname);};
 }catch(e){$c('publicconfig').classList.remove('hidden');$c('publicconfig').textContent='Lien introuvable, expiré ou révoqué.';}
}
document.addEventListener('keydown',e=>{if(e.key==='Escape'){if(!$c('cfg-picker').classList.contains('hidden'))closePicker();$c('cfg-sharing').classList.add('hidden');}});
window.renderConfigurator=renderConfigurator;
window.renderMyConfigs=renderMyConfigs;
window.renderProfile=renderProfile;
window.refreshConfigurator=()=>{if(state.page==='configurator')renderConfigurator();};
window.hardwareConfiguratorReady=(async()=>{await authRefresh();if(state.page==='profile')renderProfile();await loadPublicShare();})();
})();
