# Project Context: Dynamic Graph Discovery for Graphiti MCP Server

## What We're Building

Adding client-defined `group_id` support to the Graphiti MCP server to enable domain isolation without running multiple server instances. This is based on research showing context contamination and proactive interference in AI memory systems.

## Architecture Overview

### Key Insight
FalkorDB ALREADY supports multiple isolated graphs natively through the `graph_name` parameter. We don't need instance pooling - just pass different `graph_name` values to Graphiti!

### Design Decisions

**✅ What We're Doing:**
- Dynamic discovery via FalkorDB's `GRAPH.LIST` command
- Strict mode by default (graphs must exist before use)
- Natural user control through error messages
- Simple native integration (just pass `graph_name` to Graphiti)

**❌ What We're NOT Doing:**
- Instance pooling (unnecessary - FalkorDB handles this)
- Manual registry maintenance (query database directly)
- Auto-creation without permission (strict mode prevents this)

## Implementation Strategy

### Core Principle
**Error messages = permission system**

When the AI tries to use a non-existent graph, it gets an error that naturally prompts it to ask the user. This creates checkpoints without building complex permission logic.

### Three New Tools

1. **`list_graphs()`**
   - Calls FalkorDB's `GRAPH.LIST` command
   - Returns metadata from Redis keys
   - Shows descriptions to help AI/user choose

2. **`create_graph(graph_id, description)`**
   - Validates naming (lowercase, hyphens only)
   - Stores metadata in Redis
   - Only way to create graphs in strict mode

3. **Modified existing tools** (add_episode, search, etc.)
   - Add optional `group_id` parameter
   - Validate graph exists (strict mode)
   - Pass `graph_name` to Graphiti

## Key Technical Details

### FalkorDB Commands Used
```python
# List all graphs
graph_list = db.connection.execute_command('GRAPH.LIST')

# Get graph info
info = db.connection.execute_command('GRAPH.INFO', graph_name)

# Store metadata
db.connection.set(f"graph_metadata:{graph_id}", json.dumps(metadata))
```

### Graphiti Integration
```python
# The magic line - FalkorDB handles isolation
graphiti = Graphiti(
    uri=f"falkor://{host}:{port}",
    graph_name=actual_graph_name,  # Different graphs = isolated data
    # ... other config
)
```

## File Structure

```
mcp_server/
├── graphiti_mcp_server.py  # Main changes here
│   ├── get_falkordb_connection()  # NEW: Connection helper
│   ├── list_graphs()              # NEW: Discovery tool
│   ├── create_graph()             # NEW: Creation tool
│   ├── add_episode()              # MODIFIED: Add group_id
│   ├── search()                   # MODIFIED: Add group_id
│   └── [other tools]              # MODIFIED: Add group_id
└── README.md                      # Update with examples
```

## User Experience Flow

### Scenario 1: Creating New Graph
```
User: "Store this AI research note"
AI: Calls list_graphs() → sees no "ai-research"
AI: "Should I create an 'ai-research' graph?"
User: "Yes"
AI: Calls create_graph("ai-research", "AI/ML research")
AI: Calls add_episode(..., group_id="ai-research")
```

### Scenario 2: Reusing Existing Graph
```
User: "Store this restaurant review"
AI: Calls list_graphs() → sees "restaurants"
AI: Calls add_episode(..., group_id="restaurants")
```

### Scenario 3: Prevented Auto-creation
```
User: "Store this finance tip"
AI: Tries add_episode(..., group_id="finance")
Error: "Graph 'finance' does not exist"
AI: "The finance graph doesn't exist yet. Should I create it?"
User: "No, use ai-research instead"
AI: Calls add_episode(..., group_id="ai-research")
```

## Testing Strategy

1. **Unit tests:** Each tool works correctly
2. **Validation tests:** Rejects invalid inputs
3. **Isolation tests:** Graphs are actually isolated
4. **Integration tests:** Full AI workflows
5. **Performance tests:** Many graphs, large graphs

See TESTING_GUIDE.md for complete test scenarios.

## Code Patterns

### Standard Tool Modification Pattern
```python
@mcp.tool()
async def your_tool(
    # ... existing params
    group_id: str | None = None,
) -> str:
    # 1. Determine graph
    actual_graph_name = group_id if group_id else args.group_id
    
    # 2. Validate exists (strict mode)
    db = get_falkordb_connection()
    existing_graphs = db.connection.execute_command('GRAPH.LIST')
    if group_id and actual_graph_name not in existing_graphs:
        return json.dumps({"error": "Graph does not exist"})
    
    # 3. Use specific graph
    graphiti = Graphiti(
        uri=f"falkor://{args.falkordb_host}:{args.falkordb_port}",
        graph_name=actual_graph_name,
        # ... config
    )
    
    # 4. Do operation
    result = await graphiti.your_operation()
    
    return json.dumps({
        "graph_used": actual_graph_name,
        "result": result
    })
```

## Dependencies

```
falkordb>=4.0.0
graphiti-core>=0.3.0
mcp>=0.1.0
```

## Research Basis

This design is based on research showing:
- Context contamination in AI memory systems
- Proactive interference across domains
- Benefits of domain separation for retrieval precision

References:
- arxiv.org/abs/2506.08184
- arxiv.org/abs/2509.19517

## Benefits

1. **Research-backed:** Domain separation improves retrieval
2. **User control:** AI must ask before creating graphs
3. **Zero maintenance:** No manual registry to update
4. **Scalable:** FalkorDB supports 10K+ graphs
5. **Simple:** Native multi-tenancy, no pooling
6. **Clean:** Error messages create natural checkpoints

## Common Pitfalls to Avoid

❌ Don't create instance pooling (FalkorDB handles this)
❌ Don't use manual registries (query database directly)
❌ Don't allow silent graph creation (strict mode)
❌ Don't forget validation in every tool
❌ Don't make graph names case-sensitive or complex

✅ Do use FalkorDB's native features
✅ Do validate graph existence
✅ Do provide helpful error messages
✅ Do use consistent naming (lowercase, hyphens)
✅ Do store metadata for discovery

## Next Steps After Implementation

1. Document in README with examples
2. Add integration tests
3. Consider optional `delete_graph()` tool
4. Consider `suggest_graph()` for AI assistance
5. Monitor usage patterns
6. Optimize metadata storage if needed

## Questions?

If you need clarification on any design decision, check:
1. This CLAUDE.md file
2. IMPLEMENTATION_GUIDE.md
3. code_changes.py for exact code
4. TESTING_GUIDE.md for validation

---

**Remember:** This is about enabling domain isolation with FalkorDB's native multi-tenancy. Keep it simple and let FalkorDB do the heavy lifting!
