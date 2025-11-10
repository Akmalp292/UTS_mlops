import math
from typing import Dict

import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# =====================================
# Streamlit Config
# =====================================
st.set_page_config(
    page_title="Analisis Kelayakan SD Indonesia — Input Manual",
    page_icon="📚",
    layout="wide",
)

st.session_state.setdefault("VERSION", "v0.2.0-input-only")

# =====================================
# Helpers
# =====================================
LOWER_BETTER = ["Rasio Siswa per Guru", "Putus per 1k Siswa", "Mengulang per 1k Siswa", "Rasio Rombel per Sekolah"]
HIGHER_BETTER = ["% Guru ≥S1", "Tendik per Sekolah"]

DEFAULT_WEIGHTS = {
    "Rasio Siswa per Guru": 0.30,
    "% Guru ≥S1": 0.25,
    "Putus per 1k Siswa": 0.20,
    "Mengulang per 1k Siswa": 0.10,
    "Rasio Rombel per Sekolah": 0.10,
    "Tendik per Sekolah": 0.05,
}

# Default benchmarks (bisa diubah dari sidebar)
DEFAULT_BENCHMARKS = {
    # format: (ideal, worst)
    "Rasio Siswa per Guru": (16.0, 40.0),         # lebih kecil lebih baik
    "% Guru ≥S1": (90.0, 50.0),                   # lebih besar lebih baik
    "Putus per 1k Siswa": (0.10, 5.00),           # lebih kecil lebih baik
    "Mengulang per 1k Siswa": (0.50, 8.00),       # lebih kecil lebih baik
    "Rasio Rombel per Sekolah": (6.0, 20.0),      # lebih kecil lebih baik
    "Tendik per Sekolah": (5.0, 0.0),             # lebih besar lebih baik
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

    total_guru = guru_lt + guru_ge
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
    """Map a metric to 0..100 given ideal and worst bounds.
    Uses linear scaling with clipping.
    """
    if value is None or np.isnan(value):
        return 0.0

    # Ensure non-identical bounds
    if ideal == worst:
        worst = ideal + (1e-6 if higher_better else -1e-6)

    if higher_better:
        # ideal high -> 100, worst low -> 0
        return float(np.clip((value - worst) / (ideal - worst), 0, 1) * 100)
    else:
        # ideal low -> 100, worst high -> 0
        return float(np.clip((worst - value) / (worst - ideal), 0, 1) * 100)


def compute_feasibility_score(metrics: Dict[str, float], weights: Dict[str, float], benchmarks: Dict[str, tuple]) -> Dict[str, float]:
    sub_scores = {}
    for k, w in weights.items():
        ideal, worst = benchmarks[k]
        hb = (k in HIGHER_BETTER)
        sub_scores[k] = score_metric(metrics[k], ideal, worst, hb)

    total_w = sum(weights.values()) or 1.0
    score = sum(sub_scores[k] * weights[k] for k in weights) / total_w
    return {"score": score, **sub_scores}


# =====================================
# Sidebar Controls
# =====================================
st.sidebar.title("📚 Kelayakan SD — Input Manual")
st.sidebar.caption("Streamlit app — " + st.session_state["VERSION"])

st.sidebar.markdown("### Bobot Skor")
weights = DEFAULT_WEIGHTS.copy()
for k in list(weights.keys()):
    weights[k] = st.sidebar.slider(k, 0.0, 1.0, float(weights[k]), 0.05)
# Normalize
w_sum = sum(weights.values()) or 1.0
for k in weights:
    weights[k] = weights[k] / w_sum

with st.sidebar.expander("Benchmark/Target (atur sesuai kebijakan)", expanded=False):
    bm = {}
    for k, (ideal, worst) in DEFAULT_BENCHMARKS.items():
        c1, c2 = st.columns(2)
        with c1:
            new_ideal = st.number_input(f"Ideal — {k}", value=float(ideal), step=0.1, format="%.2f")
        with c2:
            new_worst = st.number_input(f"Worst — {k}", value=float(worst), step=0.1, format="%.2f")
        bm[k] = (new_ideal, new_worst)

# =====================================
# Main — Inputs
# =====================================
st.title("🇮🇩 Analisis Kelayakan Sekolah Dasar — Input Manual")
st.write("Masukkan indikator agregat untuk **sebuah provinsi/sekolah hipotetis**. Aplikasi akan menghitung rasio, sub‑skor, dan **Feasibility Score** 0–100 berdasarkan bobot & benchmark yang kamu tentukan.")

with st.form("inputs"):
    st.subheader("Input Indikator (Agregat)")
    c1, c2, c3 = st.columns(3)
    with c1:
        prov_name = st.text_input("Nama Provinsi/Unit (opsional)", value="Skenario A")
        sekolah = st.number_input("Sekolah", min_value=1, value=2000, step=1)
        siswa = st.number_input("Siswa", min_value=1, value=500000, step=100)
        rombel = st.number_input("Rombongan Belajar", min_value=1, value=18000, step=10)
    with c2:
        mengulang = st.number_input("Mengulang", min_value=0, value=3000, step=10)
        putus = st.number_input("Putus Sekolah", min_value=0, value=1200, step=10)
        tendik_sm = st.number_input("Tenaga Kependidikan(SM)", min_value=0, value=4000, step=10)
        tendik_gt = st.number_input("Tenaga Kependidikan(>SM)", min_value=0, value=1200, step=10)
    with c3:
        guru_lt = st.number_input("Kepala Sekolah dan Guru(<S1)", min_value=0, value=2500, step=10)
        guru_ge = st.number_input("Kepala Sekolah dan Guru(≥ S1)", min_value=0, value=80000, step=100)

    submitted = st.form_submit_button("Hitung Feasibility Score")

if not submitted:
    st.info("Isi form di atas lalu klik **Hitung Feasibility Score**.")
    st.stop()

# =====================================
# Compute
# =====================================
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
res = compute_feasibility_score(metrics, weights, bm if 'bm' in locals() else DEFAULT_BENCHMARKS)

# =====================================
# KPIs & Score
# =====================================
st.subheader(f"📌 Ringkasan — {prov_name}")
colA, colB, colC, colD, colE = st.columns(5)
colA.metric("Feasibility Score", f"{res['score']:.1f}")
colB.metric("% Guru ≥S1", f"{metrics['% Guru ≥S1']:.1f}%")
colC.metric("Rasio Siswa/Guru", f"{metrics['Rasio Siswa per Guru']:.1f} : 1")
colD.metric("Putus per 1k", f"{metrics['Putus per 1k Siswa']:.2f}")
colE.metric("Rombel/Sekolah", f"{metrics['Rasio Rombel per Sekolah']:.2f}")

# Gauge chart
fig_g = go.Figure(go.Indicator(
    mode="gauge+number",
    value=res['score'],
    gauge={'axis': {'range': [0, 100]}, 'bar': {'thickness': 0.3}},
    title={'text': 'Feasibility Score'}
))
st.plotly_chart(fig_g, use_container_width=True)

# Sub-score table
st.markdown("### Sub‑Skor per Indikator (0–100)")
sub_table = pd.DataFrame({
    'Indikator': list(weights.keys()),
    'Sub‑Skor': [res[k] for k in weights.keys()],
    'Bobot': [weights[k] for k in weights.keys()],
})
st.dataframe(sub_table, use_container_width=True)

# Radar chart (normalize 0..100)
radar_df = pd.DataFrame({
    'Metric': list(weights.keys()),
    'Value': [res[k] for k in weights.keys()],
})
fig_radar = px.line_polar(radar_df, r='Value', theta='Metric', line_close=True, range_r=[0,100])
st.plotly_chart(fig_radar, use_container_width=True)

# =====================================
# Recommendations
# =====================================
st.markdown("### Rekomendasi Otomatis")
recs = []
# Compare each metric to its ideal
benchmarks = (bm if 'bm' in locals() else DEFAULT_BENCHMARKS)
for m in weights:
    ideal, worst = benchmarks[m]
    v = metrics[m]
    if m in LOWER_BETTER and not np.isnan(v):
        if v > ideal:
            recs.append(f"• Turunkan **{m}** (saat ini {v:.2f}; target ≤ {ideal}).")
    if m in HIGHER_BETTER and not np.isnan(v):
        if v < ideal:
            recs.append(f"• Naikkan **{m}** (saat ini {v:.2f}; target ≥ {ideal}).")

if not recs:
    recs = ["• Indikator sudah memenuhi target ideal yang ditetapkan."]

for r in recs:
    st.write(r)

st.markdown("---")
st.caption("Catatan: Feasibility Score berbasis **benchmark yang dapat dikonfigurasi** dan bukan penilaian resmi. Gunakan sebagai alat pendukung keputusan.")
