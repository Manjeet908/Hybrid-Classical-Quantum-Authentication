"""
Main Streamlit Application: Hybrid Quantum Authentication & QKD Suite.
Unified interactive dashboard for BB84, B92, E91, and Adaptive Hybrid QKD.
"""
import sys
import os

# Add project root directory to path for absolute package imports
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import streamlit as st
import qiskit

from ui.styles import QUANTUM_CSS, render_hero
from ui.views_simulator import render_simulator_view
from ui.views_hybrid_auth import render_hybrid_auth_view
from ui.views_theory import render_theory_view

# Streamlit Page Configuration
st.set_page_config(
    page_title="QuantumAuth | Hybrid QKD & Authentication Suite",
    page_icon="⚛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply Cyberpunk Dark Quantum CSS
st.markdown(QUANTUM_CSS, unsafe_allow_html=True)

# Main Header Hero
st.markdown(
    render_hero(
        title="HYBRID QUANTUM AUTHENTICATION & QKD SUITE",
        subtitle="Unified Qiskit simulation dashboard for BB84, B92, and E91 protocols with attack modeling and classical-quantum authentication."
    ),
    unsafe_allow_html=True
)

# Sidebar Navigation
with st.sidebar:
    st.markdown("### 🎛️ Navigation & Control")
    nav_selection = st.radio(
        "Select Dashboard Module",
        [
            "🔬 Protocol Simulator",
            "🛡️ Hybrid Auth vs MitM",
            "📚 Theory & Academy"
        ],
        index=0
    )

    st.markdown("---")
    st.markdown("### ⚙️ Simulation Environment")
    st.markdown(f"- **Quantum Backend:** `Qiskit AerSimulator`")
    st.markdown(f"- **Method:** `Matrix Product State (MPS)`")
    st.markdown(f"- **Qiskit Core:** `v{qiskit.__version__}`")
    st.markdown(f"- **Python Version:** `{sys.version.split(' ')[0]}`")

    st.markdown("---")
    st.markdown("### ℹ️ Quick Protocol Guide")
    st.caption("""
    - **BB84:** 4-state Z & X encoding; 11% QBER Shannon security bound.
    - **B92:** 2-state non-orthogonal encoding; 4.8% cutoff; simpler optics.
    - **E91:** Entangled EPR Bell pairs; CHSH Bell test (|S| > 2.0); device-independent security.
    - **Hybrid:** Wegman-Carter hash authentication on public discussion channel.
    """)

# Route to selected view
if nav_selection == "🔬 Protocol Simulator":
    render_simulator_view()
elif nav_selection == "🛡️ Hybrid Auth vs MitM":
    render_hybrid_auth_view()
elif nav_selection == "📚 Theory & Academy":
    render_theory_view()
