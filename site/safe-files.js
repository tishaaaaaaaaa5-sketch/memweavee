/* Safe, bounded JSON backup handling for the browser-local MemWeave workspace. */
(function(root,factory){
  const api=factory();
  if(typeof module==="object"&&module.exports)module.exports=api;
  if(root)root.MemWeaveSafeFiles=api;
})(typeof globalThis!=="undefined"?globalThis:this,function(){
  "use strict";
  const FORMAT="memweave-local-v2";
  const MAX_FILE_BYTES=5*1024*1024;
  const MAX_ITEMS=5000;
  const MAX_TEXT=20000;
  const MAX_SOURCE_TEXT=50000;
  const MAX_SOURCE=300;
  const ROLES=new Set(["user","assistant","system","human","ai","unlabelled"]);
  const FACETS=new Set(["goal","priorities","priority:evidence_retention","priority:downstream_answer_quality","priority:reproducibility","priority:other","technical","technical:stack","hard:token_accounting","principles","principles:benchmark_reporting","metrics","milestone","general"]);
  function cleanString(value,max,required=false){
    if(typeof value!=="string")return required?null:"";
    const clean=value.replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F]/g,"").trim();
    if(required&&!clean)return null;
    return clean.slice(0,max);
  }
  function safeNumber(value,min,max,fallback){
    const n=Number(value);
    return Number.isFinite(n)&&n>=min&&n<=max?n:fallback;
  }
  function normalizeItem(raw,options={}){
    if(!raw||typeof raw!=="object"||Array.isArray(raw))return null;
    const text=cleanString(raw.text,MAX_TEXT,true);
    if(!text)return null;
    const role=ROLES.has(raw.role)?raw.role:"unlabelled";
    const source=cleanString(raw.source,MAX_SOURCE)||"Imported backup";
    const item={
      id:options.regenerateIds===false?cleanString(raw.id,100)||"": "",
      role,source,text,
      words:countWords(text)
    };
    const sourceText=cleanString(raw.sourceText,MAX_SOURCE_TEXT);
    if(sourceText)item.sourceText=sourceText;
    const sourceId=cleanString(raw.sourceId,200);
    if(sourceId)item.sourceId=sourceId;
    const kind=cleanString(raw.kind,80);
    if(kind)item.kind=kind;
    const facet=cleanString(raw.facet,100);
    if(facet&&FACETS.has(facet))item.facet=facet;
    const derivation=cleanString(raw.derivation,40);
    if(["direct","context_resolved"].includes(derivation))item.derivation=derivation;
    for(const key of ["messageIndex","sentenceIndex","selectionOrder"]){
      const n=safeNumber(raw[key],0,1000000,null);
      if(n!==null)item[key]=Math.floor(n);
    }
    if(Array.isArray(raw.reasons))item.reasons=raw.reasons.slice(0,20).map(x=>cleanString(x,240)).filter(Boolean);
    if(raw.features&&typeof raw.features==="object"&&!Array.isArray(raw.features)){
      const features={};
      for(const key of ["novelty","meanSimilarity","top3Similarity","recencyRank","userFraction","firstPersonRate","digitRate"]){
        const n=safeNumber(raw.features[key],0,1,null);
        if(n!==null)features[key]=n;
      }
      if(Object.keys(features).length)item.features=features;
    }
    const createdAt=cleanString(raw.createdAt,40);
    if(createdAt&&Number.isFinite(Date.parse(createdAt)))item.createdAt=createdAt;
    return item;
  }
  function countWords(text){return (String(text||"").match(/[A-Za-z0-9]+(?:['’][A-Za-z0-9]+)*/g)||[]).length;}
  function byteLength(text){return typeof TextEncoder!=="undefined"?new TextEncoder().encode(text).length:unescape(encodeURIComponent(text)).length;}
  function normalizeItems(input,options={}){
    if(!Array.isArray(input))throw new Error("Backup items must be a JSON array.");
    if(input.length>MAX_ITEMS)throw new Error("Backup contains too many items (maximum "+MAX_ITEMS+").");
    const items=[],seen=new Set();let skipped=0;
    for(const raw of input){
      const item=normalizeItem(raw,options);
      if(!item){skipped++;continue;}
      const key=item.text.toLowerCase()+"\u0000"+item.source.toLowerCase()+"\u0000"+(item.sourceId||"");
      if(seen.has(key)){skipped++;continue;}
      seen.add(key);items.push(item);
    }
    return {items,skipped};
  }
  function parseBackup(text){
    if(typeof text!=="string")throw new Error("The selected file could not be read as text.");
    if(byteLength(text)>MAX_FILE_BYTES)throw new Error("Backup is larger than the 5 MB import limit.");
    let data;
    try{data=JSON.parse(text);}catch(_){throw new Error("File is not valid JSON.");}
    if(Array.isArray(data))data={format:"memweave-local-v1",items:data};
    if(!data||typeof data!=="object"||Array.isArray(data))throw new Error("Backup must contain a JSON object.");
    if(!["memweave-local-v1",FORMAT].includes(data.format))throw new Error("Unsupported backup format. Choose a MemWeave JSON backup.");
    const result=normalizeItems(data.items);
    if(!result.items.length)throw new Error("No valid memory items were found in this backup.");
    return {...result,format:FORMAT};
  }
  function exportBackup(items){
    const result=normalizeItems(items,{regenerateIds:false});
    const payload={format:FORMAT,exportedAt:new Date().toISOString(),privacy:"Contains saved evidence text and may include source excerpts. Keep this file private.",items:result.items};
    const json=JSON.stringify(payload,null,2);
    if(byteLength(json)>MAX_FILE_BYTES)throw new Error("Export exceeds the 5 MB backup limit. Export fewer memory items.");
    return json;
  }
  return {FORMAT,MAX_FILE_BYTES,MAX_ITEMS,MAX_TEXT,MAX_SOURCE_TEXT,normalizeItem,normalizeItems,parseBackup,exportBackup,countWords};
});
