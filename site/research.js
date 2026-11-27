(()=>{"use strict";
const candidates=[
 {id:"S1",name:"Project objective",detail:"Core goal and future answerability",score:.94,cost:34,superseded:0,sim:[0,.12,.08,.18,.10,.14]},
 {id:"S2",name:"Technical constraints",detail:"Python, PyTorch, fixed seeds",score:.81,cost:24,superseded:0,sim:[.12,0,.28,.10,.16,.22]},
 {id:"S3",name:"Recent project update",detail:"A later update supersedes an older plan",score:.76,cost:30,superseded:1,sim:[.08,.28,0,.20,.12,.26]},
 {id:"S4",name:"Evaluation metrics",detail:"Recall, answerability, token cost",score:.88,cost:27,superseded:0,sim:[.18,.10,.20,0,.14,.19]},
 {id:"S5",name:"Repeated background",detail:"Similar context already covered",score:.63,cost:38,superseded:0,sim:[.10,.16,.12,.14,0,.74]},
 {id:"S6",name:"Research priorities",detail:"Retention, downstream QA, baselines",score:.90,cost:32,superseded:0,sim:[.14,.22,.26,.19,.74,0]}
];
const $=id=>document.getElementById(id);
function run(){
 const mode=$("mode").value,budget=+$("budget").value/100,lambda=+$("lambda").value,gamma=+$("gamma").value,nu=$("supersede").checked?.2:0;
 $("budget-label").textContent=Math.round(budget*100)+"%";$("lambda-label").textContent=lambda.toFixed(2);$("gamma-label").textContent=gamma.toFixed(2);
 const limit=budget*candidates.reduce((a,x)=>a+x.cost,0);let used=0,chosen=[],available=new Set(candidates.map((_,i)=>i)),trace=[];
 while(available.size){
  let best=-1,bestValue=-Infinity;
  for(const i of [...available].sort((a,b)=>a-b)){
   const c=candidates[i];if(used+c.cost>limit)continue;
   let maxSim=0;for(const j of chosen)maxSim=Math.max(maxSim,c.sim[j]);
   const value=mode==="rank"?c.score:mode==="density"?c.score/Math.max(1,c.cost):Math.max(c.score-lambda*maxSim-nu*c.superseded,.000001)/Math.pow(c.cost,gamma);
   if(value>bestValue){best=i;bestValue=value}
  }
  if(best<0)break;
  chosen.push(best);available.delete(best);used+=candidates[best].cost;
  trace.push({index:best,value:bestValue,used});
 }
 const selected=new Set(chosen),fmt=n=>n.toFixed(2);
 $("candidates").innerHTML=candidates.map((c,i)=>'<div class="candidate '+(selected.has(i)?"selected":"")+'"><strong>'+c.id+' · '+c.name+(selected.has(i)?" ✓":"")+'</strong><small>'+c.detail+' · utility '+fmt(c.score)+' · cost '+c.cost+' · superseded '+c.superseded+'</small></div>').join("");
 $("trace").innerHTML=trace.length?trace.map((t,n)=>'<div class="candidate selected"><strong>'+String(n+1)+'. '+candidates[t.index].name+'</strong><small>marginal policy score '+fmt(t.value)+' · cumulative cost '+t.used+'</small></div>').join(""):'<p class="muted">No candidate fits this budget.</p>';
 $("used").textContent="Budget used: "+used+" / "+fmt(limit)+" cost units";$("selected").textContent="Selected: "+chosen.length+" / "+candidates.length;$("objective").textContent="Policy: "+({rank:"stable rank",density:"score / cost",mmr:"MMR + supersession"}[mode]);
}
["mode","budget","lambda","gamma","supersede"].forEach(id=>$(id).addEventListener("input",run));run();
})();