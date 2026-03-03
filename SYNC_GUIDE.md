# 分支同步指南

## 当前分支结构

```
origin (HKUDS/nanobot)     ← 原始仓库
    ↑
    | (定期 fetch)
    |
fork (tornado404/nanobot)  ← 你的 fork
    ↑
    | (已追踪)
    |
feature/local-dev          ← 你的开发分支（当前）
```

## 日常开发流程

### 1. 开始新功能
```bash
# 确保在开发分支
git checkout feature/local-dev

# 创建功能分支（可选）
git checkout -b feature/your-new-feature
```

### 2. 开发迭代
```bash
# 正常提交
git add .
git commit -m "feat: your feature description"

# 推送到你的 fork
git push fork feature/your-new-feature
```

### 3. 定期同步上游代码

```bash
# 步骤 1: 获取原始仓库最新代码
git fetch origin

# 步骤 2: 切换到开发分支
git checkout feature/local-dev

# 步骤 3: 合并上游 main 分支（保留你的修改）
git merge origin/main

# 或者使用 rebase（更干净的提交历史）
git rebase origin/main

# 步骤 4: 解决冲突（如果有）
# 编辑冲突文件 → git add <file> → git rebase --continue

# 步骤 5: 推送到你的 fork
git push fork feature/local-dev
```

### 4. 完整同步脚本

创建 `scripts/sync-upstream.sh`：
```bash
#!/bin/bash
# 同步上游仓库代码

set -e

echo "🔄 同步上游代码..."

# 获取原始仓库最新代码
git fetch origin

# 获取 fork 仓库最新代码
git fetch fork

# 切换到开发分支
git checkout feature/local-dev

# 合并上游 main（使用 merge 保留完整历史）
echo "📦 合并 origin/main..."
git merge origin/main

# 推送到 fork
echo "📤 推送到 fork..."
git push fork feature/local-dev

echo "✅ 同步完成！"
```

使用：
```bash
chmod +x scripts/sync-upstream.sh
./scripts/sync-upstream.sh
```

## 常用命令速查

| 操作 | 命令 |
|------|------|
| 查看远程仓库 | `git remote -v` |
| 获取上游更新 | `git fetch origin` |
| 查看分支差异 | `git diff origin/main..feature/local-dev` |
| 查看提交历史 | `git log --oneline --graph --all` |
| 切换分支 | `git checkout <branch>` |
| 创建新分支 | `git checkout -b <branch>` |

## 注意事项

1. **同步频率**: 建议每周至少同步一次，避免冲突积累
2. **冲突解决**: 合并前先提交当前工作，便于回滚
3. **测试**: 同步后运行项目测试确保兼容性
4. **备份**: 重大同步前可创建临时备份分支

## 当前状态

- **当前分支**: `feature/local-dev`
- **基于**: `fork/main` (commit: a78e680)
- **上游追踪**: `fork/feature/local-dev`
- **原始仓库**: `origin/main` (HKUDS/nanobot)
