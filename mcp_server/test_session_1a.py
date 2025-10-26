#!/usr/bin/env python3
"""
Session 1A Security Testing Script

Tests all security fixes implemented in Session 1A:
1. Group ID validation (prevents RedisSearch injection)
2. UUID validation (prevents database errors)
3. Log sanitization (prevents API key exposure)
"""

import asyncio
import json
import sys
from typing import Any

import httpx


class Colors:
    """ANSI color codes for terminal output."""

    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


class MCPClient:
    """Simple MCP client for testing."""

    def __init__(self, base_url: str = 'http://localhost:8001'):
        self.base_url = base_url
        self.session_id = 1

    async def call_tool(
        self, tool_name: str, arguments: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Call an MCP tool and return the response."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            # MCP protocol: send a tools/call request
            request_data = {
                'jsonrpc': '2.0',
                'id': self.session_id,
                'method': 'tools/call',
                'params': {'name': tool_name, 'arguments': arguments},
            }
            self.session_id += 1

            try:
                response = await client.post(
                    f'{self.base_url}/message', json=request_data, headers={'Content-Type': 'application/json'}
                )

                if response.status_code != 200:
                    print(f'{Colors.RED}HTTP Error {response.status_code}{Colors.END}')
                    print(f'Response: {response.text}')
                    return None

                return response.json()
            except Exception as e:
                print(f'{Colors.RED}Request failed: {e}{Colors.END}')
                return None


class TestResults:
    """Track test results."""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []

    def add_result(self, test_name: str, passed: bool, details: str = ''):
        """Add a test result."""
        self.tests.append({'name': test_name, 'passed': passed, 'details': details})
        if passed:
            self.passed += 1
        else:
            self.failed += 1

    def print_summary(self):
        """Print test summary."""
        print(f'\n{Colors.BOLD}{"=" * 80}{Colors.END}')
        print(f'{Colors.BOLD}TEST SUMMARY{Colors.END}')
        print(f'{Colors.BOLD}{"=" * 80}{Colors.END}\n')

        for test in self.tests:
            status = f'{Colors.GREEN}✅ PASS{Colors.END}' if test['passed'] else f'{Colors.RED}❌ FAIL{Colors.END}'
            print(f'{status} {test["name"]}')
            if test['details']:
                print(f'    {test["details"]}')

        print(f'\n{Colors.BOLD}Total: {self.passed + self.failed} tests{Colors.END}')
        print(f'{Colors.GREEN}Passed: {self.passed}{Colors.END}')
        print(f'{Colors.RED}Failed: {self.failed}{Colors.END}')

        if self.failed == 0:
            print(f'\n{Colors.GREEN}{Colors.BOLD}🎉 ALL TESTS PASSED!{Colors.END}')
            return 0
        else:
            print(f'\n{Colors.RED}{Colors.BOLD}⚠️  SOME TESTS FAILED{Colors.END}')
            return 1


async def test_group_id_validation(client: MCPClient, results: TestResults):
    """Test group_id validation with various inputs."""
    print(f'\n{Colors.BLUE}{Colors.BOLD}Testing Group ID Validation{Colors.END}')
    print(f'{Colors.BLUE}{"=" * 80}{Colors.END}\n')

    test_cases = [
        {
            'name': 'Valid group_id (alphanumeric)',
            'group_id': 'personal',
            'should_pass': True,
        },
        {
            'name': 'Valid group_id (with hyphens)',
            'group_id': 'work-projects',
            'should_pass': True,
        },
        {
            'name': 'Valid group_id (with underscores)',
            'group_id': 'my_notes',
            'should_pass': True,
        },
        {
            'name': 'Invalid group_id (path traversal attempt)',
            'group_id': '../../../etc/passwd',
            'should_pass': False,
            'expected_error': 'Invalid group_id',
        },
        {
            'name': 'Invalid group_id (special characters)',
            'group_id': 'test@domain',
            'should_pass': False,
            'expected_error': 'Invalid group_id',
        },
        {
            'name': 'Invalid group_id (hash symbol)',
            'group_id': 'group#1',
            'should_pass': False,
            'expected_error': 'Invalid group_id',
        },
        {
            'name': 'Invalid group_id (spaces)',
            'group_id': 'my group',
            'should_pass': False,
            'expected_error': 'Invalid group_id',
        },
        {
            'name': 'Invalid group_id (forward slashes)',
            'group_id': 'group/test',
            'should_pass': False,
            'expected_error': 'Invalid group_id',
        },
    ]

    for test_case in test_cases:
        print(f'Testing: {test_case["name"]}')
        print(f'  group_id: "{test_case["group_id"]}"')

        response = await client.call_tool(
            'add_memory',
            {
                'name': 'Test Episode',
                'episode_body': 'This is a test episode for validation testing.',
                'group_id': test_case['group_id'],
            },
        )

        if response is None:
            results.add_result(
                test_case['name'], False, 'No response from server'
            )
            print(f'  {Colors.RED}❌ FAIL: No response{Colors.END}\n')
            continue

        # Check for error in response
        has_error = 'error' in response or ('result' in response and 'error' in response.get('result', {}))

        if test_case['should_pass']:
            # Should succeed
            if not has_error:
                results.add_result(test_case['name'], True, 'Request accepted as expected')
                print(f'  {Colors.GREEN}✅ PASS: Request accepted{Colors.END}\n')
            else:
                error_msg = response.get('error', response.get('result', {}).get('error', 'Unknown'))
                results.add_result(
                    test_case['name'],
                    False,
                    f'Expected success but got error: {error_msg}',
                )
                print(f'  {Colors.RED}❌ FAIL: Got error when expecting success{Colors.END}')
                print(f'  Error: {error_msg}\n')
        else:
            # Should fail with validation error
            if has_error:
                error_msg = str(response.get('error', response.get('result', {}).get('error', '')))
                if test_case['expected_error'] in error_msg:
                    results.add_result(
                        test_case['name'], True, f'Correctly rejected: {error_msg}'
                    )
                    print(f'  {Colors.GREEN}✅ PASS: Correctly rejected{Colors.END}')
                    print(f'  Error message: {error_msg}\n')
                else:
                    results.add_result(
                        test_case['name'],
                        False,
                        f'Wrong error message: {error_msg}',
                    )
                    print(f'  {Colors.YELLOW}⚠️  PARTIAL: Rejected but wrong error{Colors.END}')
                    print(f'  Expected: "{test_case["expected_error"]}"')
                    print(f'  Got: "{error_msg}"\n')
            else:
                results.add_result(
                    test_case['name'],
                    False,
                    'Expected validation error but request was accepted',
                )
                print(f'  {Colors.RED}❌ FAIL: Should have been rejected{Colors.END}\n')


async def test_uuid_validation(client: MCPClient, results: TestResults):
    """Test UUID validation with various inputs."""
    print(f'\n{Colors.BLUE}{Colors.BOLD}Testing UUID Validation{Colors.END}')
    print(f'{Colors.BLUE}{"=" * 80}{Colors.END}\n')

    test_cases = [
        {
            'name': 'Valid UUID format',
            'uuid': '123e4567-e89b-12d3-a456-426614174000',
            'should_pass': True,
        },
        {
            'name': 'Invalid UUID (not a UUID)',
            'uuid': 'not-a-uuid',
            'should_pass': False,
            'expected_error': 'Invalid UUID',
        },
        {
            'name': 'Invalid UUID (random string)',
            'uuid': 'abc123',
            'should_pass': False,
            'expected_error': 'Invalid UUID',
        },
        {
            'name': 'Invalid UUID (malformed)',
            'uuid': '123e4567-e89b-XXXX-a456-426614174000',
            'should_pass': False,
            'expected_error': 'Invalid UUID',
        },
    ]

    # Note: We're testing delete_entity_edge which requires a UUID
    # Since we don't have actual edges, all will fail, but we're testing validation
    for test_case in test_cases:
        print(f'Testing: {test_case["name"]}')
        print(f'  uuid: "{test_case["uuid"]}"')

        response = await client.call_tool(
            'delete_entity_edge', {'uuid': test_case['uuid']}
        )

        if response is None:
            results.add_result(
                test_case['name'], False, 'No response from server'
            )
            print(f'  {Colors.RED}❌ FAIL: No response{Colors.END}\n')
            continue

        has_error = 'error' in response or ('result' in response and 'error' in response.get('result', {}))

        if test_case['should_pass']:
            # Valid UUID format - should get past validation
            # (might fail later because edge doesn't exist, but that's OK)
            if has_error:
                error_msg = str(response.get('error', response.get('result', {}).get('error', '')))
                # Check if it's a validation error or a "not found" error
                if 'Invalid UUID' in error_msg:
                    results.add_result(
                        test_case['name'],
                        False,
                        f'Valid UUID rejected: {error_msg}',
                    )
                    print(f'  {Colors.RED}❌ FAIL: Valid UUID was rejected{Colors.END}')
                    print(f'  Error: {error_msg}\n')
                else:
                    # It's a different error (like "not found") which is fine
                    results.add_result(
                        test_case['name'],
                        True,
                        'UUID validation passed (failed later for different reason)',
                    )
                    print(f'  {Colors.GREEN}✅ PASS: UUID validation passed{Colors.END}')
                    print(f'  (Got expected error: {error_msg})\n')
            else:
                results.add_result(test_case['name'], True, 'UUID accepted')
                print(f'  {Colors.GREEN}✅ PASS: UUID validation passed{Colors.END}\n')
        else:
            # Should fail with validation error
            if has_error:
                error_msg = str(response.get('error', response.get('result', {}).get('error', '')))
                if test_case['expected_error'] in error_msg:
                    results.add_result(
                        test_case['name'], True, f'Correctly rejected: {error_msg}'
                    )
                    print(f'  {Colors.GREEN}✅ PASS: Correctly rejected{Colors.END}')
                    print(f'  Error message: {error_msg}\n')
                else:
                    results.add_result(
                        test_case['name'],
                        False,
                        f'Wrong error message: {error_msg}',
                    )
                    print(f'  {Colors.YELLOW}⚠️  PARTIAL: Rejected but wrong error{Colors.END}')
                    print(f'  Expected: "{test_case["expected_error"]}"')
                    print(f'  Got: "{error_msg}"\n')
            else:
                results.add_result(
                    test_case['name'],
                    False,
                    'Expected validation error but UUID was accepted',
                )
                print(f'  {Colors.RED}❌ FAIL: Should have been rejected{Colors.END}\n')


async def test_log_sanitization(results: TestResults):
    """Test that API keys are redacted in logs."""
    print(f'\n{Colors.BLUE}{Colors.BOLD}Testing Log Sanitization{Colors.END}')
    print(f'{Colors.BLUE}{"=" * 80}{Colors.END}\n')

    import subprocess

    # Get recent logs from the MCP server container
    try:
        result = subprocess.run(
            [
                'docker',
                'compose',
                '--profile',
                'falkordb',
                'logs',
                'graphiti-mcp-falkordb',
                '--tail',
                '200',
            ],
            capture_output=True,
            text=True,
            cwd='/Users/lvarming/projects/graphiti/mcp_server',
        )

        logs = result.stdout + result.stderr

        # Check for exposed API keys
        print('Checking logs for exposed secrets...\n')

        # Test 1: Check if actual API key is NOT in logs
        api_key_pattern = 'sk-proj-'
        if api_key_pattern in logs:
            # Check if it's actually the full key or just a redacted version
            import re

            # Look for full API keys (sk-proj- followed by many characters)
            full_key_pattern = r'sk-proj-[A-Za-z0-9_-]{100,}'
            matches = re.findall(full_key_pattern, logs)

            if matches:
                results.add_result(
                    'API Key Sanitization',
                    False,
                    f'Found {len(matches)} exposed API key(s) in logs',
                )
                print(f'  {Colors.RED}❌ FAIL: API keys found in logs!{Colors.END}')
                print(f'  Found {len(matches)} instance(s) of exposed keys\n')
            else:
                results.add_result(
                    'API Key Sanitization',
                    True,
                    'API keys properly redacted in logs',
                )
                print(f'  {Colors.GREEN}✅ PASS: No full API keys in logs{Colors.END}\n')
        else:
            results.add_result(
                'API Key Sanitization',
                True,
                'API keys properly redacted in logs',
            )
            print(f'  {Colors.GREEN}✅ PASS: No API key patterns in logs{Colors.END}\n')

        # Test 2: Check if [REDACTED] markers are present
        redacted_markers = [
            '[REDACTED_OPENAI_KEY]',
            '[REDACTED_TOKEN]',
            '[REDACTED]',
        ]

        found_redactions = []
        for marker in redacted_markers:
            if marker in logs:
                found_redactions.append(marker)

        if found_redactions:
            results.add_result(
                'Redaction Markers Present',
                True,
                f'Found redaction markers: {", ".join(found_redactions)}',
            )
            print(f'  {Colors.GREEN}✅ PASS: Redaction markers found in logs{Colors.END}')
            print(f'  Markers: {", ".join(found_redactions)}\n')
        else:
            # This is informational - no redactions might mean no sensitive data was logged
            print(f'  {Colors.YELLOW}ℹ️  INFO: No redaction markers found{Colors.END}')
            print(f'  (This is OK if no sensitive data was logged)\n')

        # Test 3: Overall log safety check
        print('Log sample (first 500 chars):')
        print(f'{Colors.YELLOW}{logs[:500]}...{Colors.END}\n')

    except Exception as e:
        results.add_result(
            'Log Sanitization Test',
            False,
            f'Failed to retrieve logs: {str(e)}',
        )
        print(f'  {Colors.RED}❌ FAIL: Could not retrieve logs{Colors.END}')
        print(f'  Error: {e}\n')


async def main():
    """Run all Session 1A tests."""
    print(f'\n{Colors.BOLD}{Colors.BLUE}{"=" * 80}{Colors.END}')
    print(f'{Colors.BOLD}{Colors.BLUE}SESSION 1A SECURITY TESTING{Colors.END}')
    print(f'{Colors.BOLD}{Colors.BLUE}{"=" * 80}{Colors.END}')
    print(f'\nTesting MCP server at: http://localhost:8001')
    print(f'Date: 2025-10-26\n')

    results = TestResults()
    client = MCPClient()

    # Run all tests
    await test_group_id_validation(client, results)
    await test_uuid_validation(client, results)
    await test_log_sanitization(results)

    # Print summary
    exit_code = results.print_summary()

    print(f'\n{Colors.BOLD}Session 1A Testing Complete{Colors.END}\n')
    sys.exit(exit_code)


if __name__ == '__main__':
    asyncio.run(main())
