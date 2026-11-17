"""
Unit Tests for Space Communication Channel (Random and Burst Errors).
"""

import numpy as np
import pytest

from src.channel.random_error import RandomBitFlipper
from src.channel.burst_error import BurstErrorGenerator
from src.channel.channel_model import SpaceChannel, ChannelErrorMode
from src.core.frame import TelemetryFrame
from src.error_detection.crc_engine import CRCEngine


class TestSpaceChannel:

    def test_random_bit_flipper_zero_ber(self):
        flipper = RandomBitFlipper(error_probability=0.0)
        bits = np.array([1, 0, 1, 1, 0, 0, 1, 0], dtype=np.uint8)
        corrupted, num_errors, indices = flipper.corrupt_bits(bits)

        assert num_errors == 0
        assert len(indices) == 0
        np.testing.assert_array_equal(bits, corrupted)

    def test_random_bit_flipper_high_ber(self):
        flipper = RandomBitFlipper(error_probability=1.0)
        bits = np.array([1, 0, 1, 0], dtype=np.uint8)
        corrupted, num_errors, indices = flipper.corrupt_bits(bits)

        assert num_errors == 4
        expected = np.array([0, 1, 0, 1], dtype=np.uint8)
        np.testing.assert_array_equal(corrupted, expected)

    def test_burst_error_injection(self):
        generator = BurstErrorGenerator(burst_probability=1.0, burst_length=8)
        bits = np.zeros(64, dtype=np.uint8)
        corrupted, num_errors, indices = generator.corrupt_bits(bits)

        assert num_errors > 0
        assert len(indices) <= 8
        # Verify indices are contiguous
        assert max(indices) - min(indices) < 8

    def test_space_channel_error_free_mode(self):
        crc_engine = CRCEngine("CRC-16-CCITT")
        frame = TelemetryFrame(sequence_number=1, payload=b"SOLAR_ARRAY_TEMP")
        frame.attach_crc(crc_engine)

        channel = SpaceChannel(mode=ChannelErrorMode.NONE)
        rx_bytes, gt = channel.transmit(frame, frame_index=0)

        assert gt.injected_bit_errors == 0
        assert not gt.is_corrupted
        assert rx_bytes == frame.to_bytes()

    def test_space_channel_random_mode_ground_truth(self):
        crc_engine = CRCEngine("CRC-16-CCITT")
        frame = TelemetryFrame(sequence_number=10, payload=b"GYRO_ATTITUDE_X_Y_Z")
        frame.attach_crc(crc_engine)

        channel = SpaceChannel(mode=ChannelErrorMode.RANDOM, ber=0.05, seed=42)
        rx_bytes, gt = channel.transmit(frame, frame_index=1)

        # Ground truth must reflect altered bits
        if gt.injected_bit_errors > 0:
            assert rx_bytes != frame.to_bytes()
            assert len(gt.error_bit_indices) == gt.injected_bit_errors
            assert gt.is_corrupted is True
