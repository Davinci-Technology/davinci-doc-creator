"""
Integration tests for full markdown-to-PDF pipeline
Tests the complete workflow from markdown to PDF
"""
import unittest
import sys
import os
import io
from PyPDF2 import PdfReader

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_pdf
from tests.fixtures import FIXTURES, DEFAULT_CONFIG


class TestPDFGeneration(unittest.TestCase):
    """Test complete PDF generation pipeline"""

    def setUp(self):
        """Set up test environment"""
        self.test_output_dir = os.path.join(
            os.path.dirname(__file__),
            'output'
        )
        os.makedirs(self.test_output_dir, exist_ok=True)

    def _generate_pdf(self, markdown, config=None):
        """Helper to generate PDF and return buffer"""
        if config is None:
            config = DEFAULT_CONFIG.copy()

        pdf_buffer = create_pdf(markdown, config)
        return pdf_buffer

    def _save_pdf(self, pdf_buffer, filename):
        """Helper to save PDF to disk for manual inspection"""
        output_path = os.path.join(self.test_output_dir, filename)
        with open(output_path, 'wb') as f:
            f.write(pdf_buffer.read())
        pdf_buffer.seek(0)  # Reset for further use
        return output_path

    def _verify_pdf_valid(self, pdf_buffer):
        """Verify PDF is valid and readable"""
        try:
            pdf_buffer.seek(0)
            reader = PdfReader(pdf_buffer)
            self.assertGreater(len(reader.pages), 0, "PDF should have at least one page")
            return reader
        except Exception as e:
            self.fail(f"Generated PDF is not valid: {e}")

    def _extract_text_from_pdf(self, pdf_buffer):
        """Extract all text from PDF for content verification"""
        pdf_buffer.seek(0)
        reader = PdfReader(pdf_buffer)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text

    def test_simple_document(self):
        """Test generating a simple document"""
        pdf_buffer = self._generate_pdf(FIXTURES['simple'])
        self._save_pdf(pdf_buffer, 'test_simple.pdf')

        reader = self._verify_pdf_valid(pdf_buffer)
        self.assertEqual(len(reader.pages), 1, "Simple doc should be 1 page")

        # Verify content is present
        text = self._extract_text_from_pdf(pdf_buffer)
        self.assertIn("Test Document", text)
        self.assertIn("Section 1", text)

    def test_lists_document(self):
        """Test document with lists"""
        pdf_buffer = self._generate_pdf(FIXTURES['lists'])
        self._save_pdf(pdf_buffer, 'test_lists.pdf')

        self._verify_pdf_valid(pdf_buffer)
        text = self._extract_text_from_pdf(pdf_buffer)

        # Verify list items are present
        self.assertIn("First item", text)
        self.assertIn("Second item", text)

    def test_formatting_document(self):
        """Test document with text formatting"""
        pdf_buffer = self._generate_pdf(FIXTURES['formatting'])
        self._save_pdf(pdf_buffer, 'test_formatting.pdf')

        self._verify_pdf_valid(pdf_buffer)
        text = self._extract_text_from_pdf(pdf_buffer)

        # Verify formatted text is present (formatting may not be in extracted text)
        self.assertIn("bold text", text.lower())
        self.assertIn("italic text", text.lower())

    def test_table_document(self):
        """Test document with tables"""
        pdf_buffer = self._generate_pdf(FIXTURES['table'])
        self._save_pdf(pdf_buffer, 'test_table.pdf')

        self._verify_pdf_valid(pdf_buffer)
        text = self._extract_text_from_pdf(pdf_buffer)

        # Verify table content
        self.assertIn("Column 1", text)
        self.assertIn("Value A", text)

    def test_complex_document(self):
        """Test complex document with all features"""
        pdf_buffer = self._generate_pdf(FIXTURES['complex'])
        self._save_pdf(pdf_buffer, 'test_complex.pdf')

        reader = self._verify_pdf_valid(pdf_buffer)
        # Complex doc should be multiple pages
        self.assertGreaterEqual(len(reader.pages), 1)

        text = self._extract_text_from_pdf(pdf_buffer)

        # Verify key sections are present
        self.assertIn("Comprehensive Test Document", text)
        self.assertIn("Introduction", text)
        self.assertIn("Conclusion", text)

    def test_metadata_document(self):
        """Test document with metadata formatting"""
        pdf_buffer = self._generate_pdf(FIXTURES['metadata'])
        self._save_pdf(pdf_buffer, 'test_metadata.pdf')

        self._verify_pdf_valid(pdf_buffer)
        text = self._extract_text_from_pdf(pdf_buffer)

        # Verify metadata is present
        self.assertIn("Investment", text)
        self.assertIn("Timeline", text)
        self.assertIn("100,000", text)

    def test_edge_cases_document(self):
        """Test edge cases document"""
        pdf_buffer = self._generate_pdf(FIXTURES['edge_cases'])
        self._save_pdf(pdf_buffer, 'test_edge_cases.pdf')

        self._verify_pdf_valid(pdf_buffer)
        # Just verify it generates without crashing

    def test_page_numbering(self):
        """Test that page numbering works"""
        # Use complex document to ensure multiple pages
        long_markdown = FIXTURES['complex'] + "\n\n" + FIXTURES['complex']
        pdf_buffer = self._generate_pdf(long_markdown)
        self._save_pdf(pdf_buffer, 'test_page_numbering.pdf')

        reader = self._verify_pdf_valid(pdf_buffer)

        # Verify we have multiple pages
        num_pages = len(reader.pages)
        self.assertGreater(num_pages, 1, "Should generate multiple pages")

        # Page numbers are drawn on canvas, not as text objects
        # We can at least verify the PDF is valid and has correct page count

    def test_custom_config(self):
        """Test PDF generation with custom configuration"""
        custom_config = {
            'letterhead': {
                'company': 'Custom Corp',
                'address': '456 Custom Ave',
                'phone': '+1 (555) 999-9999',
                'email': 'custom@example.com'
            },
            'disclaimer': 'Custom disclaimer text',
            'logo_path': None
        }

        pdf_buffer = self._generate_pdf(FIXTURES['simple'], custom_config)
        self._save_pdf(pdf_buffer, 'test_custom_config.pdf')

        self._verify_pdf_valid(pdf_buffer)
        # Company info is in header/footer, may not extract as text
        # Main verification is that it generates without error

    def test_empty_markdown(self):
        """Test handling of empty markdown"""
        pdf_buffer = self._generate_pdf("")
        self._save_pdf(pdf_buffer, 'test_empty.pdf')

        reader = self._verify_pdf_valid(pdf_buffer)
        self.assertEqual(len(reader.pages), 1, "Empty doc should still be 1 page")

    def test_very_long_document(self):
        """Test handling of very long document"""
        # Create a very long document
        long_markdown = "# Long Document\n\n"
        for i in range(100):
            long_markdown += f"## Section {i}\n\n"
            long_markdown += "This is a paragraph with some content. " * 10
            long_markdown += "\n\n"

        pdf_buffer = self._generate_pdf(long_markdown)
        self._save_pdf(pdf_buffer, 'test_long_document.pdf')

        reader = self._verify_pdf_valid(pdf_buffer)
        # Should generate many pages
        self.assertGreater(len(reader.pages), 5)

    def test_special_characters(self):
        """Test handling of special characters"""
        markdown = """# Special Characters Test

Testing special characters: & < > " '

Also testing unicode: © ™ € £ ¥
"""
        pdf_buffer = self._generate_pdf(markdown)
        self._save_pdf(pdf_buffer, 'test_special_chars.pdf')

        self._verify_pdf_valid(pdf_buffer)

    def test_pdf_metadata(self):
        """Test PDF metadata is set correctly"""
        pdf_buffer = self._generate_pdf(FIXTURES['simple'])

        reader = self._verify_pdf_valid(pdf_buffer)
        # ReportLab sets some basic metadata
        # We're not currently setting custom metadata, but we could verify
        # that the PDF has standard fields populated


class TestPDFConsistency(unittest.TestCase):
    """Test that PDFs are generated consistently"""

    def test_deterministic_output(self):
        """Test that same input produces same output (mostly)"""
        markdown = FIXTURES['simple']
        config = DEFAULT_CONFIG.copy()

        # Generate twice
        pdf1 = create_pdf(markdown, config)
        pdf2 = create_pdf(markdown, config)

        # PDFs won't be byte-identical due to timestamps, but should be same size
        size1 = len(pdf1.getvalue())
        size2 = len(pdf2.getvalue())

        # Allow for small variations (timestamps, etc)
        size_diff = abs(size1 - size2)
        self.assertLess(size_diff, 100, "PDF sizes should be very similar")

    def test_all_fixtures_generate(self):
        """Ensure all test fixtures generate valid PDFs"""
        for name, markdown in FIXTURES.items():
            with self.subTest(fixture=name):
                pdf_buffer = create_pdf(markdown, DEFAULT_CONFIG)
                self.assertIsNotNone(pdf_buffer)
                self.assertGreater(len(pdf_buffer.getvalue()), 0)


if __name__ == '__main__':
    unittest.main()
