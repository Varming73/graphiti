#!/usr/bin/env python3
"""Test group_id validation directly."""
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
    ("group/test", False),
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
sys.exit(0 if failed == 0 else 1)
