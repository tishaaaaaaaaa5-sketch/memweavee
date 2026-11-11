# MemWeave

MemWeave studies budget-constrained conversational-memory retention: which conversation sessions should an assistant preserve when it cannot keep the entire history?

The repository contains an original query-agnostic retention study (v2.0–v2.3) and a separate role-aware feature follow-up. In the latter, a 235-question held-out test evaluation reports budgeted evidence recall of 0.4042 for the baseline and 0.7094 for the role-aware model (+0.3052; paired bootstrap 95% CI [0.252979, 0.359574]).

This is an evidence-retention result, not an end-to-end answer-accuracy result. The held-out split is from the same benchmark, the overall research process was iterative rather than preregistered, and conversation-level dependence has not been ruled out. The earlier v2.3 study found a smaller and sensitivity-dependent advantage over its strongest simple baseline; it remains a separate result.

Start with the [repository README](../README.md), then consult the [project guide](README.md), [notebook index](notebooks/README.md), and [final locked-test report](results/final_locked_test/README.md).
