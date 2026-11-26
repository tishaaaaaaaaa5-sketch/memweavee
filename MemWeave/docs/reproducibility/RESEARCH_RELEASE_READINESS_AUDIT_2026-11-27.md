# Research release readiness audit — 2026-11-27

**Scope:** open research PRs #2 and #3, the Stage C follow-up, the research artifact ZIP, and the proposed MFAR instrumentation path.  
**Decision:** do not merge either research PR as a public research release yet. Preserve the branches and their historical records; resolve the blockers below in a clean branch based on current main.

## Executive status

| Area | Current evidence | Release decision |
|---|---|---|
| Research PR #2 integration | 45 changed files; branch comparison with main is diverged (183 commits ahead, 81 behind at audit time). | Rebase/selectively port; do not merge the divergent branch directly. |
| PR #2 CI | The PR head has a completed successful MemWeave artifact-validation workflow. | Positive software check only; it does not verify missing binary artifacts or privacy. |
| Research ZIP | Independently extracted from the committed public-repository path. ZIP SHA-256 matches `32bc3f886f569a8fe788ca62b37032fe51d44178184b432539a7b224b7575634`; all 52 manifest-listed files match hashes and sizes; CRC and path checks pass. | Integrity passes. Privacy/licensing remains blocked: one CSV contains 26,913 cleartext LoCoMo spans (~810k characters), and LoCoMo/Long-MT-Bench+ redistribution conditions need explicit treatment. See [archive content audit](RESEARCH_ARCHIVE_CONTENT_AUDIT_2026-11-27.md). |
| Consolidated 88-cell Kaggle notebook | Branch audit reports 78 executed code cells and saved outputs in 74 cells. It is not the canonical source notebook and includes historical diagnostics. | Preserve only as an execution archive after reviewing the actual notebook and outputs; do not replace canonical notebooks. |
| Stage C research results | Reports describe LongMemEval, LoCoMo and Long-MT-Bench+ results; several raw per-question and audit exports are not committed as standalone artifacts. | Results remain exploratory and partially unaudited. Do not label them independently reproduced. |
| MFAR | Schema, adapter, retention audit and runtime event validators are proposed/implemented on the research branch. The current Stage B/C adapter covers retention only; real runtime event coverage is not demonstrated. | Treat as instrumentation/design work, not a validated MFAR method. |
| Research PR #3 | Draft PR based on PR #2; branch is diverged from main and has no associated PR CI run at the inspected head. | Do not merge until its literature claims and specification are reviewed on current main. |

## What is established, and what is not

### Stage B and Stage C must remain separate

The project records materially different historical LongMemEval role-aware evidence-recall results:

- Stage B: 0.709433.
- Stage C: 0.820638.

The Stage C dataset hashes recorded in the research branch are:

- LongMemEval-S: revision `98d7416c24c778c2fee6e6f3006e7a073259d48f`, SHA-256 `d6f21ea9d60a0d56f34a05b609c79c88a451d2ae03597821ea3d5a9678c3a442`.
- LoCoMo: revision `cbfbc1dba6bc53d00625212a0f22d55ffee7c1fc`, SHA-256 `79fa87e90f04081343b8c8debecb80a9a6842b76a7aa537dc9fdf651ea698ff4`.

These values are transcribed from the research-branch audit documents, not independently recomputed in this repository audit. Stage B must not inherit Stage C's checksums or provenance retroactively.

The Stage C notebook's reported 54 PASS / 3 WARNING / 0 FAIL is an internal audit of checks implemented in that notebook. It is not an independent rerun, an external audit of every evaluator mapping, or proof of independent generalization.

### Downstream reader results are exploratory

The research reports describe LoCoMo experiments over 10 conversation clusters and Long-MT-Bench+ experiments over 11 clusters. These are small cluster counts. Token F1 and exact match are lexical metrics and do not by themselves establish semantic entailment. The reports must be presented as preliminary transfer evidence, not definitive independent confirmation.

### MFAR has no end-to-end validation claim yet

The current offline adapter maps Stage B/C candidate and retention exports into partial traces. Retrieval, compression and answer stages are not observable in those exports. They must remain explicitly unobserved; do not infer failure labels or probabilities for missing stages.

The opt-in runtime hooks still require a real traced run on approved data, event-lineage validation, coverage reporting, and a traced-versus-untraced output-equivalence check. Until then, MFAR is an instrumentation/design proposal.

## Artifact and privacy release gates

The ZIP has now been independently extracted and its SHA-256, CRCs, paths, and all 52 manifest-listed file hashes and byte sizes have been verified. The full findings are recorded in [RESEARCH_ARCHIVE_CONTENT_AUDIT_2026-11-27.md](RESEARCH_ARCHIVE_CONTENT_AUDIT_2026-11-27.md).

The integrity result does **not** clear the archive for release. `locomo_reader_qa_evidence_span_flan_t5_base/evidence_span_selections.csv` contains 26,913 cleartext LoCoMo-derived spans (~810k characters) across 600 rows. The archive also contains text-bearing reader predictions and shortened question hashes. A narrow scan found no email/API-key/private-key patterns, but that is not a full privacy review.

The upstream LoCoMo dataset is CC BY-NC 4.0; the archive does not include the corresponding attribution/license notice or a modification notice. Long-MT-Bench+ result outputs are also present, while the inspected dataset card does not state a license. These issues must be resolved before the research ZIP is described as privacy-cleared or approved for public redistribution.

A ZIP passing CRC integrity (`testzip()`) does not establish scientific correctness, privacy safety, or redistribution permission.

## Required research-release work

- [x] Independently extract and verify the ZIP and all per-file manifest digests.
- [ ] Complete privacy/data-governance and dataset-license review; specifically decide whether to remove cleartext LoCoMo spans or distribute them with CC BY-NC attribution and non-commercial restrictions.
- [ ] Publish only the privacy-approved derived CSV/JSON exports with provenance manifests.
- [ ] Preserve the consolidated notebook as an archive, not as a canonical notebook replacement.
- [ ] Publish the corrected role-feature ablation aggregate with an explicit note that it is descriptive and lacks per-question uncertainty in the supplied summary.
- [ ] Reconcile all reader-QA per-question exports, cluster-bootstrap JSONs, tokenizer/budget audits, reader/model revisions, prompts and sample IDs.
- [ ] Re-run the relevant notebook/export audit from a clean environment after the exact source artifacts are available.
- [ ] Run MFAR runtime instrumentation on the real pipeline, validate lineage and compare traced/untraced outputs.
- [ ] Review the Strategy C related-work matrix against full papers and record task, budget, information access, dataset overlap, protocol and implementation details before making novelty claims.
- [ ] Rebase/selectively port PR #2 and PR #3 onto current main; resolve conflicts and run all relevant CI before asking for review.

## Recommended merge policy

- PR #2: keep open as a research integration draft until the artifact and privacy gates are satisfied. Its successful CI is not a substitute for those gates.
- PR #3: keep open as a dependent research-specification draft. First rebase it onto current main, then review its sources and novelty statement; do not merge it merely because it contains documentation rather than code.
- Do not merge binary research artifacts or raw benchmark material until the privacy and license review is complete.

## Audit limitation

This audit inspected GitHub branch/PR metadata and text files, then independently extracted and checked the committed research ZIP through a repository CI artifact. It did not rerun the Kaggle notebook, retrain models, or independently recompute the benchmark source-dataset digests. Archive integrity is independently verified; experimental results and scientific reproducibility are not.
