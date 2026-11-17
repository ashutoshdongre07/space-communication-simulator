"""
Burst Error Generator.

Simulates concentrated space disturbances (solar flares, ionospheric interference,
or transient RF interference) affecting contiguous bit blocks.

SRS References:
- Feature 2: FR-07 (Burst-error scenarios)
- Verification Test: TC-02
"""

from typing import Tuple, List, Optional
import numpy as np


class BurstErrorGenerator:
    """Injects localized burst errors of configurable length and probability."""

    def __init__(
        self,
        burst_probability: float = 0.0,
        burst_length: int = 8,
        rng: Optional[np.random.Generator] = None,
    ):
        """
        Args:
            burst_probability: Probability that a transmitted frame experiences a burst (0.0 to 1.0).
            burst_length: Number of consecutive bits subject to the burst disturbance.
            rng: Optional NumPy random generator.
        """
        self.set_parameters(burst_probability, burst_length)
        self.rng = rng if rng is not None else np.random.default_rng()

    def set_parameters(self, burst_probability: float, burst_length: int) -> None:
        if not (0.0 <= burst_probability <= 1.0):
            raise ValueError(f"burst_probability must be between 0.0 and 1.0, got {burst_probability}")
        if burst_length < 1:
            raise ValueError(f"burst_length must be >= 1, got {burst_length}")
        self.burst_probability = float(burst_probability)
        self.burst_length = int(burst_length)

    def corrupt_bits(self, bits: np.ndarray) -> Tuple[np.ndarray, int, List[int]]:
        """
        Inject burst noise into a bit array if burst event triggers.

        Returns:
            Tuple of:
            - corrupted_bits: 1D np.ndarray of uint8
            - num_errors: Count of altered bits
            - error_indices: List of inverted bit indices
        """
        if self.burst_probability == 0.0 or len(bits) == 0:
            return bits.copy(), 0, []

        # Check if burst occurs in this frame
        if self.rng.random() >= self.burst_probability:
            return bits.copy(), 0, []

        corrupted = bits.copy()
        num_bits = len(bits)

        # Select random start position for burst
        max_start = max(0, num_bits - self.burst_length)
        start_idx = int(self.rng.integers(0, max_start + 1)) if max_start > 0 else 0
        end_idx = min(num_bits, start_idx + self.burst_length)

        # Corrupt bits in the burst window (flip bits with 50% to 100% chance, ensuring at least one flip)
        error_indices = []
        burst_flips = self.rng.random(size=(end_idx - start_idx)) < 0.8
        # Ensure at least the first bit in burst flips
        burst_flips[0] = True

        for i, flip in enumerate(burst_flips):
            if flip:
                bit_idx = start_idx + i
                corrupted[bit_idx] ^= 1
                error_indices.append(bit_idx)

        return corrupted, len(error_indices), error_indices
