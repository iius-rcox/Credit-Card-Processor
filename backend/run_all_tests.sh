#!/bin/bash
# Complete Test Suite Execution Script
#
# Runs all tests: contract, integration, and unit tests

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  Complete Test Suite Execution                ${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Create results directory
mkdir -p test_results

# Track overall status
OVERALL_STATUS=0

# 1. Contract Tests
echo -e "${BLUE}[1/3] Running Contract Tests...${NC}"
if pytest tests/contract/ -v --tb=short -m contract --junitxml=test_results/contract.xml 2>&1 | tee test_results/contract.log; then
    echo -e "${GREEN}✓ Contract tests passed${NC}"
else
    echo -e "${RED}✗ Contract tests failed${NC}"
    OVERALL_STATUS=1
fi
echo ""

# 2. Integration Tests (if they exist)
if [ -d "tests/integration" ] && [ "$(ls -A tests/integration/*.py 2>/dev/null)" ]; then
    echo -e "${BLUE}[2/3] Running Integration Tests...${NC}"
    if pytest tests/integration/ -v --tb=short -m integration --junitxml=test_results/integration.xml 2>&1 | tee test_results/integration.log; then
        echo -e "${GREEN}✓ Integration tests passed${NC}"
    else
        echo -e "${RED}✗ Integration tests failed${NC}"
        OVERALL_STATUS=1
    fi
else
    echo -e "${YELLOW}[2/3] Integration tests not found (skipping)${NC}"
fi
echo ""

# 3. Unit Tests (if they exist)
if [ -d "tests/unit" ] && [ "$(ls -A tests/unit/*.py 2>/dev/null)" ]; then
    echo -e "${BLUE}[3/3] Running Unit Tests...${NC}"
    if pytest tests/unit/ -v --tb=short -m unit --junitxml=test_results/unit.xml 2>&1 | tee test_results/unit.log; then
        echo -e "${GREEN}✓ Unit tests passed${NC}"
    else
        echo -e "${RED}✗ Unit tests failed${NC}"
        OVERALL_STATUS=1
    fi
else
    echo -e "${YELLOW}[3/3] Unit tests not found (skipping)${NC}"
fi
echo ""

# Summary
echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  Test Summary                                  ${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

if [ $OVERALL_STATUS -eq 0 ]; then
    echo -e "${GREEN}✓ ALL TESTS PASSED${NC}"
else
    echo -e "${RED}✗ SOME TESTS FAILED${NC}"
fi

echo ""
echo "Results saved to: test_results/"
echo ""

exit $OVERALL_STATUS
