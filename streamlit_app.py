# ---------------------------------------------
# Analisis Kelayakan SD Indonesia — Input Manual (Pro)
# Streamlit professional UI with scenario save & compare
# ---------------------------------------------
import math
from typing import Dict, Tuple

import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# ============================
# App Config & Style
# ============================
st.set_page_config(
    page_title="Analisis Kelayakan SD Indonesia",
    page_icon="📚",
    layout="wide",
)

st.session_state.setdefault("VERSION", "v0.3.0-pro")
st.session_state.setdefault("scenarios", [])  # list of dicts

# Minimal CSS polish (cards, headings)
st.markdown(
    """
    <style>
      .metric-card {border-radius: 16px; padding: 16px; border: 1px solid #E9ECEF; background: #FFFFFF; box-shadow: 0 1px 3px rgba(0,0,0,0.06);} 
      .metric-title {font-size: 12px; color: #6c757d; text-transform: uppercase; letter-spacing: .08em;}
      .metric-value {font-size: 26px; font-weight: 700; margin-top: 4px;}
      .muted {color:#6c757d}
      .section {margin-top: 8px; margin-bottom: 8px;}
    </style>
    """,
    unsafe_allow_html=True,
)

# ============================
# Constants & Helpers
# ============================
LOWER_BETTER = [
    "Rasio Siswa per Guru",
    "Putus per 1k Siswa",
    "Mengulang per 1k Siswa",
    "Rasio Rombel per Sekolah",
]
HIGHER_BETTER = ["% Guru ≥S1", "Tendik per Sekolah"]

DEFAULT_WEIGHTS: Dict[str, float] = {
    "Rasio Siswa per Guru": 0.30,
    "% Guru ≥S1": 0.25,
    "Putus per 1k Siswa": 0.20,
    "Mengulang per 1k Siswa": 0.10,
    "Rasio Rombel per Sekolah": 0.10,
    "Tendik per Sekolah": 0.05,
}

# Benchmarks: (ideal, worst)
DEFAULT_BENCHMARKS: Dict[str, Tuple[float, float]] = {
    "Rasio Siswa per Guru": (16.0, 40.0),
    "% Guru ≥S1": (90.0, 50.0),
    "Putus per 1k Siswa": (0.10, 5.00),
    "Mengulang per 1k Siswa": (0.50, 8.00),
    "Rasio Rombel per Sekolah": (6.0, 20.0),
    "Tendik per Sekolah": (5.0, 0.0),
}

PRESET_BENCHMARKS = {
    "Nasional (Moderate)": DEFAULT_BENCHMARKS,
    "Ambisius (Target 2030)": {
        "Rasio Siswa per Guru": (14.0, 40.0),
        "% Guru ≥S1": (95.0, 60.0),
        "Putus per 1k Siswa": (0.05, 5.00),
        "Mengulang per 1k Siswa": (0.30, 8.00),
        "Rasio Rombel per Sekolah": (5.0, 22.0),
        "Tendik per Sekolah": (6.0, 0.0),
    },
    "Hati‑hati (Conservative)": {
        "Rasio Siswa per Guru": (18.0, 40.0),
        "% Guru ≥S1": (85.0, 50.0),
        "Putus per 1k Siswa": (0.20, 6.00),
        "Mengulang per 1k Siswa": (1.00, 9.00),
        "Rasio Rombel per Sekolah": (7.0, 24.0),
        "Tendik per Sekolah": (4.0, 0.0),
    },
}


def _safe_div(n, d):
    try:
        n = float(n)
        d = float(d)
        return n / d if d != 0 else np.nan
    except Exception:
        return np.nan


def compute_ratios_from_counts(values: Dict[str, float]) -> Dict[str, float]:
    sekolah = values["Sekolah"]
    siswa = values["Siswa"]
    mengulang = values["Mengulang"]
    putus = values["Putus Sekolah"]
    guru_lt = values["Kepala Sekolah dan Guru(<S1)"]
    guru_ge = values["Kepala Sekolah dan Guru(≥ S1)"]
    tendik_sm = values["Tenaga Kependidikan(SM)"]
    tendik_gt = values["Tenaga Kependidikan(>SM)"]
    rombel = values["Rombongan Belajar"]

    total_guru = max(0.0, float(guru_lt) + float(guru_ge))
    rasio_siswa_per_sekolah = _safe_div(siswa, sekolah)
    rasio_rombel_per_sekolah = _safe_div(rombel, sekolah)
    pct_guru_s1 = _safe_div(guru_ge, total_guru) * 100
    rasio_siswa_per_guru = _safe_div(siswa, total_guru)
    tendik_per_sekolah = _safe_div(tendik_sm + tendik_gt, sekolah)
    putus_per_1k = _safe_div(putus, siswa) * 1000
    mengulang_per_1k = _safe_div(mengulang, siswa) * 1000

    return {
        "Rasio Siswa per Sekolah": rasio_siswa_per_sekolah,
        "Rasio Rombel per Sekolah": rasio_rombel_per_sekolah,
        "% Guru ≥S1": pct_guru_s1,
        "Rasio Siswa per Guru": rasio_siswa_per_guru,
        "Tendik per Sekolah": tendik_per_sekolah,
        "Putus per 1k Siswa": putus_per_1k,
        "Mengulang per 1k Siswa": mengulang_per_1k,
        "Total Guru": total_guru,
    }


def score_metric(value: float, ideal: float, worst: float, higher_better: bool) -> float:
    if value is None or np.isnan(value):
        return 0.0
    if ideal == worst:
        worst = ideal + (1e-6 if higher_better else -1e-6)
    if higher_better:
        return float(np.clip((value - worst) / (ideal - worst), 0, 1) * 100)
    else:
        return float(np.clip((worst - value) / (worst - ideal), 0, 1) * 100)


def compute_feasibility_score(metrics: Dict[str, float], weights: Dict[str, float], benchmarks: Dict[str, Tuple[float, float]]):
    sub_scores = {}
    for k, w in weights.items():
        ideal, worst = benchmarks[k]
        hb = (k in HIGHER_BETTER)
        sub_scores[k] = score_metric(metrics[k], ideal, worst, hb)
    total_w = sum(weights.values()) or 1.0
    score = sum(sub_scores[k] * weights[k] for k in weights) / total_w
    return {"score": score, **sub_scores}


# ============================
# Sidebar — Controls
# ============================
st.sidebar.title("📚 Kelayakan SD — Konfigurasi")
st.sidebar.caption("Streamlit — " + st.session_state["VERSION"])

# Preset Buttons for Benchmarks
preset_name = st.sidebar.selectbox("Preset Benchmark", list(PRESET_BENCHMARKS.keys()), index=0)
benchmarks = PRESET_BENCHMARKS[preset_name]

with st.sidebar.expander("Atur Bobot Indikator", expanded=True):
    weights = DEFAULT_WEIGHTS.copy()
    for k in list(weights.keys()):
        weights[k] = st.slider(k, 0.0, 1.0, float(weights[k]), 0.05)
    # Normalize
    s = sum(weights.values()) or 1.0
    for k in weights:
        weights[k] = weights[k] / s
    st.progress(min(1.0, s))

with st.sidebar.expander("Kustomisasi Benchmark", expanded=False):
    bm = {}
    for k, (ideal, worst) in benchmarks.items():
        c1, c2 = st.columns(2)
        with c1:
            new_ideal = st.number_input(f"Ideal — {k}", value=float(ideal), step=0.1, format="%.2f")
        with c2:
            new_worst = st.number_input(f"Worst — {k}", value=float(worst), step=0.1, format="%.2f")
        bm[k] = (new_ideal, new_worst)

# ============================
# Header
# ============================
st.title("🇮🇩 Analisis Kelayakan Sekolah Dasar — Input Manual (Pro)")
st.write("Masukkan indikator agregat, sesuaikan bobot & benchmark, simpan skenario, dan bandingkan dampaknya secara visual.")

# ============================
# Input Form (Professional layout)
# ============================
with st.container():
    st.subheader("Form Indikator")
    st.markdown('<div class="muted">Semua angka adalah agregat per wilayah/entitas kebijakan.</div>', unsafe_allow_html=True)
    with st.form("inputs", clear_on_submit=False):
        c1, c2, c3 = st.columns(3)
        with c1:
            prov_name = st.text_input("Nama Skenario", value="Skenario A", help="Nama bebas untuk skenario ini.")
            sekolah = st.number_input("Sekolah", min_value=1, value=2000, step=1, help="Jumlah unit SD aktif.")
            siswa = st.number_input("Siswa", min_value=1, value=500000, step=100, help="Total siswa aktif.")
            rombel = st.number_input("Rombongan Belajar", min_value=1, value=18000, step=10, help="Total kelas aktif.")
        with c2:
            mengulang = st.number_input("Mengulang", min_value=0, value=3000, step=10, help="Jumlah siswa mengulang.")
            putus = st.number_input("Putus Sekolah", min_value=0, value=1200, step=10, help="Jumlah siswa putus sekolah.")
            tendik_sm = st.number_input("Tenaga Kependidikan(SM)", min_value=0, value=4000, step=10)
            tendik_gt = st.number_input("Tenaga Kependidikan(>SM)", min_value=0, value=1200, step=10)
        with c3:
            guru_lt = st.number_input("Kepala Sekolah dan Guru(<S1)", min_value=0, value=2500, step=10)
            guru_ge = st.number_input("Kepala Sekolah dan Guru(≥ S1)", min_value=0, value=80000, step=100)
        submitted = st.form_submit_button("Hitung Feasibility Score ⚡", use_container_width=True)

if not submitted:
    st.info("Isi form di atas lalu klik **Hitung Feasibility Score**.")
    st.stop()

# ============================
# Compute & Results
# ============================
raw_values = {
    "Sekolah": sekolah,
    "Siswa": siswa,
    "Mengulang": mengulang,
    "Putus Sekolah": putus,
    "Kepala Sekolah dan Guru(<S1)": guru_lt,
    "Kepala Sekolah dan Guru(≥ S1)": guru_ge,
    "Tenaga Kependidikan(SM)": tendik_sm,
    "Tenaga Kependidikan(>SM)": tendik_gt,
    "Rombongan Belajar": rombel,
}
metrics = compute_ratios_from_counts(raw_values)
active_benchmarks = bm if 'bm' in locals() and bm else benchmarks
res = compute_feasibility_score(metrics, weights, active_benchmarks)

# ============================
# TABS — Overview | Sub-skor | Grafik | Rekomendasi | Bandingkan
# ============================
overview_tab, subs_tab, charts_tab, recs_tab, compare_tab = st.tabs([
    "Overview", "Sub‑Skor", "Grafik", "Rekomendasi", "Bandingkan Skenario",
])

with overview_tab:
    st.subheader(f"Ringkasan — {prov_name}")
    colA, colB, colC, colD, colE = st.columns(5)
    with colA:
        st.markdown('<div class="metric-card"><div class="metric-title">Feasibility Score</div>'
                    f'<div class="metric-value">{res["score"]:.1f}</div></div>', unsafe_allow_html=True)
    with colB:
        st.markdown('<div class="metric-card"><div class="metric-title">% Guru ≥S1</div>'
                    f'<div class="metric-value">{metrics["% Guru ≥S1"]:.1f}%</div></div>', unsafe_allow_html=True)
    with colC:
        st.markdown('<div class="metric-card"><div class="metric-title">Rasio Siswa/Guru</div>'
                    f'<div class="metric-value">{metrics["Rasio Siswa per Guru"]:.1f} : 1</div></div>', unsafe_allow_html=True)
    with colD:
        st.markdown('<div class="metric-card"><div class="metric-title">Putus per 1k</div>'
                    f'<div class="metric-value">{metrics["Putus per 1k Siswa"]:.2f}</div></div>', unsafe_allow_html=True)
    with colE:
        st.markdown('<div class="metric-card"><div class="metric-title">Rombel/Sekolah</div>'
                    f'<div class="metric-value">{metrics["Rasio Rombel per Sekolah"]:.2f}</div></div>', unsafe_allow_html=True)

    # Gauge
    fig_g = go.Figure(go.Indicator(
        mode="gauge+number",
        value=res['score'],
        gauge={'axis': {'range': [0, 100]}, 'bar': {'thickness': 0.3}},
        title={'text': 'Feasibility Score'}
    ))
    fig_g.update_layout(height=260, margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig_g, use_container_width=True)

    # Save scenario button
    if st.button("Simpan Skenario", type="primary"):
        st.session_state.scenarios.append({
            "name": prov_name,
            "score": float(res['score']),
            "metrics": metrics,
            "subscores": {k: float(res[k]) for k in DEFAULT_WEIGHTS.keys()},
            "weights": weights,
            "benchmarks": active_benchmarks,
        })
        st.success(f"Skenario '{prov_name}' disimpan. Lihat tab **Bandingkan Skenario**.")

with subs_tab:
    st.subheader("Sub‑Skor per Indikator (0–100)")
    sub_table = pd.DataFrame({
        'Indikator': list(weights.keys()),
        'Sub‑Skor': [res[k] for k in weights.keys()],
        'Bobot': [weights[k] for k in weights.keys()],
    }).sort_values('Sub‑Skor', ascending=False)
    st.dataframe(sub_table, use_container_width=True)

    # Radar
    radar_df = pd.DataFrame({'Metric': list(weights.keys()), 'Value': [res[k] for k in weights.keys()]})
    fig_radar = px.line_polar(radar_df, r='Value', theta='Metric', line_close=True, range_r=[0,100])
    fig_radar.update_layout(height=420, margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig_radar, use_container_width=True)

with charts_tab:
    st.subheader("Grafik Rasio & Komponen")
    charts = {
        "% Guru ≥S1": metrics["% Guru ≥S1"],
        "Rasio Siswa per Guru": metrics["Rasio Siswa per Guru"],
        "Putus per 1k Siswa": metrics["Putus per 1k Siswa"],
        "Mengulang per 1k Siswa": metrics["Mengulang per 1k Siswa"],
        "Rasio Rombel per Sekolah": metrics["Rasio Rombel per Sekolah"],
        "Tendik per Sekolah": metrics["Tendik per Sekolah"],
    }
    bar_df = pd.DataFrame({"Indikator": list(charts.keys()), "Nilai": list(charts.values())})
    fig_bar = px.bar(bar_df, x="Indikator", y="Nilai", height=460)
    fig_bar.update_layout(xaxis_tickangle=-20, margin=dict(l=10, r=10, t=40, b=100))
    st.plotly_chart(fig_bar, use_container_width=True)

with recs_tab:
    st.subheader("Rekomendasi Otomatis")
    recommendations = []
    for m in weights:
        ideal, _worst = active_benchmarks[m]
        v = metrics[m]
        if m in LOWER_BETTER and not np.isnan(v) and v > ideal:
            recommendations.append(f"• Turunkan **{m}** (saat ini {v:.2f}; target ≤ {ideal}).")
        if m in HIGHER_BETTER and not np.isnan(v) and v < ideal:
            recommendations.append(f"• Naikkan **{m}** (saat ini {v:.2f}; target ≥ {ideal}).")
    if not recommendations:
        recommendations = ["• Semua indikator sudah memenuhi target ideal yang ditetapkan."]
    for r in recommendations:
        st.write(r)

with compare_tab:
    st.subheader("Bandingkan Skenario")
    scs = st.session_state.scenarios
    if len(scs) < 1:
        st.info("Belum ada skenario tersimpan. Simpan skenario dari tab **Overview**.")
    else:
        names = [s["name"] for s in scs]
        c1, c2 = st.columns(2)
        with c1:
            sel_a = st.selectbox("Skenario A", names, index=0)
        with c2:
            sel_b = st.selectbox("Skenario B", names, index=min(1, len(names)-1) if len(names) > 1 else 0)
        A = next(s for s in scs if s["name"] == sel_a)
        B = next(s for s in scs if s["name"] == sel_b)

        # Delta table for main metrics
        comp_rows = []
        keys = list(DEFAULT_WEIGHTS.keys())
        for k in ["Feasibility Score"] + keys:
            va = (A['score'] if k == "Feasibility Score" else A['subscores'][k])
            vb = (B['score'] if k == "Feasibility Score" else B['subscores'][k])
            comp_rows.append({"Indikator": k, sel_a: va, sel_b: vb, "Δ (B - A)": vb - va})
        comp_df = pd.DataFrame(comp_rows)
        st.dataframe(comp_df, use_container_width=True)

        fig_cmp = px.bar(comp_df[comp_df["Indikator"] != "Feasibility Score"], x="Indikator", y="Δ (B - A)",
                         title="Perubahan Sub‑Skor (B - A)", height=420)
        fig_cmp.update_layout(xaxis_tickangle=-20, margin=dict(l=10, r=10, t=40, b=100))
        st.plotly_chart(fig_cmp, use_container_width=True)

# ============================
# Footer
# ============================
st.markdown("---")
st.caption(
    "© 2025 — Analisis Kelayakan SD (Input Manual). Skor bersifat indikatif berbasis bobot & benchmark yang dapat dikonfigurasi."
)
