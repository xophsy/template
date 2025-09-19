#!/usr/bin/env python3
"""Run the Steam Controller as a stand-alone keyboard and mouse mapper.

The original iteration of this script generated a Valve Data Format (VDF)
profile that had to be imported into Steam.  That still left Steam in charge of
the controller and prevented the hardware from behaving like a dedicated input
device for games or applications outside of the Steam ecosystem.

This rewrite performs the mapping at runtime without launching Steam.  It opens
the controller through the operating system's generic gamepad interface (as
exposed by ``pygame``) and replays the inputs as synthetic keyboard and mouse
events using ``pynput``.  The default layout mirrors the old template—left
trackpad for WASD, right trackpad as a mouse, triggers mapped to the primary and
secondary mouse buttons, and face buttons bound to Space, Escape, R, and E—but
all of that logic lives entirely in this process.

The script supports hotplug listing, configurable polling cadence, axis
deadzones, and mouse sensitivity adjustments so you can tailor the feel to any
game.  Because it never talks to Steam, the controller behaves like a universal
peripheral for any Windows, macOS, or Linux title that accepts keyboard and
mouse input.
"""

from __future__ import annotations

from argparse import ArgumentParser, Namespace
from dataclasses import dataclass
import importlib.util
import json
import sys
import time
from typing import Dict, Iterable, Mapping, MutableMapping, Optional, Tuple


# Third-party modules are loaded lazily so that ``--list-joysticks`` can run
# even if the runtime dependencies are missing.
pygame = None
KeyboardController = None
Key = None
KeyCode = None
MouseController = None
Button = None


def _require_dependency(module: str, pip_name: str) -> None:
    """Abort with a helpful message if a dependency is missing."""

    if importlib.util.find_spec(module) is None:
        raise SystemExit(
            f"The '{module}' module is required. Install it with 'pip install {pip_name}'."
        )


def _load_dependencies() -> None:
    """Import pygame and pynput only when they are actually needed."""

    global pygame, KeyboardController, Key, KeyCode, MouseController, Button

    if pygame is not None:
        # Already loaded
        return

    _require_dependency("pygame", "pygame")
    _require_dependency("pynput", "pynput")

    import pygame as _pygame
    from pynput.keyboard import Controller as _KeyboardController
    from pynput.keyboard import Key as _Key
    from pynput.keyboard import KeyCode as _KeyCode
    from pynput.mouse import Controller as _MouseController
    from pynput.mouse import Button as _Button

    pygame = _pygame
    KeyboardController = _KeyboardController
    Key = _Key
    KeyCode = _KeyCode
    MouseController = _MouseController
    Button = _Button


SPECIAL_KEYS: Mapping[str, str] = {
    "space": "space",
    "esc": "esc",
    "escape": "esc",
    "enter": "enter",
    "return": "enter",
    "tab": "tab",
    "shift": "shift",
    "ctrl": "ctrl",
    "control": "ctrl",
    "alt": "alt",
    "left": "left",
    "right": "right",
    "up": "up",
    "down": "down",
}


def _resolve_key(name: str):
    """Translate a textual key description into a pynput key object."""

    lower = name.lower()
    if lower in SPECIAL_KEYS:
        return getattr(Key, SPECIAL_KEYS[lower])
    if len(name) == 1:
        return KeyCode.from_char(name)
    raise ValueError(f"Unsupported key binding '{name}'.")


@dataclass
class AxisConfig:
    """Configuration for an axis that drives discrete key presses."""

    x_axis: int
    y_axis: int
    threshold: float


@dataclass
class MouseAxisConfig:
    """Configuration for an axis that controls mouse movement."""

    x_axis: int
    y_axis: int
    sensitivity: float
    deadzone: float


@dataclass
class TriggerConfig:
    """Configuration for an analog trigger mapped to a mouse button."""

    axis: int
    threshold: float
    button: str


DEFAULT_LAYOUT = {
    "axes": {
        "left_pad": {"x": 0, "y": 1},
        "right_pad": {"x": 2, "y": 3},
    },
    "triggers": {"left": 4, "right": 5},
    "buttons": {
        "a": 0,
        "b": 1,
        "x": 2,
        "y": 3,
        "lb": 4,
        "rb": 5,
        "back": 6,
        "start": 7,
    },
    "exit_button": 6,
}


def _load_layout(path: Optional[str]) -> Mapping[str, object]:
    """Return the controller layout mapping, optionally loading it from JSON."""

    if path is None:
        return DEFAULT_LAYOUT
    with open(path, "r", encoding="utf8") as handle:
        data = json.load(handle)
    return data


def _list_joysticks() -> None:
    """Print every joystick pygame can see and exit."""

    _load_dependencies()
    pygame.init()
    pygame.joystick.init()
    count = pygame.joystick.get_count()
    if count == 0:
        print("No controllers detected.")
        return
    print(f"Detected {count} controller(s):")
    for index in range(count):
        joystick = pygame.joystick.Joystick(index)
        joystick.init()
        print(f"  [{index}] {joystick.get_name()}")
        joystick.quit()


def _press(keyboard, pressed: MutableMapping[object, bool], key) -> None:
    if not pressed.get(key):
        keyboard.press(key)
        pressed[key] = True


def _release(keyboard, pressed: MutableMapping[object, bool], key) -> None:
    if pressed.get(key):
        keyboard.release(key)
        pressed[key] = False


def _update_axis_keys(value: float, negative_key, positive_key, keyboard, pressed, threshold: float) -> None:
    if value <= -threshold:
        _press(keyboard, pressed, negative_key)
        _release(keyboard, pressed, positive_key)
    elif value >= threshold:
        _press(keyboard, pressed, positive_key)
        _release(keyboard, pressed, negative_key)
    else:
        _release(keyboard, pressed, negative_key)
        _release(keyboard, pressed, positive_key)


def _update_trigger(value: float, mouse, pressed: MutableMapping[object, bool], button, threshold: float) -> None:
    if value >= threshold:
        if not pressed.get(button):
            mouse.press(button)
            pressed[button] = True
    else:
        if pressed.get(button):
            mouse.release(button)
            pressed[button] = False


def _run_mapper(args: Namespace) -> None:
    """Main loop that keeps the controller synced to keyboard and mouse."""

    _load_dependencies()

    layout = _load_layout(args.layout)
    axes = layout["axes"]
    triggers = layout["triggers"]
    buttons = layout["buttons"]
    exit_button = layout.get("exit_button", 6)

    pygame.init()
    pygame.joystick.init()

    count = pygame.joystick.get_count()
    if count == 0:
        raise SystemExit("No controllers detected. Connect the Steam Controller and try again.")
    if args.joystick_index >= count:
        raise SystemExit(f"Joystick index {args.joystick_index} is out of range (detected {count}).")

    joystick = pygame.joystick.Joystick(args.joystick_index)
    joystick.init()
    print(f"Using controller: {joystick.get_name()}")

    keyboard = KeyboardController()
    mouse = MouseController()

    key_bindings = {
        "w": _resolve_key("w"),
        "a": _resolve_key("a"),
        "s": _resolve_key("s"),
        "d": _resolve_key("d"),
        "space": _resolve_key("space"),
        "escape": _resolve_key("escape"),
        "r": _resolve_key("r"),
        "e": _resolve_key("e"),
    }

    button_bindings = {
        buttons.get("a", 0): key_bindings["space"],
        buttons.get("b", 1): key_bindings["escape"],
        buttons.get("x", 2): key_bindings["r"],
        buttons.get("y", 3): key_bindings["e"],
    }

    left_axis = AxisConfig(axes["left_pad"]["x"], axes["left_pad"]["y"], args.dpad_threshold)
    right_axis = MouseAxisConfig(
        axes["right_pad"]["x"], axes["right_pad"]["y"], args.mouse_sensitivity, args.mouse_deadzone
    )
    left_trigger = TriggerConfig(triggers["left"], args.trigger_threshold, "left")
    right_trigger = TriggerConfig(triggers["right"], args.trigger_threshold, "right")

    key_state: Dict[object, bool] = {}
    mouse_state: Dict[object, bool] = {}
    button_state: Dict[int, bool] = {}

    print("Press the BACK button to exit.")

    try:
        while True:
            pygame.event.pump()

            left_x = joystick.get_axis(left_axis.x_axis)
            left_y = joystick.get_axis(left_axis.y_axis)
            _update_axis_keys(left_x, key_bindings["a"], key_bindings["d"], keyboard, key_state, left_axis.threshold)
            _update_axis_keys(left_y, key_bindings["w"], key_bindings["s"], keyboard, key_state, left_axis.threshold)

            right_x = joystick.get_axis(right_axis.x_axis)
            right_y = joystick.get_axis(right_axis.y_axis)
            if abs(right_x) >= right_axis.deadzone or abs(right_y) >= right_axis.deadzone:
                dx = int(right_x * right_axis.sensitivity)
                dy = int(right_y * right_axis.sensitivity)
                if dx or dy:
                    mouse.move(dx, dy)

            left_value = joystick.get_axis(left_trigger.axis)
            right_value = joystick.get_axis(right_trigger.axis)
            _update_trigger(left_value, mouse, mouse_state, Button.left, left_trigger.threshold)
            _update_trigger(right_value, mouse, mouse_state, Button.right, right_trigger.threshold)

            for button_index, key in button_bindings.items():
                pressed = bool(joystick.get_button(button_index))
                if pressed and not button_state.get(button_index):
                    keyboard.press(key)
                    button_state[button_index] = True
                elif not pressed and button_state.get(button_index):
                    keyboard.release(key)
                    button_state[button_index] = False

            if joystick.get_button(exit_button):
                print("Exit button pressed; stopping mapper.")
                break

            time.sleep(args.poll_interval)
    finally:
        for key, pressed in list(key_state.items()):
            if pressed:
                keyboard.release(key)
        for key, pressed in list(button_state.items()):
            if pressed:
                keyboard.release(button_bindings[key])
        for btn, pressed in list(mouse_state.items()):
            if pressed:
                mouse.release(btn)
        joystick.quit()
        pygame.quit()


def build_parser() -> ArgumentParser:
    """Create the command-line parser."""

    parser = ArgumentParser(description="Run the Steam Controller without Steam as a keyboard/mouse mapper")
    parser.add_argument(
        "--list-joysticks",
        action="store_true",
        help="List detected controllers and exit (does not require configuration)",
    )
    parser.add_argument(
        "--joystick-index",
        type=int,
        default=0,
        help="Index of the controller to use (see --list-joysticks)",
    )
    parser.add_argument(
        "--layout",
        type=str,
        default=None,
        help="Path to a JSON file that overrides the default axis/button mapping",
    )
    parser.add_argument(
        "--mouse-sensitivity",
        type=float,
        default=18.0,
        help="Multiplier applied to right trackpad axis values when moving the mouse",
    )
    parser.add_argument(
        "--mouse-deadzone",
        type=float,
        default=0.08,
        help="Deadzone for the right trackpad axes before mouse movement is applied",
    )
    parser.add_argument(
        "--dpad-threshold",
        type=float,
        default=0.45,
        help="Axis magnitude required for WASD presses on the left trackpad",
    )
    parser.add_argument(
        "--trigger-threshold",
        type=float,
        default=0.5,
        help="Trigger value required before mouse buttons are pressed",
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=0.01,
        help="Delay (seconds) between controller polls",
    )
    return parser


def main(argv: Optional[Iterable[str]] = None) -> None:
    """Entrypoint used by both the CLI and potential unit tests."""

    parser = build_parser()
    args = parser.parse_args(argv)

    if args.list_joysticks:
        _list_joysticks()
        return

    _run_mapper(args)


if __name__ == "__main__":
    main()
