"""
Simulation Configuration Schema.

Encapsulates all parameters governing an end-to-end space telemetry simulation.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class SimulationConfig:
    """Strongly-typed parameters for a simulation run."""
    num_frames: int = 100
    payload_size_bytes: int = 64
    channel_mode: str = "random"         # 'none', 'random', 'burst', 'hybrid'
    target_ber: float = 0.001            # Channel Bit Error Rate
    burst_probability: float = 0.05      # Probability of burst occurrence per frame
    burst_length: int = 16               # Length of burst in bits
    crc_algorithm: str = "CRC-16-CCITT"  # 'CRC-16-CCITT' or 'CRC-32'
    random_seed: Optional[int] = 42      # Integer seed for deterministic reproduction

    def validate(self) -> None:
        """Sanitize and validate configuration values."""
        if self.num_frames < 1:
            raise ValueError(f"num_frames must be >= 1, got {self.num_frames}")
        if self.payload_size_bytes < 1 or self.payload_size_bytes > 65536:
            raise ValueError(f"payload_size_bytes must be within [1, 65536], got {self.payload_size_bytes}")
        if not (0.0 <= self.target_ber <= 1.0):
            raise ValueError(f"target_ber must be in range [0.0, 1.0], got {self.target_ber}")
        if not (0.0 <= self.burst_probability <= 1.0):
            raise ValueError(f"burst_probability must be in range [0.0, 1.0], got {self.burst_probability}")
        if self.burst_length < 1:
            raise ValueError(f"burst_length must be >= 1, got {self.burst_length}")
        if self.channel_mode.lower() not in ("none", "random", "burst", "hybrid"):
            raise ValueError(f"Invalid channel_mode: {self.channel_mode}")
        if self.crc_algorithm not in ("CRC-16-CCITT", "CRC-16", "CRC-32", "CRC-32-IEEE"):
            raise ValueError(f"Unsupported crc_algorithm: {self.crc_algorithm}")
