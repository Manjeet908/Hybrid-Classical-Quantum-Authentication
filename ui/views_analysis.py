"""
View: Protocol Analysis and Performance Comparison.
Focused read-only analytical benchmark for BB84, B92, and E91:
1. Vertical Protocol Performance Comparison Matrix
2. E91 CHSH Bell Inequality Analysis
"""
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from postprocessing.benchmark_evaluator import get_analytical_curves


def create_bell_noise_figure(df_noise):
    """Renders high-contrast dark theme plot for Bell |S| vs Noise."""
    fig, ax = plt.subplots(figsize=(6.2, 3.8))
    fig.patch.set_facecolor('#0f172a')
    ax.set_facecolor('#0f172a')
    ax.tick_params(colors='#94a3b8', labelsize=8.5)
    for spine in ax.spines.values():
        spine.set_color('#334155')

    x = df_noise["Noise (ε)"] * 100
    y = df_noise["E91 Bell |S|"]
    ax.plot(x, y, color='#00f5d4', linestyle='-', marker='o', markersize=4.5, linewidth=2.2, label='E91 CHSH Parameter |S|')

    ax.axhline(2.8284, color='#10b981', linestyle='--', linewidth=1.5, label="Cirel'son Bound (2.828)")
    ax.axhline(2.0000, color='#ef4444', linestyle='--', linewidth=1.5, label='Classical Bound (|S| = 2.0)')

    ax.fill_between(x, 2.0, 2.85, color='#10b981', alpha=0.08, label='Quantum Non-Locality Zone')
    ax.fill_between(x, 0.0, 2.0, color='#ef4444', alpha=0.06, label='Classical / Compromised Zone')

    ax.set_xlabel('Channel Depolarizing Noise ε (%)', color='#cbd5e1', fontsize=9.5)
    ax.set_ylabel('Bell Parameter |S|', color='#cbd5e1', fontsize=9.5)
    ax.set_ylim(0.0, 3.1)
    ax.grid(True, color='#1e293b', linestyle='--', alpha=0.7)
    ax.legend(facecolor='#1e293b', edgecolor='#334155', labelcolor='#f8fafc', fontsize=8.0, loc='lower left')
    plt.tight_layout()
    return fig


def create_bell_attack_figure(df_attack):
    """Renders high-contrast dark theme plot for Bell |S| vs Attack."""
    fig, ax = plt.subplots(figsize=(6.2, 3.8))
    fig.patch.set_facecolor('#0f172a')
    ax.set_facecolor('#0f172a')
    ax.tick_params(colors='#94a3b8', labelsize=8.5)
    for spine in ax.spines.values():
        spine.set_color('#334155')

    x = df_attack["Eve Intercept (%)"]
    y = df_attack["E91 Bell |S|"]
    ax.plot(x, y, color='#f72585', linestyle='-', marker='^', markersize=5.0, linewidth=2.2, label='E91 CHSH Parameter |S|')

    ax.axhline(2.8284, color='#10b981', linestyle='--', linewidth=1.5, label="Cirel'son Bound (2.828)")
    ax.axhline(2.0000, color='#ef4444', linestyle='--', linewidth=1.5, label='Classical Bound (|S| = 2.0)')

    ax.fill_between(x, 2.0, 2.85, color='#10b981', alpha=0.08)
    ax.fill_between(x, 0.0, 2.0, color='#ef4444', alpha=0.06)

    ax.set_xlabel('Eve Interception Rate (%)', color='#cbd5e1', fontsize=9.5)
    ax.set_ylabel('Bell Parameter |S|', color='#cbd5e1', fontsize=9.5)
    ax.set_ylim(0.0, 3.1)
    ax.grid(True, color='#1e293b', linestyle='--', alpha=0.7)
    ax.legend(facecolor='#1e293b', edgecolor='#334155', labelcolor='#f8fafc', fontsize=8.0, loc='upper right')
    plt.tight_layout()
    return fig


def render_analysis_view():
    st.markdown("### 📊 Protocol Analysis & Performance Comparison")
    st.markdown(
        "Standardized comparative evaluation across **BB84**, **B92**, and **E91** protocols. "
        "Examines architectural trade-offs, state representations, and E91 CHSH Bell inequality validation."
    )

    curves = get_analytical_curves()
    df_noise = curves["df_noise"]
    df_attack = curves["df_attack"]
    df_matrix = curves["df_matrix"]

    # ---------------------------------------------------------
    # 1. Vertical Protocol Performance Comparison Matrix
    # ---------------------------------------------------------
    st.markdown("#### 1. Protocol Performance Comparison Matrix")
    st.dataframe(df_matrix, use_container_width=True, hide_index=True)

    st.markdown("---")

    # ---------------------------------------------------------
    # 2. E91 CHSH Bell Inequality Analysis
    # ---------------------------------------------------------
    st.markdown("#### 2. E91 CHSH Bell Inequality Analysis")
    col_e91_1, col_e91_2, col_e91_3 = st.columns(3)
    col_e91_1.metric("Cirel'son Maximum Bound", "2.828", "Ideal Quantum |S| = 2√2")
    col_e91_2.metric("Classical Local Realism Bound", "2.000", "|S| ≤ 2.0 (Eavesdropped)")
    col_e91_3.metric("Entanglement Status", "Violated (|S| > 2.0)", "Quantum Non-Locality Confirmed")

    col_s1, col_s2 = st.columns(2)
    with col_s1:
        st.markdown("**Bell Parameter |S| vs Channel Noise (ε)**")
        fig_bell_noise = create_bell_noise_figure(df_noise)
        st.pyplot(fig_bell_noise)
        st.caption("Entanglement witness breaks ($|S| \\le 2.0$) when depolarizing noise exceeds ~14.6%, proving channel decoherence.")

    with col_s2:
        st.markdown("**Bell Parameter |S| vs Eve Interception Rate**")
        fig_bell_attack = create_bell_attack_figure(df_attack)
        st.pyplot(fig_bell_attack)
        st.caption("Adversarial eavesdropping collapses entangled Bell pairs into separable states, dropping $|S|$ to $\\le 1.414$ without needing error-checking bit leaks.")
