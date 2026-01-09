# MIT License
# Copyright (c) 2025 Matt / Grain Ecosystem

"""
LTM setup tool.

Sets up LTM in a project by copying commands and optionally configuring hooks.
Works for users who installed via wheel and don't have access to the source tree.
"""

import json
import re
import shutil
import sys
from importlib import resources
from pathlib import Path


def get_package_commands_dir() -> Path:
    """Get the commands directory from the installed package."""
    # Try to find commands in the package
    try:
        # For Python 3.9+
        ltm_files = resources.files("ltm")
        commands_dir = Path(str(ltm_files)).parent / "commands"
        if commands_dir.exists():
            return commands_dir
    except (TypeError, AttributeError):
        pass

    # Fallback: look relative to this file (for editable installs)
    package_root = Path(__file__).parent.parent.parent
    commands_dir = package_root / "commands"
    if commands_dir.exists():
        return commands_dir

    raise FileNotFoundError("Could not find commands directory in package")


def get_package_seeds_dir() -> Path:
    """Get the seeds directory from the installed package."""
    try:
        ltm_files = resources.files("ltm")
        seeds_dir = Path(str(ltm_files)).parent / "seeds"
        if seeds_dir.exists():
            return seeds_dir
    except (TypeError, AttributeError):
        pass

    # Fallback: look relative to this file
    package_root = Path(__file__).parent.parent.parent
    seeds_dir = package_root / "seeds"
    if seeds_dir.exists():
        return seeds_dir

    raise FileNotFoundError("Could not find seeds directory in package")


def setup_commands(project_dir: Path, force: bool = False) -> tuple[int, int]:
    """Copy command files to project's .claude/commands directory."""
    try:
        src_dir = get_package_commands_dir()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return (0, 0)

    dest_dir = project_dir / ".claude" / "commands"

    # Create directory if needed
    dest_dir.mkdir(parents=True, exist_ok=True)

    copied = 0
    skipped = 0

    for src_file in src_dir.glob("*.md"):
        dest_file = dest_dir / src_file.name

        if dest_file.exists() and not force:
            print(f"  ⏭️  {src_file.name} (exists, use --force to overwrite)")
            skipped += 1
            continue

        shutil.copy2(src_file, dest_file)
        print(f"  ✅ {src_file.name}")
        copied += 1

    return (copied, skipped)


def patch_subagents(project_dir: Path) -> tuple[int, int]:
    """
    Patch agent definition files to add subagent: true marker.

    If a project has .claude/agents/*.md files without ltm: subagent: true,
    they will shadow the global Anima agent. This function adds the marker
    so these agents are treated as subagents (invoked via Task tool) rather
    than the main session identity.

    Returns:
        Tuple of (patched_count, skipped_count)
    """
    agents_dir = project_dir / ".claude" / "agents"

    if not agents_dir.exists():
        return (0, 0)

    patched = 0
    skipped = 0

    for agent_file in sorted(agents_dir.glob("*.md")):
        content = agent_file.read_text(encoding="utf-8")

        # Check if it already has ltm: subagent: true
        if _has_subagent_marker(content):
            skipped += 1
            continue

        # Check if it has frontmatter at all
        if not content.startswith("---"):
            print(f"  ⏭️  {agent_file.name} (no frontmatter, skipping)")
            skipped += 1
            continue

        # Add ltm: subagent: true after the opening ---
        new_content = _add_subagent_marker(content)

        if new_content != content:
            agent_file.write_text(new_content, encoding="utf-8")
            print(f"  ✅ {agent_file.name} (marked as subagent)")
            patched += 1
        else:
            skipped += 1

    return (patched, skipped)


def _has_subagent_marker(content: str) -> bool:
    """Check if content already has ltm: subagent: true in frontmatter."""
    # Find frontmatter block
    match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return False

    frontmatter = match.group(1)

    # Check for ltm section with subagent: true
    in_ltm_section = False
    for line in frontmatter.split("\n"):
        stripped = line.strip()

        if stripped == "ltm:":
            in_ltm_section = True
            continue

        if in_ltm_section:
            # Check if we've left the ltm section (no indent)
            if stripped and not line.startswith(" ") and not line.startswith("\t"):
                in_ltm_section = False
                continue

            if "subagent:" in stripped:
                value = stripped.split(":", 1)[1].strip().lower()
                return value in ("true", "yes", "1")

    return False


def _add_subagent_marker(content: str) -> str:
    """Add ltm: subagent: true to frontmatter before closing ---.

    Inserts at the END of frontmatter to preserve `name:` as the first field,
    which Claude Code requires for agent recognition.
    """
    # Find the closing --- of frontmatter
    if content.startswith("---\n"):
        # Find the second --- (closing)
        end_idx = content.find("\n---", 4)
        if end_idx != -1:
            # Insert before the closing ---
            return content[:end_idx] + "\nltm:\n  subagent: true" + content[end_idx:]
    elif content.startswith("---\r\n"):
        end_idx = content.find("\r\n---", 5)
        if end_idx != -1:
            return content[:end_idx] + "\r\nltm:\r\n  subagent: true" + content[end_idx:]
    return content


def setup_hooks(project_dir: Path, force: bool = False) -> bool:
    """Add LTM hooks to project's .claude/settings.json."""
    settings_file = project_dir / ".claude" / "settings.json"

    ltm_hooks = {
        "SessionStart": [
            {
                "matcher": "startup",
                "hooks": [
                    {
                        "type": "command",
                        "command": "uv run python -m ltm.hooks.session_start"
                    }
                ]
            },
            {
                "matcher": "compact",
                "hooks": [
                    {
                        "type": "command",
                        "command": "uv run python -m ltm.hooks.session_start"
                    }
                ]
            }
        ],
        "Stop": [
            {
                "hooks": [
                    {
                        "type": "command",
                        "command": "uv run python -m ltm.hooks.session_end"
                    },
                    {
                        "type": "command",
                        "command": "uv run python -m ltm.tools.detect_achievements --since 24"
                    }
                ]
            }
        ]
    }

    # Load existing settings or create new
    if settings_file.exists():
        try:
            settings = json.loads(settings_file.read_text())
        except json.JSONDecodeError:
            print(f"  ⚠️  Invalid JSON in {settings_file}, creating backup")
            shutil.copy2(settings_file, settings_file.with_suffix(".json.bak"))
            settings = {}
    else:
        settings_file.parent.mkdir(parents=True, exist_ok=True)
        settings = {}

    # Check if hooks already exist
    if "hooks" in settings and not force:
        existing_hooks = settings.get("hooks", {})
        if "SessionStart" in existing_hooks or "Stop" in existing_hooks:
            print("  ⚠️  Hooks already configured (use --force to overwrite)")
            return False

    # Merge hooks
    if "hooks" not in settings:
        settings["hooks"] = {}

    settings["hooks"].update(ltm_hooks)

    # Write back
    settings_file.write_text(json.dumps(settings, indent=2) + "\n")
    print(f"  ✅ Hooks configured in {settings_file}")
    return True


def run(args: list[str]) -> int:
    """
    Run the setup tool.

    Usage:
        ltm setup [options] [project-dir]

    Options:
        --commands      Install slash commands only
        --hooks         Configure hooks only
        --no-patch      Skip patching existing agents as subagents
        --force         Overwrite existing files
        --help          Show this help

    If no options specified, installs commands, hooks, and patches subagents.
    """
    # Parse arguments
    force = "--force" in args
    commands_only = "--commands" in args
    hooks_only = "--hooks" in args
    no_patch = "--no-patch" in args
    show_help = "--help" in args or "-h" in args

    # Filter out flags to get project dir
    project_args = [a for a in args if not a.startswith("-")]
    project_dir = Path(project_args[0]) if project_args else Path.cwd()

    if show_help:
        print("""
LTM Setup Tool

Usage:
    uv run python -m ltm.tools.setup [options] [project-dir]

Options:
    --commands      Install slash commands only
    --hooks         Configure hooks only
    --no-patch      Skip patching existing agents as subagents
    --force         Overwrite existing files
    --help          Show this help

Examples:
    # Set up everything in current directory
    uv run python -m ltm.tools.setup

    # Install commands only
    uv run python -m ltm.tools.setup --commands

    # Set up in a specific project
    uv run python -m ltm.tools.setup /path/to/project

    # Force overwrite existing files
    uv run python -m ltm.tools.setup --force

    # Skip subagent patching (keep existing agents as primary)
    uv run python -m ltm.tools.setup --no-patch

Subagent Patching:
    If your project has .claude/agents/*.md files, they will shadow the global
    Anima agent by default. The setup tool automatically adds 'ltm: subagent: true'
    to these files so they're treated as Task-invoked subagents rather than the
    main session identity. Use --no-patch to skip this behavior.
""")
        return 0

    if not project_dir.exists():
        print(f"Error: Project directory not found: {project_dir}")
        return 1

    print(f"Setting up LTM in: {project_dir}\n")

    # Default: install both
    install_commands = not hooks_only
    install_hooks = not commands_only

    success = True

    if install_commands:
        print("Installing commands...")
        try:
            copied, skipped = setup_commands(project_dir, force)
            print(f"  Commands: {copied} installed, {skipped} skipped\n")
        except Exception as e:
            print(f"  Error installing commands: {e}\n")
            success = False

    if install_hooks:
        print("Configuring hooks...")
        try:
            if not setup_hooks(project_dir, force):
                pass  # Warning already printed
            print()
        except Exception as e:
            print(f"  Error configuring hooks: {e}\n")
            success = False

    # Patch subagents unless --no-patch or running with specific options
    if not no_patch and not commands_only and not hooks_only:
        agents_dir = project_dir / ".claude" / "agents"
        if agents_dir.exists() and list(agents_dir.glob("*.md")):
            print("Patching agent definitions...")
            try:
                patched, skipped = patch_subagents(project_dir)
                if patched > 0 or skipped > 0:
                    print(f"  Agents: {patched} patched, {skipped} skipped\n")
                else:
                    print("  No agent files found\n")
            except Exception as e:
                print(f"  Error patching agents: {e}\n")
                success = False

    if success:
        print("Setup complete!")
        print("\nNext steps:")
        print("  1. Import starter seeds:")
        print("     uv run python -m ltm.tools.import_seeds seeds/")
        print("  2. Start a Claude Code session and say 'Welcome back'")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(run(sys.argv[1:]))
