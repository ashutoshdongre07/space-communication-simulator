"""
Space Communication Simulator - Main Entry Point.

Supports:
- Command-Line Interface (CLI) execution for batch runs & headless automation
- Graphical Streamlit Dashboard launcher
"""

import sys
import argparse
import subprocess

from src.simulation.config import SimulationConfig
from src.simulation.engine import SimulationEngine


def run_cli(args):
    """Run simulation directly via terminal interface."""
    config = SimulationConfig(
        num_frames=args.frames,
        payload_size_bytes=args.payload_size,
        channel_mode=args.channel_mode,
        target_ber=args.ber,
        burst_probability=args.burst_prob,
        burst_length=args.burst_len,
        crc_algorithm=args.crc,
        random_seed=args.seed,
    )

    print("\n=======================================================")
    print("       SPACE COMMUNICATION SIMULATOR - CLI RUNNER       ")
    print("=======================================================")
    print(f"Frames to Transmit : {config.num_frames}")
    print(f"Payload Size (B)   : {config.payload_size_bytes}")
    print(f"Channel Mode       : {config.channel_mode.upper()}")
    print(f"Target BER         : {config.target_ber}")
    print(f"CRC Algorithm      : {config.crc_algorithm}")
    print(f"Random Seed        : {config.random_seed}")
    print("-------------------------------------------------------")
    print("Transmitting frames across simulated space link...")

    engine = SimulationEngine(config)
    result = engine.run()
    m = result.metrics

    print("Transmission complete!\n")
    print("------------------- RESULTS SUMMARY -------------------")
    print(f"Total Bits Transmitted : {m.total_transmitted_bits:,}")
    print(f"Injected Bit Errors    : {m.actual_corrupted_bits:,}")
    print(f"Observed Channel BER   : {m.actual_ber:.6f}")
    print(f"Actual Corrupted Frames: {m.actual_corrupted_frames} / {m.total_frames}")
    print(f"Observed FER           : {m.actual_fer * 100:.2f}%")
    print(f"Valid Frames (Pass CRC): {m.valid_frames}")
    print(f"Detected Corrupt Frames: {m.detected_corrupt_frames}")
    print(f"Undetected Frame Errors: {m.undetected_error_frames}")
    print(f"Detection Accuracy     : {m.detection_accuracy:.2f}%")
    print(f"Runtime Duration       : {m.elapsed_time_seconds:.4f}s")
    print("=======================================================\n")

    if args.output:
        df = result.to_dataframe()
        df.to_csv(args.output, index=False)
        print(f"Full results trace saved to: {args.output}\n")


def launch_dashboard():
    """Launch Streamlit web dashboard."""
    print("Launching Space Communication Simulator Dashboard...")
    subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"])


def main():
    parser = argparse.ArgumentParser(description="Space Communication Telemetry Link Simulator")
    parser.add_argument("--cli", action="store_true", help="Run in headless Command-Line mode")
    parser.add_argument("--frames", type=int, default=100, help="Number of telemetry frames (default: 100)")
    parser.add_argument("--payload-size", type=int, default=64, help="Payload size in bytes (default: 64)")
    parser.add_argument("--channel-mode", type=str, default="random", choices=["none", "random", "burst", "hybrid"])
    parser.add_argument("--ber", type=float, default=0.005, help="Target channel Bit Error Rate (default: 0.005)")
    parser.add_argument("--burst-prob", type=float, default=0.1, help="Burst occurrence probability (default: 0.1)")
    parser.add_argument("--burst-len", type=int, default=16, help="Burst length in bits (default: 16)")
    parser.add_argument("--crc", type=str, default="CRC-16-CCITT", choices=["CRC-16-CCITT", "CRC-32"])
    parser.add_argument("--seed", type=int, default=42, help="PRNG integer seed (default: 42)")
    parser.add_argument("--output", type=str, default=None, help="Save frame CSV trace to path")

    args = parser.parse_args()

    if args.cli:
        run_cli(args)
    else:
        launch_dashboard()


if __name__ == "__main__":
    main()
