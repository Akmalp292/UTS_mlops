# =============================================
# SSPI — Student Stress & Performance Insights (Guided Input)
# Friendly, sectioned inputs with small notes for guidance
# =============================================
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

st.session_state.setdefault("VERSION", "v1.1-guided")

# -----------------------------
# Constants & Helpers
# -----------------------------
OPT = {"StudyHours": 3.0, "SleepHours": 9.5, "ClassSize": 28.0}

CLIP = lambda x: float(np.clip(x, 0.0, 100.0))


def perf_component(v):
    sh = 100 * np.exp(-((v["StudyHours"] - OPT["StudyHours"])**2)/(2*(1.5**2)))
    sl = 100 * np.exp(-((v["SleepHours"] - OPT["SleepHours"])**2)/(2*(1.0**2)))
    at = v["Attendance"]
    cs = 100 * (1 - np.clip((v["ClassSize"] - 15)/(45-15), 0, 1))
    sp = v["SchoolSupport"]
    wl = 100 * (1 - v["Workload"]/100)
    return {"StudyHours": CLIP(sh), "SleepHours": CLIP(sl), "Attendance": CLIP(at), "ClassSize": CLIP(cs), "SchoolSupport": CLIP(sp), "Workload": CLIP(wl)}


def stress_component(v):
    sh = 100 * (1 - np.exp(-((v["StudyHours"] - OPT["StudyHours"])**2)/(2*(1.5**2))))
    sl = 100 * (1 - np.clip(abs(v["SleepHours"]-OPT["SleepHours"])/2.0, 0, 1))
    at = v["Attendance"]
    cs = 100 * (1 - np.clip((v["ClassSize"]-15)/(45-15), 0, 1))
    sp = v["SchoolSupport"]
    wl = 100 * (1 - v["Workload"]/100)
    return {"StudyHours": CLIP(100-sh), "SleepHours": CLIP(sl), "Attendance": CLIP(at), "ClassSize": CLIP(cs), "SchoolSupport": CLIP(sp), "Workload": CLIP(wl)}


def weighted_score(c, w):
    return float(sum(c[k]*w[k] for k in w)/sum(w.values()))


def traffic_light(score):
    if score >= 75: return "🟢 Baik"
    if score >= 50: return "🟡 Perlu Perhatian"
    return "🔴 Risiko Tinggi"

# -----------------------------
# Header & Motto
# -----------------------------
st.header("SSPI — Student Stress & Performance Insights")
st.subheader("Isi data sederhana untuk melihat keseimbangan antara stres dan performa siswa.")

# -----------------------------
# Guided Input Sections with Notes
# -----------------------------
with st.container():
    st.markdown("### 📘 Rutinitas Harian")
    st.caption("Masukkan waktu belajar dan tidur rata-rata per hari.")
    c1, c2 = st.columns(2)
    with c1:
        study = st.slider("Jam Belajar / Hari", 0.0, 8.0, 3.0, 0.5, help="Waktu belajar mandiri di luar jam sekolah.")
        st.caption("💡 Disarankan 2–4 jam per hari untuk anak SD.")
    with c2:
        sleep = st.slider("Jam Tidur / Hari", 6.0, 11.0, 9.5, 0.5, help="Durasi tidur rata-rata setiap malam.")
        st.caption("💡 Ideal: 9–10 jam untuk usia sekolah dasar.")

with st.container():
    st.markdown("### 🏫 Lingkungan Sekolah")
    st.caption("Masukkan data umum terkait kehadiran dan kondisi kelas.")
    c1, c2 = st.columns(2)
    with c1:
        attend = st.slider("Kehadiran (%)", 50, 100, 95, 1, help="Persentase kehadiran siswa di sekolah.")
        st.caption("💡 Semakin tinggi semakin baik.")
    with c2:
        classsize = st.slider("Ukuran Kelas (Jumlah Teman Sebaya)", 15, 45, 28, 1, help="Jumlah siswa rata-rata dalam satu kelas.")
        st.caption("💡 Idealnya 25–30 siswa per kelas.")

with st.container():
    st.markdown("### 🌱 Dukungan & Beban Belajar")
    st.caption("Masukkan tingkat dukungan dan beban akademik siswa.")
    c1, c2 = st.columns(2)
    with c1:
        support = st.slider("Dukungan Sekolah (0–100)", 0, 100, 70, 5, help="Ketersediaan konselor, kegiatan positif, komunikasi guru.")
        st.caption("💡 Semakin tinggi semakin sehat secara mental.")
    with c2:
        workload = st.slider("Beban Tugas (0–100)", 0, 100, 50, 5, help="Tingkat kesibukan siswa akibat PR, ujian, proyek, dll.")
        st.caption("💡 Hindari beban terlalu berat agar siswa tidak burnout.")

# -----------------------------
# Process
# -----------------------------
vals = {"StudyHours": study, "SleepHours": sleep, "Attendance": float(attend), "ClassSize": float(classsize), "SchoolSupport": float(support), "Workload": float(workload)}

perf = perf_component(vals)
stress = stress_component(vals)
weights = {k: 1 for k in vals}

perf_score = weighted_score(perf, weights)
stress_score = weighted_score(stress, weights)

# -----------------------------
# Output — clean & helpful
# -----------------------------
st.markdown("---")
colA, colB, colC = st.columns(3)
with colA:
    st.metric("Performance Readiness", f"{perf_score:.1f}")
with colB:
    st.metric("Stress Health", f"{stress_score:.1f}")
with colC:
    st.metric("Overall Signal", traffic_light(min(perf_score, stress_score)))

radar_df = pd.DataFrame({
    'Faktor': list(vals.keys()),
    'Performa': [perf[k] for k in vals],
    'Kesehatan Stres': [stress[k] for k in vals],
})
fig = px.line_polar(radar_df, r='Performa', theta='Faktor', line_close=True, range_r=[0,100])
fig.add_trace(px.line_polar(radar_df, r='Kesehatan Stres', theta='Faktor', line_close=True).data[0])
fig.update_layout(height=420, legend=dict(orientation='h', yanchor='bottom', y=-0.2, xanchor='center', x=0.5))
st.plotly_chart(fig, use_container_width=True)

# -----------------------------
# Quick Tips
# -----------------------------
st.markdown("### 💡 Tips Cepat")
tips = []
if sleep < 8.5: tips.append("Tambahkan waktu tidur hingga 9–10 jam.")
if workload > 70: tips.append("Kurangi beban tugas harian secara bertahap.")
if classsize > 35: tips.append("Kaji ulang pembagian kelas agar lebih efektif.")
if support < 60: tips.append("Perkuat dukungan sekolah dan kegiatan positif.")
if study < 2.0: tips.append("Tambah waktu belajar 15–30 menit per hari.")
if attend < 90: tips.append("Evaluasi penyebab ketidakhadiran dan cari solusi.")

if not tips:
    tips = ["Kondisi siswa terlihat seimbang. Pertahankan rutinitas positif."]
for t in tips:
    st.write("•", t)

st.markdown("---")
st.caption("SSPI adalah alat edukatif untuk eksplorasi keseimbangan belajar dan kesejahteraan siswa. Tidak menggantikan asesmen psikolog profesional.")

