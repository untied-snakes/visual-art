"""Command line: visual-art list | devices | displays | play | shuffle | render"""
import argparse
import os
from pathlib import Path

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")  # before pygame is imported

import pygame
import sounddevice as sd

from visual_art.audio import AudioInput
from visual_art.player import Player
from visual_art.registry import find_visuals
from visual_art.render import render
from visual_art.show import Show

def main() -> None:
    parser = argparse.ArgumentParser(prog="visual-art", description="Live audio visuals.")
    commands = parser.add_subparsers(dest="command", required=True)

    commands.add_parser("list", help="show available visuals")
    commands.add_parser("devices", help="show audio inputs")
    commands.add_parser("displays", help="show screens, to pick one with --display")

    play = commands.add_parser("play", help="play one visual")
    play.add_argument("name")
    add_live_options(play)

    shuffle = commands.add_parser("shuffle", help="rotate through all visuals (live set mode)")
    add_shuffle_options(shuffle)
    add_live_options(shuffle)

    render_cmd = commands.add_parser("render", help="render an audio file to MP4")
    render_cmd.add_argument("audio", type=Path)
    render_cmd.add_argument("--out", type=Path, help="output file (default: renders/<song>.mp4)")
    which = render_cmd.add_mutually_exclusive_group(required=True)
    which.add_argument("--visual", metavar="NAME", help="render one visual for the whole song")
    which.add_argument("--shuffle", action="store_true", help="rotate through all visuals")
    add_shuffle_options(render_cmd)
    render_cmd.add_argument("--seed", type=int, help="fix the shuffle order so re-renders match")
    render_cmd.add_argument("--size", default="1920x1080", help="video size, WIDTHxHEIGHT")
    render_cmd.add_argument("--fps", type=int, default=30)
    render_cmd.add_argument("--silent", action="store_true", help="leave the audio track out")

    args = parser.parse_args()
    visuals = find_visuals()

    if args.command == "list":
        for name in visuals:
            print(name)

    elif args.command == "devices":
        print(sd.query_devices())

    elif args.command == "displays":
        pygame.init()
        for i, (width, height) in enumerate(pygame.display.get_desktop_sizes()):
            print(f"{i}  {width}x{height}" + ("  (main)" if i == 0 else ""))

    elif args.command in ("play", "shuffle"):
        pygame.init()
        check_display(args.display, parser)
        width, height = parse_size(args.size, parser)
        if args.command == "play":
            check_name(args.name, visuals, parser)
            show = Show(visuals, width, height, names=[args.name])
        else:
            show = Show(visuals, width, height, names=list(visuals), seconds=args.seconds, fade=args.fade)
        audio = AudioInput(parse_device(args.device), args.gain)
        Player(show, audio, fullscreen=not args.windowed, display=args.display).run()

    elif args.command == "render":
        width, height = parse_size(args.size, parser)
        if args.visual:
            check_name(args.visual, visuals, parser)
            show = Show(visuals, width, height, names=[args.visual])
        else:
            show = Show(visuals, width, height, names=list(visuals),
                        seconds=args.seconds, fade=args.fade, seed=args.seed)
        out = args.out or Path("renders") / f"{args.audio.stem}.mp4"
        pygame.init()
        render(args.audio, out, show, width, height, args.fps, include_audio=not args.silent)
        print(f"  wrote {out}")


def add_live_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--device", help="audio input, by name or number from `devices`")
    parser.add_argument("--gain", type=float, default=1.0, help="input loudness multiplier")
    parser.add_argument("--display", type=int, default=0, help="screen number from `displays` (default: main)")
    parser.add_argument("--windowed", action="store_true", help="open in a window instead of fullscreen")
    parser.add_argument("--size", default="1920x1080", help="drawing size, WIDTHxHEIGHT, stretched to fit the screen")


def add_shuffle_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--seconds", type=float, default=45, help="time on each visual")
    parser.add_argument("--fade", type=float, default=4, help="crossfade length in seconds")


def check_name(name: str, visuals: dict, parser: argparse.ArgumentParser) -> None:
    if name not in visuals:
        parser.error(f"no visual named {name!r}. Try: {', '.join(visuals)}")


def check_display(display: int, parser: argparse.ArgumentParser) -> None:
    count = pygame.display.get_num_displays()
    if not 0 <= display < count:
        parser.error(f"no display {display}. There are {count}; see `visual-art displays`")


def parse_device(device: str | None):
    """sounddevice takes a number or a (partial) name."""
    return int(device) if device is not None and device.isdigit() else device


def parse_size(size: str, parser: argparse.ArgumentParser) -> tuple[int, int]:
    try:
        width, height = (int(n) for n in size.lower().split("x"))
    except ValueError:
        parser.error(f"--size must look like 1920x1080, got {size!r}")
    if width % 2 or height % 2:
        parser.error("--size needs even numbers (H.264 requires it)")
    return width, height
