# Dynamic Graph Discovery Implementation Guide

## Overview
This guide provides step-by-step instructions for adding client-defined `group_id` support to the Graphiti MCP server using FalkorDB's native multi-tenancy.

## Architecture Decision
**NO instance pooling needed** - FalkorDB natively supports multiple isolated graphs through the `graph_name` parameter. Simply pass different `graph_name` values to Graphiti and FalkorDB handles the isolation.

## Key Changes Required

### 1. Add FalkorDB Connection Helper
**File:** `mcp_server/graphiti_mcp_server.py`

Add a module-level FalkorDB connection manager:

```python
from falkordb import FalkorDB

# Add at module level (after imports)
FALKORDB_CLIENT = None

def get_falkordb_connection():
    """Get or create FalkorDB connection"""
    global FALKORDB_CLIENT
    if FALKORDB_CLIENT is None:
        FALKORDB_CLIENT = FalkorDB(
            host=args.falkordb_host,
            port=args.falkordb_port
        )
    return FALKORDB_CLIENT
```

### 2. Add `list_graphs()` Tool
**Purpose:** Dynamic discovery of existing graphs
**Strict mode behavior:** Shows what graphs exist, prevents accidental duplication

```python
@mcp.tool()
async def list_graphs() -> str:
    """List all available knowledge graphs with metadata
    
    Dynamically discovers all existing graph namespaces from FalkorDB.
    ALWAYS call this before creating new graphs to avoid duplicates.
    
    Returns:
        JSON list of graphs with descriptions and statistics
    """
    try:
        db = get_falkordb_connection()
        
        # Use GRAPH.LIST command to get all graphs
        graph_list = db.connection.execute_command('GRAPH.LIST')
        
        # Get metadata for each graph
        graphs_info = []
        for graph_name in graph_list:
            try:
                # Get graph statistics
                g = db.select_graph(graph_name)
                info = g.connection.execute_command('GRAPH.INFO', graph_name)
                
                # Parse info (returns list: [key1, value1, key2, value2, ...])
                info_dict = {}
                for i in range(0, len(info), 2):
                    info_dict[info[i]] = info[i + 1]
                
                # Get stored metadata if exists
                metadata_key = f"graph_metadata:{graph_name}"
                metadata_str = db.connection.get(metadata_key)
                metadata = json.loads(metadata_str) if metadata_str else {}
                
                graphs_info.append({
                    "graph_id": graph_name,
                    "description": metadata.get("description", "No description available"),
                    "created_at": metadata.get("created_at", ""),
                    "node_count": info_dict.get("Node count", 0),
                    "edge_count": info_dict.get("Edge count", 0)
                })
            except Exception as e:
                graphs_info.append({
                    "graph_id": graph_name,
                    "error": f"Could not fetch info: {str(e)}"
                })
        
        if not graphs_info:
            return json.dumps({
                "graphs": [],
                "message": "No graphs exist yet. Create one with create_graph().",
                "guidelines": {
                    "naming": "Use lowercase with hyphens (e.g., 'ai-research')",
                    "reuse": "Always reuse existing graphs when content matches"
                }
            }, indent=2)
        
        return json.dumps({
            "graphs": graphs_info,
            "count": len(graphs_info),
            "guidelines": {
                "reuse": "Always use existing graphs when content matches the description",
                "naming": "Use lowercase with hyphens (e.g., 'ai-research', not 'AI Research')",
                "create": "Only create new graphs for distinctly different domains"
            }
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "error": f"Failed to list graphs: {str(e)}"
        }, indent=2)
```

### 3. Add `create_graph()` Tool
**Purpose:** Explicit graph creation with validation
**Strict mode behavior:** Only way to create new graphs

```python
import re
from datetime import datetime

@mcp.tool()
async def create_graph(
    graph_id: str,
    description: str
) -> str:
    """Create a new knowledge graph domain
    
    IMPORTANT: Only create new graphs when absolutely necessary.
    Always check list_graphs() first and reuse existing graphs.
    
    Args:
        graph_id: Unique identifier (lowercase, hyphens only, e.g., 'ai-research')
        description: Clear purpose of this graph (helps future decisions about what to store where)
        
    Returns:
        Confirmation or error if graph exists
    """
    # Validate naming convention
    if not re.match(r'^[a-z0-9-]+$', graph_id):
        return json.dumps({
            "status": "error",
            "error": "graph_id must be lowercase letters, numbers, and hyphens only",
            "examples": ["ai-research", "personal-notes", "work-projects"]
        }, indent=2)
    
    # Check length
    if len(graph_id) < 2 or len(graph_id) > 50:
        return json.dumps({
            "status": "error",
            "error": "graph_id must be between 2 and 50 characters"
        }, indent=2)
    
    try:
        db = get_falkordb_connection()
        existing_graphs = db.connection.execute_command('GRAPH.LIST')
        
        # Check if already exists
        if graph_id in existing_graphs:
            return json.dumps({
                "status": "error",
                "error": f"Graph '{graph_id}' already exists",
                "suggestion": f"Use group_id='{graph_id}' in add_episode() and other tools"
            }, indent=2)
        
        # Store metadata about the graph
        metadata = {
            "description": description,
            "created_at": datetime.now().isoformat(),
            "episode_count": 0
        }
        metadata_key = f"graph_metadata:{graph_id}"
        db.connection.set(metadata_key, json.dumps(metadata))
        
        return json.dumps({
            "status": "success",
            "graph_id": graph_id,
            "message": f"Graph '{graph_id}' created successfully",
            "description": description,
            "usage": f"Use group_id='{graph_id}' in add_episode() and other tools"
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": f"Failed to create graph: {str(e)}"
        }, indent=2)
```

### 4. Modify All Existing Tools
**Add `group_id` parameter and validation to:**
- `add_episode()`
- `search()`
- `get_nodes()`
- `get_edges()`
- Any other tools that interact with the graph

**Pattern for each tool:**

```python
@mcp.tool()
async def add_episode(
    name: str,
    episode_body: str,
    source: str = "text",
    source_description: str | None = None,
    reference_time: str | None = None,
    group_id: str | None = None,  # NEW PARAMETER
) -> str:
    """Add an episode to the knowledge graph
    
    ⚠️ IMPORTANT WORKFLOW:
    1. FIRST call list_graphs() to see existing domains
    2. REUSE an existing graph if content matches (even roughly)
    3. ONLY create new graphs for truly distinct domains
    4. USE create_graph() explicitly if new domain needed
    
    Args:
        name: Episode name
        episode_body: Content of the episode
        source: Type of source (text, message, json)
        source_description: Optional description
        reference_time: Optional ISO format timestamp
        group_id: Graph domain identifier. Must be an existing graph from list_graphs().
                 Examples: "ai-research", "personal", "work"
                 If not provided, uses server default.
    
    Returns:
        Confirmation with graph used
    """
    # Determine which graph to use
    actual_graph_name = group_id if group_id else args.group_id
    
    # STRICT MODE: Check if graph exists
    db = get_falkordb_connection()
    existing_graphs = db.connection.execute_command('GRAPH.LIST')
    
    if group_id and actual_graph_name not in existing_graphs and actual_graph_name != args.group_id:
        return json.dumps({
            "status": "error",
            "error": f"Graph '{actual_graph_name}' does not exist",
            "suggestion": f"Create it first with create_graph('{actual_graph_name}', 'description')",
            "available_graphs": list(existing_graphs),
            "hint": "Call list_graphs() to see all options"
        }, indent=2)
    
    # Initialize Graphiti with the specific graph_name
    # KEY CHANGE: Pass graph_name parameter to Graphiti
    graphiti = Graphiti(
        uri=f"falkor://{args.falkordb_host}:{args.falkordb_port}",
        graph_name=actual_graph_name,  # This is the critical line
        # ... rest of your existing config (llm_provider, etc.)
    )
    
    try:
        # Parse reference time if provided
        ref_time = None
        if reference_time:
            ref_time = datetime.fromisoformat(reference_time)
        
        # Add the episode
        await graphiti.add_episode(
            name=name,
            episode_body=episode_body,
            source=EpisodeType[source],
            source_description=source_description,
            reference_time=ref_time
        )
        
        return json.dumps({
            "status": "success",
            "graph_used": actual_graph_name,
            "message": f"Episode '{name}' added to '{actual_graph_name}' graph"
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": str(e),
            "graph": actual_graph_name
        }, indent=2)
```

### 5. Update CLI Arguments
**File:** `mcp_server/graphiti_mcp_server.py`

Modify the argument parser:

```python
parser.add_argument(
    "--group-id",
    type=str,
    default="default",
    help="Default graph ID for operations. Can be overridden per-request via group_id parameter for domain isolation."
)

parser.add_argument(
    "--strict-graphs",
    action="store_true",
    default=True,
    help="Require graphs to exist before use (prevents auto-creation). Recommended for most users."
)
```

## Implementation Order

1. **Add FalkorDB connection helper** (5 min)
2. **Add `list_graphs()` tool** (10 min)
3. **Add `create_graph()` tool** (10 min)
4. **Modify `add_episode()` tool** (15 min)
5. **Modify remaining tools** (20 min each)
6. **Update CLI arguments** (5 min)
7. **Test everything** (30 min)

## Testing Checklist

- [ ] Start MCP server with `--group-id default`
- [ ] Call `list_graphs()` - should return empty list with helpful message
- [ ] Try `add_episode()` with `group_id="test"` - should fail with error
- [ ] Call `create_graph("ai-research", "AI research notes")`
- [ ] Call `list_graphs()` - should show ai-research
- [ ] Call `add_episode()` with `group_id="ai-research"` - should succeed
- [ ] Call `search()` with `group_id="ai-research"` - should find episode
- [ ] Call `create_graph("ai-research", "...")` - should fail (already exists)
- [ ] Try invalid graph names - should fail validation
- [ ] Create second graph and verify isolation

## Key Benefits

✅ **No instance pooling** - Simple, native FalkorDB integration  
✅ **Dynamic discovery** - `GRAPH.LIST` command queries actual database  
✅ **Strict mode** - AI must ask user before creating graphs  
✅ **No manual registry** - Zero maintenance overhead  
✅ **Scales to 10K+ graphs** - FalkorDB native multi-tenancy  
✅ **Clean error messages** - Natural user interaction checkpoints

## Files to Modify

1. **`mcp_server/graphiti_mcp_server.py`** - Main changes (all tools)
2. **`README.md`** - Document new `group_id` parameter
3. **`CLAUDE.md`** - Add context about multi-domain support (if exists)

## Dependencies Check

Ensure these are in `requirements.txt`:
```
falkordb>=4.0.0
graphiti-core>=0.3.0  # Check actual latest version
```

## Post-Implementation

After implementation:
1. Update documentation with examples
2. Add integration tests
3. Consider adding `delete_graph()` tool for cleanup
4. Consider adding `suggest_graph()` tool for AI assistance

---

**Ready for Claude Code to implement!** 🚀
