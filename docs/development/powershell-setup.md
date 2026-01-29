# PowerShell Setup & Developer Aliases

## Overview

PowerShell profile (`$PROFILE`) is configured with useful aliases to accelerate development workflow.

**Profile location:** `C:\Users\<username>\Documents\PowerShell\Microsoft.PowerShell_profile.ps1`

## Git Aliases

Shortcuts for most common git commands:

| Alias | Command | Description |
|-------|---------|-------------|
| `gs` | `git status` | Show repository status |
| `ga` | `git add` | Add files to staging |
| `gaa` | `git add --all` | Add all changes to staging |
| `gc` | `git commit` | Commit changes |
| `gcm` | `git commit -m` | Commit with message |
| `gp` | `git push` | Push to remote |
| `gpl` | `git pull` | Pull from remote |
| `gl` | `git log --oneline --graph --decorate -10` | Pretty log (last 10) |
| `gd` | `git diff` | Show differences |
| `gb` | `git branch` | List branches |
| `gco` | `git checkout` | Checkout branch |
| `gcb` | `git checkout -b` | Create new branch |

### Usage Examples

```powershell
# Typical workflow
gs                          # Check status
ga src/Alexandria.Api/      # Add files
gcm "feat: add new feature" # Commit
gp                          # Push

# Quick overview
gl                          # Log with graph
gd                          # What did I change?

# Branch management
gb                          # List branches
gcb feature/new-api         # Create and checkout new branch
```

## .NET Aliases

Shortcuts for `dotnet` commands:

| Alias | Command | Description |
|-------|---------|-------------|
| `dn` | `dotnet` | Base dotnet CLI |
| `dnb` | `dotnet build` | Build solution |
| `dnr` | `dotnet run` | Run project |
| `dnt` | `dotnet test` | Run tests |
| `dnw` | `dotnet watch run` | Run with auto-reload |

### Usage Examples

```powershell
dnb                         # Build project
dnr --project Alexandria.Api
dnt                         # Run all tests
dnw                         # Development with hot reload
```

## NPM Aliases

Shortcuts for Node.js/NPM:

| Alias | Command | Description |
|-------|---------|-------------|
| `ni` | `npm install` | Install dependencies |
| `ns` | `npm start` | Start application |
| `nt` | `npm test` | Run tests |
| `nb` | `npm run build` | Build project |

### Usage Examples

```powershell
ni                          # Install dependencies
ns                          # Start dev server
nb                          # Production build
```

## Docker Aliases

Shortcuts for Docker:

| Alias | Command | Description |
|-------|---------|-------------|
| `d` | `docker` | Base docker CLI |
| `dc` | `docker-compose` | Docker Compose |
| `dcu` | `docker-compose up` | Start services |
| `dcd` | `docker-compose down` | Stop services |

### Usage Examples

```powershell
dcu -d                      # Start in background
dcd                         # Stop services
d ps                        # List containers
dc logs -f qdrant          # Follow logs
```

## Codex CLI

Wrapper function that automatically sets `CODEX_HOME` to project-specific location:

```powershell
codex some-command
# Automatically sets: CODEX_HOME=$PWD\.codex
```

**Note:** Codex CLI is scheduled for deprecation in favor of Claude.

## Enhanced Prompt

Prompt displays:
- `username@computer` (green)
- Current path (cyan)
- **Git branch** (yellow) - if in a git repository

Example:
```
goran@MYPC:C:\repos\Alexandria (master)
>
```

## Installation

PowerShell profile loads automatically when starting any new terminal.

**Reload profile without terminal restart:**
```powershell
. $PROFILE
```

**Edit profile:**
```powershell
notepad $PROFILE
```

## Troubleshooting

### "Cannot be loaded because running scripts is disabled"

Execution policy must be set:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Profile not loading

Check if profile file exists:
```powershell
Test-Path $PROFILE
```

If it doesn't exist, create it:
```powershell
New-Item -Path $PROFILE -ItemType File -Force
```
