#!/usr/bin/env python3
"""Test UUID validation directly."""
import sys
sys.path.insert(0, '/app')

from graphiti_mcp_server import validate_uuid_mcp

# Test cases
test_cases = [
    ("123e4567-e89b-12d3-a456-426614174000", True),
    ("not-a-uuid", False),
    ("abc123", False),
    ("123e4567-e89b-XXXX-a456-426614174000", False),
    ("", False),
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
sys.exit(0 if failed == 0 else 1)
