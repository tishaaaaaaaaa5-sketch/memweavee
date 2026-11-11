# MemWeave

MemWeave investigates query-agnostic session-memory retention under a fixed token budget, using LongMemEval-S. It evaluates temporal relevance, rarity, uniqueness, and importance against recency, random, heuristic, and single-feature baselines. The primary metric is session-level evidence recall. Current results do not establish reliable superiority over the strongest simple heuristic; exploratory ablations should be interpreted cautiously.

Run the accompanying notebooks in Jupyter or Google Colab. Dataset files and large generated outputs may need to be supplied separately. The approximately 135 MB results archive exceeds GitHub's standard 100 MB per-file limit; use Git LFS or external artifact storage for it.