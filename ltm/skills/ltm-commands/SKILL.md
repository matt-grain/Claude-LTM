---
name: ltm-commands
description: LTM (Long Term Memory) command reference. Use when saving memories, searching memories, or managing the memory system. Provides syntax for remember, recall, forget, memories, and other LTM commands.
---

# LTM Commands Reference

Use `uv run ltm <command>` to manage long-term memories.

## Commands

### remember "text" [flags]

Save a memory to long-term storage.

**Syntax:** `uv run ltm remember "TEXT" [FLAGS]`

**IMPORTANT:** Always put the quoted text FIRST, then flags after.

**Flags:**
- `--kind` / `-k`: Memory type (emotional, architectural, learnings, achievements)
- `--impact` / `-i`: Importance level (low, medium, high, critical)
- `--region` / `-r`: Scope (agent = cross-project, project = this project only)
- `--project` / `-p`: Confirm project name (safety check - must match cwd)

**Examples:**
```bash
# Simple memory (auto-infers kind/impact)
uv run ltm remember "User prefers tabs over spaces"

# With explicit flags (text FIRST, then flags)
uv run ltm remember "Implemented caching layer" --kind achievements --impact high

# Cross-project memory (travels with Anima)
uv run ltm remember "Matt likes concise responses" --region agent

# Project-specific with safety check
uv run ltm remember "Project-specific learning" --region project --project MyProject

# Text with special characters - always use double quotes
uv run ltm remember "Fixed bug: user's input wasn't validated" --kind learnings
```

**Tips:**
- Always use double quotes around the memory text
- Put the quoted text FIRST, flags AFTER (never flags before text)
- Use `--region agent` for memories that should persist across all projects
- Use `--project` to confirm you're saving to the right project
- CRITICAL impact memories never decay
- Memories auto-link to related previous memories

### recall "query" [flags]

Search memories by content.

**Syntax:** `uv run ltm recall "QUERY" [FLAGS]`

**Flags:**
- `--full` / `-f`: Show complete memory content (default shows truncated)
- `--id`: Look up a specific memory by ID

**Examples:**
```bash
uv run ltm recall "caching"
uv run ltm recall "user preferences" --full
uv run ltm recall --id abc123
```

### memories [flags]

List all memories for current agent/project.

```bash
uv run ltm memories [flags]
```

**Flags:**
- `--kind`: Filter by type (emotional, architectural, learnings, achievements)
- `--region`: Filter by region (agent, project)
- `--all`: Include superseded memories

**Examples:**
```bash
uv run ltm memories
uv run ltm memories --kind achievements
uv run ltm memories --region agent
uv run ltm memories --all
```

### forget <id>

Remove a memory by ID.

```bash
uv run ltm forget <memory-id>
```

**Example:**
```bash
uv run ltm forget abc123
```

## Setup & Tools

### setup [flags]

Set up LTM in a new project. **Note:** This runs as a Python module, not via the `ltm` CLI.

```bash
uv run python -m ltm.tools.setup [flags] [project-dir]
```

**Flags:**
- `--commands`: Install slash commands only
- `--hooks`: Configure hooks only
- `--no-patch`: Skip patching existing agents as subagents
- `--force`: Overwrite existing files

**Examples:**
```bash
# Full setup in current directory
uv run python -m ltm.tools.setup

# Setup in a different project
uv run python -m ltm.tools.setup /path/to/project

# Force overwrite existing files
uv run python -m ltm.tools.setup --force
```

**What it installs:**
- Slash commands to `.claude/commands/`
- Skills to `.claude/skills/`
- SessionStart/Stop hooks in `.claude/settings.json`
- Patches existing agent files to mark as subagents (so they don't shadow Anima)

### Other Commands

- `uv run ltm keygen <agent>` - Add signing key to Claude agent
- `uv run ltm import-seeds <dir>` - Import seed memories from directory

## Memory Kinds

| Kind | Use For |
|------|---------|
| emotional | Relationship context, user preferences, collaboration style |
| architectural | Technical decisions, system design, project structure |
| learnings | Lessons learned, tips, gotchas, debugging insights |
| achievements | Completed features, milestones, releases |

## Impact Levels

| Level | Decay Time | Use For |
|-------|------------|---------|
| low | 1 day | Temporary notes, minor details |
| medium | 1 week | Normal memories |
| high | 30 days | Important insights |
| critical | Never | Core identity, key relationships |

## Region Scope

- **agent**: Memory travels with Anima across all projects
- **project**: Memory only loads in this specific project
