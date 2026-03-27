import unittest

from scripts.run_quality_checks import QualityResult, build_checks, summarize_results


class QualityToolsTests(unittest.TestCase):
    def test_build_checks_contains_required_compile_and_unittest_steps(self):
        checks = build_checks("python")

        self.assertEqual(checks[0].name, "compileall")
        self.assertTrue(checks[0].required)
        self.assertEqual(checks[1].name, "unittest")
        self.assertTrue(checks[1].required)
        self.assertIn("src/main.py", checks[2].command)
        self.assertIn("src/interface.py", checks[2].command)
        self.assertIn("src/font.py", checks[3].command)

    def test_summarize_results_only_fails_on_required_errors(self):
        checks = build_checks("python")
        results = (
            QualityResult(check=checks[0], returncode=0, stdout="", stderr=""),
            QualityResult(check=checks[1], returncode=0, stdout="", stderr=""),
            QualityResult(check=checks[2], returncode=1, stdout="", stderr="", skipped=False),
        )

        ok, summary = summarize_results(results)

        self.assertTrue(ok)
        self.assertIn("[PASS] compileall", summary)
        self.assertIn("[FAIL] ruff", summary)


if __name__ == "__main__":
    unittest.main()
