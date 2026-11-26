"""Read-only dashboard for aggregate artifacts and registered pipeline runs."""
import json
import os
from pathlib import Path

import pandas as pd
import streamlit as st

from memweave.comparison import (
    assess_run_comparability,
    compare_run_metrics,
    configuration_differences,
)
from memweave.registry import RunRegistry

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "final_locked_test"
REGISTRY_CANDIDATES = [
    ROOT.parent / "results" / "run_registry.sqlite3",
    ROOT / "results" / "run_registry.sqlite3",
]
DEFAULT_REGISTRY = next(
    (candidate for candidate in REGISTRY_CANDIDATES if candidate.is_file()),
    REGISTRY_CANDIDATES[0],
)

st.set_page_config(page_title="MemWeave Research Explorer", layout="wide")
st.title("MemWeave | Research Explorer")
st.caption("Read-only exploration of committed aggregate artifacts and completed local runs.")

paths = [
    RESULTS / "run_manifest.json",
    RESULTS / "paired_test_audit.json",
    RESULTS / "question_type_breakdown.csv",
]
if not all(path.is_file() for path in paths):
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
st.bar_chart(pd.DataFrame({
    "Evidence recall": {"Baseline": baseline, "Role-aware": role_aware}
}))
st.subheader("Question-type breakdown")
st.dataframe(pd.read_csv(paths[2]), use_container_width=True, hide_index=True)

with st.expander("Committed aggregate metadata and interpretation"):
    st.json(manifest)
    st.json(audit.get("provenance", {}))
    st.warning(
        "Evidence retention is not answer accuracy. This aggregate view does not rerun the model."
    )

st.divider()
st.header("Experiment run history and comparison")
registry_path = Path(
    os.environ.get("MEMWEAVE_REGISTRY_PATH", str(DEFAULT_REGISTRY))
).expanduser()

if not registry_path.is_file():
    st.info(
        f"No local run registry found at {registry_path}. Run memweave run first, "
        "or set MEMWEAVE_REGISTRY_PATH to an existing SQLite registry."
    )
else:
    try:
        run_records = RunRegistry(registry_path).list_runs(limit=1000)
    except (OSError, ValueError) as exc:
        st.error(f"Could not read run registry: {exc}")
        run_records = []

    if not run_records:
        st.info("The run registry is empty; completed pipeline runs will appear here.")
    else:
        history_rows = [
            {
                "run_id": item["run_id"],
                "created_at": item["created_at"],
                "primary_pool": item["summary"].get("primary_pool"),
                "n_valid": item["summary"].get("n_valid"),
                "n_dev": item["summary"].get("n_dev"),
                "n_test": item["summary"].get("n_test"),
                "output_dir": item["output_dir"],
            }
            for item in run_records
        ]
        st.subheader("Completed runs")
        st.dataframe(pd.DataFrame(history_rows), use_container_width=True, hide_index=True)

        option_to_id = {
            f"{item['created_at']} · {item['run_id']}": item["run_id"]
            for item in run_records
        }
        options = list(option_to_id)
        defaults = options[: min(2, len(options))]
        selected_labels = st.multiselect(
            "Select runs to compare",
            options=options,
            default=defaults,
            help="Choose two or more runs to compare metrics and configuration settings.",
        )
        selected_ids = [option_to_id[label] for label in selected_labels]

        if selected_ids:
            comparability = assess_run_comparability(run_records, selected_ids)
            st.subheader("Provenance and comparability")
            status = comparability["status"]
            if status == "directly_comparable":
                st.success(
                    "Directly comparable on the primary LongMemEval evidence-recall "
                    "protocol: dataset, DEV/TEST splits, metric definition, budget, "
                    "budget unit and primary pool all match."
                )
            elif status == "not_comparable":
                st.warning(
                    "These runs are not directly comparable at the primary metric level. "
                    "At least one dataset, split, metric, budget or pool field differs."
                )
            elif status == "insufficient_provenance":
                st.info(
                    "Comparability cannot be established: one or more selected runs predate "
                    "the structured provenance fields. Missing provenance is not evidence "
                    "that runs match."
                )
            else:
                st.caption("Select at least two registered runs to assess comparability.")

            if comparability["differences"]:
                st.caption("Mismatched provenance fields")
                st.dataframe(
                    pd.DataFrame([
                        {"field": field, **values}
                        for field, values in comparability["differences"].items()
                    ]),
                    use_container_width=True,
                    hide_index=True,
                )
            if comparability["missing"]:
                st.caption("Missing provenance fields")
                st.dataframe(
                    pd.DataFrame([
                        {"run_id": run_id, "missing_fields": ", ".join(fields)}
                        for run_id, fields in comparability["missing"].items()
                    ]),
                    use_container_width=True,
                    hide_index=True,
                )
            st.caption(
                "This gate checks primary LongMemEval evidence-recall comparability. "
                "It does not prove causal attribution or independent replication; "
                "model/configuration differences remain visible below."
            )

            metric_rows = compare_run_metrics(run_records, selected_ids)
            if metric_rows:
                metrics = pd.DataFrame(metric_rows)
                st.subheader("Metric comparison")
                visible = [
                    column for column in (
                        "run_id", "pool", "method", "recall@budget",
                        "ci_low", "ci_high", "n_test_questions",
                    )
                    if column in metrics.columns
                ]
                st.dataframe(metrics[visible], use_container_width=True, hide_index=True)

                pivot = metrics.pivot_table(
                    index=["pool", "method"],
                    columns="run_id",
                    values="recall@budget",
                    aggfunc="first",
                )
                st.subheader("Recall by pool and method")
                st.dataframe(pivot.reset_index(), use_container_width=True, hide_index=True)
                st.caption(
                    "These are descriptive run-level comparisons. Different splits, seeds, "
                    "budgets, or input datasets can make runs non-comparable; this view does "
                    "not calculate paired significance tests."
                )
            else:
                st.info("The selected runs do not contain stored main-results summaries.")

            differences = configuration_differences(run_records, selected_ids)
            st.subheader("Configuration differences")
            if differences:
                diff_rows = [
                    {"setting": item["path"], **item["values"]}
                    for item in differences
                ]
                st.dataframe(pd.DataFrame(diff_rows), use_container_width=True, hide_index=True)
            elif len(selected_ids) < 2:
                st.caption("Select at least two runs to inspect configuration differences.")
            else:
                st.success("The selected runs have identical stored configurations.")
