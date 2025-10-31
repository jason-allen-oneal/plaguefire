# Branch Cleanup Required

## Summary

The repository has an extra branch that should be deleted:

**Branch to delete:** `copilot/update-ci-workflow-pyinstaller`

## Branch Analysis

### Current Branches
```
✓ main                                   - Primary branch
✓ copilot/remove-extra-branch            - Current PR branch
✗ copilot/update-ci-workflow-pyinstaller - Extra branch (to be deleted)
```

### Branch Details
- **Full name:** `copilot/update-ci-workflow-pyinstaller`
- **Last commit:** `0f11ac7c952dc1f5a48284c9d056b25f07986e76`
- **Commit message:** "Initial plan"
- **Status:** Diverged from main (20 commits ahead, 1 commit behind)
- **Type:** Stale feature branch from previous PR work

### Commits on Extra Branch
The branch contains commits from old PR work including:
- PyInstaller build workflow updates
- Balen world theme integration
- Entity coloring fixes
- Various bug fixes and item updates

These commits appear to have been integrated into main through other PRs or are no longer needed.

## Deletion Instructions

### Option 1: GitHub Web Interface (Recommended)
1. Navigate to: https://github.com/jason-allen-oneal/plaguefire/branches
2. Locate `copilot/update-ci-workflow-pyinstaller` in the branch list
3. Click the trash/delete icon next to the branch name
4. Confirm deletion

### Option 2: Command Line
```bash
# Delete the remote branch
git push origin --delete copilot/update-ci-workflow-pyinstaller

# Remove local tracking reference (if it exists locally)
git branch -d copilot/update-ci-workflow-pyinstaller
```

### Option 3: GitHub CLI
```bash
gh api repos/jason-allen-oneal/plaguefire/git/refs/heads/copilot/update-ci-workflow-pyinstaller -X DELETE
```

## Post-Deletion Verification

After deletion, verify the branch is removed:

```bash
# List all remote branches
git ls-remote --heads origin

# Expected output should only show:
# <commit-hash>  refs/heads/main
# <commit-hash>  refs/heads/copilot/remove-extra-branch (this PR)
```

## Why This Branch Should Be Deleted

1. **Stale**: Last updated before the current main branch
2. **Diverged**: Contains commits that don't align with current main
3. **Unnecessary**: Work appears to have been integrated through other PRs
4. **Clutters repository**: Causes confusion about active development branches

## Note

This file can be deleted after the branch cleanup is complete.
