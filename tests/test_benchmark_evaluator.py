"""
Unit Tests for Benchmark Evaluator and Analytical Models.
"""
import unittest
import numpy as np
import pandas as pd

from postprocessing.benchmark_evaluator import (
    binary_entropy,
    secret_key_rate,
    calculate_attack_detection_and_false_alarm,
    get_analytical_curves,
    run_live_benchmark
)


class TestBenchmarkEvaluator(unittest.TestCase):

    def test_binary_entropy(self):
        self.assertEqual(binary_entropy(0.0), 0.0)
        self.assertEqual(binary_entropy(1.0), 0.0)
        self.assertAlmostEqual(binary_entropy(0.5), 1.0, places=5)
        self.assertAlmostEqual(binary_entropy(0.11), 0.5000, places=2)

    def test_secret_key_rate(self):
        # At zero error, secret key rate should be equal to sifting yield
        self.assertAlmostEqual(secret_key_rate(0.50, 0.0), 0.50, places=4)
        self.assertAlmostEqual(secret_key_rate(0.25, 0.0), 0.25, places=4)
        
        # Above threshold, key rate drops to 0.0
        self.assertEqual(secret_key_rate(0.50, 0.25), 0.0)
        self.assertEqual(secret_key_rate(0.25, 0.15), 0.0)

    def test_attack_detection_and_false_alarm(self):
        res = calculate_attack_detection_and_false_alarm(
            n_samples=40,
            qber_threshold=0.11,
            noise_level=0.02,
            eve_rate=0.5
        )
        self.assertIn("false_alarm_rate", res)
        self.assertIn("detection_rate", res)
        self.assertTrue(0.0 <= res["false_alarm_rate"] <= 1.0)
        self.assertTrue(0.0 <= res["detection_rate"] <= 1.0)
        # With active attack (p1 >> p0), detection rate should exceed false alarm rate
        self.assertGreater(res["detection_rate"], res["false_alarm_rate"])

    def test_analytical_curves(self):
        curves = get_analytical_curves()
        self.assertIn("df_noise", curves)
        self.assertIn("df_attack", curves)
        self.assertIn("df_roc", curves)
        self.assertIn("df_matrix", curves)

        df_noise = curves["df_noise"]
        self.assertFalse(df_noise.empty)
        self.assertIn("BB84 QBER (%)", df_noise.columns)
        self.assertIn("B92 QBER (%)", df_noise.columns)
        self.assertIn("E91 QBER (%)", df_noise.columns)
        self.assertIn("E91 Bell |S|", df_noise.columns)

        df_matrix = curves["df_matrix"]
        self.assertEqual(len(df_matrix), 7)
        self.assertIn("Feature / Metric", df_matrix.columns)
        self.assertIn("BB84", df_matrix.columns)
        self.assertIn("B92", df_matrix.columns)
        self.assertIn("E91", df_matrix.columns)

    def test_live_benchmark_execution(self):
        # Small run on 16 qubits
        res = run_live_benchmark(num_qubits=16, noise_level=0.02, eve_intensity=0.0)
        self.assertIn("summary_df", res)
        self.assertIn("bb84_res", res)
        self.assertIn("b92_res", res)
        self.assertIn("e91_res", res)

        summary_df = res["summary_df"]
        self.assertEqual(len(summary_df), 3)
        self.assertListEqual(list(summary_df["Protocol"]), ["BB84", "B92", "E91"])


if __name__ == "__main__":
    unittest.main()
