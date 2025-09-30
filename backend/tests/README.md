# Test Suite for Davinci Document Creator

Comprehensive test suite for the PDF generation functionality.

## Test Structure

```
tests/
├── __init__.py                 # Package initialization
├── fixtures.py                 # Test markdown documents
├── test_html_parser.py        # Unit tests for HTML parser (30+ tests)
├── test_pdf_generation.py     # Integration tests for PDF generation (15+ tests)
├── test_regression.py         # Regression tests against baselines (7 tests)
├── pdf_compare.py             # PDF comparison utilities
├── baselines/                 # Baseline PDFs for regression testing
└── output/                    # Test output PDFs for manual inspection
```

## Quick Start

### 1. Install Test Dependencies

```bash
cd backend
source venv/bin/activate  # or .venv/bin/activate
pip install -r requirements-test.txt
```

### 2. Create Baseline PDFs (First Time Only)

```bash
./run_tests.sh --save-baseline
```

This generates baseline PDFs from all test fixtures. These represent the "correct" output.

### 3. Run All Tests

```bash
./run_tests.sh
```

## Test Types

### Unit Tests (`test_html_parser.py`)

Tests the HTML parser in isolation:
- ✅ Heading parsing (H1, H2, H3)
- ✅ Paragraph formatting
- ✅ Bold and italic text
- ✅ Ordered and unordered lists
- ✅ Tables
- ✅ Nested formatting
- ✅ Code formatting
- ✅ Special characters
- ✅ Edge cases (unclosed tags, nested lists, etc.)

**Run only unit tests:**
```bash
./run_tests.sh --unit
```

### Integration Tests (`test_pdf_generation.py`)

Tests the complete markdown → PDF pipeline:
- ✅ Simple documents
- ✅ Documents with lists
- ✅ Documents with formatting
- ✅ Documents with tables
- ✅ Complex multi-section documents
- ✅ Metadata formatting
- ✅ Edge cases
- ✅ Page numbering on multi-page docs
- ✅ Custom configuration
- ✅ Empty documents
- ✅ Very long documents
- ✅ Special characters

**Run only integration tests:**
```bash
./run_tests.sh --integration
```

**Outputs:** Test PDFs are saved to `tests/output/` for manual inspection.

### Regression Tests (`test_regression.py`)

Compares generated PDFs against baseline PDFs:
- ✅ Detects changes in text content
- ✅ Detects changes in page count
- ✅ Detects changes in file size
- ✅ Uses fingerprinting for quick comparison

**Run only regression tests:**
```bash
./run_tests.sh --regression
```

**Update baselines after intentional changes:**
```bash
./run_tests.sh --regression --save-baseline
```

## Using the Tests Before Making Changes

### Step 1: Create Current Baselines

Before making any changes to the code:

```bash
cd backend
source venv/bin/activate
./run_tests.sh --save-baseline
```

This saves the **current behavior** as the baseline.

### Step 2: Make Your Changes

Edit `app.py`, modify the HTML parser, add features, etc.

### Step 3: Run Tests to Detect Breaking Changes

```bash
./run_tests.sh
```

**What to look for:**
- ❌ **Failing unit tests** = Parser logic broken
- ❌ **Failing integration tests** = PDF generation broken
- ❌ **Failing regression tests** = Output changed vs baseline

### Step 4: Investigate Failures

#### If unit tests fail:
The HTML parser has a bug. Check:
- `test_html_parser.py` output for which test failed
- The specific assertion that failed
- Fix the parser logic in `app.py`

#### If integration tests fail:
PDF generation crashed or produced invalid PDFs. Check:
- `test_pdf_generation.py` output
- Test PDFs in `tests/output/` directory
- Error messages and stack traces

#### If regression tests fail:
Output changed but didn't crash. This could be:
- ✅ **Intentional** (you wanted to change the output)
  - Update baselines: `./run_tests.sh --regression --save-baseline`
- ❌ **Unintentional** (you broke something)
  - Compare old vs new PDFs in `tests/baselines/` and `tests/output/`
  - Fix the issue

## Test Fixtures

The test suite includes 7 comprehensive fixtures:

1. **simple** - Basic document with headings and paragraphs
2. **lists** - Ordered and unordered lists
3. **formatting** - Bold, italic, and code formatting
4. **table** - Document with tables
5. **complex** - Everything combined (multi-page)
6. **metadata** - Special metadata formatting (Investment:, Timeline:, etc.)
7. **edge_cases** - Weird edge cases (empty sections, special chars, long lines)

## Manual Testing

### Generate Test PDFs

```bash
cd backend
source venv/bin/activate
python -m pytest tests/test_pdf_generation.py -v
```

Check `tests/output/` for generated PDFs. Open them and verify:
- Headers are correct colors
- Page numbers show "Page X of Y"
- Logo placement is correct
- Tables are formatted properly
- Lists have bullets/numbers

### Compare Two PDFs

```bash
python tests/pdf_compare.py tests/baselines/simple.pdf tests/output/test_simple.pdf
```

## Continuous Integration

To add tests to CI/CD pipeline, add to `.github/workflows/`:

```yaml
- name: Run tests
  run: |
    cd backend
    pip install -r requirements-test.txt
    python -m pytest tests/ -v
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'PyPDF2'"

```bash
pip install -r requirements-test.txt
```

### "No baseline found for X"

Create baselines first:
```bash
./run_tests.sh --save-baseline
```

### Tests pass but PDFs look wrong

1. Open PDFs in `tests/output/` manually
2. Look for visual issues
3. Tests only check structure, not exact pixel appearance
4. Consider adding more specific assertions

### All regression tests failing after changes

Your changes affected **all** output. Either:
- You have a widespread bug (check unit tests)
- You made an intentional change (update baselines)

## Best Practices

### Before Making Changes
✅ Run `./run_tests.sh --save-baseline` to capture current behavior

### After Making Changes
✅ Run `./run_tests.sh` to verify nothing broke

### Before Committing
✅ All tests should pass
✅ Review any baseline updates carefully
✅ Check test PDFs manually if output changed

### Before Deploying
✅ Run full test suite on production-like environment
✅ Generate and inspect test PDFs
✅ Compare to baselines

## Adding New Tests

### Add a new fixture:

Edit `tests/fixtures.py`:
```python
NEW_FIXTURE = """# New Test
Your markdown here
"""

FIXTURES['new_feature'] = NEW_FIXTURE
```

### Add a new test:

Edit appropriate test file:
```python
def test_new_feature(self):
    """Test new feature"""
    markdown = FIXTURES['new_feature']
    pdf_buffer = create_pdf(markdown, DEFAULT_CONFIG)
    # Assertions here
```

### Regenerate baselines:

```bash
./run_tests.sh --save-baseline
```

## Questions?

See the main README or check the test code for examples.
