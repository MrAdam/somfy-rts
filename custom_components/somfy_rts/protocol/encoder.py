"""Manchester encoder and RF timing generation for Somfy RTS.

Produces the alternating mark/space duration sequence suitable for
ESPHome's ``remote_transmitter`` or Home Assistant's
``RadioFrequencyCommand``.
"""

from __future__ import annotations

# Timing constants (microseconds)
SYMBOL = 604  # Manchester half-symbol
WAKEUP_HIGH = 9415
WAKEUP_LOW = 89565
HW_SYNC = 2416  # 4 × SYMBOL
SW_SYNC_HIGH = 4550
SW_SYNC_LOW = SYMBOL
INTERFRAME_GAP = 30415

HW_SYNC_PAIRS_FIRST = 2
HW_SYNC_PAIRS_REPEAT = 7
FRAME_BITS = 56


def frame_to_timings(
    frame: bytes | bytearray,
    *,
    repeats: int = 2,
) -> list[int]:
    """Convert an obfuscated 7-byte frame to raw OOK timing sequence.

    Returns alternating [mark, space, mark, space, ...] durations
    in microseconds, with consecutive same-level runs merged.
    Positive = mark (carrier ON), negative = space (carrier OFF).

    Args:
        frame: Obfuscated 7-byte Somfy frame (from ``build_frame``).
        repeats: Number of frame repetitions (default 2). First frame
            uses 2 HW sync pairs; subsequent frames use 7.

    Returns:
        Timing list for direct use with ``remote_transmitter``.
    """
    if repeats < 1:
        repeats = 1

    push = _Merger()

    # Wake-up pulse (once)
    push.mark(WAKEUP_HIGH)
    push.space(WAKEUP_LOW)

    for r in range(repeats):
        _encode_one_frame(push, frame, first=(r == 0))

    return push.result()


def _encode_one_frame(push: _Merger, frame: bytes | bytearray, *, first: bool) -> None:
    """Encode one frame (sync + Manchester payload)."""
    # Hardware sync
    hw_pairs = HW_SYNC_PAIRS_FIRST if first else HW_SYNC_PAIRS_REPEAT
    for _ in range(hw_pairs):
        push.mark(HW_SYNC)
        push.space(HW_SYNC)

    # Software sync
    push.mark(SW_SYNC_HIGH)
    push.space(SW_SYNC_LOW)

    # Data: 56 bits, MSB first, Manchester (1=low->high, 0=high->low)
    for bit_idx in range(FRAME_BITS):
        byte_idx = bit_idx // 8
        bit_pos = 7 - (bit_idx % 8)
        b = (frame[byte_idx] >> bit_pos) & 1

        if b:
            push.space(SYMBOL)
            push.mark(SYMBOL)
        else:
            push.mark(SYMBOL)
            push.space(SYMBOL)

    # Inter-frame gap
    push.space(INTERFRAME_GAP)


class _Merger:
    """Accumulates mark/space durations, merging consecutive same-polarity runs."""

    def __init__(self) -> None:
        self._timings: list[int] = []
        self._last = 0  # 1 = last was mark, 0 = last was space, -1 = unset

    def mark(self, duration: int) -> None:
        if self._last == 1:
            self._timings[-1] += duration
        else:
            self._timings.append(duration)
            self._last = 1

    def space(self, duration: int) -> None:
        if self._last == 0:
            self._timings[-1] = -(-self._timings[-1] + duration)  # keep negative
        else:
            self._timings.append(-duration)
            self._last = 0

    def result(self) -> list[int]:
        return self._timings