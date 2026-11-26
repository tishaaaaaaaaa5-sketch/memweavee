# MFAR retention audit: observed real-data results

**Run date:** 2026-11-26  
**Input:** original Stage B/C LongMemEval candidate-retention traces  
**Scope:** 2,115 traces, 235 held-out questions, nine conditions (baseline plus eight factorial variants)  
**Status:** audit completed successfully in the user's Kaggle environment; this report records the supplied run output.

## Audit outcome

The audit processed all 2,115 traces. Candidate-pool consistency and evidence-provenance checks passed. No failure labels were inferred: construction, compression, retrieval, and answering all remain `NOT_OBSERVABLE`. This is a retention-stage audit, not an MFAR diagnostic-model evaluation.

## Results by condition

| Condition | Micro retention recall | Gold candidates not retained | Mean budget utilization |
|---|---:|---:|---:|
| Baseline | 0.423841 | 261 | 0.872741 |
| Raw, cap 20,000, unfiltered | 0.675497 | 147 | 0.894938 |
| Raw, cap 20,000, filtered | 0.675497 | 147 | 0.894938 |
| Raw, uncapped, unfiltered | 0.655629 | 156 | 0.892854 |
| Raw, uncapped, filtered | 0.655629 | 156 | 0.892854 |
| Z-score, cap 20,000, unfiltered | **0.750552** | **113** | 0.898518 |
| Z-score, cap 20,000, filtered | **0.750552** | **113** | 0.898518 |
| Z-score, uncapped, unfiltered | 0.746137 | 115 | 0.899297 |
| Z-score, uncapped, filtered | 0.746137 | 115 | 0.899297 |

The best observed retention condition is z-score scaling with the 20,000-feature cap. Relative to baseline, its micro retention recall is higher by 0.326711 (32.67 percentage points), and it retains 148 more gold candidates (261 fewer omissions). This is a descriptive comparison of the supplied run; no new confidence interval or significance test is asserted here.

## Factorial observations

- **Filtering:** filtered and unfiltered results are exactly equal within each scaling/cap pair. In this run, the message-filter factor produced no measurable change in the reported retention outcomes.
- **Scaling:** z-score conditions outperform their raw counterparts in both cap settings.
- **Vocabulary cap:** with z-score scaling, the capped condition is slightly higher in recall than the uncapped condition (0.750552 vs 0.746137), while uncapped mean budget utilization is slightly higher. Do not interpret this small descriptive difference as statistically significant without paired inference.
- **Budget utilization:** values are based on the recorded word-count-proxy budget, not exact tokenizer tokens.

## Interpretation limits

1. These metrics measure whether gold candidates were retained by the selection policy. They are not retrieval recall, answer accuracy, or end-to-end conversational-memory quality.
2. A missed gold candidate is a retention omission in this export. It does not establish whether the underlying cause was construction, compression, retrieval, or answering.
3. All four MFAR failure modes remain `NOT_OBSERVABLE`; no labels or probabilities were generated.
4. The supplied audit output confirms structural and provenance checks for this export. It does not independently reproduce the original feature extraction or model fitting.
5. Raw benchmark content and large per-trace outputs are not committed. Keep the Kaggle CSV/JSON artifacts access-controlled and retain their checksums in the local run record.

## Next engineering gate

Before implementing MFAR diagnostics or interventions, identify and instrument the actual memory backend that performs construction, compression, retrieval, and answer generation. The repository currently contains the MFAR algorithm specification and a retention-trace adapter, but the adapter alone does not expose those lifecycle stages. Instrumentation must attach to the real pipeline; do not substitute a mock or synthetic backend. Until the backend and its event logs are available, do not train a failure detector or label the four modes.
