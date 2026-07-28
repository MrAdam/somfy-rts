"""RF command wrapper for the radio_frequency platform.

Uses the official ``rf-protocols`` library for Somfy RTS command encoding.
"""

from __future__ import annotations

from rf_protocols.codes.somfy.rts import SomfyRTSButton
from rf_protocols.commands.somfy_rts import SomfyRTSCommand as _SomfyRTSCommand

# Re-export for convenience
SomfyRTSCommand = _SomfyRTSCommand
SomfyRTSButton = SomfyRTSButton

__all__ = ["SomfyRTSCommand", "SomfyRTSButton"]