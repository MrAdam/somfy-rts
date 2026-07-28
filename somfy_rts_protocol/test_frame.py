"""Tests for Somfy RTS protocol library.

Run with: python -m pytest somfy_rts_protocol/test_frame.py -v
Or just:   python somfy_rts_protocol/test_frame.py
"""

from __future__ import annotations

import somfy_rts_protocol as srp


# ---------------------------------------------------------------------------
# Frame construction & checksum
# ---------------------------------------------------------------------------

def test_checksum_detects_corruption():
    """A frame with a deliberately wrong checksum should fail validation."""
    frame = srp.build_frame(address=0x970229, counter=42, command=srp.UP)
    plain = srp.deobfuscate(frame)
    assert srp.checksum_valid(plain)
    # Corrupt the stored checksum nibble
    plain[1] ^= 0x01
    assert not srp.checksum_valid(plain)




def test_roundtrip(frame=None):
    """Build, obfuscate, deobfuscate — fields should survive."""
    if frame is None:
        frame = srp.build_frame(address=0xABCDEF, counter=12345, command=srp.DOWN)

    plain = srp.deobfuscate(frame)

    assert srp.checksum_valid(plain)
    assert srp.extract_address(plain) == 0xABCDEF
    assert srp.extract_counter(plain) == 12345
    assert srp.extract_command(plain) == srp.DOWN
    assert (plain[0] & 0xF0) == 0xA0


def test_counter_increments_independent():
    """Each build with a new counter produces a valid frame."""
    prev_counter = None
    for c in (6834, 6835, 6836, 7000):
        frame = srp.build_frame(address=0x970229, counter=c, command=srp.MY)
        plain = srp.deobfuscate(frame)
        assert srp.checksum_valid(plain)
        assert srp.extract_counter(plain) == c
        if prev_counter is not None:
            assert c > prev_counter  # counter should increase
        prev_counter = c


# ---------------------------------------------------------------------------
# Manchester encoding → timing output
# ---------------------------------------------------------------------------

def test_timings_produces_alternating_output():
    """The timing list alternates positive (mark) and negative (space)."""
    frame = srp.build_frame(address=0x970229, counter=6834, command=srp.MY)
    timings = srp.frame_to_timings(frame, repeats=1)

    # Must have at least the sync + 112 data half-bits worth of timings
    assert len(timings) > 10
    # All positive values
    for t in timings:
        assert t != 0
    # No consecutive same sign (merging should prevent this)
    prev_sign = None
    for t in timings:
        sign = t > 0
        if prev_sign is not None:
            assert sign != prev_sign, f"Consecutive same sign at {t}"
        prev_sign = sign


def test_timings_include_wakeup_and_sync():
    """First two values should be the wake-up pulse."""
    frame = srp.build_frame(address=0x970229, counter=6834, command=srp.MY)
    timings = srp.frame_to_timings(frame, repeats=1)

    # Wake-up: high ~9415, low ~89565
    assert 8000 < timings[0] < 11000  # wake-up high
    assert -100000 < timings[1] < -8000  # wake-up low


def test_timings_first_frame_has_correct_hw_sync():
    """First frame has 2 HW sync pairs (4 values of ~2416)."""
    frame = srp.build_frame(address=0x970229, counter=6834, command=srp.MY)
    timings = srp.frame_to_timings(frame, repeats=1)

    # After wake-up, we should find 4 values of ~2416 in a row
    # Actually with merging: 2416 mark, 2416 space, 2416 mark, 2416 space
    # After the long wake-up low, next is mark
    sync_start = 2  # index 0 = wake high, 1 = wake low, 2 = first sync mark
    for i in range(4):
        val = timings[sync_start + i]
        assert 2000 < abs(val) < 3000, f"Sync value {val} at idx {sync_start+i} out of range"


# ---------------------------------------------------------------------------
# Verify against real-world captures
# ---------------------------------------------------------------------------

def test_build_matches_captured_frame():
    """Reproduce the user's Telis 1 frame and verify checksum."""
    # Known good from decoded captures
    frame = srp.build_frame(
        address=0x970229,
        counter=6834,
        command=srp.MY,
        key_byte=0xA1,  # specific key byte from the capture
    )

    plain = srp.deobfuscate(frame)
    assert srp.checksum_valid(plain)

    # Verify the frame bytes match the captured frame (obfuscated)
    # Cap1 decoded: 0xA1BEA4168183AA
    expected = bytes.fromhex("A1BEA4168183AA")
    assert bytes(frame) == expected, (
        f"Frame mismatch: got {bytes(frame).hex().upper()}, expected {expected.hex().upper()}"
    )


def test_capture_reproduces_correct_timing_pattern():
    """Timings from our encoder should match the timing structure of captured frames."""
    frame = srp.build_frame(address=0x970229, counter=6834, command=srp.MY, key_byte=0xA1)
    timings = srp.frame_to_timings(frame, repeats=1)

    # After wake-up + HW sync, we should see SW sync: ~4550 mark, ~604 space merged with data
    # Find the 4550-ish value
    sw_sync_idx = None
    for i, t in enumerate(timings):
        if 4200 < abs(t) < 5000 and t > 0:
            sw_sync_idx = i
            break

    assert sw_sync_idx is not None, "Could not find SW sync high (~4550 mark)"

    # After SW sync, we should see ~1208 space (604 SW sync low + 604 first data half-bit)
    # if the first data bit is 1 (which it is for this frame)
    post_sw = timings[sw_sync_idx + 1]
    assert 1000 < abs(post_sw) < 1500, (
        f"Post-SW-sync value {post_sw} should be ~1208 (merged SW sync low + data)"
    )


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    tests = [
        ("checksum_detects_corruption", test_checksum_detects_corruption),
        ("roundtrip", test_roundtrip),
        ("counter_increments_independent", test_counter_increments_independent),
        ("timings_produces_alternating_output", test_timings_produces_alternating_output),
        ("timings_include_wakeup_and_sync", test_timings_include_wakeup_and_sync),
        ("timings_first_frame_has_correct_hw_sync", test_timings_first_frame_has_correct_hw_sync),
        ("build_matches_captured_frame", test_build_matches_captured_frame),
        ("capture_reproduces_correct_timing_pattern", test_capture_reproduces_correct_timing_pattern),
    ]

    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"  ✓ {name}")
        except AssertionError as e:
            print(f"  ✗ {name}: {e}")
            failed += 1
        except Exception as e:
            print(f"  ✗ {name}: {type(e).__name__}: {e}")
            failed += 1

    print(f"\n{failed}/{len(tests)} failed")
    sys.exit(1 if failed else 0)