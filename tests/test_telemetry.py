"""
Unit Tests for Telemetry Generation Module.

Tests:
1. Configurable payload length (bytes and bits).
2. Seed reproducibility (identical streams for identical seeds).
3. Independent streams for differing seeds.
4. Byte-oriented and bit-oriented conversions.
5. Synthetic telemetry patterns (Random, Alternating, Counter, All Zeros, All Ones).
6. Strict parameter validation and boundary error handling.
"""

import numpy as np
import pytest

from src.core.telemetry import TelemetryGenerator, TelemetryPayload, TelemetryPattern


class TestTelemetryPayload:
    """Tests for TelemetryPayload immutable container and conversions."""

    def test_payload_initialization_and_properties(self):
        raw = b"\x01\x02\x03\x04"
        payload = TelemetryPayload(raw)
        assert payload.data == raw
        assert payload.length_bytes == 4
        assert payload.length_bits == 32
        assert payload.hex() == "01020304"

    def test_to_bits_conversion(self):
        # 0xAA = 10101010b, 0x55 = 01010101b
        raw = bytes([0xAA, 0x55])
        payload = TelemetryPayload(raw)
        bits = payload.to_bits()

        assert isinstance(bits, np.ndarray)
        assert bits.dtype == np.uint8
        assert len(bits) == 16
        expected_bits = np.array([1, 0, 1, 0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 1, 0, 1], dtype=np.uint8)
        np.testing.assert_array_equal(bits, expected_bits)

    def test_to_bitstring(self):
        raw = bytes([0xA0])  # 10100000b
        payload = TelemetryPayload(raw)
        assert payload.to_bitstring() == "10100000"

    def test_from_bits_roundtrip_ndarray(self):
        original_bytes = b"SPACE_TELEMETRY"
        payload = TelemetryPayload(original_bytes)
        bits = payload.to_bits()

        reconstructed = TelemetryPayload.from_bits(bits)
        assert reconstructed.data == original_bytes
        assert reconstructed == payload

    def test_from_bits_roundtrip_string(self):
        bitstring = "1100110000110011"
        payload = TelemetryPayload.from_bits(bitstring)
        assert payload.length_bytes == 2
        assert payload.to_bitstring() == bitstring

    def test_from_bits_validation(self):
        # Non-multiple of 8
        with pytest.raises(ValueError, match="multiple of 8"):
            TelemetryPayload.from_bits("101")

        # Invalid characters in bitstring
        with pytest.raises(ValueError, match="only '0' and '1'"):
            TelemetryPayload.from_bits("10101012")

        # Non-binary array
        with pytest.raises(ValueError, match="strictly 0 or 1"):
            TelemetryPayload.from_bits(np.array([0, 1, 2, 0, 0, 0, 0, 0]))

        # Invalid type
        with pytest.raises(TypeError):
            TelemetryPayload.from_bits(12345)  # type: ignore

    def test_payload_type_validation(self):
        with pytest.raises(TypeError, match="must be bytes"):
            TelemetryPayload("not_bytes")  # type: ignore


class TestTelemetryGenerator:
    """Tests for TelemetryGenerator logic, reproducibility, and patterns."""

    def test_configurable_lengths(self):
        gen = TelemetryGenerator(seed=42)
        for length in [1, 2, 7, 32, 64, 256, 1024]:
            payload = gen.generate(length_bytes=length)
            assert payload.length_bytes == length
            assert payload.length_bits == length * 8
            assert len(payload.data) == length
            assert len(payload.to_bits()) == length * 8

    def test_seed_reproducibility(self):
        seed = 123456
        gen1 = TelemetryGenerator(seed=seed)
        gen2 = TelemetryGenerator(seed=seed)

        payload1 = gen1.generate(length_bytes=64)
        payload2 = gen2.generate(length_bytes=64)

        # Identical seeds must yield bit-for-bit identical payloads
        assert payload1.data == payload2.data
        assert payload1.to_bitstring() == payload2.to_bitstring()
        assert np.array_equal(payload1.to_bits(), payload2.to_bits())

    def test_differing_seeds_produce_different_payloads(self):
        gen1 = TelemetryGenerator(seed=101)
        gen2 = TelemetryGenerator(seed=202)

        payload1 = gen1.generate(length_bytes=32)
        payload2 = gen2.generate(length_bytes=32)

        assert payload1.data != payload2.data

    def test_consecutive_generations_vary_without_reset(self):
        gen = TelemetryGenerator(seed=999)
        p1 = gen.generate(length_bytes=32)
        p2 = gen.generate(length_bytes=32)
        assert p1.data != p2.data

        # Resetting the seed reproduces the exact first payload
        gen.set_seed(999)
        p3 = gen.generate(length_bytes=32)
        assert p1.data == p3.data

    def test_pattern_alternating(self):
        gen = TelemetryGenerator()
        payload = gen.generate(length_bytes=8, pattern=TelemetryPattern.ALTERNATING)
        assert payload.data == bytes([0xAA] * 8)
        assert payload.to_bitstring() == "10101010" * 8

    def test_pattern_counter(self):
        gen = TelemetryGenerator()
        payload = gen.generate(length_bytes=5, pattern=TelemetryPattern.COUNTER)
        assert payload.data == bytes([0, 1, 2, 3, 4])

        # Test wraparound at 256
        payload_long = gen.generate(length_bytes=300, pattern=TelemetryPattern.COUNTER)
        assert payload_long.data[255] == 255
        assert payload_long.data[256] == 0
        assert payload_long.data[257] == 1

    def test_pattern_all_zeros(self):
        gen = TelemetryGenerator()
        payload = gen.generate(length_bytes=16, pattern=TelemetryPattern.ALL_ZEROS)
        assert payload.data == bytes(16)
        assert all(b == 0 for b in payload.to_bits())

    def test_pattern_all_ones(self):
        gen = TelemetryGenerator()
        payload = gen.generate(length_bytes=16, pattern=TelemetryPattern.ALL_ONES)
        assert payload.data == bytes([0xFF] * 16)
        assert all(b == 1 for b in payload.to_bits())

    def test_pattern_as_string_input(self):
        gen = TelemetryGenerator()
        payload = gen.generate(length_bytes=4, pattern="alternating")
        assert payload.data == bytes([0xAA] * 4)

    def test_validation_invalid_length(self):
        gen = TelemetryGenerator()
        with pytest.raises(ValueError, match="strictly positive"):
            gen.generate(length_bytes=0)

        with pytest.raises(ValueError, match="strictly positive"):
            gen.generate(length_bytes=-10)

        with pytest.raises(TypeError, match="must be an integer"):
            gen.generate(length_bytes=16.5)  # type: ignore

        with pytest.raises(TypeError, match="must be an integer"):
            gen.generate(length_bytes="32")  # type: ignore

        with pytest.raises(ValueError, match="exceeds maximum allowed limit"):
            gen.generate(length_bytes=TelemetryGenerator.MAX_PAYLOAD_BYTES + 1)

    def test_validation_invalid_seed(self):
        with pytest.raises(TypeError, match="Seed must be an integer"):
            TelemetryGenerator(seed="abc")  # type: ignore

        with pytest.raises(ValueError, match="Seed must be within"):
            TelemetryGenerator(seed=-1)

        with pytest.raises(ValueError, match="Seed must be within"):
            TelemetryGenerator(seed=2**32 + 10)

    def test_validation_invalid_pattern(self):
        gen = TelemetryGenerator()
        with pytest.raises(ValueError, match="Invalid pattern 'invalid_mode'"):
            gen.generate(length_bytes=16, pattern="invalid_mode")

        with pytest.raises(TypeError, match="pattern must be"):
            gen.generate(length_bytes=16, pattern=12345)  # type: ignore
