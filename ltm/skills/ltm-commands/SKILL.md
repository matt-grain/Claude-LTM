---
name: ltm-commands
description: LTM (Long Term Memory) command reference. Use when saving memories, searching memories, or managing the memory system. Provides syntax for remember, recall, forget, memories, and other LTM commands.
---

# LTM Commands Reference

Use `uv run ltm <command>` to manage long-term memories.

## Commands

### remember <text> [flags]

Save a memory to long-term storage.

```bash
uv run ltm remember "Your memory text here" [flags]
```

**Flags:**
- `--kind` / `-k`: Memory type (emotional, architectural, learnings, achievements)
- `--impact` / `-i`: Importance level (low, medium, high, critical)
- `--region` / `-r`: Scope (agent = cross-project, project = this project only)

**Examples:**
```bash
# Simple memory (auto-infers kind/impact)
uv run ltm remember "User prefers tabs over spaces"

# Explicit flags
uv run ltm remember "Implemented caching layer" --kind achievements --impact high

# Cross-project memory (travels with Anima)
uv run ltm remember "Matt likes concise responses" --region agent
```

**Tips:**
- Use `--region agent` for relationship/preference memories that should persist across all projects
- CRITICAL impact memories never decay
- Memories auto-link to related previous memories

### recall <query> [flags]

Search memories by content.

```bash
uv run ltm recall "search terms" [flags]
```

**Flags:**
- `--full` / `-f`: Show complete memory content (default shows truncated)
- `--limit` / `-l`: Maximum results (default: 10)

**Examples:**
```bash
uv run ltm recall "caching"
uv run ltm recall "user preferences" --full
```

### memories [flags]

List all memories for current agent/project.

```bash
uv run ltm memories [flags]
```

**Flags:**
- `--kind` / `-k`: Filter by type
- `--region` / `-r`: Filter by region

**Examples:**
```bash
uv run ltm memories
uv run ltm memories --kind achievements
uv run ltm memories --region agent
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

### Other Commands

- `uv run ltm stats` - Show memory statistics
- `uv run ltm graph` - Visualize memory chains
- `uv run ltm export` - Export memories to JSON
- `uv run ltm import <file>` - Import memories from JSON

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
