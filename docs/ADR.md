# Architecture Decision Record (ADR)

This document records all significant architectural decisions made during the MCP Server production readiness project.

---

## ADR-001: Global State Refactoring Strategy

**Date:** 2025-10-26
**Status:** Approved
**Deciders:** lvarming (PO), Claude Code (Developer)

### Context
The current implementation uses global mutable state (`config`, `graphiti_client`, `episode_queues`) which creates testing challenges, thread-safety concerns, and tight coupling.

### Decision
**Use FastMCP Context Management (Option A)**

### Rationale
- Minimal change to existing codebase
- Leverages FastMCP's built-in context features
- Less invasive refactor while achieving cleaner architecture
- Keeps code similar to current structure for easier maintenance
- Faster to implement (aligns with 3-week timeline)

### Consequences

**Positive:**
- Easier to test (can inject mock clients)
- Better separation of concerns
- Maintains compatibility with FastMCP patterns
- Reduces global state issues

**Negative:**
- Still somewhat coupled to FastMCP framework
- Not as pure as full DI, but acceptable trade-off

### Alternatives Considered
- **Option B: Dependency Injection Container** - More refactoring, cleaner long-term but overkill for current scope
- **Option C: Singleton Pattern** - Middle ground but doesn't leverage FastMCP features

---

## ADR-002: Input Validation Strategy

**Date:** 2025-10-26
**Status:** Approved
**Deciders:** lvarming (PO), Claude Code (Developer)

### Context
The current implementation has minimal input validation, leading to potential security issues and poor error messages.

### Decision
**Fail Fast with Strict Validation (Option A)**

### Rationale
- Better user experience with immediate, clear error messages
- Catches problems before expensive LLM API calls
- Prevents security issues (injection attacks)
- Aligns with security-first approach
- More validation code but better long-term quality

### Consequences

**Positive:**
- Security vulnerabilities prevented early
- Users get helpful error messages
- Reduced waste of API calls on invalid inputs
- Easier to debug issues

**Negative:**
- More code to write and maintain
- Potentially less flexible for edge cases
- Need to ensure validation doesn't reject valid inputs

### Implementation Requirements
1. Validate group_ids: alphanumeric + hyphens/underscores only
2. Validate UUIDs: proper UUID format
3. Validate strings: non-empty where required
4. Validate numbers: positive integers, reasonable bounds
5. Validate JSON: valid JSON format when source='json'
6. Validate entity types: must be in allowed list

### Alternatives Considered
- **Option B: Permissive with Warnings** - More flexible but risk of silent failures

---

## ADR-003: Error Response Format

**Date:** 2025-10-26
**Status:** Approved
**Deciders:** lvarming (PO), Claude Code (Developer)

### Context
Need to standardize how errors are communicated to MCP clients.

### Decision
**Continue with Current TypedDict Approach (Option A)**

### Rationale
- Simple and consistent with current implementation
- Sufficient for MCP protocol needs
- Easier to implement and maintain
- No need for complex error codes at this stage

### Consequences

**Positive:**
- Simple, clear error responses
- Easy to implement
- Consistent with existing code

**Negative:**
- No error codes for programmatic handling
- Clients must parse error messages

### Format
```python
ErrorResponse(error="User-friendly message describing what went wrong")
```

### Improvement Plan
Focus on making error messages:
- User-friendly (not technical jargon)
- Actionable (tell user how to fix)
- Specific (what exactly was wrong)
- Safe (don't expose internals or secrets)

### Alternatives Considered
- **Option B: Structured Errors with Codes** - Overkill for current needs, can add later if clients need it

---

## ADR-004: Testing Coverage Philosophy

**Date:** 2025-10-26
**Status:** Approved
**Deciders:** lvarming (PO), Claude Code (Developer)

### Context
Need to balance comprehensive testing with time constraints of 3-week timeline.

### Decision
**Phased Approach: Critical Paths → Comprehensive**
- Phase 2 (Week 2): 60-70% coverage (Option A)
- Phase 3 (Week 3): Expand to 80%+ coverage (Option B)

### Rationale
- Pragmatic approach balancing quality and timeline
- Critical paths tested first (highest risk areas)
- Can expand coverage incrementally
- Allows early delivery of value

### Consequences

**Positive:**
- Faster initial delivery
- Focuses effort on highest-risk code
- Can ship earlier while still improving quality
- Incremental approach reduces risk

**Negative:**
- Some edge cases may not be covered initially
- Need discipline to actually expand coverage in Phase 3

### Testing Priorities (in order)
1. **Critical Path Tests (Phase 2)**
   - All 8 MCP tool functions (happy path)
   - Input validation functions
   - Error handling for common failures
   - Configuration loading

2. **Comprehensive Tests (Phase 3)**
   - Edge cases and boundary conditions
   - Concurrent access scenarios
   - Database failure scenarios
   - LLM API failure scenarios
   - All error paths

3. **Future (post-project)**
   - Performance/load testing
   - Integration tests with real databases
   - End-to-end user scenarios

### Alternatives Considered
- **Option C: 90%+ Coverage from Start** - Too time-consuming for 3-week timeline

---

## ADR-005: Database Driver Factory Pattern

**Date:** 2025-10-26
**Status:** Approved
**Deciders:** lvarming (PO), Claude Code (Developer)

### Context
Currently supports Neo4j and FalkorDB with if/elif logic. Need to make it easier to add new database backends.

### Decision
**Simple if/elif Factory with Clear Extension Points (Option A)**

### Rationale
- Quick to implement (fits 3-week timeline)
- Works well for 2-3 databases
- Can be refactored to plugin architecture later if needed
- Clear code that's easy to understand
- Sufficient for current and near-term needs

### Consequences

**Positive:**
- Easy to implement and test
- Clear, readable code
- Works for current needs (Neo4j, FalkorDB)
- Can add 1-2 more databases without issues

**Negative:**
- Will need refactoring if supporting many (5+) databases
- Less "enterprise" than plugin architecture
- Violates Open/Closed Principle slightly

### Implementation Pattern
```python
def create_driver(config: GraphitiConfig) -> GraphDriver:
    if config.database_type == 'neo4j':
        return Neo4jDriver(...)
    elif config.database_type == 'falkordb':
        return FalkorDriver(...)
    else:
        raise ValueError(f'Unsupported database type: {config.database_type}')
```

With clear documentation on how to add new drivers.

### Extension Plan
Document in code comments:
1. Create new driver class inheriting from GraphDriver
2. Add configuration class
3. Add elif clause in factory
4. Update environment variable documentation

### Alternatives Considered
- **Option B: Plugin-based Architecture** - Overkill for 2-3 databases, adds unnecessary complexity

---

## ADR-006: Upstream Compatibility Strategy

**Date:** 2025-10-26
**Status:** Approved
**Deciders:** lvarming (PO), Claude Code (Developer)

### Context
This is a fork/customization of upstream Graphiti project. Need to maintain ability to merge upstream updates.

### Decision
**Minimize Divergence Through Extensions and Configuration**

### Rationale
- Documented in CLAUDE.md as core principle
- Makes merging upstream updates easier
- Reduces maintenance burden
- Allows benefiting from upstream improvements

### Consequences

**Positive:**
- Can easily merge upstream bug fixes and features
- Less merge conflict resolution
- Smaller maintenance burden

**Negative:**
- May constrain some implementation choices
- Requires discipline to follow principle

### Guidelines (from CLAUDE.md)
1. Prefer configuration over code changes where possible
2. Keep modifications isolated and well-documented
3. Avoid refactoring existing Graphiti core code
4. Add custom features as extensions rather than modifications

### Application to This Project
- MCP server is separate module (good isolation)
- Changes to `graphiti_core` should be minimal
- Document any necessary core changes clearly
- Prefer wrapper patterns over modifying core classes

---

## ADR-007: Security Model for Initial Release

**Date:** 2025-10-26
**Status:** Approved
**Deciders:** lvarming (PO), Claude Code (Developer)

### Context
MCP server needs authentication for production use, but implementing auth is complex and time-consuming.

### Decision
**Trusted-Network-Only for Initial Release**

Document clearly that:
- Server has no authentication
- Should only run in trusted environments
- Network-level security required (firewall, VPN, etc.)
- Remote access authentication is future work

### Rationale
- Allows focusing on core functionality and security hardening
- Clearly sets expectations for users
- Can add authentication later as separate project
- Common pattern for internal tools

### Consequences

**Positive:**
- Simpler initial implementation
- Faster delivery
- Clear expectations set
- Can add auth later without breaking changes

**Negative:**
- Cannot be deployed to public internet safely
- Users must secure network access
- Limited deployment scenarios

### Documentation Requirements
1. Prominent warning in README.md
2. Security model documentation
3. Deployment guide with network security recommendations
4. Clear roadmap for authentication feature

### Future Authentication Options
- API key authentication
- OAuth 2.0
- mTLS (mutual TLS)
- Integration with existing auth systems

---

## ADR-008: Logging and Observability

**Date:** 2025-10-26
**Status:** Approved
**Deciders:** lvarming (PO), Claude Code (Developer)

### Context
Current logging is plain text with potential for sensitive data exposure.

### Decision
**Sanitize Logs, Keep Plain Text Format**

For this phase:
- Implement log filtering to prevent API key/secret exposure
- Keep plain text format (easier for development)
- Document structured logging as future enhancement

### Rationale
- Addresses immediate security concern
- Plain text is easier to debug during development
- Structured logging can be added later without major refactoring
- Fits 3-week timeline

### Consequences

**Positive:**
- No secret exposure in logs
- Easy to read logs during development
- Simple to implement

**Negative:**
- Harder to parse logs programmatically
- Not ideal for production log aggregation

### Implementation Requirements
1. Create log filter class
2. Redact patterns: API keys, passwords, tokens
3. Apply to all loggers
4. Test with sensitive data

### Future Enhancements (out of scope)
- Structured logging (JSON format)
- Log aggregation integration (ELK, CloudWatch, etc.)
- OpenTelemetry tracing
- Metrics collection

---

## Decision Making Process

**For New Decisions:**
1. Identify decision point
2. Document context and options
3. Discuss with PO (lvarming)
4. Record decision with rationale
5. Implement according to decision
6. Update ADR with any lessons learned

**Review Schedule:**
- After each phase completion
- When significant new requirements emerge
- When architectural issues discovered

---

## Change Log

| Date | ADR | Change | Reason |
|------|-----|--------|--------|
| 2025-10-26 | All | Initial decisions | Project kickoff |

---

## References

- Project Plan: [PROJECT_PLAN.md](./PROJECT_PLAN.md)
- Session Log: [SESSION_LOG.md](./SESSION_LOG.md)
- Main Project Documentation: [../CLAUDE.md](../CLAUDE.md)
