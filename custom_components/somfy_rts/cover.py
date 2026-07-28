"""Somfy RTS cover entity for Home Assistant.

Each Somfy motor is represented as a Cover entity with open/close/stop
commands transmitted via the ``radio_frequency`` platform.
"""

from __future__ import annotations

from typing import Any

from homeassistant.components.cover import CoverEntity, CoverEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .command import SomfyRTSCommand
from .const import CONF_ADDRESS, CONF_COUNTER, CONF_TRANSMITTER, DOMAIN
from .protocol import UP, MY, DOWN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Somfy RTS cover from a config entry."""
    async_add_entities([SomfyRTSCover(entry)])


class SomfyRTSCover(CoverEntity):
    """Representation of a Somfy RTS motorized cover."""

    _attr_assumed_state = True
    _attr_supported_features = (
        CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE | CoverEntityFeature.STOP
    )
    _attr_device_class = None


    def __init__(self, entry: ConfigEntry) -> None:
        """Initialize the cover."""
        self._entry = entry
        self._attr_unique_id = f"{DOMAIN}_{entry.data[CONF_ADDRESS]:06x}"
        self._attr_name = entry.title
        # Work around propcache Cython bug: set all cached state attrs
        self._attr_is_closed = None
        self._attr_is_opening = None
        self._attr_is_closing = None

    @property
    def device_info(self):
        """Device info for the motor."""
        return {
            "identifiers": {(DOMAIN, f"{self._entry.data[CONF_ADDRESS]:06x}")},
            "name": self._entry.title,
            "manufacturer": "Somfy",
            "model": "RTS Motor",
        }

    async def _send_command(self, command: int) -> None:
        """Build and transmit a Somfy RTS command."""
        from homeassistant.components.radio_frequency import async_send_command

        # Read and increment the rolling code
        counter = self._entry.data[CONF_COUNTER]
        new_counter = (counter + 1) & 0xFFFF

        cmd = SomfyRTSCommand.build(
            address=self._entry.data[CONF_ADDRESS],
            counter=counter,
            command=command,
        )

        await async_send_command(
            self.hass,
            self._entry.data[CONF_TRANSMITTER],
            cmd,
        )

        # Persist the new counter
        new_data = {**self._entry.data, CONF_COUNTER: new_counter}
        self.hass.config_entries.async_update_entry(self._entry, data=new_data)

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open the cover."""
        await self._send_command(UP)

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Close the cover."""
        await self._send_command(DOWN)

    async def async_stop_cover(self, **kwargs: Any) -> None:
        """Stop the cover."""
        await self._send_command(MY)