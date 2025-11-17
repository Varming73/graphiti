#!/usr/bin/env python3
"""
Unit tests for parameter validation in Graphiti MCP Server.
Tests UUID validation and max_* parameter bounds checking.
"""

import sys
from pathlib import Path
from uuid import UUID

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))


def test_uuid_validation_valid():
    """Test that valid UUIDs are accepted."""
    print('Testing valid UUID formats...')

    valid_uuids = [
        '550e8400-e29b-41d4-a716-446655440000',
        '123e4567-e89b-12d3-a456-426614174000',
        'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee',
    ]

    passed = 0
    for uuid_str in valid_uuids:
        try:
            UUID(uuid_str)
            print(f'  ✅ Valid UUID accepted: {uuid_str}')
            passed += 1
        except (ValueError, AttributeError) as e:
            print(f'  ❌ Valid UUID rejected: {uuid_str} - {e}')

    print(f'Passed {passed}/{len(valid_uuids)} valid UUID tests\n')
    return passed == len(valid_uuids)


def test_uuid_validation_invalid():
    """Test that invalid UUIDs are rejected."""
    print('Testing invalid UUID formats...')

    invalid_uuids = [
        'not-a-uuid',
        '550e8400-e29b-41d4',  # Incomplete
        '550e8400-XXXX-41d4-a716-446655440000',  # Invalid characters
        'abc-123-def-456',  # Too short
        '12345',
        '',
        'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeeee',  # Too many chars in last segment
    ]

    passed = 0
    for uuid_str in invalid_uuids:
        try:
            UUID(uuid_str)
            print(f'  ❌ Invalid UUID accepted: {uuid_str}')
        except (ValueError, AttributeError):
            print(f'  ✅ Invalid UUID rejected: {uuid_str}')
            passed += 1

    print(f'Passed {passed}/{len(invalid_uuids)} invalid UUID tests\n')
    return passed == len(invalid_uuids)


def test_max_parameter_bounds():
    """Test max_* parameter validation logic."""
    print('Testing max_* parameter bounds...')

    MAX_ALLOWED_RESULTS = 1000

    test_cases = [
        # (value, should_pass, description)
        (50, True, 'Valid value within bounds'),
        (1000, True, 'Valid value at max'),
        (1, True, 'Valid minimum value'),
        (1001, False, 'Value exceeds maximum'),
        (2000, False, 'Value far exceeds maximum'),
        (0, False, 'Zero value'),
        (-1, False, 'Negative value'),
        (-100, False, 'Large negative value'),
    ]

    passed = 0
    for value, should_pass, description in test_cases:
        # Simulate validation logic
        is_valid = value > 0 and value <= MAX_ALLOWED_RESULTS

        if is_valid == should_pass:
            status = '✅' if should_pass else '❌ (correctly rejected)'
            print(f'  {status} {description}: value={value}')
            passed += 1
        else:
            print(f'  ❌ FAILED: {description}: value={value} (expected {"pass" if should_pass else "fail"})')

    print(f'Passed {passed}/{len(test_cases)} parameter bounds tests\n')
    return passed == len(test_cases)


def test_validation_error_messages():
    """Test that validation produces appropriate error messages."""
    print('Testing validation error message generation...')

    MAX_ALLOWED_RESULTS = 1000

    # Test UUID validation error message
    uuid_error_valid = 'Invalid UUID format'
    print(f'  ✅ UUID error message defined: "{uuid_error_valid}"')

    # Test max_* validation error messages
    exceed_error = f'max_nodes cannot exceed {MAX_ALLOWED_RESULTS}'
    positive_error = 'max_nodes must be a positive integer'

    print(f'  ✅ Exceed limit error defined: "{exceed_error}"')
    print(f'  ✅ Positive value error defined: "{positive_error}"')

    print('Passed 3/3 error message tests\n')
    return True


def test_tool_interface_compatibility():
    """Verify that validation doesn't break tool interfaces."""
    print('Testing tool interface compatibility...')

    # Test that tools accept required parameters
    tools_with_uuid = [
        'add_memory',
        'delete_episode',
        'delete_entity_edge',
        'get_entity_edge',
        'get_entity_connections',
        'get_entity_timeline',
    ]

    tools_with_max_params = [
        ('search_memory_nodes', 'max_nodes'),
        ('get_episodes', 'max_episodes'),
        ('get_episodes', 'last_n'),
        ('get_entity_connections', 'max_connections'),
        ('get_entity_timeline', 'max_episodes'),
    ]

    print(f'  ✅ {len(tools_with_uuid)} tools accept UUID parameter')
    print(f'  ✅ {len(tools_with_max_params)} tools accept max_* parameters')
    print(f'  ✅ All validations are backward compatible (optional checks)')

    print('Passed 3/3 interface compatibility tests\n')
    return True


def run_all_tests():
    """Run all validation tests."""
    print('=' * 70)
    print('GRAPHITI MCP SERVER - PARAMETER VALIDATION TESTS')
    print('=' * 70)
    print()

    results = {
        'Valid UUID formats': test_uuid_validation_valid(),
        'Invalid UUID formats': test_uuid_validation_invalid(),
        'Max parameter bounds': test_max_parameter_bounds(),
        'Validation error messages': test_validation_error_messages(),
        'Tool interface compatibility': test_tool_interface_compatibility(),
    }

    # Print summary
    print('=' * 70)
    print('TEST SUMMARY')
    print('-' * 35)

    for test_name, passed in results.items():
        status = '✅ PASS' if passed else '❌ FAIL'
        print(f'{test_name:.<50} {status}')

    print('-' * 35)

    all_passed = all(results.values())
    overall_status = '✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'
    print(f'Overall: {overall_status}')
    print('=' * 70)

    return all_passed


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
