# =============================================
# SSPI — Student Stress & Performance Insights (Refined Version)
# Two-section layout with focused recommendations and no emojis
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
    layout="wide",
)

st.session_state.setdefault("VERSION", "v1.3-refined")
st.session_state.setdefault("sspi_data", None)

# -----------------------------
# Global Styles (Professional look)
# -----------------------------
st.markdown(
    """
    <style>
      /* App background */
      [data-testid=\"stAppViewContainer\"] {
        background: linear-gradient(180deg,#f7f9fc 0%, #ffffff 40%);
      }
      /* Sidebar */
      [data-testid=\"stSidebar\"] {
        background: #0f172a; /* slate-900 */
        color: #e2e8f0;
      }
      [data-testid=\"stSidebar\"] h1, [data-testid=\"stSidebar\"] h2, [data-testid=\"stSidebar\"] h3,
      [data-testid=\"stSidebar\"] label, [data-testid=\"stSidebar\"] p {
        color: #e2e8f0 !important;
      }
      /* Section title */
      .section-title {
        font-weight: 800; color: #0f172a; font-size: 1.15rem; margin: 0.25rem 0 0.5rem 0;
      }
      /* Card wrapper */
      .card { background: #ffffff; border: 1px solid #e5e7eb; border-radius: 12px; padding: 16px; box-shadow: 0 2px 8px rgba(15,23,42,0.06); }
      .kpi { background: #ffffff; border: 1px solid #e5e7eb; border-radius: 12px; padding: 8px 12px; box-shadow: 0 2px 8px rgba(15,23,42,0.04); }
      /* Divider */
      .divider { height: 1px; background: linear-gradient(90deg, rgba(15,23,42,0), rgba(15,23,42,.15), rgba(15,23,42,0)); margin: 14px 0; }
      /* Chart containers */
      .chart { background: #ffffff; border: 1px solid #e5e7eb; border-radius: 12px; padding: 8px; box-shadow: 0 2px 8px rgba(15,23,42,0.04); }
    </style>
    """,
    unsafe_allow_html=True,
)

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
    if score >= 75: return "Baik"
    if score >= 50: return "Perlu Perhatian"
    return "Risiko Tinggi"

def build_recommendation(vals: Dict[str, float]) -> str:
    suggestions = []
    if vals["SleepHours"] < 8.5:
        suggestions.append(f"Kamu perlu tidur yang cukup, idealnya sekitar 9–10 jam per hari.")
    if vals["Workload"] > 70:
        suggestions.append(f"Kurangi beban tugas agar waktu istirahat dan rekreasi lebih seimbang.")
    if vals["ClassSize"] > 35:
        suggestions.append(f"Ukuran kelas yang besar dapat meningkatkan tekanan belajar, pertimbangkan pengelompokan ulang kelas.")
    if vals["SchoolSupport"] < 60:
        suggestions.append(f"Tingkatkan dukungan sekolah melalui kegiatan positif dan layanan konseling.")
    if vals["StudyHours"] < 2.0:
        suggestions.append(f"Tambahkan waktu belajar mandiri sekitar 15–30 menit setiap hari untuk meningkatkan pemahaman.")
    if vals["Attendance"] < 90:
        suggestions.append(f"Tingkatkan kehadiran di sekolah untuk menjaga keterlibatan akademik yang konsisten.")

    if not suggestions:
        return ("Kondisi belajar dan stres tampak seimbang. Pertahankan pola tidur, waktu belajar, dan dukungan sekolah yang sudah baik.")

    return " ".join(suggestions)

# -----------------------------
# Header & Navigation
# -----------------------------
st.header("SSPI — Student Stress & Performance Insights")
st.caption("Alat sederhana untuk memahami keseimbangan antara stres dan performa belajar siswa.")
section = st.sidebar.radio("Navigasi", ["Input & Hasil", "Evaluasi & Saran"], index=0)

# -----------------------------
# SECTION 1 — INPUT & HASIL
# -----------------------------
if section == "Input & Hasil":
    st.subheader("Input & Hasil")

    st.markdown('<div class="section-title">Rutinitas Harian</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        study = st.slider("Jam Belajar / Hari", 0.0, 8.0, 3.0, 0.5, help="Waktu belajar mandiri di luar jam sekolah.")
    with c2:
        sleep = st.slider("Jam Tidur / Hari", 6.0, 11.0, 9.5, 0.5, help="Durasi tidur rata-rata setiap malam.")

    st.markdown('<div class="section-title">Lingkungan Sekolah</div>', unsafe_allow_html=True)
    c3, c4 = st.columns(2)
    with c3:
        attend = st.slider("Kehadiran (%)", 50, 100, 95, 1, help="Persentase kehadiran siswa di sekolah.")
    with c4:
        classsize = st.slider("Ukuran Kelas", 15, 45, 28, 1, help="Jumlah siswa rata-rata dalam satu kelas.")

    st.markdown('<div class="section-title">Dukungan & Beban Belajar</div>', unsafe_allow_html=True)
    c5, c6 = st.columns(2)
    with c5:
        support = st.slider("Dukungan Sekolah (0–100)", 0, 100, 70, 5, help="Konselor, kegiatan positif, komunikasi orang tua.")
    with c6:
        workload = st.slider("Beban Tugas (0–100)", 0, 100, 50, 5, help="PR, ujian, proyek, dll.")

    vals = {"StudyHours": study, "SleepHours": sleep, "Attendance": float(attend), "ClassSize": float(classsize), "SchoolSupport": float(support), "Workload": float(workload)}

    perf = perf_component(vals)
    stress = stress_component(vals)
    weights = {k: 1 for k in vals}
    perf_score = weighted_score(perf, weights)
    stress_score = weighted_score(stress, weights)

    st.session_state["sspi_data"] = {"vals": vals, "perf": perf, "stress": stress, "perf_score": perf_score, "stress_score": stress_score}

    st.markdown("---")
    cA, cB, cC = st.columns(3)
with cA:
    st.markdown('<div class="kpi">', unsafe_allow_html=True)
    st.metric("Kesiapan Belajar", f"{perf_score:.1f}")
    st.markdown('</div>', unsafe_allow_html=True)
with cB:
    st.markdown('<div class="kpi">', unsafe_allow_html=True)
    st.metric("Kesehatan Stres", f"{stress_score:.1f}")
    st.markdown('</div>', unsafe_allow_html=True)
with cC:
    overall = min(perf_score, stress_score)
    st.markdown('<div class="kpi">', unsafe_allow_html=True)
    st.metric("Kesimpulan Umum", traffic_light(overall))
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

with st.container():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    fig_g = go.Figure(go.Indicator(
        mode="gauge+number",
        value=overall,
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'thickness': 0.3},
            'steps': [
                {'range': [0, 50], 'color': '#f2cccc'},
                {'range': [50, 75], 'color': '#fff1cc'},
                {'range': [75, 100], 'color': '#d9f7be'}
            ]
        },
        title={'text': 'Keseimbangan Umum'}
    ))
    fig_g.update_layout(height=240, margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig_g, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------
# SECTION 2 — EVALUASI & SARAN
# -----------------------------
elif section == "Evaluasi & Saran":
    st.subheader("Evaluasi & Saran")
    data = st.session_state.get("sspi_data")
    if not data:
        st.info("Silakan isi bagian 'Input & Hasil' terlebih dahulu.")
        st.stop()

    vals = data["vals"]; perf = data["perf"]; stress = data["stress"]

    radar_df = pd.DataFrame({
        'Faktor': list(vals.keys()),
        'Performa': [perf[k] for k in vals],
        'KesehatanStres': [stress[k] for k in vals],
    })
    fig_radar = px.line_polar(radar_df, r='Performa', theta='Faktor', line_close=True, range_r=[0,100])
    fig_radar.add_trace(px.line_polar(radar_df, r='KesehatanStres', theta='Faktor', line_close=True).data[0])
    fig_radar.update_layout(height=420, legend=dict(orientation='h', yanchor='bottom', y=-0.15, xanchor='center', x=0.5))
    st.plotly_chart(fig_radar, use_container_width=True)

    strength_df = pd.DataFrame({
        'Faktor': list(vals.keys()),
        'Performa': [perf[k] for k in vals],
        'KesehatanStres': [stress[k] for k in vals],
    })
    strength_df['Gabungan'] = (strength_df['Performa'] + strength_df['KesehatanStres']) / 2.0
    strength_df = strength_df.sort_values('Gabungan', ascending=False)
    fig_bar = px.bar(strength_df.melt(id_vars='Faktor', value_vars=['Performa','KesehatanStres'], var_name='Dimensi', value_name='Skor'),
                     x='Faktor', y='Skor', color='Dimensi', barmode='group', height=420,
                     title='Kekuatan Faktor — Semakin Tinggi Semakin Baik')
    fig_bar.update_layout(xaxis_tickangle=-20, margin=dict(l=10, r=10, t=50, b=100))
    st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("### Saran")
    paragraph = build_recommendation(vals)
    st.write(paragraph)

st.markdown("---")
st.caption("SSPI membantu memahami keseimbangan antara stres dan performa siswa. Gunakan hasil ini sebagai refleksi, bukan diagnosis.")

