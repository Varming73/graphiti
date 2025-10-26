# MCP Server Production Readiness Project Plan

**Project Owner:** lvarming
**Start Date:** 2025-10-26
**Target Completion:** 3 weeks (mid-November 2025)
**Status:** Planning → Execution

---

## Project Overview

Transform the Graphiti MCP Server from a functional proof-of-concept into a production-ready system suitable for public sharing and real-world use. Focus on security hardening, comprehensive testing, and architectural improvements while maintaining upstream compatibility with the original Graphiti project.

---

## Scope

**In Scope:**
- Critical and High priority security fixes
- Medium priority improvements (input validation, error handling, architecture)
- Security hardening and documentation
- Database driver factory pattern
- Comprehensive test suite

**Out of Scope (for now):**
- Authentication implementation (trusted-network-only documented instead)
- LOW priority items (monitoring stack, load testing, CI/CD)
- Remote MCP server authentication (future phase)

---

## Success Criteria

### Phase 1 Success Criteria
- ✅ No critical security vulnerabilities remain
- ✅ Input validation prevents malicious inputs
- ✅ Logs don't expose sensitive data
- ✅ AI can discover and manage group_ids intelligently (normalization + fuzzy matching)
- ✅ Cross-domain entities can be linked (SAME_AS edges work)
- ✅ All MCP tools have intelligent workflow guidance in docstrings
- ✅ "Rune Bysted" use case works (same person as friend AND colleague)
- ✅ Can share with technical colleagues without concerns

### Phase 2 Success Criteria
- ✅ 60-70% test coverage on critical paths
- ✅ All race conditions resolved
- ✅ Clean architecture without global state issues
- ✅ Professional code quality suitable for public GitHub

### Phase 3 Success Criteria
- ✅ Handles LLM API failures gracefully with retries
- ✅ Database driver easily extensible to new backends
- ✅ Security documentation complete
- ✅ Production deployment guide available
- ✅ Ready for production use with real data

---

## Three-Phase Approach

## Phase 1: Shareable Hobby Project (Week 1)

**Goal:** Safe to use in trusted environments and share with technical friends

### Session 1A: Quick Security Wins (2-3 hours)
**Deliverables:**
- group_id validation (regex pattern, alphanumeric + hyphens/underscores)
- UUID validation for all UUID parameters
- Log sanitization to prevent API key exposure
- Documentation of trusted-network-only requirement

**Testing Required:**
- Test malicious group_id inputs
- Test invalid UUID formats
- Verify logs don't contain secrets
- FalkorDB-specific validation testing

### Session 1.5: Group Discovery & Cross-Domain Linking (3-4 hours)
**Deliverables:**
- Group ID normalization (lowercase with hyphens)
- `list_group_ids()` MCP tool with fuzzy matching - Discover existing domains and suggest similar names
- `set_group_description()` MCP tool with normalization - Attach human-readable descriptions
- `link_entities()` MCP tool - Create SAME_AS edges for cross-domain entities
- `find_linked_entities()` helper - Traverse SAME_AS edges
- All 8 MCP tool docstrings updated with intelligent workflow guidance
- Metadata storage in Redis (FalkorDB connection)
- Documentation for AI-driven group_id management and cross-domain linking

**Testing Required:**
- Test normalization: "Work_Projects" → "work-projects"
- Test fuzzy matching: "personl" suggests "personal"
- Test setting and retrieving descriptions
- Test "Rune Bysted" use case: friend (personal) AND colleague (work) linked via SAME_AS edge
- Test SAME_AS edge creation and bidirectional traversal
- Verify Redis metadata persistence
- Test with no existing group_ids (empty graph)
- Verify integration with all existing tools

**Implementation Notes:**
- **Zero divergence from upstream Graphiti** - MCP server only, no changes to `graphiti_core/`
- Uses existing `validate_group_id()` from `graphiti_core/helpers.py`
- Uses existing `EntityEdge` structure for SAME_AS edges
- Leverages existing BFS traversal (search.py:220-248)
- Query: `MATCH (n) WHERE n.group_id IS NOT NULL RETURN DISTINCT n.group_id`
- Metadata: `SET graph_meta:{group_id} {description}` (Redis keys)
- Fuzzy matching with `rapidfuzz` library

**Why This Matters:**
- **Solves real architectural gap:** Same person across domains (Rune as friend AND colleague)
- Prevents AI from creating duplicate group_ids ("personal" vs "Personal")
- Uses graph database power properly (SAME_AS edges for relationships)
- Improves long-term maintainability with descriptive labels and entity linking
- Comprehensive workflow guidance in all 8 existing MCP tools
- Self-documenting data organization
- Natural checkpoint for AI before creating new domains

### Session 1B: Critical Error Handling (2-3 hours)
**Deliverables:**
- Queue size limits with overflow handling
- Basic input validation (empty strings, negative numbers, invalid source types)
- User-friendly error messages (standardized format)

**Testing Required:**
- Test queue overflow scenarios
- Test all invalid inputs
- Verify error messages are helpful

**Phase 1 Milestone:** Code is safe to share and use in trusted environments, with intelligent group_id management and cross-domain entity linking

---

## Phase 2: Public Release Ready (Week 2)

**Goal:** Professional quality, ready for GitHub stars

### Session 2A: Test Foundation (3-4 hours)
**Deliverables:**
- Complete test suite structure (`mcp_server/tests/`)
- Unit tests for all 8 MCP tools
- Error case testing
- Validation function testing
- Test fixtures and mocks

**Testing Required:**
- Run full test suite: `pytest mcp_server/tests/`
- Verify 60-70% code coverage
- All tests pass

### Session 2B: Architecture Cleanup (3-4 hours)
**Deliverables:**
- Fix queue creation race condition (asyncio.Lock)
- Refactor global state (FastMCP context or DI pattern)
- Complete input validation (JSON validation, entity type checks)
- Comprehensive edge case handling

**Testing Required:**
- Test concurrent requests
- Verify no regressions
- Test all edge cases
- Validate JSON episode bodies

**Phase 2 Milestone:** Professional, well-tested code ready for public sharing

---

## Phase 3: Production Hardened (Week 3)

**Goal:** Ready for real-world use with production data

### Session 3A: Resilience (2-3 hours)
**Deliverables:**
- LLM failure handling (specific exceptions, retry with exponential backoff)
- Rate limit handling
- Timeout handling
- Complete test coverage for failure scenarios

**Testing Required:**
- Test with intentional failures (disconnect DB, invalid API key)
- Test retry logic
- Verify graceful degradation

### Session 3B: Production Features (2-3 hours)
**Deliverables:**
- Database driver factory pattern
- Security hardening (dependency scanning setup, security checklist)
- Production deployment documentation
- Security model documentation

**Testing Required:**
- Test database driver switching (Neo4j ↔ FalkorDB)
- Run vulnerability scans
- Review security documentation

**Phase 3 Milestone:** Production-ready system with proper error handling and extensibility

---

## Timeline & Milestones

| Phase | Duration | Target Completion | Key Deliverable |
|-------|----------|-------------------|-----------------|
| Phase 1 | Week 1 (7-10 hours: 1A=2-3h, 1.5=3-4h, 1B=2-3h) | Nov 2, 2025 | Shareable hobby project with AI group management & cross-domain linking |
| Phase 2 | Week 2 (2 sessions: 6-8 hours) | Nov 9, 2025 | Public release ready |
| Phase 3 | Week 3 (2 sessions: 4-6 hours) | Nov 16, 2025 | Production hardened |

**Daily Testing Schedule:** PO tests deliverables within 24 hours of session completion

---

## Risk Management

### Technical Risks
| Risk | Impact | Mitigation |
|------|--------|------------|
| FalkorDB-specific quirks | Medium | Early testing in Phase 1 |
| Test failures reveal architecture issues | Medium | Flexible refactoring time |
| LLM API changes | Low | Use stable API versions |

### Schedule Risks
| Risk | Impact | Mitigation |
|------|--------|------------|
| Testing feedback delays | Medium | Daily testing commitment |
| Scope creep | High | Strict adherence to defined scope |
| Environment setup issues | Low | Test environment ready upfront |

---

## Resource Requirements

**Developer:** Claude Code (AI pair programming)
**Product Owner/PM:** lvarming
**Testing Environment:** FalkorDB + OpenAI API
**Tools:** pytest, uv, ruff, Docker

---

## Dependencies

**External:**
- FalkorDB instance available for testing
- OpenAI API key for LLM testing
- UV package manager installed

**Internal:**
- CLAUDE.md architecture guidelines followed
- Upstream compatibility maintained
- All changes preserve existing functionality

---

## Change Management

**Version Control Strategy:**
- **Model:** Fork workflow (origin = Varming73/graphiti, upstream = getzep/graphiti)
- **Verified:** Upstream has NO dev branch (uses main + feature branches)
- **Feature Branches:** Each session in separate feature branch (feature/session-X-description)
- **Main Branch:** Contains tested, production-ready code
- **Detailed Workflow:** See [GIT_WORKFLOW.md](GIT_WORKFLOW.md)

**Commit Standards:**
- Conventional commits format: `type(scope): description`
- Descriptive messages with session references
- Co-authored by Claude Code

**Documentation Updates:**
- CHANGELOG.md updated after each session
- SESSION_LOG.md tracks progress
- README updates for new features/requirements
- GIT_WORKFLOW.md for workflow guidance

**Upstream Compatibility:**
- Prefer configuration over code changes
- Keep modifications isolated and well-documented
- Avoid refactoring existing Graphiti core code
- Extensions over modifications
- Periodic sync with upstream/main (weekly or before major features)

---

## Communication Plan

**Session Start:**
- Review session plan in SESSION_LOG.md
- Confirm testing environment ready
- PO approval to proceed

**During Session:**
- Real-time progress via TodoWrite tool
- Agent outputs visible as they complete

**Session End:**
- Summary of deliverables
- Testing instructions provided
- Next session plan outlined

**Between Sessions:**
- PO tests deliverables
- PO provides pass/fail feedback
- Issues logged in SESSION_LOG.md

---

## Quality Standards

**Code Quality:**
- Follows Ruff formatting (100 char line length, single quotes)
- Type hints with Pyright validation
- No global mutable state (after Phase 2)
- Comprehensive error handling

**Testing Standards:**
- 60-70% coverage minimum (Phase 2)
- All critical paths tested
- Error cases covered
- FalkorDB-specific scenarios tested

**Security Standards:**
- No secrets in code or logs
- Input validation on all user inputs
- Parameterized database queries
- Security documentation complete

**Documentation Standards:**
- All architectural decisions recorded in ADR.md
- Session outcomes in SESSION_LOG.md
- Changes tracked in CHANGELOG.md
- README updated for new requirements

---

## Post-Project

**Future Enhancements (not in scope):**
- Remote MCP server authentication
- Monitoring and metrics (OpenTelemetry)
- Load testing and performance optimization
- CI/CD pipeline
- Additional database backends

**Maintenance Plan:**
- Monitor upstream Graphiti changes
- Merge upstream updates regularly
- Keep dependencies updated
- Security vulnerability monitoring

---

## Approval

**Plan Approved By:** lvarming
**Date:** 2025-10-26
**Next Review:** After Phase 1 completion

---

## Notes

- This plan prioritizes security and quality over speed
- Each phase delivers incremental value
- Testing feedback loops are critical to success
- Upstream compatibility must be maintained throughout
