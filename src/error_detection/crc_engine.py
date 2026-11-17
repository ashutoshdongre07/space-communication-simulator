"""
Cyclic Redundancy Check (CRC) Engine.

Implements standard CRC generation, appendage, and receiver syndrome evaluation
for space telemetry data.

SRS References:
- Feature 1: FR-04 (Calculate and append CRC before transmission)
- Feature 3: FR-10, FR-11 (Recompute and compare CRC at receiver)
- Verification Tests: TC-01, TC-03
"""

from typing import Tuple, Union
import numpy as np

from src.error_detection.polynomials import CRCParameters, CRC16_CCITT, CRC32_IEEE, SUPPORTED_CRC_PROFILES


def reflect_bits(val: int, width: int) -> int:
    """Reflect the lower `width` bits of `val`."""
    reflected = 0
    for i in range(width):
        if (val >> i) & 1:
            reflected |= 1 << (width - 1 - i)
    return reflected


class CRCEngine:
    """
    Table-driven CRC calculation and verification engine.
    """

    def __init__(self, params: Union[CRCParameters, str] = CRC16_CCITT):
        if isinstance(params, str):
            if params not in SUPPORTED_CRC_PROFILES:
                raise ValueError(
                    f"Unsupported CRC algorithm '{params}'. Supported: {list(SUPPORTED_CRC_PROFILES.keys())}"
                )
            self.params = SUPPORTED_CRC_PROFILES[params]
        elif isinstance(params, CRCParameters):
            self.params = params
        else:
            raise TypeError(f"params must be CRCParameters or str, got {type(params).__name__}")

        self.width = self.params.width
        self.mask = (1 << self.width) - 1
        self.top_bit = 1 << (self.width - 1)
        self.table = self._generate_lookup_table()

    def _generate_lookup_table(self) -> list[int]:
        """Precompute 256-entry CRC lookup table for fast execution."""
        table = []
        poly = self.params.polynomial

        for byte_val in range(256):
            if self.params.reflect_in:
                cur = reflect_bits(byte_val, 8) << (self.width - 8)
            else:
                cur = byte_val << (self.width - 8)

            for _ in range(8):
                if cur & self.top_bit:
                    cur = ((cur << 1) ^ poly) & self.mask
                else:
                    cur = (cur << 1) & self.mask

            if self.params.reflect_in:
                cur = reflect_bits(cur, self.width)

            table.append(cur)
        return table

    def calculate(self, data: bytes) -> int:
        """
        Calculate CRC checksum over arbitrary byte sequence.

        Args:
            data: Input byte sequence.

        Returns:
            Integer checksum (16-bit or 32-bit).
        """
        if not isinstance(data, (bytes, bytearray)):
            raise TypeError(f"Input data must be bytes or bytearray, got {type(data).__name__}")

        crc = self.params.initial_value

        if self.params.reflect_in:
            for byte in data:
                tbl_idx = (crc ^ byte) & 0xFF
                crc = (crc >> 8) ^ self.table[tbl_idx]
        else:
            shift = self.width - 8
            for byte in data:
                tbl_idx = ((crc >> shift) ^ byte) & 0xFF
                crc = ((crc << 8) ^ self.table[tbl_idx]) & self.mask

        if self.params.reflect_out and not self.params.reflect_in:
            crc = reflect_bits(crc, self.width)

        return (crc ^ self.params.final_xor) & self.mask

    def calculate_bytes(self, data: bytes) -> bytes:
        """Return the calculated CRC as big-endian bytes."""
        val = self.calculate(data)
        byte_len = self.width // 8
        return val.to_bytes(byte_len, byteorder="big")

    def append_crc(self, frame_without_crc: bytes) -> bytes:
        """
        Compute CRC over frame data and append as the frame footer (trailer).
        """
        crc_bytes = self.calculate_bytes(frame_without_crc)
        return frame_without_crc + crc_bytes

    def verify(self, frame_with_crc: bytes) -> Tuple[bool, int, int]:
        """
        Verify the CRC of an incoming received frame.

        Args:
            frame_with_crc: Full frame containing header, payload, and CRC footer.

        Returns:
            Tuple of (is_valid: bool, received_crc: int, computed_crc: int)
        """
        crc_len = self.width // 8
        if len(frame_with_crc) < crc_len:
            raise ValueError(
                f"Frame length ({len(frame_with_crc)}) is shorter than CRC footer length ({crc_len})"
            )

        data_part = frame_with_crc[:-crc_len]
        crc_part = frame_with_crc[-crc_len:]

        received_crc = int.from_bytes(crc_part, byteorder="big")
        computed_crc = self.calculate(data_part)

        is_valid = (received_crc == computed_crc)
        return is_valid, received_crc, computed_crc
