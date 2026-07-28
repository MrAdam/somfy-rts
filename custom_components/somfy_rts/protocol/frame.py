"""Somfy RTS frame construction and deobfuscation.

Frame format (7 bytes, 56 bits, before obfuscation):

    [0]  Encryption key byte (0xA0–0xAF)
    [1]  Command in high nibble, checksum in low nibble
    [2]  Rolling code, high byte (big-endian)
    [3]  Rolling code, low byte
    [4]  Address, high byte (big-endian)
    [5]  Address, middle byte
    [6]  Address, low byte

- Checksum: XOR of all nibbles of all bytes, masked to 4 bits.
- Obfuscation: chained XOR — frame[i] ^= frame[i-1] for i in 1..6.
"""

from __future__ import annotations


def build_frame(
    address: int,
    counter: int,
    command: int,
    *,
    key_byte: int = 0xA7,
) -> bytearray:
    """Build an obfuscated 7-byte Somfy RTS frame ready for transmission.

    Args:
        address: 24-bit remote address/ID.
        counter: 16-bit rolling code.
        command: 4-bit command (0x1=MY/STOP, 0x2=UP, 0x4=DOWN, 0x8=PROG).
        key_byte: Frame[0] encryption key (0xA0–0xAF). Default 0xA7.

    Returns:
        Obfuscated 7-byte frame.
    """
    frame = bytearray(7)

    frame[0] = key_byte & 0xFF
    frame[1] = (command & 0x0F) << 4  # checksum goes in low nibble
    frame[2] = (counter >> 8) & 0xFF
    frame[3] = counter & 0xFF
    frame[4] = (address >> 16) & 0xFF
    frame[5] = (address >> 8) & 0xFF
    frame[6] = address & 0xFF

    _compute_checksum(frame)
    _obfuscate(frame)

    return frame


def deobfuscate(frame: bytearray | bytes) -> bytearray:
    """Reverse the chained-XOR obfuscation in-place."""
    f = bytearray(frame)
    for i in range(6, 0, -1):
        f[i] ^= f[i - 1]
    return f


def checksum_valid(frame: bytearray | bytes) -> bool:
    """Check whether the frame's checksum is valid (deobfuscate first)."""
    f = bytearray(frame)
    expected = f[1] & 0x0F
    f[1] &= 0xF0  # zero the checksum nibble
    csum = 0
    for b in f:
        csum ^= b ^ (b >> 4)
    return (csum & 0x0F) == expected


def extract_address(frame: bytearray | bytes) -> int:
    """Extract the 24-bit address from a deobfuscated frame."""
    f = bytes(frame)
    return (f[4] << 16) | (f[5] << 8) | f[6]


def extract_counter(frame: bytearray | bytes) -> int:
    """Extract the 16-bit rolling code from a deobfuscated frame."""
    f = bytes(frame)
    return (f[2] << 8) | f[3]


def extract_command(frame: bytearray | bytes) -> int:
    """Extract the 4-bit command from a deobfuscated frame."""
    return (frame[1] >> 4) & 0x0F


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _compute_checksum(frame: bytearray) -> None:
    """Compute nibble-wise XOR checksum and store in frame[1] low nibble."""
    csum = 0
    for b in frame:
        csum ^= b ^ (b >> 4)
    frame[1] |= csum & 0x0F


def _obfuscate(frame: bytearray) -> None:
    """Chained XOR: frame[i] ^= frame[i-1] for i in 1..6."""
    for i in range(1, 7):
        frame[i] ^= frame[i - 1]