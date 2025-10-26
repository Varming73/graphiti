#!/bin/bash
#
# Manual test script for Session 1A security fixes
# This tests validation by sending requests directly to the MCP server

echo "================================"
echo "Session 1A Manual Security Tests"
echo "================================"
echo ""

# Test 1: Test group_id validation with Python script
echo "Test 1: Group ID Validation"
echo "----------------------------"

# Create a simple Python client test
cat > /tmp/test_groupid.py << 'EOF'
import asyncio
import sys
sys.path.insert(0, '/app')

from graphiti_mcp_server import validate_group_id_mcp

# Test cases
test_cases = [
    ("personal", True),
    ("work-projects", True),
    ("my_notes", True),
    ("../../../etc/passwd", False),
    ("test@domain", False),
    ("group#1", False),
    ("my group", False),
]

print("\nTesting Group ID Validation:")
print("=" * 60)
passed = 0
failed = 0

for group_id, should_pass in test_cases:
    try:
        result = validate_group_id_mcp(group_id)
        if should_pass:
            print(f"✅ PASS: '{group_id}' accepted")
            passed += 1
        else:
            print(f"❌ FAIL: '{group_id}' should have been rejected")
            failed += 1
    except ValueError as e:
        if not should_pass:
            print(f"✅ PASS: '{group_id}' rejected - {e}")
            passed += 1
        else:
            print(f"❌ FAIL: '{group_id}' should have been accepted - {e}")
            failed += 1

print(f"\nResults: {passed} passed, {failed} failed")
EOF

docker exec mcp_server-graphiti-mcp-falkordb-1 python /tmp/test_groupid.py

echo ""
echo "Test 2: UUID Validation"
echo "------------------------"

# Test UUID validation
cat > /tmp/test_uuid.py << 'EOF'
import sys
sys.path.insert(0, '/app')

from graphiti_mcp_server import validate_uuid_mcp

# Test cases
test_cases = [
    ("123e4567-e89b-12d3-a456-426614174000", True),
    ("not-a-uuid", False),
    ("abc123", False),
    ("123e4567-e89b-XXXX-a456-426614174000", False),
]

print("\nTesting UUID Validation:")
print("=" * 60)
passed = 0
failed = 0

for uuid_str, should_pass in test_cases:
    try:
        result = validate_uuid_mcp(uuid_str)
        if should_pass:
            print(f"✅ PASS: '{uuid_str}' accepted")
            passed += 1
        else:
            print(f"❌ FAIL: '{uuid_str}' should have been rejected")
            failed += 1
    except ValueError as e:
        if not should_pass:
            print(f"✅ PASS: '{uuid_str}' rejected - {e}")
            passed += 1
        else:
            print(f"❌ FAIL: '{uuid_str}' should have been accepted - {e}")
            failed += 1

print(f"\nResults: {passed} passed, {failed} failed")
EOF

docker exec mcp_server-graphiti-mcp-falkordb-1 python /tmp/test_uuid.py

echo ""
echo "Test 3: Log Sanitization"
echo "-------------------------"

# Check logs for sensitive data
echo "Checking logs for exposed API keys..."
cd /Users/lvarming/projects/graphiti/mcp_server
LOGS=$(docker compose --profile falkordb logs graphiti-mcp-falkordb --tail 500)

# Check for full API keys (should NOT be present)
if echo "$LOGS" | grep -q "sk-proj-[A-Za-z0-9_-]\{100,\}"; then
    echo "❌ FAIL: Full API keys found in logs!"
else
    echo "✅ PASS: No full API keys in logs"
fi

# Check for partial key patterns (informational)
if echo "$LOGS" | grep -q "sk-proj-"; then
    echo "⚠️  WARNING: Partial API key pattern found (check if properly redacted)"
else
    echo "✅ INFO: No API key patterns in logs"
fi

# Check for redaction markers (optional - only if sensitive data was logged)
if echo "$LOGS" | grep -q "\[REDACTED"; then
    echo "✅ INFO: Redaction markers found in logs"
    echo "$LOGS" | grep "\[REDACTED" | head -3
else
    echo "ℹ️  INFO: No redaction markers (no sensitive data logged)"
fi

echo ""
echo "================================"
echo "Manual Testing Complete"
echo "================================"
