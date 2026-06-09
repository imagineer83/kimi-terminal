from __future__ import annotations

import argparse
import sys

from kimi_terminal.app import KimiTerminalApp


def main() -> int:
    parser = argparse.ArgumentParser(description="Kimi Terminal - Bloomberg-style TUI for A-share/HK stocks")
    parser.add_argument("--config-dir", type=str, default=None, help="Override config directory")
    args = parser.parse_args()
    app = KimiTerminalApp(config_dir=args.config_dir)
    app.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
