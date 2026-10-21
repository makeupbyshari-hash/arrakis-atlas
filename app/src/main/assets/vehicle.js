(function(){
'use strict';
const c=window.ATLAS_CALC,vdb=window.ATLAS_VEHICLES,key='arrakis-workshop-v1';
const $=id=>document.getElementById(id);
const el=(tag,txt)=>{const n=document.createElement(tag);if(txt!==undefined)n.textContent=txt;return n};
let db;try{db=JSON.parse(localStorage.getItem(key))}catch(e){}
if(!db||typeof db!=='object')db={projects:[],stock:{},recipes:{}};
db.projects=Array.isArray(db.projects)?db.projects:[];db.stock=db.stock||{};db.recipes=db.recipes||{};
const save=()=>{try{localStorage.setItem(key,JSON.stringify(db))}catch(e){alert('Speichern fehlgeschlagen. Gerätespeicher prüfen.')}};
const idFor=(v,part,t)=>part==='harness'?'ornithoptertransportharness':part==='containervehicle'?'containervehicle':v.prefix+part+'_'+t;
const title=id=>c.label(id)+(c.names[id]?'':' (deutscher Itemname ungeprüft)');
let planned=[];
const choice=()=>({v:vdb[$('vehicle').value],tier:$('tier').value,purpose:$('purpose').value});
function start(){
 const v=vdb[$('vehicle').value],oldTier=+$('tier').value,oldPurpose=$('purpose').value;
 $('tier').replaceChildren();v.levels.forEach(n=>{const o=el('option','Typ '+n);o.value=n;$('tier').append(o)});
 $('tier').value=v.levels.includes(oldTier)?oldTier:(v.levels.includes(5)?5:v.levels[v.levels.length-1]);
 $('purpose').replaceChildren();v.purposes.forEach(([id,name])=>{const o=el('option',name);o.value=id;$('purpose').append(o)});
 $('purpose').value=v.purposes.some(x=>x[0]===oldPurpose)?oldPurpose:(v.prefix==='buggy'?'both':v.prefix==='ornithoptertransport'?'vehicles':v.purposes[0][0]);
 update();
}
function update(){
 const {v,tier,purpose}=choice(),hint=v.purposes.find(x=>x[0]===purpose);
 $('purposeHint').textContent=hint?hint[2]:'';
 planned=[];const selected=new Set();
 for(const [part,qty] of [...v.base,...(v.mods[purpose]||[])]){
   const id=idFor(v,part,tier);if(selected.has(id))continue;
   planned.push({id,qty,enabled:true,required:v.base.some(x=>x[0]===part)});selected.add(id);
 }
 const extra=new Set([...v.extra.map(x=>x[0]),...Object.values(v.mods).flat().map(x=>x[0])]);
 for(const part of extra){const id=idFor(v,part,tier);if(!selected.has(id)&&c.valid(id)){planned.push({id,qty:1,enabled:false,required:false});selected.add(id)}}
 draw();
}
function draw(){
 const root=$('parts');root.replaceChildren();
 for(const p of planned){
   const card=el('div');card.className='part';const head=el('div');head.className='parthead';
   const enabled=el('input');enabled.type='checkbox';enabled.checked=p.enabled;enabled.setAttribute('aria-label','Teil: '+title(p.id));
   enabled.onchange=()=>{p.enabled=enabled.checked;window.VP.refresh()};
   const name=el('strong',title(p.id));
   const qty=el('input');qty.type='number';qty.min=1;qty.max=99;qty.value=p.qty;qty.setAttribute('aria-label','Anzahl: '+title(p.id));
   qty.onchange=()=>{p.qty=Math.max(1,c.count(qty.value));qty.value=p.qty;window.VP.refresh()};
   head.append(enabled,name,qty);card.append(head);
   const group=el('div',p.required?'Grundbauteil':'Zusatzausrüstung · optional');group.className='muted';card.append(group);
   if(c.valid(p.id)){
     const d=el('details');d.append(el('summary','Herstellungsrezept anzeigen'));
     const ul=el('ul');
     for(const ing of c.recipes[p.id].ingredients)ul.append(el('li',Number(ing.qty).toLocaleString('de-DE')+' × '+title(ing.id)));
     d.append(ul);
     const stations=c.recipes[p.id].station||[];
     const station=el('div','Werkstatt: '+(stations.length?stations.join(', '):'in der Datenquelle nicht angegeben'));station.className='muted';d.append(station);card.append(d);
   }else{const pmsg=el('p','Für dieses Bauteil ist kein überprüftes Rezept hinterlegt.');pmsg.className='muted warning';card.append(pmsg)}
   root.append(card);
 }
 window.VP.refresh();
}
window.VP={c,vdb,db,save,$,el,title,choice,start,update,get planned(){return planned},refresh:()=>{}};
})();