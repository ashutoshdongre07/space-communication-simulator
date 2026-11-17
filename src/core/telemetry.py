"""
Telemetry Generation Module.

Implements synthetic binary and byte-oriented telemetry payload generation
for spacecraft digital communication simulation.

SRS References:
- Feature 1: Telemetry and Frame Generation (FR-01, FR-03)
- Verification Test: TC-01 (Payload Generation Component)
"""

from __future__ import annotations

import enum
from typing import Optional, Union
import numpy as np


class TelemetryPattern(str, enum.Enum):
    """Supported synthetic telemetry payload generation patterns."""
    RANDOM = "random"             # Pseudo-random bytes (simulating sensor noise / scientific data)
    ALTERNATING = "alternating"   # Alternating bit pattern (0xAA = 10101010b)
    COUNTER = "counter"           # Sequential counter bytes (0x00, 0x01, 0x02, ...)
    ALL_ZEROS = "all_zeros"       # Static baseline (0x00)
    ALL_ONES = "all_ones"         # Static baseline (0xFF)


class TelemetryPayload:
    """
    Immutable telemetry payload representation supporting both byte-oriented
    and bit-oriented operations.
    """

    def __init__(self, data: bytes):
        if not isinstance(data, (bytes, bytearray)):
            raise TypeError(f"Payload data must be bytes or bytearray, got {type(data).__name__}")
        self._data = bytes(data)

    @property
    def data(self) -> bytes:
        """Raw byte-oriented payload."""
        return self._data

    @property
    def length_bytes(self) -> int:
        """Payload length in bytes."""
        return len(self._data)

    @property
    def length_bits(self) -> int:
        """Payload length in bits."""
        return len(self._data) * 8

    def to_bits(self) -> np.ndarray:
        """
        Convert payload bytes into a 1D NumPy array of bits (uint8: 0 or 1),
        Most Significant Bit (MSB) first per space communications standard.
        """
        if not self._data:
            return np.empty(0, dtype=np.uint8)
        # Unpack bytes into MSB-first uint8 bit array
        byte_array = np.frombuffer(self._data, dtype=np.uint8)
        return np.unpackbits(byte_array)

    def to_bitstring(self) -> str:
        """Return binary string representation (e.g. '10101010...')."""
        bits = self.to_bits()
        return "".join(bits.astype(str))

    def hex(self) -> str:
        """Return uppercase hex representation."""
        return self._data.hex().upper()

    @classmethod
    def from_bits(cls, bits: Union[np.ndarray, list[int], str]) -> TelemetryPayload:
        """
        Construct a TelemetryPayload from a 1D array, list, or string of bits.
        Bits must have a length divisible by 8.
        """
        if isinstance(bits, str):
            if not all(c in ('0', '1') for c in bits):
                raise ValueError("Bitstring must contain only '0' and '1' characters.")
            if len(bits) % 8 != 0:
                raise ValueError(f"Bit length must be a multiple of 8, got {len(bits)} bits.")
            bit_array = np.array([int(c) for c in bits], dtype=np.uint8)
        elif isinstance(bits, (np.ndarray, list)):
            bit_array = np.asarray(bits, dtype=np.uint8)
            if not np.all((bit_array == 0) | (bit_array == 1)):
                raise ValueError("Bit values must be strictly 0 or 1.")
            if len(bit_array) % 8 != 0:
                raise ValueError(f"Bit length must be a multiple of 8, got {len(bit_array)} bits.")
        else:
            raise TypeError(f"Unsupported bits type: {type(bits).__name__}")

        packed = np.packbits(bit_array)
        return cls(packed.tobytes())

    def __eq__(self, other: object) -> bool:
        if isinstance(other, TelemetryPayload):
            return self._data == other._data
        if isinstance(other, (bytes, bytearray)):
            return self._data == bytes(other)
        return False

    def __repr__(self) -> str:
        preview = self._data[:8].hex().upper()
        if len(self._data) > 8:
            preview += "..."
        return f"TelemetryPayload({len(self._data)} bytes, [{preview}])"


class TelemetryGenerator:
    """
    Generator for synthetic spacecraft telemetry payloads.

    Provides deterministic, reproducible payload streams with configurable
    sizes and patterns.
    """

    MAX_PAYLOAD_BYTES = 65536  # Upper bound safety limit (64 KB)

    def __init__(self, seed: Optional[int] = None):
        """
        Initialize the generator.

        Args:
            seed: Optional integer seed for pseudo-random reproducibility.
                  If None, generation uses system entropy.
        """
        self.set_seed(seed)

    def set_seed(self, seed: Optional[int]) -> None:
        """Configure or reset the PRNG seed."""
        if seed is not None:
            if not isinstance(seed, int) or isinstance(seed, bool):
                raise TypeError(f"Seed must be an integer or None, got {type(seed).__name__}")
            if seed < 0 or seed > 2**32 - 1:
                raise ValueError(f"Seed must be within [0, 2^32 - 1], got {seed}")
        self._seed = seed
        self._rng = np.random.default_rng(seed)

    @property
    def seed(self) -> Optional[int]:
        """Current seed configured for this generator instance."""
        return self._seed

    def generate(
        self,
        length_bytes: int,
        pattern: Union[TelemetryPattern, str] = TelemetryPattern.RANDOM,
    ) -> TelemetryPayload:
        """
        Generate a synthetic telemetry payload.

        Args:
            length_bytes: Exact payload length in bytes (must be > 0 and <= MAX_PAYLOAD_BYTES).
            pattern: Pattern type ('random', 'alternating', 'counter', 'all_zeros', 'all_ones').

        Returns:
            TelemetryPayload instance containing generated data.

        Raises:
            TypeError: If arguments are of incorrect type.
            ValueError: If parameters are outside valid bounds.
        """
        # Validate length_bytes
        if not isinstance(length_bytes, int) or isinstance(length_bytes, bool):
            raise TypeError(f"length_bytes must be an integer, got {type(length_bytes).__name__}")
        if length_bytes <= 0:
            raise ValueError(f"length_bytes must be strictly positive (> 0), got {length_bytes}")
        if length_bytes > self.MAX_PAYLOAD_BYTES:
            raise ValueError(
                f"length_bytes exceeds maximum allowed limit ({self.MAX_PAYLOAD_BYTES}), "
                f"got {length_bytes}"
            )

        # Validate pattern
        if isinstance(pattern, str):
            try:
                pattern = TelemetryPattern(pattern.lower())
            except ValueError:
                valid_modes = [p.value for p in TelemetryPattern]
                raise ValueError(f"Invalid pattern '{pattern}'. Supported patterns: {valid_modes}")
        elif not isinstance(pattern, TelemetryPattern):
            raise TypeError(f"pattern must be TelemetryPattern or str, got {type(pattern).__name__}")

        # Generate payload based on pattern
        if pattern == TelemetryPattern.RANDOM:
            # Generate uniform pseudo-random bytes via isolated RNG
            raw_data = self._rng.integers(0, 256, size=length_bytes, dtype=np.uint8).tobytes()

        elif pattern == TelemetryPattern.ALTERNATING:
            # 0xAA = 10101010b in binary
            raw_data = bytes([0xAA] * length_bytes)

        elif pattern == TelemetryPattern.COUNTER:
            # Modular counter 0x00, 0x01, ..., 0xFF, 0x00, ...
            raw_data = bytes(i % 256 for i in range(length_bytes))

        elif pattern == TelemetryPattern.ALL_ZEROS:
            raw_data = bytes(length_bytes)

        elif pattern == TelemetryPattern.ALL_ONES:
            raw_data = bytes([0xFF] * length_bytes)

        else:
            raise RuntimeError(f"Unhandled pattern: {pattern}")

        return TelemetryPayload(raw_data)
