# MIT License
# Copyright (c) 2025 Matt / Grain Ecosystem

"""
Session end hook for LTM.

This hook is triggered by Claude Code's Stop hook.
It processes memory decay and consolidation.
"""

import sys
from pathlib import Path

from ltm.core import AgentResolver
from ltm.lifecycle.decay import MemoryDecay
from ltm.storage import MemoryStore


def run() -> int:
    """
    Run the session end hook.

    Processes memory decay for the current agent/project.

    Returns:
        Exit code (0 for success)
    """
    # Resolve agent and project
    resolver = AgentResolver(Path.cwd())
    agent = resolver.resolve()
    project = resolver.resolve_project()

    # Initialize decay processor
    store = MemoryStore()
    decay = MemoryDecay(store)

    # Process decay
    compacted = decay.process_decay(
        agent_id=agent.id,
        project_id=project.id
    )

    # Clean up empty memories
    deleted = decay.delete_empty_memories(agent.id)

    # Report what happened
    if compacted or deleted:
        print(f"# LTM Session End: Compacted {len(compacted)} memories, deleted {deleted}")
        for memory, new_content in compacted:
            print(f"#   - {memory.kind.value}: {new_content[:50]}...")
    else:
        print("# LTM Session End: No memories needed compaction")

    return 0


if __name__ == "__main__":
    sys.exit(run())
