"""
Space Communication Channel Orchestrator.

Combines random bit errors and burst errors into a realistic physical space channel.

SRS References:
- Feature 2: FR-05, FR-06, FR-07, FR-08, FR-09
- Verification Test: TC-02
"""

import enum
from typing import Tuple, Optional
import numpy as np

from src.core.frame import TelemetryFrame
from src.channel.random_error import RandomBitFlipper
from src.channel.burst_error import BurstErrorGenerator
from src.channel.ground_truth import FrameGroundTruth


class ChannelErrorMode(str, enum.Enum):
    """Channel noise profile."""
    NONE = "none"             # Ideal error-free channel
    RANDOM = "random"         # Independent random bit flips
    BURST = "burst"           # Contiguous burst errors
    HYBRID = "hybrid"         # Random cosmic noise + periodic bursts


class SpaceChannel:
    """
    Simulates physical space transmission channel.
    """

    def __init__(
        self,
        mode: ChannelErrorMode = ChannelErrorMode.RANDOM,
        ber: float = 0.001,
        burst_probability: float = 0.05,
        burst_length: int = 16,
        seed: Optional[int] = None,
    ):
        self.mode = ChannelErrorMode(mode) if isinstance(mode, str) else mode
        self.rng = np.random.default_rng(seed)

        self.random_flipper = RandomBitFlipper(error_probability=ber, rng=self.rng)
        self.burst_generator = BurstErrorGenerator(
            burst_probability=burst_probability,
            burst_length=burst_length,
            rng=self.rng,
        )

    def transmit(
        self,
        frame: TelemetryFrame,
        frame_index: int = 0,
    ) -> Tuple[bytes, FrameGroundTruth]:
        """
        Transmit a telemetry frame through the space channel, injecting errors
        according to the configured noise mode.

        Args:
            frame: Outgoing TelemetryFrame with attached CRC.
            frame_index: Index of frame within transmission stream.

        Returns:
            Tuple of:
            - corrupted_frame_bytes: Raw bytes received at the ground station.
            - ground_truth: FrameGroundTruth record with exact bit audit.
        """
        raw_bytes = frame.to_bytes()
        bits = np.unpackbits(np.frombuffer(raw_bytes, dtype=np.uint8))
        total_bits = len(bits)

        altered_indices = set()
        corrupted_bits = bits.copy()

        if self.mode in (ChannelErrorMode.RANDOM, ChannelErrorMode.HYBRID):
            corrupted_bits, _, rand_indices = self.random_flipper.corrupt_bits(corrupted_bits)
            altered_indices.update(rand_indices)

        if self.mode in (ChannelErrorMode.BURST, ChannelErrorMode.HYBRID):
            corrupted_bits, _, burst_indices = self.burst_generator.corrupt_bits(corrupted_bits)
            altered_indices.update(burst_indices)

        # Pack corrupted bits back to bytes
        corrupted_bytes = np.packbits(corrupted_bits).tobytes()

        # Compile ground truth record
        ground_truth = FrameGroundTruth(
            frame_index=frame_index,
            sequence_number=frame.sequence_number,
            total_bits=total_bits,
            injected_bit_errors=len(altered_indices),
            error_bit_indices=sorted(altered_indices),
        )

        return corrupted_bytes, ground_truth
