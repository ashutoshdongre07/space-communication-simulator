"""
Ground Station Telemetry Receiver Module.

Processes incoming digital frame bytes, recomputes CRC, checks syndromes,
and marks frames as VALID or ERROR-DETECTED.

SRS References:
- Feature 3: FR-10, FR-11, FR-12, FR-13
- Verification Test: TC-03
"""

from dataclasses import dataclass
from typing import Optional
from src.core.frame import TelemetryFrame, FrameStatus
from src.error_detection.crc_engine import CRCEngine


@dataclass
class ReceiverFrameAudit:
    """Diagnostic audit record for a frame processed by the receiver."""
    frame_index: int
    sequence_number: int
    status: FrameStatus
    received_crc: int
    computed_crc: int
    payload_length: int
    is_valid: bool


class GroundStationReceiver:
    """
    Ground station receiver performing frame synchronization, CRC verification,
    and integrity classification.
    """

    def __init__(self, crc_engine: CRCEngine):
        self.crc_engine = crc_engine

    def process_frame(
        self,
        raw_bytes: bytes,
        frame_index: int = 0,
    ) -> ReceiverFrameAudit:
        """
        Ingest raw bytes from space channel, parse frame, verify CRC,
        and assign VALID or ERROR-DETECTED status.

        Args:
            raw_bytes: Corrupted or clean frame bytes from space channel.
            frame_index: Sequence index in transmission run.

        Returns:
            ReceiverFrameAudit summary.
        """
        crc_byte_len = self.crc_engine.width // 8

        try:
            # Parse frame structure
            frame = TelemetryFrame.from_bytes(raw_bytes, crc_length=crc_byte_len)

            # Recompute CRC over data portion (Header + Payload)
            is_valid, received_crc, computed_crc = self.crc_engine.verify(raw_bytes)

            status = FrameStatus.VALID if is_valid else FrameStatus.ERROR_DETECTED
            frame.status = status

            return ReceiverFrameAudit(
                frame_index=frame_index,
                sequence_number=frame.sequence_number,
                status=status,
                received_crc=received_crc,
                computed_crc=computed_crc,
                payload_length=frame.payload_length,
                is_valid=is_valid,
            )

        except Exception as e:
            # Malformed frame structure (e.g. truncated bytes)
            return ReceiverFrameAudit(
                frame_index=frame_index,
                sequence_number=-1,
                status=FrameStatus.ERROR_DETECTED,
                received_crc=0,
                computed_crc=0,
                payload_length=0,
                is_valid=False,
            )
