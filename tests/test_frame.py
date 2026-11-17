"""
Unit Tests for Telemetry Frame Formation and Management.
"""

import pytest
import numpy as np

from src.core.frame import TelemetryFrame, FrameStatus
from src.core.telemetry import TelemetryPayload
from src.error_detection.crc_engine import CRCEngine


class TestTelemetryFrame:

    def test_frame_assembly_and_header(self):
        payload = TelemetryPayload(b"HELLO_SPACE")
        frame = TelemetryFrame(sequence_number=105, payload=payload)

        assert frame.sequence_number == 105
        assert frame.payload_length == 11
        assert frame.status == FrameStatus.PENDING
        assert len(frame.header_bytes) == TelemetryFrame.HEADER_SIZE

    def test_crc_attachment_and_serialization(self):
        payload = TelemetryPayload(b"TEST_PAYLOAD")
        frame = TelemetryFrame(sequence_number=1, payload=payload)
        crc_engine = CRCEngine("CRC-16-CCITT")

        # Serializing before attaching CRC raises ValueError
        with pytest.raises(ValueError, match="CRC has not been attached"):
            frame.to_bytes()

        frame.attach_crc(crc_engine)
        assert len(frame.crc_bytes) == 2

        frame_bytes = frame.to_bytes()
        expected_len = TelemetryFrame.HEADER_SIZE + len(b"TEST_PAYLOAD") + 2
        assert len(frame_bytes) == expected_len

        # Verify bits representation
        bits = frame.to_bits()
        assert isinstance(bits, np.ndarray)
        assert len(bits) == expected_len * 8

    def test_deserialization_from_bytes(self):
        payload_data = b"ORBIT_DATA_99"
        crc_engine = CRCEngine("CRC-16-CCITT")
        frame_tx = TelemetryFrame(sequence_number=500, payload=payload_data)
        frame_tx.attach_crc(crc_engine)

        raw_bytes = frame_tx.to_bytes()
        frame_rx = TelemetryFrame.from_bytes(raw_bytes, crc_length=2)

        assert frame_rx.sequence_number == 500
        assert frame_rx.payload == payload_data
        assert frame_rx.crc_bytes == frame_tx.crc_bytes

    def test_invalid_parameters(self):
        with pytest.raises(ValueError):
            TelemetryFrame(sequence_number=-1, payload=b"X")

        with pytest.raises(ValueError):
            TelemetryFrame(sequence_number=70000, payload=b"X")

        with pytest.raises(TypeError):
            TelemetryFrame(sequence_number="abc", payload=b"X")  # type: ignore
