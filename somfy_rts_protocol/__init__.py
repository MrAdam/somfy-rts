"""Somfy RTS protocol library — pure Python, no Home Assistant dependencies."""

from somfy_rts_protocol.commands import UP, MY, DOWN, PROG
from somfy_rts_protocol.frame import (
    build_frame,
    deobfuscate,
    checksum_valid,
    extract_address,
    extract_counter,
    extract_command,
)
from somfy_rts_protocol.encoder import frame_to_timings

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