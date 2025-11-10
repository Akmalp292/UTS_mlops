# =============================================
# SSPI — Student Stress & Performance Insights (Simple)
# Minimal, safe, fun, and informative Streamlit app
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

st.session_state.setdefault("VERSION", "v1.0-simple")

# -----------------------------
# Core: Minimal feature set & simple scoring
# -----------------------------
# Chosen key factors (few, relevant, easy to answer by user)
# 1) Rata-rata jam belajar per hari (StudyHours)
# 2) Rata-rata jam tidur per hari (SleepHours)
# 3) Kehadiran (%) (Attendance)
# 4) Ukuran kelas rata-rata (ClassSize)
# 5) Dukungan sekolah (SchoolSupport) — skala 0..100 gabungan konselor, program BK, ekstrakurikuler positif
# 6) Beban tugas/materi (Workload) — 0..100 (semakin tinggi semakin berat)

FEATURES = [
    "StudyHours", "SleepHours", "Attendance", "ClassSize", "SchoolSupport", "Workload"
]

# Simple rules for stress & performance scores (0..100)
# - Performance up with StudyHours, SleepHours (till optimal), Attendance, Support; down with excessive Workload & huge ClassSize
# - Stress up with Workload, ClassSize; down with SleepHours, Support; slightly up if StudyHours too low or too high

OPT = {
    "StudyHours": 3.0,   # jam/hari yang sehat untuk SD (belajar mandiri di rumah)
    "SleepHours": 9.5,   # rekomendasi anak usia SD
    "ClassSize": 28.0,   # target ideal per kelas
}

WEIGHTS_PERF = {
    "StudyHours": 0.22,
    "SleepHours": 0.22,
    "Attendance": 0.24,
    "ClassSize": 0.10,
    "SchoolSupport": 0.14,
    "Workload": 0.08,
}

WEIGHTS_STRESS = {
    "StudyHours": 0.10,
    "SleepHours": 0.25,
    "Attendance": 0.05,
    "ClassSize": 0.20,
    "SchoolSupport": 0.20,
    "Workload": 0.20,
}

# helper bounds
CLIP = lambda x: float(np.clip(x, 0.0, 100.0))


def perf_component(vals: Dict[str, float]) -> Dict[str, float]:
    v = vals
    # StudyHours: bell around OPT (too low/high reduces)
    sh = 100.0 * np.exp(-((v["StudyHours"] - OPT["StudyHours"])**2) / (2 * (1.5**2)))
    # SleepHours: bell around OPT
    sl = 100.0 * np.exp(-((v["SleepHours"] - OPT["SleepHours"])**2) / (2 * (1.0**2)))
    # Attendance: linear
    at = v["Attendance"]
    # ClassSize: larger => lower; map 15..45 → 100..0
    cs = 100.0 * (1 - np.clip((v["ClassSize"] - 15) / (45 - 15), 0, 1))
    # SchoolSupport: direct
    sp = v["SchoolSupport"]
    # Workload: heavier => lower; map 0..100 → 100..0
    wl = 100.0 * (1 - v["Workload"]/100.0)
    return {"StudyHours": CLIP(sh), "SleepHours": CLIP(sl), "Attendance": CLIP(at),
            "ClassSize": CLIP(cs), "SchoolSupport": CLIP(sp), "Workload": CLIP(wl)}


def stress_component(vals: Dict[str, float]) -> Dict[str, float]:
    v = vals
    # StudyHours: U-shape (too low => ketertinggalan; too high => burnout)
    sh = 100.0 * (1 - np.exp(-((v["StudyHours"] - OPT["StudyHours"])**2) / (2 * (1.5**2))))
    # SleepHours: less sleep => more stress (map 6..11 to 100..0 around OPT)
    sl = 100.0 * np.clip((np.abs(v["SleepHours"] - OPT["SleepHours"]) / 2.0), 0, 1)
    sl = 100.0 - sl*100.0  # more aligned with OPT => lower stress → higher score means lower stress contribution, invert later in weight
    # Attendance: low attendance → academic stress risk
    at = 100.0 * (v["Attendance"]/100.0)
    # ClassSize: bigger → more stress (map 15..45 → 0..100)
    cs = 100.0 * np.clip((v["ClassSize"] - 15) / (45 - 15), 0, 1)
    # Support: more support → less stress (use inverse)
    sp = 100.0 - v["SchoolSupport"]
    # Workload: direct to stress
    wl = v["Workload"]
    # Return as components where 100 = good (low stress) to align with weighted average → invert for cs & wl
    # We'll convert to "good" scale: lower stress = higher component
    cs_good = 100.0 - cs
    wl_good = 100.0 - wl
    sh_good = 100.0 - sh
    return {"StudyHours": CLIP(sh_good), "SleepHours": CLIP(sl), "Attendance": CLIP(at),
            "ClassSize": CLIP(cs_good), "SchoolSupport": CLIP(100.0 - sp), "Workload": CLIP(wl_good)}


def weighted_score(components: Dict[str, float], weights: Dict[str, float]) -> float:
    return float(sum(components[k]*weights[k] for k in weights) / sum(weights.values()))


def traffic_light(score: float) -> str:
    if score >= 75: return "🟢 Baik"
    if score >= 50: return "🟡 Perlu Perhatian"
    return "🔴 Risiko Tinggi"

# -----------------------------
# Sidebar (minimal controls)
# -----------------------------
st.sidebar.title("SSPI — Konfigurasi Ringkas")
st.sidebar.caption("Versi " + st.session_state["VERSION"]) 

with st.sidebar.expander("Sesuaikan Bobot (opsional)", expanded=False):
    w_perf = {}
    for k in WEIGHTS_PERF:
        w_perf[k] = st.slider(f"Perf — {k}", 0.0, 1.0, float(WEIGHTS_PERF[k]), 0.05)
    s = sum(w_perf.values()) or 1.0
    for k in w_perf: w_perf[k] /= s

    w_str = {}
    for k in WEIGHTS_STRESS:
        w_str[k] = st.slider(f"Stress — {k}", 0.0, 1.0, float(WEIGHTS_STRESS[k]), 0.05)
    s2 = sum(w_str.values()) or 1.0
    for k in w_str: w_str[k] /= s2

# -----------------------------
# Header & Motto (concise)
# -----------------------------
st.header("SSPI — Student Stress & Performance Insights")
st.subheader("Simple inputs → clear insights. Safe, fun, and informative.")

# -----------------------------
# Inputs — to the point
# -----------------------------
with st.form("inputs"):
    c1, c2, c3 = st.columns(3)
    with c1:
        study = st.slider("Jam Belajar/Hari", 0.0, 8.0, 3.0, 0.5)
        sleep = st.slider("Jam Tidur/Hari", 6.0, 11.0, 9.5, 0.5)
    with c2:
        attend = st.slider("Kehadiran (%)", 50, 100, 95, 1)
        classsize = st.slider("Ukuran Kelas", 15, 45, 28, 1)
    with c3:
        support = st.slider("Dukungan Sekolah (0–100)", 0, 100, 70, 5)
        workload = st.slider("Beban Tugas (0–100)", 0, 100, 50, 5)
    go_btn = st.form_submit_button("Lihat Insight")

if not go_btn:
    st.info("Atur slider di atas lalu klik **Lihat Insight**.")
    st.stop()

vals = {
    "StudyHours": study,
    "SleepHours": sleep,
    "Attendance": float(attend),
    "ClassSize": float(classsize),
    "SchoolSupport": float(support),
    "Workload": float(workload),
}

perf_comp = perf_component(vals)
stress_comp = stress_component(vals)

w_perf = locals().get('w_perf', WEIGHTS_PERF)
w_str = locals().get('w_str', WEIGHTS_STRESS)

perf_score = weighted_score(perf_comp, w_perf)
stress_health = weighted_score(stress_comp, w_str)  # 0..100 where higher = healthier (lower stress)

# -----------------------------
# Output — clean & fun
# -----------------------------
colA, colB, colC = st.columns(3)
with colA:
    st.metric("Performance Readiness", f"{perf_score:.1f}", help="Semakin tinggi semakin siap berprestasi.")
with colB:
    st.metric("Stress Health", f"{stress_health:.1f}", help="Semakin tinggi semakin sehat (stres terkendali).")
with colC:
    mood = traffic_light(min(perf_score, stress_health))
    st.metric("Overall Signal", mood)

# Radar chart (both)
radar_df = pd.DataFrame({
    'Metric': FEATURES,
    'Performance': [perf_comp[k] for k in FEATURES],
    'StressHealth': [stress_comp[k] for k in FEATURES],
})
fig_radar = px.line_polar(radar_df, r='Performance', theta='Metric', line_close=True, range_r=[0,100])
fig_radar.add_trace(px.line_polar(radar_df, r='StressHealth', theta='Metric', line_close=True).data[0])
fig_radar.update_layout(height=420, legend=dict(orientation='h', yanchor='bottom', y=-0.15, xanchor='center', x=0.5))
st.plotly_chart(fig_radar, use_container_width=True)

# Friendly tips (short, actionable)
st.markdown("### Quick Tips")
tips = []
if sleep < 8.5: tips.append("Tingkatkan waktu tidur mendekati 9–10 jam untuk anak SD.")
if workload > 70: tips.append("Kurangi beban tugas harian atau bagi menjadi tugas kecil.")
if classsize > 35: tips.append("Kaji pengelompokan kelas agar interaksi guru-siswa lebih efektif.")
if support < 60: tips.append("Perkuat dukungan: konselor, klub positif, komunikasi orang tua.")
if study < 2.0: tips.append("Tambah rutinitas belajar harian 15–30 menit secara bertahap.")
if attend < 90: tips.append("Identifikasi hambatan kehadiran dan buat rencana dukungan.")

if not tips:
    tips = ["Kondisi sudah cukup baik. Pertahankan kebiasaan tidur, ritme belajar, dan dukungan sekolah."]
for t in tips:
    st.write("• ", t)

st.markdown("---")
st.caption("SSPI adalah alat edukatif. Bukan pengganti asesmen profesional. Gunakan secara bertanggung jawab.")
