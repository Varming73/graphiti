# Testing Guide: Dynamic Graph Discovery

## Overview
This guide covers testing the new dynamic graph discovery feature with strict mode for the Graphiti MCP server.

## Prerequisites

1. **FalkorDB running:**
   ```bash
   docker run -p 6379:6379 -p 3000:3000 -it --rm falkordb/falkordb:latest
   ```

2. **MCP server dependencies installed:**
   ```bash
   pip install falkordb graphiti-core mcp
   ```

3. **Server started:**
   ```bash
   python mcp_server/graphiti_mcp_server.py --group-id default --strict-graphs
   ```

## Test Scenarios

### Test 1: Empty State - List Graphs
**Purpose:** Verify list_graphs() works with no graphs

**Steps:**
1. Call `list_graphs()` tool
2. Verify response shows empty list
3. Verify helpful message about creating first graph

**Expected Response:**
```json
{
  "graphs": [],
  "message": "No graphs exist yet. Create one with create_graph().",
  "guidelines": {
    "naming": "Use lowercase with hyphens (e.g., 'ai-research')",
    "reuse": "Always reuse existing graphs when content matches"
  }
}
```

**Pass/Fail:** ✓ / ✗

---

### Test 2: Graph Creation - Valid Name
**Purpose:** Verify create_graph() works with valid input

**Steps:**
1. Call `create_graph("ai-research", "AI and machine learning research notes")`
2. Verify success response
3. Call `list_graphs()` to confirm it exists

**Expected Response:**
```json
{
  "status": "success",
  "graph_id": "ai-research",
  "message": "Graph 'ai-research' created successfully",
  "description": "AI and machine learning research notes",
  "usage": "Use group_id='ai-research' in add_episode() and other tools"
}
```

**Pass/Fail:** ✓ / ✗

---

### Test 3: Graph Creation - Invalid Names
**Purpose:** Verify validation rejects bad names

**Test 3a: Uppercase letters**
```
create_graph("AI-Research", "...")
Expected: Error about lowercase only
```

**Test 3b: Spaces**
```
create_graph("ai research", "...")
Expected: Error about valid characters
```

**Test 3c: Special characters**
```
create_graph("ai_research!", "...")
Expected: Error about valid characters
```

**Test 3d: Too short**
```
create_graph("a", "...")
Expected: Error about length
```

**Test 3e: Reserved name**
```
create_graph("default", "...")
Expected: Error about reserved name
```

**Pass/Fail:** ✓ / ✗

---

### Test 4: Duplicate Graph Creation
**Purpose:** Verify cannot create duplicate graphs

**Steps:**
1. Create graph: `create_graph("test-graph", "Test")`
2. Try to create same graph again
3. Verify error response

**Expected Response:**
```json
{
  "status": "error",
  "error": "Graph 'test-graph' already exists",
  "suggestion": "Use group_id='test-graph' in add_episode() and other tools"
}
```

**Pass/Fail:** ✓ / ✗

---

### Test 5: Add Episode - Non-existent Graph (Strict Mode)
**Purpose:** Verify strict mode prevents using non-existent graphs

**Steps:**
1. Call `add_episode()` with `group_id="nonexistent"`
2. Verify error response with helpful suggestions

**Expected Response:**
```json
{
  "status": "error",
  "error": "Graph 'nonexistent' does not exist",
  "suggestion": "Create it first with create_graph('nonexistent', 'description')",
  "available_graphs": ["ai-research"],
  "hint": "Call list_graphs() to see all available graphs with descriptions"
}
```

**Pass/Fail:** ✓ / ✗

---

### Test 6: Add Episode - Valid Graph
**Purpose:** Verify episodes can be added to existing graphs

**Steps:**
1. Create graph: `create_graph("test", "Test graph")`
2. Add episode:
   ```
   add_episode(
       name="Test Episode",
       episode_body="This is test content",
       group_id="test"
   )
   ```
3. Verify success response

**Expected Response:**
```json
{
  "status": "success",
  "graph_used": "test",
  "message": "Episode 'Test Episode' added to 'test' graph",
  "episode_name": "Test Episode"
}
```

**Pass/Fail:** ✓ / ✗

---

### Test 7: Add Episode - Default Graph
**Purpose:** Verify default graph works when group_id not specified

**Steps:**
1. Add episode without group_id:
   ```
   add_episode(
       name="Default Episode",
       episode_body="This goes to default graph"
   )
   ```
2. Verify it uses server's default graph

**Expected:** Success with `graph_used: "default"`

**Pass/Fail:** ✓ / ✗

---

### Test 8: Graph Isolation
**Purpose:** Verify data isolation between graphs

**Steps:**
1. Create two graphs:
   - `create_graph("graph-a", "Graph A")`
   - `create_graph("graph-b", "Graph B")`
2. Add episode to graph-a:
   ```
   add_episode(
       name="Episode A",
       episode_body="Unique content in A with keyword: ELEPHANT",
       group_id="graph-a"
   )
   ```
3. Add episode to graph-b:
   ```
   add_episode(
       name="Episode B", 
       episode_body="Different content in B",
       group_id="graph-b"
   )
   ```
4. Search in graph-a for "ELEPHANT": `search("ELEPHANT", group_id="graph-a")`
5. Search in graph-b for "ELEPHANT": `search("ELEPHANT", group_id="graph-b")`

**Expected:**
- Search in graph-a: Finds Episode A
- Search in graph-b: Finds nothing (or Episode B but not A)

**Pass/Fail:** ✓ / ✗

---

### Test 9: List Graphs - Multiple Graphs
**Purpose:** Verify list_graphs() shows all graphs with metadata

**Steps:**
1. Create multiple graphs with different purposes
2. Add episodes to each
3. Call `list_graphs()`
4. Verify all graphs shown with stats

**Expected Response:**
```json
{
  "graphs": [
    {
      "graph_id": "ai-research",
      "description": "AI and ML research notes",
      "created_at": "2025-10-26T10:30:00",
      "node_count": 5,
      "edge_count": 12
    },
    {
      "graph_id": "personal",
      "description": "Personal notes and ideas",
      "created_at": "2025-10-26T10:35:00",
      "node_count": 3,
      "edge_count": 7
    }
  ],
  "count": 2,
  "guidelines": {...}
}
```

**Pass/Fail:** ✓ / ✗

---

### Test 10: Search - Non-existent Graph
**Purpose:** Verify search validates graph existence

**Steps:**
1. Call `search("query", group_id="nonexistent")`
2. Verify error response

**Expected Response:**
```json
{
  "status": "error",
  "error": "Graph 'nonexistent' does not exist",
  "available_graphs": [...]
}
```

**Pass/Fail:** ✓ / ✗

---

### Test 11: Invalid Reference Time
**Purpose:** Verify reference_time validation

**Steps:**
1. Try to add episode with invalid timestamp:
   ```
   add_episode(
       name="Test",
       episode_body="Content",
       reference_time="not-a-timestamp",
       group_id="test"
   )
   ```
2. Verify helpful error message

**Expected:** Error with hint about ISO format

**Pass/Fail:** ✓ / ✗

---

### Test 12: FalkorDB Connection Failure
**Purpose:** Verify graceful handling of FalkorDB issues

**Steps:**
1. Stop FalkorDB: `docker stop <container_id>`
2. Try to call `list_graphs()`
3. Verify error message (not crash)

**Expected:** JSON error response, not Python traceback

**Pass/Fail:** ✓ / ✗

---

## Integration Testing

### Workflow Test: AI Creating New Domain

**Scenario:** User asks AI to store content in new domain

**Steps:**
1. User: "Store this AI research note about transformers"
2. AI calls `list_graphs()` - sees no "ai-research" graph
3. AI asks user: "Should I create an 'ai-research' graph?"
4. User: "Yes"
5. AI calls `create_graph("ai-research", "AI/ML research notes")`
6. AI calls `add_episode(..., group_id="ai-research")`
7. Verify success

**Pass/Fail:** ✓ / ✗

---

### Workflow Test: AI Reusing Existing Graph

**Scenario:** User asks to store content that matches existing graph

**Steps:**
1. Graph "restaurants" already exists
2. User: "Store this restaurant review"
3. AI calls `list_graphs()` - sees "restaurants"
4. AI directly calls `add_episode(..., group_id="restaurants")`
5. No graph creation needed

**Pass/Fail:** ✓ / ✗

---

### Workflow Test: AI Prevented from Auto-creation

**Scenario:** Strict mode prevents silent graph creation

**Steps:**
1. User: "Store this finance tip"
2. AI tries `add_episode(..., group_id="finance")`
3. Gets error: graph doesn't exist
4. AI asks user about creating "finance" graph
5. User decides (yes/no/use different graph)

**Pass/Fail:** ✓ / ✗

---

## Performance Testing

### Test 13: Many Graphs
**Purpose:** Verify performance with multiple graphs

**Steps:**
1. Create 20 graphs
2. Call `list_graphs()`
3. Measure response time

**Expected:** < 500ms

**Pass/Fail:** ✓ / ✗

---

### Test 14: Large Graph
**Purpose:** Verify performance with large graph

**Steps:**
1. Create graph with 1000+ episodes
2. Call `list_graphs()`
3. Verify node/edge counts correct

**Pass/Fail:** ✓ / ✗

---

## Cleanup

After testing:
```bash
# Stop FalkorDB
docker stop <container_id>

# Clear data (if needed)
rm -rf ./data
```

## Test Summary Template

```
Date: _____________
Tester: _____________

Total Tests: 14
Passed: ___
Failed: ___
Skipped: ___

Critical Issues:
1. 
2.

Minor Issues:
1.
2.

Notes:


```

## Automated Test Script

For automation, create `test_graph_discovery.py`:

```python
import asyncio
import json

async def run_tests():
    """Run all tests automatically"""
    
    results = {
        "passed": 0,
        "failed": 0,
        "errors": []
    }
    
    # Test 1: List empty graphs
    try:
        response = await list_graphs()
        data = json.loads(response)
        assert data["graphs"] == []
        results["passed"] += 1
    except Exception as e:
        results["failed"] += 1
        results["errors"].append(f"Test 1: {e}")
    
    # Test 2: Create valid graph
    try:
        response = await create_graph("test-graph", "Test")
        data = json.loads(response)
        assert data["status"] == "success"
        results["passed"] += 1
    except Exception as e:
        results["failed"] += 1
        results["errors"].append(f"Test 2: {e}")
    
    # Add more tests...
    
    print(f"\nTest Results:")
    print(f"Passed: {results['passed']}")
    print(f"Failed: {results['failed']}")
    if results['errors']:
        print("\nErrors:")
        for error in results['errors']:
            print(f"  - {error}")

if __name__ == "__main__":
    asyncio.run(run_tests())
```

---

**All tests should pass before merging to main!**
