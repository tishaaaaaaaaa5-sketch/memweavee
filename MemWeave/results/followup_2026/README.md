# MemWeave follow-up: recovery, ablations, and LoCoMo transfer

**Status:** executed notebook supplied; artifact audit passed with warnings  
**Scope:** regenerated LongMemEval-S follow-up and frozen-model LoCoMo transfer check  
**Important:** this is a new run and must not be merged numerically with the earlier role-aware result.

## Executive summary

The supplied executed Kaggle notebook regenerated the privacy-safe per-question LongMemEval export, recorded immutable dataset provenance, ran feature ablations, and evaluated models frozen on LongMemEval DEV data against LoCoMo.

The final notebook audit reported **54 PASS, 3 WARNING, 0 FAIL**. This is an artifact-integrity audit, not proof of end-to-end independent reproduction. The remaining warnings concern independent budget reconstruction, end-to-end evidence mapping, and independent replication.

## LongMemEval-S regenerated run

| Item | Value |
|---|---:|
| Dataset | LongMemEval-S cleaned |
| Dataset revision | `98d7416c24c778c2fee6e6f3006e7a073259d48f` |
| Dataset SHA-256 | `d6f21ea9d60a0d56f34a05b609c79c88a451d2ae03597821ea3d5a9678c3a442` |
| Pool | `same_pipeline` |
| DEV / TEST | 235 / 235 |
| Model | Logistic regression, `C=0.3` |
| Selection budget | 10% word-count proxy |
| Baseline evidence recall | 0.404184 |
| Role-aware evidence recall | 0.820638 |
| Paired gain | +0.416454 |
| Paired bootstrap 95% CI | [0.358723, 0.474184] |

These regenerated values differ from the earlier repository headline (0.709433 role-aware recall; +0.305248 gain). Treat the runs as separate experimental records. Do not silently replace or combine the historical result. The current run reconstructs the canonical pipeline and feature matrices at the pinned source commit; differences require a documented reconciliation before a single headline is chosen.

The privacy-safe per-question CSV contains 235 rows, 20-character SHA-256 question identifiers, candidate/gold counts, rank, budgeted recall, and budget utilization. The notebook recorded its SHA-256 as:

`fbe3c234c6038d0918dc1b5f8648fdb39fecd790df5fb52bdb6f7743b9b6d82a`

No raw question text, answers, or conversation content should be committed.

## Feature ablation findings

The group ablation is the strongest diagnostic signal:

| Ablation | Full minus ablated recall | 95% CI | Holm-adjusted p |
|---|---:|---:|---:|
| User message group | +0.03922 | [0.00929, 0.07007] | 0.17242 |
| Assistant message group | +0.02199 | [0.00284, 0.04397] | 1.00000 |
| Message similarity group | **+0.42071** | [0.36248, 0.47872] | <0.00001 (rounded to 0.00000 in notebook) |
| Message count group | 0.00000 | [0.00000, 0.00000] | 1.00000 |

The similarity group appears to account for most of the observed gain. This is a priority for interpretation: the result may reflect stronger question-to-message similarity signals rather than a distinct benefit from role-awareness itself. Individual leave-one-feature-out effects were small or inconclusive after correction. Do not claim that every role feature contributes.

## Frozen LoCoMo transfer evaluation

The notebook pinned LoCoMo to commit `cbfbc1dba6bc53d00625212a0f22d55ffee7c1fc` with SHA-256:

`79fa87e90f04081343b8c8debecb80a9a6842b76a7aa537dc9fdf651ea698ff4`

The frozen baseline and role-aware models were fit on LongMemEval DEV only. LoCoMo was not used for fitting, tuning, calibration, or feature selection. Ten conversations and 1,536 questions were processed under each of two speaker-role orientations.

| Orientation | Role-aware macro recall | Baseline macro recall | Difference |
|---|---:|---:|---:|
| speaker_a as user | 0.61694 | 0.09350 | +0.52344 |
| speaker_b as user | 0.61650 | 0.09350 | +0.52300 |

Conversation-cluster bootstrap intervals for role-aware minus baseline were [0.47717, 0.57130] and [0.48287, 0.56638], respectively. The role-aware model also exceeded the recency, low-novelty, and random comparators in the reported conversation-level summaries.

**Interpretation limit:** this is preliminary cross-dataset transfer evidence, not definitive independent replication. There are only ten conversation clusters; orientation variants are sensitivity analyses, not independent replications. Speaker-role mapping and evidence-annotation alignment still require a dedicated audit.

## Provenance and audit

- LongMemEval source: https://huggingface.co/datasets/xiaowu0162/longmemeval-cleaned
- LoCoMo source: https://github.com/snap-research/locomo
- Canonical source notebook commit: `d642215226fa2a9204bb6d64c4ff0f6447920274`
- Final artifact audit: 54 PASS / 3 WARNING / 0 FAIL
- Audit status: **ARTIFACT CHECKS PASSED WITH WARNINGS**

### Remaining release blockers

1. Independently reconstruct the word-count budget from selected session IDs and word costs; the current export records utilization but not the full selection trace.
2. Audit the complete gold-evidence-to-session mapping end to end; existing-session reference checks alone do not prove evaluator correctness.
3. Verify speaker-role mapping and annotation alignment for LoCoMo.
4. Re-run the audit from the committed CSV/JSON files, not only from notebook state.
5. Obtain a clean, independently executed reproduction before making a strong replication claim.

## Artifact inventory

The supplied notebook reports that it generated:

- `memweave_role_aware_per_question_privacy_safe.csv`
- `role_feature_ablation.csv`
- `memweave_followup_run_manifest.json`
- `locomo_per_conversation_speaker_a_user.csv`
- `locomo_per_conversation_speaker_b_user.csv`
- `locomo_frozen_validation_summary.csv`

The supplied ZIP export is preserved at `../artifacts/2026-11-26/MemWeave_Research_Artifacts.zip`. Its notebook export cell reports 52 archived files and a passing ZIP integrity check; independently verify every manifest entry and complete privacy review before treating the bundle as release-certified. The notebook itself should be committed as an executed, privacy-reviewed notebook after removing obsolete/debug audit outputs.


## End-to-end reader QA — implemented, awaiting execution

Notebook 05 now contains a predeclared reader evaluation that tests whether the frozen role-aware selector improves generated answer quality, rather than only evidence retention. It uses the pinned LoCoMo dataset, a fixed google/flan-t5-small reader, up to 20 answerable evidence-annotated questions per conversation, and exact tokenizer-counted 10% storage budgets. The primary comparison is role-aware versus baseline; recency and question-only are controls. Exact match and token F1 are scored, with paired bootstrap resampling over conversation clusters.

This is a new answer-quality endpoint, but **not untouched independent confirmation**: LoCoMo was already used for selector-transfer analysis and has only ten conversation clusters. The protocol and limitations are in [END_TO_END_READER_QA_PROTOCOL.md](END_TO_END_READER_QA_PROTOCOL.md). Results remain pending until the Kaggle cell is executed.