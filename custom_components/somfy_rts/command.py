"""RF command wrapper for the radio_frequency platform.

The Home Assistant ``radio_frequency`` integration expects commands to have:
- ``frequency`` (int, Hz)
- ``modulation`` (str or enum, "OOK")
- ``get_raw_timings()`` → list of alternating mark/space durations in µs

This module provides ``SomfyRTSCommand`` which is compatible with
``radio_frequency.async_send_command``.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .protocol import build_frame, frame_to_timings, UP, MY, DOWN, PROG

FREQUENCY = 433_420_000


@dataclass
class SomfyRTSCommand:
    """A Somfy RTS command ready for RF transmission."""

    frequency: int = FREQUENCY
    modulation: str = "OOK"
    repeat_count: int = 0
    _timings: list[int] = field(default_factory=list, repr=False)

    @classmethod
    def build(
        cls,
        address: int,
        counter: int,
        command: int,
        *,
        key_byte: int = 0xA7,
        repeat_count: int = 0,
    ) -> SomfyRTSCommand:
        """Build a Somfy RTS command from parameters."""
        frame = build_frame(
            address=address,
            counter=counter,
            command=command,
            key_byte=key_byte,
        )
        timings = frame_to_timings(frame, repeats=repeat_count + 1)
        return cls(
            frequency=FREQUENCY,
            repeat_count=repeat_count,
            _timings=timings,
        )

    def get_raw_timings(self) -> list[int]:
        """Return the raw OOK timings for transmission."""
        return self._timings

    def get_frequency(self) -> int | None:
        """Return the carrier frequency for retuning."""
        return self.frequency