"""
Simulation Orchestration Engine.

Integrates Telemetry Generation, Frame Formation, CRC Engine, Space Channel,
Receiver Verification, and Metrics Calculation into an end-to-end workflow.

SRS References:
- Feature 1: FR-01, FR-02, FR-03, FR-04
- Feature 2: FR-05, FR-06, FR-07, FR-08, FR-09
- Feature 3: FR-10, FR-11, FR-12, FR-13, FR-14
- Feature 5: FR-20, FR-21
"""

import time
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Callable
import pandas as pd

from src.core.telemetry import TelemetryGenerator, TelemetryPattern
from src.core.frame import TelemetryFrame, FrameStatus
from src.core.receiver import GroundStationReceiver, ReceiverFrameAudit
from src.error_detection.crc_engine import CRCEngine
from src.channel.channel_model import SpaceChannel, ChannelErrorMode
from src.channel.ground_truth import FrameGroundTruth
from src.simulation.config import SimulationConfig
from src.simulation.metrics import SimulationMetrics, MetricsCalculator


@dataclass
class SimulationResult:
    """Consolidated outcome of a completed simulation run."""
    config: SimulationConfig
    metrics: SimulationMetrics
    frame_records: List[Dict[str, Any]]

    def to_dataframe(self) -> pd.DataFrame:
        """Convert per-frame audit logs into a Pandas DataFrame."""
        return pd.DataFrame(self.frame_records)


class SimulationEngine:
    """
    Master simulation orchestrator coordinating end-to-end telemetry link execution.
    """

    def __init__(self, config: Optional[SimulationConfig] = None):
        self.config = config if config is not None else SimulationConfig()
        self.config.validate()

    def run(
        self,
        progress_callback: Optional[Callable[[int, int, Dict[str, Any]], None]] = None,
    ) -> SimulationResult:
        """
        Execute the end-to-end space telemetry communication pipeline.

        Workflow:
        1. Initialize generators, CRC engine, space channel, and receiver.
        2. For each frame in 0..N-1:
           a. Generate synthetic telemetry payload.
           b. Form TelemetryFrame with Sequence Counter and Header.
           c. Compute and append CRC footer.
           d. Transmit frame through space channel (inject stochastic/burst noise).
           e. Ingest corrupted frame at ground station receiver.
           f. Recompute CRC, test syndrome, mark VALID or ERROR-DETECTED.
           g. Audit ground-truth vs receiver status.
        3. Compute aggregated metrics and compile tabular audit dataset.

        Returns:
            SimulationResult containing configuration, metrics, and frame records.
        """
        start_time = time.perf_counter()
        cfg = self.config

        # Initialize modules
        telemetry_gen = TelemetryGenerator(seed=cfg.random_seed)
        crc_engine = CRCEngine(params=cfg.crc_algorithm)
        receiver = GroundStationReceiver(crc_engine=crc_engine)

        channel_seed = (cfg.random_seed + 1000) if cfg.random_seed is not None else None
        channel = SpaceChannel(
            mode=cfg.channel_mode,
            ber=cfg.target_ber,
            burst_probability=cfg.burst_probability,
            burst_length=cfg.burst_length,
            seed=channel_seed,
        )

        ground_truths: List[FrameGroundTruth] = []
        receiver_audits: List[ReceiverFrameAudit] = []
        frame_records: List[Dict[str, Any]] = []

        total_frames = cfg.num_frames

        for i in range(total_frames):
            seq_num = i % 65536

            # 1. Generate payload
            payload = telemetry_gen.generate(
                length_bytes=cfg.payload_size_bytes,
                pattern=TelemetryPattern.RANDOM,
            )

            # 2. Form frame and attach CRC
            tx_frame = TelemetryFrame(sequence_number=seq_num, payload=payload)
            tx_frame.attach_crc(crc_engine)

            # 3. Transmit through space channel
            rx_bytes, gt = channel.transmit(frame=tx_frame, frame_index=i)
            ground_truths.append(gt)

            # 4. Receiver processing & CRC verification
            rx_audit = receiver.process_frame(raw_bytes=rx_bytes, frame_index=i)
            receiver_audits.append(rx_audit)

            # 5. Compile frame diagnostic record
            is_undetected_error = (gt.is_corrupted and rx_audit.status == FrameStatus.VALID)

            record = {
                "Frame_ID": i,
                "Sequence_Num": seq_num,
                "Total_Bits": gt.total_bits,
                "Injected_Bit_Errors": gt.injected_bit_errors,
                "Actual_Corrupted": "YES" if gt.is_corrupted else "NO",
                "Receiver_Status": rx_audit.status.value,
                "Received_CRC": f"0x{rx_audit.received_crc:04X}" if crc_engine.width == 16 else f"0x{rx_audit.received_crc:08X}",
                "Computed_CRC": f"0x{rx_audit.computed_crc:04X}" if crc_engine.width == 16 else f"0x{rx_audit.computed_crc:08X}",
                "CRC_Match": "PASS" if rx_audit.is_valid else "FAIL",
                "Undetected_Error": "ALERT!" if is_undetected_error else "NO",
            }
            frame_records.append(record)

            # Periodic progress callback
            if progress_callback and (i % 20 == 0 or i == total_frames - 1):
                interim_stats = {
                    "frames_done": i + 1,
                    "total_frames": total_frames,
                    "injected_errors": gt.injected_bit_errors,
                }
                progress_callback(i + 1, total_frames, interim_stats)

        elapsed = time.perf_counter() - start_time

        # Calculate consolidated metrics
        metrics = MetricsCalculator.calculate(
            ground_truth_list=ground_truths,
            receiver_audits=receiver_audits,
            elapsed_time=elapsed,
        )

        return SimulationResult(
            config=cfg,
            metrics=metrics,
            frame_records=frame_records,
        )
