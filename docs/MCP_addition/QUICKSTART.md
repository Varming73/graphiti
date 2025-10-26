# Quick Start: Using Claude Code to Implement Dynamic Graph Discovery

## Overview

This guide helps you use Claude Code to implement the dynamic graph discovery feature in your Graphiti MCP server fork.

## Prerequisites

1. **Claude Code installed:**
   ```bash
   npm install -g @anthropic-ai/claude-code
   ```

2. **Your Graphiti fork cloned:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/graphiti.git
   cd graphiti
   ```

3. **These implementation files downloaded:**
   - IMPLEMENTATION_GUIDE.md
   - code_changes.py
   - TESTING_GUIDE.md
   - CLAUDE.md

## Step 1: Set Up Your Fork

```bash
# Navigate to your graphiti fork
cd /path/to/your/graphiti/fork

# Create a feature branch
git checkout -b feature/dynamic-graph-discovery

# Copy the implementation files to your project root
cp /path/to/downloads/CLAUDE.md ./CLAUDE.md
cp /path/to/downloads/IMPLEMENTATION_GUIDE.md ./docs/IMPLEMENTATION_GUIDE.md
cp /path/to/downloads/code_changes.py ./docs/code_changes.py
cp /path/to/downloads/TESTING_GUIDE.md ./docs/TESTING_GUIDE.md
```

## Step 2: Launch Claude Code

From your project root directory:

```bash
# Start Claude Code
claude
```

Claude will launch and be able to see all your project files, including the CLAUDE.md context.

## Step 3: Give Claude the Task

Once Claude Code is running, use this prompt:

```
I need you to implement the dynamic graph discovery feature for the Graphiti MCP server.

Please read these files first:
1. CLAUDE.md - Project context and design decisions
2. docs/IMPLEMENTATION_GUIDE.md - Step-by-step implementation plan
3. docs/code_changes.py - Exact code to implement

Then:
1. Implement the changes in mcp_server/graphiti_mcp_server.py
2. Make sure to follow the patterns exactly
3. Add the three new tools: list_graphs(), create_graph(), and modify add_episode()
4. Apply the same pattern to search() and any other graph tools
5. Update the CLI arguments section

After implementing, please:
- Show me a summary of changes made
- Run any syntax checks
- Create a commit with a good message

Take your time and make sure each change follows the design in CLAUDE.md.
```

## Step 4: Review Claude's Work

Claude Code will:
1. Read all the context files
2. Understand the architecture
3. Implement the changes
4. Show you diffs for review

**Important:** Review each change carefully. Claude will show them as diffs in your IDE.

## Step 5: Test the Implementation

After Claude finishes:

```bash
# Install dependencies
pip install -r requirements.txt

# Start FalkorDB
docker run -p 6379:6379 -p 3000:3000 -it --rm falkordb/falkordb:latest

# In another terminal, start the MCP server
python mcp_server/graphiti_mcp_server.py --group-id default --strict-graphs

# Run tests (you can ask Claude to help create test scripts)
```

Follow TESTING_GUIDE.md for comprehensive test scenarios.

## Step 6: Commit Your Changes

```bash
# Stage the changes
git add mcp_server/graphiti_mcp_server.py

# Commit (Claude can help with this)
git commit -m "feat: Add dynamic graph discovery with strict mode

- Add list_graphs() tool for dynamic discovery
- Add create_graph() tool for explicit graph creation
- Add group_id parameter to all graph tools
- Implement strict mode validation
- Use FalkorDB native multi-tenancy

Enables domain isolation without instance pooling."

# Push to your fork
git push origin feature/dynamic-graph-discovery
```

## Alternative: Step-by-Step Approach

If you prefer more control, break it into smaller tasks:

### Task 1: Add Connection Helper
```
Claude, please add the FalkorDB connection helper function to mcp_server/graphiti_mcp_server.py.
See the pattern in code_changes.py under "MODULE-LEVEL ADDITIONS".
```

### Task 2: Add list_graphs() Tool
```
Now add the list_graphs() tool. Use the complete implementation from code_changes.py.
```

### Task 3: Add create_graph() Tool
```
Add the create_graph() tool with all validation logic.
```

### Task 4: Modify add_episode()
```
Modify the existing add_episode() tool to add the group_id parameter and validation.
See the complete implementation in code_changes.py.
```

### Task 5: Modify Other Tools
```
Apply the same pattern to search(), get_nodes(), and any other tools that interact with the graph.
```

## Common Claude Code Commands

During implementation:

- **Stop Claude:** Press `Escape` (not Ctrl+C)
- **See previous messages:** `Escape` twice
- **Accept a change:** Review in IDE diff viewer, then accept
- **Reject a change:** Reject in IDE diff viewer
- **Run a command:** Claude will ask permission
- **Skip permissions:** `claude --dangerously-skip-permissions` (if you trust the prompt)

## Troubleshooting

### Claude seems confused
```
Claude, please re-read CLAUDE.md and IMPLEMENTATION_GUIDE.md to understand the architecture.
The key insight is that we DON'T need instance pooling - FalkorDB handles multi-tenancy natively.
```

### Changes don't look right
```
Claude, compare your implementation to the exact code in code_changes.py.
Make sure you're following the pattern exactly, especially:
1. Using graph_name parameter in Graphiti()
2. Validating graph existence in strict mode
3. Returning helpful error messages
```

### Need to start over
```bash
# Discard changes and restart
git checkout mcp_server/graphiti_mcp_server.py
claude  # Start fresh conversation
```

## Advanced: Running Tests with Claude

After implementation:

```
Claude, now let's test the implementation.

1. First, help me create an automated test script based on TESTING_GUIDE.md
2. Run the tests and tell me which ones pass/fail
3. Fix any issues that come up

Start by reading docs/TESTING_GUIDE.md to understand what we need to test.
```

## What to Expect

**Time estimate:** 30-60 minutes total
- Claude reading context: 2-5 minutes
- Implementation: 15-30 minutes
- Review and adjustments: 10-15 minutes
- Testing: 15-20 minutes

**Output:**
- Modified `mcp_server/graphiti_mcp_server.py` with all changes
- Clean git commit ready to push
- Tested and working implementation

## Tips for Success

1. **Let Claude read the context first** - Don't rush into coding
2. **Review every diff** - Don't blindly accept changes
3. **Test incrementally** - Ask Claude to test after each major change
4. **Use the exact patterns** - The code_changes.py file has proven patterns
5. **Ask questions** - Claude has full context from CLAUDE.md

## Getting Help

If you run into issues:

1. **Check CLAUDE.md** - Design decisions are documented
2. **Read error messages** - They're designed to be helpful
3. **Ask Claude to explain** - "Why did you implement it this way?"
4. **Compare to code_changes.py** - Reference implementation
5. **Test in isolation** - Test each tool independently

## After Successful Implementation

1. ✅ All tests pass (see TESTING_GUIDE.md)
2. ✅ Code follows patterns in code_changes.py
3. ✅ Helpful error messages guide users
4. ✅ Git commit is clean and descriptive
5. ✅ Ready to create PR or continue development

## Next Steps

After merging this feature:
- Document in README with examples
- Consider adding `delete_graph()` tool
- Consider adding `suggest_graph()` for AI assistance
- Monitor usage and iterate

---

**Good luck!** Claude Code + these detailed guides should make implementation smooth. 🚀
