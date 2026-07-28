# Somfy RTS

[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz/)

> This project is built with AI assistance. Free time is precious, and so is time with my family.

Home Assistant custom integration for Somfy RTS motorized blinds and shutters via RF.

Uses the [radio_frequency](https://developers.home-assistant.io/blog/2026/04/24/radio-frequency-entity-platform/) platform — no cloud, no TaHoma, no proprietary bridge. Works with any RF transmitter that exposes a `RadioFrequencyTransmitterEntity` (ESPHome + CC1101, Broadlink, RFXtrx, etc.).

## Requirements

- Home Assistant 2026.5 or later
- An RF transmitter supported by the `radio_frequency` platform (e.g. ESPHome with CC1101)
- Python 3.13+

## Hardware

A tested reference setup: ESP32-C3 + CC1101 433 MHz transceiver module.

See [`docs/rf_proxy.yaml`](docs/rf_proxy.yaml) for the ESPHome configuration.

## Installation

### HACS (recommended)

1. Add this repository as a custom repository in HACS
2. Install "Somfy RTS" from HACS
3. Restart Home Assistant

### Manual

```bash
cd /path/to/homeassistant/config
git clone https://github.com/MrAdam/somfy-rts.git
ln -s "$(pwd)/somfy-rts/custom_components/somfy_rts" custom_components/somfy_rts
```

## Configuration

1. Go to **Settings** → **Devices & Services** → **Add Integration** → **Somfy RTS**
2. Select your RF transmitter
3. Enter your remote's address (hex) and starting rolling code

### Finding your remote's parameters

The integration needs three values from your Somfy RTS remote:

| Parameter | How to find it |
|-----------|---------------|
| Address | Check the battery compartment sticker (6 hex digits), or capture with SDR/CC1101 |
| Rolling code | Start at 0 — the motor accepts any counter higher than the last seen value |
| Encryption key | Uses Telis 1 default (`0xA7`), configurable |

To capture your remote's parameters:

1. Enable `dump: raw` on your ESPHome receiver (see `docs/rf_proxy.yaml`)
2. Press a button on your remote while watching ESPHome logs
3. Decode the raw timings using the protocol library (see below)

Or use the standalone protocol library:

```python
from somfy_rts_protocol import build_frame, deobfuscate, checksum_valid

# After capturing and decoding raw timings:
frame = bytes.fromhex("A1BEA4168183AA")
plain = deobfuscate(frame)
assert checksum_valid(plain)
# Extract address, counter, and key from `plain`
```

## Protocol library

The protocol implementation lives in `custom_components/somfy_rts/protocol/` and is also available as a standalone Python package (`somfy_rts_protocol/`) with zero Home Assistant dependencies.

```python
from somfy_rts_protocol import build_frame, frame_to_timings, UP

frame = build_frame(address=0x970229, counter=42, command=UP)
timings = frame_to_timings(frame)
# timings = [9415, -89565, 2416, -2416, ...]
```

## License

MIT