"""
Streamlit Web Dashboard for Space Communication Telemetry Simulation.

Professional Aerospace Mission Control Console.
Compliant with CCSDS 131.0-B-5 Telemetry Synchronization and Channel Standards.

Supports:
- Dual High-Contrast Themes: Light Mode (Mission Control) & Dark Mode (Deep Space Night)
- Full Mission Telemetry Configuration (Frames, Payload, CRC-16/32, Channel Noise, Seeds)
- Real-time Interactive Execution with Progress Tracking
- Aerospace Mission Metric Cards (BER, FER, Valid Frames, Corrupted Frames, Detection Accuracy)
- Plotly Visualizations (Integrity Donut, Per-Frame Injected Errors, Theoretical BPSK Waterfall)
- Searchable & Filterable Telemetry Frame Audit Table
- Direct CSV Data Export
"""

import math
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from src.simulation.config import SimulationConfig
from src.simulation.engine import SimulationEngine, SimulationResult
from src.core.frame import FrameStatus

# Page configuration
st.set_page_config(
    page_title="Space Communication Mission Control",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------
# Theme Management & Palette Definition
# ---------------------------------------------------------
if "theme_mode" not in st.session_state:
    st.session_state["theme_mode"] = "Light Mode ☀️"

# Sidebar Theme Selector (Preserved toggle with persistence)
theme_choice = st.sidebar.radio(
    "🌓 Console Theme",
    ["Light Mode ☀️", "Dark Mode 🌙"],
    index=0 if st.session_state["theme_mode"] == "Light Mode ☀️" else 1,
    help="Toggle between Light Mission Control and Dark Deep Space themes.",
)
st.session_state["theme_mode"] = theme_choice

is_dark = (theme_choice == "Dark Mode 🌙")

if is_dark:
    # DARK MODE PALETTE (Refined Deep Space Theme)
    c_bg = "#111827"           # Main background
    c_sidebar = "#172033"      # Sidebar background
    c_card = "#1F2937"         # Card background
    c_card_inner = "#182234"   # Secondary inner card
    c_text_primary = "#F9FAFB" # Primary text (white)
    c_text_muted = "#A7B4C8"   # Secondary text (muted grey-blue)
    c_accent = "#60A5FA"       # Accent blue
    c_accent_hover = "#3B82F6" # Accent blue hover
    c_success = "#34D399"      # Success green
    c_warning = "#FBBF24"      # Warning amber
    c_error = "#F87171"        # Error red
    c_border = "#374151"       # Borders
    c_grid = "#2B3545"         # Chart grid lines
    plotly_template = "plotly_dark"
    badge_bg = "rgba(52, 211, 153, 0.15)"
    badge_border = "#059669"
else:
    # LIGHT MODE PALETTE (High-Contrast Professional Aerospace Theme)
    c_bg = "#F4F7FB"           # Main background
    c_sidebar = "#E8EEF6"      # Sidebar background
    c_card = "#FFFFFF"         # Card background
    c_card_inner = "#F8FAFC"   # Secondary inner card
    c_text_primary = "#172B4D" # Primary text (dark navy)
    c_text_muted = "#53657D"   # Secondary text (readable slate grey)
    c_accent = "#1769AA"       # Accent blue
    c_accent_hover = "#135284" # Accent blue hover
    c_success = "#16866A"      # Success green
    c_warning = "#B45309"      # Warning amber
    c_error = "#C62828"        # Error red
    c_border = "#CBD5E1"       # Borders
    c_grid = "#E2E8F0"         # Chart grid lines
    plotly_template = "plotly_white"
    badge_bg = "#E6F4EA"
    badge_border = "#34A853"

# ---------------------------------------------------------
# Dynamic High-Contrast CSS Injection
# ---------------------------------------------------------
custom_css = f"""
<style>
    /* Global Base */
    .stApp {{
        background-color: {c_bg} !important;
        color: {c_text_primary} !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    }}

    /* Global Headings & Typography */
    h1, h2, h3, h4, h5, h6, .stMarkdown p {{
        color: {c_text_primary} !important;
    }}
    .stMarkdown p {{
        font-size: 0.95rem;
        line-height: 1.5;
    }}

    /* Sidebar Container */
    [data-testid="stSidebar"] {{
        background-color: {c_sidebar} !important;
        border-right: 1px solid {c_border} !important;
    }}
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {{
        color: {c_text_primary} !important;
        font-weight: 700 !important;
        letter-spacing: -0.01em;
    }}
    [data-testid="stSidebar"] label, [data-testid="stSidebar"] .stMarkdown p {{
        color: {c_text_primary} !important;
        font-weight: 600 !important;
        font-size: 0.88rem !important;
    }}
    [data-testid="stSidebar"] .stSlider span, [data-testid="stSidebar"] .stSelectbox span {{
        color: {c_text_muted} !important;
        font-weight: 500 !important;
    }}

    /* Primary Launch Button */
    .stButton > button[kind="primary"] {{
        background-color: {c_accent} !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 6px !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
        letter-spacing: 0.03em !important;
        padding: 0.55rem 1rem !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.12) !important;
        transition: all 0.15s ease-in-out !important;
    }}
    .stButton > button[kind="primary"]:hover {{
        background-color: {c_accent_hover} !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2) !important;
        transform: translateY(-1px) !important;
    }}

    /* Secondary Download Button */
    .stDownloadButton > button {{
        background-color: {c_card} !important;
        color: {c_accent} !important;
        border: 1.5px solid {c_accent} !important;
        border-radius: 6px !important;
        font-weight: 700 !important;
        font-size: 0.9rem !important;
        padding: 0.5rem 1rem !important;
        transition: all 0.15s ease-in-out !important;
    }}
    .stDownloadButton > button:hover {{
        background-color: {c_accent} !important;
        color: #FFFFFF !important;
    }}

    /* Mission Control Metric Cards */
    .mission-card {{
        background-color: {c_card};
        border: 1px solid {c_border};
        border-radius: 8px;
        padding: 18px 20px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        margin-bottom: 14px;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }}
    .mission-card-tag {{
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: {c_text_muted};
        margin-bottom: 6px;
    }}
    .mission-card-value {{
        font-size: 2.1rem;
        font-weight: 800;
        line-height: 1.1;
        letter-spacing: -0.02em;
        margin-bottom: 6px;
    }}
    .mission-card-meta {{
        font-size: 0.82rem;
        font-weight: 500;
        color: {c_text_muted};
    }}

    /* Status Banner */
    .status-banner {{
        background-color: {c_card};
        border: 1px solid {c_border};
        border-left: 4px solid {c_accent};
        border-radius: 6px;
        padding: 12px 18px;
        margin-top: 10px;
        margin-bottom: 22px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        font-size: 0.9rem;
        color: {c_text_primary};
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }}

    /* Tabs Component */
    .stTabs [data-baseweb="tab-list"] {{
        background-color: transparent !important;
        border-bottom: 2px solid {c_border} !important;
        gap: 6px !important;
    }}
    .stTabs [data-baseweb="tab"] {{
        background-color: {c_card} !important;
        border: 1px solid {c_border} !important;
        border-bottom: none !important;
        border-radius: 6px 6px 0 0 !important;
        padding: 10px 20px !important;
        color: {c_text_muted} !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
    }}
    .stTabs [aria-selected="true"] {{
        background-color: {c_card} !important;
        color: {c_accent} !important;
        border-top: 3px solid {c_accent} !important;
        font-weight: 700 !important;
    }}

    /* Reference & Info Cards */
    .info-box {{
        background-color: {c_card};
        border: 1px solid {c_border};
        border-radius: 8px;
        padding: 18px 22px;
        margin-bottom: 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }}
    .info-box h4 {{
        margin-top: 0;
        color: {c_accent} !important;
        font-size: 1.05rem;
        font-weight: 700;
        display: flex;
        align-items: center;
        gap: 8px;
    }}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# ---------------------------------------------------------
# Sidebar: Mission Configuration
# ---------------------------------------------------------
st.sidebar.markdown(
    f"""
    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 4px;">
        <span style="font-size: 1.8rem;">🛰️</span>
        <div>
            <div style="font-size: 1.15rem; font-weight: 800; color: {c_text_primary}; letter-spacing: -0.01em;">MISSION CONTROL</div>
            <div style="font-size: 0.75rem; font-weight: 600; color: {c_text_muted}; text-transform: uppercase; letter-spacing: 0.05em;">Telemetry Uplink / Downlink</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.sidebar.divider()

st.sidebar.markdown(
    f"<div style='font-size: 0.78rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: {c_accent}; margin-bottom: 8px;'>1. Telemetry Link Profile</div>",
    unsafe_allow_html=True,
)

num_frames = st.sidebar.slider(
    "Total Telemetry Frames",
    min_value=10,
    max_value=1000,
    value=150,
    step=10,
    help="Total communication frames transmitted across the space telemetry link.",
)

payload_size = st.sidebar.slider(
    "Subsystem Payload Length (Bytes)",
    min_value=8,
    max_value=256,
    value=64,
    step=8,
    help="Bytes of synthetic sensor data generated per telemetry frame.",
)

crc_choice = st.sidebar.selectbox(
    "Error Detection Polynomial",
    ["CRC-16-CCITT", "CRC-32"],
    index=0,
    help="CRC algorithm. CRC-16-CCITT (0x1021) is standard for CCSDS TM frames.",
)

st.sidebar.divider()
st.sidebar.markdown(
    f"<div style='font-size: 0.78rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: {c_accent}; margin-bottom: 8px;'>2. Channel Environment Physics</div>",
    unsafe_allow_html=True,
)

channel_mode = st.sidebar.selectbox(
    "Space Channel Disturbance Model",
    ["random", "burst", "hybrid", "none"],
    index=0,
    format_func=lambda x: {
        "random": "Cosmic Noise (Stochastic Bit Flips)",
        "burst": "Solar Flare (Burst Noise)",
        "hybrid": "Deep Space (Hybrid Cosmic + Burst)",
        "none": "Ideal Spacecraft Link (Noiseless)",
    }[x],
)

target_ber = 0.005
if channel_mode in ("random", "hybrid"):
    target_ber = st.sidebar.select_slider(
        "Target Channel Bit Error Rate (BER)",
        options=[0.0001, 0.0005, 0.001, 0.002, 0.005, 0.01, 0.02, 0.05],
        value=0.005,
        format_func=lambda x: f"{x:.4f} ({x*100:.2f}%)",
    )

burst_prob = 0.10
burst_len = 16
if channel_mode in ("burst", "hybrid"):
    burst_prob = st.sidebar.slider(
        "Burst Disturbance Probability",
        min_value=0.02,
        max_value=0.40,
        value=0.10,
        step=0.02,
        help="Probability that a frame encounters contiguous burst corruption.",
    )
    burst_len = st.sidebar.slider(
        "Burst Cluster Span (Bits)",
        min_value=4,
        max_value=48,
        value=16,
        step=4,
        help="Maximum contiguous bit block subjected to burst inversion.",
    )

st.sidebar.divider()
st.sidebar.markdown(
    f"<div style='font-size: 0.78rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: {c_accent}; margin-bottom: 8px;'>3. Deterministic Seeding</div>",
    unsafe_allow_html=True,
)

seed_input = st.sidebar.number_input(
    "PRNG Random Seed",
    value=42,
    min_value=0,
    max_value=999999,
    help="Guarantees 100% bit-exact reproducible simulation runs.",
)

st.sidebar.markdown("<div style='margin-top: 14px;'></div>", unsafe_allow_html=True)
run_button = st.sidebar.button("🚀 Transmit Telemetry Link", type="primary", width="stretch")

# ---------------------------------------------------------
# Simulation Execution Engine (Backend Orchestration)
# ---------------------------------------------------------
if run_button or "sim_result" not in st.session_state:
    config = SimulationConfig(
        num_frames=num_frames,
        payload_size_bytes=payload_size,
        channel_mode=channel_mode,
        target_ber=target_ber,
        burst_probability=burst_prob,
        burst_length=burst_len,
        crc_algorithm=crc_choice,
        random_seed=int(seed_input),
    )

    engine = SimulationEngine(config)
    progress_bar = st.progress(0, text="Establishing Downlink Carrier...")

    def update_progress(curr, total, stats):
        pct = int((curr / total) * 100)
        progress_bar.progress(pct, text=f"Transmitting Frame {curr} of {total} via space channel...")

    result = engine.run(progress_callback=update_progress)
    progress_bar.empty()
    st.session_state["sim_result"] = result

result: SimulationResult = st.session_state["sim_result"]
metrics = result.metrics
df_records = result.to_dataframe()

# ---------------------------------------------------------
# Main View: Header & Status Banner
# ---------------------------------------------------------
st.markdown(
    f"""
    <div style="display: flex; align-items: center; justify-content: space-between; border-bottom: 1.5px solid {c_border}; padding-bottom: 12px; margin-bottom: 16px;">
        <div>
            <div style="display: flex; align-items: center; gap: 10px;">
                <span style="font-size: 2.2rem;">🛰️</span>
                <div>
                    <h1 style="margin: 0; font-size: 1.9rem; font-weight: 800; color: {c_text_primary}; letter-spacing: -0.02em;">
                        SPACE TELEMETRY LINK SIMULATOR
                    </h1>
                    <div style="font-size: 0.9rem; font-weight: 600; color: {c_text_muted}; margin-top: 2px;">
                        CCSDS 131.0-B-5 Standard Synchronized Telemetry Link • Ground Station Receiver & Error Detection Engine
                    </div>
                </div>
            </div>
        </div>
        <div style="text-align: right;">
            <span style="background-color: {badge_bg}; color: {c_success}; border: 1.5px solid {badge_border}; padding: 6px 14px; border-radius: 20px; font-weight: 800; font-size: 0.8rem; letter-spacing: 0.06em; text-transform: uppercase;">
                ● LINK STATUS: NOMINAL
            </span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# Aerospace Mission Metric Cards
# ---------------------------------------------------------
m1, m2, m3, m4, m5 = st.columns(5)

with m1:
    st.markdown(
        f"""
        <div class="mission-card">
            <div class="mission-card-tag">Observed Channel BER</div>
            <div class="mission-card-value" style="color: {c_text_primary};">{metrics.actual_ber:.5f}</div>
            <div class="mission-card-meta">Target: <b>{result.config.target_ber:.4f}</b></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with m2:
    st.markdown(
        f"""
        <div class="mission-card">
            <div class="mission-card-tag">Frame Error Rate (FER)</div>
            <div class="mission-card-value" style="color: {c_warning if metrics.actual_fer > 0.05 else c_text_primary};">
                {metrics.actual_fer * 100:.2f}%
            </div>
            <div class="mission-card-meta">{metrics.actual_corrupted_frames} of {metrics.total_frames} Frames Altered</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with m3:
    st.markdown(
        f"""
        <div class="mission-card" style="border-top: 3px solid {c_success};">
            <div class="mission-card-tag">Valid Frames</div>
            <div class="mission-card-value" style="color: {c_success};">{metrics.valid_frames}</div>
            <div class="mission-card-meta">CRC Remainder Zero (PASS)</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with m4:
    st.markdown(
        f"""
        <div class="mission-card" style="border-top: 3px solid {c_error};">
            <div class="mission-card-tag">Corrupted Frames</div>
            <div class="mission-card-value" style="color: {c_error};">{metrics.detected_corrupt_frames}</div>
            <div class="mission-card-meta">Flagged ERROR-DETECTED</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with m5:
    st.markdown(
        f"""
        <div class="mission-card" style="border-top: 3px solid {c_accent};">
            <div class="mission-card-tag">Detection Accuracy</div>
            <div class="mission-card-value" style="color: {c_accent};">{metrics.detection_accuracy:.1f}%</div>
            <div class="mission-card-meta">{metrics.undetected_error_frames} Undetected Misses</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------
# Mission Control Telemetry Strip
# ---------------------------------------------------------
st.markdown(
    f"""
    <div class="status-banner">
        <div>
            📡 <b>TRANSMISSION AUDIT:</b>
            Transmitted <b>{metrics.total_transmitted_bits:,}</b> total bits across <b>{metrics.total_frames}</b> frames
            &nbsp;•&nbsp; Injected <b>{metrics.actual_corrupted_bits:,}</b> bit flips
            &nbsp;•&nbsp; Codec: <b>{result.config.crc_algorithm}</b>
            &nbsp;•&nbsp; Noise Model: <b>{result.config.channel_mode.upper()}</b>
        </div>
        <div style="font-weight: 700; color: {c_text_muted};">
            ⏱ Execution Latency: {metrics.elapsed_time_seconds * 1000:.1f} ms
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# Tabbed Workspace
# ---------------------------------------------------------
tab_charts, tab_table, tab_info = st.tabs([
    "📊 Performance Visualizations",
    "📋 Frame Audit Table",
    "📖 Space Standards & Technical Reference",
])

# ---------------------------------------------------------
# TAB 1: Visualizations
# ---------------------------------------------------------
with tab_charts:
    col_chart_left, col_chart_right = st.columns([1, 2])

    with col_chart_left:
        # Donut Chart: Frame Integrity
        donut_df = pd.DataFrame({
            "Integrity Status": ["Valid Frames", "Detected Corrupt", "Undetected Errors"],
            "Count": [metrics.valid_frames, metrics.detected_corrupt_frames, metrics.undetected_error_frames],
        })

        fig_donut = px.pie(
            donut_df,
            values="Count",
            names="Integrity Status",
            hole=0.62,
            color="Integrity Status",
            color_discrete_map={
                "Valid Frames": c_success,
                "Detected Corrupt": c_error,
                "Undetected Errors": c_warning,
            },
            title="Telemetry Frame Reception Status",
            template=plotly_template,
        )
        fig_donut.update_layout(
            margin=dict(l=15, r=15, t=45, b=15),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.22,
                xanchor="center",
                x=0.5,
                font=dict(color=c_text_primary, size=11),
            ),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="sans-serif", color=c_text_primary),
            title_font=dict(size=14, color=c_text_primary, family="sans-serif"),
        )
        st.plotly_chart(fig_donut, width="stretch")

    with col_chart_right:
        # Bar Chart: Injected Bit Errors per Frame
        color_map = {"VALID": c_success, "ERROR-DETECTED": c_error}
        fig_bar = px.bar(
            df_records,
            x="Frame_ID",
            y="Injected_Bit_Errors",
            color="Receiver_Status",
            color_discrete_map=color_map,
            title="Bit Error Inversion Profile per Frame Sequence",
            labels={"Frame_ID": "Frame Sequence Number", "Injected_Bit_Errors": "Injected Bit Errors"},
            template=plotly_template,
        )
        fig_bar.update_layout(
            margin=dict(l=15, r=15, t=45, b=15),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                font=dict(color=c_text_primary, size=11),
            ),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(
                title_font=dict(color=c_text_primary, size=12, family="sans-serif"),
                tickfont=dict(color=c_text_muted, size=10),
                gridcolor=c_grid,
                showgrid=True,
            ),
            yaxis=dict(
                title_font=dict(color=c_text_primary, size=12, family="sans-serif"),
                tickfont=dict(color=c_text_muted, size=10),
                gridcolor=c_grid,
                showgrid=True,
            ),
            font=dict(family="sans-serif", color=c_text_primary),
            title_font=dict(size=14, color=c_text_primary, family="sans-serif"),
        )
        st.plotly_chart(fig_bar, width="stretch")

    # Theoretical BER vs SNR Reference Waterfall Curve
    st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
    st.subheader("Deep-Space Link Theoretical Performance (BPSK / AWGN Benchmark)")

    snr_db = np.linspace(0, 12, 100)
    snr_linear = 10 ** (snr_db / 10.0)
    erfc_vec = np.vectorize(math.erfc)
    theoretical_ber = 0.5 * erfc_vec(np.sqrt(snr_linear))

    fig_waterfall = go.Figure()
    fig_waterfall.add_trace(
        go.Scatter(
            x=snr_db,
            y=theoretical_ber,
            mode="lines",
            name="Theoretical Uncoded BPSK (AWGN Link)",
            line=dict(color=c_accent, width=2.5),
        )
    )

    # Mark active simulation operating point
    if metrics.actual_ber > 0:
        fig_waterfall.add_trace(
            go.Scatter(
                x=[6.0],  # Indicative operating point for visual alignment
                y=[metrics.actual_ber],
                mode="markers",
                name=f"Current Simulation Run (Observed BER={metrics.actual_ber:.5f})",
                marker=dict(size=13, color=c_error, symbol="diamond", line=dict(width=1.5, color=c_card)),
            )
        )

    fig_waterfall.update_layout(
        title="Theoretical Bit Error Rate Waterfall Curve ($P_b$ vs $E_b/N_0$)",
        xaxis_title="Signal-to-Noise Ratio Eb/N0 (dB)",
        yaxis_title="Bit Error Rate (BER, log scale)",
        yaxis_type="log",
        template=plotly_template,
        margin=dict(l=20, r=20, t=50, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(
            title_font=dict(color=c_text_primary, size=12),
            tickfont=dict(color=c_text_muted, size=10),
            gridcolor=c_grid,
            showgrid=True,
        ),
        yaxis=dict(
            title_font=dict(color=c_text_primary, size=12),
            tickfont=dict(color=c_text_muted, size=10),
            gridcolor=c_grid,
            showgrid=True,
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(color=c_text_primary, size=11),
        ),
        font=dict(family="sans-serif", color=c_text_primary),
        title_font=dict(size=14, color=c_text_primary),
    )
    st.plotly_chart(fig_waterfall, width="stretch")

# ---------------------------------------------------------
# TAB 2: Frame Audit Table
# ---------------------------------------------------------
with tab_table:
    st.subheader("Telemetry Frame Reception Diagnostic Audit")
    st.markdown(
        f"<p style='color: {c_text_muted}; font-size: 0.9rem; margin-top: -6px;'>"
        f"Detailed frame-by-frame transmission log comparing ground-truth injected bit corruptions, calculated checksums, and receiver verdicts."
        f"</p>",
        unsafe_allow_html=True,
    )

    f_col1, f_col2, f_col3 = st.columns([1.5, 2, 1.5])
    with f_col1:
        status_filter = st.selectbox(
            "Filter Table by Receiver Verdict:",
            ["ALL FRAMES", "VALID (CRC PASSED)", "ERROR-DETECTED (CRC FAILED)"],
            index=0,
        )

    filtered_df = df_records
    if status_filter == "VALID (CRC PASSED)":
        filtered_df = df_records[df_records["Receiver_Status"] == "VALID"]
    elif status_filter == "ERROR-DETECTED (CRC FAILED)":
        filtered_df = df_records[df_records["Receiver_Status"] == "ERROR-DETECTED"]

    with f_col2:
        st.markdown(
            f"<div style='margin-top: 28px; font-size: 0.88rem; font-weight: 600; color: {c_text_muted};'>"
            f"Showing <b>{len(filtered_df)}</b> of <b>{len(df_records)}</b> frames ({metrics.valid_frames} Valid, {metrics.detected_corrupt_frames} Flagged Error)"
            f"</div>",
            unsafe_allow_html=True,
        )

    with f_col3:
        csv_bytes = df_records.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Export Complete Trace (CSV)",
            data=csv_bytes,
            file_name=f"space_telemetry_{result.config.crc_algorithm}_{metrics.total_frames}frames.csv",
            mime="text/csv",
            width="stretch",
        )

    st.dataframe(
        filtered_df,
        width="stretch",
        hide_index=True,
        height=400,
    )

# ---------------------------------------------------------
# TAB 3: Space Standards & Technical Reference
# ---------------------------------------------------------
with tab_info:
    st.subheader("Aerospace Communication Standards & Mathematical Specifications")

    col_info_a, col_info_b = st.columns(2)

    with col_info_a:
        st.markdown(
            f"""
            <div class="info-box">
                <h4>🛰️ CCSDS 131.0-B-5 Telemetry Framing</h4>
                <p style="color: {c_text_primary};">
                    The simulator implements standardized digital frame packetization compliant with the Consultative Committee for Space Data Systems (CCSDS):
                </p>
                <ul style="color: {c_text_primary}; font-size: 0.9rem; line-height: 1.6;">
                    <li><b>Frame Header (6 Bytes):</b> 16-bit Attached Sync Marker prefix (<code>0x1ACF</code>), 16-bit Frame Sequence Counter (0..65535), and 16-bit Payload Length Indicator.</li>
                    <li><b>Subsystem Payload:</b> Deterministic binary/byte-oriented spacecraft sensor telemetry.</li>
                    <li><b>Frame Footer:</b> Trailing Error Control field carrying cyclic checksum bytes.</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
            <div class="info-box">
                <h4>🌌 Deep Space Channel Physics</h4>
                <p style="color: {c_text_primary};">
                    Transmission is degraded by physical space disturbances modeled mathematically:
                </p>
                <ul style="color: {c_text_primary}; font-size: 0.9rem; line-height: 1.6;">
                    <li><b>Cosmic Noise:</b> Modeled as a Binary Symmetric Channel (BSC) with independent bit inversions matching target Bit Error Rate (BER).</li>
                    <li><b>Solar Flares / Interference:</b> Modeled as correlated burst errors corrupting contiguous bit blocks of configurable length.</li>
                    <li><b>Ground-Truth Ledger:</b> Tracks exact transmitted vs. inverted bit indices with zero guesswork.</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_info_b:
        st.markdown(
            f"""
            <div class="info-box">
                <h4>🛡️ CRC Polynomial Specifications</h4>
                <p style="color: {c_text_primary};">
                    Error detection is performed using high-order cyclic generator polynomials:
                </p>
                <ul style="color: {c_text_primary}; font-size: 0.9rem; line-height: 1.6;">
                    <li><b>CRC-16-CCITT (CCSDS Standard):</b> Generator polynomial $P(x) = x^{{16}} + x^{{12}} + x^5 + 1$ (<code>0x1021</code>), Initial remainder <code>0xFFFF</code>. Standard check vector <code>"123456789"</code> yields <code>0x29B1</code>.</li>
                    <li><b>CRC-32-IEEE (802.3 Space Profile):</b> Generator polynomial $P(x) = 0x04C11DB7$, Initial remainder <code>0xFFFFFFFF</code>. Standard check vector <code>"123456789"</code> yields <code>0xCBF43926</code>.</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
            <div class="info-box">
                <h4>📐 Mathematical Indicators</h4>
                <p style="color: {c_text_primary};">
                    All performance metrics are computed empirically over the transmitted sample:
                </p>
                <ul style="color: {c_text_primary}; font-size: 0.9rem; line-height: 1.6;">
                    <li><b>Bit Error Rate (BER):</b> $\\text{{BER}} = \\frac{{\\sum \\text{{Injected Bit Flips}}}}{{\\sum \\text{{Transmitted Bits}}}}$</li>
                    <li><b>Frame Error Rate (FER):</b> $\\text{{FER}} = \\frac{{\\sum \\text{{Corrupted Frames}}}}{{\\text{{Total Transmitted Frames}}}}$</li>
                    <li><b>Detection Accuracy:</b> $\\text{{Accuracy}} = \\frac{{\\text{{Detected Corrupt Frames}}}}{{\\text{{Actual Corrupt Frames}}}} \\times 100\\%$</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )
