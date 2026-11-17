"""
Space Telemetry Frame Formation and Management Module.

Defines frame structures with Header, Sequence ID, Payload, and Footer/CRC.
Implements serialization, deserialization, and status classification.

SRS References:
- Feature 1: Telemetry & Frame Generation (FR-02, FR-03, FR-04)
- Feature 3: Error Detection (FR-12: Mark as VALID or ERROR-DETECTED)
- Verification Tests: TC-01, TC-03
"""

from __future__ import annotations

import enum
import struct
from typing import Optional, Union
import numpy as np

from src.core.telemetry import TelemetryPayload
from src.error_detection.crc_engine import CRCEngine
from src.error_detection.polynomials import CRC16_CCITT, CRCParameters


class FrameStatus(str, enum.Enum):
    """Integrity state of a received communication frame."""
    PENDING = "PENDING"
    VALID = "VALID"
    ERROR_DETECTED = "ERROR-DETECTED"


class TelemetryFrame:
    """
    Standardized Space Telemetry Frame.

    Format:
    ┌───────────────────────────┬────────────────────┬──────────────────────┐
    │          HEADER           │      PAYLOAD       │        FOOTER        │
    │ Sync (2B) | Seq (2B) | Len(2B)│  Data (N Bytes)   │  CRC-16/32 (2/4 B)   │
    └───────────────────────────┴────────────────────┴──────────────────────┘
    """

    SYNC_MARKER: int = 0x1ACF  # Standard CCSDS-derived Sync Pattern (2 bytes)
    HEADER_SIZE: int = 6       # 2B Sync + 2B Seq + 2B Length

    def __init__(
        self,
        sequence_number: int,
        payload: Union[TelemetryPayload, bytes],
        crc_bytes: Optional[bytes] = None,
        status: FrameStatus = FrameStatus.PENDING,
    ):
        if not isinstance(sequence_number, int) or isinstance(sequence_number, bool):
            raise TypeError(f"sequence_number must be int, got {type(sequence_number).__name__}")
        if sequence_number < 0 or sequence_number > 65535:
            raise ValueError(f"sequence_number must be between 0 and 65535, got {sequence_number}")

        if isinstance(payload, TelemetryPayload):
            self._payload = payload.data
        elif isinstance(payload, (bytes, bytearray)):
            self._payload = bytes(payload)
        else:
            raise TypeError(f"payload must be TelemetryPayload or bytes, got {type(payload).__name__}")

        if crc_bytes is not None and not isinstance(crc_bytes, (bytes, bytearray)):
            raise TypeError(f"crc_bytes must be bytes or None, got {type(crc_bytes).__name__}")

        self.sequence_number = sequence_number
        self.crc_bytes = bytes(crc_bytes) if crc_bytes is not None else b""
        self.status = status

    @property
    def payload(self) -> bytes:
        """Raw payload data."""
        return self._payload

    @property
    def payload_length(self) -> int:
        """Length of payload in bytes."""
        return len(self._payload)

    @property
    def header_bytes(self) -> bytes:
        """Serialized 6-byte header: Sync (2B) + Sequence (2B) + Payload Length (2B)."""
        return struct.pack(">HHH", self.SYNC_MARKER, self.sequence_number, self.payload_length)

    @property
    def data_for_crc(self) -> bytes:
        """Portion of frame over which CRC is calculated (Header + Payload)."""
        return self.header_bytes + self._payload

    def attach_crc(self, crc_engine: CRCEngine) -> None:
        """Compute CRC over header + payload and attach as frame footer."""
        self.crc_bytes = crc_engine.calculate_bytes(self.data_for_crc)

    def to_bytes(self) -> bytes:
        """Serialize full frame: Header + Payload + Footer (CRC)."""
        if not self.crc_bytes:
            raise ValueError("Cannot serialize frame: CRC has not been attached yet.")
        return self.header_bytes + self._payload + self.crc_bytes

    def to_bits(self) -> np.ndarray:
        """Return frame as 1D array of bits (uint8: 0 or 1, MSB-first)."""
        byte_data = self.to_bytes()
        byte_array = np.frombuffer(byte_data, dtype=np.uint8)
        return np.unpackbits(byte_array)

    @classmethod
    def from_bytes(
        cls,
        raw_frame: bytes,
        crc_length: int = 2,
    ) -> TelemetryFrame:
        """
        Parse raw received frame bytes into TelemetryFrame object.
        """
        if not isinstance(raw_frame, (bytes, bytearray)):
            raise TypeError(f"raw_frame must be bytes or bytearray, got {type(raw_frame).__name__}")

        min_length = cls.HEADER_SIZE + crc_length
        if len(raw_frame) < min_length:
            raise ValueError(
                f"Frame size ({len(raw_frame)} bytes) is smaller than minimum required header+footer ({min_length} bytes)"
            )

        sync, seq, payload_len = struct.unpack(">HHH", raw_frame[:cls.HEADER_SIZE])
        if sync != cls.SYNC_MARKER:
            # Sync marker mismatch (possible header corruption)
            pass

        expected_total = cls.HEADER_SIZE + payload_len + crc_length
        if len(raw_frame) != expected_total:
            # Allow parsing even if payload length header was corrupted
            payload_data = raw_frame[cls.HEADER_SIZE:-crc_length]
            crc_data = raw_frame[-crc_length:]
        else:
            payload_data = raw_frame[cls.HEADER_SIZE:cls.HEADER_SIZE + payload_len]
            crc_data = raw_frame[cls.HEADER_SIZE + payload_len:]

        return cls(
            sequence_number=seq,
            payload=payload_data,
            crc_bytes=crc_data,
            status=FrameStatus.PENDING,
        )

    def __repr__(self) -> str:
        return (
            f"TelemetryFrame(Seq={self.sequence_number}, "
            f"PayloadLen={self.payload_length}B, "
            f"CRC={self.crc_bytes.hex().upper() if self.crc_bytes else 'None'}, "
            f"Status={self.status.value})"
        )
