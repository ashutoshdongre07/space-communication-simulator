"""
Integration Tests for Complete End-to-End Simulation Workflow.
"""

import pytest
from src.simulation.config import SimulationConfig
from src.simulation.engine import SimulationEngine


class TestSimulationEngine:

    def test_error_free_scenario(self):
        config = SimulationConfig(
            num_frames=50,
            payload_size_bytes=32,
            channel_mode="none",
            target_ber=0.0,
            random_seed=100,
        )
        engine = SimulationEngine(config)
        result = engine.run()

        m = result.metrics
        assert m.total_frames == 50
        assert m.actual_corrupted_bits == 0
        assert m.actual_ber == 0.0
        assert m.actual_corrupted_frames == 0
        assert m.actual_fer == 0.0
        assert m.valid_frames == 50
        assert m.detected_corrupt_frames == 0
        assert m.undetected_error_frames == 0
        assert m.detection_accuracy == 100.0

        # DataFrame check
        df = result.to_dataframe()
        assert len(df) == 50
        assert (df["Receiver_Status"] == "VALID").all()

    def test_random_error_scenario(self):
        config = SimulationConfig(
            num_frames=100,
            payload_size_bytes=64,
            channel_mode="random",
            target_ber=0.01,  # 1% BER
            random_seed=2026,
        )
        engine = SimulationEngine(config)
        result = engine.run()

        m = result.metrics
        assert m.total_frames == 100
        assert m.actual_corrupted_bits > 0
        assert m.actual_ber > 0.0
        assert m.actual_corrupted_frames > 0
        assert m.actual_fer > 0.0
        assert m.detected_corrupt_frames > 0
        # CRC detection should catch corrupted frames with high accuracy
        assert m.detection_accuracy >= 99.0

    def test_burst_error_scenario(self):
        config = SimulationConfig(
            num_frames=50,
            payload_size_bytes=48,
            channel_mode="burst",
            burst_probability=0.3,
            burst_length=16,
            random_seed=777,
        )
        engine = SimulationEngine(config)
        result = engine.run()

        m = result.metrics
        assert m.total_frames == 50
        assert m.actual_corrupted_bits > 0
        assert m.detected_corrupt_frames == m.actual_corrupted_frames

    def test_crc32_algorithm_support(self):
        config = SimulationConfig(
            num_frames=20,
            payload_size_bytes=16,
            channel_mode="random",
            target_ber=0.02,
            crc_algorithm="CRC-32",
            random_seed=42,
        )
        engine = SimulationEngine(config)
        result = engine.run()

        df = result.to_dataframe()
        # Verify 32-bit CRC formatting (0xXXXXXXXX, 8 hex digits)
        sample_crc = df["Received_CRC"].iloc[0]
        assert len(sample_crc) == 10  # '0x' + 8 hex digits
