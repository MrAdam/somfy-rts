"""Constants for the Somfy RTS integration."""

from typing import Final

DOMAIN: Final = "somfy_rts"

CONF_ADDRESS: Final = "address"
CONF_COUNTER: Final = "rolling_code"
CONF_TRANSMITTER: Final = "transmitter_entity"

STORAGE_VERSION: Final = 1

DEFAULT_NAME: Final = "Somfy RTS Cover"
FREQUENCY: Final = 433_420_000