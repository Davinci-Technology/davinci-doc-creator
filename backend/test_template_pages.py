#!/usr/bin/env python3
"""
Quick test to verify title page and signature page functionality
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from app import create_pdf

# Test markdown content
test_markdown = """# Test Document Title

## Introduction

This is a test document to verify that the title page and signature page features work correctly.

### Key Points

- Title page should appear before this content
- Title page should NOT have a page number
- This content should start with "Page 1 of X"
- Signature page should appear after this content
- Signature page SHOULD have a page number

## Section 2

More content here to make the document multi-page.

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.

### Subsection

Even more content to ensure we have multiple pages.

- Bullet point one
- Bullet point two
- Bullet point three

## Conclusion

This concludes the test document.
"""

# Test configurations
configs = [
    {
        'name': 'no_template_pages',
        'config': {
            'letterhead': {
                'company': 'Test Company',
                'address': '123 Test St',
                'phone': '555-1234',
                'email': 'test@test.com'
            },
            'disclaimer': 'Test disclaimer',
            'logo_path': None,
            'include_title_page': False,
            'include_signature_page': False
        }
    },
    {
        'name': 'with_title_page',
        'config': {
            'letterhead': {
                'company': 'Test Company',
                'address': '123 Test St',
                'phone': '555-1234',
                'email': 'test@test.com'
            },
            'disclaimer': 'Test disclaimer',
            'logo_path': None,
            'include_title_page': True,
            'include_signature_page': False
        }
    },
    {
        'name': 'with_signature_page',
        'config': {
            'letterhead': {
                'company': 'Test Company',
                'address': '123 Test St',
                'phone': '555-1234',
                'email': 'test@test.com'
            },
            'disclaimer': 'Test disclaimer',
            'logo_path': None,
            'include_title_page': False,
            'include_signature_page': True
        }
    },
    {
        'name': 'with_both_pages',
        'config': {
            'letterhead': {
                'company': 'Test Company',
                'address': '123 Test St',
                'phone': '555-1234',
                'email': 'test@test.com'
            },
            'disclaimer': 'Test disclaimer',
            'logo_path': None,
            'include_title_page': True,
            'include_signature_page': True
        }
    }
]

print("Testing template page functionality...")
print("=" * 60)

for test in configs:
    print(f"\nTest: {test['name']}")
    print(f"  Title page: {test['config']['include_title_page']}")
    print(f"  Signature page: {test['config']['include_signature_page']}")

    try:
        pdf_buffer = create_pdf(test_markdown, test['config'])
        output_file = f"test_{test['name']}.pdf"

        with open(output_file, 'wb') as f:
            f.write(pdf_buffer.read())

        file_size = os.path.getsize(output_file)
        print(f"  ✅ PDF generated: {output_file} ({file_size} bytes)")

    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 60)
print("Test complete! Check the generated PDFs:")
print("  - test_no_template_pages.pdf (baseline)")
print("  - test_with_title_page.pdf (should have title page, no numbers on page 1)")
print("  - test_with_signature_page.pdf (should have signature page at end)")
print("  - test_with_both_pages.pdf (should have both)")
