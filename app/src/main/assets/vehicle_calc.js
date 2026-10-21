(function(){
'use strict';
const data=window.ATLAS_RECIPE_DATA||{},recipes=data.items||{},names=data.names||{};
const normalize=s=>String(s||'').toLocaleLowerCase('de-DE').normalize('NFD').replace(/[\u0300-\u036f]/g,'').trim();
const label=id=>names[id]||id;
const lookup=new Map();
for(const [id,name] of Object.entries(names)){lookup.set(normalize(id),id);if(!lookup.has(normalize(name)))lookup.set(normalize(name),id)}
for(const [id,rec] of Object.entries(recipes)){lookup.set(normalize(id),id);if(rec.name&&!lookup.has(normalize(rec.name)))lookup.set(normalize(rec.name),id)}
for(const obj of window.ARRAKIS_ITEMS||[]){const id=lookup.get(normalize(obj.id));if(id&&obj.name)lookup.set(normalize(obj.name),id)}
const valid=id=>!!recipes[id]&&Array.isArray(recipes[id].ingredients)&&recipes[id].ingredients.length>0;
const count=value=>Math.max(0,Math.min(999999,Math.floor(Number(value)||0)));
function calculate(parts,stockSource){
 const stock={},needed={},produced={},used={},gather={},surplus={},stations=new Set(),cycle=new Set(),seen={},order=[];
 const toId=name=>lookup.get(normalize(name))||String(name||'').trim();
 for(const [key,v] of Object.entries(stockSource||{})){const id=toId(key);stock[id]=(stock[id]||0)+count(v)}
 const visit=(id,parents=[])=>{
   if(seen[id]===1){cycle.add([...parents,id].map(label).join(' → '));return}
   if(seen[id]===2)return;
   seen[id]=1;
   if(valid(id))for(const ing of recipes[id].ingredients)visit(ing.id,[...parents,id]);
   seen[id]=2;order.push(id);
 };
 for(const part of parts){if(!part.enabled||!count(part.qty))continue;needed[part.id]=(needed[part.id]||0)+count(part.qty);visit(part.id)}
 order.reverse().forEach(id=>{
   let qty=needed[id]||0;if(qty<=0)return;
   const own=Math.min(qty,stock[id]||0);
   if(own){qty-=own;stock[id]-=own;used[id]=(used[id]||0)+own}
   if(qty<=0)return;
   if(!valid(id)){gather[id]=(gather[id]||0)+qty;return}
   const recipe=recipes[id],perBatch=Math.max(1,Number(recipe.output)||1),batches=Math.ceil(qty/perBatch);
   produced[id]=(produced[id]||0)+batches*perBatch;
   const extra=batches*perBatch-qty;
   if(extra)surplus[id]=(surplus[id]||0)+extra;
   for(const s of recipe.station||[])stations.add(s);
   for(const ing of recipe.ingredients){const n=Number(ing.qty)||0;if(n>0)needed[ing.id]=(needed[ing.id]||0)+n*batches}
 });
 return {gather,produced,used,surplus,stations:[...stations],cycles:[...cycle],recipeCount:Object.keys(recipes).length};
}
window.ATLAS_CALC={data,recipes,names,normalize,label,lookup,valid,count,calculate,resolve:s=>lookup.get(normalize(s))||s};
})();