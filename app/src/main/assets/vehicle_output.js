(function(){
'use strict';
const V=window.VP,{c,db,$,el,title,save}=V;
function rows(object,root){
 const entries=Object.entries(object).filter(x=>Number(x[1])>0).sort((a,b)=>title(a[0]).localeCompare(title(b[0]),'de'));
 if(!entries.length){root.append(el('p','Keine'));return}
 for(const [id,qty] of entries){
   const div=el('div');div.className='line';
   div.append(el('span',title(id)),el('b',Number(qty).toLocaleString('de-DE')+' ×'));root.append(div);
 }
}
V.refresh=function(){
 const {v,tier}=V.choice(),parts=V.planned.filter(x=>x.enabled),result=c.calculate(parts,db.stock);
 const box=$('summary');box.replaceChildren();
 box.append(el('strong',v.label+' · '+$('purpose').selectedOptions[0].textContent+' · Typ '+tier));
 const link=el('a','Materialliste ansehen ↓');link.href='#results';link.style.display='block';link.style.color='#f2cf96';
 box.append(el('div',parts.reduce((sum,x)=>sum+c.count(x.qty),0)+' ausgewählte Bauteile'),link);
 const out=$('results');out.replaceChildren();
 const primary=el('div');primary.className='results';primary.append(el('h3','Noch benötigte Materialien, Rohstoffe und Beute'));
 rows(result.gather,primary);out.append(primary);
 const cols=el('div');cols.className='columns';
 const craft=el('div');craft.append(el('h3','Herzustellende Teile und Zwischenprodukte'));rows(result.produced,craft);
 const used=el('div');used.append(el('h3','Vorhandenes Material angerechnet'));rows(result.used,used);cols.append(craft,used);out.append(cols);
 const station=el('p',result.stations.length?'Werkstätten aus der Rezeptquelle: '+result.stations.join(', '):'Fahrzeugbauteile: '+(Number(tier)>=6?'Fortschrittlicher Fahrzeugfabrikator':'Fahrzeugfabrikator')+' (laut deutschsprachiger Fahrzeugdatenbank; einzelne Sonderteile prüfen).');
 station.className='muted';out.append(station);
 if(result.cycles.length){const warning=el('p','Fehlerhafter Rezeptkreislauf: '+result.cycles.join('; '));warning.className='warning';out.append(warning)}
 if(Object.keys(result.surplus).length)out.append(el('p','Überschuss durch Rezeptmengen: '+Object.entries(result.surplus).map(([id,n])=>n+' × '+title(id)).join(', ')));
 const note=el('p','Gegenstände ohne Rezept gelten als direkt zu beschaffen. Nicht alles im Spiel ist herstellbar.');note.className='muted';out.append(note);
};
function listStock(){
 const root=$('stockList');root.replaceChildren();
 for(const [name,qty] of Object.entries(db.stock).filter(x=>Number(x[1])>0)){
   const line=el('div');line.className='line';
   const button=el('button','Entfernen');button.onclick=()=>{delete db.stock[name];save();listStock();V.refresh()};
   line.append(el('span',name+' · '+qty+' ×'),button);root.append(line);
 }
}
$('addStock').onclick=()=>{
 const value=$('stockItem').value.trim();if(!value)return;
 const id=c.resolve(value),name=c.label(id);
 for(const k of Object.keys(db.stock))if(c.resolve(k)===id)delete db.stock[k];
 db.stock[name]=c.count($('stockQty').value);save();listStock();V.refresh();$('stockItem').value='';
};
$('saveProject').onclick=()=>{
 const {v,tier}=V.choice(),purpose=$('purpose').selectedOptions[0].textContent;
 const items=V.planned.filter(p=>p.enabled).map(p=>({name:c.label(p.id),qty:c.count(p.qty)}));
 if(!items.length){alert('Bitte zuerst Fahrzeugteile auswählen.');return}
 const name=v.label+' Typ '+tier+' – '+purpose;
 db.projects.push({id:'vehicle-'+Date.now(),name,items});save();
 $('saveMessage').textContent='Bauprojekt gespeichert: '+name+'. Unter „Werkstatt & Projekte“ findest du es wieder.';
};
$('vehicle').onchange=V.start;$('tier').onchange=V.update;$('purpose').onchange=V.update;
const data=$('nameOptions');const names=new Set([...Object.values(c.names),...(window.ARRAKIS_ITEMS||[]).map(x=>x.name).filter(Boolean)]);
[...names].sort((a,b)=>a.localeCompare(b,'de')).forEach(name=>{const o=el('option');o.value=name;data.append(o)});
const incoming=new URLSearchParams(location.search).get('vehicle');
if(incoming&&V.vdb[incoming])$('vehicle').value=incoming;
V.start();listStock();
})();