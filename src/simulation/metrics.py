"""
Space Communication Metrics Calculator.

Computes exact statistical indicators:
- Transmitted & altered bits
- Bit Error Rate (BER)
- Frame Error Rate (FER)
- Detected vs. Undetected corrupted frames
- Detection accuracy percentage

SRS References:
- Feature 2: FR-08, FR-09
- Feature 3: FR-13, FR-14
- Feature 5: FR-20
- Verification Test: TC-05
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any
import numpy as np

from src.core.frame import FrameStatus
from src.core.receiver import ReceiverFrameAudit
from src.channel.ground_truth import FrameGroundTruth


@dataclass
class SimulationMetrics:
    """Consolidated performance indicators for an entire simulation run."""
    total_frames: int
    total_transmitted_bits: int
    actual_corrupted_bits: int
    actual_ber: float

    actual_corrupted_frames: int
    actual_fer: float

    valid_frames: int
    detected_corrupt_frames: int
    undetected_error_frames: int
    false_alarm_frames: int
    detection_accuracy: float

    elapsed_time_seconds: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary for JSON serialization & dashboard display."""
        return {
            "total_frames": self.total_frames,
            "total_transmitted_bits": self.total_transmitted_bits,
            "actual_corrupted_bits": self.actual_corrupted_bits,
            "actual_ber": self.actual_ber,
            "actual_corrupted_frames": self.actual_corrupted_frames,
            "actual_fer": self.actual_fer,
            "valid_frames": self.valid_frames,
            "detected_corrupt_frames": self.detected_corrupt_frames,
            "undetected_error_frames": self.undetected_error_frames,
            "false_alarm_frames": self.false_alarm_frames,
            "detection_accuracy_pct": round(self.detection_accuracy, 3),
            "elapsed_time_seconds": round(self.elapsed_time_seconds, 4),
        }


class MetricsCalculator:
    """Calculates ground-truth vs receiver observation metrics."""

    @staticmethod
    def calculate(
        ground_truth_list: List[FrameGroundTruth],
        receiver_audits: List[ReceiverFrameAudit],
        elapsed_time: float = 0.0,
    ) -> SimulationMetrics:
        """
        Compute consolidated metrics from paired ground-truth and receiver audit logs.
        """
        total_frames = len(ground_truth_list)
        if total_frames == 0:
            return SimulationMetrics(
                total_frames=0,
                total_transmitted_bits=0,
                actual_corrupted_bits=0,
                actual_ber=0.0,
                actual_corrupted_frames=0,
                actual_fer=0.0,
                valid_frames=0,
                detected_corrupt_frames=0,
                undetected_error_frames=0,
                false_alarm_frames=0,
                detection_accuracy=100.0,
                elapsed_time_seconds=elapsed_time,
            )

        total_transmitted_bits = sum(gt.total_bits for gt in ground_truth_list)
        actual_corrupted_bits = sum(gt.injected_bit_errors for gt in ground_truth_list)

        actual_ber = (actual_corrupted_bits / total_transmitted_bits) if total_transmitted_bits > 0 else 0.0

        actual_corrupted_frames = 0
        valid_frames = 0
        detected_corrupt_frames = 0
        undetected_error_frames = 0
        false_alarm_frames = 0

        for gt, rx in zip(ground_truth_list, receiver_audits):
            frame_had_errors = gt.is_corrupted
            frame_flagged_error = (rx.status == FrameStatus.ERROR_DETECTED)

            if frame_had_errors:
                actual_corrupted_frames += 1

            if rx.status == FrameStatus.VALID:
                valid_frames += 1
            else:
                detected_corrupt_frames += 1

            # Check detection fidelity
            if frame_had_errors and not frame_flagged_error:
                # Frame had flipped bits, but receiver labeled it VALID
                undetected_error_frames += 1
            elif not frame_had_errors and frame_flagged_error:
                # Frame was completely clean, but receiver labeled it ERROR_DETECTED
                false_alarm_frames += 1

        actual_fer = (actual_corrupted_frames / total_frames) if total_frames > 0 else 0.0

        if actual_corrupted_frames > 0:
            # Fraction of corrupted frames that were successfully detected
            detected_actual = actual_corrupted_frames - undetected_error_frames
            detection_accuracy = (detected_actual / actual_corrupted_frames) * 100.0
        else:
            detection_accuracy = 100.0

        return SimulationMetrics(
            total_frames=total_frames,
            total_transmitted_bits=total_transmitted_bits,
            actual_corrupted_bits=actual_corrupted_bits,
            actual_ber=actual_ber,
            actual_corrupted_frames=actual_corrupted_frames,
            actual_fer=actual_fer,
            valid_frames=valid_frames,
            detected_corrupt_frames=detected_corrupt_frames,
            undetected_error_frames=undetected_error_frames,
            false_alarm_frames=false_alarm_frames,
            detection_accuracy=detection_accuracy,
            elapsed_time_seconds=elapsed_time,
        )
