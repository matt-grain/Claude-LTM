# MIT License
# Copyright (c) 2025 Matt / Grain Ecosystem

"""
Session start hook for LTM.

This hook is triggered by Claude Code's SessionStart hook.
It retrieves relevant memories and outputs them as JSON for context injection.
"""

import json
import sys
from pathlib import Path

from ltm.core import AgentResolver
from ltm.lifecycle.injection import MemoryInjector
from ltm.storage import MemoryStore


def run() -> int:
    """
    Run the session start hook.

    Resolves the current agent and project, retrieves memories,
    and outputs them as JSON for Claude Code to inject into context.

    Returns:
        Exit code (0 for success)
    """
    # Resolve agent and project from current directory
    resolver = AgentResolver(Path.cwd())
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
        output = {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": "# LTM: No memories found for this agent/project yet."
            }
        }
        print(json.dumps(output))

    return 0


if __name__ == "__main__":
    sys.exit(run())
