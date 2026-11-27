"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const root = path.resolve(__dirname, "..");
const read = (relative) => fs.readFileSync(path.join(root, relative), "utf8");
const portal = read("site/research.html");
const finalAudit = read("MemWeave/results/final_locked_test/README.md");
const finalJson = read("MemWeave/results/final_locked_test/paired_test_audit.json");
const stageBC = read("MemWeave/results/stage_bc_2026-11-26/README.md");
const followup = read("MemWeave/results/followup_2026/README.md");
const reader = read("MemWeave/results/followup_2026/LOCOMO_END_TO_END_READER_QA_INITIAL_RESULTS.md");
const releaseAudit = read("MemWeave/docs/reproducibility/RESEARCH_RELEASE_READINESS_AUDIT_2026-11-27.md");
const freeze = read("MemWeave/docs/research/CANONICAL_PIPELINE_FREEZE.md");

// Keep the portal's headline values tied to their actual source records.
assert.match(finalAudit, /0\.404184[\s\S]*?0\.709433/);
assert.match(finalJson, /"role_aware_budgeted_evidence_recall":\s*0\.7094326241/);
assert.match(portal, /70\.94% recall/);
assert.match(portal, /\+30\.52 pp/);
assert.match(portal, /\+25\.30,\+35\.96/);

assert.match(stageBC, /Z-score role features, unlimited vocabulary \| 0\.820638/);
assert.match(followup, /Role-aware evidence recall \| 0\.820638/);
assert.match(followup, /Paired gain \| \+0\.416454/);
assert.match(followup, /Message similarity group \| \*\*\+0\.42071\*\*/);
assert.match(portal, /82\.06% recall/);
assert.match(portal, /0\.820638/);
assert.match(portal, /message-similarity feature group/);

// Reader QA is a separate exploratory endpoint, not evidence recall.
assert.match(reader, /Role-aware \| 200 \| 0\.080 \| 0\.2057/);
assert.match(portal, /Token F1 0\.1015/);
assert.match(portal, /Token F1 0\.2057/);

// Protect the interpretation boundary: the repeatedly inspected TEST split
// must not be presented as an untouched confirmatory set.
assert.match(releaseAudit, /TEST set used in the Stage B\/C analysis has now been inspected repeatedly/);
assert.match(freeze, /not an untouched confirmatory test set/);
assert.match(portal, /not an untouched confirmatory test set/);
assert.match(portal, /historical held-out result/);
assert.doesNotMatch(portal, /235-question held-out LongMemEval-S split/);
assert.doesNotMatch(portal, /235 held-out questions/);

// The source links must point to the canonical records that back the claims.
assert.match(portal, /MemWeave\/results\/followup_2026\/README\.md/);
assert.match(portal, /MemWeave\/results\/final_locked_test\/README\.md/);
assert.match(portal, /MemWeave\/docs\/reproducibility\/RESEARCH_RELEASE_READINESS_AUDIT_2026-11-27\.md/);

console.log("Research portal provenance checks passed.");
