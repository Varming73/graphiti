#!/usr/bin/env python3
"""Standalone test for Session 1A validation functions."""
import re
import uuid

# Copy the validation functions directly from graphiti_mcp_server.py
def validate_group_id_mcp(group_id: str | None) -> str:
    """Validate group_id for MCP server to prevent RedisSearch injection.

    Args:
        group_id: The group_id to validate

    Returns:
        The validated group_id

    Raises:
        ValueError: If group_id is None, empty, or contains invalid characters
    """
    if not group_id:
        raise ValueError('group_id is required')

    # Only allow alphanumeric characters, hyphens, and underscores
    # This prevents RedisSearch injection attacks
    if not re.match(r'^[a-zA-Z0-9_-]+$', group_id):
        raise ValueError(
            f"Invalid group_id '{group_id}'. Must contain only alphanumeric characters, "
            'hyphens, and underscores.'
        )

    return group_id


def validate_uuid_mcp(uuid_str: str) -> str:
    """Validate UUID format for MCP server.

    Args:
        uuid_str: The UUID string to validate

    Returns:
        The validated UUID string

    Raises:
        ValueError: If uuid_str is not a valid UUID format
    """
    try:
        # Try to parse as UUID to validate format
        uuid.UUID(uuid_str)
        return uuid_str
    except (ValueError, AttributeError) as e:
        raise ValueError(f"Invalid UUID '{uuid_str}'. Must be a valid UUID format.") from e


# Test cases for group_id
print("================================================================================")
print("SESSION 1A SECURITY TESTING")
print("================================================================================")
print()

print("Test 1: Group ID Validation")
print("----------------------------")

group_id_tests = [
    ("personal", True),
    ("work-projects", True),
    ("my_notes", True),
    ("../../../etc/passwd", False),
    ("test@domain", False),
    ("group#1", False),
    ("my group", False),
    ("group/test", False),
]

passed = 0
failed = 0

for group_id, should_pass in group_id_tests:
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
            print(f"✅ PASS: '{group_id}' rejected")
            print(f"         Error: {e}")
            passed += 1
        else:
            print(f"❌ FAIL: '{group_id}' should have been accepted")
            print(f"         Error: {e}")
            failed += 1

print(f"\nGroup ID Tests: {passed} passed, {failed} failed\n")

# Test cases for UUID
print("Test 2: UUID Validation")
print("------------------------")

uuid_tests = [
    ("123e4567-e89b-12d3-a456-426614174000", True),
    ("not-a-uuid", False),
    ("abc123", False),
    ("123e4567-e89b-XXXX-a456-426614174000", False),
]

uuid_passed = 0
uuid_failed = 0

for uuid_str, should_pass in uuid_tests:
    try:
        result = validate_uuid_mcp(uuid_str)
        if should_pass:
            print(f"✅ PASS: '{uuid_str}' accepted")
            uuid_passed += 1
        else:
            print(f"❌ FAIL: '{uuid_str}' should have been rejected")
            uuid_failed += 1
    except ValueError as e:
        if not should_pass:
            print(f"✅ PASS: '{uuid_str}' rejected")
            print(f"         Error: {e}")
            uuid_passed += 1
        else:
            print(f"❌ FAIL: '{uuid_str}' should have been accepted")
            print(f"         Error: {e}")
            uuid_failed += 1

print(f"\nUUID Tests: {uuid_passed} passed, {uuid_failed} failed\n")

# Summary
total_passed = passed + uuid_passed
total_failed = failed + uuid_failed

print("================================================================================")
print("TEST SUMMARY")
print("================================================================================")
print(f"Total Tests: {total_passed + total_failed}")
print(f"✅ Passed: {total_passed}")
print(f"❌ Failed: {total_failed}")

if total_failed == 0:
    print("\n🎉 ALL VALIDATION TESTS PASSED!")
else:
    print(f"\n⚠️  {total_failed} TESTS FAILED")
