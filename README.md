# MemWeave
### Role-aware, budget-constrained memory retention for long-horizon conversations

MemWeave studies a practical question for conversational assistants: **when the full conversation history cannot fit in memory, which sessions should be retained so that future questions remain answerable?**

This repository contains a multi-stage research project: the original query-agnostic retention study and benchmark audit (v2.0–v2.3), followed by a role-aware feature experiment with a held-out locked-test evaluation. The stages answer related but distinct questions; their headline numbers should not be pooled or presented as one continuous model comparison.

> **Current headline (role-aware follow-up):** on 235 held-out test questions from the `same_pipeline` pool, role-aware session scoring increased 10%-budget evidence recall from **40.42% to 70.94%** (+30.52 percentage points). The paired question-level bootstrap 95% CI was **[25.30, 35.96] pp**. This is a promising result on one benchmark split, not proof of improved end-to-end answer accuracy or independent generalization.

---

## Research snapshot

| Item | Current role-aware follow-up |
|---|---|
| Benchmark | LongMemEval-S cleaned |
| Evaluation pool | `same_pipeline` (primary pool in the final notebook) |
| Split | 235 DEV / 235 locked TEST questions; abstention questions excluded |
| Model | Logistic regression, `C = 0.3` |
| Comparison | Baseline feature set vs. baseline + six message-role-aware features |
| Selection budget | 10% of pool word count (word count is the notebook's budget proxy) |
| Primary outcome | Question-level budgeted evidence recall |
| Held-out sample | 235 questions |
| OOF reconstruction | Exact for baseline and role-aware scores (maximum absolute error 0.0) |

## Main held-out result

| Metric | Baseline | Role-aware | Change |
|---|---:|---:|---:|
| Budgeted evidence recall | 0.4042 | **0.7094** | **+0.3052** |
| Recall@1 | 0.4255 | **0.8000** | +0.3745 |
| Recall@3 | 0.6128 | **0.8979** | +0.2851 |
| Recall@5 | 0.7064 | **0.9447** | +0.2383 |
| Recall@10 | 0.8000 | **0.9702** | +0.1702 |
| MRR | 0.5486 | **0.8546** | +0.3060 |
| Mean gold rank | 5.8553 | **1.9277** | -3.9277 |

Paired inference for budgeted recall:
- Paired mean gain: **+0.305248**.
- Question-level paired bootstrap 95% CI: **[0.252979, 0.359574]**.
- Sign-flip permutation: Monte Carlo `p = 0.000005` at the resolution of 200,000 permutations (plus-one correction; report as `p ≤ 0.000005`).
- Exact paired sign test: `p = 5.11 × 10⁻²⁵`; 96 positive differences, 3 negative, 136 ties.
- Gold-rank direction: 127 improved, 3 worsened, 105 unchanged.

The bootstrap resamples questions, not conversation clusters. Conversation-level dependence has not been ruled out.

## Results by question type

| Question type | n | Baseline | Role-aware | Gain |
|---|---:|---:|---:|---:|
| Single-session user | 32 | 0.0625 | 0.6875 | +0.6250 |
| Knowledge update | 36 | 0.4444 | 0.8333 | +0.3889 |
| Temporal reasoning | 63 | 0.4082 | 0.6648 | +0.2566 |
| Single-session assistant | 28 | 0.6786 | 0.9286 | +0.2500 |
| Single-session preference | 15 | 0.0000 | 0.2000 | +0.2000 |
| Multi-session | 61 | 0.5290 | 0.7186 | +0.1896 |

Holm-adjusted paired sign tests were significant for five of six groups. The preference group was inconclusive (`p_{Holm} = 0.25`) and has only 15 questions. Category-level estimates are exploratory subgroup results; they do not establish causal feature attribution.

## Research lineage: do not conflate the stages

- **v2.0–v2.3:** the original 500-question query-agnostic retention study, its benchmark-shortcut audit, corrected inference, and external/QA proxy analyses. The corrected v2.3 result found only a small and sensitivity-dependent advantage over the strongest simple heuristic; see `MemWeave/results/findings_v2_3.txt`.
- **Role-aware follow-up:** the separate 235-question held-out evaluation documented in `MemWeave/results/final_locked_test/`. It compares a baseline feature set with an augmented set containing six message-role-aware features. It does not retroactively change the v2.3 result.

## Repository map

```text
.
├── README.md
└── MemWeave/
    ├── README.md                    # project guide and research lineage
    ├── PROJECT_OVERVIEW.md           # concise project scope
    ├── notebooks/
    │   ├── README.md                # canonical notebook index
    │   ├── 00_MemWeave_2_0.ipynb
    │   ├── 01_MemWeave_2_1.ipynb
    │   ├── 02_MemWeave_2_2.ipynb
    │   ├── 03_memweave_v2_3_addendum.ipynb
    │   └── 04_MemWeave_Final.ipynb
    └── results/
        ├── README.md
        ├── findings_v2_3.txt
        ├── tables/                  # curated v2.3 tables
        ├── v2_0/ ... v2_2/          # historical, versioned results
        └── final_locked_test/       # role-aware held-out audit
```

### Recommended reading order

1. Read this page for the current headline and the distinction between research stages.
2. Read [the project guide](MemWeave/README.md) and [notebook index](MemWeave/notebooks/README.md).
3. Read [the final locked-test report](MemWeave/results/final_locked_test/README.md) before quoting the role-aware result.
4. Read [the v2.3 corrected findings](MemWeave/results/findings_v2_3.txt) for the earlier study's more cautious result.
5. Inspect the notebook source and run manifests before attempting reproduction.

## Reproducibility

The notebooks are designed for Jupyter/Google Colab. Run them from a clean kernel, in order, and retain the generated outputs and manifests. Dataset JSONs, feature caches, and raw per-question exports are not committed here; obtain the datasets under their applicable terms and verify the checksums recorded by the relevant run.

For the role-aware follow-up, the notebook reports:
- `same_pipeline` pool; `C = 0.3`; 10% word-count budget.
- 235 DEV and 235 locked TEST questions.
- 4,216 / 5,523 retained training rows for both model variants after the held-out content-overlap filter.
- Exact OOF score reconstruction before the TEST evaluation.
- 50,000 paired bootstrap resamples and 200,000 sign-flip permutations for the primary audit.

The currently committed `04_MemWeave_Final.ipynb` is the source notebook. The executed notebook uploaded during the repository update contains saved outputs, but those outputs are not silently represented as committed notebook outputs. The aggregate results and protocol are documented under `MemWeave/results/final_locked_test/`.

## Limitations and responsible claims

- Evidence retention/retrieval metrics are not end-to-end answer correctness.
- The result comes from one benchmark and one locked split; the split is not an independent external replication.
- The project evolved iteratively. The final test was held out for the reported evaluation, but the overall research process was not preregistered.
- The role-aware feature bundle has not been isolated by a complete feature ablation; subgroup gains do not prove which feature caused the improvement.
- Question-level bootstrap inference may understate uncertainty if questions share conversations.
- The single-session preference subgroup is small and inconclusive.
- The 10% budget uses word count as a proxy in the final notebook; it should not be described as an exact tokenizer-based token budget.

## Citation

A formal citation entry should be added when the manuscript's author list, title, venue/status, and year are finalized. Until then, cite the repository and identify the work as an ongoing research project; do not invent a publication venue or DOI.
