"""
Test fixtures - real-world markdown documents for testing
"""

# Simple document
SIMPLE_DOC = """# Test Document

This is a simple test document.

## Section 1

Here is some body text.
"""

# Document with lists
LISTS_DOC = """# Document with Lists

## Unordered List

- First item
- Second item
- Third item

## Ordered List

1. First step
2. Second step
3. Third step
"""

# Document with formatting
FORMATTING_DOC = """# Document with Formatting

This document has **bold text** and *italic text*.

We also have **bold with *nested italic*** text.

Here is some `inline code` as well.
"""

# Document with tables
TABLE_DOC = """# Document with Tables

| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Value A  | Value B  | Value C  |
| Value D  | Value E  | Value F  |
"""

# Complex document with everything
COMPLEX_DOC = """# Comprehensive Test Document

## Introduction

This document contains **all supported features** to test the PDF generator.

### Key Features

- Bullet points work
- With multiple items
- And nested formatting like **bold**

### Formatted Text

Here's a paragraph with **bold text**, *italic text*, and `inline code`.

## Section 2: Lists

### Ordered Lists

1. First item
2. Second item with **bold**
3. Third item with *italic*

### Unordered Lists

- Item one
- Item two
- Item three

## Section 3: Tables

| Feature | Status | Notes |
|---------|--------|-------|
| **Headers** | ✓ | Working |
| **Lists** | ✓ | Working |
| **Tables** | ✓ | Working |

## Metadata Format

**From:** Engineering Team
**Investment:** $50,000
**Timeline:** Q1 2025
**Deliverable:** PDF Generation System

## Conclusion

This concludes the comprehensive test document.
"""

# Edge cases document
EDGE_CASES_DOC = """# Edge Cases

## Empty sections

### Empty subsection

## Special Characters

Testing special characters: & < > " '

## Very Long Line

This is a very long line that should wrap properly in the PDF output and not cause any issues with text rendering or layout problems that might occur with extremely long lines of text that go on and on without any breaks whatsoever.

## Multiple consecutive headers

### Header 1
### Header 2
### Header 3

## Lists with no spacing

- Item 1
- Item 2
- Item 3
"""

# Metadata-heavy document (tests special spacing)
METADATA_DOC = """# Project Proposal

**From:** John Doe
**To:** Jane Smith
**Investment:** $100,000
**Timeline:** 6 months
**Deliverable:** Mobile Application

## Overview

This is the project overview.
"""

# Document with new features (links, blockquotes, better code)
NEW_FEATURES_DOC = """# New Features Test

## Clickable Links

Visit [Davinci AI Solutions](https://davincisolutions.ai) for more information.

## Blockquotes

> This is a blockquote with some important information.
> It should be styled differently from regular text.

## Improved Code Blocks

Here is some `inline code` with background styling.

## Combined Features

Check out our **[documentation](https://docs.davincisolutions.ai)** for details.

> **Note:** Code like `python app.py` should have grey background.
"""

# All test fixtures
FIXTURES = {
    'simple': SIMPLE_DOC,
    'lists': LISTS_DOC,
    'formatting': FORMATTING_DOC,
    'table': TABLE_DOC,
    'complex': COMPLEX_DOC,
    'edge_cases': EDGE_CASES_DOC,
    'metadata': METADATA_DOC,
    'new_features': NEW_FEATURES_DOC,
}

# Default config for testing
DEFAULT_CONFIG = {
    'letterhead': {
        'company': 'Test Company',
        'address': '123 Test St, Test City, TC 12345',
        'phone': '+1 (555) 123-4567',
        'email': 'test@example.com'
    },
    'disclaimer': 'Test disclaimer text for document testing.',
    'logo_path': None
}
