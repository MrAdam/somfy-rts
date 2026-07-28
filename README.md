# Somfy RTS

[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz/)

> [!IMPORTANT]
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

You need three values from your Somfy RTS remote: **address**, **rolling code**,
and **key byte**. Use the included decoder script to extract them from a raw
capture.

**Step 1: Enable raw capture on your RF Proxy**

Add ``dump: raw`` to the ``remote_receiver`` in your ESPHome config
(see ``docs/rf_proxy.yaml`` for a complete example).

```yaml
remote_receiver:
  id: rf_rx
  pin: GPIO8
  dump: raw
```

Flash the device.

**Step 2: Capture a button press**

Open ESPHome device logs and press a button on your Somfy remote:

```bash
esphome logs rf_proxy.yaml
```

You'll see output like:

```
[I][remote.raw:026]: Received Raw: 2457, -2505, 2465, -2502, 4714, -1243, ...
```

Copy the full ``Received Raw`` lines (including continuation lines).

**Step 3: Decode**

python3 docs/decode_capture.py
```

Paste the timings and press Ctrl+D. Output:

```
--- Capture 1 (87 values) ---
  ✓ Address:  0x970229
    Counter:  6834 (0x1AB2)
    Command:  0x1 (MY/STOP)
    Key byte: 0xA1
```

Use these values in the integration config flow.

## Credits

This integration builds on the work of many others who reverse-engineered
and documented the Somfy RTS protocol over the years:

- [**L-Henke**](https://github.com/L-Henke) — [reference implementation](https://github.com/home-assistant/core/pull/169920) for Home Assistant core and the [rf-protocols library](https://github.com/home-assistant-libs/rf-protocols/pull/8)
- [**nilsree/flipper-somfy**](https://github.com/nilsree/flipper-somfy) — well-documented Flipper Zero implementation that clarified frame format and timing constants
- [**Nickduino/Somfy\_Remote**](https://github.com/Nickduino/Somfy_Remote) — the original Arduino library that first documented the protocol in open source
- [**Pushstack**](https://pushstack.wordpress.com/somfy-rts-protocol/) — the definitive protocol reverse-engineering blog post
- [**Home Assistant architecture discussion #1365**](https://github.com/home-assistant/architecture/discussions/1365) — the radio\_frequency entity platform design

## License

MIT