"""Somfy RTS protocol library — pure Python, no Home Assistant dependencies."""

from .commands import UP, MY, DOWN, PROG
from .frame import (
    build_frame,
    deobfuscate,
    checksum_valid,
    extract_address,
    extract_counter,
    extract_command,
)
from .encoder import frame_to_timings

__all__ = [
    "UP",
    "MY",
    "DOWN",
    "PROG",
    "build_frame",
    "deobfuscate",
    "checksum_valid",
    "extract_address",
    "extract_counter",
    "extract_command",
    "frame_to_timings",
]