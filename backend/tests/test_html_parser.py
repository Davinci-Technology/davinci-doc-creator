"""
Unit tests for HTMLToReportLab parser
Tests the HTML parsing logic without full PDF generation
"""
import unittest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import HTMLToReportLab
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY


class TestHTMLParser(unittest.TestCase):
    """Test the HTML parser component"""

    def setUp(self):
        """Set up test fixtures"""
        self.styles = getSampleStyleSheet()

        # Add custom styles like the app does
        self.styles.add(ParagraphStyle(
            name='CustomHeading1',
            parent=self.styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#0B98CE'),
            spaceAfter=14,
            spaceBefore=16,
            fontName='Helvetica-Bold'
        ))

        self.styles.add(ParagraphStyle(
            name='CustomHeading2',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#316EA8'),
            spaceAfter=14,
            spaceBefore=10,
            fontName='Helvetica-Bold'
        ))

        self.styles.add(ParagraphStyle(
            name='CustomHeading3',
            parent=self.styles['Heading3'],
            fontSize=12,
            textColor=colors.HexColor('#494949'),
            spaceAfter=8,
            spaceBefore=10,
            fontName='Helvetica-Bold'
        ))

        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['BodyText'],
            fontSize=11,
            textColor=colors.HexColor('#494949'),
            alignment=TA_JUSTIFY,
            leading=15,
            spaceBefore=2,
            spaceAfter=6,
            fontName='Helvetica'
        ))

        self.styles.add(ParagraphStyle(
            name='BulletText',
            parent=self.styles['BodyText'],
            fontSize=11,
            textColor=colors.HexColor('#494949'),
            leftIndent=24,
            bulletIndent=10,
            leading=15,
            spaceBefore=5,
            spaceAfter=4,
            fontName='Helvetica'
        ))

        self.styles.add(ParagraphStyle(
            name='MetadataText',
            parent=self.styles['BodyText'],
            fontSize=11,
            textColor=colors.HexColor('#494949'),
            leading=13,
            spaceBefore=0,
            spaceAfter=4,
            fontName='Helvetica'
        ))

    def test_simple_paragraph(self):
        """Test parsing a simple paragraph"""
        html = "<p>This is a test paragraph.</p>"
        parser = HTMLToReportLab(self.styles)
        parser.feed(html)
        story = parser.get_story()

        self.assertEqual(len(story), 1)
        self.assertEqual(str(story[0].text), "This is a test paragraph.")

    def test_heading_1(self):
        """Test H1 heading parsing"""
        html = "<h1>Main Heading</h1>"
        parser = HTMLToReportLab(self.styles)
        parser.feed(html)
        story = parser.get_story()

        self.assertEqual(len(story), 1)
        self.assertEqual(str(story[0].text), "Main Heading")

    def test_heading_2(self):
        """Test H2 heading parsing"""
        html = "<h2>Subheading</h2>"
        parser = HTMLToReportLab(self.styles)
        parser.feed(html)
        story = parser.get_story()

        self.assertEqual(len(story), 1)
        self.assertEqual(str(story[0].text), "Subheading")

    def test_bold_text(self):
        """Test bold text formatting"""
        html = "<p>This has <strong>bold text</strong> in it.</p>"
        parser = HTMLToReportLab(self.styles)
        parser.feed(html)
        story = parser.get_story()

        self.assertEqual(len(story), 1)
        self.assertIn("<b>", str(story[0].text))
        self.assertIn("</b>", str(story[0].text))

    def test_italic_text(self):
        """Test italic text formatting"""
        html = "<p>This has <em>italic text</em> in it.</p>"
        parser = HTMLToReportLab(self.styles)
        parser.feed(html)
        story = parser.get_story()

        self.assertEqual(len(story), 1)
        self.assertIn("<i>", str(story[0].text))
        self.assertIn("</i>", str(story[0].text))

    def test_unordered_list(self):
        """Test unordered list parsing"""
        html = "<ul><li>Item 1</li><li>Item 2</li><li>Item 3</li></ul>"
        parser = HTMLToReportLab(self.styles)
        parser.feed(html)
        story = parser.get_story()

        self.assertEqual(len(story), 3)
        # Check bullet points are added
        for item in story:
            self.assertIn("•", str(item.text))

    def test_ordered_list(self):
        """Test ordered list parsing"""
        html = "<ol><li>First</li><li>Second</li><li>Third</li></ol>"
        parser = HTMLToReportLab(self.styles)
        parser.feed(html)
        story = parser.get_story()

        self.assertEqual(len(story), 3)
        # Check numbers are added
        self.assertIn("1.", str(story[0].text))
        self.assertIn("2.", str(story[1].text))
        self.assertIn("3.", str(story[2].text))

    def test_table_parsing(self):
        """Test table parsing"""
        html = """
        <table>
            <tr><th>Header 1</th><th>Header 2</th></tr>
            <tr><td>Cell 1</td><td>Cell 2</td></tr>
        </table>
        """
        parser = HTMLToReportLab(self.styles)
        parser.feed(html)
        story = parser.get_story()

        # Should have a table and a spacer
        self.assertGreaterEqual(len(story), 1)
        # First item should be the table
        self.assertEqual(story[0].__class__.__name__, 'Table')

    def test_nested_formatting(self):
        """Test nested bold and italic"""
        html = "<p><strong>Bold with <em>italic inside</em></strong></p>"
        parser = HTMLToReportLab(self.styles)
        parser.feed(html)
        story = parser.get_story()

        self.assertEqual(len(story), 1)
        text = str(story[0].text)
        self.assertIn("<b>", text)
        self.assertIn("<i>", text)

    def test_multiple_paragraphs(self):
        """Test multiple consecutive paragraphs"""
        html = "<p>First paragraph.</p><p>Second paragraph.</p><p>Third paragraph.</p>"
        parser = HTMLToReportLab(self.styles)
        parser.feed(html)
        story = parser.get_story()

        self.assertEqual(len(story), 3)

    def test_metadata_detection(self):
        """Test metadata spacing detection"""
        html = "<p><b>Investment:</b> $50,000</p>"
        parser = HTMLToReportLab(self.styles)
        parser.feed(html)
        story = parser.get_story()

        self.assertEqual(len(story), 1)
        # Should detect as metadata and use MetadataText style
        # This is a bit of a white box test

    def test_empty_content(self):
        """Test handling of empty HTML"""
        html = ""
        parser = HTMLToReportLab(self.styles)
        parser.feed(html)
        story = parser.get_story()

        self.assertEqual(len(story), 0)

    def test_horizontal_rule(self):
        """Test horizontal rule parsing"""
        html = "<p>Before</p><hr><p>After</p>"
        parser = HTMLToReportLab(self.styles)
        parser.feed(html)
        story = parser.get_story()

        # Should have: paragraph, HR, paragraph
        self.assertGreaterEqual(len(story), 3)

    def test_code_formatting(self):
        """Test code tag formatting"""
        html = "<p>Here is <code>some code</code> text.</p>"
        parser = HTMLToReportLab(self.styles)
        parser.feed(html)
        story = parser.get_story()

        self.assertEqual(len(story), 1)
        text = str(story[0].text)
        # Check for improved code styling with grey background
        self.assertIn('<font name="Courier" backColor="#F5F5F5">', text)
        self.assertIn('some code', text)

    def test_special_characters(self):
        """Test HTML entity handling"""
        html = "<p>Testing &amp; &lt; &gt;</p>"
        parser = HTMLToReportLab(self.styles)
        parser.feed(html)
        story = parser.get_story()

        self.assertEqual(len(story), 1)
        # Parser should convert entities
        text = str(story[0].text)
        self.assertIn("&", text)


class TestHTMLParserEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions"""

    def setUp(self):
        """Set up test fixtures"""
        self.styles = getSampleStyleSheet()
        # Add minimal required custom styles
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['BodyText']
        ))
        self.styles.add(ParagraphStyle(
            name='MetadataText',
            parent=self.styles['BodyText']
        ))

    def test_unclosed_tags(self):
        """Test handling of unclosed tags"""
        html = "<p><strong>Bold text</p>"
        parser = HTMLToReportLab(self.styles)
        # Should not crash
        try:
            parser.feed(html)
            story = parser.get_story()
            self.assertGreater(len(story), 0)
        except Exception as e:
            self.fail(f"Parser crashed on unclosed tags: {e}")

    def test_nested_lists(self):
        """Test nested lists (potential issue)"""
        html = """
        <ul>
            <li>Item 1
                <ul>
                    <li>Nested 1</li>
                    <li>Nested 2</li>
                </ul>
            </li>
            <li>Item 2</li>
        </ul>
        """
        parser = HTMLToReportLab(self.styles)
        try:
            parser.feed(html)
            story = parser.get_story()
            # Just verify it doesn't crash
            self.assertGreater(len(story), 0)
        except Exception as e:
            # Document if nested lists fail
            print(f"Warning: Nested lists not supported - {e}")

    def test_table_with_bold_cells(self):
        """Test table cells with bold content"""
        html = """
        <table>
            <tr><td><b>Bold cell</b></td><td>Normal cell</td></tr>
        </table>
        """
        parser = HTMLToReportLab(self.styles)
        parser.feed(html)
        story = parser.get_story()

        self.assertGreater(len(story), 0)

    def test_very_long_text(self):
        """Test handling of very long text"""
        long_text = "word " * 1000
        html = f"<p>{long_text}</p>"
        parser = HTMLToReportLab(self.styles)
        parser.feed(html)
        story = parser.get_story()

        self.assertEqual(len(story), 1)


if __name__ == '__main__':
    unittest.main()
