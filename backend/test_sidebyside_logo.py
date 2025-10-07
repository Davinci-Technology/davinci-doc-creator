#!/usr/bin/env python3
"""
Test to verify side-by-side logo appears on title page
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from app import create_pdf

test_markdown = """# Davinci AI Solutions Proposal

## Executive Summary

This is a test document to verify that:
- The side-by-side logo appears on the title page
- The regular logo appears in the header
- Both logos render correctly

## Content

Lorem ipsum dolor sit amet, consectetur adipiscing elit.
"""

config = {
    'letterhead': {
        'company': 'Davinci AI Solutions',
        'address': '11-6320 11 Street SE, Calgary, AB T2H 2L7',
        'phone': '+1 (403) 245-9429',
        'email': 'info@davincisolutions.ai'
    },
    'disclaimer': 'Test disclaimer',
    'logo_path': None,  # Use default logos
    'include_title_page': True,
    'include_signature_page': False
}

print("Testing side-by-side logo on title page...")
print("=" * 60)

try:
    pdf_buffer = create_pdf(test_markdown, config)
    output_file = "test_sidebyside_logo.pdf"

    with open(output_file, 'wb') as f:
        f.write(pdf_buffer.read())

    file_size = os.path.getsize(output_file)
    print(f"✅ PDF generated: {output_file} ({file_size} bytes)")
    print(f"\nExpected:")
    print(f"  - Title page with SIDE-BY-SIDE logo (larger, centered)")
    print(f"  - Content pages with REGULAR logo in header (top-right)")
    print(f"\nOpen the PDF to verify both logos are correct!")

except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
