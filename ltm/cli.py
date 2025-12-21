# MIT License
# Copyright (c) 2025 Matt / Grain Ecosystem

"""LTM CLI - Entry point for Long Term Memory commands."""

import sys


def main() -> int:
    """Main entry point for LTM CLI."""
    if len(sys.argv) < 2:
        print("LTM - Long Term Memory for Claude")
        print("Usage: ltm <command> [args]")
        print("")
        print("Commands:")
        print("  remember <text>  Save a memory")
        print("  recall <query>   Search memories")
        print("  forget <id>      Remove a memory")
        print("  memories         List all memories")
        print("  import-seeds <dir>  Import seed memories")
        return 0

    command = sys.argv[1]
    args = sys.argv[2:]

    match command:
        case "remember":
            from ltm.commands.remember import run
            return run(args)
        case "recall":
            from ltm.commands.recall import run
            return run(args)
        case "forget":
            from ltm.commands.forget import run
            return run(args)
        case "memories":
            from ltm.commands.memories import run
            return run(args)
        case "import-seeds":
            from ltm.tools.import_seeds import run
            return run(args)
        case _:
            print(f"Unknown command: {command}")
            return 1


if __name__ == "__main__":
    sys.exit(main())
