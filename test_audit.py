import unittest
import audit

class ReliabilityAuditTests(unittest.TestCase):
    def test_baseline_metrics(self):
        rows = audit.evaluate(audit.baseline)
        s = audit.summary(rows)
        self.assertAlmostEqual(s["overall_pass_rate"], 0.40)
        self.assertAlmostEqual(s["evidence_or_abstention_accuracy"], 0.70)
        self.assertAlmostEqual(s["supported_answer_accuracy"], 9 / 16)
        self.assertAlmostEqual(s["unsupported_abstention_rate"], 0.0)

    def test_improved_metrics(self):
        rows = audit.evaluate(audit.reliability_aware)
        s = audit.summary(rows)
        self.assertAlmostEqual(s["overall_pass_rate"], 0.95)
        self.assertAlmostEqual(s["evidence_or_abstention_accuracy"], 1.0)
        self.assertAlmostEqual(s["supported_answer_accuracy"], 15 / 16)
        self.assertAlmostEqual(s["unsupported_abstention_rate"], 1.0)

    def test_known_remaining_failure_is_preserved(self):
        rows = audit.evaluate(audit.reliability_aware)
        failures = [row["id"] for row in rows if not row["pass"]]
        self.assertEqual(failures, ["Q07"])

if __name__ == "__main__":
    unittest.main()
