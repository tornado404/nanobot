# Nanobot Version Control Strategy

## Current State Analysis

### Your Local Modifications
You have **5 modified files** with local changes:

1. **nanobot/agent/context.py** - Added token counting with LiteLLM fallback
2. **nanobot/agent/loop.py** - Added `max_context_tokens` parameter, improved error formatting
3. **nanobot/config/schema.py** - Changed default model to `bailian/qwen3.5-plus`, added `max_context_tokens` config
4. **nanobot/providers/registry.py** - Added Bailian provider configuration
5. **nanobot/cli/commands.py** - Passed `max_context_tokens` to AgentLoop

### Upstream Status
- **Current upstream tag**: v0.1.4.post3 (you have this tag locally)
- **Your branch**: 148 commits behind origin/main
- **Upstream changes since your last sync**: 49 files changed, 3491 insertions, 897 deletions

---

## Recommended Strategy: Feature Branch + Periodic Rebase

### Why This Approach?

| Approach | Pros | Cons | Verdict |
|----------|------|------|---------|
| **Direct merge** | Simple | Loses your changes on conflicts | ❌ |
| **Separate fork** | Clean separation | Hard to track upstream tags | ❌ |
| **Feature branch + rebase** | Keeps your changes, clean history, easy to update | Requires discipline | ✅ |

---

## Workflow Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    MAIN BRANCH (upstream)                       │
│  v0.1.4.post3 ──→ v0.1.4.post4 ──→ v0.1.4.post5 ──→ ...       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ pull/rebase
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                 YOUR FEATURE BRANCH (local-changes)             │
│  your-changes: context.py, loop.py, schema.py, etc.            │
└─────────────────────────────────────────────────────────────────┘
```

---

## Step-by-Step Implementation

### Phase 1: Create Your Feature Branch (One-Time Setup)

```bash
# 1. Ensure you're on main and up to date with upstream tag
git checkout main
git fetch origin --tags

# 2. Create a branch from your current state (with local changes)
git checkout -b local/customizations

# 3. Commit your current changes
git add -A
git commit -m "feat: custom local changes (token limits, bailian provider)"
```

### Phase 2: Update from Upstream (Repeatable Workflow)

**When a new version is released (e.g., v0.1.4.post4):**

```bash
# 1. Switch to main and update to new tag
git checkout main
git fetch origin --tags
git checkout v0.1.4.post4  # or latest tag

# 2. Switch back to your branch
git checkout local/customizations

# 3. Rebase onto the new tag
git rebase v0.1.4.post4

# 4. Resolve any conflicts (if they occur)
#    - Git will pause and show conflicting files
#    - Edit files to resolve conflicts
#    - Run: git add <resolved-file>
#    - Run: git rebase --continue

# 5. Verify everything works
#    - Run tests, check your customizations

# 6. Update main (optional - keeps main in sync)
git checkout main
git merge local/customizations
```

### Phase 3: Automated Sync Script

Create a script to automate the update process (see `scripts/sync-upstream.sh`).

---

## Conflict Resolution Strategy

### Your Changes Are Likely Safe Because:

1. **context.py**: Token counting is additive - unlikely to conflict
2. **loop.py**: `max_context_tokens` parameter is new functionality
3. **schema.py**: Config additions are additive
4. **providers/registry.py**: Provider additions are isolated
5. **commands.py**: Wiring changes follow upstream patterns

### If Conflicts Occur:

```bash
# During rebase, if conflicts happen:
# 1. See what conflicted
git status

# 2. Open conflicted files, look for:
# <<<<<<< HEAD
# Your changes
# =======
# Upstream changes
# >>>>>>>

# 3. Keep BOTH if they're complementary:
# - Your token counting logic
# - Their upstream improvements

# 4. After resolving each file:
git add <file>
git rebase --continue
```

---

## Long-Term Maintenance

### Monthly Check Routine

```bash
# 1. Check for new upstream tags
git fetch origin --tags
git tag -l | tail -5

# 2. See how many commits you're behind
git log --oneline HEAD..origin/main | wc -l

# 3. If significantly behind, update:
./scripts/sync-upstream.sh  # Use the automation script
```

### If You Want to Contribute Back

Your changes (token limits, Bailian provider) could be valuable upstream:

1. Keep your branch clean and well-documented
2. Consider opening PRs to upstream for generic improvements
3. Keep provider-specific config in your branch

---

## Alternative: Two-Remote Strategy

If you want even cleaner separation:

```bash
# Add your own fork as a remote (if you have one)
git remote add myfork https://github.com/YOUR_USERNAME/nanobot.git

# Push your customizations
git push myfork local/customizations

# Now you have:
# - origin: upstream (read-only)
# - myfork: your customizations
```

---

## Quick Reference Commands

| Task | Command |
|------|---------|
| Check current branch | `git branch --show-current` |
| See local changes | `git status` |
| See diff from upstream | `git diff HEAD origin/main` |
| Fetch new tags | `git fetch origin --tags` |
| Start rebase | `git rebase <tag>` |
| Abort bad rebase | `git rebase --abort` |
| Continue after conflict | `git rebase --continue` |

---

## Next Steps

1. **Commit your current changes** to a dedicated branch
2. **Create the sync script** (automates future updates)
3. **Test the workflow** with a dry-run rebase
4. **Document your customizations** for future reference
