from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import mfar_reference_pipeline as reference


class MfarReferencePipelineTests(unittest.TestCase):
    def test_all_scenarios_validate_against_schema(self):
        try:
            from jsonschema import Draft202012Validator, FormatChecker
        except ImportError:
            self.skipTest("jsonschema is optional in the development environment")
        schema = json.loads((ROOT / "schemas" / "mfar_trace.schema.json").read_text(encoding="utf-8"))
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        for scenario in sorted(reference.SCENARIOS):
            with self.subTest(scenario=scenario):
                trace = reference.run_scenario(scenario, "2026-11-26T12:00:00Z")
                self.assertEqual(list(validator.iter_errors(trace)), [])
                self.assertIsNone(trace["oracle_labels"])

    def test_each_failure_scenario_has_distinct_stage_signature(self):
        clean = reference.run_scenario("clean")
        construction = reference.run_scenario("construction_loss")
        compression = reference.run_scenario("compression_loss")
        retrieval = reference.run_scenario("retrieval_loss")
        answering = reference.run_scenario("answering_failure")

        self.assertEqual(len(clean["pipeline"]["candidate_memory"]), 1)
        self.assertEqual(len(construction["pipeline"]["candidate_memory"]), 0)
        self.assertEqual(len(compression["pipeline"]["candidate_memory"]), 1)
        self.assertEqual(len(compression["pipeline"]["stored_memory"]), 0)
        self.assertEqual(len(retrieval["pipeline"]["stored_memory"]), 1)
        self.assertEqual(len(retrieval["pipeline"]["retrieved_evidence"]), 0)
        self.assertEqual(len(answering["pipeline"]["retrieved_evidence"]), 1)
        self.assertEqual(answering["outcome"]["claim_support"][0]["support_status"], "unsupported")

    def test_fixture_never_claims_a_learned_diagnosis_or_oracle_label(self):
        for scenario in reference.SCENARIOS:
            trace = reference.run_scenario(scenario)
            self.assertTrue(all(value is None for value in trace["diagnosis"]["probabilities"].values()))
            self.assertIsNone(trace["oracle_labels"])
            self.assertEqual(trace["controller"]["selected_action"], "diagnostic_only")


if __name__ == "__main__":
    unittest.main()
