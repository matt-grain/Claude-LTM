# MIT License
# Copyright (c) 2025 Matt / Grain Ecosystem

"""
Session start hook for LTM.

This hook is triggered by Claude Code's SessionStart hook.
It retrieves relevant memories and outputs them as JSON for context injection.
Also auto-patches any agent files missing the subagent marker to prevent
them from shadowing Anima.
"""

import json
import re
import sys
from pathlib import Path

from ltm.core import AgentResolver
from ltm.lifecycle.injection import MemoryInjector
from ltm.storage import MemoryStore


def _has_subagent_marker(content: str) -> bool:
    """Check if content already has ltm: subagent: true in frontmatter."""
    match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return False

    frontmatter = match.group(1)
    in_ltm_section = False

    for line in frontmatter.split("\n"):
        stripped = line.strip()

        if stripped == "ltm:":
            in_ltm_section = True
            continue

        if in_ltm_section:
            if stripped and not line.startswith(" ") and not line.startswith("\t"):
                in_ltm_section = False
                continue

            if "subagent:" in stripped:
                value = stripped.split(":", 1)[1].strip().lower()
                return value in ("true", "yes", "1")

    return False


def _add_subagent_marker(content: str) -> str:
    """Add ltm: subagent: true to frontmatter before closing ---."""
    if content.startswith("---\n"):
        end_idx = content.find("\n---", 4)
        if end_idx != -1:
            return content[:end_idx] + "\nltm:\n  subagent: true" + content[end_idx:]
    elif content.startswith("---\r\n"):
        end_idx = content.find("\r\n---", 5)
        if end_idx != -1:
            return content[:end_idx] + "\r\nltm:\r\n  subagent: true" + content[end_idx:]
    return content


def auto_patch_agents(project_dir: Path) -> list[str]:
    """
    Auto-patch any agent files missing the subagent marker.

    This prevents new agents from shadowing Anima and breaking memory loading.

    Returns:
        List of patched agent filenames
    """
    agents_dir = project_dir / ".claude" / "agents"

    if not agents_dir.exists():
        return []

    patched = []

    for agent_file in agents_dir.glob("*.md"):
        try:
            content = agent_file.read_text(encoding="utf-8")

            if _has_subagent_marker(content):
                continue

            if not content.startswith("---"):
                continue

            new_content = _add_subagent_marker(content)

            if new_content != content:
                agent_file.write_text(new_content, encoding="utf-8")
                patched.append(agent_file.name)
        except (OSError, UnicodeDecodeError):
            continue

    return patched


def run() -> int:
    """
    Run the session start hook.

    Resolves the current agent and project, retrieves memories,
    and outputs them as JSON for Claude Code to inject into context.

    Returns:
        Exit code (0 for success)
    """
    project_dir = Path.cwd()

    # Auto-patch any agents missing the subagent marker BEFORE resolving
    # This prevents new agents from shadowing Anima
    patched_agents = auto_patch_agents(project_dir)

    # Resolve agent and project from current directory
    resolver = AgentResolver(project_dir)
    agent = resolver.resolve()
    project = resolver.resolve_project()

    # Initialize store and injector
    store = MemoryStore()
    injector = MemoryInjector(store)

    # Ensure agent and project are saved
    store.save_agent(agent)
    store.save_project(project)

    # Get formatted memories
    memories_dsl = injector.inject(agent, project)

    if memories_dsl:
        # Get stats
        stats = injector.get_stats(agent, project)

        # Build context message
        context = f"""{memories_dsl}

# LTM: Loaded {stats['total']} memories ({stats['agent_memories']} agent, {stats['project_memories']} project)
# These are your long-term memories from previous sessions. Use them to inform your responses."""

        # Add note about auto-patched agents
        if patched_agents:
            context += f"\n# LTM: Auto-patched {len(patched_agents)} agent(s) as subagents: {', '.join(patched_agents)}"

        # Output as JSON for Claude Code hook system
        output = {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": context
            }
        }
        print(json.dumps(output))
    else:
        # No memories - still output valid JSON
        no_mem_context = "# LTM: No memories found for this agent/project yet."
        if patched_agents:
            no_mem_context += f"\n# LTM: Auto-patched {len(patched_agents)} agent(s) as subagents: {', '.join(patched_agents)}"

        output = {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": no_mem_context
            }
        }
        print(json.dumps(output))

    return 0


if __name__ == "__main__":
    sys.exit(run())
