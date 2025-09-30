"""
PDF Comparison utilities for regression testing
Helps identify visual and structural changes in generated PDFs
"""
import os
import io
from PyPDF2 import PdfReader
from PIL import Image
import hashlib


class PDFComparator:
    """Compare two PDFs for regression testing"""

    def __init__(self):
        self.differences = []

    def compare(self, pdf1_buffer, pdf2_buffer):
        """
        Compare two PDFs and return differences

        Returns:
            dict: Comparison results with details about differences
        """
        self.differences = []

        # Reset buffers
        pdf1_buffer.seek(0)
        pdf2_buffer.seek(0)

        try:
            reader1 = PdfReader(pdf1_buffer)
            reader2 = PdfReader(pdf2_buffer)
        except Exception as e:
            return {
                'identical': False,
                'error': f"Failed to read PDFs: {e}",
                'differences': []
            }

        # Compare page count
        if len(reader1.pages) != len(reader2.pages):
            self.differences.append({
                'type': 'page_count',
                'pdf1': len(reader1.pages),
                'pdf2': len(reader2.pages)
            })

        # Compare text content on each page
        max_pages = max(len(reader1.pages), len(reader2.pages))
        for i in range(max_pages):
            if i < len(reader1.pages) and i < len(reader2.pages):
                text1 = reader1.pages[i].extract_text()
                text2 = reader2.pages[i].extract_text()

                if text1 != text2:
                    self.differences.append({
                        'type': 'text_content',
                        'page': i + 1,
                        'text1_length': len(text1),
                        'text2_length': len(text2),
                        'preview1': text1[:100] if text1 else '',
                        'preview2': text2[:100] if text2 else ''
                    })

        # Compare file sizes (rough proxy for structural differences)
        pdf1_buffer.seek(0)
        pdf2_buffer.seek(0)
        size1 = len(pdf1_buffer.read())
        size2 = len(pdf2_buffer.read())

        size_diff_percent = abs(size1 - size2) / max(size1, size2) * 100

        if size_diff_percent > 1:  # More than 1% difference
            self.differences.append({
                'type': 'file_size',
                'pdf1': size1,
                'pdf2': size2,
                'diff_percent': size_diff_percent
            })

        return {
            'identical': len(self.differences) == 0,
            'differences': self.differences,
            'summary': {
                'page_count_diff': any(d['type'] == 'page_count' for d in self.differences),
                'text_content_diff': any(d['type'] == 'text_content' for d in self.differences),
                'size_diff': any(d['type'] == 'file_size' for d in self.differences)
            }
        }

    def get_pdf_fingerprint(self, pdf_buffer):
        """
        Generate a fingerprint of PDF content (excluding timestamps)

        Returns:
            str: Hash of PDF text content
        """
        pdf_buffer.seek(0)
        try:
            reader = PdfReader(pdf_buffer)
            text_content = ""
            for page in reader.pages:
                text_content += page.extract_text()

            # Hash the text content
            return hashlib.sha256(text_content.encode()).hexdigest()
        except Exception as e:
            return f"error: {e}"


class PDFRegressionTester:
    """Manager for regression testing PDFs"""

    def __init__(self, baseline_dir):
        """
        Initialize regression tester

        Args:
            baseline_dir: Directory containing baseline PDFs
        """
        self.baseline_dir = baseline_dir
        os.makedirs(baseline_dir, exist_ok=True)
        self.comparator = PDFComparator()

    def save_baseline(self, name, pdf_buffer):
        """Save a PDF as baseline for future comparisons"""
        baseline_path = os.path.join(self.baseline_dir, f"{name}.pdf")
        pdf_buffer.seek(0)
        with open(baseline_path, 'wb') as f:
            f.write(pdf_buffer.read())
        pdf_buffer.seek(0)

        # Also save fingerprint
        fingerprint = self.comparator.get_pdf_fingerprint(pdf_buffer)
        fingerprint_path = os.path.join(self.baseline_dir, f"{name}.fingerprint")
        with open(fingerprint_path, 'w') as f:
            f.write(fingerprint)

        return baseline_path

    def compare_to_baseline(self, name, pdf_buffer):
        """
        Compare a PDF to its baseline

        Returns:
            dict: Comparison results
        """
        baseline_path = os.path.join(self.baseline_dir, f"{name}.pdf")

        if not os.path.exists(baseline_path):
            return {
                'identical': False,
                'error': f"No baseline found for {name}. Run with --save-baseline first.",
                'differences': []
            }

        with open(baseline_path, 'rb') as f:
            baseline_buffer = io.BytesIO(f.read())

        return self.comparator.compare(baseline_buffer, pdf_buffer)

    def check_fingerprint(self, name, pdf_buffer):
        """
        Quick check using fingerprint (faster than full comparison)

        Returns:
            bool: True if fingerprints match
        """
        fingerprint_path = os.path.join(self.baseline_dir, f"{name}.fingerprint")

        if not os.path.exists(fingerprint_path):
            return False

        with open(fingerprint_path, 'r') as f:
            baseline_fingerprint = f.read().strip()

        current_fingerprint = self.comparator.get_pdf_fingerprint(pdf_buffer)

        return baseline_fingerprint == current_fingerprint

    def list_baselines(self):
        """List all available baseline PDFs"""
        if not os.path.exists(self.baseline_dir):
            return []

        baselines = []
        for filename in os.listdir(self.baseline_dir):
            if filename.endswith('.pdf'):
                baselines.append(filename[:-4])  # Remove .pdf extension
        return sorted(baselines)


def compare_pdfs_simple(pdf1_path, pdf2_path):
    """
    Simple utility function to compare two PDF files

    Args:
        pdf1_path: Path to first PDF
        pdf2_path: Path to second PDF

    Returns:
        dict: Comparison results
    """
    with open(pdf1_path, 'rb') as f1, open(pdf2_path, 'rb') as f2:
        buffer1 = io.BytesIO(f1.read())
        buffer2 = io.BytesIO(f2.read())

    comparator = PDFComparator()
    return comparator.compare(buffer1, buffer2)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Compare two PDF files')
    parser.add_argument('pdf1', help='First PDF file')
    parser.add_argument('pdf2', help='Second PDF file')
    args = parser.parse_args()

    result = compare_pdfs_simple(args.pdf1, args.pdf2)

    print(f"\nComparison Results:")
    print(f"==================")
    print(f"Identical: {result['identical']}")

    if result['differences']:
        print(f"\nDifferences found: {len(result['differences'])}")
        for diff in result['differences']:
            print(f"\n- {diff['type'].upper()}")
            for key, value in diff.items():
                if key != 'type':
                    print(f"  {key}: {value}")
    else:
        print("\nNo differences found!")
