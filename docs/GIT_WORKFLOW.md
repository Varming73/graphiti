# Git Workflow for Graphiti Production Readiness Project

**Last Updated:** 2025-10-26
**Owner:** lvarming
**Strategy:** Fork Workflow with Feature Branches

---

## Repository Structure

```
Official Repository (upstream):
getzep/graphiti
  └─ main (stable releases)
  └─ feature/* (various feature branches)

Your Fork (origin):
Varming73/graphiti
  └─ main ← Your production-ready branch
  └─ feature/* ← Your feature branches

Your Local Repository:
  ├─ main (tracks origin/main) ← Merge tested features here
  ├─ feature/session-1a-security ← Example: Session 1A work
  ├─ feature/session-1.5-* ← Example: Next session
  └─ ... (future feature branches)
```

---

## Why Fork Workflow?

**Checked:** Upstream has NO `dev` branch (uses `main` + feature branches)

**Advantages for This Project:**
1. ✅ **You own your fork** - Full control over Varming73/graphiti
2. ✅ **Clear separation** - Your production features separate from upstream
3. ✅ **Shareable** - Can share as "Graphiti Production Ready" publicly
4. ✅ **Upstream compatible** - Can pull updates and contribute back
5. ✅ **Professional** - Standard open-source contribution workflow

---

## Daily Workflow

### 1. Starting a New Session

```bash
# Ensure you're on main and up-to-date
git checkout main
git pull origin main

# Create feature branch for the session
git checkout -b feature/session-X-description

# Example:
git checkout -b feature/session-1a-security
```

### 2. During Development

```bash
# Make changes, test locally
# Commit frequently with descriptive messages

git add <files>
git commit -m "descriptive message"

# Push to origin to backup work (optional during development)
git push origin feature/session-X-description
```

### 3. After Session Completion & PO Testing

```bash
# Once PO approves, merge to main
git checkout main
git pull origin main  # Ensure main is current

# Merge feature branch (use --no-ff to preserve branch history)
git merge --no-ff feature/session-X-description

# Push to your fork
git push origin main

# Optional: Delete feature branch after merge
git branch -d feature/session-X-description
git push origin --delete feature/session-X-description
```

---

## Syncing with Upstream

**Frequency:** Weekly or before starting new major features

### Check for Upstream Updates

```bash
# Fetch latest from official repo
git fetch upstream

# See what's new
git log main..upstream/main --oneline
```

### Merge Upstream Changes

```bash
# Switch to main
git checkout main

# Merge upstream changes
git merge upstream/main

# Resolve any conflicts if they occur
# Then push to your fork
git push origin main
```

### If Conflicts Occur

```bash
# During merge, Git will mark conflicts
# Edit conflicting files to resolve

# After resolving:
git add <resolved-files>
git commit -m "chore: merge upstream updates, resolve conflicts"
git push origin main
```

---

## Branch Naming Convention

**Format:** `feature/session-X-short-description`

**Examples:**
- `feature/session-1a-security` ✅
- `feature/session-1.5-group-discovery` ✅
- `feature/session-2a-tests` ✅
- `bugfix/session-1a-uuid-validation` ✅ (for bug fixes)
- `docs/update-readme` ✅ (for documentation only)

**Avoid:**
- `dev-hobby` ❌ (not needed with fork workflow)
- `my-changes` ❌ (not descriptive)
- `test` ❌ (too vague)

---

## Commit Message Format

Follow conventional commits for clarity:

```
<type>(<scope>): <short description>

<optional detailed description>

<optional footer>
```

**Types:**
- `feat`: New feature (Session 1A security fixes)
- `fix`: Bug fix
- `docs`: Documentation changes
- `chore`: Maintenance (dependency updates, etc.)
- `test`: Adding/updating tests
- `refactor`: Code restructuring without behavior change

**Examples:**
```bash
git commit -m "feat(security): add group_id validation to prevent RedisSearch injection"

git commit -m "docs(readme): add Security Model section with deployment guidelines"

git commit -m "test(validation): add UUID validation test cases"
```

---

## Protecting Your Work

### Backup Important Branches

```bash
# Push feature branch to origin (your fork)
git push origin feature/session-X-description

# Even if not merged yet, it's backed up on GitHub
```

### Before Risky Operations

```bash
# Create a backup branch before experimenting
git checkout -b backup/before-risky-change

# Do risky operation on original branch
git checkout feature/session-X-description
# ... experiment ...

# If it works, delete backup
git branch -d backup/before-risky-change

# If it fails, restore from backup
git checkout backup/before-risky-change
git branch -D feature/session-X-description  # Delete failed attempt
git checkout -b feature/session-X-description  # Recreate from backup
```

---

## Repository Health Checks

### Monthly Maintenance

```bash
# 1. Sync with upstream
git fetch upstream
git checkout main
git merge upstream/main
git push origin main

# 2. Clean up merged branches
git branch --merged main | grep -v "^\* main" | xargs -n 1 git branch -d

# 3. Check for divergence
git log origin/main..upstream/main --oneline
```

### Before Major Sessions

```bash
# Ensure clean state
git status

# Ensure main is current
git checkout main
git pull origin main

# Fetch upstream updates
git fetch upstream
```

---

## Emergency Recovery

### Undo Last Commit (Not Pushed)

```bash
# Keep changes, undo commit
git reset --soft HEAD~1

# Discard changes, undo commit
git reset --hard HEAD~1
```

### Undo Last Commit (Already Pushed)

```bash
# Create a new commit that reverses the last one
git revert HEAD
git push origin <branch>
```

### Restore Deleted Branch

```bash
# Find the commit SHA of the deleted branch
git reflog

# Recreate branch from that commit
git checkout -b feature/recovered-branch <commit-sha>
```

---

## Communication with Upstream

### If You Want to Contribute Back

```bash
# 1. Create feature branch from upstream/main
git checkout -b feature/contribute-X upstream/main

# 2. Make changes
# ... implement feature ...

# 3. Push to your fork
git push origin feature/contribute-X

# 4. Open Pull Request on GitHub
# From: Varming73/graphiti feature/contribute-X
# To: getzep/graphiti main
```

### Checking Upstream Issues

```bash
# Visit official repo to check for relevant updates
# https://github.com/getzep/graphiti/issues
# https://github.com/getzep/graphiti/pulls
```

---

## Current Status

**Last Sync with Upstream:** 2025-10-26 (Initial fork)
**Active Branch:** feature/session-1a-security
**Main Branch Status:** Contains planning docs
**Next Sync:** After Session 1A testing completes

**Remote Configuration:**
```bash
# Verify with:
git remote -v

# Expected output:
origin    https://github.com/Varming73/graphiti.git (fetch)
origin    https://github.com/Varming73/graphiti.git (push)
upstream  https://github.com/getzep/graphiti (fetch)
upstream  https://github.com/getzep/graphiti (push)
```

---

## Quick Reference

**Start new session:**
```bash
git checkout main && git pull origin main
git checkout -b feature/session-X-description
```

**Commit work:**
```bash
git add <files>
git commit -m "type(scope): description"
```

**Merge after testing:**
```bash
git checkout main
git merge --no-ff feature/session-X-description
git push origin main
```

**Sync with upstream:**
```bash
git fetch upstream
git checkout main
git merge upstream/main
git push origin main
```

---

## Troubleshooting

**Issue:** `git push` rejected (diverged histories)
**Solution:**
```bash
git pull origin <branch> --rebase
git push origin <branch>
```

**Issue:** Merge conflict during upstream sync
**Solution:**
```bash
# Edit conflicting files
git add <resolved-files>
git commit
git push origin main
```

**Issue:** Accidentally committed to main
**Solution:**
```bash
# Create feature branch from current main
git checkout -b feature/accidental-work

# Reset main to origin
git checkout main
git reset --hard origin/main

# Continue work in feature branch
git checkout feature/accidental-work
```

---

## See Also

- [PROJECT_PLAN.md](PROJECT_PLAN.md) - Overall project plan
- [SESSION_LOG.md](SESSION_LOG.md) - Development session tracking
- [ADR.md](ADR.md) - Architecture decisions
- [CHANGELOG.md](../mcp_server/CHANGELOG.md) - Version history
