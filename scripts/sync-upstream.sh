#!/bin/bash
#
# sync-upstream.sh - Sync local customizations with upstream nanobot releases
#
# Usage:
#   ./scripts/sync-upstream.sh              # Sync to latest tag
#   ./scripts/upstream.sh v0.1.4.post4      # Sync to specific tag
#
# This script:
# 1. Fetches latest upstream tags
# 2. Rebases your local/customizations branch onto the new tag
# 3. Helps you resolve conflicts if they occur
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
CUSTOM_BRANCH="local/customizations"
REMOTE="origin"

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    log_error "Not in a git repository"
    exit 1
fi

# Check if custom branch exists
branch_exists() {
    git show-ref --verify --quiet refs/heads/$CUSTOM_BRANCH
}

# Get latest tag
get_latest_tag() {
    git fetch ${REMOTE} --tags 2>/dev/null
    git tag -l | grep -E '^v[0-9]+\.[0-9]+\.[0-9]+' | sort -V | tail -1
}

# Main script
main() {
    local target_tag="$1"
    
    log_info "Nanobot Upstream Sync Script"
    echo "=================================="
    echo ""
    
    # Step 1: Fetch latest tags
    log_info "Fetching upstream tags from ${REMOTE}..."
    git fetch ${REMOTE} --tags
    
    # Determine target tag
    if [ -z "$target_tag" ]; then
        target_tag=$(get_latest_tag)
        if [ -z "$target_tag" ]; then
            log_error "No upstream tags found"
            exit 1
        fi
        log_info "Latest upstream tag: ${target_tag}"
    else
        log_info "Target tag specified: ${target_tag}"
        # Verify tag exists
        if ! git rev-parse "${target_tag}" >/dev/null 2>&1; then
            log_error "Tag ${target_tag} not found. Available tags:"
            git tag -l | tail -10
            exit 1
        fi
    fi
    
    # Step 2: Check current branch
    current_branch=$(git rev-parse --abbrev-ref HEAD)
    log_info "Current branch: ${current_branch}"
    
    # Check for uncommitted changes
    if ! git diff-index --quiet HEAD --; then
        log_error "You have uncommitted changes. Please commit or stash them first."
        echo ""
        echo "Uncommitted files:"
        git status --short
        echo ""
        echo "Suggestions:"
        echo "  git add -A && git commit -m 'WIP: before sync'"
        echo "  git stash"
        exit 1
    fi
    
    # Step 3: Check if custom branch exists
    if ! branch_exists; then
        log_warning "Custom branch '${CUSTOM_BRANCH}' does not exist"
        echo ""
        echo "This appears to be your first sync. You need to create your custom branch first:"
        echo ""
        echo "  git checkout -b ${CUSTOM_BRANCH}"
        echo "  git add -A"
        echo "  git commit -m 'feat: local customizations'"
        echo ""
        read -p "Create branch now? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            git checkout -b ${CUSTOM_BRANCH}
            git add -A
            git commit -m "feat: local customizations (initial)"
            log_success "Custom branch created"
        else
            exit 0
        fi
    fi
    
    # Step 4: Switch to custom branch
    if [ "$current_branch" != "$CUSTOM_BRANCH" ]; then
        log_info "Switching to ${CUSTOM_BRANCH}..."
        git checkout ${CUSTOM_BRANCH}
    fi
    
    # Step 5: Show what will be rebased
    echo ""
    log_info "Rebase preview:"
    echo "  Base: ${target_tag}"
    echo "  Branch: ${CUSTOM_BRANCH}"
    echo ""
    echo "Commits that will be rebased:"
    git log --oneline ${target_tag}..HEAD | head -10
    echo ""
    
    # Step 6: Perform rebase
    log_info "Starting rebase onto ${target_tag}..."
    echo ""
    
    if git rebase ${target_tag}; then
        log_success "Rebase completed successfully!"
        echo ""
        log_info "Your customizations are now based on ${target_tag}"
        echo ""
        
        # Show what changed
        log_info "Summary of changes:"
        echo "  Files modified in your branch:"
        git diff --name-only ${target_tag} | head -20
        echo ""
        
    else
        log_error "Rebase encountered conflicts"
        echo ""
        echo -e "${YELLOW}Manual resolution required:${NC}"
        echo ""
        echo "1. Resolve conflicts in the files shown by git"
        echo "2. After resolving each file: git add <file>"
        echo "3. Continue rebase: git rebase --continue"
        echo ""
        echo "If you want to abort:"
        echo "  git rebase --abort"
        echo ""
        echo "Current conflicted files:"
        git status --short | grep "^UU"
        echo ""
        
        # Provide conflict resolution tips
        log_info "Conflict resolution tips:"
        echo "  - Your changes are in HEAD (above ======)"
        echo "  - Upstream changes are below ======"
        echo "  - Keep both if they're complementary"
        echo "  - Test after resolving!"
        echo ""
        
        exit 1
    fi
    
    # Step 7: Verify
    log_info "Running verification..."
    
    # Check Python syntax (if Python files were changed)
    python_files=$(git diff --name-only ${target_tag} | grep '\.py$' || true)
    if [ -n "$python_files" ]; then
        log_info "Checking Python syntax..."
        for file in $python_files; do
            if [ -f "$file" ]; then
                python3 -m py_compile "$file" 2>/dev/null || log_warning "Syntax check failed for $file"
            fi
        done
    fi
    
    echo ""
    log_success "Sync completed!"
    echo ""
    echo "Next steps:"
    echo "  1. Test your customizations"
    echo "  2. Optionally update main: git checkout main && git merge ${CUSTOM_BRANCH}"
    echo "  3. Run nanobot to verify everything works"
    echo ""
}

# Run main function
main "$@"
