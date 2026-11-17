"""
Ground Truth Tracking for Space Communication Channel.

Maintains exact bookkeeping of transmitted bits vs altered bits for
accurate empirical BER and FER calculations.

SRS References:
- Feature 2: FR-08 (Record transmitted and altered bits)
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class FrameGroundTruth:
    """Exact audit data for a single transmitted frame."""
    frame_index: int
    sequence_number: int
    total_bits: int
    injected_bit_errors: int
    error_bit_indices: List[int] = field(default_factory=list)

    @property
    def is_corrupted(self) -> bool:
        """True if any bit in the frame was flipped by the channel."""
        return self.injected_bit_errors > 0
