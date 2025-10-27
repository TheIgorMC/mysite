#!/bin/bash
# Quick deployment checker - Run AFTER deploying to verify everything is working
# Usage: ./check_deployment.sh

echo "🔍 Deployment Verification Checklist"
echo "====================================="
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

pass_count=0
fail_count=0

# Check 1: Container running
echo -n "1. Container running... "
if docker ps | grep -q orion-project; then
    echo -e "${GREEN}✓ PASS${NC}"
    ((pass_count++))
else
    echo -e "${RED}✗ FAIL${NC}"
    ((fail_count++))
    echo "   Run: docker-compose up -d"
fi

# Check 2: Cache clearing in logs
echo -n "2. Cache cleared on startup... "
if docker logs orion-project 2>&1 | grep -q "Clearing Python cache"; then
    echo -e "${GREEN}✓ PASS${NC}"
    ((pass_count++))
else
    echo -e "${RED}✗ FAIL${NC}"
    ((fail_count++))
    echo "   Cache clearing may not have run"
fi

# Check 3: Template recompilation
echo -n "3. Templates recompiled... "
if docker logs orion-project 2>&1 | grep -q "Forcing template recompilation"; then
    echo -e "${GREEN}✓ PASS${NC}"
    ((pass_count++))
else
    echo -e "${RED}✗ FAIL${NC}"
    ((fail_count++))
    echo "   Template touch may not have run"
fi

# Check 4: No .pyc files
echo -n "4. No cached bytecode... "
pyc_count=$(docker exec orion-project find /app -name "*.pyc" -o -name "*.pyo" 2>/dev/null | wc -l)
if [ "$pyc_count" -eq 0 ]; then
    echo -e "${GREEN}✓ PASS${NC}"
    ((pass_count++))
else
    echo -e "${YELLOW}⚠ WARNING${NC} - Found $pyc_count .pyc/.pyo files"
    ((fail_count++))
fi

# Check 5: Template modification time
echo -n "5. Template file is recent... "
mod_time=$(docker exec orion-project stat -c %Y /app/site01/app/templates/archery/competitions.html 2>/dev/null)
current_time=$(date +%s)
age=$((current_time - mod_time))

if [ "$age" -lt 3600 ]; then # Less than 1 hour old
    echo -e "${GREEN}✓ PASS${NC} (${age}s ago)"
    ((pass_count++))
else
    minutes=$((age / 60))
    echo -e "${YELLOW}⚠ WARNING${NC} (${minutes}m ago)"
    ((fail_count++))
    echo "   File may be from old build"
fi

# Check 6: Flask config
echo -n "6. TEMPLATES_AUTO_RELOAD enabled... "
auto_reload=$(docker exec orion-project python -c "from app import create_app; app=create_app('production'); print(app.config.get('TEMPLATES_AUTO_RELOAD', False))" 2>/dev/null)
if [ "$auto_reload" = "True" ]; then
    echo -e "${GREEN}✓ PASS${NC}"
    ((pass_count++))
else
    echo -e "${RED}✗ FAIL${NC}"
    ((fail_count++))
    echo "   Flask may not auto-reload templates"
fi

# Check 7: Gunicorn workers
echo -n "7. Gunicorn workers running... "
worker_count=$(docker exec orion-project ps aux | grep -c "[g]unicorn.*worker" 2>/dev/null)
if [ "$worker_count" -ge 4 ]; then
    echo -e "${GREEN}✓ PASS${NC} ($worker_count workers)"
    ((pass_count++))
else
    echo -e "${RED}✗ FAIL${NC} (only $worker_count workers)"
    ((fail_count++))
fi

# Check 8: Database accessible
echo -n "8. Database accessible... "
if docker exec orion-project test -f /app/data/orion.db 2>/dev/null; then
    echo -e "${GREEN}✓ PASS${NC}"
    ((pass_count++))
else
    echo -e "${RED}✗ FAIL${NC}"
    ((fail_count++))
    echo "   Database file not found at /app/data/orion.db"
fi

# Check 9: No errors in recent logs
echo -n "9. No errors in recent logs... "
error_count=$(docker logs orion-project --tail 50 2>&1 | grep -ic "error\|exception\|traceback" || true)
if [ "$error_count" -eq 0 ]; then
    echo -e "${GREEN}✓ PASS${NC}"
    ((pass_count++))
else
    echo -e "${YELLOW}⚠ WARNING${NC} - Found $error_count error-like lines"
    echo "   Check logs: docker logs orion-project --tail 50"
fi

# Check 10: Git status
echo -n "10. Git repo is clean... "
if [ -z "$(git status --porcelain)" ]; then
    echo -e "${GREEN}✓ PASS${NC}"
    ((pass_count++))
else
    echo -e "${YELLOW}⚠ WARNING${NC} - Uncommitted changes"
    echo "   Run: git status"
fi

echo ""
echo "====================================="
echo -e "Results: ${GREEN}$pass_count passed${NC}, ${RED}$fail_count failed/warnings${NC}"
echo ""

if [ "$fail_count" -eq 0 ]; then
    echo -e "${GREEN}✅ All checks passed!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Open browser and go to your site"
    echo "2. Press Ctrl+Shift+R (hard refresh)"
    echo "3. Verify changes are visible"
    exit 0
else
    echo -e "${YELLOW}⚠️  Some checks failed or have warnings${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "- Run: ./force_deploy.sh"
    echo "- Check logs: docker logs orion-project"
    echo "- Verify Git: git status && git pull"
    echo "- See: docs/CACHE_TROUBLESHOOTING.md"
    exit 1
fi
