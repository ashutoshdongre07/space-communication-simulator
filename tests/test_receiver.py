"""
Unit Tests for Ground Station Receiver and Status Evaluation.
"""

from src.core.frame import TelemetryFrame, FrameStatus
from src.core.receiver import GroundStationReceiver
from src.error_detection.crc_engine import CRCEngine


class TestGroundStationReceiver:

    def test_clean_frame_marked_valid(self):
        crc_engine = CRCEngine("CRC-16-CCITT")
        receiver = GroundStationReceiver(crc_engine)

        frame = TelemetryFrame(sequence_number=7, payload=b"BATTERY_VOLTAGE_28V")
        frame.attach_crc(crc_engine)

        audit = receiver.process_frame(frame.to_bytes(), frame_index=0)
        assert audit.is_valid is True
        assert audit.status == FrameStatus.VALID
        assert audit.sequence_number == 7

    def test_corrupted_frame_marked_error_detected(self):
        crc_engine = CRCEngine("CRC-16-CCITT")
        receiver = GroundStationReceiver(crc_engine)

        frame = TelemetryFrame(sequence_number=8, payload=b"THRUSTER_PRESSURE")
        frame.attach_crc(crc_engine)

        raw = bytearray(frame.to_bytes())
        # Invert bit in payload
        raw[TelemetryFrame.HEADER_SIZE + 2] ^= 0x01

        audit = receiver.process_frame(bytes(raw), frame_index=1)
        assert audit.is_valid is False
        assert audit.status == FrameStatus.ERROR_DETECTED

    def test_malformed_frame_handled_gracefully(self):
        crc_engine = CRCEngine("CRC-16-CCITT")
        receiver = GroundStationReceiver(crc_engine)

        # Truncated byte sequence (less than minimum frame size)
        truncated = b"\x01\x02"
        audit = receiver.process_frame(truncated, frame_index=2)
        assert audit.status == FrameStatus.ERROR_DETECTED
        assert audit.is_valid is False
