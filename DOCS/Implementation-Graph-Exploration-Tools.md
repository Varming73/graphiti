# Implementation Plan: Graph Exploration Tools for PKM

**Status:** Ready for Implementation
**Priority:** High
**Estimated Effort:** 1 hour
**Created:** 2025-11-15

## Executive Summary

Add two new MCP tools and improve documentation to enable effective Personal Knowledge Management (PKM) workflows with Graphiti. This addresses the perceived issue of "missing relations" by giving the LLM visibility into existing graph structure before adding new information.

## Background

### Problem Statement

User reported that Graphiti "doesn't update and form new relations as data is added." Initial investigation suggested reprocessing episodes to extract new relations.

### Critical Analysis

After investigating Graphiti's temporal architecture and use case analysis, we determined:

1. **Reprocessing is the wrong solution** - Episodes contain immutable text; reprocessing yields identical extractions
2. **Real issue is workflow, not architecture** - LLM lacks visibility into existing graph structure when adding new information
3. **Core features already exist** - Graphiti has powerful graph traversal methods not exposed through MCP

### Use Case Context

- **Scenario:** Conversational PKM system (extended memory/second brain)
- **Data Types:** Work projects, health tracking, personal notes
- **Access Pattern:** Real-time conversational data entry via MCP
- **Current Gap:** LLM cannot explore existing connections before adding new episodes

## Solution: Expose Existing Graph Traversal Features

### Recommended Implementation

#### 1. Add Two New MCP Tools (HIGH VALUE)

##### Tool 1: `get_entity_connections`

**Purpose:** Show ALL relationships connected to a specific entity

**Core Implementation:**
```python
@mcp.tool(
    annotations={
        'title': 'Get Entity Connections',
        'readOnlyHint': True,
        'destructiveHint': False,
        'idempotentHint': True,
        'openWorldHint': True,
    },
)
async def get_entity_connections(
    entity_uuid: str,
    group_ids: list[str] | None = None,
    max_connections: int = 50,
) -> FactSearchResponse | ErrorResponse:
    """Get ALL relationships/facts connected to a specific entity. **Direct graph traversal.**

    **PRIORITY: Use this to explore what's already known about an entity before adding new information.**

    Unlike search_memory_facts which requires a semantic query, this tool performs direct
    graph traversal to return every relationship where the specified entity is involved.

    WHEN TO USE THIS TOOL:
    - Exploring entity neighborhood → get_entity_connections (this tool) **USE THIS**
    - Before adding related information → get_entity_connections (this tool) **USE THIS**
    - Understanding entity context without formulating a query
    - Seeing the full relationship web around a concept

    Use Cases:
    - "Show me everything connected to the Django project"
    - "What relationships exist for my health issues?"
    - Before adding: "Let me see what's already known about X"
    - Exploring the knowledge graph structure

    Args:
        entity_uuid: UUID of the entity to explore (from search_nodes or previous results)
        group_ids: Optional list of memory namespaces to filter connections
        max_connections: Maximum number of relationships to return (default: 50)

    Returns:
        FactSearchResponse with all connected relationships, including temporal metadata

    Examples:
        # After finding an entity
        nodes = search_nodes(query="Django project")
        django_uuid = nodes[0]['uuid']

        # Get all connections
        get_entity_connections(entity_uuid=django_uuid)

        # Limited results
        get_entity_connections(
            entity_uuid=django_uuid,
            max_connections=20
        )
    """
    global graphiti_service

    if graphiti_service is None:
        return ErrorResponse(error='Graphiti service not initialized')

    try:
        client = await graphiti_service.get_client()

        # Use existing EntityEdge.get_by_node_uuid() method
        edges = await EntityEdge.get_by_node_uuid(client.driver, entity_uuid)

        # Filter by group_ids if provided
        if group_ids:
            edges = [e for e in edges if e.group_id in group_ids]

        # Limit results
        edges = edges[:max_connections]

        if not edges:
            return FactSearchResponse(
                message=f'No connections found for entity {entity_uuid}',
                facts=[]
            )

        # Format using existing formatter
        facts = [format_fact_result(edge) for edge in edges]

        return FactSearchResponse(
            message=f'Found {len(facts)} connections for entity',
            facts=facts
        )

    except Exception as e:
        error_msg = str(e)
        logger.error(f'Error getting entity connections: {error_msg}')
        return ErrorResponse(error=f'Error getting entity connections: {error_msg}')
```

**Leverages:** `graphiti_core/edges.py:456` - `EntityEdge.get_by_node_uuid()`

##### Tool 2: `get_entity_timeline`

**Purpose:** Show ALL episodes/conversations mentioning a specific entity

**Core Implementation:**
```python
@mcp.tool(
    annotations={
        'title': 'Get Entity Timeline',
        'readOnlyHint': True,
        'destructiveHint': False,
        'idempotentHint': True,
        'openWorldHint': True,
    },
)
async def get_entity_timeline(
    entity_uuid: str,
    group_ids: list[str] | None = None,
    max_episodes: int = 20,
) -> EpisodeSearchResponse | ErrorResponse:
    """Get all episodes/conversations that mention a specific entity. **Entity history.**

    **PRIORITY: Use this to understand how an entity evolved across conversations.**

    Returns all episodes where this entity was mentioned, in chronological order.
    Shows the full conversational history and temporal evolution of a concept.

    WHEN TO USE THIS TOOL:
    - Understanding entity history → get_entity_timeline (this tool) **USE THIS**
    - "When did we discuss X?" → get_entity_timeline (this tool) **USE THIS**
    - Seeing context across multiple conversations
    - Tracking how understanding evolved over time

    Use Cases:
    - "Show me all discussions about the Django project"
    - "When did I talk about this medication?"
    - "What conversations mentioned productivity issues?"
    - Understanding entity context from original sources

    Args:
        entity_uuid: UUID of the entity (from search_nodes or previous results)
        group_ids: Optional list of memory namespaces to filter episodes
        max_episodes: Maximum number of episodes to return (default: 20)

    Returns:
        EpisodeSearchResponse with episodes ordered chronologically

    Examples:
        # After finding an entity
        nodes = search_nodes(query="medication")
        med_uuid = nodes[0]['uuid']

        # Get conversation history
        get_entity_timeline(entity_uuid=med_uuid)

        # Limited to recent episodes
        get_entity_timeline(
            entity_uuid=med_uuid,
            max_episodes=10
        )
    """
    global graphiti_service

    if graphiti_service is None:
        return ErrorResponse(error='Graphiti service not initialized')

    try:
        client = await graphiti_service.get_client()

        # Use existing EpisodicNode.get_by_entity_node_uuid() method
        episodes = await EpisodicNode.get_by_entity_node_uuid(
            client.driver,
            entity_uuid
        )

        # Filter by group_ids if provided
        if group_ids:
            episodes = [e for e in episodes if e.group_id in group_ids]

        # Sort by valid_at (chronological order)
        episodes.sort(key=lambda e: e.valid_at)

        # Limit results
        episodes = episodes[:max_episodes]

        if not episodes:
            return EpisodeSearchResponse(
                message=f'No episodes found mentioning entity {entity_uuid}',
                episodes=[]
            )

        # Format episodes
        episode_results = []
        for ep in episodes:
            episode_results.append({
                'uuid': ep.uuid,
                'name': ep.name,
                'content': ep.content,
                'valid_at': ep.valid_at.isoformat() if ep.valid_at else None,
                'created_at': ep.created_at.isoformat() if ep.created_at else None,
                'source': ep.source.value if ep.source else None,
                'group_id': ep.group_id,
            })

        return EpisodeSearchResponse(
            message=f'Found {len(episode_results)} episodes mentioning entity',
            episodes=episode_results
        )

    except Exception as e:
        error_msg = str(e)
        logger.error(f'Error getting entity timeline: {error_msg}')
        return ErrorResponse(error=f'Error getting entity timeline: {error_msg}')
```

**Leverages:** `graphiti_core/nodes.py:415` - `EpisodicNode.get_by_entity_node_uuid()`

#### 2. Improve MCP Instructions (MEDIUM VALUE)

**Update `GRAPHITI_MCP_INSTRUCTIONS` in `mcp_server/src/graphiti_mcp_server.py`:**

```python
GRAPHITI_MCP_INSTRUCTIONS = """
Graphiti is a memory service for AI agents built on a knowledge graph. Graphiti performs well
with dynamic data such as user interactions, changing enterprise data, and external information.

Graphiti transforms information into a richly connected knowledge network, allowing you to
capture relationships between concepts, entities, and information. The system organizes data as episodes
(content snippets), nodes (entities), and facts (relationships between entities), creating a dynamic,
queryable memory store that evolves with new information.

Key capabilities:
1. Add episodes (text, messages, or JSON) to the knowledge graph with add_memory
2. Search for entities in the graph using search_nodes
3. Explore entity relationships with get_entity_connections
4. Track entity history across conversations with get_entity_timeline
5. Find relevant facts with search_memory_facts
6. Retrieve specific items by UUID or manage the graph

**RECOMMENDED WORKFLOW - SEARCH FIRST, THEN ADD:**

Before adding new information, ALWAYS explore what already exists:

1. **Search for existing entities:**
   search_nodes(query="relevant keywords") → find entities

2. **Explore connections:**
   get_entity_connections(entity_uuid="...") → see what's already linked

3. **Review history (optional):**
   get_entity_timeline(entity_uuid="...") → understand context

4. **Add with explicit references:**
   add_memory(
     name="...",
     episode_body="Started X, related to existing Y and Z"
   )

**Example - Adding Medication:**
```
❌ BAD (creates disconnected data):
add_memory(name="New med", episode_body="Started new medication")

✅ GOOD (creates rich connections):
1. search_nodes(query="medication health")
   → Finds: Metformin (diabetes), blood pressure condition
2. get_entity_connections(uuid="metformin_uuid")
   → Sees: connected to diabetes, side effects
3. add_memory(
     name="New medication",
     episode_body="Started Lisinopril for blood pressure, different from
                   my existing Metformin for diabetes. Will monitor interactions."
   )
```

**When to use each tool:**
- **Finding entities** → search_nodes
- **Exploring what's connected** → get_entity_connections (NEW)
- **Understanding entity history** → get_entity_timeline (NEW)
- **Searching relationships/content** → search_memory_facts
- **Adding information** → add_memory (AFTER searching)

The search-first pattern ensures that new information is automatically connected to existing
knowledge, creating a richly interconnected graph without manual reprocessing.

For temporal data: Graphiti tracks both when facts were true (domain time) and when they
were added to the graph (system time), enabling temporal queries and historical analysis.
"""
```

#### 3. Enhanced Tool Docstrings (LOW EFFORT)

**Update existing `add_memory` docstring to emphasize search-first:**

```python
async def add_memory(
    name: str,
    episode_body: str,
    ...
) -> SuccessResponse | ErrorResponse:
    """Add information to memory. **This is the PRIMARY method for storing information.**

    **IMPORTANT: SEARCH FIRST, THEN ADD**
    Before using this tool, search for related entities with search_nodes() and explore
    their connections with get_entity_connections(). Then reference found entities
    by name in your episode_body to create proper connections.

    **PRIORITY: Use this tool AFTER exploring existing knowledge.**

    ...rest of docstring...

    Best Practice Example:
        # 1. Search first
        existing = search_nodes(query="project django")
        connections = get_entity_connections(entity_uuid=existing[0]['uuid'])

        # 2. Add with context
        add_memory(
            name="Project update",
            episode_body="Django project now using PostgreSQL database,
                         as discussed previously with the team"
        )
    """
```

## Rejected Alternatives

### Alternative 1: Build Episode Reprocessing Tool
**Why Rejected:**
- Episodes contain immutable text - reprocessing yields identical results
- Expensive (re-runs LLM on all episodes)
- Doesn't solve the root problem (LLM needs visibility, not reprocessing)
- Wrong for conversational PKM use case

### Alternative 2: Build Community Clustering MCP Tool
**Why Rejected:**
- No clear trigger for when AI should call it
- Expensive with unclear value
- Current search doesn't use communities
- Better as manual admin operation

### Alternative 3: Automatic Relation Discovery
**Why Rejected:**
- Complex implementation
- Hard to control costs
- Unclear triggering logic
- May cause unexpected graph mutations

## Implementation Details

### File Changes

**File:** `mcp_server/src/graphiti_mcp_server.py`

1. Add imports (if not already present):
```python
from graphiti_core.nodes import EpisodicNode
```

2. Add two new tool functions after existing tools (~line 1240)
3. Update `GRAPHITI_MCP_INSTRUCTIONS` constant (~line 117)
4. Update `add_memory` docstring (~line 385)

**No changes to graphiti_core** - leverages existing features only

### Testing Plan

#### Manual Testing

1. **Test `get_entity_connections`:**
```python
# Setup: Add test data
add_memory(name="Test", episode_body="Django connects to PostgreSQL")
nodes = search_nodes(query="Django")
django_uuid = nodes[0]['uuid']

# Test: Get connections
connections = get_entity_connections(entity_uuid=django_uuid)

# Verify: Should return edge to PostgreSQL
assert len(connections['facts']) > 0
assert 'PostgreSQL' in str(connections['facts'])
```

2. **Test `get_entity_timeline`:**
```python
# Setup: Add multiple episodes
add_memory(name="Day 1", episode_body="Started Django project")
add_memory(name="Day 2", episode_body="Django project added tests")
nodes = search_nodes(query="Django")
django_uuid = nodes[0]['uuid']

# Test: Get timeline
timeline = get_entity_timeline(entity_uuid=django_uuid)

# Verify: Should return both episodes
assert len(timeline['episodes']) == 2
assert timeline['episodes'][0]['name'] == "Day 1"  # chronological
```

3. **Test search-first workflow:**
```python
# Workflow test
nodes = search_nodes(query="existing entity")
connections = get_entity_connections(entity_uuid=nodes[0]['uuid'])
add_memory(
    name="New related info",
    episode_body=f"Update about {nodes[0]['name']}..."
)
# Verify connections exist
```

#### Integration Testing

- Test with LibreChat MCP integration
- Verify tool discovery and schema
- Test error handling (invalid UUIDs, empty results)
- Verify group_id filtering works correctly

### Deployment

1. **Development:**
   - Implement changes on feature branch
   - Run local tests
   - Test with MCP inspector

2. **Docker Build:**
   - Update version in `mcp_server/pyproject.toml`
   - Build custom Docker image
   - Test in Docker environment

3. **Documentation:**
   - Update MCP server README
   - Add usage examples
   - Document new workflow pattern

## Success Metrics

### Qualitative
- ✅ LLM can explore entity connections before adding data
- ✅ User can ask "what do I know about X?" and get comprehensive view
- ✅ Reduced duplicate/disconnected entities

### Quantitative
- Tool implementation: < 100 lines of code
- No new dependencies required
- Reuses 100% existing Graphiti features
- Implementation time: ~1 hour

## Timeline

| Phase | Duration | Tasks |
|-------|----------|-------|
| Implementation | 30-45 min | Add two new tools, update imports |
| Documentation | 15-20 min | Update instructions and docstrings |
| Testing | 15-20 min | Manual workflow testing |
| **Total** | **1-1.5 hours** | |

## References

### Related Files
- `graphiti_core/edges.py:456` - `EntityEdge.get_by_node_uuid()`
- `graphiti_core/nodes.py:415` - `EpisodicNode.get_by_entity_node_uuid()`
- `mcp_server/src/graphiti_mcp_server.py` - MCP tool definitions
- `mcp_server/src/utils/formatting.py` - Result formatters

### Investigation Documents
- Analysis of Graphiti temporal architecture
- PKM use case critical analysis
- Core feature audit

## Notes

- **No core changes required** - only MCP layer modifications
- **Backward compatible** - adds new tools, doesn't modify existing
- **Low risk** - exposes existing, tested functionality
- **High value for PKM** - dramatically improves conversational workflows
- **FastMCP compatible** - uses standard annotations and patterns

## Next Steps

1. Review and approve this implementation plan
2. Implement changes on feature branch
3. Test locally with MCP server
4. Deploy to Docker/production
5. Monitor usage and gather feedback
6. Consider future enhancements (e.g., path finding between entities)
