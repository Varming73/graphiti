# Graphiti Python Library Guide: Episodic Memory & Pattern Recognition

**IMPORTANT:** This guide is for the **Python library API**. If you're using the **Graphiti MCP server** (for AI agents), see `Graphiti-MCP-Guide-Episodic-Memory.md` instead.

**Target Use Case:** Python developers building episodic memory systems for professional experiences, state changes, relationship events, and pattern recognition over time.

---

## 1. Core Architecture: How Graphiti Actually Works

### 1.1 The Three-Layer Data Model

Graphiti maintains three types of nodes that work together:

**EpisodicNodes (The Timeline)**
- **What they store:** Raw episode content exactly as you provide it
- **Key timestamps:**
  - `created_at`: When added to system (system time)
  - `valid_at`: When the event actually occurred (your provided reference time)
- **Source types:** `message`, `json`, or `text`
- **Special property:** `entity_edges` - tracks which facts were extracted from this episode

**EntityNodes (The Cast of Characters)**
- **What they are:** Extracted entities (people, projects, companies, concepts)
- **Key properties:**
  - `name`: The entity identifier
  - `labels`: List of types (e.g., `["Person"]`, `["Project", "Initiative"]`)
  - `summary`: Auto-generated summary of all known information
  - `attributes`: Custom structured data (JSON dict)
  - `name_embedding`: Vector for semantic search
- **Example:** "Peter", "Project Alpha", "Stakeholder X", "Copenhagen Conference"

**EntityEdges (The Facts/Relationships)**
- **What they store:** Relationships between entities as natural language facts
- **Critical temporal properties:**
  - `valid_at`: When relationship became true
  - `invalid_at`: When relationship ended
  - `created_at`: When fact entered system
  - `expired_at`: When fact was superseded/invalidated
- **Key properties:**
  - `name`: Relation type (e.g., "WORKS_AT", "ATTENDED")
  - `fact`: Natural language description
  - `fact_embedding`: Vector for semantic search
  - `episodes`: List of episode UUIDs that mentioned this fact
  - `attributes`: Custom structured data

### 1.2 Bi-Temporal Design: The Secret Sauce for Your Use Case

Graphiti tracks TWO timelines for every fact:

1. **Real-World Time** (`valid_at` → `invalid_at`)
   - When did this actually happen in the real world?
   - Example: "Peter changed jobs on 2024-03-15"

2. **System Time** (`created_at` → `expired_at`)
   - When did I learn this?
   - When did I update/invalidate this information?

**Why this matters for pattern recognition:**
```
Episode 1 (Feb 2024): "Started Project Alpha, team morale high"
  → Creates: EntityEdge with valid_at=2024-02-01

Episode 2 (May 2024): "Project Alpha struggling after Bob left"
  → Creates: New EntityEdge with valid_at=2024-05-01
  → Invalidates: Previous morale edge (sets expired_at)

Your query (Aug 2024): "Show me project trajectory patterns"
  → Can see the full temporal evolution
  → Both facts preserved with their valid timeframes
```

---

## 2. The Ingestion Process: What Happens When You Add an Episode

### 2.1 The `add_episode` Workflow

When you call `graphiti.add_episode()`, this is exactly what happens:

```python
await graphiti.add_episode(
    name="Stakeholder Meeting Retrospective",
    episode_body="Stakeholder meeting went poorly—scope creep discussion again. Same pattern as last quarter.",
    source_description="Weekly retrospective note",
    reference_time=datetime(2024, 11, 15, 14, 0),  # When meeting actually happened
    source=EpisodeType.text,
    group_id="my-workspace"  # Optional: partition your graph
)
```

**Step-by-step internal process:**

1. **Context Retrieval**
   - Fetches last N episodes for context (default: recent episodes before reference_time)
   - Uses these to disambiguate entities ("the meeting" → "Stakeholder X meeting")

2. **Entity Extraction (LLM)**
   - Prompts LLM to extract entities from episode content
   - Uses previous episodes as context for disambiguation
   - Can classify entities into custom types
   - Example extractions: "Stakeholder X", "scope creep", "project"

3. **Entity Deduplication**
   - Searches for similar existing entities using embeddings + BM25
   - LLM decides if extracted entity is same as existing one
   - Either returns existing UUID or creates new entity
   - Updates entity summaries with new information

4. **Edge Extraction (LLM)**
   - Extracts relationships between entities as facts
   - Extracts temporal information (when relationship started/ended)
   - Example: "Stakeholder X discussed scope creep on 2024-11-15"

5. **Edge Deduplication & Resolution**
   - Finds similar existing edges
   - LLM determines if new fact contradicts, updates, or complements existing facts
   - May invalidate old facts (sets `expired_at`)

6. **Persistence**
   - Saves episode, entities, edges to graph database
   - Creates `MENTIONS` edges from episode to entities
   - Generates embeddings for search

### 2.2 Custom Entity Types (For Your Domain)

You can define custom entity types to match your domain:

```python
from pydantic import BaseModel, Field

class Person(BaseModel):
    role: str | None = Field(None, description="Professional role")
    relationship_type: str | None = Field(None, description="stakeholder, colleague, client")

class Project(BaseModel):
    status: str | None = Field(None, description="active, completed, stalled")
    start_date: str | None = Field(None, description="Project start date")

class Pattern(BaseModel):
    pattern_type: str | None = Field(None, description="recurring_issue, success_factor, anti-pattern")
    frequency: str | None = Field(None, description="How often this pattern occurs")

entity_types = {
    "Person": Person,
    "Project": Project,
    "Pattern": Pattern,
}

await graphiti.add_episode(
    ...,
    entity_types=entity_types
)
```

**How Graphiti uses these:**
- Entities get labels: `["Person"]`, `["Project"]`, etc.
- Attributes get validated and structured
- Can filter searches by entity type later

---

## 3. The Search System: Finding Patterns Over Time

### 3.1 Three Search Layers

Graphiti searches across three layers simultaneously:

**1. Edge Search (Primary for your use case)**
- Searches relationship facts
- Best for: "What happened between X and Y?"
- Returns: EntityEdge objects

**2. Node Search**
- Searches entity names and summaries
- Best for: "What do I know about person X?"
- Returns: EntityNode objects

**3. Episode Search**
- Searches raw episode content
- Best for: "What did I write about X in my notes?"
- Returns: EpisodicNode objects

### 3.2 Search Methods (Can combine multiple)

Each layer supports three search methods:

**BM25 (Keyword Search)**
- Full-text search using BM25 algorithm
- Good for exact phrase matching
- Example: "scope creep" will match episodes with those exact words

**Cosine Similarity (Semantic Search)**
- Vector similarity using embeddings
- Good for concept matching
- Example: "project delays" will match "initiative timeline issues"

**BFS (Graph Traversal)**
- Breadth-first search from origin nodes
- Good for: "What's connected to this entity?"
- Can specify max depth

### 3.3 Reranking Methods

After initial search, results get reranked:

**RRF (Reciprocal Rank Fusion)**
- Combines results from multiple search methods
- General-purpose, fast
- Default choice for most queries

**MMR (Maximal Marginal Relevance)**
- Reduces redundancy in results
- Good for diverse perspectives on a topic

**Cross-Encoder**
- Most accurate, slowest
- Uses LLM to score relevance
- Best for critical queries

**Node Distance**
- Ranks by graph distance from a center node
- Good for: "What's most related to Project X?"

**Episode Mentions**
- Ranks by how many episodes mention this fact
- Good for: "What patterns appear most frequently?"

### 3.4 Temporal Filtering: The Key to Pattern Recognition

**Your most powerful tool for pattern analysis:**

```python
from graphiti_core.search.search_filters import SearchFilters, DateFilter, ComparisonOperator
from datetime import datetime

# Example 1: Facts that were true during Q3 2024
filters = SearchFilters(
    valid_at=[[
        DateFilter(date=datetime(2024, 7, 1), comparison_operator=ComparisonOperator.greater_than_equal),
        DateFilter(date=datetime(2024, 10, 1), comparison_operator=ComparisonOperator.less_than)
    ]]
)

results = await graphiti.search_(
    "stakeholder interactions",
    config=EDGE_HYBRID_SEARCH_RRF,
    search_filter=filters
)

# Example 2: Facts that ended (became invalid) - indicates state changes
filters = SearchFilters(
    invalid_at=[[
        DateFilter(comparison_operator=ComparisonOperator.is_not_null)
    ]]
)

# Example 3: Facts added in last month (what I learned recently)
filters = SearchFilters(
    created_at=[[
        DateFilter(date=datetime(2024, 10, 1), comparison_operator=ComparisonOperator.greater_than_equal)
    ]]
)

# Example 4: Only show facts about specific entity types
filters = SearchFilters(
    node_labels=["Project", "Stakeholder"]
)
```

**Date Filter Logic:**
- Multiple filters in inner list = AND
- Multiple inner lists = OR
- Example: `[[filter1, filter2], [filter3]]` = `(filter1 AND filter2) OR filter3`

### 3.5 Search Recipes for Your Use Cases

**Pattern Recognition Query:**
```python
# Find recurring issues with stakeholder X over time
results = await graphiti.search_(
    "scope creep discussions stakeholder interactions",
    config=EDGE_HYBRID_SEARCH_EPISODE_MENTIONS,  # Rank by frequency
    search_filter=SearchFilters(
        node_labels=["Stakeholder"],
        valid_at=[[
            DateFilter(
                date=datetime(2024, 1, 1),
                comparison_operator=ComparisonOperator.greater_than_equal
            )
        ]]
    ),
    limit=50
)

# Analyze edges for patterns
for edge in results.edges:
    print(f"{edge.fact} | Valid: {edge.valid_at} | Mentioned in {len(edge.episodes)} episodes")
```

**State Change Tracking:**
```python
# Find all role changes or project state changes
results = await graphiti.search_(
    "role change project status transition",
    config=COMBINED_HYBRID_SEARCH_RRF,
    search_filter=SearchFilters(
        invalid_at=[[
            DateFilter(comparison_operator=ComparisonOperator.is_not_null)
        ]]
    )
)
```

**Relationship Evolution:**
```python
# Track relationship with specific person over time
node = await EntityNode.get_by_name(driver, "Peter")  # Hypothetical

results = await graphiti.search_(
    "Peter relationship work collaboration",
    config=EDGE_HYBRID_SEARCH_NODE_DISTANCE,
    center_node_uuid=node.uuid,  # Rank by proximity to Peter
    limit=100
)

# Group by time periods to see evolution
edges_by_quarter = defaultdict(list)
for edge in results.edges:
    quarter = f"{edge.valid_at.year}-Q{(edge.valid_at.month-1)//3 + 1}"
    edges_by_quarter[quarter].append(edge)
```

**Success Pattern Discovery:**
```python
# Find what preceded successful project outcomes
# Step 1: Identify successful projects
successful_projects = await graphiti.search_(
    "project completed successful launched",
    config=NODE_HYBRID_SEARCH_RRF,
    search_filter=SearchFilters(node_labels=["Project"])
)

# Step 2: For each project, find edges from early phases
for project in successful_projects.nodes:
    early_edges = await graphiti.search_(
        f"{project.name} planning preparation early-stage",
        config=EDGE_HYBRID_SEARCH_NODE_DISTANCE,
        center_node_uuid=project.uuid,
        search_filter=SearchFilters(
            valid_at=[[
                DateFilter(
                    date=project.created_at,
                    comparison_operator=ComparisonOperator.less_than_equal
                )
            ]]
        )
    )
    # Analyze common patterns in early_edges across all successful projects
```

---

## 4. Episodic Memory Management

### 4.1 Bulk Ingestion for Historical Data

If you have historical retrospectives to import:

```python
from graphiti_core.utils.bulk_utils import RawEpisode

episodes = [
    RawEpisode(
        name="Q1 2024 Retrospective",
        content="Project Alpha kicked off...",
        source_description="Quarterly retrospective",
        reference_time=datetime(2024, 3, 31),
        source=EpisodeType.text,
    ),
    RawEpisode(
        name="Q2 2024 Retrospective",
        content="Stakeholder X relationship deteriorated...",
        source_description="Quarterly retrospective",
        reference_time=datetime(2024, 6, 30),
        source=EpisodeType.text,
    ),
]

results = await graphiti.add_episode_bulk(
    episodes,
    group_id="my-workspace",
    entity_types=entity_types
)
```

**Important:** Bulk mode is faster but skips some deduplication steps. Best for initial historical import.

### 4.2 Episode Retrieval by Time Window

```python
# Get all episodes from specific time range
episodes = await graphiti.retrieve_episodes(
    reference_time=datetime(2024, 12, 1),
    last_n=20,  # Last 20 episodes before this time
    group_ids=["my-workspace"]
)

for ep in episodes:
    print(f"{ep.name} | {ep.valid_at} | {ep.content[:100]}")
```

### 4.3 Deleting Episodes (with cleanup)

```python
# Remove episode and cleanup orphaned entities
await graphiti.remove_episode(episode_uuid)
```

**What this does:**
- Deletes episode node
- Deletes edges that were ONLY created by this episode
- Deletes entity nodes that are ONLY mentioned in this episode
- Preserves entities/edges mentioned in other episodes

---

## 5. Advanced Features for Your Use Case

### 5.1 Community Detection (Clusters of Related Entities)

Find implicit groupings in your graph:

```python
# Build communities across entire graph
communities, community_edges = await graphiti.build_communities()

# Each community has:
# - name: Auto-generated description
# - summary: What this cluster is about
# - members: Connected via HAS_MEMBER edges

for community in communities:
    print(f"Community: {community.name}")
    print(f"Summary: {community.summary}")
```

**Use case:** Discover implicit project teams, related stakeholders, or topic clusters without manual tagging.

### 5.2 Entity Summaries (Auto-Updated Knowledge Base)

Every entity maintains a rolling summary:

```python
node = await EntityNode.get_by_uuid(driver, node_uuid)
print(node.summary)
# "Peter is a senior architect who joined in 2023.
#  Initially collaborative but relationship deteriorated
#  during Project Alpha due to scope disagreements..."
```

**How it works:**
- Each time episode mentions entity, LLM updates summary
- Combines new info with existing summary
- Stays under character limit (condensing old info)

### 5.3 Group IDs (Multi-Workspace)

Partition your graph for different contexts:

```python
# Work episodic memory
await graphiti.add_episode(
    ...,
    group_id="work-memory"
)

# Personal episodic memory
await graphiti.add_episode(
    ...,
    group_id="personal-memory"
)

# Query specific workspace
results = await graphiti.search_(
    "project patterns",
    group_ids=["work-memory"]
)
```

---

## 6. Best Practices for Pattern Recognition

### 6.1 Structuring Episodes for Maximum Value

**Good Episode Structure:**
```python
name = "Sprint 12 Retrospective - Project Alpha"  # Specific, searchable
episode_body = """
What happened: Stakeholder X pushed back on timeline again
Context: Third time this sprint cycle they've extended scope
Outcome: Team morale dropped, velocity decreased 20%
Pattern: Similar to Sprint 8 with Client Y
"""
reference_time = datetime(2024, 11, 15, 16, 0)  # Precise time
```

**Why this works:**
- Clear temporal markers
- Explicit pattern references
- Measurable outcomes
- Entity mentions (Stakeholder X, Client Y)

### 6.2 Querying Strategy for Pattern Analysis

**Multi-Pass Pattern Discovery:**

```python
# Pass 1: Broad search for domain
edges_raw = await graphiti.search_(
    "stakeholder scope discussions",
    config=EDGE_HYBRID_SEARCH_RRF,
    limit=200
)

# Pass 2: Temporal grouping
from collections import defaultdict
patterns_by_time = defaultdict(list)
for edge in edges_raw.edges:
    week = edge.valid_at.isocalendar()[1]
    patterns_by_time[week].append(edge)

# Pass 3: Identify recurring entity pairs
entity_pair_counts = defaultdict(int)
for edge in edges_raw.edges:
    pair = tuple(sorted([edge.source_node_uuid, edge.target_node_uuid]))
    entity_pair_counts[pair] += 1

# Pass 4: Deep dive on high-frequency patterns
for pair, count in sorted(entity_pair_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
    # Get all edges between this pair
    edges = await EntityEdge.get_between_nodes(driver, pair[0], pair[1])
    # Analyze temporal evolution
    timeline = sorted(edges, key=lambda e: e.valid_at)
    print(f"Pattern evolution for {pair}: {len(timeline)} interactions")
```

### 6.3 Recommended Search Configs by Use Case

```python
# For frequency analysis (what patterns repeat?)
EDGE_HYBRID_SEARCH_EPISODE_MENTIONS

# For relationship mapping (how are things connected?)
EDGE_HYBRID_SEARCH_NODE_DISTANCE

# For semantic pattern discovery (similar situations?)
EDGE_HYBRID_SEARCH_MMR  # Diverse, non-redundant results

# For precise analytical queries
COMBINED_HYBRID_SEARCH_CROSS_ENCODER  # Most accurate
```

### 6.4 Handling Contradictions and Updates

Graphiti automatically handles conflicting information:

```python
# Episode 1 (March): "Project Alpha launched with 5-person team"
# Episode 2 (June): "Project Alpha now has 8 people after expansion"

# Both facts are preserved with temporal bounds:
# Edge 1: valid_at=2024-03-01, invalid_at=2024-06-01, expired_at=2024-06-15
# Edge 2: valid_at=2024-06-01, invalid_at=null
```

**Pattern query can see evolution:**
```python
filters = SearchFilters(
    expired_at=[[
        DateFilter(comparison_operator=ComparisonOperator.is_not_null)
    ]]
)
# Returns facts that were updated/invalidated - shows change points
```

---

## 7. System Design Considerations

### 7.1 When to Call add_episode

**Recommended triggers:**
- After each retrospective/reflection session
- Weekly summaries of key events
- Immediately after significant state changes
- When capturing meeting outcomes

**Not recommended:**
- Every single chat message (too granular)
- Unstructured stream-of-consciousness dumps
- Duplicate content (Graphiti will dedupe but wastes tokens)

### 7.2 Performance Characteristics

**add_episode timing (typical):**
- Simple episode (2-3 entities, 3-5 edges): 2-5 seconds
- Complex episode (10+ entities, 20+ edges): 10-30 seconds

**search_ timing (typical):**
- Simple query: 200-800ms
- Complex with cross-encoder: 1-3 seconds

**Recommendations:**
- Use background tasks for add_episode
- Sequential episode processing (don't parallelize)
- Bulk import for historical data
- Cache search results when appropriate

### 7.3 Cost Optimization

**LLM calls per add_episode (approximate):**
- Entity extraction: 1-2 calls
- Entity deduplication: 1 call per extracted entity
- Edge extraction: 1 call
- Edge deduplication: 1 call per extracted edge
- Summary updates: 1 call per new/updated entity

**Optimization strategies:**
- Use smaller models for entity extraction (GPT-4.1-mini)
- Use larger models only for critical deduplication (GPT-4.1)
- Batch historical imports with add_episode_bulk
- Set reasonable EPISODE_WINDOW_LEN (default: 5 previous episodes)

---

## 8. The Complete Flow Example

**Your weekly retrospective workflow:**

```python
# 1. Capture the episode
await graphiti.add_episode(
    name="Week 46 Retrospective",
    episode_body="""
    Stakeholder meeting went poorly—scope creep discussion again.
    This is the fourth time in three months Client X has requested
    major changes mid-sprint. Team morale noticeably lower.

    Compare to Project Beta last year: early technical spikes
    prevented this exact problem. That project had scope freeze
    in week 2 and smooth execution afterward.
    """,
    source_description="Weekly retrospective",
    reference_time=datetime(2024, 11, 15, 17, 0),
    source=EpisodeType.text,
    entity_types=entity_types,
    group_id="work-memory"
)

# 2. Pattern analysis query (run quarterly)
from datetime import timedelta

three_months_ago = datetime.now() - timedelta(days=90)

scope_patterns = await graphiti.search_(
    "scope creep stakeholder mid-sprint changes",
    config=EDGE_HYBRID_SEARCH_EPISODE_MENTIONS,
    search_filter=SearchFilters(
        node_labels=["Stakeholder", "Project"],
        valid_at=[[
            DateFilter(date=three_months_ago, comparison_operator=ComparisonOperator.greater_than_equal)
        ]]
    ),
    limit=50
)

# 3. Identify recurring patterns
stakeholder_issues = defaultdict(list)
for edge in scope_patterns.edges:
    if "scope" in edge.fact.lower():
        stakeholder_issues[edge.source_node_uuid].append({
            'fact': edge.fact,
            'when': edge.valid_at,
            'episodes': len(edge.episodes)
        })

# 4. Find success factors from past projects
success_patterns = await graphiti.search_(
    "technical spike early planning scope freeze successful",
    config=EDGE_HYBRID_SEARCH_RRF,
    search_filter=SearchFilters(
        node_labels=["Project"],
        invalid_at=[[  # Completed projects
            DateFilter(comparison_operator=ComparisonOperator.is_not_null)
        ]]
    )
)

# 5. Generate insights
print("Recurring Issues:")
for stakeholder_uuid, issues in sorted(stakeholder_issues.items(), key=lambda x: len(x[1]), reverse=True):
    print(f"  Stakeholder: {len(issues)} scope-related interactions")
    for issue in issues[:3]:  # Top 3
        print(f"    - {issue['when'].strftime('%Y-%m-%d')}: {issue['fact'][:100]}")

print("\nSuccess Patterns from Past Projects:")
for edge in success_patterns.edges[:5]:
    print(f"  - {edge.fact}")
```

---

## 9. Key Insights for AI Agent Implementation

### 9.1 What Makes Graphiti Different

1. **Temporal graph, not static knowledge base**
   - Facts have validity periods
   - Can query "what was true when"
   - Tracks information evolution

2. **Auto-deduplication with LLM**
   - "Peter", "peter", "Pete" → same entity
   - "hired by Acme", "joined Acme Corp" → same fact
   - Prevents knowledge fragmentation

3. **Episodic grounding**
   - Every fact traces back to source episodes
   - Can audit: "Where did I learn this?"
   - Episode count = confidence signal

4. **Hybrid search**
   - Semantic + keyword + graph traversal
   - No single point of failure
   - Combines strengths of each approach

### 9.2 Common Pitfalls to Avoid

**1. Over-granular episodes**
```python
# BAD: Every chat turn as episode
"User: How are you?"
"Agent: I'm good!"

# GOOD: Thematic summaries
"30-minute planning discussion about Q1 goals.
 Decided to focus on customer retention metrics."
```

**2. Ignoring reference_time**
```python
# BAD: Always use datetime.now()
reference_time = datetime.now()  # Wrong! This is when you're adding it

# GOOD: When event actually occurred
reference_time = datetime(2024, 11, 15, 14, 30)  # Actual meeting time
```

**3. Not using temporal filters**
```python
# BAD: Search without time context
results = await graphiti.search_("stakeholder issues")
# Returns everything ever, hard to find patterns

# GOOD: Scoped temporal queries
results = await graphiti.search_(
    "stakeholder issues",
    search_filter=SearchFilters(
        valid_at=[[DateFilter(date=quarter_start, ...)]]
    )
)
```

**4. Treating it like a traditional database**
```python
# BAD: Expecting exact entity names
node = await get_entity_by_name("Pete Johnson")  # Might fail

# GOOD: Search semantically, let dedup work
results = await graphiti.search_(
    "Pete Johnson engineer",
    config=NODE_HYBRID_SEARCH_RRF
)
node = results.nodes[0]
```

### 9.3 When to Use vs. Not Use Graphiti

**✅ Perfect for:**
- Episodic/autobiographical memory
- Relationship tracking over time
- Pattern recognition across timeframes
- Professional journal with temporal queries
- Dynamic knowledge that changes/evolves
- Need to understand "what was true when"

**❌ Not ideal for:**
- Static reference data (use traditional DB)
- Real-time chat (too slow for turn-by-turn)
- Exact entity matching requirements (fuzzy dedup)
- Simple key-value storage
- Append-only logs (no need for dedup overhead)

---

## 10. Quick Reference

### Essential Imports
```python
from graphiti_core import Graphiti
from graphiti_core.nodes import EntityNode, EpisodeType
from graphiti_core.edges import EntityEdge
from graphiti_core.search.search_config_recipes import (
    EDGE_HYBRID_SEARCH_RRF,
    EDGE_HYBRID_SEARCH_EPISODE_MENTIONS,
    COMBINED_HYBRID_SEARCH_CROSS_ENCODER,
)
from graphiti_core.search.search_filters import SearchFilters, DateFilter, ComparisonOperator
from datetime import datetime
```

### Common Temporal Queries
```python
# Facts valid during specific period
SearchFilters(valid_at=[[
    DateFilter(date=start, comparison_operator=ComparisonOperator.greater_than_equal),
    DateFilter(date=end, comparison_operator=ComparisonOperator.less_than)
]])

# Facts that ended (state changes)
SearchFilters(invalid_at=[[
    DateFilter(comparison_operator=ComparisonOperator.is_not_null)
]])

# Recently added facts
SearchFilters(created_at=[[
    DateFilter(date=recent_date, comparison_operator=ComparisonOperator.greater_than_equal)
]])

# Facts that were invalidated (contradictions/updates)
SearchFilters(expired_at=[[
    DateFilter(comparison_operator=ComparisonOperator.is_not_null)
]])
```

### Search Config Cheat Sheet
```python
# Balanced speed/accuracy
EDGE_HYBRID_SEARCH_RRF

# Frequency-based (pattern detection)
EDGE_HYBRID_SEARCH_EPISODE_MENTIONS

# Relationship-focused
EDGE_HYBRID_SEARCH_NODE_DISTANCE(center_node_uuid=...)

# Maximum accuracy (slower)
COMBINED_HYBRID_SEARCH_CROSS_ENCODER

# Diverse results (avoid redundancy)
EDGE_HYBRID_SEARCH_MMR
```

---

## Conclusion

Graphiti's power for your use case comes from:

1. **Bi-temporal tracking**: Distinguish "when it happened" from "when I learned it"
2. **Automatic deduplication**: Focus on patterns, not data cleaning
3. **Hybrid search + temporal filters**: Query patterns across time windows
4. **Episodic grounding**: Audit trail for every fact
5. **Entity summaries**: Auto-maintained knowledge base

The key to effective pattern recognition is combining temporal filters with the right search strategies. Start broad, then narrow by time windows and entity types to discover recurring patterns in your professional experiences.
