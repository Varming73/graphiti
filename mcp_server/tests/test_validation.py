#!/usr/bin/env python3
"""
Test suite for input validation in Graphiti MCP Server.
Tests UUID validation and parameter bounds checking.
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))


class GraphitiValidationTest:
    """Test client for validating input validation in Graphiti MCP Server."""

    def __init__(self):
        self.test_group_id = f'test_validation_{int(time.time())}'
        self.session = None

    async def __aenter__(self):
        """Start the MCP client session."""
        # Find the main.py path relative to the tests directory
        main_path = Path(__file__).parent.parent / 'main.py'

        server_params = StdioServerParameters(
            command='uv',
            args=['run', str(main_path), '--transport', 'stdio'],
            env={
                'NEO4J_URI': os.environ.get('NEO4J_URI', 'bolt://localhost:7687'),
                'NEO4J_USER': os.environ.get('NEO4J_USER', 'neo4j'),
                'NEO4J_PASSWORD': os.environ.get('NEO4J_PASSWORD', 'graphiti'),
                'OPENAI_API_KEY': os.environ.get('OPENAI_API_KEY', 'dummy_key_for_testing'),
            },
        )

        print(f'🚀 Starting validation test with test group: {self.test_group_id}')

        self.client_context = stdio_client(server_params)
        read, write = await self.client_context.__aenter__()
        self.session = ClientSession(read, write)
        await self.session.initialize()

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close the MCP client session."""
        if self.session:
            await self.session.close()
        if hasattr(self, 'client_context'):
            await self.client_context.__aexit__(exc_type, exc_val, exc_tb)

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        """Call an MCP tool and return the result."""
        try:
            result = await self.session.call_tool(tool_name, arguments)
            return result.content[0].text if result.content else {'error': 'No content returned'}
        except Exception as e:
            return {'error': str(e)}

    def parse_response(self, response: Any) -> dict:
        """Parse response to extract error or success information."""
        if isinstance(response, dict):
            return response
        if isinstance(response, str):
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                return {'raw': response}
        return {'unknown': response}

    async def test_uuid_validation_add_memory(self) -> dict[str, bool]:
        """Test UUID validation in add_memory tool."""
        print('🔍 Testing UUID validation in add_memory...')
        results = {}

        # Test 1: Invalid UUID format (not a UUID at all)
        print('   Testing invalid UUID format (not a UUID)...')
        try:
            result = await self.call_tool(
                'add_memory',
                {
                    'name': 'Test Memory',
                    'episode_body': 'Test content',
                    'uuid': 'not-a-uuid',
                    'group_id': self.test_group_id,
                },
            )
            parsed = self.parse_response(result)
            has_error = 'error' in parsed or 'Invalid UUID' in str(result)

            if has_error:
                print(f'   ✅ Correctly rejected invalid UUID: {parsed.get("error", result)[:100]}')
                results['invalid_format'] = True
            else:
                print(f'   ❌ Failed to reject invalid UUID: {result}')
                results['invalid_format'] = False
        except Exception as e:
            print(f'   ❌ Test error: {e}')
            results['invalid_format'] = False

        # Test 2: Invalid UUID format (partial UUID)
        print('   Testing partial UUID...')
        try:
            result = await self.call_tool(
                'add_memory',
                {
                    'name': 'Test Memory',
                    'episode_body': 'Test content',
                    'uuid': '550e8400-e29b-41d4',  # Incomplete
                    'group_id': self.test_group_id,
                },
            )
            parsed = self.parse_response(result)
            has_error = 'error' in parsed or 'Invalid UUID' in str(result)

            if has_error:
                print(f'   ✅ Correctly rejected partial UUID')
                results['partial_uuid'] = True
            else:
                print(f'   ❌ Failed to reject partial UUID: {result}')
                results['partial_uuid'] = False
        except Exception as e:
            print(f'   ❌ Test error: {e}')
            results['partial_uuid'] = False

        # Test 3: Invalid UUID format (wrong characters)
        print('   Testing UUID with invalid characters...')
        try:
            result = await self.call_tool(
                'add_memory',
                {
                    'name': 'Test Memory',
                    'episode_body': 'Test content',
                    'uuid': '550e8400-XXXX-41d4-a716-446655440000',
                    'group_id': self.test_group_id,
                },
            )
            parsed = self.parse_response(result)
            has_error = 'error' in parsed or 'Invalid UUID' in str(result)

            if has_error:
                print(f'   ✅ Correctly rejected UUID with invalid characters')
                results['invalid_chars'] = True
            else:
                print(f'   ❌ Failed to reject UUID with invalid characters: {result}')
                results['invalid_chars'] = False
        except Exception as e:
            print(f'   ❌ Test error: {e}')
            results['invalid_chars'] = False

        # Test 4: Valid UUID (should succeed)
        print('   Testing valid UUID...')
        try:
            result = await self.call_tool(
                'add_memory',
                {
                    'name': 'Test Memory',
                    'episode_body': 'Test content',
                    'uuid': '550e8400-e29b-41d4-a716-446655440000',
                    'group_id': self.test_group_id,
                },
            )
            parsed = self.parse_response(result)
            has_error = 'error' in parsed and 'Invalid UUID' in str(result)

            if not has_error:
                print(f'   ✅ Correctly accepted valid UUID')
                results['valid_uuid'] = True
            else:
                print(f'   ❌ Incorrectly rejected valid UUID: {result}')
                results['valid_uuid'] = False
        except Exception as e:
            print(f'   ❌ Test error: {e}')
            results['valid_uuid'] = False

        return results

    async def test_uuid_validation_operations(self) -> dict[str, bool]:
        """Test UUID validation in delete and get operations."""
        print('🔍 Testing UUID validation in delete/get operations...')
        results = {}

        # Test delete_episode with invalid UUID
        print('   Testing delete_episode with invalid UUID...')
        try:
            result = await self.call_tool('delete_episode', {'uuid': 'invalid-uuid-123'})
            parsed = self.parse_response(result)
            has_error = 'error' in parsed or 'Invalid UUID' in str(result)

            if has_error:
                print(f'   ✅ delete_episode correctly rejected invalid UUID')
                results['delete_episode'] = True
            else:
                print(f'   ❌ delete_episode failed to reject invalid UUID')
                results['delete_episode'] = False
        except Exception as e:
            print(f'   ❌ Test error: {e}')
            results['delete_episode'] = False

        # Test delete_entity_edge with invalid UUID
        print('   Testing delete_entity_edge with invalid UUID...')
        try:
            result = await self.call_tool('delete_entity_edge', {'uuid': 'abc-123'})
            parsed = self.parse_response(result)
            has_error = 'error' in parsed or 'Invalid UUID' in str(result)

            if has_error:
                print(f'   ✅ delete_entity_edge correctly rejected invalid UUID')
                results['delete_entity_edge'] = True
            else:
                print(f'   ❌ delete_entity_edge failed to reject invalid UUID')
                results['delete_entity_edge'] = False
        except Exception as e:
            print(f'   ❌ Test error: {e}')
            results['delete_entity_edge'] = False

        # Test get_entity_edge with invalid UUID
        print('   Testing get_entity_edge with invalid UUID...')
        try:
            result = await self.call_tool('get_entity_edge', {'uuid': '12345'})
            parsed = self.parse_response(result)
            has_error = 'error' in parsed or 'Invalid UUID' in str(result)

            if has_error:
                print(f'   ✅ get_entity_edge correctly rejected invalid UUID')
                results['get_entity_edge'] = True
            else:
                print(f'   ❌ get_entity_edge failed to reject invalid UUID')
                results['get_entity_edge'] = False
        except Exception as e:
            print(f'   ❌ Test error: {e}')
            results['get_entity_edge'] = False

        # Test get_entity_connections with invalid UUID
        print('   Testing get_entity_connections with invalid UUID...')
        try:
            result = await self.call_tool(
                'get_entity_connections', {'entity_uuid': 'not-valid', 'max_connections': 10}
            )
            parsed = self.parse_response(result)
            has_error = 'error' in parsed or 'Invalid UUID' in str(result)

            if has_error:
                print(f'   ✅ get_entity_connections correctly rejected invalid UUID')
                results['get_entity_connections'] = True
            else:
                print(f'   ❌ get_entity_connections failed to reject invalid UUID')
                results['get_entity_connections'] = False
        except Exception as e:
            print(f'   ❌ Test error: {e}')
            results['get_entity_connections'] = False

        # Test get_entity_timeline with invalid UUID
        print('   Testing get_entity_timeline with invalid UUID...')
        try:
            result = await self.call_tool(
                'get_entity_timeline', {'entity_uuid': 'bad-uuid', 'max_episodes': 10}
            )
            parsed = self.parse_response(result)
            has_error = 'error' in parsed or 'Invalid UUID' in str(result)

            if has_error:
                print(f'   ✅ get_entity_timeline correctly rejected invalid UUID')
                results['get_entity_timeline'] = True
            else:
                print(f'   ❌ get_entity_timeline failed to reject invalid UUID')
                results['get_entity_timeline'] = False
        except Exception as e:
            print(f'   ❌ Test error: {e}')
            results['get_entity_timeline'] = False

        return results

    async def test_max_parameter_validation(self) -> dict[str, bool]:
        """Test max_* parameter validation."""
        print('🔍 Testing max_* parameter validation...')
        results = {}

        # Test 1: max_nodes exceeding limit
        print('   Testing max_nodes > 1000...')
        try:
            result = await self.call_tool(
                'search_memory_nodes',
                {
                    'query': 'test',
                    'group_ids': [self.test_group_id],
                    'max_nodes': 1001,  # Exceeds MAX_ALLOWED_RESULTS
                },
            )
            parsed = self.parse_response(result)
            has_error = 'error' in parsed or 'cannot exceed' in str(result)

            if has_error:
                print(f'   ✅ Correctly rejected max_nodes=1001')
                results['max_nodes_exceeded'] = True
            else:
                print(f'   ❌ Failed to reject max_nodes=1001')
                results['max_nodes_exceeded'] = False
        except Exception as e:
            print(f'   ❌ Test error: {e}')
            results['max_nodes_exceeded'] = False

        # Test 2: max_nodes = 0 (invalid)
        print('   Testing max_nodes = 0...')
        try:
            result = await self.call_tool(
                'search_memory_nodes',
                {'query': 'test', 'group_ids': [self.test_group_id], 'max_nodes': 0},
            )
            parsed = self.parse_response(result)
            has_error = 'error' in parsed or 'must be a positive' in str(result)

            if has_error:
                print(f'   ✅ Correctly rejected max_nodes=0')
                results['max_nodes_zero'] = True
            else:
                print(f'   ❌ Failed to reject max_nodes=0')
                results['max_nodes_zero'] = False
        except Exception as e:
            print(f'   ❌ Test error: {e}')
            results['max_nodes_zero'] = False

        # Test 3: max_nodes = -1 (invalid)
        print('   Testing max_nodes = -1...')
        try:
            result = await self.call_tool(
                'search_memory_nodes',
                {'query': 'test', 'group_ids': [self.test_group_id], 'max_nodes': -1},
            )
            parsed = self.parse_response(result)
            has_error = 'error' in parsed or 'must be a positive' in str(result)

            if has_error:
                print(f'   ✅ Correctly rejected max_nodes=-1')
                results['max_nodes_negative'] = True
            else:
                print(f'   ❌ Failed to reject max_nodes=-1')
                results['max_nodes_negative'] = False
        except Exception as e:
            print(f'   ❌ Test error: {e}')
            results['max_nodes_negative'] = False

        # Test 4: max_episodes exceeding limit
        print('   Testing max_episodes > 1000...')
        try:
            result = await self.call_tool(
                'get_episodes', {'group_id': self.test_group_id, 'max_episodes': 1500}
            )
            parsed = self.parse_response(result)
            has_error = 'error' in parsed or 'cannot exceed' in str(result)

            if has_error:
                print(f'   ✅ Correctly rejected max_episodes=1500')
                results['max_episodes_exceeded'] = True
            else:
                print(f'   ❌ Failed to reject max_episodes=1500')
                results['max_episodes_exceeded'] = False
        except Exception as e:
            print(f'   ❌ Test error: {e}')
            results['max_episodes_exceeded'] = False

        # Test 5: last_n exceeding limit
        print('   Testing last_n > 1000...')
        try:
            result = await self.call_tool(
                'get_episodes', {'group_id': self.test_group_id, 'last_n': 2000}
            )
            parsed = self.parse_response(result)
            has_error = 'error' in parsed or 'cannot exceed' in str(result)

            if has_error:
                print(f'   ✅ Correctly rejected last_n=2000')
                results['last_n_exceeded'] = True
            else:
                print(f'   ❌ Failed to reject last_n=2000')
                results['last_n_exceeded'] = False
        except Exception as e:
            print(f'   ❌ Test error: {e}')
            results['last_n_exceeded'] = False

        # Test 6: max_connections exceeding limit
        print('   Testing max_connections > 1000...')
        try:
            result = await self.call_tool(
                'get_entity_connections',
                {
                    'entity_uuid': '550e8400-e29b-41d4-a716-446655440000',
                    'max_connections': 1200,
                },
            )
            parsed = self.parse_response(result)
            has_error = 'error' in parsed or 'cannot exceed' in str(result)

            if has_error:
                print(f'   ✅ Correctly rejected max_connections=1200')
                results['max_connections_exceeded'] = True
            else:
                print(f'   ❌ Failed to reject max_connections=1200')
                results['max_connections_exceeded'] = False
        except Exception as e:
            print(f'   ❌ Test error: {e}')
            results['max_connections_exceeded'] = False

        # Test 7: Valid max_nodes value (should succeed)
        print('   Testing valid max_nodes=50...')
        try:
            result = await self.call_tool(
                'search_memory_nodes',
                {'query': 'test', 'group_ids': [self.test_group_id], 'max_nodes': 50},
            )
            parsed = self.parse_response(result)
            has_validation_error = (
                'error' in parsed and ('cannot exceed' in str(result) or 'must be a positive' in str(result))
            )

            if not has_validation_error:
                print(f'   ✅ Correctly accepted max_nodes=50')
                results['max_nodes_valid'] = True
            else:
                print(f'   ❌ Incorrectly rejected max_nodes=50')
                results['max_nodes_valid'] = False
        except Exception as e:
            print(f'   ❌ Test error: {e}')
            results['max_nodes_valid'] = False

        return results

    async def run_validation_tests(self) -> dict[str, Any]:
        """Run all validation tests."""
        print('🚀 Starting Graphiti MCP Server Validation Tests')
        print(f'   Test group ID: {self.test_group_id}')
        print('=' * 70)

        results = {
            'uuid_add_memory': {},
            'uuid_operations': {},
            'max_parameters': {},
            'overall_success': False,
        }

        # Test 1: UUID validation in add_memory
        results['uuid_add_memory'] = await self.test_uuid_validation_add_memory()
        print()

        # Test 2: UUID validation in other operations
        results['uuid_operations'] = await self.test_uuid_validation_operations()
        print()

        # Test 3: max_* parameter validation
        results['max_parameters'] = await self.test_max_parameter_validation()
        print()

        # Calculate overall success
        uuid_add_success = sum(results['uuid_add_memory'].values()) >= 3  # At least 3/4 tests passed
        uuid_ops_success = sum(results['uuid_operations'].values()) >= 4  # At least 4/5 tests passed
        max_param_success = sum(results['max_parameters'].values()) >= 6  # At least 6/7 tests passed

        results['overall_success'] = uuid_add_success and uuid_ops_success and max_param_success

        # Print comprehensive summary
        print('=' * 70)
        print('📊 VALIDATION TEST SUMMARY')
        print('-' * 35)

        uuid_add_stats = f'({sum(results["uuid_add_memory"].values())}/{len(results["uuid_add_memory"])} tests)'
        print(
            f'UUID Validation (add_memory):    {"✅ PASS" if uuid_add_success else "❌ FAIL"} {uuid_add_stats}'
        )

        uuid_ops_stats = f'({sum(results["uuid_operations"].values())}/{len(results["uuid_operations"])} tests)'
        print(
            f'UUID Validation (operations):    {"✅ PASS" if uuid_ops_success else "❌ FAIL"} {uuid_ops_stats}'
        )

        max_param_stats = f'({sum(results["max_parameters"].values())}/{len(results["max_parameters"])} tests)'
        print(
            f'Max Parameter Validation:        {"✅ PASS" if max_param_success else "❌ FAIL"} {max_param_stats}'
        )

        print('-' * 35)
        print(f'🎯 OVERALL RESULT: {"✅ SUCCESS" if results["overall_success"] else "❌ FAILED"}')

        if results['overall_success']:
            print('\n🎉 All validation tests passed!')
            print('   Input validation is working correctly.')
        else:
            print('\n⚠️  Some validation tests failed. Review the results above.')

        return results


async def main():
    """Run the validation tests."""
    try:
        async with GraphitiValidationTest() as test:
            results = await test.run_validation_tests()

            # Exit with appropriate code
            exit_code = 0 if results['overall_success'] else 1
            exit(exit_code)
    except Exception as e:
        print(f'❌ Test setup failed: {e}')
        import traceback
        traceback.print_exc()
        exit(1)


if __name__ == '__main__':
    asyncio.run(main())
