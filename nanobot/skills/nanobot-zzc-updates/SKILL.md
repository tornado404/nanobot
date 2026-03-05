# Nanobot ZZC Updates Skill

> **Purpose**: Track and maintain custom nanobot version updates for ZZC (tornado404) fork.
> 
> **Branch**: `local/customizations`
> 
> **Upstream**: `origin/main` (HKUDS/nanobot)

---

## 📋 Overview

This skill manages custom modifications to nanobot that diverge from upstream. The goal is to:

1. Keep custom changes isolated in `local/customizations` branch
2. Regularly rebase onto upstream updates
3. Preserve all local modifications during sync

---

## 🎯 Custom Modifications

### Current Local Changes

| File | Modification | Purpose |
|------|-------------|---------|
| `nanobot/agent/context.py` | Token counting with LiteLLM fallback | Context window management |
| `nanobot/agent/loop.py` | `max_context_tokens` parameter | Prevent OOM errors |
| `nanobot/config/schema.py` | Default model `bailian/qwen3.5-plus` | Bailian provider config |
| `nanobot/providers/registry.py` | Bailian provider registration | Enable Bailian API |
| `nanobot/cli/commands.py` | Pass `max_context_tokens` to AgentLoop | Wire up config |

---

## 🔧 Workflow

### Daily Development

```bash
# Always work on local/customizations branch
git checkout local/customizations

# Make your changes
# ... edit files ...
git add -A
git commit -m "feat: your customization"

# Push to your fork
git push fork local/customizations
```

### Sync Upstream (Weekly/Monthly)

**Automated (Recommended)**:
```bash
./scripts/sync-upstream.sh
```

**Manual**:
```bash
git checkout local/customizations
git fetch origin
git rebase origin/main
git push fork local/customizations --force-with-lease
```

---

## 📁 File Structure

```
nanobot/skills/nanobot-zzc-updates/
├── SKILL.md                      # This file
├── sync-upstream.sh              # Automated sync script
└── VERSION_CONTROL_STRATEGY.md   # Detailed strategy doc
```

---

## 🛠️ Commands

### Check Status

```bash
# Current branch
git branch --show-current

# See local changes
git status

# See diff from upstream
git diff origin/main..local/customizations

# Count commits behind upstream
git log --oneline HEAD..origin/main | wc -l
```

### Sync Operations

```bash
# Fetch upstream tags
git fetch origin --tags

# List recent tags
git tag -l | tail -5

# Rebase onto specific tag
git rebase v0.1.4.post4

# Abort bad rebase
git rebase --abort

# Continue after resolving conflicts
git rebase --continue
```

### Push Operations

```bash
# Normal push
git push fork local/customizations

# Force push after rebase (use --force-with-lease for safety)
git push fork local/customizations --force-with-lease
```

---

## ⚠️ Conflict Resolution

### During Rebase

```bash
# 1. Git will pause and show conflicted files
git status

# 2. Open conflicted files, look for markers:
# <<<<<<< HEAD
# Your changes
# =======
# Upstream changes
# >>>>>>>

# 3. Keep BOTH if complementary:
# - Your token counting logic
# - Their upstream improvements

# 4. After resolving each file:
git add <file>
git rebase --continue
```

### Common Conflicts

| File | Likely Conflict | Resolution |
|------|----------------|------------|
| `context.py` | Token counting logic | Keep your counting, merge upstream context building |
| `schema.py` | Config defaults | Keep your defaults, add upstream new fields |
| `providers/registry.py` | Provider list | Add your provider to new list |

---

## 📊 Branch Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Remote Configuration                         │
├─────────────────────────────────────────────────────────────────┤
│  origin  → https://github.com/HKUDS/nanobot.git (upstream)     │
│  fork    → https://github.com/tornado404/nanobot.git (yours)   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                       Branch Strategy                           │
├─────────────────────────────────────────────────────────────────┤
│  origin/main                                                    │
│      │                                                          │
│      │  (weekly rebase)                                         │
│      ▼                                                          │
│  local/customizations  ← Your custom commits                    │
│      │                                                          │
│      │  (push)                                                  │
│      ▼                                                          │
│  fork/local/customizations                                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🧪 Testing After Sync

After each rebase, verify your customizations work:

```bash
# 1. Check token counting
python -c "from nanobot.agent.context import ContextBuilder; print('OK')"

# 2. Verify Bailian provider
python -c "from nanobot.providers.registry import get_provider; p = get_provider('bailian'); print(f'Bailian: {p}')"

# 3. Test config loading
python -c "from nanobot.config import Config; c = Config.load(); print(f'Default model: {c.agents.defaults.model}')"
```

---

## 📝 Version History

### Current State

- **Base Tag**: v0.1.4.post3
- **Custom Commits**: 1 (feat: local customizations)
- **Last Sync**: 2026-03-05

### Planned Updates

| Version | Target Date | Notes |
|---------|-------------|-------|
| v0.1.4.post4 | TBD | Wait for upstream release |
| v0.1.4.post5 | TBD | Wait for upstream release |

---

## 🔗 Related Resources

- [Fork Maintenance Guide](FORK_MAINTENANCE.md)
- [Version Control Strategy](VERSION_CONTROL_STRATEGY.md)
- [Sync Script](scripts/sync-upstream.sh)
- [Upstream Repo](https://github.com/HKUDS/nanobot)
- [Your Fork](https://github.com/tornado404/nanobot)

---

## 🚨 Emergency Procedures

### If Rebase Goes Wrong

```bash
# 1. Abort current rebase
git rebase --abort

# 2. Check backup branch (created by sync script)
git branch | grep backup

# 3. Restore from backup
git checkout local/customizations-backup-YYYYMMDD-HHMMSS

# 4. Try manual merge instead
git checkout local/customizations
git merge origin/main
```

### If You Accidentally Commit to main

```bash
# 1. Switch to correct branch
git checkout local/customizations

# 2. Cherry-pick the commit
git cherry-pick <commit-hash>

# 3. Remove from main
git checkout main
git reset --hard origin/main
```

---

*Last updated: 2026-03-05*  
*Maintainer: tornado404*  
*Skill version: 1.0.0*
