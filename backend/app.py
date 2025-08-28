from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import markdown2
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image, Table, TableStyle
from reportlab.platypus.flowables import PageNumLabel
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT, TA_JUSTIFY
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.platypus import PageTemplate, Frame, BaseDocTemplate
import io
import os
from datetime import datetime
import base64

app = Flask(__name__)
CORS(app)

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []
        self.page_num = 0
        self.total_pages = 0
        self.logo_path = kwargs.get('logo_path')
        self.letterhead = kwargs.get('letterhead')
        self.disclaimer = kwargs.get('disclaimer')

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        self.total_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number()
            self.draw_header()
            self.draw_footer()
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self):
        self.saveState()
        self.setFont("Helvetica", 9)
        self.drawRightString(
            letter[0] - inch * 0.75, 
            inch * 0.75,
            f"Page {self._pageNumber} of {self.total_pages}"
        )
        self.restoreState()

    def draw_header(self):
        self.saveState()
        
        # Letterhead on top left
        if self.letterhead:
            self.setFont("Helvetica-Bold", 12)
            self.drawString(inch * 0.75, letter[1] - inch * 0.75, self.letterhead['company'])
            self.setFont("Helvetica", 9)
            self.drawString(inch * 0.75, letter[1] - inch * 0.95, self.letterhead.get('address', ''))
            self.drawString(inch * 0.75, letter[1] - inch * 1.1, self.letterhead.get('phone', ''))
        
        # Logo on top right (placeholder for now)
        if self.logo_path and os.path.exists(self.logo_path):
            try:
                self.drawImage(
                    self.logo_path,
                    letter[0] - inch * 2.5,
                    letter[1] - inch * 1.25,
                    width=inch * 1.5,
                    height=inch * 0.75,
                    preserveAspectRatio=True,
                    mask='auto'
                )
            except:
                pass
        
        self.restoreState()

    def draw_footer(self):
        self.saveState()
        
        # Disclaimer in bottom center
        if self.disclaimer:
            self.setFont("Helvetica", 8)
            text_width = self.stringWidth(self.disclaimer, "Helvetica", 8)
            self.drawString(
                (letter[0] - text_width) / 2,
                inch * 0.5,
                self.disclaimer
            )
        
        self.restoreState()

def create_pdf(markdown_text, config):
    buffer = io.BytesIO()
    
    # Create custom document template
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=inch * 0.75,
        leftMargin=inch * 0.75,
        topMargin=inch * 1.5,
        bottomMargin=inch * 1.25
    )
    
    # Create custom styles
    styles = getSampleStyleSheet()
    
    # Custom heading styles
    styles.add(ParagraphStyle(
        name='CustomHeading1',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=12,
        fontName='Helvetica-Bold'
    ))
    
    styles.add(ParagraphStyle(
        name='CustomHeading2',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#34495e'),
        spaceAfter=10,
        fontName='Helvetica-Bold'
    ))
    
    styles.add(ParagraphStyle(
        name='CustomHeading3',
        parent=styles['Heading3'],
        fontSize=12,
        textColor=colors.HexColor('#34495e'),
        spaceAfter=8,
        fontName='Helvetica-Bold'
    ))
    
    styles.add(ParagraphStyle(
        name='CustomBody',
        parent=styles['BodyText'],
        fontSize=11,
        alignment=TA_JUSTIFY,
        spaceBefore=6,
        spaceAfter=6
    ))
    
    styles.add(ParagraphStyle(
        name='BulletText',
        parent=styles['BodyText'],
        fontSize=11,
        leftIndent=20,
        bulletIndent=10
    ))
    
    # Convert markdown to HTML
    html = markdown2.markdown(
        markdown_text,
        extras=['fenced-code-blocks', 'tables', 'break-on-newline']
    )
    
    # Parse HTML and create flowables
    story = []
    
    # Simple HTML to ReportLab conversion
    lines = html.split('\n')
    for line in lines:
        if not line.strip():
            story.append(Spacer(1, 6))
        elif line.startswith('<h1>'):
            text = line.replace('<h1>', '').replace('</h1>', '')
            story.append(Paragraph(text, styles['CustomHeading1']))
        elif line.startswith('<h2>'):
            text = line.replace('<h2>', '').replace('</h2>', '')
            story.append(Paragraph(text, styles['CustomHeading2']))
        elif line.startswith('<h3>'):
            text = line.replace('<h3>', '').replace('</h3>', '')
            story.append(Paragraph(text, styles['CustomHeading3']))
        elif line.startswith('<li>'):
            text = line.replace('<li>', '• ').replace('</li>', '')
            story.append(Paragraph(text, styles['BulletText']))
        elif line.startswith('<p>'):
            text = line.replace('<p>', '').replace('</p>', '')
            story.append(Paragraph(text, styles['CustomBody']))
    
    # Build PDF with custom canvas
    doc.build(
        story,
        canvasmaker=lambda *args, **kwargs: NumberedCanvas(
            *args,
            **kwargs,
            logo_path=config.get('logo_path'),
            letterhead=config.get('letterhead'),
            disclaimer=config.get('disclaimer')
        )
    )
    
    buffer.seek(0)
    return buffer

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"})

@app.route('/api/convert', methods=['POST'])
def convert_markdown():
    try:
        data = request.json
        markdown_text = data.get('markdown', '')
        
        # Configuration for the PDF
        config = {
            'letterhead': {
                'company': data.get('company', 'Davinci Corporation'),
                'address': data.get('address', '123 Business St, Suite 100'),
                'phone': data.get('phone', '(555) 123-4567')
            },
            'disclaimer': data.get('disclaimer', 'This document is confidential and proprietary.'),
            'logo_path': None  # Will be handled separately
        }
        
        # Handle logo if provided as base64
        if data.get('logo_base64'):
            logo_data = base64.b64decode(data['logo_base64'])
            logo_path = '/tmp/temp_logo.png'
            with open(logo_path, 'wb') as f:
                f.write(logo_data)
            config['logo_path'] = logo_path
        
        pdf_buffer = create_pdf(markdown_text, config)
        
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'document_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        )
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/preview', methods=['POST'])
def preview():
    try:
        data = request.json
        markdown_text = data.get('markdown', '')
        
        # Convert markdown to HTML for preview
        html = markdown2.markdown(
            markdown_text,
            extras=['fenced-code-blocks', 'tables', 'break-on-newline']
        )
        
        return jsonify({"html": html})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)