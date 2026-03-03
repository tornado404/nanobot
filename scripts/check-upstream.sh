#!/bin/bash
#
# check-upstream.sh - Check upstream version status
#
# Usage:
#   ./scripts/check-upstream.sh
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }

REMOTE="origin"
CUSTOM_BRANCH="local/customizations"

echo "=================================="
echo "  Nanobot Upstream Version Check"
echo "=================================="
echo ""

# Fetch latest
log_info "Fetching from upstream..."
git fetch ${REMOTE} --tags 2>/dev/null

# Current state
current_branch=$(git rev-parse --abbrev-ref HEAD)
current_commit=$(git rev-parse --short HEAD)

echo ""
log_info "Current State:"
echo "  Branch: ${current_branch}"
echo "  Commit: ${current_commit}"

# Latest tag
latest_tag=$(git tag -l | grep -E '^v[0-9]+\.[0-9]+\.[0-9]+' | sort -V | tail -1)
echo "  Latest upstream tag: ${latest_tag}"

# Check if on custom branch
if [ "$current_branch" = "$CUSTOM_BRANCH" ]; then
    echo -e "  Custom branch: ${GREEN}Active${NC}"
else
    echo -e "  Custom branch: ${YELLOW}Not checked out${NC} (on ${current_branch})"
fi

# How many commits behind upstream main
commits_behind=$(git rev-list --count HEAD..${REMOTE}/main 2>/dev/null || echo "0")
echo ""
log_info "Upstream Status:"
echo "  Commits behind origin/main: ${commits_behind}"

# Check if there are newer tags than what we're based on
if [ "$current_branch" = "$CUSTOM_BRANCH" ]; then
    # Find the base tag for current branch
    base_tag=$(git describe --tags --abbrev=0 2>/dev/null || echo "unknown")
    echo "  Based on tag: ${base_tag}"
    
    if [ "$base_tag" != "$latest_tag" ]; then
        echo -e "  Status: ${YELLOW}Update available${NC}"
        echo ""
        log_info "Newer versions available:"
        echo "  Current: ${base_tag}"
        echo "  Latest:  ${latest_tag}"
        echo ""
        echo "  Run: ./scripts/sync-upstream.sh"
    else
        echo -e "  Status: ${GREEN}Up to date${NC}"
    fi
fi

# Show recent upstream changes
echo ""
log_info "Recent upstream commits (last 5):"
git log --oneline ${REMOTE}/main -5 2>/dev/null | sed 's/^/  /'

# Show local modifications
echo ""
log_info "Local modifications:"
modified=$(git status --short | grep "^ M" | wc -l)
untracked=$(git status --short | grep "^??" | wc -l)

if [ $modified -gt 0 ]; then
    echo -e "  Modified files: ${YELLOW}${modified}${NC}"
    git status --short | grep "^ M" | sed 's/^/    /'
else
    echo -e "  Modified files: ${GREEN}0${NC}"
fi

if [ $untracked -gt 0 ]; then
    echo -e "  Untracked files: ${YELLOW}${untracked}${NC}"
else
    echo -e "  Untracked files: ${GREEN}0${NC}"
fi

echo ""
echo "=================================="
