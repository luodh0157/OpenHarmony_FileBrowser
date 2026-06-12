#!/bin/bash
# =============================================================================
# OpenHarmony File Browser - Test Runner (Linux/macOS)
# =============================================================================
# Usage:
#   ./run_tests.sh              # Run all tests
#   ./run_tests.sh unit         # Run unit tests only
#   ./run_tests.sh integration  # Run integration tests only
#   ./run_tests.sh test_file_utils.py  # Run specific test file
#   ./run_tests.sh --coverage   # Run with coverage report
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE} OpenHarmony File Browser - Test Runner${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: python3 not found${NC}"
    exit 1
fi

PYTHON=python3

# Check if virtual environment exists
if [ -d "venv" ]; then
    source venv/bin/activate
    PYTHON=python
elif [ -d ".venv" ]; then
    source .venv/bin/activate
    PYTHON=python
fi

echo -e "${BLUE}Python: $(which $PYTHON)${NC}"
echo -e "${BLUE}Version: $($PYTHON --version)${NC}"
echo ""

# Install test dependencies if needed
echo -e "${YELLOW}Checking test dependencies...${NC}"
$PYTHON -c "import pytest" 2>/dev/null || {
    echo -e "${YELLOW}Installing pytest...${NC}"
    $PYTHON -m pip install -q pytest
}

# Parse arguments
COVERAGE=false
TEST_TYPE="all"
SPECIFIC_FILE=""

for arg in "$@"; do
    case $arg in
        --coverage|-c)
            COVERAGE=true
            shift
            ;;
        unit|u)
            TEST_TYPE="unit"
            shift
            ;;
        integration|i)
            TEST_TYPE="integration"
            shift
            ;;
        *)
            SPECIFIC_FILE="$arg"
            shift
            ;;
    esac
done

# Install coverage if needed
if [ "$COVERAGE" = true ]; then
    $PYTHON -c "import coverage" 2>/dev/null || {
        echo -e "${YELLOW}Installing coverage...${NC}"
        $PYTHON -m pip install -q coverage pytest-cov
    }
fi

# Cleanup function
cleanup() {
    echo ""
    echo -e "${YELLOW}Cleaning up temporary files...${NC}"
    rm -rf .pytest_cache
    rm -rf htmlcov
    rm -f .coverage
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    echo -e "${GREEN}Cleanup completed.${NC}"
}

# Trap EXIT to ensure cleanup runs even on failure
trap cleanup EXIT

# Run tests
echo -e "${BLUE}Running tests...${NC}"
echo ""

if [ -n "$SPECIFIC_FILE" ]; then
    # Run specific test file
    if [ "$COVERAGE" = true ]; then
        $PYTHON -m pytest "tests/$SPECIFIC_FILE" -v --tb=short --cov=src --cov-report=term-missing --cov-report=html:htmlcov
    else
        $PYTHON -m pytest "tests/$SPECIFIC_FILE" -v --tb=short
    fi
elif [ "$TEST_TYPE" = "unit" ]; then
    # Run unit tests only
    if [ "$COVERAGE" = true ]; then
        $PYTHON -m pytest tests/unit/ -v --tb=short --cov=src --cov-report=term-missing --cov-report=html:htmlcov
    else
        $PYTHON -m pytest tests/unit/ -v --tb=short
    fi
elif [ "$TEST_TYPE" = "integration" ]; then
    # Run integration tests only
    if [ "$COVERAGE" = true ]; then
        $PYTHON -m pytest tests/integration/ -v --tb=short --cov=src --cov-report=term-missing --cov-report=html:htmlcov
    else
        $PYTHON -m pytest tests/integration/ -v --tb=short
    fi
else
    # Run all tests
    if [ "$COVERAGE" = true ]; then
        $PYTHON -m pytest tests/ -v --tb=short --cov=src --cov-report=term-missing --cov-report=html:htmlcov
    else
        $PYTHON -m pytest tests/ -v --tb=short
    fi
fi

EXIT_CODE=$?

echo ""
echo -e "${BLUE}============================================${NC}"

if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
else
    echo -e "${RED}Some tests failed (exit code: $EXIT_CODE)${NC}"
fi

if [ "$COVERAGE" = true ]; then
    echo -e "${YELLOW}Coverage report: htmlcov/index.html${NC}"
fi

echo -e "${BLUE}============================================${NC}"

# Cleanup will run via trap, but we override exit code
exit $EXIT_CODE
