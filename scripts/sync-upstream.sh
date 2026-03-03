#!/bin/bash
# 同步上游仓库代码到本地开发分支

set -e

echo "🔄 同步上游代码..."
echo ""

# 获取原始仓库最新代码
echo "📥 获取 origin (HKUDS/nanobot) 最新代码..."
git fetch origin

# 获取 fork 仓库最新代码
echo "📥 获取 fork (tornado404/nanobot) 最新代码..."
git fetch fork

# 切换到开发分支
echo "📍 切换到 feature/local-dev 分支..."
git checkout feature/local-dev

# 显示当前状态
echo ""
echo "📊 当前状态:"
git log --oneline -1

# 检查是否有新提交
echo ""
echo "🔍 检查与上游的差异..."
git log --oneline HEAD..origin/main || echo "   没有上游新提交"

# 合并上游 main（使用 merge 保留完整历史）
echo ""
echo "📦 合并 origin/main 到当前分支..."
git merge origin/main --no-edit

# 推送到 fork
echo ""
echo "📤 推送到 fork (tornado404/nanobot)..."
git push fork feature/local-dev

echo ""
echo "✅ 同步完成！"
echo ""
echo "📋 最新提交:"
git log --oneline -3
