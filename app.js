/* MemWeave browser-local workspace: conversations remain on this device. */
(()=>{"use strict";
const DB="memweave.browser.workspace.v1";let items=load(),pending=[];
const $=id=>document.getElementById(id),newId=()=>((crypto&&crypto.randomUUID)?crypto.randomUUID():String(Date.now())+Math.random());
function load(){try{return JSON.parse(localStorage.getItem(DB)||"[]")}catch{return []}}
function persist(){localStorage.setItem(DB,JSON.stringify(items));updateStats()}
function words(s){return (s.match(/[A-Za-z0-9]+(?:['’-][A-Za-z0-9]+)*/g)||[]).length}
const STOPWORDS=new Set("a an the and or but if then than is am are was were be been being do does did can could would should will may might must have has had having i me my mine we our you your he she it they them this that these those what which who whom when where why how to of in on at by for from with about as into over under after before between through during up down out not no yes please tell explain".split(" "));
function tokens(s){return [...new Set((s.toLowerCase().match(/[a-z0-9]+/g)||[]).filter(t=>t.length>2&&!STOPWORDS.has(t))) ]}
function esc(s){return String(s).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]))}
function parse(text,source){const lines=text.replace(/\r/g,"").split("\n"),messages=[];let current=null;const marker=/^\s*(user|assistant|system|human|ai|speaker\s*\w*)\s*:\s*(.*)$/i;
 for(const line of lines){const m=line.match(marker);if(m){if(current&&current.text.trim())messages.push(current);current={role:/^(user|human)$/i.test(m[1])?"user":/^(assistant|ai)$/i.test(m[1])?"assistant":m[1].toLowerCase(),text:m[2]};}else if(current){current.text+=(current.text?"\n":"")+line;}else if(line.trim())messages.push({role:"unlabelled",text:line.trim()});}
 if(current&&current.text.trim())messages.push(current);
 if(!messages.length)return text.split(/\n\s*\n/).map(x=>({role:"unlabelled",text:x.trim()})).filter(x=>x.text);
 const out=[];for(const m of messages){const parts=m.text.split(/\n\s*\n/).map(x=>x.trim()).filter(Boolean);for(const part of parts)out.push({...m,text:part});}
 return out.map((m,i)=>({...m,id:newId(),source,words:words(m.text),position:i}));
}
function score(m){const t=m.text.toLowerCase();let s=.7;const reasons=[];
 if(m.role==="user"){s+=.8;reasons.push("user-authored evidence")}
 const rules=[
  [/\b(three main priorities|research priorities|priorities are|top priorities|priority is)\b/,2.8,"explicit research priorities"],
  [/\b(main goal|primary goal|research objective|aims? to|purpose of|objective is|goal is)\b/,2.6,"project goal or research objective"],
  [/\b(milestone|deliverable|working demonstration|immediate project|next step|deadline)\b/,2.0,"project milestone or deliverable"],
  [/\b(pytorch|tensorflow|python|cuda|gpu|framework|programming language|technical stack|fixed random seeds)\b/,1.9,"technical fact or constraint"],
  [/\b(evaluation metrics?|measure|measuring|accuracy|evidence coverage|answerability|token budget|storage cost|retention quality|retrieval accuracy)\b/,1.9,"evaluation metric or research measure"],
  [/\b(research project|research|experiment|benchmark|dataset|model|method|baseline|retention|retrieval|evidence|memory budget|constrained budget)\b/,1.0,"research-relevant information"],
  [/\b(remember|prefer|always|never|important|i need|i want|i use|i work|i am|i'm)\b/, .65,"explicit preference or durable statement"],
  [/\b(should prioritize|prioritise|durable preferences|technical constraints|important decisions)\b/, .65,"memory-selection principle"]
 ];
 for(const [re,weight,label] of rules){if(re.test(t)){s+=weight;reasons.push(label)}}
 if(/\b(favourite colour|favorite color|coffee|tea|vacation|visited)\b/i.test(t)){s-=1.8;reasons.push("incidental personal detail; lower future research value")}
 if(/\?/.test(t)){s-=.35;reasons.push("question is less useful than its answer")}
 if(/\b(because|therefore|result|found|decided|must|constraint)\b/i.test(t)){s+=.35;reasons.push("reasoning or decision signal")}
 if(m.words>=8&&m.words<=65){s+=.35;reasons.push("compact evidence unit")}else if(m.words>100){s-=.35;reasons.push("long passage")}
 if(m.role==="system")s-=.5;
 return {score:Math.max(.1,s),reasons:reasons.length?reasons:["general conversation evidence"]};
}
function analyze(){const raw=$("conversation").value.trim();if(!raw){notify("Paste a conversation first.",true);return}
 const source=$("source-name").value.trim()||"Pasted conversation",parsed=parse(raw,source).map(m=>({...m,...score(m)}));
 const budget=Math.max(1,Math.floor(words(raw)*Number($("budget").value)/100));let used=0;const selected=[];
 const remaining=[...parsed];while(remaining.length){let bestIndex=-1,bestUtility=-Infinity;
  for(let i=0;i<remaining.length;i++){const m=remaining[i];if(used+m.words>budget)continue;
   const mt=new Set(tokens(m.text));let redundancy=0;
   for(const chosen of selected){const ct=new Set(tokens(chosen.text));const overlap=[...mt].filter(x=>ct.has(x)).length/Math.max(1,new Set([...mt,...ct]).size);redundancy=Math.max(redundancy,overlap)}
   const utility=(m.score*(1-.65*redundancy))/Math.pow(Math.max(1,m.words),.32);
   if(utility>bestUtility){bestUtility=utility;bestIndex=i}
  }
  if(bestIndex<0)break;const [chosen]=remaining.splice(bestIndex,1);selected.push(chosen);used+=chosen.words;
 }
 pending=selected.sort((a,b)=>a.position-b.position);
 $("retained-count").textContent=selected.length+" / "+parsed.length+" units";
 $("retention-summary").innerHTML='<div><strong>'+used+'</strong><span>retained words</span></div><div><strong>'+words(raw)+'</strong><span>source words</span></div><div><strong>'+Math.round(used/Math.max(1,words(raw))*100)+'%</strong><span>actual budget used</span></div>';
 $("retained-items").innerHTML=selected.length?selected.map(m=>card(m,true)).join(""):'<div class="empty">No units fit this budget. Increase the budget or use a shorter source.</div>';
 $("retention-result").hidden=false;$("retention-result").scrollIntoView({behavior:"smooth",block:"start"});notify("Analysis complete. Review the selected evidence before saving.");
}
function card(m,showScore=false){return '<article class="evidence-card"><div class="evidence-top"><span class="role-tag">'+esc((m.role||"unlabelled").toUpperCase())+'</span><span class="source-tag">'+esc(m.source||"local memory")+'</span>'+(showScore?'<span class="score-tag">SCORE '+m.score.toFixed(2)+'</span>':"")+'</div><p>'+esc(m.text)+'</p><div class="evidence-foot"><span>'+m.words+' words · '+(m.reasons||[]).map(esc).join(" · ")+'</span>'+(showScore?"":'<button class="remove-item" data-remove="'+esc(m.id)+'">Remove</button>')+'</div></article>'}
function save(){if(!pending.length){notify("There is no selected evidence to save.",true);return}const now=new Date().toISOString();for(const m of pending)items.push({...m,createdAt:now,id:newId()});persist();pending=[];$("retention-result").hidden=true;notify("Evidence saved to this browser's memory store.");switchView("memory")}
function renderMemory(){const q=($("memory-filter").value||"").toLowerCase();const list=items.filter(x=>(x.text+" "+x.source+" "+x.role).toLowerCase().includes(q));$("memory-count").textContent=items.length+" items";$("memory-list").innerHTML=list.length?list.map(m=>card(m)).join(""):'<div class="empty">'+(items.length?"No memories match that filter.":"No memories saved yet. Start by ingesting a conversation.")+'</div>';updateStats()}
function retrieve(query){const qt=tokens(query);if(!qt.length)return [];const docs=items.map(m=>new Set(tokens(m.text))),N=Math.max(1,items.length);
 const weights=qt.map(term=>({term,weight:Math.log(1+(N+1)/(1+docs.filter(d=>d.has(term)).length))}));
 const total=weights.reduce((a,x)=>a+x.weight,0)||1;
 return items.map((m,i)=>{const mt=docs[i],matched=weights.filter(x=>mt.has(x.term)).map(x=>x.term);
  const covered=weights.filter(x=>mt.has(x.term)).reduce((a,x)=>a+x.weight,0)/total;
  const phrase=tokens(query).length>1&&m.text.toLowerCase().includes(query.toLowerCase())?.15:0;
  return {...m,matched,score:Math.min(1,covered+phrase)};
 }).filter(x=>x.matched.length).sort((a,b)=>b.score-a.score||b.matched.length-a.matched.length).slice(0,12)}
function search(e){e.preventDefault();const q=$("query").value.trim(),found=retrieve(q);$("retrieval-meta").textContent=found.length?found.length+" evidence items matched · ranked by query-term coverage":"No matching evidence found."; $("matches").innerHTML=found.length?found.map(m=>'<article class="evidence-card"><div class="evidence-top"><span class="role-tag">'+esc(m.role.toUpperCase())+'</span><span class="source-tag">'+esc(m.source)+'</span><span class="score-tag">'+Math.round(m.score*100)+'% TERM COVERAGE</span></div><p>'+esc(m.text)+'</p><div class="evidence-foot"><span>MATCHED TERMS: '+m.matched.map(esc).join(", ")+'</span><span>'+m.words+' words</span></div></article>').join(""):'<div class="empty">No matching evidence. Try different terms or ingest more conversation history.</div>'}
function switchView(name){document.querySelectorAll(".side-tab").forEach(b=>b.classList.toggle("active",b.dataset.view===name));document.querySelectorAll(".view").forEach(v=>v.hidden=v.id!=="view-"+name);const t={ingest:["WORKSPACE / INGEST & RETAIN","Give your history a <em>memory.</em>","Add a conversation, set a memory budget, and inspect what MemWeave keeps."],memory:["MEMORY STORE / OVERVIEW","Your retained <em>evidence.</em>","Inspect and manage the evidence available to future retrieval."],retrieve:["RETRIEVAL / EVIDENCE SEARCH","Find what <em>matters.</em>","Ask a question and inspect the source evidence MemWeave can recover."]}[name];$("crumb").textContent=t[0];$("view-title").innerHTML=t[1];$("view-subtitle").textContent=t[2];if(name==="memory")renderMemory()}
function updateStats(){const n=items.reduce((a,x)=>a+x.words,0);$("storage-label").textContent=n.toLocaleString()+" words retained";$("storage-fill").style.width=Math.min(100,n/2000*100)+"%"}
function notify(msg,error=false){$("notice").textContent=msg;$("notice").classList.toggle("error",error)}
document.querySelectorAll(".side-tab").forEach(b=>b.addEventListener("click",()=>switchView(b.dataset.view)));
$("conversation").addEventListener("input",()=>{$("input-count").textContent=words($("conversation").value).toLocaleString()+" words"});
$("budget").addEventListener("input",()=>{$("budget-value").textContent=$("budget").value+"%"});
$("analyze-btn").addEventListener("click",analyze);$("save-btn").addEventListener("click",save);$("discard-btn").addEventListener("click",()=>{$("retention-result").hidden=true;pending=[]});
$("memory-filter").addEventListener("input",renderMemory);$("search-form").addEventListener("submit",search);
$("memory-list").addEventListener("click",e=>{const id=e.target.dataset.remove;if(!id)return;items=items.filter(x=>x.id!==id);persist();renderMemory();notify("Memory item removed.")});
$("export-btn").addEventListener("click",()=>{const blob=new Blob([JSON.stringify({format:"memweave-local-v1",exportedAt:new Date().toISOString(),items},null,2)],{type:"application/json"}),url=URL.createObjectURL(blob),a=document.createElement("a");a.href=url;a.download="memweave-memory-backup.json";a.click();URL.revokeObjectURL(url);notify("Memory backup exported.")});
$("import-file").addEventListener("change",async e=>{const f=e.target.files[0];if(!f)return;try{const data=JSON.parse(await f.text());if(!Array.isArray(data.items))throw Error("Invalid backup format");const incoming=data.items.filter(x=>x&&typeof x.text==="string"&&typeof x.words==="number");items=[...items,...incoming];persist();renderMemory();notify("Imported "+incoming.length+" memory items.")}catch(err){notify("Could not import backup: "+err.message,true)}e.target.value=""});
$("clear-btn").addEventListener("click",()=>{if(!confirm("Clear all MemWeave memories saved in this browser? Export a backup first if needed."))return;items=[];persist();renderMemory();notify("Local memory store cleared.")});
updateStats();renderMemory();
})();