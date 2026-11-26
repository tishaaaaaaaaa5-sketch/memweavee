from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import assemble_mfar_retention_traces as adapter


class RetentionTraceAdapterTests(unittest.TestCase):
    def setUp(self):
        self.manifest = {
            "longmemeval_revision": "a" * 40,
            "longmemeval_sha256": "b" * 64,
            "pool": "same_pipeline",
            "budget_fraction": 0.10,
            "budget_cost_unit": "word-count proxy; not exact tokens",
        }
        self.rows = [
            {
                "qid": "c" * 20,
                "query_hash": "d" * 64,
                "variant": "baseline",
                "candidate_index": 0,
                "source_id": "src_" + "1" * 32,
                "content_hash": "2" * 64,
                "grade": "gold",
                "word_cost": 120.0,
                "selected": True,
            },
            {
                "qid": "c" * 20,
                "query_hash": "d" * 64,
                "variant": "baseline",
                "candidate_index": 1,
                "source_id": "src_" + "3" * 32,
                "content_hash": "4" * 64,
                "grade": "irrelevant",
                "word_cost": 80.0,
                "selected": False,
            },
        ]

    def test_optional_candidate_checksum_is_verified(self):
        with tempfile.NamedTemporaryFile(mode="wb") as handle:
            handle.write(b"candidate-export")
            handle.flush()
            expected = hashlib.sha256(b"candidate-export").hexdigest()
            adapter.verify_candidate_checksum(Path(handle.name), expected)
            with self.assertRaises(SystemExit):
                adapter.verify_candidate_checksum(Path(handle.name), "0" * 64)

    def test_trace_preserves_observability_boundary(self):
        trace = adapter.build_trace(
            "c" * 20, "baseline", self.rows, self.manifest,
            "2026-11-26T00:00:00Z",
        )
        self.assertEqual(trace["schema_version"], "0.2.0")
        self.assertEqual(len(trace["pipeline"]["source_evidence"]), 2)
        self.assertEqual(len(trace["pipeline"]["candidate_memory"]), 2)
        self.assertEqual(len(trace["pipeline"]["stored_memory"]), 1)
        self.assertEqual(trace["pipeline"]["retrieved_evidence"], [])
        self.assertFalse(trace["observability"]["retrieval_trace_available"])
        self.assertFalse(trace["observability"]["answer_trace_available"])
        self.assertTrue(all(v is None for v in trace["diagnosis"]["probabilities"].values()))
        self.assertEqual(trace["outcome"]["status"], "not_evaluated")
        self.assertIsNone(trace["outcome"]["answer_id"])

    def test_repeated_source_session_preserves_distinct_candidate_occurrences(self):
        repeated = [dict(row) for row in self.rows]
        repeated[1].update({
            "candidate_index": 1,
            "source_id": repeated[0]["source_id"],
            "content_hash": repeated[0]["content_hash"],
            "grade": "irrelevant",
        })
        trace = adapter.build_trace(
            "c" * 20, "baseline", repeated, self.manifest,
            "2026-11-26T00:00:00Z",
        )
        evidence_ids = [x["evidence_id"] for x in trace["pipeline"]["source_evidence"]]
        memory_ids = [x["memory_id"] for x in trace["pipeline"]["candidate_memory"]]
        self.assertEqual(len(evidence_ids), len(set(evidence_ids)))
        self.assertEqual(len(memory_ids), len(set(memory_ids)))
        self.assertEqual(
            [x["source_id"] for x in trace["pipeline"]["source_evidence"]],
            [repeated[0]["source_id"], repeated[1]["source_id"]],
        )
        adapter.validate_groups({
            ("c" * 20, "baseline"): repeated,
        })

    def test_candidate_pool_must_match_across_variants(self):
        groups = {
            ("c" * 20, "baseline"): [dict(row) for row in self.rows],
            ("c" * 20, "variant-b"): [
                {**row, "variant": "variant-b"} for row in self.rows
            ],
        }
        adapter.validate_groups(groups)
        groups[("c" * 20, "variant-b")][1]["source_id"] = "src_" + "5" * 32
        with self.assertRaises(SystemExit):
            adapter.validate_groups(groups)

    def test_generated_trace_passes_schema(self):
        try:
            from jsonschema import Draft202012Validator, FormatChecker
        except ImportError:
            self.skipTest("jsonschema is optional in the development environment")
        schema_path = ROOT / "schemas" / "mfar_trace.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        trace = adapter.build_trace(
            "c" * 20, "baseline", self.rows, self.manifest,
            "2026-11-26T00:00:00Z",
        )
        errors = list(Draft202012Validator(
            schema, format_checker=FormatChecker()
        ).iter_errors(trace))
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
