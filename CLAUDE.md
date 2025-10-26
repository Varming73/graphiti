# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Graphiti is a Python framework for building temporally-aware knowledge graphs designed for AI agents. It enables real-time incremental updates to knowledge graphs without batch recomputation, making it suitable for dynamic environments.

Key features:

- Bi-temporal data model with explicit tracking of event occurrence times
- Hybrid retrieval combining semantic embeddings, keyword search (BM25), and graph traversal
- Support for custom entity definitions via Pydantic models
- Integration with Neo4j and FalkorDB as graph storage backends
- Optional OpenTelemetry distributed tracing support

## Development Commands

### Main Development Commands (run from project root)

```bash
# Install dependencies
uv sync --extra dev

# Format code (ruff import sorting + formatting)
make format

# Lint code (ruff + pyright type checking)
make lint

# Run tests
make test

# Run all checks (format, lint, test)
make check
```

### Server Development (run from server/ directory)

```bash
cd server/
# Install server dependencies
uv sync --extra dev

# Run server in development mode
uvicorn graph_service.main:app --reload

# Format, lint, test server code
make format
make lint
make test
```

### MCP Server Development (run from mcp_server/ directory)

```bash
cd mcp_server/
# Install MCP server dependencies
uv sync

# Run with Docker Compose
docker-compose up
```

## Code Architecture

### Core Library (`graphiti_core/`)

- **Main Entry Point**: `graphiti.py` - Contains the main `Graphiti` class that orchestrates all functionality
- **Graph Storage**: `driver/` - Database drivers for Neo4j and FalkorDB
- **LLM Integration**: `llm_client/` - Clients for OpenAI, Anthropic, Gemini, Groq
- **Embeddings**: `embedder/` - Embedding clients for various providers
- **Graph Elements**: `nodes.py`, `edges.py` - Core graph data structures
- **Search**: `search/` - Hybrid search implementation with configurable strategies
- **Prompts**: `prompts/` - LLM prompts for entity extraction, deduplication, summarization
- **Utilities**: `utils/` - Maintenance operations, bulk processing, datetime handling

### Server (`server/`)

- **FastAPI Service**: `graph_service/main.py` - REST API server
- **Routers**: `routers/` - API endpoints for ingestion and retrieval
- **DTOs**: `dto/` - Data transfer objects for API contracts

### MCP Server (`mcp_server/`)

- **MCP Implementation**: `graphiti_mcp_server.py` - Model Context Protocol server for AI assistants
- **Docker Support**: Containerized deployment with Neo4j

## Testing

- **Unit Tests**: `tests/` - Comprehensive test suite using pytest
- **Integration Tests**: Tests marked with `_int` suffix require database connections
- **Evaluation**: `tests/evals/` - End-to-end evaluation scripts

## Configuration

### Environment Variables

- `OPENAI_API_KEY` - Required for LLM inference and embeddings
- `USE_PARALLEL_RUNTIME` - Optional boolean for Neo4j parallel runtime (enterprise only)
- Provider-specific keys: `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, `GROQ_API_KEY`, `VOYAGE_API_KEY`

### Database Setup

- **Neo4j**: Version 5.26+ required, available via Neo4j Desktop
  - Database name defaults to `neo4j` (hardcoded in Neo4jDriver)
  - Override by passing `database` parameter to driver constructor
- **FalkorDB**: Version 1.1.2+ as alternative backend
  - Database name defaults to `default_db` (hardcoded in FalkorDriver)
  - Override by passing `database` parameter to driver constructor

## Development Guidelines

### Security Guidelines

Protect sensitive data and prevent common vulnerabilities:

- **Secrets Management**
  - Never commit API keys, tokens, or credentials to git
  - Use `.env` files for local development (ensure `.env` is in `.gitignore`)
  - Use environment variables for all sensitive configuration
  - Audit code before committing to ensure no secrets are exposed

- **Database Security**
  - Sanitize all user inputs before using in Cypher queries
  - Use parameterized queries to prevent Cypher injection (both Neo4j and FalkorDB support this)
  - For FalkorDB fulltext search: Always use the driver's `sanitize()` method to escape RedisSearch special characters
  - **Important for FalkorDB group_ids**: The `build_fulltext_query()` method does NOT sanitize group_ids before string interpolation. Always validate that group_ids contain only expected characters (alphanumeric, hyphens, underscores) before passing to this method. Never pass raw user input as group_ids without validation.
  - Avoid exposing raw database errors to users (information leakage)

- **LLM Security**
  - Be aware of prompt injection risks when user input flows to LLMs
  - Validate and sanitize user input before including in prompts
  - Don't blindly trust LLM outputs (validate before executing)
  - Log suspicious patterns but never log API keys or sensitive data

### AI/LLM Best Practices

Handle LLM integrations safely and efficiently:

- **Output Validation**
  - Always validate LLM responses against expected schemas
  - Handle malformed or incomplete responses gracefully
  - Use structured output modes when available (OpenAI, Gemini)
  - Have fallback strategies for validation failures

- **Error Handling**
  - Wrap LLM API calls in try/except blocks
  - Handle rate limits, timeouts, and API errors gracefully
  - Provide meaningful error messages without exposing internals
  - Consider retry logic with exponential backoff for transient failures

- **Cost & Performance**
  - Be mindful of token usage in prompts and outputs
  - Use appropriate models for each task (don't over-provision)
  - Cache embeddings and LLM results where appropriate
  - Monitor API costs in production environments

- **Prompt Engineering**
  - Keep prompts clear, specific, and concise
  - Test prompts with edge cases and unusual inputs
  - Version control prompts alongside code changes
  - Document prompt design decisions in comments

### Upstream Compatibility

Minimize divergence from the upstream repository to facilitate merging future updates:

- Prefer configuration over code changes where possible
- Keep modifications isolated and well-documented
- Avoid refactoring existing code unless necessary
- Add custom features as extensions rather than modifications

### Code Style

- Use Ruff for formatting and linting (configured in pyproject.toml)
- Line length: 100 characters
- Quote style: single quotes
- Type checking with Pyright is enforced
- Main project uses `typeCheckingMode = "basic"`, server uses `typeCheckingMode = "standard"`

### Testing Requirements

- Run tests with `make test` or `pytest`
- Integration tests require database connections and are marked with `_int` suffix
- Use `pytest-xdist` for parallel test execution
- Run specific test files: `pytest tests/test_specific_file.py`
- Run specific test methods: `pytest tests/test_file.py::test_method_name`
- Run only integration tests: `pytest tests/ -k "_int"`
- Run only unit tests: `pytest tests/ -k "not _int"`

### LLM Provider Support

The codebase supports multiple LLM providers but works best with services supporting structured output (OpenAI, Gemini). Other providers may cause schema validation issues, especially with smaller models.

### MCP Server Usage Guidelines

When working with the MCP server, follow the patterns established in `mcp_server/cursor_rules.md`:

- Always search for existing knowledge before adding new information
- Use specific entity type filters (`Preference`, `Procedure`, `Requirement`)
- Store new information immediately using `add_memory`
- Follow discovered procedures and respect established preferences