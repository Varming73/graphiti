# Code Changes for Graphiti MCP Server
# Complete implementation of dynamic graph discovery with strict mode

import json
import re
from datetime import datetime
from falkordb import FalkorDB
from graphiti_core import Graphiti
from graphiti_core.nodes import EpisodeType

# =============================================================================
# MODULE-LEVEL ADDITIONS
# Add these at the top of mcp_server/graphiti_mcp_server.py after imports
# =============================================================================

# FalkorDB connection singleton
FALKORDB_CLIENT = None

def get_falkordb_connection():
    """Get or create FalkorDB connection
    
    Returns a singleton FalkorDB client for graph operations.
    """
    global FALKORDB_CLIENT
    if FALKORDB_CLIENT is None:
        FALKORDB_CLIENT = FalkorDB(
            host=args.falkordb_host,
            port=args.falkordb_port
        )
    return FALKORDB_CLIENT


# =============================================================================
# NEW TOOL: list_graphs()
# Add this as a new MCP tool
# =============================================================================

@mcp.tool()
async def list_graphs() -> str:
    """List all available knowledge graphs with metadata
    
    Dynamically discovers all existing graph namespaces from FalkorDB.
    ALWAYS call this before creating new graphs to avoid duplicates.
    
    Returns:
        JSON object containing:
        - graphs: List of graph objects with id, description, stats
        - count: Total number of graphs
        - guidelines: Best practices for graph usage
    
    Example response:
    {
        "graphs": [
            {
                "graph_id": "ai-research",
                "description": "AI and ML research notes",
                "created_at": "2025-10-26T10:30:00",
                "node_count": 142,
                "edge_count": 356
            }
        ],
        "count": 1,
        "guidelines": {...}
    }
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


# =============================================================================
# NEW TOOL: create_graph()
# Add this as a new MCP tool
# =============================================================================

@mcp.tool()
async def create_graph(
    graph_id: str,
    description: str
) -> str:
    """Create a new knowledge graph domain
    
    IMPORTANT: Only create new graphs when absolutely necessary.
    Always check list_graphs() first and reuse existing graphs.
    
    This is the ONLY way to create new graphs in strict mode.
    The graph will be created automatically by FalkorDB on first use.
    
    Args:
        graph_id: Unique identifier following naming rules:
                 - lowercase letters only
                 - numbers allowed
                 - hyphens allowed for separation
                 - 2-50 characters
                 Examples: "ai-research", "personal-notes", "work-projects"
        description: Clear purpose of this graph (helps future decisions)
                    This description will be shown in list_graphs() to help
                    users decide which graph to use for new content.
        
    Returns:
        JSON object with status and usage instructions
    
    Example usage:
        create_graph("ai-research", "AI and machine learning research notes")
    """
    # Validate naming convention
    if not re.match(r'^[a-z0-9-]+$', graph_id):
        return json.dumps({
            "status": "error",
            "error": "graph_id must be lowercase letters, numbers, and hyphens only",
            "examples": ["ai-research", "personal-notes", "work-projects"],
            "invalid_chars": "No uppercase, spaces, or special characters"
        }, indent=2)
    
    # Check length
    if len(graph_id) < 2 or len(graph_id) > 50:
        return json.dumps({
            "status": "error",
            "error": "graph_id must be between 2 and 50 characters",
            "provided_length": len(graph_id)
        }, indent=2)
    
    # Check for reserved names
    reserved_names = ['default', 'system', 'admin', 'root']
    if graph_id in reserved_names:
        return json.dumps({
            "status": "error",
            "error": f"'{graph_id}' is a reserved name",
            "reserved_names": reserved_names
        }, indent=2)
    
    try:
        db = get_falkordb_connection()
        existing_graphs = db.connection.execute_command('GRAPH.LIST')
        
        # Check if already exists
        if graph_id in existing_graphs:
            return json.dumps({
                "status": "error",
                "error": f"Graph '{graph_id}' already exists",
                "suggestion": f"Use group_id='{graph_id}' in add_episode() and other tools",
                "tip": "Call list_graphs() to see all existing graphs"
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
            "usage": f"Use group_id='{graph_id}' in add_episode() and other tools",
            "note": "Graph will be initialized in FalkorDB on first episode"
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": f"Failed to create graph: {str(e)}"
        }, indent=2)


# =============================================================================
# MODIFIED TOOL: add_episode()
# Replace the existing add_episode() with this version
# =============================================================================

@mcp.tool()
async def add_episode(
    name: str,
    episode_body: str,
    source: str = "text",
    source_description: str | None = None,
    reference_time: str | None = None,
    group_id: str | None = None,
) -> str:
    """Add an episode to the knowledge graph
    
    ⚠️ IMPORTANT WORKFLOW:
    1. FIRST call list_graphs() to see existing domains
    2. REUSE an existing graph if content matches (even roughly)
    3. ONLY create new graphs for truly distinct domains
    4. USE create_graph() explicitly if new domain needed
    
    Args:
        name: Episode name/title
        episode_body: The content to store in the knowledge graph
        source: Type of source - "text", "message", or "json"
        source_description: Optional description of the source
        reference_time: Optional ISO format timestamp (e.g., "2025-10-26T10:30:00")
                       If not provided, uses current time
        group_id: Graph domain identifier. MUST be an existing graph from list_graphs().
                 Examples: "ai-research", "personal", "work-projects"
                 
                 If not provided, uses the server's default graph.
                 To see available graphs, call list_graphs().
                 To create a new graph, use create_graph() first.
    
    Returns:
        JSON object with status, graph used, and confirmation message
    
    Example:
        add_episode(
            name="Transformer Architecture",
            episode_body="Attention is all you need...",
            group_id="ai-research"
        )
    """
    # Determine which graph to use
    actual_graph_name = group_id if group_id else args.group_id
    
    # STRICT MODE: Validate graph exists
    try:
        db = get_falkordb_connection()
        existing_graphs = db.connection.execute_command('GRAPH.LIST')
        
        # Check if graph exists (unless it's the default)
        if group_id and actual_graph_name not in existing_graphs and actual_graph_name != args.group_id:
            return json.dumps({
                "status": "error",
                "error": f"Graph '{actual_graph_name}' does not exist",
                "suggestion": f"Create it first with create_graph('{actual_graph_name}', 'description')",
                "available_graphs": list(existing_graphs),
                "hint": "Call list_graphs() to see all available graphs with descriptions"
            }, indent=2)
        
    except Exception as e:
        # If we can't check, log but continue (fail open)
        print(f"Warning: Could not validate graph existence: {e}")
    
    # Initialize Graphiti with the specific graph_name
    # This is the KEY change - FalkorDB handles isolation natively
    try:
        graphiti = Graphiti(
            uri=f"falkor://{args.falkordb_host}:{args.falkordb_port}",
            graph_name=actual_graph_name,  # CRITICAL: This enables multi-tenancy
            # Add your existing Graphiti config here
            # llm_provider=args.llm_provider,
            # embedding_provider=args.embedding_provider,
            # etc.
        )
        
        # Parse reference time if provided
        ref_time = None
        if reference_time:
            try:
                ref_time = datetime.fromisoformat(reference_time)
            except ValueError as e:
                return json.dumps({
                    "status": "error",
                    "error": f"Invalid reference_time format: {str(e)}",
                    "hint": "Use ISO format like '2025-10-26T10:30:00'"
                }, indent=2)
        
        # Add the episode to Graphiti
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
            "message": f"Episode '{name}' added to '{actual_graph_name}' graph",
            "episode_name": name
        }, indent=2)
        
    except KeyError:
        return json.dumps({
            "status": "error",
            "error": f"Invalid source type: {source}",
            "valid_sources": ["text", "message", "json"]
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": str(e),
            "graph": actual_graph_name
        }, indent=2)


# =============================================================================
# MODIFIED TOOL: search()
# Apply same pattern to search tool
# =============================================================================

@mcp.tool()
async def search(
    query: str,
    group_id: str | None = None,
) -> str:
    """Search for information in the knowledge graph
    
    Args:
        query: Search query in natural language
        group_id: Optional graph to search in. If not provided, searches default graph.
                 Call list_graphs() to see available graphs.
    
    Returns:
        JSON with search results from the specified graph
    """
    actual_graph_name = group_id if group_id else args.group_id
    
    # Validate graph exists
    try:
        db = get_falkordb_connection()
        existing_graphs = db.connection.execute_command('GRAPH.LIST')
        
        if group_id and actual_graph_name not in existing_graphs:
            return json.dumps({
                "status": "error",
                "error": f"Graph '{actual_graph_name}' does not exist",
                "available_graphs": list(existing_graphs)
            }, indent=2)
    except Exception as e:
        print(f"Warning: Could not validate graph: {e}")
    
    try:
        # Create Graphiti instance for this graph
        graphiti = Graphiti(
            uri=f"falkor://{args.falkordb_host}:{args.falkordb_port}",
            graph_name=actual_graph_name,
            # ... your config
        )
        
        # Perform search
        results = await graphiti.search(query)
        
        return json.dumps({
            "status": "success",
            "graph_searched": actual_graph_name,
            "query": query,
            "results": results
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": str(e),
            "graph": actual_graph_name
        }, indent=2)


# =============================================================================
# CLI ARGUMENT MODIFICATIONS
# Update the argument parser section
# =============================================================================

# In the argparse section, modify or add these arguments:

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

parser.add_argument(
    "--falkordb-host",
    type=str,
    default="localhost",
    help="FalkorDB host address"
)

parser.add_argument(
    "--falkordb-port",
    type=int,
    default=6379,
    help="FalkorDB port"
)


# =============================================================================
# PATTERN FOR OTHER TOOLS
# Apply this pattern to all other tools that interact with the graph:
# - get_nodes()
# - get_edges()
# - Any other graph operations
# =============================================================================

"""
Standard pattern for adding group_id support:

1. Add group_id parameter (optional, default None)
2. Determine actual graph name: group_id or args.group_id
3. Validate graph exists (in strict mode)
4. Create Graphiti instance with graph_name parameter
5. Perform operation
6. Return result with graph name included

Example template:

@mcp.tool()
async def your_tool(
    # ... existing params
    group_id: str | None = None,
) -> str:
    actual_graph_name = group_id if group_id else args.group_id
    
    # Validate
    db = get_falkordb_connection()
    existing_graphs = db.connection.execute_command('GRAPH.LIST')
    if group_id and actual_graph_name not in existing_graphs:
        return json.dumps({"error": "Graph does not exist"})
    
    # Use
    graphiti = Graphiti(
        uri=f"falkor://{args.falkordb_host}:{args.falkordb_port}",
        graph_name=actual_graph_name,
        # ... config
    )
    
    # Operate
    result = await graphiti.your_operation()
    
    return json.dumps({
        "graph_used": actual_graph_name,
        "result": result
    })
"""
