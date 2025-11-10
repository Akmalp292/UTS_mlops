# =============================================
# SSPI — Student Stress & Performance Insights (Two-Section, Guided)
# Minimal, safe, fun, informative — with navigation & argumentative recommendation
# =============================================
from typing import Dict
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# -----------------------------
# App Config
# -----------------------------
st.set_page_config(
    page_title="SSPI — Student Stress & Performance Insights",
    page_icon="🎓",
    layout="wide",
)

st.session_state.setdefault("VERSION", "v1.2-two-sections")
st.session_state.setdefault("sspi_data", None)

# -----------------------------
# Constants & Helpers
# -----------------------------
OPT = {"StudyHours": 3.0, "SleepHours": 9.5, "ClassSize": 28.0}

CLIP = lambda x: float(np.clip(x, 0.0, 100.0))


def perf_component(v: Dict[str, float]) -> Dict[str, float]:
    sh = 100 * np.exp(-((v["StudyHours"] - OPT["StudyHours"])**2)/(2*(1.5**2)))
    sl = 100 * np.exp(-((v["SleepHours"] - OPT["SleepHours"])**2)/(2*(1.0**2)))
    at = v["Attendance"]
    cs = 100 * (1 - np.clip((v["ClassSize"] - 15)/(45-15), 0, 1))
    sp = v["SchoolSupport"]
    wl = 100 * (1 - v["Workload"]/100)
    return {"StudyHours": CLIP(sh), "SleepHours": CLIP(sl), "Attendance": CLIP(at), "ClassSize": CLIP(cs), "SchoolSupport": CLIP(sp), "Workload": CLIP(wl)}


def stress_component(v: Dict[str, float]) -> Dict[str, float]:
    sh = 100 * (1 - np.exp(-((v["StudyHours"] - OPT["StudyHours"])**2)/(2*(1.5**2))))
    sl = 100 * (1 - np.clip(abs(v["SleepHours"]-OPT["SleepHours"])/2.0, 0, 1))
    at = v["Attendance"]
    cs = 100 * (1 - np.clip((v["ClassSize"]-15)/(45-15), 0, 1))
    sp = v["SchoolSupport"]
    wl = 100 * (1 - v["Workload"]/100)
    return {"StudyHours": CLIP(100-sh), "SleepHours": CLIP(sl), "Attendance": CLIP(at), "ClassSize": CLIP(cs), "SchoolSupport": CLIP(sp), "Workload": CLIP(wl)}


def weighted_score(c: Dict[str, float], weights: Dict[str, float]) -> float:
    return float(sum(c[k]*weights[k] for k in weights)/sum(weights.values()))


def traffic_light(score: float) -> str:
    if score >= 75: return "🟢 Baik"
    if score >= 50: return "🟡 Perlu Perhatian"
    return "🔴 Risiko Tinggi"


def build_recommendation(vals: Dict[str, float], perf_score: float, stress_score: float) -> str:
    """Return a short argumentative paragraph based on the weakest factors."""
    # Identify weakest components by combined score
    pc = perf_component(vals)
    sc = stress_component(vals)
    combined = {k: (pc[k] + sc[k]) / 2 for k in vals}
    weak = sorted(combined.items(), key=lambda x: x[1])[:2]
    parts = []

    # Core arguments
    if vals["SleepHours"] < 8.5:
        parts.append("menambah durasi tidur mendekati 9–10 jam untuk menekan stres dan menjaga konsentrasi")
    if vals["Workload"] > 70:
        parts.append("meringankan beban tugas harian atau memecahnya menjadi unit kecil yang terjadwal")
    if vals["ClassSize"] > 35:
        parts.append("mengurangi ukuran kelas/kelompok belajar agar interaksi guru‑siswa lebih efektif")
    if vals["SchoolSupport"] < 60:
        parts.append("memperkuat dukungan sekolah (konselor, kegiatan positif, komunikasi orang tua‑guru)")
    if vals["StudyHours"] < 2.0:
        parts.append("meningkatkan rutinitas belajar mandiri bertahap 15–30 menit per hari")
    if vals["Attendance"] < 90:
        parts.append("mengurangi ketidakhadiran melalui rencana dukungan dan komunikasi dengan keluarga")

    focus = ", ".join([w[0] for w in weak]) if weak else "faktor kunci"
    if not parts:
        return (
            f"Skor kesiapan {perf_score:.0f} dan kesehatan stres {stress_score:.0f} sudah seimbang. "
            f"Pertahankan kebiasaan yang ada dan monitor {focus} agar tidak menjadi penghambat ke depan."
        )
    return (
        f"Hasil menunjukkan keseimbangan performa ({perf_score:.0f}) dan stres ({stress_score:.0f}). "
        f"Untuk peningkatan yang cepat, prioritaskan {focus} dengan cara " + "; ".join(parts) + "."
    )

# -----------------------------
# Header & Navigation
# -----------------------------
st.header("SSPI — Student Stress & Performance Insights")
st.caption("Simple inputs → clear insights. Safe, fun, and informative.")
section = st.sidebar.radio("Navigasi", ["1) Input & Hasil", "2) Evaluasi & Saran"], index=0)

# -----------------------------
# SECTION 1 — INPUT & HASIL
# -----------------------------
if section == "1) Input & Hasil":
    st.subheader("1) Input & Hasil")
    # Optional intro GIF (placeholder path)
    # st.image("assets/intro_study_balance.gif", use_column_width=True)

    # Guided Inputs
    st.markdown("### 📘 Rutinitas Harian")
    c1, c2 = st.columns(2)
    with c1:
        study = st.slider("Jam Belajar / Hari", 0.0, 8.0, 3.0, 0.5, help="Waktu belajar mandiri di luar jam sekolah.")
        st.caption("💡 Disarankan 2–4 jam per hari untuk anak SD.")
    with c2:
        sleep = st.slider("Jam Tidur / Hari", 6.0, 11.0, 9.5, 0.5, help="Durasi tidur rata-rata setiap malam.")
        st.caption("💡 Ideal: 9–10 jam untuk usia sekolah dasar.")

    st.markdown("### 🏫 Lingkungan Sekolah")
    c3, c4 = st.columns(2)
    with c3:
        attend = st.slider("Kehadiran (%)", 50, 100, 95, 1, help="Persentase kehadiran siswa di sekolah.")
        st.caption("💡 Semakin tinggi semakin baik.")
    with c4:
        classsize = st.slider("Ukuran Kelas (Jumlah Teman Sebaya)", 15, 45, 28, 1, help="Jumlah siswa rata-rata dalam satu kelas.")
        st.caption("💡 Idealnya 25–30 siswa per kelas.")

    st.markdown("### 🌱 Dukungan & Beban Belajar")
    c5, c6 = st.columns(2)
    with c5:
        support = st.slider("Dukungan Sekolah (0–100)", 0, 100, 70, 5, help="Konselor, kegiatan positif, komunikasi orang tua.")
        st.caption("💡 Semakin tinggi semakin sehat secara mental.")
    with c6:
        workload = st.slider("Beban Tugas (0–100)", 0, 100, 50, 5, help="PR, ujian, proyek, dll.")
        st.caption("💡 Hindari beban terlalu berat agar tidak burnout.")

    # Compute immediately (no submit button to keep it simple)
    vals = {
        "StudyHours": float(study),
        "SleepHours": float(sleep),
        "Attendance": float(attend),
        "ClassSize": float(classsize),
        "SchoolSupport": float(support),
        "Workload": float(workload),
    }

    perf = perf_component(vals)
    stress = stress_component(vals)
    weights = {k: 1 for k in vals}
    perf_score = weighted_score(perf, weights)
    stress_score = weighted_score(stress, weights)

    # Save to session for Section 2
    st.session_state["sspi_data"] = {
        "vals": vals, "perf": perf, "stress": stress,
        "perf_score": perf_score, "stress_score": stress_score,
    }

    # KPIs
    st.markdown("---")
    cA, cB, cC = st.columns(3)
    with cA:
        st.metric("Performance Readiness", f"{perf_score:.1f}", help="Semakin tinggi semakin siap berprestasi.")
    with cB:
        st.metric("Stress Health", f"{stress_score:.1f}", help="Semakin tinggi semakin sehat (stres terkendali).")
    with cC:
        overall = min(perf_score, stress_score)
        st.metric("Overall Signal", traffic_light(overall))

    # Gauge
    fig_g = go.Figure(go.Indicator(
        mode="gauge+number",
        value=overall,
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'thickness': 0.3},
            'steps': [
                {'range': [0, 50], 'color': '#ffd6d6'},
                {'range': [50, 75], 'color': '#fff4cc'},
                {'range': [75, 100], 'color': '#d9f7be'}
            ]
        },
        title={'text': 'Overall Balance'}
    ))
    fig_g.update_layout(height=240, margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig_g, use_container_width=True)

# -----------------------------
# SECTION 2 — EVALUASI & SARAN
# -----------------------------
elif section == "2) Evaluasi & Saran":
    st.subheader("2) Evaluasi & Saran")
    data = st.session_state.get("sspi_data")
    if not data:
        st.info("Silakan isi **Section 1 — Input & Hasil** terlebih dahulu.")
        st.stop()

    vals = data["vals"]; perf = data["perf"]; stress = data["stress"]
    perf_score = data["perf_score"]; stress_score = data["stress_score"]

    # Evaluation Charts
    radar_df = pd.DataFrame({
        'Metric': list(vals.keys()),
        'Performance': [perf[k] for k in vals],
        'StressHealth': [stress[k] for k in vals],
    })
    fig_radar = px.line_polar(radar_df, r='Performance', theta='Metric', line_close=True, range_r=[0,100])
    fig_radar.add_trace(px.line_polar(radar_df, r='StressHealth', theta='Metric', line_close=True).data[0])
    fig_radar.update_layout(height=420, legend=dict(orientation='h', yanchor='bottom', y=-0.15, xanchor='center', x=0.5))
    st.plotly_chart(fig_radar, use_container_width=True)

    strength_df = pd.DataFrame({
        'Factor': list(vals.keys()),
        'Performance': [perf[k] for k in vals],
        'StressHealth': [stress[k] for k in vals],
    })
    strength_df['Combined'] = (strength_df['Performance'] + strength_df['StressHealth']) / 2.0
    strength_df = strength_df.sort_values('Combined', ascending=False)
    fig_bar = px.bar(strength_df.melt(id_vars='Factor', value_vars=['Performance','StressHealth'],
                         var_name='Dimension', value_name='Score'),
                     x='Factor', y='Score', color='Dimension', barmode='group', height=420,
                     title='Factor Strengths — Higher is Better')
    fig_bar.update_layout(xaxis_tickangle=-20, margin=dict(l=10, r=10, t=50, b=100))
    st.plotly_chart(fig_bar, use_container_width=True)

    # Argumentative Recommendation (one short paragraph)
    st.markdown("### Saran")
    paragraph = build_recommendation(vals, perf_score, stress_score)
    st.write(paragraph)

# -----------------------------
# Footer
# -----------------------------
st.markdown("---")
st.caption("SSPI adalah alat edukatif untuk eksplorasi keseimbangan belajar dan kesejahteraan siswa. Bukan pengganti asesmen profesional.")
