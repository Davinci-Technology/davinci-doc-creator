from flask import Flask, request, jsonify, send_file, session, redirect, url_for
from flask_cors import CORS
import markdown2
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image as RLImage, Table, TableStyle, HRFlowable, Preformatted
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
import tempfile
from datetime import datetime
import base64
from html.parser import HTMLParser
import re
from PIL import Image as PILImage
import logging
import os
from logging.handlers import RotatingFileHandler
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from docusign_client import DocuSignClient

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

# Initialize rate limiter for API endpoints
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Initialize DocuSign client
docusign_client = DocuSignClient()

# Register NotoSans fonts for Unicode support
try:
    font_dir = os.path.join(os.path.dirname(__file__), 'assets', 'fonts')
    pdfmetrics.registerFont(TTFont('NotoSans', os.path.join(font_dir, 'NotoSans-Regular.ttf')))
    pdfmetrics.registerFont(TTFont('NotoSans-Bold', os.path.join(font_dir, 'NotoSans-Bold.ttf')))
    # Register italic variants if available, or just map to regular for now to prevent crashes
    # Ideally we would download Italic too, but Regular/Bold covers 99% of use cases
except Exception as e:
    logging.warning(f"Failed to load NotoSans fonts: {e}. Fallback to Helvetica.")
    # Fallback map if load fails (though we downloaded them)
    pass

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
        self.setFont("NotoSans", 9)
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
            self.setFont("NotoSans-Bold", 12)
            self.setFillColor(colors.HexColor('#0B98CE'))  # Davinci Blue
            self.drawString(inch * 0.75, letter[1] - inch * 0.75, self.letterhead['company'])
            self.setFont("NotoSans", 9)
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
            self.setFont("NotoSans", 8)
            self.setFillColor(colors.HexColor('#7A879C'))  # Davinci Stone (light grey for disclaimer)
            text_width = self.stringWidth(self.disclaimer, "NotoSans", 8)
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
        self.list_depth = 0
        self.list_type_stack = [] # Stack to track 'ul' or 'ol'
        self.list_counters = []   # Stack to track counters for 'ol'
        
        self.in_table = False
        self.table_data = []
        self.table_row = []
        self.in_cell = False
        
        self.in_pre = False
        
        self.in_bold = False
        self.in_italic = False
        self.in_link = False
        self.link_href = None
        self.in_blockquote = False
        self.last_was_metadata = False
        
    def handle_starttag(self, tag, attrs):
        # Flush any accumulated text before handling new tag
        if self.current_text and tag not in ['strong', 'em', 'b', 'i', 'code', 'a', 'td', 'th', 'br'] and not self.in_cell and not self.in_pre:
            self._flush_text()

        if tag == 'h1':
            self.current_style = 'CustomHeading1'
        elif tag == 'h2':
            self.current_style = 'CustomHeading2'
        elif tag == 'h3':
            self.current_style = 'CustomHeading3'
        elif tag == 'p':
            if not self.in_table: # Don't reset style inside tables
                self.current_style = 'CustomBody'
        elif tag == 'ul':
            self.list_depth += 1
            self.list_type_stack.append('ul')
            self.list_counters.append(0)
        elif tag == 'ol':
            self.list_depth += 1
            self.list_type_stack.append('ol')
            self.list_counters.append(0)
        elif tag == 'li':
            # Determine list type and increment counter if needed
            if self.list_type_stack:
                list_type = self.list_type_stack[-1]
                if list_type == 'ol':
                    self.list_counters[-1] += 1
                    number = f"{self.list_counters[-1]}."
                    self.current_text.append(f'{number} ')
                else:
                    self.current_text.append('• ')
            else:
                self.current_text.append('• ') # Fallback
            
            # Set style to BulletText but we'll manually adjust indent in _flush_text or by creating a custom style on the fly
            self.current_style = 'BulletText'
            
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
            if not self.in_link:
                self.in_link = True
                href = None
                for attr_name, attr_value in attrs:
                    if attr_name == 'href':
                        href = attr_value
                        break
                if href:
                    self.link_href = href
                    self.current_text.append(f'<link href="{href}" color="blue"><u>')
        elif tag in ['strong', 'b']:
            if not self.in_bold:
                self.in_bold = True
                self.current_text.append('<b>')
        elif tag in ['em', 'i']:
            if not self.in_italic:
                self.in_italic = True
                self.current_text.append('<i>')
        elif tag == 'pre':
            self.in_pre = True
            self._flush_text() # Ensure previous text is saved
        elif tag == 'code':
            if not self.in_pre:
                # Inline code
                self.current_text.append('<font name="Courier" backColor="#F5F5F5">')
        elif tag == 'br':
            self.current_text.append('<br/>')
        elif tag == 'blockquote':
            self.in_blockquote = True
            self.current_style = 'BlockQuote'
            
        # Image handling (same as before)
        elif tag == 'img':
            src = None
            alt = ''
            width = None
            height = None
            for attr_name, attr_value in attrs:
                if attr_name == 'src': src = attr_value
                elif attr_name == 'alt': alt = attr_value
                elif attr_name == 'width':
                    try: width = float(attr_value)
                    except: pass
                elif attr_name == 'height':
                    try: height = float(attr_value)
                    except: pass
            
            if src:
                if self.current_text: self._flush_text()
                try:
                    if src.startswith('data:image'):
                        if ',' in src:
                            base64_data = src.split(',', 1)[1]
                            image_data = base64.b64decode(base64_data)
                            img_buffer = io.BytesIO(image_data)
                            img = RLImage(img_buffer, width=width or 4*inch, height=height)
                            self.story.append(img)
                            self.story.append(Spacer(1, 12))
                    elif os.path.exists(src):
                        img = RLImage(src, width=width or 4*inch, height=height)
                        self.story.append(img)
                        self.story.append(Spacer(1, 12))
                except Exception:
                     if alt: self.story.append(Paragraph(f'[Image: {alt}]', self.styles['CustomBody']))

    def handle_endtag(self, tag):
        if tag in ['h1', 'h2', 'h3', 'p']:
            self._flush_text()
            self.current_style = 'CustomBody'
        elif tag == 'li':
            self._flush_text()
            # Don't reset style yet, might be in nested list
        elif tag == 'blockquote':
            self._flush_text()
            self.in_blockquote = False
            self.current_style = 'CustomBody'
        elif tag == 'a':
            if self.in_link:
                self.in_link = False
                self.current_text.append('</u></link>')
        elif tag == 'ul' or tag == 'ol':
            if self.list_depth > 0:
                self.list_depth -= 1
                if self.list_type_stack: self.list_type_stack.pop()
                if self.list_counters: self.list_counters.pop()
        elif tag == 'table':
            self.in_table = False
            if self.table_data:
                self._process_table()
        elif tag == 'tr':
            if self.table_row:
                self.table_data.append(self.table_row)
                self.table_row = []
        elif tag in ['td', 'th']:
            text = ''.join(self.current_text).strip()
            # Remove empty formatting tags
            text = text.replace('<b></b>', '').replace('<i></i>', '')
            self.table_row.append(text)
            self.current_text = []
            self.in_cell = False
        elif tag in ['strong', 'b']:
            if self.in_bold:
                self.in_bold = False
                self.current_text.append('</b>')
        elif tag in ['em', 'i']:
            if self.in_italic:
                self.in_italic = False
                self.current_text.append('</i>')
        elif tag == 'pre':
            self.in_pre = False
            text = ''.join(self.current_text) # Preserve whitespace
            self.current_text = []
            if text.strip():
                # Create a Preformatted flowable for code blocks
                style = self.styles['CodeBlock']
                self.story.append(Preformatted(text, style))
                self.story.append(Spacer(1, 12))
        elif tag == 'code':
            if not self.in_pre:
                self.current_text.append('</font>')

    def handle_data(self, data):
        if self.in_pre:
            self.current_text.append(data) # Preserve exact characters including newlines
        elif self.in_cell:
            self.current_text.append(data)
        elif self.in_table:
            pass # Skip whitespace between tr/td
        elif data.strip() or self.current_text: # Add if content or if we already have content (space)
             # Collapse whitespace for normal text
             if not self.in_pre:
                 self.current_text.append(data)

    def _process_table(self):
        # Robust table creation using Paragraphs for all cells
        cell_style = ParagraphStyle(
            'TableCell',
            parent=self.styles['CustomBody'],
            fontSize=9,
            leading=11,
            fontName='NotoSans'
        )
        
        # Convert all data to Paragraphs
        cleaned_data = []
        for row in self.table_data:
            cleaned_row = []
            for cell_text in row:
                if not cell_text: cell_text = ""
                cleaned_row.append(Paragraph(cell_text, cell_style))
            cleaned_data.append(cleaned_row)
            
        if not cleaned_data: return

        # Calculate widths - distributed evenly for robustness
        num_cols = len(cleaned_data[0])
        avail_width = 6.5 * inch
        col_widths = [avail_width / num_cols] * num_cols
        
        table = Table(cleaned_data, colWidths=col_widths)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F0F0F0')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#CCCCCC')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        self.story.append(table)
        self.story.append(Spacer(1, 12))

    def _flush_text(self):
        if self.current_text:
            text = ''.join(self.current_text).strip()
            if text:
                # Auto-close open tags to prevent ReportLab crashes
                if self.in_bold: text += '</b>'
                if self.in_italic: text += '</i>'
                if self.in_link: text += '</u></link>'
                
                text = text.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
                
                # Dynamic indentation for nested lists
                style = self.styles[self.current_style]
                
                if self.current_style == 'BulletText':
                    # Create a temp style with correct indentation
                    # Base indent 24, plus 12 for each extra level
                    indent = 24 + (max(0, self.list_depth - 1) * 12)
                    style = ParagraphStyle(
                        f'BulletLevel{self.list_depth}',
                        parent=self.styles['BulletText'],
                        leftIndent=indent,
                        firstLineIndent=0
                    )
                
                try:
                    self.story.append(Paragraph(text, style))
                except:
                    # Fallback
                    self.story.append(Paragraph(text, self.styles['CustomBody']))
        
        # Reset open tag state since we've flushed the paragraph
        self.in_bold = False
        self.in_italic = False
        self.in_link = False
        self.current_text = []
        
    def get_story(self):
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

    # Company logo handling (unchanged)
    logo_path = None
    use_svg = False

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
            if use_svg or logo_path.endswith('.svg'):
                logo = SVGFlowable(logo_path, width=12*cm)
                logo.hAlign = 'CENTER'
                story.append(logo)
            else:
                logo = RLImage(logo_path, width=12*cm, height=3.6*cm, kind='proportional')
                logo.hAlign = 'CENTER'
                story.append(logo)
            story.append(Spacer(1, 0.75 * inch))
        except Exception:
            pass

    title_style = ParagraphStyle(
        name='TitlePageTitle',
        parent=styles['Heading1'],
        fontSize=28,
        textColor=colors.HexColor('#0B98CE'),
        alignment=TA_CENTER,
        spaceAfter=24,
        fontName='NotoSans-Bold',
        leading=34
    )
    story.append(Paragraph(document_title or 'Document', title_style))

    story.append(Spacer(1, 0.5 * inch))

    company_style = ParagraphStyle(
        name='TitlePageCompany',
        parent=styles['Heading2'],
        fontSize=18,
        textColor=colors.HexColor('#316EA8'),
        alignment=TA_CENTER,
        spaceAfter=12,
        fontName='NotoSans-Bold'
    )
    letterhead = config.get('letterhead', {})
    company_name = letterhead.get('company', 'Davinci AI Solutions')
    story.append(Paragraph(company_name, company_style))

    story.append(Spacer(1, 0.3 * inch))

    date_style = ParagraphStyle(
        name='TitlePageDate',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#494949'),
        alignment=TA_CENTER,
        fontName='NotoSans'
    )
    current_date = datetime.now().strftime('%B %d, %Y')
    story.append(Paragraph(current_date, date_style))

    story.append(PageBreak())

    return story

def create_signature_page(config, styles):
    story = []
    story.append(PageBreak())

    signature_title_style = ParagraphStyle(
        name='SignatureTitle',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#0B98CE'),
        alignment=TA_LEFT,
        spaceAfter=12,
        spaceBefore=0,
        fontName='NotoSans-Bold'
    )
    story.append(Paragraph('Approval & Signatures', signature_title_style))

    preamble_style = ParagraphStyle(
        name='SignaturePreamble',
        parent=styles['BodyText'],
        fontSize=11,
        textColor=colors.HexColor('#494949'),
        alignment=TA_LEFT,
        leading=16,
        spaceBefore=8,
        spaceAfter=24,
        fontName='NotoSans'
    )

    preamble_text = (
        "By signing below, you acknowledge that you have reviewed this document "
        "and agree with its contents, recommendations, and proposed course of action. "
        "Your signature confirms your approval to proceed as outlined in this document."
    )

    story.append(Paragraph(preamble_text, preamble_style))

    anchor_style = ParagraphStyle(
        name='Anchor',
        parent=styles['BodyText'],
        fontSize=1,
        textColor=colors.white,
        fontName='NotoSans'
    )

    signature_data = [
        ['Davinci AI Solutions', '', '', ''],
        ['Name:', Paragraph('/ds_davinci_name/', anchor_style), 'Date:', Paragraph('/ds_davinci_date/', anchor_style)],
        ['Title/Role:', Paragraph('/ds_davinci_title/', anchor_style), '', ''],
        ['Signature:', Paragraph('/ds_davinci_signature/', anchor_style), '', ''],
        ['', '', '', ''],
        ['Approved by:', '', '', ''],
        ['Name:', Paragraph('/ds_recipient_name/', anchor_style), 'Date:', Paragraph('/ds_recipient_date/', anchor_style)],
        ['Title/Role:', Paragraph('/ds_recipient_title/', anchor_style), '', ''],
        ['Signature:', Paragraph('/ds_recipient_signature/', anchor_style), '', '']
    ]

    signature_table = Table(signature_data, colWidths=[1.2*inch, 2.3*inch, 0.8*inch, 1.7*inch])
    signature_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'NotoSans'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#494949')),
        ('FONTNAME', (0, 0), (0, 0), 'NotoSans-Bold'),
        ('FONTSIZE', (0, 0), (0, 0), 12),
        ('SPAN', (0, 0), (-1, 0)),
        ('FONTNAME', (0, 5), (0, 5), 'NotoSans-Bold'),
        ('FONTSIZE', (0, 5), (0, 5), 12),
        ('SPAN', (0, 5), (-1, 5)),
        ('SPAN', (0, 4), (-1, 4)),
        ('LINEBELOW', (0, 4), (-1, 4), 0, colors.white),
        ('LINEABOVE', (0, 4), (-1, 4), 0, colors.white),
        ('SPAN', (1, 2), (3, 2)),
        ('SPAN', (1, 3), (3, 3)),
        ('SPAN', (1, 7), (3, 7)),
        ('SPAN', (1, 8), (3, 8)),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CCCCCC')),
        ('LINEABOVE', (0, 0), (-1, 0), 1, colors.HexColor('#0B98CE')),
        ('LINEABOVE', (0, 5), (-1, 5), 1, colors.HexColor('#0B98CE')),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F0F8FF')),
        ('BACKGROUND', (0, 5), (-1, 5), colors.HexColor('#F0F8FF')),
    ]))
    story.append(signature_table)

    return story

def create_pdf(markdown_text, config):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=inch * 1.0,
        leftMargin=inch * 1.0,
        topMargin=inch * 1.6,
        bottomMargin=inch * 1.3
    )
    
    styles = getSampleStyleSheet()
    
    styles.add(ParagraphStyle(
        name='CustomHeading1',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#0B98CE'),
        spaceAfter=14,
        spaceBefore=16,
        fontName='NotoSans-Bold'
    ))
    
    styles.add(ParagraphStyle(
        name='CustomHeading2',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#316EA8'),
        spaceAfter=14,
        spaceBefore=10,
        fontName='NotoSans-Bold'
    ))
    
    styles.add(ParagraphStyle(
        name='CustomHeading3',
        parent=styles['Heading3'],
        fontSize=12,
        textColor=colors.HexColor('#494949'),
        spaceAfter=8,
        spaceBefore=10,
        fontName='NotoSans-Bold'
    ))
    
    styles.add(ParagraphStyle(
        name='CustomBody',
        parent=styles['BodyText'],
        fontSize=11,
        textColor=colors.HexColor('#494949'),
        alignment=TA_JUSTIFY,
        leading=15,
        spaceBefore=2,
        spaceAfter=6,
        fontName='NotoSans'
    ))
    
    styles.add(ParagraphStyle(
        name='BulletText',
        parent=styles['BodyText'],
        fontSize=11,
        textColor=colors.HexColor('#494949'),
        leftIndent=24,
        bulletIndent=10,
        leading=15,
        spaceBefore=5,
        spaceAfter=4,
        fontName='NotoSans'
    ))
    
    styles.add(ParagraphStyle(
        name='MetadataText',
        parent=styles['BodyText'],
        fontSize=11,
        textColor=colors.HexColor('#494949'),
        leading=13,
        spaceBefore=0,
        spaceAfter=4,
        fontName='NotoSans'
    ))

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
        fontName='NotoSans', # Regular, but could be Italic if we had it
        borderColor=colors.HexColor('#CCCCCC'),
        borderWidth=0,
        borderPadding=8,
        backColor=colors.HexColor('#FAFAFA')
    ))

    # New style for Code Blocks
    styles.add(ParagraphStyle(
        name='CodeBlock',
        parent=styles['BodyText'],
        fontSize=9,
        textColor=colors.HexColor('#333333'),
        fontName='Courier',
        leading=11,
        leftIndent=12,
        rightIndent=12,
        spaceBefore=12,
        spaceAfter=12,
        backColor=colors.HexColor('#F5F5F5'),
        borderPadding=8,
    ))
    
    # Preprocessing (No more regex for lists!)
    lines = markdown_text.split('\n')
    processed_lines = []
    in_table = False

    for i, line in enumerate(lines):
        stripped = line.strip()
        is_table_line = stripped.startswith('|') and '|' in stripped[1:]
        is_table_separator = is_table_line and '-' in stripped

        if is_table_line:
            if not in_table and len(processed_lines) > 0:
                if processed_lines[-1].strip():
                    processed_lines.append('')
            in_table = True
        elif in_table and not is_table_line:
            in_table = False

        if (len(stripped) >= 3 and all(c in '=-_■' for c in stripped) and not is_table_separator):
            processed_lines.append('---')
        else:
            processed_lines.append(line)

    markdown_text = '\n'.join(processed_lines)

    document_title = None
    for line in lines:
        if line.startswith('# '):
            document_title = line[2:].strip()
            break

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

    # Removed dangerous regex post-processing

    parser = HTMLToReportLab(styles)
    parser.feed(html)
    content_story = parser.get_story()

    if not content_story:
        content_story.append(Paragraph("No content to display", styles['CustomBody']))

    story = []
    include_title_page = config.get('include_title_page', False)
    include_signature_page = config.get('include_signature_page', False)

    if include_title_page:
        story.extend(create_title_page(config, styles, document_title))

    story.extend(content_story)

    if include_signature_page:
        story.extend(create_signature_page(config, styles))

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

@app.route('/api/convert', methods=['POST'])
def convert_markdown():
    # Check authentication
    if not is_authenticated_request():
        app.logger.warning('Unauthorized convert request')
        return jsonify({"error": "Authentication required"}), 401

    temp_logo_file = None
    try:
        data = request.json
        markdown_text = data.get('markdown', '')

        if not isinstance(markdown_text, str) or not markdown_text.strip():
            return jsonify({"error": "'markdown' is required and cannot be empty"}), 400
        
        title = 'document'
        lines = markdown_text.split('\n')
        for line in lines:
            if line.startswith('# '):
                title = line[2:].strip()
                title = ''.join(c if c.isalnum() or c in (' ', '-', '_') else '' for c in title)
                title = title.replace(' ', '-').lower()
                break
        
        config = {
            'letterhead': {
                'company': data.get('company', 'Davinci AI Solutions'),
                'address': data.get('address', '11-6320 11 Street SE, Calgary, AB T2H 2L7'),
                'phone': data.get('phone', '+1 (403) 245-9429'),
                'email': data.get('email', 'info@davincisolutions.ai')
            },
            'disclaimer': data.get('disclaimer', 'This document contains confidential and proprietary information of Davinci AI Solutions. © 2025 All Rights Reserved.'),
            'logo_path': None,
            'include_title_page': data.get('includeTitlePage', False),
            'include_signature_page': data.get('includeSignaturePage', False)
        }
        
        logo_b64 = data.get('logo_base64') or data.get('logoBase64')
        if logo_b64:
            try:
                logo_data = base64.b64decode(logo_b64)
            except Exception:
                return jsonify({"error": "Invalid base64 for logo"}), 400

            if len(logo_data) > 5 * 1024 * 1024:
                return jsonify({"error": "Logo image exceeds 5MB limit"}), 400

            try:
                img = PILImage.open(io.BytesIO(logo_data))
                img.verify()
            except Exception as e:
                app.logger.warning(f"Invalid logo upload: {e}")
                return jsonify({"error": f"Uploaded logo is not a valid image: {str(e)}"}), 400

            temp_logo_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
            temp_logo_file.write(logo_data)
            temp_logo_file.close()
            config['logo_path'] = temp_logo_file.name
        else:
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
    finally:
        if temp_logo_file and os.path.exists(temp_logo_file.name):
            try:
                os.unlink(temp_logo_file.name)
            except Exception as e:
                app.logger.warning(f"Failed to delete temp logo file: {e}")

@app.route('/api/docusign/send-for-signature', methods=['POST'])
@limiter.limit("10 per hour")
def send_for_signature():
    if not is_authenticated_request():
        app.logger.warning('Unauthorized DocuSign send request')
        return jsonify({"error": "Authentication required"}), 401

    temp_logo_file = None
    try:
        data = request.json

        markdown_text = data.get('markdown', '')
        recipient_name = data.get('recipient_name', '').strip()
        recipient_email = data.get('recipient_email', '').strip()

        if not markdown_text.strip(): return jsonify({"error": "markdown is required"}), 400
        if not recipient_name: return jsonify({"error": "recipient_name is required"}), 400
        if not recipient_email: return jsonify({"error": "recipient_email is required"}), 400

        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, recipient_email):
            return jsonify({"error": "Invalid recipient_email format"}), 400

        document_name = data.get('document_name', 'Document')
        if not document_name or document_name == 'Document':
            lines = markdown_text.split('\n')
            for line in lines:
                if line.startswith('# '):
                    document_name = line[2:].strip()
                    break

        config = {
            'letterhead': {
                'company': data.get('company', 'Davinci AI Solutions'),
                'address': data.get('address', '11-6320 11 Street SE, Calgary, AB T2H 2L7'),
                'phone': data.get('phone', '+1 (403) 245-9429'),
                'email': data.get('email', 'info@davincisolutions.ai')
            },
            'disclaimer': data.get('disclaimer', 'This document contains confidential and proprietary information of Davinci AI Solutions. © 2025 All Rights Reserved.'),
            'logo_path': None,
            'include_title_page': data.get('includeTitlePage', False),
            'include_signature_page': data.get('includeSignaturePage', True)
        }

        logo_b64 = data.get('logo_base64') or data.get('logoBase64')
        if logo_b64:
            try:
                logo_data = base64.b64decode(logo_b64)
                if len(logo_data) > 5 * 1024 * 1024:
                    return jsonify({"error": "Logo image exceeds 5MB limit"}), 400

                img = PILImage.open(io.BytesIO(logo_data))
                img.verify()

                temp_logo_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
                temp_logo_file.write(logo_data)
                temp_logo_file.close()
                config['logo_path'] = temp_logo_file.name
            except Exception as e:
                app.logger.warning(f"Invalid logo upload for DocuSign: {e}")
                return jsonify({"error": f"Invalid logo: {str(e)}"}), 400
        else:
            default_logo_png = os.path.join(os.path.dirname(__file__), 'assets', 'logos', 'davinci_logo.png')
            default_logo_png_parent = os.path.join(os.path.dirname(__file__), '..', 'assets', 'logos', 'davinci_logo.png')
            if os.path.exists(default_logo_png):
                config['logo_path'] = default_logo_png
            elif os.path.exists(default_logo_png_parent):
                config['logo_path'] = default_logo_png_parent

        app.logger.info(f'Generating PDF for DocuSign: {document_name}')
        pdf_buffer = create_pdf(markdown_text, config)

        app.logger.info(f'Sending to DocuSign: recipient={recipient_email}')
        result = docusign_client.send_envelope_for_signature(
            pdf_buffer=pdf_buffer,
            recipient_name=recipient_name,
            recipient_email=recipient_email,
            document_name=document_name,
            email_subject=data.get('email_subject'),
            email_message=data.get('email_message', '')
        )

        app.logger.info(f'DocuSign envelope created: {result["envelope_id"]}')

        return jsonify({
            'success': True,
            'envelope_id': result['envelope_id'],
            'status': result['status'],
            'recipient': result['recipient'],
            'counter_signer': result['counter_signer'],
            'message': 'Document sent for signature successfully'
        }), 200

    except ValueError as e:
        app.logger.error(f'DocuSign validation error: {e}')
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        app.logger.exception(f'DocuSign send failed: {e}')
        return jsonify({"error": f"Failed to send document for signature: {str(e)}"}), 500
    finally:
        if temp_logo_file and os.path.exists(temp_logo_file.name):
            try:
                os.unlink(temp_logo_file.name)
            except Exception as e:
                app.logger.warning(f"Failed to delete temp logo file: {e}")

# ... rest of docusign routes (get status, webhook) are unchanged