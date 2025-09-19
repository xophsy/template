#!/usr/bin/env python3
"""Generate a universal Steam Controller layout.

This script writes a Valve Data Format (VDF) configuration that maps Steam
Controller inputs to generic keyboard and mouse actions. The result serves as a
starting point for games that lack native controller support.

When run with ``--install`` on Windows, the layout is copied into Steam's
template directory so it overrides Steam's defaults for any game.
"""
from pathlib import Path
from argparse import ArgumentParser
import os
import shutil

VDF_TEMPLATE = """
"controller_config"
{{
    "Version" "1"
    "Title" "Universal Layout"
    "Description" "Generic keyboard/mouse layout for Steam Controller."
    "pads"
    {{
        "left_trackpad"
        {{
            "mode" "dpad"
            "keys" "W,A,S,D"
        }}
        "right_trackpad"
        {{
            "mode" "mouse"
            "sensitivity" "1.0"
        }}
        "left_trigger"
        {{
            "mode" "mouse_button"
            "button" "MOUSE1"
        }}
        "right_trigger"
        {{
            "mode" "mouse_button"
            "button" "MOUSE2"
        }}
        "a_button"
        {{
            "mode" "key"
            "key" "SPACE"
        }}
        "b_button"
        {{
            "mode" "key"
            "key" "ESCAPE"
        }}
        "x_button"
        {{
            "mode" "key"
            "key" "R"
        }}
        "y_button"
        {{
            "mode" "key"
            "key" "E"
        }}
    }}
}}
"""


def generate_vdf() -> str:
    """Return the layout VDF."""
    return VDF_TEMPLATE


def write_layout(path: Path) -> None:
    """Write the universal layout VDF to the provided path."""
    path.write_text(generate_vdf())


def default_steam_dir() -> Path:
    """Return the default Steam installation directory on Windows."""
    if os.name == "nt":
        prog_x86 = os.environ.get("ProgramFiles(x86)") or os.environ.get("ProgramFiles")
        if prog_x86:
            return Path(prog_x86) / "Steam"
    return Path.home() / ".steam/steam"


def install_layout(layout: Path, steam_dir: Path) -> Path:
    """Copy the layout into Steam's template directory and return the destination path."""
    templates = steam_dir / "controller_base" / "templates"
    templates.mkdir(parents=True, exist_ok=True)
    dest = templates / layout.name
    shutil.copy2(layout, dest)
    return dest


if __name__ == "__main__":
    parser = ArgumentParser(description="Generate universal Steam Controller layout")
    parser.add_argument(
        "--output", type=Path, default=Path("steam_universal_layout.vdf"), help="Output VDF file"
    )
    parser.add_argument(
        "--install",
        action="store_true",
        help="Install into Steam's template directory (Windows only)",
    )
    parser.add_argument(
        "--steam-dir",
        type=Path,
        default=default_steam_dir(),
        help="Path to Steam installation (for --install)",
    )
    args = parser.parse_args()

    write_layout(args.output)
    print(f"Universal layout written to {args.output.resolve()}")
    if args.install:
        if os.name != "nt":
            print("Skipping installation: only supported on Windows.")
        else:
            dest = install_layout(args.output, args.steam_dir)
            print(f"Layout installed to {dest}")
