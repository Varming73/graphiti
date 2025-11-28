# Graphiti MCP Guide: Episodic Memory & Pattern Recognition

**Target Audience:** AI agent using Graphiti MCP server
**Use Case:** Professional episodic memory (autobiography) for tracking experiences, state changes, relationships, and discovering patterns over time

---

## 1. Understanding the MCP Tool Architecture

### 1.1 What Graphiti MCP Provides

The Graphiti MCP server exposes **13 tools** that work together to build a temporal knowledge graph:

**Core Storage & Retrieval:**
- `add_memory` - Store new information (episodes)
- `search_nodes` - Find entities (people, projects, concepts)
- `search_memory_facts` - Search relationships and conversation content
- `get_entities_by_type` - List all entities of specific type(s)

**Graph Exploration:**
- `get_entity_connections` - Get ALL relationships for an entity (complete graph traversal)
- `get_entity_timeline` - Get ALL episodes mentioning an entity (chronological history)

**Temporal Analysis:**
- `compare_facts_over_time` - Track how knowledge changed between two time periods

**Data Management:**
- `get_episodes` - List recent episodes (like git log)
- `get_entity_edge` - Retrieve specific relationship by UUID
- `delete_episode` - Remove episode
- `delete_entity_edge` - Remove relationship
- `clear_graph` - Delete all data (DESTRUCTIVE)

**Diagnostics:**
- `get_status` - Check server health

### 1.2 The Three-Layer Data Model

**Episodes** (your timeline entries)
- Raw content exactly as you provide it
- `created_at`: When added to system
- `valid_at`: When event actually occurred
- Example: "Stakeholder meeting went poorly—scope creep discussion again"

**Entities/Nodes** (the cast of characters)
- Extracted people, projects, companies, concepts
- Auto-generated summaries
- Custom attributes
- Example: "Stakeholder X", "Project Alpha", "scope creep pattern"

**Facts/Edges** (the relationships)
- Connections between entities as natural language
- Temporal metadata: when relationship started/ended
- Example: "Stakeholder X discussed scope creep on 2024-11-15"

### 1.3 Bi-Temporal Tracking: The Secret Sauce

Every fact has TWO timelines:

**Real-World Time** (`valid_at` → `invalid_at`)
- When did this happen in reality?
- "Peter changed jobs on 2024-03-15"

**System Time** (`created_at` → `expired_at`)
- When did I learn/update this?
- When was this information superseded?

**Why this matters for pattern recognition:**
```
Feb 2024: Add "Project Alpha started, team morale high"
  → fact.valid_at = 2024-02-01

May 2024: Add "Project Alpha struggling after Bob left"
  → New fact with valid_at = 2024-05-01
  → Previous morale fact gets expired_at set

Aug 2024: Query patterns across time
  → Can see full trajectory with temporal filters
```

---

## 2. The Core Workflow: SEARCH FIRST, THEN ADD

**CRITICAL PRINCIPLE:** Always explore existing knowledge before adding new information.

### 2.1 The Recommended Pattern

```
User provides information
    ↓
1. search_nodes(extract key entities/concepts)
    ↓
2. IF entities found:
   → get_entity_connections(entity_uuid) - See what's already linked
   → get_entity_timeline(entity_uuid) - Understand history
    ↓
3. add_memory(episode_body with explicit references to found entities)
    ↓
Result: New episode automatically connects to existing knowledge
```

### 2.2 Why This Matters

**❌ BAD - Adding without searching:**
```
add_memory(
    name="Database choice",
    episode_body="Chose PostgreSQL for new service"
)
# Creates isolated node, no connections
```

**✅ GOOD - Search first, then add with context:**
```
# Step 1: Search
nodes = search_nodes(query="database architecture microservices")
# Found: MySQL, Redis, microservices pattern

# Step 2: Explore connections
connections = get_entity_connections(entity_uuid=nodes[0]['uuid'])
# Sees: MySQL → user-service, payment-service

# Step 3: Add with explicit references
add_memory(
    name="Database choice",
    episode_body="Chose PostgreSQL for new notification-service.
                  Different from existing MySQL used by user-service
                  and payment-service because we need better JSON
                  support for notification templates."
)
# Result: Rich connections created automatically
```

---

## 3. Tool Reference for Your Use Case

### 3.1 Adding Professional Experiences: `add_memory`

**When to use:** Every retrospective, significant event, state change, or relationship update

**Signature:**
```python
add_memory(
    name: str,              # Brief title
    episode_body: str,      # Content (markdown supported)
    group_id: str | None,   # Optional namespace
    source: str,            # 'text', 'json', or 'message' (default: 'text')
    source_description: str,# Optional context
    uuid: str | None        # Only for updates
)
```

**Best practices for your use case:**

```python
# Professional experience
add_memory(
    name="Sprint 12 Retrospective - Project Alpha",
    episode_body="""
What happened: Stakeholder X pushed back on timeline again
Context: Third time this sprint cycle they've extended scope
Outcome: Team morale dropped, velocity decreased 20%
Pattern: Similar to Sprint 8 with Client Y
Related: Project Alpha, Stakeholder X, scope creep
""",
    source="text",
    source_description="Weekly retrospective note"
)

# State change
add_memory(
    name="Role Change",
    episode_body="Started new role as lead architect on Project Beta.
                  Transitioned from individual contributor on Project Alpha.",
    source="text",
    source_description="Career milestone"
)

# Relationship event
add_memory(
    name="Stakeholder Dinner",
    episode_body="Dinner with Peter - he mentioned changing jobs to Acme Corp.
                  Discussed challenges with distributed teams.",
    source="text",
    source_description="Professional networking"
)
```

**What happens internally:**
1. Content queued for background processing
2. LLM extracts entities (Stakeholder X, Project Alpha, scope creep, etc.)
3. System searches for existing similar entities and deduplicates
4. LLM extracts relationships between entities
5. Temporal metadata captured (when relationships started/ended)
6. Everything saved to graph with embeddings for search

**Returns immediately** - processing happens asynchronously in background

### 3.2 Finding Entities: `search_nodes`

**When to use:** Finding people, projects, concepts, patterns before adding related info

**Signature:**
```python
search_nodes(
    query: str,                    # Search keywords or semantic description
    group_ids: list[str] | None,   # Optional namespace filter
    max_nodes: int,                # Default: 10
    entity_types: list[str] | None # Optional type filter
)
```

**Use cases:**

```python
# Find entities by name
search_nodes(query="Stakeholder X")

# Semantic search
search_nodes(query="projects with scope issues")

# Filter by custom entity type
search_nodes(
    query="patterns recurring problems",
    entity_types=["Pattern", "Insight"]
)
```

**Returns:**
```python
{
    "message": "Nodes retrieved successfully",
    "nodes": [
        {
            "uuid": "abc-123...",
            "name": "Stakeholder X",
            "labels": ["Stakeholder", "Person"],
            "summary": "Executive at Client Company. History of scope changes...",
            "created_at": "2024-01-15T10:30:00Z",
            "group_id": "work-memory",
            "attributes": {
                "role": "VP Engineering",
                "relationship_type": "client"
            }
        }
    ]
}
```

### 3.3 Complete Graph Exploration: `get_entity_connections`

**When to use:**
- Before adding related information
- Pattern detection (need COMPLETE data, not search results)
- Understanding full context without formulating semantic queries

**Critical distinction:**
- `search_memory_facts` → Semantic query, may miss connections
- `get_entity_connections` → COMPLETE traversal, guaranteed ALL relationships

**Signature:**
```python
get_entity_connections(
    entity_uuid: str,              # From search_nodes
    group_ids: list[str] | None,
    max_connections: int           # Default: 50
)
```

**Your use case - Pattern detection:**

```python
# Step 1: Find entity
nodes = search_nodes(query="Stakeholder X")
stakeholder_uuid = nodes[0]['uuid']

# Step 2: Get ALL connections (complete data)
connections = get_entity_connections(
    entity_uuid=stakeholder_uuid,
    max_connections=100  # Get more for pattern analysis
)

# Step 3: Analyze patterns in complete dataset
for fact in connections['facts']:
    if 'scope' in fact['fact'].lower():
        print(f"{fact['valid_at']}: {fact['fact']}")
        # 2024-02-10: Stakeholder X requested additional features
        # 2024-03-05: Stakeholder X expanded scope mid-sprint
        # 2024-04-12: Stakeholder X discussed scope changes
        # Pattern: Consistent scope creep every 3-4 weeks
```

**Returns ALL relationships** where entity is source or target:
```python
{
    "message": "Found 23 connection(s) for entity",
    "facts": [
        {
            "uuid": "fact-uuid-1",
            "fact": "Stakeholder X discussed scope changes for Project Alpha",
            "source_node_uuid": "stakeholder-uuid",
            "target_node_uuid": "project-alpha-uuid",
            "source_node_name": "Stakeholder X",
            "target_node_name": "Project Alpha",
            "name": "DISCUSSED",
            "valid_at": "2024-02-10T14:00:00Z",
            "invalid_at": null,
            "created_at": "2024-02-10T18:30:00Z",
            "expired_at": null,
            "group_id": "work-memory"
        }
    ]
}
```

### 3.4 Temporal History: `get_entity_timeline`

**When to use:**
- "When did we first discuss X?"
- Track evolution of understanding over time
- See context from original sources

**Signature:**
```python
get_entity_timeline(
    entity_uuid: str,
    group_ids: list[str] | None,
    max_episodes: int              # Default: 20
)
```

**Your use case - Evolution tracking:**

```python
# Find pattern entity
nodes = search_nodes(query="scope creep pattern")
pattern_uuid = nodes[0]['uuid']

# Get chronological history
timeline = get_entity_timeline(
    entity_uuid=pattern_uuid,
    max_episodes=30
)

# Analyze evolution
for episode in timeline['episodes']:
    print(f"{episode['valid_at']}: {episode['name']}")
    print(f"  {episode['content'][:100]}...")
```

**Returns episodes chronologically:**
```python
{
    "message": "Found 12 episode(s) mentioning entity",
    "episodes": [
        {
            "uuid": "ep-1",
            "name": "Sprint 8 Retrospective",
            "content": "Client Y introduced scope changes mid-sprint...",
            "valid_at": "2024-02-15T17:00:00Z",
            "created_at": "2024-02-15T18:30:00Z",
            "source": "text",
            "group_id": "work-memory"
        },
        {
            "uuid": "ep-2",
            "name": "Sprint 12 Retrospective",
            "content": "Stakeholder X pushed back on timeline again...",
            "valid_at": "2024-03-15T17:00:00Z",
            "created_at": "2024-03-15T18:30:00Z",
            "source": "text",
            "group_id": "work-memory"
        }
    ]
}
```

### 3.5 Temporal Analysis: `compare_facts_over_time`

**When to use:** Quarterly reviews, tracking how understanding changed, identifying when patterns emerged

**Signature:**
```python
compare_facts_over_time(
    query: str,                    # What to track
    start_time: str,               # ISO 8601: "2024-01-01" or "2024-01-01T00:00:00Z"
    end_time: str,                 # ISO 8601
    group_ids: list[str] | None,
    max_facts_per_period: int      # Default: 10
)
```

**Your use case - Quarterly pattern analysis:**

```python
# Track stakeholder relationship evolution Q1 → Q2
comparison = compare_facts_over_time(
    query="Stakeholder X interactions",
    start_time="2024-01-01",
    end_time="2024-06-30",
    max_facts_per_period=20
)

# Returns 4 categories:
# - facts_from_start: What was true at Q1 start
# - facts_at_end: What was true at Q2 end
# - facts_invalidated: Relationships that ended
# - facts_added: New relationships formed
```

**Returns:**
```python
{
    "message": "Comparison completed between 2024-01-01 and 2024-06-30",
    "start_time": "2024-01-01",
    "end_time": "2024-06-30",
    "summary": {
        "facts_at_start_count": 8,
        "facts_at_end_count": 15,
        "facts_invalidated_count": 2,
        "facts_added_count": 9
    },
    "facts_from_start": [...],    # What existed at Q1
    "facts_at_end": [...],         # What exists at Q2 end
    "facts_invalidated": [...],    # What changed/ended
    "facts_added": [...]           # What was learned
}
```

**Insights you can derive:**
- Relationship velocity (how many new connections formed)
- Changed facts (understanding evolved)
- Invalidated facts (state changes, project completions)

### 3.6 Listing by Type: `get_entities_by_type`

**When to use:** Browse knowledge organized by classification

**Signature:**
```python
get_entities_by_type(
    entity_types: list[str],       # REQUIRED: ["Insight"], ["Pattern"]
    group_ids: list[str] | None,
    max_entities: int,             # Default: 20
    query: str | None              # Optional filter within type
)
```

**Your use case - Custom entity types:**

```python
# If you've configured custom entity types in MCP config:
# entity_types:
#   - name: "Pattern"
#     description: "Recurring patterns in professional work"
#   - name: "Stakeholder"
#     description: "Key stakeholders and clients"
#   - name: "Project"
#     description: "Work projects and initiatives"

# Get all patterns
patterns = get_entities_by_type(
    entity_types=["Pattern"]
)

# Get stakeholders and projects
entities = get_entities_by_type(
    entity_types=["Stakeholder", "Project"]
)

# Filter within type
tech_patterns = get_entities_by_type(
    entity_types=["Pattern"],
    query="technical spike architecture"
)
```

### 3.7 Semantic Fact Search: `search_memory_facts`

**When to use:** Searching conversation content, finding specific relationships

**Difference from `get_entity_connections`:**
- `search_memory_facts` → Query-driven, semantic, may miss some
- `get_entity_connections` → Complete, guaranteed all relationships

**Signature:**
```python
search_memory_facts(
    query: str,
    group_ids: list[str] | None,
    max_facts: int,                # Default: 10
    center_node_uuid: str | None   # Focus search around entity
)
```

**Use cases:**

```python
# Broad semantic search
search_memory_facts(query="scope creep discussions")

# Focused around entity
nodes = search_nodes(query="Project Alpha")
search_memory_facts(
    query="timeline delays",
    center_node_uuid=nodes[0]['uuid']
)
```

---

## 4. Pattern Recognition Workflows

### 4.1 Weekly Retrospective Workflow

**Goal:** Capture experience, link to existing patterns

```python
# Week 46 retrospective
# 1. Search for related patterns
patterns = search_nodes(query="scope creep stakeholder mid-sprint")

# 2. If pattern exists, get its history
if patterns['nodes']:
    pattern_uuid = patterns['nodes'][0]['uuid']

    # See all connections
    connections = get_entity_connections(entity_uuid=pattern_uuid)

    # See chronological mentions
    timeline = get_entity_timeline(entity_uuid=pattern_uuid)

    # Now add with explicit reference
    add_memory(
        name="Week 46 Retrospective",
        episode_body=f"""
Stakeholder X pushed back on timeline again.
Fourth occurrence of scope creep pattern.
Previous instances: Sprint 8 (Client Y), Sprint 10, Sprint 12.

Team morale impact: 20% velocity decrease.
Root cause: No scope freeze process in place.

Action: Implement week-2 scope freeze based on Project Beta success pattern.
""",
        source="text",
        source_description="Weekly retrospective"
    )
else:
    # First occurrence - create pattern
    add_memory(
        name="Week 46 Retrospective",
        episode_body="""
Identified new pattern: Scope Creep Pattern.
Stakeholder X introduced mid-sprint changes.
Creating this as trackable pattern for future analysis.
""",
        source="text",
        source_description="Weekly retrospective"
    )
```

### 4.2 Quarterly Pattern Analysis Workflow

**Goal:** Discover recurring patterns, success factors

```python
# Quarterly review - identify patterns

# 1. Get all scope-related entities
scope_entities = search_nodes(
    query="scope creep timeline changes",
    max_nodes=30
)

# 2. For each, get complete connection data
pattern_data = {}
for entity in scope_entities['nodes']:
    connections = get_entity_connections(
        entity_uuid=entity['uuid'],
        max_connections=100
    )

    # Group by time periods
    q1_facts = [f for f in connections['facts']
                if '2024-01' <= f['valid_at'] <= '2024-03']
    q2_facts = [f for f in connections['facts']
                if '2024-04' <= f['valid_at'] <= '2024-06']

    pattern_data[entity['name']] = {
        'q1_count': len(q1_facts),
        'q2_count': len(q2_facts),
        'trend': 'increasing' if len(q2_facts) > len(q1_facts) else 'stable'
    }

# 3. Compare time periods for specific query
comparison = compare_facts_over_time(
    query="stakeholder scope discussions",
    start_time="2024-01-01",
    end_time="2024-06-30",
    max_facts_per_period=50
)

# 4. Find success patterns from completed projects
success_entities = search_nodes(
    query="project completed successful",
    entity_types=["Project"],
    max_nodes=20
)

for project in success_entities['nodes']:
    # Get early-phase activities
    timeline = get_entity_timeline(
        entity_uuid=project['uuid'],
        max_episodes=30
    )

    # Analyze what happened in first 2 weeks
    early_episodes = [ep for ep in timeline['episodes']
                      if calculate_weeks_from_start(ep, project) <= 2]

    # Extract common success patterns
    # (technical spikes, scope freeze, etc.)

# 5. Record insights
add_memory(
    name="Q2 Pattern Analysis",
    episode_body=f"""
Pattern Analysis Results (Jan-Jun 2024):

RECURRING ISSUES:
- Scope creep pattern: 12 occurrences, primarily with Stakeholder X
- Frequency: Every 3-4 weeks on average
- Impact: 15-20% velocity decrease per occurrence

SUCCESS FACTORS (from completed projects):
- Technical spikes in week 1: 80% success rate
- Scope freeze by week 2: 60% fewer late-stage changes
- Early stakeholder alignment: 50% better team morale

RECOMMENDATIONS:
1. Implement mandatory technical spike phase (week 1)
2. Institute scope freeze process (end of week 2)
3. Weekly stakeholder check-ins for early alignment

Evidence from: {len(scope_entities['nodes'])} scope-related entities,
{comparison['summary']['facts_added_count']} new patterns identified Q2.
""",
    source="text",
    source_description="Quarterly strategic analysis"
)
```

### 4.3 Relationship Evolution Tracking

**Goal:** Track how professional relationships changed over time

```python
# Track relationship with specific stakeholder

# 1. Find stakeholder
stakeholder = search_nodes(query="Stakeholder X")
stakeholder_uuid = stakeholder['nodes'][0]['uuid']

# 2. Get complete interaction history
timeline = get_entity_timeline(
    entity_uuid=stakeholder_uuid,
    max_episodes=50
)

# 3. Get all relationships
connections = get_entity_connections(
    entity_uuid=stakeholder_uuid,
    max_connections=100
)

# 4. Temporal analysis
q1_interactions = [ep for ep in timeline['episodes']
                   if '2024-01' <= ep['valid_at'] <= '2024-03']
q2_interactions = [ep for ep in timeline['episodes']
                   if '2024-04' <= ep['valid_at'] <= '2024-06']

# 5. Sentiment/topic analysis
q1_topics = extract_topics(q1_interactions)  # Your analysis
q2_topics = extract_topics(q2_interactions)

# 6. Compare time periods
comparison = compare_facts_over_time(
    query="Stakeholder X",
    start_time="2024-01-01",
    end_time="2024-06-30"
)

# 7. Record relationship analysis
add_memory(
    name="Stakeholder X - Relationship Review",
    episode_body=f"""
Relationship Evolution: Stakeholder X (Jan-Jun 2024)

Q1 PATTERN:
- {len(q1_interactions)} interactions
- Topics: {q1_topics}
- Sentiment: Collaborative, proactive

Q2 PATTERN:
- {len(q2_interactions)} interactions
- Topics: {q2_topics}
- Sentiment: Reactive, scope-focused

KEY CHANGES:
- {len(comparison['facts_invalidated'])} relationships ended
- {len(comparison['facts_added'])} new patterns emerged
- Shift from early planning to mid-sprint interventions

HYPOTHESIS:
Project Alpha delays triggered shift to micromanagement style.
Similar pattern observed with Client Y on Project Beta.

ACTION:
Schedule relationship reset meeting, propose new collaboration model.
""",
    source="text",
    source_description="Relationship analysis"
)
```

---

## 5. Custom Entity Types for Your Use Case

### 5.1 Recommended Entity Types

Configure these in your MCP server config file:

```yaml
graphiti:
  entity_types:
    - name: "Person"
      description: "People - colleagues, stakeholders, clients"

    - name: "Stakeholder"
      description: "Key stakeholders and decision makers"

    - name: "Project"
      description: "Work projects and initiatives"

    - name: "Pattern"
      description: "Recurring patterns identified in work (success factors, anti-patterns, recurring issues)"

    - name: "Insight"
      description: "Strategic insights and lessons learned"

    - name: "Process"
      description: "Work processes and methodologies"

    - name: "Technology"
      description: "Technologies, tools, and technical decisions"
```

### 5.2 Using Custom Types

```python
# List all patterns
patterns = get_entities_by_type(
    entity_types=["Pattern"]
)

# Search specific types
tech_decisions = search_nodes(
    query="architecture database",
    entity_types=["Technology", "Process"]
)

# Filter facts by entity types
# Note: search_memory_facts doesn't have entity_type filter
# Instead, search entities first, then get their connections
tech_entities = search_nodes(
    query="microservices",
    entity_types=["Technology"]
)

for entity in tech_entities['nodes']:
    connections = get_entity_connections(entity_uuid=entity['uuid'])
    # All relationships involving this technology
```

---

## 6. Best Practices for AI Agents

### 6.1 When Adding Information: The Search-First Protocol

**ALWAYS:**
1. **Search** for related entities: `search_nodes`
2. **Explore** their context: `get_entity_connections`, `get_entity_timeline`
3. **Reference** found entities explicitly in `episode_body`
4. **Then add**: `add_memory`

**Example of good practice:**

```python
# User: "Had a meeting with Peter about the database migration"

# Step 1: Search
peter = search_nodes(query="Peter")
db_entities = search_nodes(query="database migration")

# Step 2: Explore
if peter['nodes']:
    peter_history = get_entity_timeline(entity_uuid=peter['nodes'][0]['uuid'])
    # See: Previous mentions of Peter

if db_entities['nodes']:
    db_connections = get_entity_connections(entity_uuid=db_entities['nodes'][0]['uuid'])
    # See: Related technologies, projects, people

# Step 3: Add with context
add_memory(
    name="Database Migration Meeting - Peter",
    episode_body=f"""
Meeting with Peter (Senior DBA) about PostgreSQL migration for Project Alpha.

Context from history:
- Peter previously worked on MySQL optimization (see Feb 2024 notes)
- Database migration connects to microservices architecture decision

Discussion points:
- Timeline: 3-week migration window
- Risk: Data consistency during cutover
- Mitigation: Blue-green deployment strategy

This relates to our previous architectural discussions and Peter's expertise
from the MySQL optimization project.
""",
    source="text",
    source_description="Meeting notes"
)
```

### 6.2 Pattern Recognition: Use Complete Data

**For pattern detection, ALWAYS use complete traversal tools:**

```python
# ❌ BAD - Semantic search might miss connections
facts = search_memory_facts(query="scope creep")
# Might miss: "timeline changes", "requirement expansion", "feature additions"

# ✅ GOOD - Complete traversal guarantees all data
nodes = search_nodes(query="scope creep pattern")
if nodes['nodes']:
    pattern_uuid = nodes['nodes'][0]['uuid']
    all_connections = get_entity_connections(
        entity_uuid=pattern_uuid,
        max_connections=200  # Get comprehensive data
    )
    # Guaranteed: ALL relationships, nothing missed
    # Now analyze complete dataset for patterns
```

### 6.3 Temporal Queries: Be Specific

**Good temporal context in episode_body:**

```python
add_memory(
    name="Sprint 15 Retrospective",
    episode_body="""
Date: November 28, 2024
Sprint: Week 46-47 (Nov 18-28)

Key events:
- Week 46: Stakeholder X requested scope changes (Tuesday Nov 19)
- Week 46: Team velocity dropped to 15 points (from usual 25)
- Week 47: Implemented scope freeze process (Friday Nov 22)
- Week 47: Velocity recovered to 23 points

Timeline observation:
Similar to Sprint 12 (3 months ago) - scope changes in week 1 caused disruption.
Unlike Sprint 13 - where scope freeze prevented issues.

Pattern: Scope freeze timing is critical. Must implement by end of week 1.
""",
    source="text",
    source_description="Sprint retrospective with temporal analysis"
)
```

### 6.4 Namespace Organization with group_id

**Separate contexts with group_id:**

```python
# Work memory
add_memory(
    name="Project Alpha Update",
    episode_body="...",
    group_id="work-memory"
)

# Personal professional development
add_memory(
    name="Conference Insights - Copenhagen",
    episode_body="...",
    group_id="professional-development"
)

# Query specific namespace
work_patterns = search_nodes(
    query="project patterns",
    group_ids=["work-memory"]
)
```

### 6.5 Avoid Common Pitfalls

**1. Don't add without searching:**
```python
# ❌ Creates disconnected knowledge
add_memory(name="Meeting notes", episode_body="Discussed Redis")

# ✅ Search first, add with context
redis_entities = search_nodes(query="Redis caching")
add_memory(
    name="Meeting notes",
    episode_body="Discussed Redis caching strategy, building on our
                  previous evaluation from Q1 (see Redis entity)..."
)
```

**2. Don't rely only on semantic search for patterns:**
```python
# ❌ May miss connections
facts = search_memory_facts(query="database problems")

# ✅ Get complete data
db_entities = search_nodes(query="database")
for entity in db_entities['nodes']:
    all_facts = get_entity_connections(entity_uuid=entity['uuid'])
    # Complete dataset for pattern analysis
```

**3. Don't forget temporal context:**
```python
# ❌ Vague timing
add_memory(name="Update", episode_body="Project status changed")

# ✅ Explicit temporal markers
add_memory(
    name="Project Alpha Status Change",
    episode_body="Status changed from 'active' to 'maintenance mode'
                  as of November 28, 2024. Active development ended
                  after 6-month cycle that started May 2024."
)
```

---

## 7. Complete Example: Quarterly Review Agent

**Goal:** AI agent that conducts quarterly professional reviews

```python
def quarterly_review_agent(quarter_start: str, quarter_end: str):
    """
    Comprehensive quarterly review using Graphiti MCP.

    Args:
        quarter_start: "2024-01-01"
        quarter_end: "2024-03-31"
    """

    # === PHASE 1: Gather Data ===

    # 1. Get all patterns
    patterns = get_entities_by_type(
        entity_types=["Pattern", "Insight"]
    )

    # 2. Get all projects
    projects = get_entities_by_type(
        entity_types=["Project"]
    )

    # 3. Get all stakeholders
    stakeholders = get_entities_by_type(
        entity_types=["Stakeholder"]
    )

    # === PHASE 2: Temporal Analysis ===

    # Track changes for each pattern
    pattern_evolution = {}
    for pattern in patterns['nodes']:
        comparison = compare_facts_over_time(
            query=pattern['name'],
            start_time=quarter_start,
            end_time=quarter_end
        )

        pattern_evolution[pattern['name']] = {
            'frequency': len(comparison['facts_added']),
            'changes': len(comparison['facts_invalidated']),
            'status': 'increasing' if len(comparison['facts_added']) > 5 else 'stable'
        }

    # === PHASE 3: Deep Dive on High-Frequency Patterns ===

    high_frequency_patterns = [
        p for p, data in pattern_evolution.items()
        if data['frequency'] > 5
    ]

    pattern_details = {}
    for pattern_name in high_frequency_patterns:
        # Find pattern entity
        pattern_nodes = search_nodes(query=pattern_name)
        if not pattern_nodes['nodes']:
            continue

        pattern_uuid = pattern_nodes['nodes'][0]['uuid']

        # Get complete context
        connections = get_entity_connections(
            entity_uuid=pattern_uuid,
            max_connections=100
        )

        timeline = get_entity_timeline(
            entity_uuid=pattern_uuid,
            max_episodes=50
        )

        # Extract insights
        pattern_details[pattern_name] = {
            'connections': len(connections['facts']),
            'mentions': len(timeline['episodes']),
            'related_entities': set([
                f['source_node_name'] for f in connections['facts']
            ] + [
                f['target_node_name'] for f in connections['facts']
            ]),
            'first_seen': timeline['episodes'][0]['valid_at'] if timeline['episodes'] else None,
            'last_seen': timeline['episodes'][-1]['valid_at'] if timeline['episodes'] else None
        }

    # === PHASE 4: Relationship Analysis ===

    stakeholder_analysis = {}
    for stakeholder in stakeholders['nodes']:
        # Get interaction frequency
        timeline = get_entity_timeline(
            entity_uuid=stakeholder['uuid'],
            max_episodes=100
        )

        quarter_interactions = [
            ep for ep in timeline['episodes']
            if quarter_start <= ep['valid_at'] <= quarter_end
        ]

        # Get relationship changes
        comparison = compare_facts_over_time(
            query=stakeholder['name'],
            start_time=quarter_start,
            end_time=quarter_end
        )

        stakeholder_analysis[stakeholder['name']] = {
            'interactions': len(quarter_interactions),
            'new_relationships': len(comparison['facts_added']),
            'ended_relationships': len(comparison['facts_invalidated']),
            'net_change': len(comparison['facts_added']) - len(comparison['facts_invalidated'])
        }

    # === PHASE 5: Success Factor Identification ===

    # Find completed projects
    completed_projects = search_nodes(
        query="completed successful finished",
        entity_types=["Project"]
    )

    success_factors = {}
    for project in completed_projects['nodes']:
        timeline = get_entity_timeline(
            entity_uuid=project['uuid'],
            max_episodes=100
        )

        connections = get_entity_connections(
            entity_uuid=project['uuid'],
            max_connections=100
        )

        # Look for early-phase activities (first 20% of episodes)
        early_phase_count = len(timeline['episodes']) // 5
        early_episodes = timeline['episodes'][:early_phase_count]

        # Extract common patterns from early phase
        early_patterns = set()
        for ep in early_episodes:
            content_lower = ep['content'].lower()
            if 'technical spike' in content_lower:
                early_patterns.add('technical_spike')
            if 'scope freeze' in content_lower:
                early_patterns.add('scope_freeze')
            if 'architecture' in content_lower:
                early_patterns.add('early_architecture')

        success_factors[project['name']] = {
            'early_patterns': list(early_patterns),
            'duration_weeks': calculate_project_duration(timeline),
            'stakeholder_count': count_unique_stakeholders(connections)
        }

    # === PHASE 6: Generate Review ===

    review_text = f"""
# Quarterly Review: {quarter_start} to {quarter_end}

## Pattern Analysis

### High-Frequency Patterns
{format_pattern_analysis(pattern_details, pattern_evolution)}

### Pattern Trends
- Increasing: {count_by_status(pattern_evolution, 'increasing')} patterns
- Stable: {count_by_status(pattern_evolution, 'stable')} patterns

## Relationship Analysis

### Stakeholder Engagement
{format_stakeholder_analysis(stakeholder_analysis)}

### Relationship Velocity
- New relationships formed: {sum_metric(stakeholder_analysis, 'new_relationships')}
- Relationships ended: {sum_metric(stakeholder_analysis, 'ended_relationships')}
- Net change: {sum_metric(stakeholder_analysis, 'net_change')}

## Success Factors

### Completed Projects
{format_success_factors(success_factors)}

### Common Success Patterns
{identify_common_patterns(success_factors)}

## Recommendations

### Based on Pattern Analysis
{generate_pattern_recommendations(pattern_details, pattern_evolution)}

### Based on Success Factors
{generate_success_recommendations(success_factors)}

### Relationship Management
{generate_stakeholder_recommendations(stakeholder_analysis)}

---

Evidence Base:
- {len(patterns['nodes'])} patterns analyzed
- {len(projects['nodes'])} projects reviewed
- {len(stakeholders['nodes'])} stakeholder relationships tracked
- {sum([len(p.get('related_entities', [])) for p in pattern_details.values()])} unique entity connections
"""

    # === PHASE 7: Store Review ===

    add_memory(
        name=f"Quarterly Review: {quarter_start} to {quarter_end}",
        episode_body=review_text,
        source="text",
        source_description="AI-generated quarterly professional review"
    )

    return review_text
```

---

## 8. Quick Reference

### 8.1 Tool Selection Decision Tree

```
Need to ADD information?
  → add_memory (after searching first!)

Need to FIND entities (people, projects, concepts)?
  → search_nodes

Need to LIST all of a type?
  → get_entities_by_type

Need COMPLETE context for an entity?
  → get_entity_connections (guaranteed complete)

Need chronological HISTORY of entity?
  → get_entity_timeline (guaranteed complete)

Need to SEARCH relationships semantically?
  → search_memory_facts (query-driven, may miss some)

Need to COMPARE time periods?
  → compare_facts_over_time

Need to see RECENT additions?
  → get_episodes (like git log)

Have specific UUID?
  → get_entity_edge

Need to DELETE?
  → delete_episode, delete_entity_edge (after confirmation!)

Need to RESET everything?
  → clear_graph (DESTRUCTIVE - confirm multiple times!)
```

### 8.2 Pattern Recognition Cheat Sheet

```python
# Weekly retrospective
1. search_nodes("relevant entities")
2. get_entity_connections(uuid) for each
3. get_entity_timeline(uuid) for context
4. add_memory(with explicit references)

# Quarterly analysis
1. get_entities_by_type(["Pattern", "Insight"])
2. compare_facts_over_time(Q_start, Q_end)
3. For high-frequency patterns:
   - get_entity_connections(uuid) - COMPLETE data
   - get_entity_timeline(uuid) - chronological context
4. Analyze complete datasets
5. add_memory(findings)

# Relationship tracking
1. search_nodes("person/stakeholder name")
2. get_entity_timeline(uuid) - all interactions
3. get_entity_connections(uuid) - all relationships
4. compare_facts_over_time(period_start, period_end)
5. Analyze evolution
6. add_memory(relationship analysis)
```

### 8.3 Common Patterns

**Before adding:**
```python
entities = search_nodes(query="...")
for e in entities['nodes']:
    connections = get_entity_connections(entity_uuid=e['uuid'])
    timeline = get_entity_timeline(entity_uuid=e['uuid'])
    # Review, then add with context
add_memory(name="...", episode_body="... references found entities ...")
```

**Pattern detection:**
```python
pattern = search_nodes(query="pattern name")
all_connections = get_entity_connections(
    entity_uuid=pattern['nodes'][0]['uuid'],
    max_connections=200  # Complete data
)
# Analyze frequencies, temporal patterns, related entities
```

**Temporal analysis:**
```python
comparison = compare_facts_over_time(
    query="topic",
    start_time="2024-01-01",
    end_time="2024-06-30"
)
# Examine: facts_added, facts_invalidated, changes over time
```

---

## 9. Key Differences from Python Library

If you're familiar with the Python library, note these MCP-specific differences:

| Python Library | MCP Tool | Notes |
|---|---|---|
| `graphiti.add_episode()` | `add_memory()` | MCP: async queue, returns immediately |
| `graphiti.search_()` with node config | `search_nodes()` | MCP: simplified interface |
| `graphiti.search_()` with edge config | `search_memory_facts()` | MCP: simplified interface |
| `EntityNode.get_by_uuids()` | `search_nodes()` + `get_entities_by_type()` | MCP: search-based |
| `EntityEdge.get_by_node_uuid()` | `get_entity_connections()` | MCP: dedicated tool |
| `EpisodicNode.get_by_entity_node_uuid()` | `get_entity_timeline()` | MCP: dedicated tool |
| Temporal search filters | `compare_facts_over_time()` | MCP: built-in temporal comparison |
| `graphiti.retrieve_episodes()` | `get_episodes()` | MCP: simplified pagination |

**Philosophy difference:**
- Python library: Full control, complex configurations
- MCP: Simplified, opinionated, optimized for AI agents

---

## Conclusion

The Graphiti MCP server is designed for AI agents to build and query temporal knowledge graphs. For your episodic memory use case:

**Core principles:**
1. **Always search before adding** - Create rich connections
2. **Use complete data for patterns** - `get_entity_connections`, `get_entity_timeline`
3. **Track temporal evolution** - `compare_facts_over_time`
4. **Reference entities explicitly** - Enable auto-linking
5. **Organize with group_id** - Separate contexts

**The power comes from:**
- Bi-temporal tracking (when it happened vs when you learned it)
- Complete graph traversal (not just semantic search)
- Automatic entity deduplication
- Chronological timelines
- Temporal comparison built-in

**For pattern recognition:**
- Use `get_entity_connections` for COMPLETE data (guaranteed all relationships)
- Use `get_entity_timeline` for COMPLETE history (guaranteed all episodes)
- Use `compare_facts_over_time` for temporal evolution
- Analyze frequencies, temporal patterns, and related entities from complete datasets
- Don't rely solely on semantic search for pattern detection

Use this guide to build an AI agent that can track professional experiences over time and discover patterns that would be invisible day-to-day.
