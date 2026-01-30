# Git Workflow Guide

> Practical guide for working with Auto-Claude and GitHub Pull Requests

## 📋 Standard Workflow

### 1️⃣ After Auto-Claude Completes a Task

```bash
# Check what was done
git status
git log -5 --oneline

# Auto-Claude automatically:
# - Created a branch (e.g., auto-claude/015-add-feature)
# - Committed changes
# - Pushed to GitHub
# - (optionally) Created a Pull Request
```

### 2️⃣ Review Pull Request on GitHub

1. Go to **GitHub → Pull Requests**
2. Click on the new PR
3. Review changes in the **"Files changed"** tab
4. Check:
   - ✅ Are the changes logical?
   - ✅ Do commit messages make sense?
   - ✅ Are tests passing?

### 3️⃣ Merge Pull Request

On GitHub:
- Click **"Merge pull request"**
- Confirm merge
- (optional) Delete branch on GitHub

### 4️⃣ ⭐ CRITICAL: Pull Changes Locally

```bash
# Switch to master
git checkout master

# Pull merged changes
git pull origin master

# Verify everything is synchronized
git status
# Should see: "Your branch is up to date with 'origin/master'"
```

### 5️⃣ Clean Up Local Branches (optional)

```bash
# Delete local branch (safe since it's merged)
git branch -d auto-claude/015-add-feature

# If worktree exists, remove it
git worktree list
git worktree remove --force .auto-claude/worktrees/tasks/015-add-feature
```

---

## 🔧 Fixing Issues in a PR

If you need to fix something **BEFORE** merging:

```bash
# Switch to the PR branch
git checkout auto-claude/015-add-feature

# Make fixes
# ... edit files ...

# Commit
git add .
git commit -m "fix: correct XYZ issue"

# Push (PR will update automatically!)
git push origin auto-claude/015-add-feature
```

---

## ⚠️ Common Mistakes and How to Avoid Them

### ❌ Mistake #1: Forgetting to Pull After GitHub Merge

**Symptom:**
- Local master is behind remote master
- Git says: "Your branch is behind 'origin/master' by X commits"

**Solution:**
```bash
git checkout master
git pull origin master
```

### ❌ Mistake #2: Merging Locally What's Already Merged on GitHub

**Symptom:**
- Creates duplicate merge commits
- Git history becomes messy

**Solution:**
- **Don't merge locally** if you already merged on GitHub
- Instead, pull from remote

### ❌ Mistake #3: Working on Master While Local Master is Outdated

**Symptom:**
- Conflicts when pushing
- "Your branch and 'origin/master' have diverged"

**Prevention:**
```bash
# ALWAYS before starting work:
git checkout master
git pull origin master
git status  # verify everything is ok
```

---

## 📊 Useful Git Commands for Daily Work

### Checking Status

```bash
# Where am I and what do I have?
git status

# Am I synchronized with remote?
git fetch
git status

# What are the latest commits?
git log --oneline -10

# Graphical branch view
git log --oneline --graph --all --decorate -20
```

### Working with Branches

```bash
# List all branches
git branch -a

# List branches NOT merged into master
git branch --no-merged

# List branches that ARE merged
git branch --merged

# Delete merged branch
git branch -d branch-name

# Force delete branch (if not merged)
git branch -D branch-name
```

### Worktree Management

```bash
# List all worktrees
git worktree list

# Remove worktree
git worktree remove .auto-claude/worktrees/tasks/task-name

# Force remove (if has uncommitted changes)
git worktree remove --force .auto-claude/worktrees/tasks/task-name
```

---

## 🎯 Quick Reference Checklist

Print this and keep it handy:

- [ ] Auto-Claude finished task
- [ ] PR reviewed on GitHub
- [ ] PR merged on GitHub
- [ ] `git checkout master`
- [ ] `git pull origin master`
- [ ] `git status` → "up to date"
- [ ] (optional) Clean up local branch
- [ ] (optional) Clean up worktree

**Rule #1:** Pull after EVERY GitHub merge!

---

## 📚 Additional Resources

- [GitHub Flow Guide](https://docs.github.com/en/get-started/quickstart/github-flow)
- [Git Branching Model](https://nvie.com/posts/a-successful-git-branching-model/)
- [Conventional Commits](https://www.conventionalcommits.org/)

---

_Last updated: 2026-01-29_
