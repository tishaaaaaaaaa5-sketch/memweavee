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
assert.equal(messages.reduce((n, m) => n + m.words, 0), Engine.countWords(messages.map(m => m.text).join(" ")),
  "speaker labels are excluded from message-word accounting");

const units = Engine.buildCandidates(messages);
assert.equal(units.length, 6, "the final two-sentence message becomes two source-linked evidence units");
assert.equal(units[4].messageIndex, 4);
assert.equal(units[5].sourceId, units[4].sourceId);
assert.match(units[4].text, /benchmark and report/);
assert.match(units[5].text, /answer accuracy/);

const scored = Engine.scoreCandidates(units);
assert.ok(scored.every(x => Number.isFinite(x.score) && x.score >= 0 && x.score <= 1));
assert.ok(scored.every(x => x.features && Number.isFinite(x.features.novelty)));

for (const mode of ["rank", "density", "mmr"]) {
  const result = Engine.selectCandidates(scored, 22, { mode, lambda: 0.25 });
  assert.ok(result.usedWords <= 22, mode + " must respect the word-proxy budget");
  assert.equal(result.usedWords, result.selected.reduce((n, x) => n + x.words, 0));
  assert.equal(result.trace.length, result.selected.length);
}
assert.equal(Engine.selectCandidates(scored, 0).selected.length, 0);

const synthetic = [
  { id: "a", text: "project memory evidence retrieval", words: 4, score: .95 },
  { id: "b", text: "project memory evidence retrieval system", words: 5, score: .90 },
  { id: "c", text: "quarterly revenue forecast sales", words: 4, score: .82 }
];
const sim = Engine.similarityMatrix(synthetic.map(x => x.text));
const withSim = synthetic.map((x, i) => ({ ...x, similarities: sim[i] }));
const ranked = Engine.selectCandidates(withSim, 9, { mode: "rank" });
const diversified = Engine.selectCandidates(withSim, 9, { mode: "mmr", lambda: .65 });
assert.deepEqual(ranked.selected.map(x => x.id), ["a", "b"]);
assert.ok(diversified.selected.some(x => x.id === "c"), "MMR should preserve complementary evidence when budget permits");

const saved = [
  { id: "1", role: "user", source: "test", text: "MemWeave preserves evidence under strict memory budgets.", words: 8 },
  { id: "2", role: "user", source: "test", text: "Evidence recall is not the same as answer accuracy.", words: 9 },
  { id: "3", role: "assistant", source: "test", text: "Would you like to add more detail?", words: 7 }
];
const retrieved = Engine.rankEvidence("Where is the MemWeave memory budget?", saved);
assert.ok(retrieved.length >= 1);
assert.equal(retrieved[0].id, "1");
assert.ok(retrieved[0].matched.includes("memweave"));
assert.ok(retrieved[0].diversityPenalty >= 0);

assert.deepEqual(Engine.parseConversation("one paragraph\n\nsecond paragraph").map(x => x.text),
  ["one paragraph", "second paragraph"]);
console.log("MemWeave evidence-engine tests passed.");
