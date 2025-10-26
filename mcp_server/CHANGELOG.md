# Changelog

All notable changes to the Graphiti MCP Server production readiness project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Project Management Setup - 2025-10-26
#### Added
- Project management documentation structure
- `docs/PROJECT_PLAN.md` - 3-phase approach for production readiness
- `docs/ADR.md` - Architecture decision record with 8 initial decisions
- `docs/SESSION_LOG.md` - Session tracking and testing log
- `CHANGELOG.md` - This file

#### Documentation
- Established phased approach: Shareable Hobby → Public Release → Production
- Documented all architecture decisions (ADR-001 through ADR-008)
- Created detailed Session 1A plan with parallel agent strategy

---

## [0.4.0] - Baseline (Before Production Readiness Project)

### Existing Features
- FastMCP server implementation with SSE and stdio transports
- Support for Neo4j and FalkorDB database backends
- 8 MCP tools:
  - `add_memory` - Add episodes to knowledge graph
  - `search_memory_nodes` - Search for entities
  - `search_memory_facts` - Search for relationships
  - `delete_entity_edge` - Delete relationships
  - `delete_episode` - Delete episodes
  - `get_entity_edge` - Retrieve specific relationships
  - `get_episodes` - Retrieve recent episodes
  - `clear_graph` - Clear all data
- Custom entity types (Requirement, Preference, Procedure)
- Sequential episode processing per group_id
- Docker deployment with docker-compose
- Azure OpenAI support with managed identity

### Known Issues (To Be Addressed)
- No group_id validation (RedisSearch injection risk)
- No UUID validation
- Potential API key exposure in logs
- Global state management issues
- Race condition in queue creation
- No queue size limits (memory exhaustion risk)
- Minimal input validation
- Inconsistent error messages
- No comprehensive test suite
- No LLM failure retry logic

---

## Session-Based Changes

Changes will be organized by development session as they are completed.

### Session 1A: Quick Security Wins
**Status:** ✅ Completed
**Date:** 2025-10-26

#### Added
- `validate_group_id_mcp()` function (mcp_server/graphiti_mcp_server.py:633-661)
  - Prevents RedisSearch injection attacks via malicious group_ids
  - Only allows alphanumeric characters, hyphens, and underscores
  - Applied to: add_memory, search_memory_nodes, search_memory_facts, get_episodes
- `validate_uuid_mcp()` function (mcp_server/graphiti_mcp_server.py:664-681)
  - Validates UUID format to prevent database errors
  - Applied to: delete_entity_edge, delete_episode, get_entity_edge
- `SensitiveDataFilter` logging filter class (mcp_server/graphiti_mcp_server.py:569-630)
  - Automatically redacts API keys, passwords, tokens, JWTs from logs
  - Prevents accidental secret exposure in error messages
  - Applied to root logger
- Security Model section in README.md (mcp_server/README.md:439-526)
  - Documents trusted-network-only deployment model
  - Lists security limitations and best practices
  - Describes input validation mechanisms

#### Security Fixes
- ✅ Prevents RedisSearch injection via group_id validation (FalkorDB-specific)
- ✅ Prevents database errors from invalid UUID formats
- ✅ Prevents API key exposure in application logs
- ✅ Documents trusted-network-only security requirements

#### Implementation Notes
- All 7 MCP tools now validate inputs before processing
- Validation returns user-friendly error messages
- Log filter applied globally to all loggers
- Zero breaking changes to existing API

---

### Session 1.5: Group Discovery & Cross-Domain Linking
**Status:** Not Started
**Date:** TBD (After Session 1A)
**Duration:** 3-4 hours

#### Planned Additions
- Group ID normalization (lowercase with hyphens)
- `list_group_ids()` MCP tool with fuzzy matching - Discover existing domains and suggest similar names
- `set_group_description()` MCP tool with normalization - Attach human-readable descriptions
- `link_entities()` MCP tool - Create SAME_AS edges for cross-domain entities
- `find_linked_entities()` helper - Traverse SAME_AS edges
- All 8 MCP tool docstrings updated with intelligent workflow guidance
- Redis metadata storage for group_id descriptions
- Documentation for AI-driven group_id management and cross-domain linking

#### New Features
- **Cross-domain entity linking:** Same person across domains (e.g., "Rune Bysted" as friend AND colleague)
- AI can discover existing domains to prevent fragmentation
- Normalization prevents "Personal" vs "personal" duplicates
- Fuzzy matching suggests similar group_ids for typos
- Self-documenting organization with descriptive labels
- Uses graph database power properly (SAME_AS edges for relationships)
- Comprehensive workflow guidance in all 8 existing MCP tools
- Zero divergence from upstream Graphiti (MCP-only extension)

#### Implementation Details
- Location: `mcp_server/graphiti_mcp_server.py` only (no `graphiti_core/` changes)
- Uses existing `validate_group_id()` from `graphiti_core/helpers.py`
- Uses existing `EntityEdge` structure for SAME_AS edges
- Leverages existing BFS traversal (search.py:220-248)
- Metadata stored in Redis: `graph_meta:{group_id}` keys
- Query: `MATCH (n) WHERE n.group_id IS NOT NULL RETURN DISTINCT n.group_id`
- Fuzzy matching with `rapidfuzz` library

#### Use Case Example
```
Episode 1 (personal): "I went for a walk with my friend Rune Bysted"
→ Creates EntityNode(name="Rune Bysted", group_id="personal")

Episode 2 (work): "I had a meeting with Rune about the project"
→ Creates EntityNode(name="Rune Bysted", group_id="work")
→ AI calls link_entities() to connect them
→ Creates EntityEdge(name="SAME_AS", ...)

Query: "What do I know about Rune?"
→ Returns unified view: friend + former boss + current colleague
```

---

### Session 1B: Critical Error Handling
**Status:** Not Started
**Date:** TBD (After Session 1.5)

#### Planned Additions
- Queue size limits with overflow handling
- Comprehensive input validation
- Standardized error messages

---

## Future Phases

### Phase 2: Public Release Ready (Week 2)
**Status:** Not Started

Planned work:
- Complete test suite (60-70% coverage)
- Fix race conditions
- Refactor global state
- Complete input validation

### Phase 3: Production Hardened (Week 3)
**Status:** Not Started

Planned work:
- LLM failure handling with retry logic
- Database driver factory pattern
- Security hardening
- Production documentation

---

## Version History Notes

**Version Numbering:**
- Major version (X.0.0): Breaking changes
- Minor version (0.X.0): New features, backward compatible
- Patch version (0.0.X): Bug fixes, backward compatible

**Current Development:**
- Working toward v0.5.0 (Phase 1 completion)
- Target v1.0.0 (Phase 3 completion - production ready)

---

## Migration Guides

### From 0.4.0 to 0.5.0 (Planned)
TBD after Session 1 completion

**Expected Breaking Changes:**
- group_id validation may reject previously accepted values
- Error response formats may change
- Queue behavior changes with size limits

**Migration Steps:**
TBD

---

## Security Advisories

### Baseline (0.4.0) - Known Vulnerabilities
**Severity:** HIGH

1. **RedisSearch Injection via group_id**
   - **Impact:** Malicious group_ids can manipulate database queries
   - **Status:** To be fixed in Session 1A
   - **Workaround:** Only accept group_ids from trusted sources

2. **API Key Exposure in Logs**
   - **Impact:** Secrets may be logged in error messages
   - **Status:** To be fixed in Session 1A
   - **Workaround:** Carefully review and sanitize logs

3. **No Authentication**
   - **Impact:** Anyone with network access can modify data
   - **Status:** Documented as trusted-network-only
   - **Workaround:** Deploy behind firewall/VPN only

### Session 1A - Security Fixes
**Status:** Planned

Will address vulnerabilities #1 and #2 above.

---

## Deprecation Notices

None at this time.

---

## Credits

**Original Implementation:** Zep AI (Graphiti project)
**Production Hardening:** lvarming (PO), Claude Code (Developer)
**Project Start:** October 26, 2025

---

## Links

- [Project Plan](../docs/PROJECT_PLAN.md)
- [Architecture Decisions](../docs/ADR.md)
- [Session Log](../docs/SESSION_LOG.md)
- [Main Documentation](../CLAUDE.md)
- [Upstream Graphiti](https://github.com/getzep/graphiti)
