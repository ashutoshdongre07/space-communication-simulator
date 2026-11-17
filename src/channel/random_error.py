"""
Random Bit Error Generator.

Simulates stochastic deep-space cosmic noise via independent bit inversions
(Binary Symmetric Channel / AWGN equivalent).

SRS References:
- Feature 2: FR-05 (Configurable BER), FR-06 (Random bit flips)
- Verification Test: TC-02
"""

from typing import Tuple, List, Optional
import numpy as np


class RandomBitFlipper:
    """Injects independent, identically distributed (i.i.d.) random bit flips."""

    def __init__(self, error_probability: float = 0.0, rng: Optional[np.random.Generator] = None):
        """
        Args:
            error_probability: Target Bit Error Rate (0.0 to 1.0).
            rng: Optional NumPy random generator for deterministic seeds.
        """
        self.set_error_probability(error_probability)
        self.rng = rng if rng is not None else np.random.default_rng()

    def set_error_probability(self, prob: float) -> None:
        if not isinstance(prob, (int, float)):
            raise TypeError(f"error_probability must be float, got {type(prob).__name__}")
        if not (0.0 <= prob <= 1.0):
            raise ValueError(f"error_probability must be between 0.0 and 1.0, got {prob}")
        self.error_probability = float(prob)

    def corrupt_bits(self, bits: np.ndarray) -> Tuple[np.ndarray, int, List[int]]:
        """
        Apply random bit flips to a bit array.

        Returns:
            Tuple of:
            - corrupted_bits: 1D np.ndarray of uint8 (0 or 1)
            - num_errors: Count of flipped bits
            - error_indices: List of inverted bit indices
        """
        if self.error_probability == 0.0 or len(bits) == 0:
            return bits.copy(), 0, []

        flip_mask = self.rng.random(size=len(bits)) < self.error_probability
        corrupted_bits = bits ^ flip_mask.astype(np.uint8)

        error_indices = np.where(flip_mask)[0].tolist()
        num_errors = len(error_indices)

        return corrupted_bits, num_errors, error_indices
