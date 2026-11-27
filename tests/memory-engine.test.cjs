const assert = require("node:assert/strict");
const Engine = require("../site/memory-engine.js");

const sample = [
  "User: My main goal is to build MemWeave, a research system that preserves evidence from long conversations under a strict memory budget.",
  "User: My research priorities are improving evidence retention, measuring downstream answer quality, and making every experiment reproducible.",
  "User: I use Python and scikit-learn for the research pipeline, and I want exact token-cost accounting rather than a word-count estimate.",
  "Assistant: Would you like to add more details about your project?",
  "User: Please keep research claims tied to the specific benchmark and report. Evidence recall must not be described as answer accuracy."
].join("\n");

const messages = Engine.parseConversation(sample, "test");
assert.equal(messages.length, 5, "speaker-labelled messages are separated");
assert.equal(messages[0].role, "user");
assert.equal(messages[3].role, "assistant");
assert.equal(messages.reduce((n, m) => n + m.words, 0),
  Engine.countWords(messages.map(m => m.text).join(" ")),
  "speaker labels are excluded from source-word accounting");

const units = Engine.buildCandidates(messages);
assert.ok(units.length >= 8, "lists and independent clauses become atomic evidence units");
assert.ok(units.some(x => x.text.includes("MemWeave goal: preserve evidence")));
assert.equal(units.filter(x => x.kind === "priorities").length, 3,
  "the three research priorities become independently selectable evidence");
assert.deepEqual(units.filter(x => x.kind === "priorities").map(x => x.facet), [
  "priority:evidence_retention", "priority:downstream_answer_quality", "priority:reproducibility"
], "each named research priority receives its own coverage facet");
assert.ok(units.some(x => x.text.includes("I use Python and scikit-learn")), "the independent technical-stack clause is not lost during compression");
assert.ok(units.some(x => x.text === "Cost requirement: exact tokenizer tokens, not word-count estimates." && x.facet === "hard:token_accounting"),
  "token-cost constraint is compacted into a high-priority, source-linked hard requirement");
assert.ok(units.some(x => x.text === "Tie claims to benchmark reports; separate evidence recall from answer accuracy."),
  "linked reporting constraints are compacted without losing their meaning");
assert.ok(units.every(x => x.sourceText && x.sourceId && Number.isInteger(x.messageIndex)),
  "each evidence unit retains source provenance");
assert.ok(units.filter(x => x.derivation === "context_resolved").length >= 5,
  "context-resolved candidates are explicitly marked");

const scored = Engine.scoreCandidates(units);
assert.ok(scored.every(x => Number.isFinite(x.score) && x.score >= 0 && x.score <= 1));
assert.ok(scored.every(x => x.features && Number.isFinite(x.features.novelty)));
assert.ok(scored.some(x => x.role === "assistant" && x.score <= .02),
  "assistant questions must not outrank user-authored evidence");

const sourceWords = messages.reduce((n, x) => n + x.words, 0);
const budget = Math.floor(sourceWords * .20);
for (const mode of ["rank", "density", "mmr", "coverage_only", "coverage", "knapsack"]) {
  const result = Engine.selectCandidates(scored, budget, { mode, lambda: 0.25 });
  assert.ok(result.usedWords <= budget, mode + " must respect the word-proxy budget");
  assert.equal(result.usedWords, result.selected.reduce((n, x) => n + x.words, 0));
  assert.equal(result.trace.length, result.selected.length);
  assert.equal(result.skipped.length + result.selected.length, scored.length);
}
const exactFixture = [
  {id:"a",text:"high value compact",words:4,score:.95,kind:"goal"},
  {id:"b",text:"high value longer",words:5,score:.90,kind:"goal"},
  {id:"c",text:"alternative compact",words:4,score:.82,kind:"technical"}
];
const exact = Engine.selectCandidates(exactFixture, 9, {mode:"knapsack"});
assert.equal(exact.optimal, true, "small additive-score budgets use exact DP");
assert.equal(exact.usedWords, 9);
assert.deepEqual(exact.selected.map(x=>x.id), ["a","b"], "exact knapsack chooses the maximum total score feasible subset");
const coverage = Engine.selectCandidates(scored, budget, { mode: "coverage", lambda: .25 });
assert.ok(coverage.selected.length >= 2,
  "atomic evidence extraction and coverage selection should avoid a one-item result on the research sample");
assert.ok(coverage.coveredFacets.length >= 2,
  "coverage policy should preserve more than one evidence facet");
assert.ok(coverage.coveredFacets.some(x => x.startsWith("priority:")),
  "coverage audit should expose fine-grained priority facets");
const coverageOnly = Engine.selectCandidates(scored, budget, {mode:"coverage_only",lambda:.25});
assert.ok(coverageOnly.trace.every(x => x.redundancy === 0), "coverage-only has no MMR redundancy penalty");
assert.ok(coverageOnly.trace.some(x => x.facetWeight > 1), "explicit priorities and hard requirements receive weighted facet gains");
const hardConstraint = units.find(x => x.facet === "hard:token_accounting");
assert.ok(hardConstraint && hardConstraint.words <= 9, "token-accounting evidence is compact enough to compete under tight budgets");
const sweep = [20, 30, 40, 50].map(p => Engine.selectCandidates(scored, Math.floor(sourceWords*p/100), {mode:"coverage",lambda:.25}));
assert.equal(sweep.length, 4);
assert.ok(sweep.every((r,i) => r.usedWords <= Math.floor(sourceWords*[20,30,40,50][i]/100)),
  "every budget-sweep point must respect its own cap");
assert.ok(sweep.every(r => Array.isArray(r.coveredFacets)), "each sweep point reports covered facets");
assert.equal(Engine.selectCandidates(scored, 0, { mode: "coverage" }).selected.length, 0);

const synthetic = [
  { id: "a", text: "project memory evidence retrieval", words: 4, score: .95, kind: "goal" },
  { id: "b", text: "project memory evidence retrieval system", words: 5, score: .90, kind: "goal" },
  { id: "c", text: "quarterly revenue forecast sales", words: 4, score: .82, kind: "technical" }
];
const sim = Engine.similarityMatrix(synthetic.map(x => x.text));
const withSim = synthetic.map((x, i) => ({ ...x, similarities: sim[i] }));
const ranked = Engine.selectCandidates(withSim, 9, { mode: "rank" });
const diversified = Engine.selectCandidates(withSim, 9, { mode: "mmr", lambda: .65 });
const covered = Engine.selectCandidates(withSim, 9, { mode: "coverage", lambda: .65, coverageBonus: .3 });
assert.deepEqual(ranked.selected.map(x => x.id), ["a", "b"]);
assert.ok(diversified.selected.some(x => x.id === "c"), "MMR should preserve complementary evidence when budget permits");
assert.ok(covered.selected.some(x => x.id === "c"), "coverage + MMR should reward a new evidence facet");

const saved = [
  { id: "1", role: "user", source: "test", text: "MemWeave preserves evidence under strict memory budgets.", words: 8 },
  { id: "2", role: "user", source: "test", text: "Evidence recall is not the same as answer accuracy.", words: 9 },
  { id: "3", role: "assistant", source: "test", text: "Would you like to add more detail?", words: 7 }
];
const labelMetrics = Engine.evaluateEvidenceSelection(["a","b"],["b","c"]);
assert.deepEqual(
  [labelMetrics.truePositives,labelMetrics.falsePositives,labelMetrics.falseNegatives,labelMetrics.precision,labelMetrics.recall,labelMetrics.f1],
  [1,1,1,.5,.5,.5],
  "manual gold-evidence labels produce transparent precision, recall, and F1"
);
const retrieved = Engine.rankEvidence("Where is the MemWeave memory budget?", saved);
assert.ok(retrieved.length >= 1);
assert.equal(retrieved[0].id, "1");
assert.ok(retrieved[0].matched.includes("memweave"));
assert.ok(retrieved[0].diversityPenalty >= 0);

// Keep retention and question-conditioned retrieval as separate evaluation stages.
const relevantForQuestion = ["1", "2"];
const retainedSubset = [saved[0]];
const retentionStage = Engine.evaluateEvidenceSelection(retainedSubset.map(x => x.id), relevantForQuestion);
const retrievedFromRetained = Engine.rankEvidence("Where does MemWeave preserve evidence under a strict memory budget?", retainedSubset, {limit:5});
const retrievalStage = Engine.evaluateEvidenceSelection(retrievedFromRetained.map(x => x.id), relevantForQuestion);
assert.equal(retentionStage.recall, 0.5, "retention recall measures gold evidence surviving the budget");
assert.equal(retrievalStage.precision, 1, "retrieval precision measures returned evidence against the labelled set");
assert.equal(retrievalStage.recall, 0.5, "retrieval recall is measured only over evidence available in the retained subset");

assert.deepEqual(Engine.parseConversation("one paragraph\n\nsecond paragraph").map(x => x.text),
  ["one paragraph", "second paragraph"]);
const exactOversized = Engine.selectCandidates(exactFixture, 2000000, {mode:"knapsack"});
assert.equal(exactOversized.optimal, false, "large DP workloads report their explicit greedy fallback");
assert.equal(exactOversized.mode, "knapsack");
console.log("MemWeave atomic-evidence, provenance, weighted-priority, knapsack, and baseline tests passed.");


// Bounded backup-file validation and sanitisation.
const SafeFiles = require("../site/safe-files.js");
const backup = SafeFiles.exportBackup(saved);
const restored = SafeFiles.parseBackup(backup);
assert.equal(restored.items.length, saved.length);
assert.equal(restored.items[0].words, Engine.countWords(restored.items[0].text), "word counts are recomputed, not trusted from uploaded JSON");
assert.ok(!Object.prototype.hasOwnProperty.call(restored.items[0], "unexpected"), "unknown uploaded fields are discarded");
assert.throws(() => SafeFiles.parseBackup("not json"), /valid JSON/);
assert.throws(() => SafeFiles.parseBackup(JSON.stringify({format:"unknown",items:[]})), /Unsupported backup format/);
assert.throws(() => SafeFiles.parseBackup(" ".repeat(SafeFiles.MAX_FILE_BYTES+1)), /5 MB/);
assert.throws(() => SafeFiles.normalizeItems(new Array(SafeFiles.MAX_ITEMS+1).fill({text:"x"})), /too many items/);
const untrusted = SafeFiles.parseBackup(JSON.stringify({format:"memweave-local-v2",items:[
  {text:"  Safe evidence <script>alert(1)</script>  ",role:"user",source:"test",words:999,id:"attacker-id",isAdmin:true,features:{novelty:4,meanSimilarity:.4},facet:"not-an-allowed-facet"},
  {text:"  Safe evidence <script>alert(1)</script>  ",role:"user",source:"test"}
]}));
assert.equal(untrusted.items.length,1,"duplicate records are collapsed during import");
assert.notEqual(untrusted.items[0].id,"attacker-id","uploaded identifiers are not trusted");
assert.equal(untrusted.items[0].isAdmin,undefined,"unknown fields cannot be imported");
assert.equal(untrusted.items[0].features.novelty,undefined,"out-of-range feature values are discarded");
assert.equal(untrusted.items[0].facet,undefined,"unknown facets are discarded");
assert.ok(!untrusted.items[0].text.includes("\\u0000"),"control characters are removed from imported text");
console.log("MemWeave safe-file validation tests passed.");
