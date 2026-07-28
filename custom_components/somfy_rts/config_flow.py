"""Config flow for Somfy RTS."""

from __future__ import annotations

from typing import Any
try:
    from rf_protocols import ModulationType
except ImportError:
    ModulationType = None  # type: ignore[assignment]
import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigEntry, OptionsFlow
from homeassistant.core import callback
from homeassistant.components.radio_frequency import async_get_transmitters
from homeassistant.helpers.selector import EntitySelector, EntitySelectorConfig

from .const import CONF_ADDRESS, CONF_COUNTER, CONF_TRANSMITTER, DEFAULT_NAME, DOMAIN, FREQUENCY


class SomfyRTSConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Somfy RTS."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step: select transmitter."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._transmitter = user_input[CONF_TRANSMITTER]
            return await self.async_step_configure()

        # Get available transmitters
        try:
            transmitters = async_get_transmitters(
                self.hass, FREQUENCY, ModulationType.OOK
            )
        except HomeAssistantError:
            return self.async_abort(reason="no_transmitters")

        if not transmitters:
            return self.async_abort(reason="no_compatible_transmitters")

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_TRANSMITTER): EntitySelector(
                        EntitySelectorConfig(
                            domain="radio_frequency",
                            include_entities=transmitters,
                        )
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_configure(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the configuration step: enter address and counter."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                address = int(user_input[CONF_ADDRESS], 16)
            except ValueError:
                errors[CONF_ADDRESS] = "invalid_hex"
            else:
                if not (0 <= address <= 0xFFFFFF):
                    errors[CONF_ADDRESS] = "address_out_of_range"

            if not errors:
                return self.async_create_entry(
                    title=user_input.get("name", DEFAULT_NAME),
                    data={
                        CONF_TRANSMITTER: self._transmitter,
                        CONF_ADDRESS: address,
                        CONF_COUNTER: int(user_input[CONF_COUNTER]),
                    },
                )

        return self.async_show_form(
            step_id="configure",
            data_schema=vol.Schema(
                {
                    vol.Required("name", default=DEFAULT_NAME): str,
                    vol.Required(CONF_ADDRESS, default="970229"): str,
                    vol.Required(CONF_COUNTER, default=0): int,
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Get the options flow for this handler."""
        return SomfyRTSOptionsFlow(config_entry)


class SomfyRTSOptionsFlow(OptionsFlow):
    """Handle options for Somfy RTS."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self._entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage options: update transmitter and counter."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_TRANSMITTER,
                        default=self.config_entry.data.get(CONF_TRANSMITTER, ""),
                    ): str,
                    vol.Required(
                        CONF_COUNTER,
                        default=self.config_entry.data.get(CONF_COUNTER, 0),
                    ): int,
                }
            ),
        )