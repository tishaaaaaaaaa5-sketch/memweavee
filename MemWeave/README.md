# MemWeave

Research notebooks for query-agnostic session-memory retention under a fixed token budget, evaluated on LongMemEval-S.

## Repository layout

```text
MemWeave/
├── README.md
├── PROJECT_OVERVIEW.md
└── notebooks/
    └── memweave_v2_3_addendum.ipynb
```

## Recommended reading order

1. **PROJECT_OVERVIEW.md** — research question, method, evaluation metric, and interpretation limits.
2. **notebooks/memweave_v2_3_addendum.ipynb** — follow-up analysis notebook.
3. The v2.2 research notebooks and final notebook will be added after their complete source files can be transferred and validated.

## Reproducing experiments

Use Jupyter or Google Colab. Review each notebook's setup/configuration cells before running. LongMemEval-S data and generated result files may need to be downloaded or supplied separately.

## Reporting results responsibly

The primary metric is session-level evidence recall. QA-proxy results are supplementary, not an official LLM-judge score. Current evidence does not establish reliable superiority over the strongest simple heuristic; exploratory analyses should be labelled accordingly.

## Large artifacts

Do not commit the approximately 135 MB `results.zip` as a normal Git file: it exceeds GitHub's 100 MB per-file limit. Store it with Git LFS or an external artifact store if needed.