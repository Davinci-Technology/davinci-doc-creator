"""
Simple script to create baseline PDFs for regression testing
"""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_pdf
from tests.fixtures import FIXTURES, DEFAULT_CONFIG
from tests.pdf_compare import PDFRegressionTester

def main():
    baseline_dir = os.path.join(os.path.dirname(__file__), 'tests', 'baselines')
    tester = PDFRegressionTester(baseline_dir)

    print("Creating baseline PDFs...")
    print(f"Baseline directory: {baseline_dir}\n")

    for name, markdown in FIXTURES.items():
        print(f"Creating baseline for '{name}'...")
        pdf_buffer = create_pdf(markdown, DEFAULT_CONFIG)
        baseline_path = tester.save_baseline(name, pdf_buffer)
        print(f"  ✓ Saved: {baseline_path}\n")

    print("✅ All baselines created successfully!")
    print(f"\nBaselines saved to: {baseline_dir}")
    print(f"Total baselines: {len(FIXTURES)}")

if __name__ == '__main__':
    main()
