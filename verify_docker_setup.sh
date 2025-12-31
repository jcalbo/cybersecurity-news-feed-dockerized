#!/bin/bash
# Docker Setup Verification Script for dev02 Branch
# Tests all three services: Elasticsearch, Backend, Frontend

set -e

echo "🔍 Verifying Docker Setup for dev02 Branch"
echo "============================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Function to test and report
test_step() {
    local test_name="$1"
    local test_command="$2"
    
    echo -n "Testing: $test_name... "
    
    if eval "$test_command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASS${NC}"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}✗ FAIL${NC}"
        ((TESTS_FAILED++))
        return 1
    fi
}

echo "📋 Prerequisites Check"
echo "----------------------"
test_step "Docker installed" "command -v docker"
test_step "Docker Compose installed" "command -v docker-compose"
test_step "User in docker group" "groups | grep -q docker"
echo ""

echo "🐳 Docker Container Status"
echo "--------------------------"
test_step "Elasticsearch container running" "docker ps | grep -q cybersecurity-news-elasticsearch"
test_step "Kibana container running" "docker ps | grep -q cybersecurity-news-kibana"
test_step "Backend container running" "docker ps | grep -q cybersecurity-news-backend"
test_step "Frontend container running" "docker ps | grep -q cybersecurity-news-frontend"
echo ""

echo "🔌 Service Health Checks"
echo "------------------------"
test_step "Elasticsearch responding" "curl -sf http://localhost:9200 -o /dev/null"
test_step "Kibana responding" "curl -sf http://localhost:5601/api/status -o /dev/null"
test_step "Backend /health endpoint" "curl -sf http://localhost:8000/health -o /dev/null"
test_step "Frontend Streamlit health" "curl -sf http://localhost:8501/_stcore/health -o /dev/null"
echo ""

echo "🔗 Elasticsearch Integration"
echo "-----------------------------"
test_step "Backend connects to Elasticsearch" "curl -sf http://localhost:8000/health/elasticsearch | grep -q '\"connected\":true'"

# Get and display Elasticsearch stats
echo ""
echo "📊 Elasticsearch Statistics:"
curl -s http://localhost:8000/api/stats | python3 -m json.tool | grep -E "(total_documents|latest_fetch|cache_is_fresh)" || echo "  Stats unavailable"
echo ""

echo "🌐 API Endpoints Test"
echo "---------------------"
test_step "GET /api/sources" "curl -sf http://localhost:8000/api/sources -o /dev/null"
test_step "GET /api/stats" "curl -sf http://localhost:8000/api/stats -o /dev/null"

# Test POST /api/news (might take a few seconds)
echo -n "Testing: POST /api/news... "
if curl -sf -X POST http://localhost:8000/api/news \
    -H "Content-Type: application/json" \
    -d '{"hours": 24, "response_format": "json"}' | grep -q '"title"'; then
    echo -e "${GREEN}✓ PASS${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗ FAIL${NC}"
    ((TESTS_FAILED++))
fi
echo ""

echo "📦 Data Verification"
echo "--------------------"
DOC_COUNT=$(curl -s http://localhost:8000/api/stats | grep -o '"total_documents":[0-9]*' | grep -o '[0-9]*')

if [ -n "$DOC_COUNT" ] && [ "$DOC_COUNT" -gt 0 ]; then
    echo -e "Documents in Elasticsearch: ${GREEN}$DOC_COUNT${NC} ✓"
    ((TESTS_PASSED++))
else
    echo -e "Documents in Elasticsearch: ${YELLOW}0 (may need first fetch)${NC}"
    echo "  Run: curl -X POST http://localhost:8000/api/news -H 'Content-Type: application/json' -d '{\"hours\": 24}'"
fi
echo ""

# Final summary
echo "============================================"
echo "📊 Test Summary"
echo "============================================"
echo -e "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests Failed: ${RED}$TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed! Docker setup is working correctly.${NC}"
    echo ""
    echo "🎉 Your services are ready:"
    echo "   - Frontend UI:     http://localhost:8501"
    echo "   - Backend API:     http://localhost:8000"
    echo "   - Elasticsearch:   http://localhost:9200"
    echo "   - Kibana:          http://localhost:5601"
    echo ""
    exit 0
else
    echo -e "${RED}❌ Some tests failed. Check the output above.${NC}"
    echo ""
    echo "🔧 Troubleshooting:"
    echo "   - Run: docker-compose logs <service>"
    echo "   - Run: docker-compose ps"
    echo "   - Check: docker-compose down && docker-compose up -d"
    echo ""
    exit 1
fi

