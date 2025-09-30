"""
Regression tests using baseline PDFs
Run with --save-baseline to create new baselines
Run normally to compare against baselines
"""
import unittest
import sys
import os
import io

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_pdf
from tests.fixtures import FIXTURES, DEFAULT_CONFIG
from tests.pdf_compare import PDFRegressionTester


class TestPDFRegression(unittest.TestCase):
    """Regression tests comparing against baseline PDFs"""

    @classmethod
    def setUpClass(cls):
        """Set up baseline directory"""
        cls.baseline_dir = os.path.join(
            os.path.dirname(__file__),
            'baselines'
        )
        cls.tester = PDFRegressionTester(cls.baseline_dir)

        # Check if we should save baselines
        cls.save_baseline = '--save-baseline' in sys.argv
        if cls.save_baseline:
            print("\n=== SAVING NEW BASELINES ===")
            sys.argv.remove('--save-baseline')

    def _test_fixture_regression(self, fixture_name):
        """Helper to test a fixture against its baseline"""
        markdown = FIXTURES[fixture_name]
        pdf_buffer = create_pdf(markdown, DEFAULT_CONFIG)

        if self.save_baseline:
            # Save as new baseline
            baseline_path = self.tester.save_baseline(fixture_name, pdf_buffer)
            print(f"Saved baseline: {baseline_path}")
            # When saving baselines, mark test as passed
            self.assertTrue(True, f"Baseline saved for {fixture_name}")
            return

        # Compare to baseline
        result = self.tester.compare_to_baseline(fixture_name, pdf_buffer)

        if not result['identical']:
            msg = f"PDF differs from baseline for {fixture_name}\n"
            msg += f"Differences: {len(result['differences'])}\n"
            for diff in result['differences']:
                msg += f"  - {diff}\n"
            self.fail(msg)

    def test_simple_regression(self):
        """Regression test for simple document"""
        self._test_fixture_regression('simple')

    def test_lists_regression(self):
        """Regression test for lists document"""
        self._test_fixture_regression('lists')

    def test_formatting_regression(self):
        """Regression test for formatting document"""
        self._test_fixture_regression('formatting')

    def test_table_regression(self):
        """Regression test for table document"""
        self._test_fixture_regression('table')

    def test_complex_regression(self):
        """Regression test for complex document"""
        self._test_fixture_regression('complex')

    def test_metadata_regression(self):
        """Regression test for metadata document"""
        self._test_fixture_regression('metadata')

    def test_edge_cases_regression(self):
        """Regression test for edge cases document"""
        self._test_fixture_regression('edge_cases')

    def test_all_baselines_exist(self):
        """Verify all expected baselines exist"""
        if self.save_baseline:
            self.skipTest("Skipping when saving baselines")

        baselines = self.tester.list_baselines()
        expected = list(FIXTURES.keys())

        missing = set(expected) - set(baselines)
        if missing:
            self.fail(f"Missing baselines: {missing}. Run with --save-baseline first.")


if __name__ == '__main__':
    # Usage: python test_regression.py --save-baseline  (to create baselines)
    #        python test_regression.py                   (to test against baselines)

    # Remove --save-baseline from sys.argv before unittest.main() processes it
    # It's already been captured in setUpClass
    if '--save-baseline' in sys.argv:
        sys.argv.remove('--save-baseline')

    unittest.main()
