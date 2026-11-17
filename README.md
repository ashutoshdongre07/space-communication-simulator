# Error Detection in Space Communication System

A software-based digital telemetry simulation modeling error detection and forward-error-correction (FEC) in space-to-ground communication links.

Grounded in **CCSDS 131.0-B-5** (TM Synchronization and Channel Coding) and **NASA SP-8000** space communication standards.

---

## 1. Project Objectives
* **Telemetry Modeling:** Generate structured spacecraft telemetry frames with headers, identifiers, and control fields.
* **Space Channel Modeling:** Simulate deep-space physical degradation (cosmic noise, stochastic bit flips, and localized burst errors).
* **CRC-Based Error Detection:** Compute, append, and verify cyclic redundancy checks (CRC-16-CCITT, CRC-32) at the ground receiver.
* **Performance Analysis:** Quantitatively evaluate empirical Bit Error Rate (BER) and Frame Error Rate (FER) across varying channel conditions.
* **FEC Coding Comparison (Optional):** Compare uncoded baseline transmission with space-grade forward-error-correction codes (e.g. Reed-Solomon, Convolutional/Viterbi).
* **Reporting & Visualization:** Export structured experiment traces (CSV/JSON) and render BER vs. SNR waterfall curves.

---

## 2. System Architecture

The system follows a strict 4-tier layered architecture:
1. **Presentation Layer:** Command-Line Interface (`cli.py`) and Interactive Visual Dashboard (`dashboard.py`).
2. **Orchestration Layer:** Simulation Engine (`engine.py`), Configuration Manager (`config.py`), and Metrics Calculator (`metrics.py`).
3. **Core Domain Layer:**
   - Telemetry & Frame Formatting (`core/telemetry.py`, `core/frame.py`)
   - Error Detection Engine (`error_detection/crc_engine.py`)
   - Channel & Noise Models (`channel/random_error.py`, `channel/burst_error.py`)
   - Channel Coding Codecs (`coding/uncoded.py`, `coding/reed_solomon.py`, `coding/convolutional.py`)
4. **Persistence & Reporting Layer:** CSV frame logger, JSON report serializer (`exporter.py`), and matplotlib curve generator (`plotter.py`).

---

## 3. Directory Layout

```text
Space Communication Simulator/
├── config/                 # Default parameter profiles & CCSDS settings
├── docs/                   # Academic citations, references, and user guide
├── outputs/                # Simulation run outputs (logs, reports, plots)
│   ├── logs/               # Detailed per-frame CSV logs
│   ├── plots/              # Saved graphical figures (.png)
│   └── reports/            # Summary JSON metrics
├── src/                    # Application source code
│   ├── core/               # Telemetry and frame packaging
│   ├── channel/            # Space noise, random bit flips, burst models
│   ├── coding/             # Uncoded baseline & optional FEC codecs
│   ├── error_detection/    # CRC calculators & syndrome evaluators
│   ├── reporting/          # CSV/JSON exporters and waterfall plotters
│   ├── simulation/         # Pipeline runner and metric statistics
│   └── ui/                 # CLI and visual dashboard
├── tests/                  # Verification test suite (TC-01 to TC-05)
├── requirements.txt        # Python package dependencies
├── .gitignore              # Git ignore rules
└── README.md               # Project documentation
```

---

## 4. Installation & Setup

### Prerequisites
* Python 3.10 or higher
* Recommended: Virtual environment (`venv`)

### Installation
```powershell
# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install required dependencies
pip install -r requirements.txt
```

---

## 5. Verification Test Suite

The verification suite validates compliance with SRS Section 3.4 & 7.2:
* **TC-01:** Frame Generation & CRC Validation (`test_tc01_frame_crc.py`)
* **TC-02:** Random and Burst Error Injection (`test_tc02_channel_noise.py`)
* **TC-03:** Corrupted-Frame Detection (`test_tc03_error_detection.py`)
* **TC-04:** Coding Comparison (`test_tc04_coding_comparison.py`)
* **TC-05:** BER/FER Calculation & Export (`test_tc05_metrics_export.py`)

Run tests using pytest:
```bash
pytest tests/ -v
```
