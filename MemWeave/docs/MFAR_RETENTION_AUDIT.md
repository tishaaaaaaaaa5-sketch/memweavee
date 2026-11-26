# Audit the original MFAR retention traces

**Status:** real-data audit utility for the Stage B/C LongMemEval candidate-retention export. It does not use synthetic records.

## Purpose

`scripts/audit_mfar_retention_traces.py` consumes the JSONL created by `assemble_mfar_retention_traces.py` and calculates retention-stage measurements from the original candidate export:

- candidate and gold-candidate counts;
- retained candidate and retained gold counts;
- gold candidates not retained;
- micro- and macro-averaged retention recall;
- retention precision and candidate-retention rate;
- mean utilization of the recorded word-count-proxy budget.

It also checks that query/variant records are unique, every stored memory maps back to one candidate and its source evidence, candidate-pool counts match across variants, and all four MFAR probabilities and oracle labels remain null.

## Run in Kaggle

After assembling the real traces from the original Stage B/C candidate CSV and manifest:

```bash
python MemWeave/scripts/audit_mfar_retention_traces.py \
  --input /kaggle/working/mfar_retention_traces.jsonl \
  --per-trace-output /kaggle/working/mfar_retention_audit_per_trace.csv \
  --summary-output /kaggle/working/mfar_retention_audit_summary.json
```

The script uses only Python's standard library. It does not access raw benchmark text and does not modify the input traces.

## Interpretation boundary

A gold candidate that was not selected is reported as a **retention-stage omission**. It is not automatically labelled as a construction failure or compression failure. The Stage B/C export does not record a separate source-to-candidate construction trace, a pre/post-compression comparison, a retrieval operation, or answer generation.

Consequently, all four MFAR failure labels remain `NOT_OBSERVABLE` in the audit CSV, and all diagnosis probabilities remain unestimated. This script does not train a failure detector, assign oracle labels, or claim end-to-end answer accuracy.

The recorded budget is a word-count proxy, not exact tokenizer-based token usage. Treat all hashes and opaque identifiers as potentially linkable metadata and keep outputs access-controlled.
