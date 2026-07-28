#!/usr/bin/env python3
"""Decode raw Somfy RTS timings captured from an ESPHome remote_receiver.

Usage:
  1. Enable ``dump: raw`` on your ESPHome receiver (see docs/rf_proxy.yaml)
  2. Press a button on your Somfy remote
  3. Copy the raw timing lines from ESPHome logs
  4. Run: python3 decode_capture.py
  5. Paste the timings and press Ctrl+D

No dependencies beyond Python 3.9+ standard library.

The timings should look like:
    [I][remote.raw:026]: Received Raw: 2457, -2505, 2465, -2502, 4714, -1243, ...

Output: address, rolling counter, command, and key byte for each capture.
"""

from __future__ import annotations

import sys

SYMBOL = 604
SW_SYNC_MARK_MIN = 4500
COMMAND_NAMES = {0x1: "MY/STOP", 0x2: "UP", 0x4: "DOWN", 0x8: "PROG"}


# ── Timestamp parsing ───────────────────────────────────────────────

def parse_timings(text: str) -> list[int]:
    values: list[int] = []
    for part in text.replace(",", " ").split():
        part = part.strip()
        if not part:
            continue
        try:
            values.append(int(part))
        except ValueError:
            continue
    return values


# ── Sync detection + Manchester decode ──────────────────────────────

def find_data_start(timings: list[int]) -> int | None:
    """Return index of software sync high (~4550 µs mark)."""
    for i, v in enumerate(timings):
        if v > SW_SYNC_MARK_MIN:
            return i
    return None


def to_halfbits(data_timings: list[int]) -> list[int]:
    """Convert mark/space durations to half-bit signal (0=space, 1=mark).

    The first duration includes the software sync low (604 µs) merged
    with the first data half-bit.
    """
    sw_low = SYMBOL
    halfbits: list[int] = []
    first = abs(data_timings[0])
    remaining = first - sw_low
    halfbits.extend([0] * max(1, round(remaining / SYMBOL)))
    level = 1
    for v in data_timings[1:]:
        count = max(1, round(abs(v) / SYMBOL))
        halfbits.extend([level] * count)
        level = 1 - level
    return halfbits


def manchester_decode(halfbits: list[int]) -> tuple[list[int], bool]:
    """Decode Manchester.  1 = low→high, 0 = high→low."""
    bits: list[int] = []
    for i in range(0, len(halfbits) - 1, 2):
        a, b = halfbits[i], halfbits[i + 1]
        if a == 0 and b == 1:
            bits.append(1)
        elif a == 1 and b == 0:
            bits.append(0)
        else:
            bits.append(-1)
    return bits, all(b != -1 for b in bits)


# ── Frame deobfuscation + validation ────────────────────────────────

def bits_to_frame(bits: list[int]) -> bytes:
    valid = [b for b in bits if b != -1]
    if len(valid) < 56:
        valid.append(0)
    bitstr = "".join(str(b) for b in valid[:56])
    return bytes(int(bitstr[i:i + 8], 2) for i in range(0, 56, 8))


def deobfuscate(frame: bytes) -> bytearray:
    f = bytearray(frame)
    for i in range(6, 0, -1):
        f[i] ^= f[i - 1]
    return f


def checksum_valid(frame: bytearray | bytes) -> bool:
    f = bytearray(frame)
    expected = f[1] & 0x0F
    f[1] &= 0xF0
    csum = 0
    for b in f:
        csum ^= b ^ (b >> 4)
    return (csum & 0x0F) == expected


def extract_address(frame: bytearray | bytes) -> int:
    return (frame[4] << 16) | (frame[5] << 8) | frame[6]


def extract_counter(frame: bytearray | bytes) -> int:
    return (frame[2] << 8) | frame[3]


def extract_command(frame: bytearray | bytes) -> int:
    return (frame[1] >> 4) & 0x0F


# ── Main ────────────────────────────────────────────────────────────

def main() -> None:
    print("Paste ESPHome raw timings (Ctrl+D when done):")
    raw_text = sys.stdin.read()
    if not raw_text.strip():
        print("No input provided.", file=sys.stderr)
        sys.exit(1)

    captures: list[list[int]] = []
    current: list[int] = []
    for line in raw_text.strip().split("\n"):
        if "Received Raw:" in line:
            if current:
                captures.append(current)
                current = []
        current.extend(parse_timings(line))
    if current:
        captures.append(current)

    for i, timings in enumerate(captures):
        print(f"\n--- Capture {i + 1} ({len(timings)} values) ---")

        start = find_data_start(timings)
        if start is None:
            print("  Could not find software sync marker (~4700 µs mark)")
            continue

        data = timings[start + 1:]
        if len(data) < 10:
            print("  Not enough data samples after sync")
            continue

        hb = to_halfbits(data)
        bits, valid = manchester_decode(hb)
        if not valid:
            inv = sum(1 for b in bits if b == -1)
            print(f"  Manchester decode: {len(bits)} bits, {inv} invalid")
            continue

        frame = bits_to_frame(bits)
        print(f"  Obfuscated frame: {frame.hex().upper()}")

        plain = deobfuscate(frame)
        if not checksum_valid(plain):
            print("  ✗ Checksum invalid — frame may be corrupted")
            continue

        addr = extract_address(plain)
        ctr = extract_counter(plain)
        cmd = extract_command(plain)
        key = plain[0]

        print(f"  ✓ Address:  0x{addr:06X}")
        print(f"    Counter:  {ctr} (0x{ctr:04X})")
        print(f"    Command:  0x{cmd:X} ({COMMAND_NAMES.get(cmd, 'UNKNOWN')})")
        print(f"    Key byte: 0x{key:02X}")


if __name__ == "__main__":
    main()