/* MemWeave browser-local workspace. The scoring policy is an explicit heuristic baseline, not a trained model. */
(()=>{"use strict";
const Engine=window.MemWeaveEngine,SafeFiles=window.MemWeaveSafeFiles;
if(!Engine||!SafeFiles){document.body.innerHTML='<main style="padding:32px;color:#fff">MemWeave could not load its evidence engine. Refresh the page or check the deployed files.</main>';return}
const DB="memweave.browser.workspace.v2";let items=load(),pending=[],evaluationCandidates=[],goldEvidenceIds=new Set(),evaluationSourceWords=0,lastEvaluationQuestion="";
const $=id=>document.getElementById(id);
const newId=()=>typeof crypto!=="undefined"&&crypto.randomUUID?crypto.randomUUID():String(Date.now())+Math.random();
function esc(s){return String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]))}
function load(){
 for(const key of [DB,"memweave.browser.workspace.v1"]){
  try{
   const v=JSON.parse(localStorage.getItem(key)||"[]");
   const saved=Array.isArray(v)?v:(v&&Array.isArray(v.items)?v.items:[]);
   if(saved.length){const clean=SafeFiles.normalizeItems(saved,{regenerateIds:false}).items;return clean.map(x=>({...x,id:x.id||newId()}));}
  }catch{}
 }
 return [];
}
function persist(){
 try{
  if(items.length>SafeFiles.MAX_ITEMS)throw new Error("The local store has reached the "+SafeFiles.MAX_ITEMS+" item limit. Export a backup and remove older items.");
  const serialized=JSON.stringify(items);
  if(new Blob([serialized]).size>SafeFiles.MAX_FILE_BYTES)throw new Error("The local store exceeds the 5 MB safety limit. Export a backup and remove older items.");
  localStorage.setItem(DB,serialized);updateStats();return true;
 }catch(e){notify("Could not save memory in this browser: "+e.message,true);return false}
}
function downloadJson(filename,json){const blob=new Blob([json],{type:"application/json;charset=utf-8"});const url=URL.createObjectURL(blob),a=document.createElement("a");a.href=url;a.download=filename;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000)}
function notify(msg,error=false){$("notice").textContent=msg;$("notice").classList.toggle("error",error)}
function parseAndScore(raw,source){
 const messages=Engine.parseConversation(raw,source);
 return {messages,candidates:Engine.scoreCandidates(Engine.buildCandidates(messages))};
}
function analyze(){
 const raw=$("conversation").value.trim();
 if(!raw){notify("Paste a conversation first.",true);return}
 const source=$("source-name").value.trim()||"Pasted conversation";
 const parsed=parseAndScore(raw,source);
 const scored=parsed.candidates;
 evaluationCandidates=scored;goldEvidenceIds=new Set();
 if(!scored.length){notify("No evidence units could be extracted from this text.",true);return}
 const sourceWords=parsed.messages.reduce((sum,m)=>sum+m.words,0);
 const wordBudget=Math.floor(sourceWords*Number($("budget").value)/100);
 const mode=$("policy").value,lambda=Number($("redundancy").value);
 const result=Engine.selectCandidates(scored,wordBudget,{mode,lambda,coverageBonus:0.22});
 pending=result.selected.map((x,i)=>({...x,selectionOrder:i+1,selected:true}));
 const traceById=new Map(result.trace.map(x=>[x.id,x]));
 $("retained-count").textContent=result.selected.length+" / "+scored.length+" evidence units";
 $("retention-summary").innerHTML=[
  ["CANDIDATES",scored.length],
  ["RETAINED",result.selected.length],
  ["SOURCE WORDS",sourceWords],
  ["WORD PROXY",result.usedWords+" / "+result.wordBudget],
  ["UNUSED CAP",result.remainingWords]
 ].map(([label,value])=>'<div><strong>'+esc(value)+'</strong><span>'+esc(label)+'</span></div>').join("");
 const policyName=({rank:"rank-only baseline",density:"score / word-cost density",mmr:"MMR-only baseline",coverage_only:"coverage-only baseline",coverage:"coverage + MMR (experimental ablation)",knapsack:"exact additive-score knapsack baseline"})[mode];
 const policyDetails=mode==="coverage"
  ?"Priority-weighted facet gains are combined with an MMR redundancy penalty; candidates are greedily chosen by marginal utility per word. This is a browser ablation, not a globally optimal solver or validated MW-ECS implementation."
  :mode==="coverage_only"?"Priority-weighted facet gains are applied without a redundancy penalty."
  :mode==="mmr"?"MMR subtracts λ × maximum TF-IDF cosine similarity to already selected units, without facet bonuses."
  :mode==="density"?"Candidates are ranked by heuristic score divided by word-proxy cost."
  :mode==="knapsack"?"Exact 0/1 dynamic programming maximises additive heuristic score under the integer word-proxy cap when within the browser work limit; it does not optimise coverage or MMR."
  :"Candidates are ranked by the transparent heuristic score without coverage or MMR.";
 $("selection-note").innerHTML='<strong>Policy:</strong> '+esc(policyName)+' · <strong>λ:</strong> '+lambda.toFixed(2)+' · <strong>Cost:</strong> selected-text word count proxy. '+policyDetails+' The utility score is a transparent browser heuristic, not the trained logistic-regression model or a benchmark result. Context-resolved units retain a link to the full original source message. Exact tokenizer cost and full metadata cost are not available in this static demo.';
 $("budget-sweep").innerHTML=renderBudgetSweep(scored,sourceWords,mode,lambda);
 $("baseline-comparison").innerHTML=renderBaselineComparison(scored,sourceWords,lambda);
 renderEvidenceEvaluation(scored,sourceWords,lambda);
 $("retained-items").innerHTML=result.selected.length?result.selected.map(m=>card(m,true,traceById.get(m.id))).join(""):'<div class="empty">No complete evidence unit fit the current word-proxy budget. Increase the budget or shorten the source.</div>';
 $("not-retained-count").textContent=result.skipped.length+" not retained";
 $("not-retained-items").innerHTML=result.skipped.length?result.skipped.map(x=>{
  const m=scored.find(y=>y.id===x.id);
  return '<article class="evidence-card not-retained"><div class="evidence-top"><span class="role-tag">'+esc((m?.role||"unlabelled").toUpperCase())+'</span><span class="source-tag">NOT RETAINED · '+esc(m?.facet||m?.kind||"general")+'</span><span class="score-tag">SCORE '+Number(x.score).toFixed(3)+'</span></div><p>'+esc(m?.text||x.id)+'</p><div class="evidence-foot"><span>'+x.words+' word-proxy units · '+esc(x.reason)+'</span></div>'+(m?.sourceText?'<details class="source-detail"><summary>Show source message</summary><p>'+esc(m.sourceText)+'</p></details>':"")+'</article>';
 }).join(""):'<div class="empty">Every candidate unit was retained.</div>';
 $("retention-result").hidden=false;
 $("retention-result").scrollIntoView({behavior:"smooth",block:"start"});
 notify("Analysis complete. Review coverage, source provenance, and rejected evidence before saving.");
}

function renderBudgetSweep(scored,sourceWords,mode,lambda){
 const rows=[10,20,30,40,50].map(percent=>{
  const cap=Math.floor(sourceWords*percent/100);
  const result=Engine.selectCandidates(scored,cap,{mode,lambda,coverageBonus:0.22});
  const facets=result.coveredFacets||[];
  const names=result.selected.map(x=>x.text);
  return '<tr><td>'+percent+'%</td><td>'+result.selected.length+'/'+scored.length+'</td><td>'+result.usedWords+'/'+cap+'</td><td>'+facets.length+'</td><td><details><summary>View retained units</summary><ul>'+names.map(x=>'<li>'+esc(x)+'</li>').join('')+'</ul></details></td></tr>';
 }).join('');
 return '<div class="sweep-wrap"><div class="sweep-intro">Same candidates, scoring, policy, and λ; only the word-proxy cap changes. These are descriptive browser results, not benchmark measurements.</div><table class="sweep-table"><thead><tr><th>Budget</th><th>Retained</th><th>Words used / cap</th><th>Facets</th><th>Retained evidence</th></tr></thead><tbody>'+rows+'</tbody></table></div>';
}

function renderBaselineComparison(scored,sourceWords,lambda){
 const budgets=[10,20,30,40,50],policies=[
  ["rank","Rank-only"],["knapsack","Exact knapsack"],["coverage_only","Coverage-only"],["mmr","MMR-only"],["coverage","Coverage + MMR"]
 ];
 const rows=[];
 for(const percent of budgets){
  const cap=Math.floor(sourceWords*percent/100);
  for(const [mode,label] of policies){
   const r=Engine.selectCandidates(scored,cap,{mode,lambda,coverageBonus:.22});
   const method=r.optimal===true?"Exact DP":r.optimal===false?"Density fallback":"Heuristic";
   rows.push('<tr><td>'+percent+'%</td><td>'+label+'</td><td>'+r.selected.length+'/'+scored.length+'</td><td>'+r.usedWords+'/'+cap+'</td><td>'+r.coveredFacets.length+'</td><td>'+Math.round(r.weightedFacetCoverage*100)+'%</td><td>'+method+'</td></tr>');
  }
 }
 return '<div class="sweep-wrap"><div class="sweep-intro">Matched browser-heuristic comparison: identical candidates, scores, word-proxy caps, and λ. The primary LongMemEval study uses a 10% word-count proxy, so 10% is shown explicitly. Exact knapsack maximises additive heuristic score when its DP work limit is met; it is not a relevance oracle. Weighted facet coverage is a policy diagnostic, not gold evidence recall. The trained logistic-regression selector is not loaded in this static browser demo and must be compared from the research pipeline using its frozen feature schema and weights.</div><table class="sweep-table"><thead><tr><th>Budget</th><th>Policy</th><th>Retained</th><th>Words / cap</th><th>Facets</th><th>Weighted facet coverage</th><th>Solver</th></tr></thead><tbody>'+rows.join('')+'</tbody></table><p class="sweep-intro"><strong>Gold evidence recall:</strong> not measured; this requires annotated relevant-evidence labels. <strong>Downstream answer quality:</strong> not measured; this requires a fixed reader, answer set, and task-appropriate evaluator. Keep both as separate evaluation outcomes.</p></div>';
}

function renderEvidenceEvaluation(scored,sourceWords,lambda){
 evaluationSourceWords=sourceWords;lastEvaluationQuestion="";
 $("eval-question").value="";
 $("eval-labels").innerHTML=scored.map(m=>'<label class="annotation-card"><input type="checkbox" data-gold-id="'+esc(m.id)+'"><span><strong>'+esc(m.facet||m.kind||"general")+'</strong><span>'+esc(m.text)+'</span><small>'+esc((m.role||"unlabelled").toUpperCase())+' · '+m.words+' word-proxy units · '+esc(m.source||"source")+'</small></span></label>').join("");
 $("eval-metrics").innerHTML='<div class="sweep-intro">Enter a held-out question and mark every candidate unit that contains evidence needed to answer it. Metrics remain empty until at least one evidence unit is labelled.</div>';
}
function updateEvidenceEvaluation(){
 const question=$("eval-question").value.trim();
 if(!question||!goldEvidenceIds.size){
  $("eval-metrics").innerHTML='<div class="sweep-intro">Add a held-out question and mark its required evidence units to calculate question-level precision, recall, and F1.</div>';
  return;
 }
 const sourceWords=evaluationSourceWords;
 const lambda=Number($("redundancy").value);
 const policies=[["rank","Rank-only"],["knapsack","Exact knapsack"],["coverage_only","Coverage-only"],["mmr","MMR-only"],["coverage","Coverage + MMR"]];
 const rows=[];
 for(const percent of [10,20,30,40,50]){
  const cap=Math.floor(sourceWords*percent/100);
  for(const [mode,label] of policies){
   const result=Engine.selectCandidates(evaluationCandidates,cap,{mode,lambda,coverageBonus:.22});
   const retained=Engine.evaluateEvidenceSelection(result.selected.map(x=>x.id),[...goldEvidenceIds]);
   const retrieved=Engine.rankEvidence(question,result.selected,{lambda:.18,limit:5});
   const retrieval=Engine.evaluateEvidenceSelection(retrieved.map(x=>x.id),[...goldEvidenceIds]);
   retrieval.precision=retrieval.truePositives/5;
   retrieval.f1=retrieval.precision+retrieval.recall
     ?2*retrieval.precision*retrieval.recall/(retrieval.precision+retrieval.recall):0;
   const solver=result.optimal===true?"Exact DP":result.optimal===false?"Fallback":"Heuristic";
   rows.push('<tr><td>'+percent+'%</td><td>'+label+'</td><td>'+Math.round(retained.recall*100)+'%</td><td>'+Math.round(retrieval.precision*100)+'%</td><td>'+Math.round(retrieval.recall*100)+'%</td><td>'+Math.round(retrieval.f1*100)+'%</td><td>'+result.usedWords+'/'+cap+'</td><td>'+solver+'</td></tr>');
  }
 }
 $("eval-metrics").innerHTML='<div class="sweep-wrap"><div class="sweep-intro">Manual labels for one question: "'+esc(question)+'" · '+goldEvidenceIds.size+' relevant evidence units. Retention recall asks whether gold evidence survived selection. Retrieval P/R/F1 measures whether the browser BM25+MMR retriever returns gold evidence from the retained subset (top 5). These are annotation-based diagnostics, not answer quality, benchmark results, or the trained research model.</div><table class="sweep-table"><thead><tr><th>Budget</th><th>Policy</th><th>Retention recall</th><th>Retrieval P@5</th><th>Retrieval R@5</th><th>Retrieval F1@5</th><th>Words / cap</th><th>Solver</th></tr></thead><tbody>'+rows.join('')+'</tbody></table><p class="sweep-intro">The fixed reader / answer-generation stage is not run here. To measure downstream answer quality, evaluate the same retained evidence with the frozen reader and task evaluator used in the research pipeline.</p></div>';
}
function exportEvidenceLabels(){
 const question=$("eval-question").value.trim();
 if(!question||!goldEvidenceIds.size){notify("Enter an evaluation question and label at least one relevant evidence unit first.",true);return}
 const lambda=Number($("redundancy").value),retrievalLambda=.18;
 const policies=[["rank","Rank-only"],["knapsack","Exact knapsack"],["coverage_only","Coverage-only"],["mmr","MMR-only"],["coverage","Coverage + MMR"]];
 const evaluations=[];
 for(const budgetPercent of [10,20,30,40,50]){
  const budgetCap=Math.floor(evaluationSourceWords*budgetPercent/100);
  for(const [policy,label] of policies){
   const result=Engine.selectCandidates(evaluationCandidates,budgetCap,{mode:policy,lambda,coverageBonus:.22});
   const retrieved=Engine.rankEvidence(question,result.selected,{lambda:retrievalLambda,limit:5});
   evaluations.push({budgetPercent,policy,label,lambda,retrievalLambda,budgetCap,usedCost:result.usedWords,
    solver:result.optimal===true?"Exact DP":result.optimal===false?"Fallback":"Heuristic",
    selectedIds:result.selected.map(x=>x.id),retrievalIds:retrieved.map(x=>x.id)});
  }
 }
 const payload={format:"memweave-question-evidence-labels-v2",schemaVersion:2,
  taskType:"browser_atomic_evidence_diagnostic",source:$("source-name").value.trim(),question,
  annotatedAt:new Date().toISOString(),wordBudgetProxyOnly:true,costUnit:"browser word-count proxy",
  relevantEvidenceIds:[...goldEvidenceIds],
  candidateEvidence:evaluationCandidates.map(x=>({id:x.id,text:x.text,sourceId:x.sourceId,sourceText:x.sourceText,
   role:x.role,source:x.source,facet:x.facet,words:x.words})),
  evaluations};
 const json=JSON.stringify(payload,null,2);
 if(new Blob([json]).size>SafeFiles.MAX_FILE_BYTES){notify("Evidence-label export exceeds the 5 MB safety limit.",true);return}
 downloadJson("memweave-evidence-labels.json",json);
 notify("Reproducible v2 audit exported with gold labels, selected IDs, retrieved IDs and policy/budget settings. The file contains private evidence text.");
}

function card(m,showScore=false,trace=null){
 const feat=m.features||{};
 const reasons=(m.reasons||[]).map(esc).join(" · ");
 const metadata=(m.source||"local memory")+" · message "+((m.messageIndex??0)+1)+" · unit "+((m.sentenceIndex??0)+1);
 const detail=m.sourceText&&m.sourceText!==m.text?'<details class="source-detail"><summary>Show full source message</summary><p>'+esc(m.sourceText)+'</p></details>':"";
 const featureLine=showScore?'<div class="feature-line">novelty '+Number(feat.novelty||0).toFixed(2)+' · mean sim '+Number(feat.meanSimilarity||0).toFixed(2)+' · top-3 sim '+Number(feat.top3Similarity||0).toFixed(2)+' · recency '+Number(feat.recencyRank||0).toFixed(2)+' · role '+Number(feat.userFraction||0).toFixed(2)+' · first-person '+Number(feat.firstPersonRate||0).toFixed(2)+' · digits '+Number(feat.digitRate||0).toFixed(2)+'</div>':"";
 const order=trace?'<span class="order-tag">SELECTED #'+trace.order+'</span>'+(trace.coverageGain>0?'<span class="order-tag">NEW FACET +'+Number(trace.coverageGain).toFixed(2)+'</span>':""):"";
 return '<article class="evidence-card"><div class="evidence-top"><span class="role-tag">'+esc((m.role||"unlabelled").toUpperCase())+'</span><span class="source-tag">'+esc(metadata)+'</span>'+order+(showScore?'<span class="score-tag">SCORE '+Number(m.score||0).toFixed(3)+'</span>':"")+'</div><p>'+esc(m.text)+'</p><div class="evidence-foot"><span>'+m.words+' word-proxy units · '+reasons+'</span>'+(showScore&&trace?'<span>marginal '+Number(trace.utility).toFixed(3)+' · redundancy '+Number(trace.redundancy).toFixed(2)+' · facet '+esc(trace.facet)+'</span>':showScore?"":'<button class="remove-item" data-remove="'+esc(m.id)+'">Remove</button>')+'</div>'+featureLine+detail+'</article>';
}
function save(){
 if(!pending.length){notify("There is no selected evidence to save.",true);return}
 const now=new Date().toISOString();
 const clean=pending.map(m=>{
  const {similarities,selected,selectionOrder,...stored}=m;
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
 notify("Research sample loaded. Compare rank, exact knapsack, density, MMR, and coverage policies under the same word-proxy cap.");
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
$("eval-question").addEventListener("input",()=>{
 const question=$("eval-question").value.trim();
 if(question!==lastEvaluationQuestion){
  goldEvidenceIds.clear();
  $("eval-labels").querySelectorAll("input[data-gold-id]").forEach(input=>{input.checked=false});
  lastEvaluationQuestion=question;
 }
 updateEvidenceEvaluation();
});
$("eval-labels").addEventListener("change",e=>{
 const id=e.target.dataset.goldId;if(!id)return;
 if(e.target.checked)goldEvidenceIds.add(id);else goldEvidenceIds.delete(id);
 updateEvidenceEvaluation();
});
$("eval-export-btn").addEventListener("click",exportEvidenceLabels);
$("search-form").addEventListener("submit",search);
$("memory-list").addEventListener("click",e=>{
 const id=e.target.dataset.remove;if(!id)return;
 const previous=items;items=items.filter(x=>x.id!==id);if(!persist()){items=previous;renderMemory();return}renderMemory();notify("Memory item removed.");
});
$("export-btn").addEventListener("click",()=>{
 try{downloadJson("memweave-memory-backup.json",SafeFiles.exportBackup(items));notify("Validated JSON backup exported. It contains saved evidence text and may include source excerpts and is not encrypted; keep it private.");}
 catch(err){notify("Could not export backup: "+err.message,true)}
});
$("import-file").addEventListener("change",async e=>{
 const f=e.target.files[0];if(!f)return;const previous=items;
 try{
  if(f.size>SafeFiles.MAX_FILE_BYTES)throw new Error("File is larger than the 5 MB import limit.");
  if(!/\.json$/i.test(f.name))throw new Error("Choose a .json MemWeave backup file.");
  const parsed=SafeFiles.parseBackup(await f.text());
  const merged=SafeFiles.normalizeItems([...items,...parsed.items],{regenerateIds:false});
  items=merged.items.map(x=>({...x,id:x.id||newId()}));
  if(!persist()){items=previous;renderMemory();return}
  renderMemory();notify("Imported "+parsed.items.length+" valid backup items; "+(parsed.skipped+merged.skipped)+" invalid or duplicate records were skipped. Data remains in this browser.");
 }catch(err){items=previous;notify("Could not import backup: "+err.message,true)}finally{e.target.value=""}
});
$("clear-btn").addEventListener("click",()=>{
 if(!confirm("Clear all MemWeave memories saved in this browser? Export a backup first if needed."))return;
 const previous=items;items=[];if(!persist()){items=previous;renderMemory();return}renderMemory();notify("Local memory store cleared.");
});
updateStats();renderMemory();
})();