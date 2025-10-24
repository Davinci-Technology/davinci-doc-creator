from flask import Flask, request, jsonify, send_file, session, redirect, url_for
from flask_cors import CORS
import markdown2
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image as RLImage, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT, TA_JUSTIFY
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPDF
from reportlab.platypus.flowables import Flowable
from reportlab.platypus import PageTemplate, Frame, BaseDocTemplate
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import reportlab.rl_config
reportlab.rl_config.warnOnMissingFontGlyphs = 0
import io
import os
from datetime import datetime
import base64
from html.parser import HTMLParser
import re
from PIL import Image as PILImage
import logging
import os
from logging.handlers import RotatingFileHandler

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
CORS(app,
     origins=["*"],  # Allow all origins for local development
     expose_headers=['Content-Disposition'],
     allow_headers=['Content-Type'],
     methods=['GET', 'POST', 'OPTIONS'],
     supports_credentials=True)

# Initialize Azure AD authentication
from auth import AzureADAuth
auth = AzureADAuth(app)

# Check if authentication is required
REQUIRE_AUTH = os.environ.get('REQUIRE_AUTH', 'false').lower() == 'true'

# Test API key for automated testing and health checks
TEST_API_KEY = os.environ.get('TEST_API_KEY', None)

def is_authenticated_request():
    """Check if request is authenticated via API key or Azure AD session"""
    # Check for test API key in header
    if TEST_API_KEY:
        api_key = request.headers.get('X-API-Key')
        if api_key == TEST_API_KEY:
            app.logger.info('Request authenticated with test API key')
            return True

    # Check for Azure AD session
    if REQUIRE_AUTH and 'user' not in session:
        return False

    return True

# Set up application logging to tmp/logs
# Write logs under backend/tmp/logs so they are visible via the bind mount
logs_dir = os.path.join(os.path.dirname(__file__), 'tmp', 'logs')
try:
    os.makedirs(logs_dir, exist_ok=True)
    handler = RotatingFileHandler(os.path.join(logs_dir, 'backend.log'), maxBytes=2_000_000, backupCount=3)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    handler.setFormatter(formatter)
    if not app.logger.handlers:
        app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)
except Exception:
    # Fallback to default logger if filesystem not writable
    pass

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        # Extract custom parameters before passing to Canvas
        self.logo_path = kwargs.pop('logo_path', None)
        self.letterhead = kwargs.pop('letterhead', None)
        self.disclaimer = kwargs.pop('disclaimer', None)
        self.has_title_page = kwargs.pop('has_title_page', False)

        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []
        self.current_page_number = 1
        self.total_pages = 0

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        # Count total pages (raw page count)
        num_pages = len(self._saved_page_states)

        # Calculate total numbered pages (exclude title page if present)
        total_numbered_pages = num_pages - 1 if self.has_title_page else num_pages

        # Draw on each saved page
        for page_index, state in enumerate(self._saved_page_states):
            self.__dict__.update(state)

            # Skip numbering/header/footer for title page
            if self.has_title_page and page_index == 0:
                # Title page - no numbering, header, or footer
                canvas.Canvas.showPage(self)
                continue

            # Calculate page number for content pages
            # If title page exists, first content page is index 1 but numbered as "Page 1"
            if self.has_title_page:
                self.current_page_number = page_index  # index 1 becomes page 1
            else:
                self.current_page_number = page_index + 1  # index 0 becomes page 1

            self.total_pages = total_numbered_pages
            self.draw_page_number()
            self.draw_header()
            self.draw_footer()
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self):
        self.saveState()
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.HexColor('#494949'))  # Davinci Grey
        self.drawRightString(
            letter[0] - inch * 0.75, 
            inch * 0.5,
            f"Page {self.current_page_number} of {self.total_pages}"
        )
        self.restoreState()

    def draw_header(self):
        self.saveState()
        
        # Logo on top right per branding guidelines (horizontal version, size S: 3.5cm x 1.05cm)
        if self.logo_path and os.path.exists(self.logo_path):
            try:
                self.drawImage(
                    self.logo_path,
                    letter[0] - (3.5 * cm) - inch * 0.75,  # Right aligned with margin
                    letter[1] - (1.05 * cm) - inch * 0.5,  # Top aligned with space
                    width=3.5 * cm,  # Size S from branding guidelines
                    height=1.05 * cm,
                    preserveAspectRatio=True,
                    mask='auto'
                )
            except:
                pass
        
        # Letterhead on top left - using Davinci Blue color
        if self.letterhead:
            self.setFont("Helvetica-Bold", 12)
            self.setFillColor(colors.HexColor('#0B98CE'))  # Davinci Blue
            self.drawString(inch * 0.75, letter[1] - inch * 0.75, self.letterhead['company'])
            self.setFont("Helvetica", 9)
            self.setFillColor(colors.HexColor('#494949'))  # Davinci Grey
            self.drawString(inch * 0.75, letter[1] - inch * 0.95, self.letterhead.get('address', ''))
            self.drawString(inch * 0.75, letter[1] - inch * 1.1, self.letterhead.get('phone', ''))
            if self.letterhead.get('email'):
                self.drawString(inch * 0.75, letter[1] - inch * 1.25, self.letterhead.get('email', ''))
        
        self.restoreState()

    def draw_footer(self):
        self.saveState()
        
        # Disclaimer in bottom center
        if self.disclaimer:
            self.setFont("Helvetica", 8)
            self.setFillColor(colors.HexColor('#7A879C'))  # Davinci Stone (light grey for disclaimer)
            text_width = self.stringWidth(self.disclaimer, "Helvetica", 8)
            self.drawString(
                (letter[0] - text_width) / 2,
                inch * 0.3,
                self.disclaimer
            )
        
        self.restoreState()

class HTMLToReportLab(HTMLParser):
    """Convert HTML to ReportLab flowables"""
    def __init__(self, styles):
        super().__init__()
        self.story = []
        self.styles = styles
        self.current_text = []
        self.current_style = 'CustomBody'
        self.in_list = False
        self.list_type = None  # 'ul' or 'ol'
        self.list_counter = 0
        self.in_table = False
        self.table_data = []
        self.table_row = []
        self.in_cell = False
        self.in_bold = False
        self.in_italic = False
        self.in_link = False
        self.link_href = None
        self.in_blockquote = False
        self.last_was_metadata = False  # Track if previous paragraph was metadata
        
    def handle_starttag(self, tag, attrs):
        # Flush any accumulated text before handling new tag (except for inline tags and br)
        if self.current_text and tag not in ['strong', 'em', 'b', 'i', 'code', 'a', 'td', 'th', 'br'] and not self.in_cell:
            self._flush_text()

        if tag == 'h1':
            self.current_style = 'CustomHeading1'
        elif tag == 'h2':
            self.current_style = 'CustomHeading2'
        elif tag == 'h3':
            self.current_style = 'CustomHeading3'
        elif tag == 'p':
            self.current_style = 'CustomBody'
        elif tag == 'ul':
            self.in_list = True
            self.list_type = 'ul'
        elif tag == 'ol':
            self.in_list = True
            self.list_type = 'ol'
            self.list_counter = 0
        elif tag == 'li':
            if self.in_list:
                self.current_style = 'BulletText'
                if self.list_type == 'ol':
                    self.list_counter += 1
                    self.current_text.append(f'{self.list_counter}. ')
                else:
                    self.current_text.append('• ')
        elif tag == 'hr':
            self.story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#CCCCCC'), spaceBefore=16, spaceAfter=4))
        elif tag == 'table':
            self.in_table = True
            self.table_data = []
        elif tag == 'tr' and self.in_table:
            self.table_row = []
        elif tag in ['td', 'th'] and self.in_table:
            self.in_cell = True
            self.current_text = []
        elif tag == 'a':
            # Handle links - extract href and create clickable link
            if not self.in_link:
                self.in_link = True
                # Get href attribute
                href = None
                for attr_name, attr_value in attrs:
                    if attr_name == 'href':
                        href = attr_value
                        break
                if href:
                    self.link_href = href
                    # ReportLab uses <link> tags with href and color
                    self.current_text.append(f'<link href="{href}" color="blue"><u>')
                else:
                    self.in_link = False  # No href, treat as plain text
        elif tag == 'strong' or tag == 'b':
            if not self.in_bold:  # Avoid double nesting
                self.in_bold = True
                self.current_text.append('<b>')
        elif tag == 'em' or tag == 'i':
            if not self.in_italic:  # Avoid double nesting
                self.in_italic = True
                self.current_text.append('<i>')
        elif tag == 'img':
            # Handle images - support both URLs and base64
            src = None
            alt = ''
            width = None
            height = None

            for attr_name, attr_value in attrs:
                if attr_name == 'src':
                    src = attr_value
                elif attr_name == 'alt':
                    alt = attr_value
                elif attr_name == 'width':
                    try:
                        width = float(attr_value)
                    except:
                        pass
                elif attr_name == 'height':
                    try:
                        height = float(attr_value)
                    except:
                        pass

            if src:
                try:
                    # Flush current text before adding image
                    if self.current_text:
                        self._flush_text()

                    # Handle base64 encoded images
                    if src.startswith('data:image'):
                        # Extract base64 data
                        if ',' in src:
                            base64_data = src.split(',', 1)[1]
                            image_data = base64.b64decode(base64_data)
                            img_buffer = io.BytesIO(image_data)
                            img = RLImage(img_buffer, width=width or 4*inch, height=height)
                            self.story.append(img)
                            self.story.append(Spacer(1, 12))
                    else:
                        # Handle URL or file path
                        # For security, we'll skip external URLs in production
                        # but support local file paths
                        if src.startswith(('http://', 'https://')):
                            # Could add URL image support here if needed
                            # For now, add alt text as placeholder
                            if alt:
                                self.story.append(Paragraph(f'[Image: {alt}]', self.styles['CustomBody']))
                        else:
                            # Local file path
                            if os.path.exists(src):
                                img = RLImage(src, width=width or 4*inch, height=height)
                                self.story.append(img)
                                self.story.append(Spacer(1, 12))
                except Exception as e:
                    # If image fails, add alt text
                    if alt:
                        self.story.append(Paragraph(f'[Image: {alt}]', self.styles['CustomBody']))
        elif tag == 'blockquote':
            self.in_blockquote = True
            self.current_style = 'BlockQuote'
        elif tag == 'code':
            # Improved code styling with grey background
            self.current_text.append('<font name="Courier" backColor="#F5F5F5">')
        elif tag == 'br':
            self.current_text.append('<br/>')
            
    def handle_endtag(self, tag):
        if tag in ['h1', 'h2', 'h3', 'p', 'li']:
            self._flush_text()
            self.current_style = 'CustomBody'
        elif tag == 'blockquote':
            self.in_blockquote = False
            self._flush_text()
            self.current_style = 'CustomBody'
        elif tag == 'a':
            if self.in_link:
                self.in_link = False
                self.current_text.append('</u></link>')
                self.link_href = None
        elif tag == 'ul' or tag == 'ol':
            self.in_list = False
        elif tag == 'table' and self.in_table:
            self.in_table = False
            if self.table_data:
                # Clean up table data - convert HTML tags in cells to ReportLab format
                cleaned_data = []
                for row in self.table_data:
                    cleaned_row = []
                    for cell in row:
                        # Process cell content to handle bold tags properly
                        if '<b>' in cell and '</b>' in cell:
                            # Cell has bold content - wrap in Paragraph for proper rendering
                            cleaned_row.append(Paragraph(cell, self.styles['CustomBody']))
                        else:
                            # Plain text cell
                            cleaned_row.append(cell)
                    cleaned_data.append(cleaned_row)
                
                # Create table with styling
                table = Table(cleaned_data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F0F0F0')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#494949')),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#CCCCCC')),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                    ('TOPPADDING', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                    ('LEFTPADDING', (0, 0), (-1, -1), 8),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ]))
                self.story.append(table)
                self.story.append(Spacer(1, 12))
        elif tag == 'tr' and self.in_table:
            if self.table_row:
                self.table_data.append(self.table_row)
                self.table_row = []
        elif tag in ['td', 'th'] and self.in_table:
            # Get cell content, removing nested HTML tags if they weren't handled
            text = ''.join(self.current_text).strip()
            # Clean up any unclosed tags
            text = text.replace('<b></b>', '').replace('<i></i>', '')
            self.table_row.append(text)
            self.current_text = []
            self.in_cell = False
        elif tag == 'strong' or tag == 'b':
            if self.in_bold:
                self.in_bold = False
                self.current_text.append('</b>')
        elif tag == 'em' or tag == 'i':
            if self.in_italic:
                self.in_italic = False
                self.current_text.append('</i>')
        elif tag == 'code':
            self.current_text.append('</font>')
            
    def handle_data(self, data):
        # Always add data if we're in a cell, even whitespace might be important
        if self.in_cell:
            self.current_text.append(data)
        elif self.in_table and not self.in_cell:
            return  # Skip whitespace between table structure tags
        elif data.strip():  # For non-table content, only add non-empty data
            self.current_text.append(data)
        elif self.current_text:  # If we have text accumulated, preserve whitespace
            # This handles the case where we have newlines after <br/> tags
            self.current_text.append(' ')
            
    def _flush_text(self):
        if self.current_text:
            text = ''.join(self.current_text).strip()
            if text:
                # Handle escaped HTML entities
                text = text.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
                
                # Check if this is a metadata line (bold text with colon like "Investment:", "Timeline:")
                is_metadata = False
                style_to_use = self.current_style
                if self.current_style == 'CustomBody' and '<b>' in text and '</b>' in text:
                    # Check if it's one of our key metadata lines
                    clean_text = re.sub(r'<[^>]+>', '', text).lower()
                    if any(keyword in clean_text for keyword in ['investment', 'timeline', 'deliverable', 'from:']):
                        is_metadata = True
                        # If previous was also metadata, use zero spacing
                        if self.last_was_metadata:
                            # Add a tiny spacer between metadata lines
                            self.story.append(Spacer(1, 4))
                
                try:
                    # Use very tight spacing for metadata lines
                    if is_metadata:
                        # Create a custom paragraph with minimal spacing
                        para = Paragraph(text, self.styles['MetadataText'])
                    else:
                        # If transitioning from metadata to normal body content, add extra breathing room
                        if self.last_was_metadata:
                            self.story.append(Spacer(1, 10))
                        para = Paragraph(text, self.styles[style_to_use])
                    self.story.append(para)

                    # Only add extra spacing after bold text with colon if it's NOT metadata
                    # and we didn't already add spacing for a metadata transition
                    if ('<b>' in text and '</b>' in text and ':' in text and
                        not is_metadata and not self.last_was_metadata):
                        self.story.append(Spacer(1, 6))

                    self.last_was_metadata = is_metadata
                except (KeyError, ValueError) as e:
                    # If paragraph style is missing or text formatting fails, add as plain text
                    app.logger.warning(f"Failed to create paragraph with style '{style_to_use}': {e}")
                    clean_text = re.sub(r'<[^>]+>', '', text)
                    self.story.append(Paragraph(clean_text, self.styles.get('CustomBody', self.styles['BodyText'])))
                    self.last_was_metadata = False
                except Exception as e:
                    # Unexpected error - log and use fallback
                    app.logger.error(f"Unexpected error creating paragraph: {e}")
                    clean_text = re.sub(r'<[^>]+>', '', text)
                    self.story.append(Paragraph(clean_text, self.styles.get('CustomBody', self.styles['BodyText'])))
                    self.last_was_metadata = False
        self.current_text = []
        
    def get_story(self):
        # Flush any remaining text
        self._flush_text()
        return self.story

class SVGFlowable(Flowable):
    """Custom flowable to render SVG graphics in ReportLab PDFs"""
    def __init__(self, svg_path, width=None, height=None):
        Flowable.__init__(self)
        self.svg_path = svg_path
        self.drawing = svg2rlg(svg_path)

        if self.drawing:
            # Get original dimensions
            orig_width = self.drawing.width
            orig_height = self.drawing.height
            aspect_ratio = orig_height / orig_width

            # Calculate dimensions
            if width and not height:
                self.width = width
                self.height = width * aspect_ratio
            elif height and not width:
                self.height = height
                self.width = height / aspect_ratio
            elif width and height:
                self.width = width
                self.height = height
            else:
                self.width = orig_width
                self.height = orig_height

            # Scale the drawing
            scale_x = self.width / orig_width
            scale_y = self.height / orig_height
            self.drawing.width = self.width
            self.drawing.height = self.height
            self.drawing.scale(scale_x, scale_y)
        else:
            self.width = 0
            self.height = 0

    def draw(self):
        if self.drawing:
            renderPDF.draw(self.drawing, self.canv, 0, 0)

def create_title_page(config, styles, document_title):
    """Create a professional title page with company logo and document info"""
    story = []

    # Add large vertical spacer to center content
    story.append(Spacer(1, 2.5 * inch))

    # Company logo (centered, larger size) - ALWAYS use side-by-side logo for title page
    # The title page should always use the side-by-side logo, not the header logo
    logo_path = None
    use_svg = False

    # Try to find SVG side-by-side logo first (best quality)
    sidebyside_svg = os.path.join(os.path.dirname(__file__), 'assets', 'logos', 'davinci_logo_sidebyside.svg')
    sidebyside_svg_parent = os.path.join(os.path.dirname(__file__), '..', 'assets', 'logos', 'davinci_logo_sidebyside.svg')
    sidebyside_png = os.path.join(os.path.dirname(__file__), 'assets', 'logos', 'davinci_logo_sidebyside.png')
    sidebyside_png_parent = os.path.join(os.path.dirname(__file__), '..', 'assets', 'logos', 'davinci_logo_sidebyside.png')

    if os.path.exists(sidebyside_svg):
        logo_path = sidebyside_svg
        use_svg = True
    elif os.path.exists(sidebyside_svg_parent):
        logo_path = sidebyside_svg_parent
        use_svg = True
    elif os.path.exists(sidebyside_png):
        logo_path = sidebyside_png
    elif os.path.exists(sidebyside_png_parent):
        logo_path = sidebyside_png_parent

    if logo_path and os.path.exists(logo_path):
        try:
            # Larger size for title page - 12cm wide
            if use_svg or logo_path.endswith('.svg'):
                # Use SVG for perfect quality at any size
                app.logger.info(f"Using SVG logo for title page: {logo_path}")
                logo = SVGFlowable(logo_path, width=12*cm)
                logo.hAlign = 'CENTER'
                story.append(logo)
            else:
                # Fallback to PNG/raster image
                app.logger.info(f"Using PNG logo for title page: {logo_path}")
                # Side-by-side logo ratio is ~3.36:1, so height = 12/3.36 ≈ 3.6cm
                logo = RLImage(logo_path, width=12*cm, height=3.6*cm, kind='proportional')
                logo.hAlign = 'CENTER'
                story.append(logo)
            story.append(Spacer(1, 0.75 * inch))
        except Exception as e:
            app.logger.error(f"Error loading logo for title page: {e}")
            import traceback
            app.logger.error(traceback.format_exc())
            pass

    # Document title - large, centered, bold
    title_style = ParagraphStyle(
        name='TitlePageTitle',
        parent=styles['Heading1'],
        fontSize=28,
        textColor=colors.HexColor('#0B98CE'),
        alignment=TA_CENTER,
        spaceAfter=24,
        fontName='Helvetica-Bold',
        leading=34
    )
    story.append(Paragraph(document_title or 'Document', title_style))

    story.append(Spacer(1, 0.5 * inch))

    # Company name
    company_style = ParagraphStyle(
        name='TitlePageCompany',
        parent=styles['Heading2'],
        fontSize=18,
        textColor=colors.HexColor('#316EA8'),
        alignment=TA_CENTER,
        spaceAfter=12,
        fontName='Helvetica-Bold'
    )
    letterhead = config.get('letterhead', {})
    company_name = letterhead.get('company', 'Davinci AI Solutions')
    story.append(Paragraph(company_name, company_style))

    story.append(Spacer(1, 0.3 * inch))

    # Date
    date_style = ParagraphStyle(
        name='TitlePageDate',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#494949'),
        alignment=TA_CENTER,
        fontName='Helvetica'
    )
    current_date = datetime.now().strftime('%B %d, %Y')
    story.append(Paragraph(current_date, date_style))

    # Force page break after title page
    story.append(PageBreak())

    return story

def create_signature_page(config, styles):
    """Create a signature page with approval context and signature lines"""
    story = []

    # Force new page - signature page should be separate
    story.append(PageBreak())

    # Left-aligned title - feels like a document section heading
    signature_title_style = ParagraphStyle(
        name='SignatureTitle',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#0B98CE'),
        alignment=TA_LEFT,
        spaceAfter=12,
        spaceBefore=0,
        fontName='Helvetica-Bold'
    )
    story.append(Paragraph('Approval & Signatures', signature_title_style))

    # Friendly preamble - clear explanation in plain English
    preamble_style = ParagraphStyle(
        name='SignaturePreamble',
        parent=styles['BodyText'],
        fontSize=11,
        textColor=colors.HexColor('#494949'),
        alignment=TA_LEFT,
        leading=16,
        spaceBefore=8,
        spaceAfter=24,
        fontName='Helvetica'
    )

    preamble_text = (
        "By signing below, you acknowledge that you have reviewed this document "
        "and agree with its contents, recommendations, and proposed course of action. "
        "Your signature confirms your approval to proceed as outlined in this document."
    )

    story.append(Paragraph(preamble_text, preamble_style))

    # Signature table with proper borders - two signature blocks
    # Format: Header row, then fields (Name, Title/Role, Signature, Date)
    signature_data = [
        # Davinci AI Solutions section
        ['Davinci AI Solutions', '', '', ''],
        ['Name:', '', 'Date:', ''],
        ['Title/Role:', '', '', ''],
        ['Signature:', '', '', ''],
        # Spacer row
        ['', '', '', ''],
        # Approved by section
        ['Approved by:', '', '', ''],
        ['Name:', '', 'Date:', ''],
        ['Title/Role:', '', '', ''],
        ['Signature:', '', '', ''],
    ]

    # Create table with 4 columns: label, value, label, value
    signature_table = Table(signature_data, colWidths=[1.2*inch, 2.3*inch, 0.8*inch, 1.7*inch])
    signature_table.setStyle(TableStyle([
        # Font and text settings
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#494949')),

        # Section headers (row 0 and row 5) - bold, larger, span all columns
        ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (0, 0), 12),
        ('SPAN', (0, 0), (-1, 0)),  # Davinci AI Solutions header spans all columns
        ('FONTNAME', (0, 5), (0, 5), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 5), (0, 5), 12),
        ('SPAN', (0, 5), (-1, 5)),  # Approved by header spans all columns

        # Spacer row (row 4) - no borders
        ('SPAN', (0, 4), (-1, 4)),
        ('LINEBELOW', (0, 4), (-1, 4), 0, colors.white),
        ('LINEABOVE', (0, 4), (-1, 4), 0, colors.white),

        # Span Title/Role and Signature rows across full width (no Date column break)
        # Davinci AI Solutions section
        ('SPAN', (1, 2), (3, 2)),  # Title/Role spans from col 1 to 3
        ('SPAN', (1, 3), (3, 3)),  # Signature spans from col 1 to 3
        # Approved by section
        ('SPAN', (1, 7), (3, 7)),  # Title/Role spans from col 1 to 3
        ('SPAN', (1, 8), (3, 8)),  # Signature spans from col 1 to 3

        # Grid borders - light grey
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CCCCCC')),
        ('LINEABOVE', (0, 0), (-1, 0), 1, colors.HexColor('#0B98CE')),  # Blue line above Davinci section
        ('LINEABOVE', (0, 5), (-1, 5), 1, colors.HexColor('#0B98CE')),  # Blue line above Approved section

        # Padding
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),

        # Alignment
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

        # Background color for header rows
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F0F8FF')),  # Light blue for Davinci
        ('BACKGROUND', (0, 5), (-1, 5), colors.HexColor('#F0F8FF')),  # Light blue for Approved
    ]))
    story.append(signature_table)

    return story

def create_pdf(markdown_text, config):
    buffer = io.BytesIO()
    
    # Create custom document template
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=inch * 1.0,   # add breathing room on the sides
        leftMargin=inch * 1.0,
        topMargin=inch * 1.6,     # slightly more top margin
        bottomMargin=inch * 1.3
    )
    
    # Create custom styles
    styles = getSampleStyleSheet()
    
    # Custom heading styles using Davinci brand colors
    styles.add(ParagraphStyle(
        name='CustomHeading1',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#0B98CE'),  # Davinci Blue
        spaceAfter=14,
        spaceBefore=16,
        fontName='Helvetica-Bold'
    ))
    
    styles.add(ParagraphStyle(
        name='CustomHeading2',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#316EA8'),  # Davinci Denim (darker blue)
        spaceAfter=14,
        spaceBefore=10,
        fontName='Helvetica-Bold'
    ))
    
    styles.add(ParagraphStyle(
        name='CustomHeading3',
        parent=styles['Heading3'],
        fontSize=12,
        textColor=colors.HexColor('#494949'),  # Davinci Grey
        spaceAfter=8,
        spaceBefore=10,
        fontName='Helvetica-Bold'
    ))
    
    styles.add(ParagraphStyle(
        name='CustomBody',
        parent=styles['BodyText'],
        fontSize=11,
        textColor=colors.HexColor('#494949'),  # Davinci Grey for body text
        alignment=TA_JUSTIFY,
        leading=15,                # increase line spacing for readability
        spaceBefore=2,
        spaceAfter=6,
        fontName='Helvetica'
    ))
    
    styles.add(ParagraphStyle(
        name='BulletText',
        parent=styles['BodyText'],
        fontSize=11,
        textColor=colors.HexColor('#494949'),  # Davinci Grey
        leftIndent=24,
        bulletIndent=10,
        leading=15,
        spaceBefore=5,
        spaceAfter=4,
        fontName='Helvetica'
    ))
    
    # Add a tight style for metadata lines like Investment, Timeline, Deliverable
    styles.add(ParagraphStyle(
        name='MetadataText',
        parent=styles['BodyText'],
        fontSize=11,
        textColor=colors.HexColor('#494949'),
        leading=13,
        spaceBefore=0,
        spaceAfter=4,              # a touch more room for stacked metadata lines
        fontName='Helvetica'
    ))

    # Add blockquote style
    styles.add(ParagraphStyle(
        name='BlockQuote',
        parent=styles['BodyText'],
        fontSize=11,
        textColor=colors.HexColor('#666666'),
        leftIndent=24,
        rightIndent=24,
        leading=15,
        spaceBefore=12,
        spaceAfter=12,
        fontName='Helvetica-Oblique',
        borderColor=colors.HexColor('#CCCCCC'),
        borderWidth=0,
        borderPadding=8,
        backColor=colors.HexColor('#FAFAFA')
    ))
    
    # Extract document title from first H1 for title page
    document_title = None
    lines = markdown_text.split('\n')
    for line in lines:
        if line.startswith('# '):
            document_title = line[2:].strip()
            break

    # Convert markdown to HTML with all features enabled
    html = markdown2.markdown(
        markdown_text,
        extras=[
            'fenced-code-blocks',
            'tables',
            'break-on-newline',
            'header-ids',
            'strike',
            'task_list'
        ]
    )

    # Use the HTML parser to create ReportLab flowables
    parser = HTMLToReportLab(styles)
    parser.feed(html)
    content_story = parser.get_story()

    # Ensure we have some content
    if not content_story:
        content_story.append(Paragraph("No content to display", styles['CustomBody']))

    # Build complete story with optional title and signature pages
    story = []
    include_title_page = config.get('include_title_page', False)
    include_signature_page = config.get('include_signature_page', False)

    # Add title page if requested
    if include_title_page:
        title_page_story = create_title_page(config, styles, document_title)
        story.extend(title_page_story)

    # Add main content
    story.extend(content_story)

    # Add signature page if requested
    if include_signature_page:
        signature_page_story = create_signature_page(config, styles)
        story.extend(signature_page_story)

    # Build PDF with custom canvas
    doc.build(
        story,
        canvasmaker=lambda *args, **kwargs: NumberedCanvas(
            *args,
            **kwargs,
            logo_path=config.get('logo_path'),
            letterhead=config.get('letterhead'),
            disclaimer=config.get('disclaimer'),
            has_title_page=include_title_page
        )
    )
    
    buffer.seek(0)
    return buffer

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"})

@app.route('/api/convert', methods=['POST'])
def convert_markdown():
    # Check authentication
    if not is_authenticated_request():
        app.logger.warning('Unauthorized convert request')
        return jsonify({"error": "Authentication required"}), 401

    try:
        data = request.json
        markdown_text = data.get('markdown', '')

        # Basic validation (allow large docs, just prevent empty submissions)
        if not isinstance(markdown_text, str) or not markdown_text.strip():
            return jsonify({"error": "'markdown' is required and cannot be empty"}), 400
        
        # Extract document title from first H1 header
        title = 'document'
        lines = markdown_text.split('\n')
        for line in lines:
            if line.startswith('# '):
                # Extract title and clean it for filename
                title = line[2:].strip()
                # Remove special characters and replace spaces with hyphens
                title = ''.join(c if c.isalnum() or c in (' ', '-', '_') else '' for c in title)
                title = title.replace(' ', '-').lower()
                break
        
        # Configuration for the PDF with Davinci AI Solutions defaults
        config = {
            'letterhead': {
                'company': data.get('company', 'Davinci AI Solutions'),
                'address': data.get('address', '11-6320 11 Street SE, Calgary, AB T2H 2L7'),
                'phone': data.get('phone', '+1 (403) 245-9429'),
                'email': data.get('email', 'info@davincisolutions.ai')
            },
            'disclaimer': data.get('disclaimer', 'This document contains confidential and proprietary information of Davinci AI Solutions. © 2025 All Rights Reserved.'),
            'logo_path': None,  # Will be handled separately
            'include_title_page': data.get('includeTitlePage', False),
            'include_signature_page': data.get('includeSignaturePage', False)
        }
        
        # Handle logo - accept both snake_case and camelCase, validate size/type
        logo_b64 = data.get('logo_base64') or data.get('logoBase64')
        if logo_b64:
            try:
                logo_data = base64.b64decode(logo_b64)
            except Exception:
                return jsonify({"error": "Invalid base64 for logo"}), 400

            # Enforce reasonable logo size (5MB) without limiting document content size
            if len(logo_data) > 5 * 1024 * 1024:
                return jsonify({"error": "Logo image exceeds 5MB limit"}), 400

            # Verify it is an image Pillow can open
            try:
                img = PILImage.open(io.BytesIO(logo_data))
                img.verify()  # Validate file integrity
            except Exception as e:
                app.logger.warning(f"Invalid logo upload: {e}")
                return jsonify({"error": f"Uploaded logo is not a valid image: {str(e)}"}), 400

            logo_path = '/tmp/temp_logo.png'
            with open(logo_path, 'wb') as f:
                f.write(logo_data)
            config['logo_path'] = logo_path
        else:
            # Use default Davinci logo if it exists (prefer PNG for ReportLab compatibility)
            # Try both locations - in container and in development
            default_logo_png = os.path.join(os.path.dirname(__file__), 'assets', 'logos', 'davinci_logo.png')
            default_logo_png_parent = os.path.join(os.path.dirname(__file__), '..', 'assets', 'logos', 'davinci_logo.png')

            if os.path.exists(default_logo_png):
                config['logo_path'] = default_logo_png
            elif os.path.exists(default_logo_png_parent):
                config['logo_path'] = default_logo_png_parent
        
        app.logger.info('Starting conversion request')
        pdf_buffer = create_pdf(markdown_text, config)
        size_bytes = pdf_buffer.getbuffer().nbytes
        app.logger.info('Conversion success: title=%s size_bytes=%d', title, size_bytes)
        
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'{title}-{datetime.now().strftime("%Y-%m-%d-%H%M%S")}.pdf'
        )
    
    except ValueError as e:
        app.logger.error('Invalid input: %s', str(e))
        return jsonify({"error": f"Invalid input: {str(e)}"}), 400
    except IOError as e:
        app.logger.error('File I/O error: %s', str(e))
        return jsonify({"error": f"File error: {str(e)}"}), 500
    except Exception as e:
        app.logger.exception('PDF conversion failed: %s', str(e))
        return jsonify({"error": f"PDF generation failed: {str(e)}"}), 500

# Removed unused /api/preview endpoint. Frontend does client-side preview.

# Authentication routes
@app.route('/api/auth/login')
def login():
    """Redirect to Azure AD login"""
    if not REQUIRE_AUTH:
        # If auth is disabled, mock a successful login
        session['user'] = {
            'name': 'Test User',
            'email': 'test@davincisolutions.ai',
            'sub': 'test-user-id'
        }
        return redirect('/')

    auth_url = auth.get_auth_url()
    if auth_url:
        return redirect(auth_url)
    return jsonify({'error': 'Authentication not configured'}), 500

@app.route('/api/auth/callback')
def auth_callback():
    """Handle Azure AD callback"""
    if not REQUIRE_AUTH:
        # Mock successful auth for testing
        session['user'] = {
            'name': 'Test User',
            'email': 'test@davincisolutions.ai',
            'sub': 'test-user-id'
        }
        return redirect('/')

    code = request.args.get('code')
    if not code:
        return jsonify({'error': 'No authorization code received'}), 400

    token_result = auth.acquire_token_by_code(code)
    if 'error' in token_result:
        return jsonify({'error': token_result['error_description']}), 400

    # Store user info in session
    session['user'] = token_result.get('id_token_claims', {})

    # Redirect to frontend
    return redirect('/')

@app.route('/api/auth/user')
def get_user():
    """Get current user info"""
    if not REQUIRE_AUTH:
        # Return mock user for testing
        return jsonify({
            'name': 'Test User',
            'email': 'test@davincisolutions.ai',
            'authenticated': True
        })

    user = session.get('user')
    if user:
        return jsonify({
            'name': user.get('name', ''),
            'email': user.get('preferred_username', user.get('email', '')),
            'authenticated': True
        })
    return jsonify({'authenticated': False})

@app.route('/api/auth/logout')
def logout():
    """Logout user"""
    session.clear()

    if not REQUIRE_AUTH:
        return redirect('/')

    # Redirect to Azure AD logout
    logout_url = f"https://login.microsoftonline.com/{auth.tenant_id}/oauth2/v2.0/logout"
    return redirect(logout_url)

if __name__ == '__main__':
    app.run(debug=True, port=5001, host='0.0.0.0')
