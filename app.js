/* MemWeave browser-local workspace. The scoring policy is an explicit heuristic baseline, not a trained model. */
(()=>{"use strict";
const Engine=window.MemWeaveEngine;
if(!Engine){document.body.innerHTML='<main style="padding:32px;color:#fff">MemWeave could not load its evidence engine. Refresh the page or check the deployed files.</main>';return}
const DB="memweave.browser.workspace.v2";let items=load(),pending=[];
const $=id=>document.getElementById(id);
const newId=()=>typeof crypto!=="undefined"&&crypto.randomUUID?crypto.randomUUID():String(Date.now())+Math.random();
function esc(s){return String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]))}
function load(){
 for(const key of [DB,"memweave.browser.workspace.v1"]){
  try{
   const v=JSON.parse(localStorage.getItem(key)||"[]");
   const saved=Array.isArray(v)?v:(v&&Array.isArray(v.items)?v.items:[]);
   if(saved.length)return saved.filter(x=>x&&typeof x.text==="string");
  }catch{}
 }
 return [];
}
function persist(){try{localStorage.setItem(DB,JSON.stringify(items));updateStats();return true}catch(e){notify("Could not save memory in this browser: "+e.message,true);return false}}
function notify(msg,error=false){$("notice").textContent=msg;$("notice").classList.toggle("error",error)}
function parseAndScore(raw,source){return Engine.scoreCandidates(Engine.buildCandidates(Engine.parseConversation(raw,source)))}
function analyze(){
 const raw=$("conversation").value.trim();
 if(!raw){notify("Paste a conversation first.",true);return}
 const source=$("source-name").value.trim()||"Pasted conversation";
 const scored=parseAndScore(raw,source);
 if(!scored.length){notify("No evidence units could be extracted from this text.",true);return}
 const sourceWords=scored.reduce((sum,x)=>sum+x.words,0);
 const wordBudget=Math.floor(sourceWords*Number($("budget").value)/100);
 const mode=$("policy").value,lambda=Number($("redundancy").value);
 const result=Engine.selectCandidates(scored,wordBudget,{mode,lambda});
 pending=result.selected.map((x,i)=>({...x,selectionOrder:i+1,selected:true}));
 const traceById=new Map(result.trace.map(x=>[x.id,x]));
 $("retained-count").textContent=result.selected.length+" / "+scored.length+" evidence units";
 $("retention-summary").innerHTML=[
  ["CANDIDATES",scored.length],
  ["RETAINED",result.selected.length],
  ["WORD PROXY",result.usedWords+" / "+result.wordBudget],
  ["UNUSED CAP",result.remainingWords]
 ].map(([label,value])=>'<div><strong>'+esc(value)+'</strong><span>'+esc(label)+'</span></div>').join("");
 const policyName=({rank:"stable score rank",density:"score / word-cost density",mmr:"greedy MMR diversity"})[mode];
 $("selection-note").innerHTML='<strong>Policy:</strong> '+esc(policyName)+' · <strong>λ:</strong> '+lambda.toFixed(2)+' · <strong>Cost:</strong> message-text word count only. '+(mode==="mmr"?"MMR subtracts maximum TF-IDF cosine similarity to already selected units. ":"")+"The utility score is a transparent browser heuristic, not the trained logistic-regression model or a benchmark result. This front-end splits messages into sentence-level evidence units; the Python research experiments use session-level candidates, so this is not a direct reproduction. Exact tokenizer cost and full metadata cost are not available in this static demo.";
 $("retained-items").innerHTML=result.selected.length?result.selected.map(m=>card(m,true,traceById.get(m.id))).join(""):'<div class="empty">No complete evidence unit fit the current word-proxy budget. Increase the budget or shorten the source.</div>';
 $("not-retained-count").textContent=result.skipped.length+" not retained";
 $("not-retained-items").innerHTML=result.skipped.length?result.skipped.map(x=>{
  const m=scored.find(y=>y.id===x.id);
  return '<article class="evidence-card not-retained"><div class="evidence-top"><span class="role-tag">'+esc((m?.role||"unlabelled").toUpperCase())+'</span><span class="source-tag">NOT RETAINED</span><span class="score-tag">SCORE '+Number(x.score).toFixed(3)+'</span></div><p>'+esc(m?.text||x.id)+'</p><div class="evidence-foot"><span>'+x.words+' word-proxy units · '+esc(x.reason)+'</span></div></article>';
 }).join(""):'<div class="empty">Every candidate unit was retained.</div>';
 $("retention-result").hidden=false;
 $("retention-result").scrollIntoView({behavior:"smooth",block:"start"});
 notify("Analysis complete. Inspect the selected and rejected evidence, then save only what you want to keep.");
}
function card(m,showScore=false,trace=null){
 const feat=m.features||{};
 const reasons=(m.reasons||[]).map(esc).join(" · ");
 const metadata=(m.source||"local memory")+" · message "+((m.messageIndex??0)+1)+" · sentence "+((m.sentenceIndex??0)+1);
 const detail=m.sourceText&&m.sourceText!==m.text?'<details class="source-detail"><summary>Show full source message</summary><p>'+esc(m.sourceText)+'</p></details>':"";
 const featureLine=showScore?'<div class="feature-line">novelty '+Number(feat.novelty||0).toFixed(2)+' · recency '+Number(feat.recencyRank||0).toFixed(2)+' · role '+Number(feat.userFraction||0).toFixed(2)+' · first-person '+Number(feat.firstPersonRate||0).toFixed(2)+'</div>':"";
 const order=trace?'<span class="order-tag">SELECTED #'+trace.order+'</span>':"";
 return '<article class="evidence-card"><div class="evidence-top"><span class="role-tag">'+esc((m.role||"unlabelled").toUpperCase())+'</span><span class="source-tag">'+esc(metadata)+'</span>'+order+(showScore?'<span class="score-tag">SCORE '+Number(m.score||0).toFixed(3)+'</span>':"")+'</div><p>'+esc(m.text)+'</p><div class="evidence-foot"><span>'+m.words+' word-proxy units · '+reasons+'</span>'+(showScore&&trace?'<span>marginal '+Number(trace.utility).toFixed(3)+' · redundancy '+Number(trace.redundancy).toFixed(2)+'</span>':showScore?"":'<button class="remove-item" data-remove="'+esc(m.id)+'">Remove</button>')+'</div>'+featureLine+detail+'</article>';
}
function save(){
 if(!pending.length){notify("There is no selected evidence to save.",true);return}
 const now=new Date().toISOString();
 const clean=pending.map(m=>{
  const {similarities,sourceText,selected,selectionOrder,...stored}=m;
  return {...stored,createdAt:now,id:newId()};
 });
 items.push(...clean);
 if(!persist()){items=items.slice(0,-clean.length);return}
 pending=[];$("retention-result").hidden=true;notify("Evidence saved to this browser's memory store.");switchView("memory");
}
function renderMemory(){
 const q=($("memory-filter").value||"").toLowerCase();
 const list=items.filter(x=>(x.text+" "+x.source+" "+x.role).toLowerCase().includes(q));
 $("memory-count").textContent=items.length+" items";
 $("memory-list").innerHTML=list.length?list.map(m=>card(m)).join(""):'<div class="empty">'+(items.length?"No memories match that filter.":"No memories saved yet. Start by ingesting a conversation.")+'</div>';
 updateStats();
}
function search(e){
 e.preventDefault();
 const q=$("query").value.trim(),found=Engine.rankEvidence(q,items,{lambda:.18,limit:12});
 const intent=Engine.queryIntent(q);
 const label=({goal:"project goal",priorities:"research priorities",milestone:"project milestone",metrics:"evaluation metrics",technical:"technical setup",principles:"selection principles"})[intent]||"general evidence";
 $("retrieval-meta").textContent=found.length?found.length+" evidence units ranked · BM25 term relevance + TF-IDF MMR diversification · detected query intent: "+label:"No matching evidence units. Try different wording or ingest the source conversation.";
 $("matches").innerHTML=found.length?found.map(m=>'<article class="evidence-card"><div class="evidence-top"><span class="role-tag">'+esc((m.role||"unlabelled").toUpperCase())+'</span><span class="source-tag">'+esc(m.source||"local memory")+'</span><span class="score-tag">'+Math.round(m.score*100)+'% NORMALISED BM25</span></div><p>'+esc(m.text)+'</p><div class="evidence-foot"><span>TERMS: '+m.matched.map(esc).join(", ")+' · TYPE: '+esc(m.kind)+'</span><span>'+m.words+' word-proxy units · '+Math.round(m.coverage*100)+'% query-term coverage · redundancy '+Number(m.diversityPenalty).toFixed(2)+'</span></div></article>').join(""):'<div class="empty">No matching evidence. The query cannot retrieve information that was not retained.</div>';
}
function switchView(name){
 document.querySelectorAll(".side-tab").forEach(b=>b.classList.toggle("active",b.dataset.view===name));
 document.querySelectorAll(".view").forEach(v=>v.hidden=v.id!=="view-"+name);
 const t={ingest:["WORKSPACE / INGEST & RETAIN","Give your history a <em>memory.</em>","Extract sentence-level evidence units, compare transparent retention policies, and inspect the budget audit."],memory:["MEMORY STORE / OVERVIEW","Your retained <em>evidence.</em>","Inspect source-linked evidence available to future retrieval."],retrieve:["RETRIEVAL / EVIDENCE SEARCH","Find what <em>matters.</em>","Rank retained evidence with BM25 relevance and MMR diversity; no answer is generated."]}[name];
 $("crumb").textContent=t[0];$("view-title").innerHTML=t[1];$("view-subtitle").textContent=t[2];
 if(name==="memory")renderMemory();
}
function updateStats(){
 const n=items.reduce((a,x)=>a+(Number(x.words)||Engine.countWords(x.text)),0);
 $("storage-label").textContent=n.toLocaleString()+" word-proxy units retained";
 $("storage-fill").style.width=Math.min(100,n/2000*100)+"%";
}
function readSample(){
 $("conversation").value=[
 "User: My main goal is to build MemWeave, a research system that preserves evidence from long conversations under a strict memory budget.",
 "User: My research priorities are improving evidence retention, measuring downstream answer quality, and making every experiment reproducible.",
 "User: I use Python and scikit-learn for the research pipeline, and I want exact token-cost accounting rather than a word-count estimate.",
 "Assistant: Would you like to add more details about your project?",
 "User: Please keep research claims tied to the specific benchmark and report. Evidence recall must not be described as answer accuracy."
 ].join("\n");
 $("source-name").value="MemWeave sample conversation";
 $("input-count").textContent=Engine.countWords($("conversation").value).toLocaleString()+" message words";
 notify("Research sample loaded. Compare the rank, density, and MMR policies under the same word-proxy cap.");
}
document.querySelectorAll(".side-tab").forEach(b=>b.addEventListener("click",()=>switchView(b.dataset.view)));
$("conversation").addEventListener("input",()=>{$("input-count").textContent=Engine.countWords($("conversation").value).toLocaleString()+" message words"});
$("budget").addEventListener("input",()=>{$("budget-value").textContent=$("budget").value+"%"});
$("redundancy").addEventListener("input",()=>{$("redundancy-value").textContent=Number($("redundancy").value).toFixed(2)});
$("analyze-btn").addEventListener("click",analyze);
$("example-btn").addEventListener("click",readSample);
$("save-btn").addEventListener("click",save);
$("discard-btn").addEventListener("click",()=>{$("retention-result").hidden=true;pending=[]});
$("memory-filter").addEventListener("input",renderMemory);
$("search-form").addEventListener("submit",search);
$("memory-list").addEventListener("click",e=>{
 const id=e.target.dataset.remove;if(!id)return;
 items=items.filter(x=>x.id!==id);persist();renderMemory();notify("Memory item removed.");
});
$("export-btn").addEventListener("click",()=>{
 const blob=new Blob([JSON.stringify({format:"memweave-local-v2",exportedAt:new Date().toISOString(),items},null,2)],{type:"application/json"});
 const url=URL.createObjectURL(blob),a=document.createElement("a");a.href=url;a.download="memweave-memory-backup.json";a.click();URL.revokeObjectURL(url);notify("Memory backup exported.");
});
$("import-file").addEventListener("change",async e=>{
 const f=e.target.files[0];if(!f)return;
 try{
  const data=JSON.parse(await f.text());if(!Array.isArray(data.items))throw Error("Invalid backup format");
  const incoming=data.items.filter(x=>x&&typeof x.text==="string");
  items=[...items,...incoming.map(x=>({...x,id:newId(),words:Number(x.words)||Engine.countWords(x.text)}))];
  if(persist()){renderMemory();notify("Imported "+incoming.length+" memory items.")}
 }catch(err){notify("Could not import backup: "+err.message,true)}
 e.target.value="";
});
$("clear-btn").addEventListener("click",()=>{
 if(!confirm("Clear all MemWeave memories saved in this browser? Export a backup first if needed."))return;
 items=[];persist();renderMemory();notify("Local memory store cleared.");
});
updateStats();renderMemory();
})();