#!/bin/bash

# Test runner for Davinci Document Creator
# Run all tests with coverage reporting

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "======================================="
echo "Davinci Document Creator - Test Suite"
echo "======================================="
echo ""

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Warning: Virtual environment not activated"
    echo "   Activate with: source venv/bin/activate"
    echo ""
fi

# Check if test dependencies are installed
if ! python -c "import PyPDF2" 2>/dev/null; then
    echo "📦 Installing test dependencies..."
    pip install -r requirements-test.txt
    echo ""
fi

# Parse command line arguments
RUN_MODE="all"
SAVE_BASELINE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --unit)
            RUN_MODE="unit"
            shift
            ;;
        --integration)
            RUN_MODE="integration"
            shift
            ;;
        --regression)
            RUN_MODE="regression"
            shift
            ;;
        --save-baseline)
            SAVE_BASELINE=true
            shift
            ;;
        --quick)
            RUN_MODE="quick"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--unit|--integration|--regression|--quick] [--save-baseline]"
            exit 1
            ;;
    esac
done

# Run tests based on mode
case $RUN_MODE in
    unit)
        echo "🧪 Running unit tests..."
        python -m pytest tests/test_html_parser.py -v
        ;;
    integration)
        echo "🧪 Running integration tests..."
        python -m pytest tests/test_pdf_generation.py -v
        ;;
    regression)
        echo "🧪 Running regression tests..."
        if [ "$SAVE_BASELINE" = true ]; then
            echo "📝 Saving new baselines..."
            python tests/test_regression.py --save-baseline
        else
            python -m pytest tests/test_regression.py -v
        fi
        ;;
    quick)
        echo "🧪 Running quick test suite..."
        python -m pytest tests/test_html_parser.py -v --tb=short
        ;;
    all)
        echo "🧪 Running complete test suite..."
        echo ""

        echo "1️⃣  Unit Tests (HTML Parser)"
        echo "----------------------------"
        python -m pytest tests/test_html_parser.py -v
        echo ""

        echo "2️⃣  Integration Tests (PDF Generation)"
        echo "--------------------------------------"
        python -m pytest tests/test_pdf_generation.py -v
        echo ""

        if [ "$SAVE_BASELINE" = true ]; then
            echo "3️⃣  Creating Regression Baselines"
            echo "---------------------------------"
            python tests/test_regression.py --save-baseline
        else
            echo "3️⃣  Regression Tests (Baseline Comparison)"
            echo "------------------------------------------"
            python -m pytest tests/test_regression.py -v
        fi
        echo ""
        ;;
esac

echo ""
echo "✅ Tests complete!"
echo ""
echo "Generated test outputs are in: tests/output/"
echo "Baseline PDFs are in: tests/baselines/"
