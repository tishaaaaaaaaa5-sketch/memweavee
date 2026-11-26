"""Read-only dashboard for committed MemWeave aggregate artifacts."""
import json
from pathlib import Path
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "final_locked_test"
st.set_page_config(page_title="MemWeave Research Explorer", layout="wide")
st.title("MemWeave | Research Explorer")
st.caption("Read-only exploration of committed aggregate artifacts. No model is run here.")
paths = [RESULTS / "run_manifest.json", RESULTS / "paired_test_audit.json", RESULTS / "question_type_breakdown.csv"]
if not all(p.is_file() for p in paths):
    st.error("Required aggregate result files are missing.")
    st.stop()
manifest = json.loads(paths[0].read_text(encoding="utf-8"))
audit = json.loads(paths[1].read_text(encoding="utf-8"))
test = audit.get("test_metrics", {})
baseline = float(test["baseline_budgeted_evidence_recall"])
role_aware = float(test["role_aware_budgeted_evidence_recall"])
gain = float(test["paired_mean_gain"])
a, b, c = st.columns(3)
a.metric("Baseline evidence recall", f"{baseline:.1%}")
b.metric("Role-aware evidence recall", f"{role_aware:.1%}")
c.metric("Paired gain", f"{gain:+.1%}")
st.subheader("Aggregate comparison")
st.bar_chart(pd.DataFrame({"Evidence recall": {"Baseline": baseline, "Role-aware": role_aware}}))
st.subheader("Question-type breakdown")
st.dataframe(pd.read_csv(paths[2]), use_container_width=True, hide_index=True)
with st.expander("Run metadata and interpretation"):
    st.json(manifest)
    st.json(audit.get("provenance", {}))
    st.warning("Evidence retention is not answer accuracy; this dashboard does not rerun the model.")
