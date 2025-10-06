#!/bin/bash
# Contract Test Execution Script for Feature 005
#
# This script runs all contract tests and generates a validation report

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  Credit Card Reconciliation - Contract Tests  ${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Check if we're in the backend directory
if [ ! -f "pytest.ini" ]; then
    echo -e "${RED}Error: Must be run from backend/ directory${NC}"
    echo "Usage: cd backend && ./run_contract_tests.sh"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ] && [ ! -d ".venv" ]; then
    echo -e "${YELLOW}Warning: No virtual environment found${NC}"
    echo -e "${YELLOW}Consider creating one: python -m venv venv${NC}"
    echo ""
fi

# Check if dependencies are installed
echo -e "${BLUE}Checking dependencies...${NC}"
if ! python -c "import pytest" 2>/dev/null; then
    echo -e "${RED}Error: pytest not installed${NC}"
    echo "Install dependencies: pip install -r requirements.txt"
    exit 1
fi

if ! python -c "import httpx" 2>/dev/null; then
    echo -e "${RED}Error: httpx not installed${NC}"
    echo "Install dependencies: pip install -r requirements.txt"
    exit 1
fi

echo -e "${GREEN}✓ Dependencies OK${NC}"
echo ""

# Run contract tests
echo -e "${BLUE}Running contract tests...${NC}"
echo ""

# Create test results directory
mkdir -p test_results

# Run tests with various output formats
pytest tests/contract/ \
    -v \
    --tb=short \
    -m contract \
    --junitxml=test_results/contract_tests.xml \
    --html=test_results/contract_tests.html \
    --self-contained-html \
    2>&1 | tee test_results/contract_tests.log

# Capture exit code
TEST_EXIT_CODE=$?

echo ""
echo -e "${BLUE}================================================${NC}"

# Summary
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ All contract tests passed!${NC}"
else
    echo -e "${RED}✗ Some tests failed (exit code: $TEST_EXIT_CODE)${NC}"
    echo -e "${YELLOW}Check test_results/contract_tests.html for details${NC}"
fi

echo -e "${BLUE}================================================${NC}"
echo ""

# Show results location
echo -e "${BLUE}Test Results:${NC}"
echo "  - Log: test_results/contract_tests.log"
echo "  - XML: test_results/contract_tests.xml"
echo "  - HTML: test_results/contract_tests.html"
echo ""

# Quick stats
if [ -f "test_results/contract_tests.log" ]; then
    echo -e "${BLUE}Quick Stats:${NC}"

    PASSED=$(grep -c "PASSED" test_results/contract_tests.log || echo "0")
    FAILED=$(grep -c "FAILED" test_results/contract_tests.log || echo "0")
    ERRORS=$(grep -c "ERROR" test_results/contract_tests.log || echo "0")

    echo -e "  Passed: ${GREEN}${PASSED}${NC}"
    echo -e "  Failed: ${RED}${FAILED}${NC}"
    echo -e "  Errors: ${RED}${ERRORS}${NC}"
    echo ""
fi

exit $TEST_EXIT_CODE
