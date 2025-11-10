# =============================================
# StudiSantuy — Insight Stres & Performa
# Dashboard (Weather Forecast-style), gradient + deep shadow
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
st.set_page_config(page_title="StudiSantuy — Insight Stres & Performa", layout="wide")

# -----------------------------
# THEME (Merah–Putih–Biru) + Enhanced Gradient & Shadows
# -----------------------------
PRIMARY, SECONDARY, ACCENT = "#d90429", "#1d3557", "#457b9d"

st.markdown(f"""
<style>
/* ===== Background: layered gradient + soft pattern + gradient blobs ===== */
[data-testid="stAppViewContainer"] {{
  background:
    radial-gradient(1200px 600px at -10% 0%, rgba(69,123,157,0.10), transparent 60%),
    radial-gradient(900px 500px at 110% 10%, rgba(217,4,41,0.08), transparent 55%),
    radial-gradient(700px 500px at 30% 95%, rgba(29,53,87,0.08), transparent 60%),
    linear-gradient(180deg, #f3f7ff 0%, #ffffff 70%);
}}
/* Tricolor ribbon */
.top-ribbon {{
  height: 10px; width: 100%;
  background: linear-gradient(90deg, {PRIMARY} 0%, #ffffff 50%, {SECONDARY} 100%);
  margin: 0 0 16px 0; border-radius: 10px;
  box-shadow: 0 8px 24px rgba(29,53,87,0.15);
}}
/* Sidebar */
[data-testid="stSidebar"] {{
  background: {SECONDARY};
  color: #e2e8f0;
  border-top-right-radius: 18px; border-bottom-right-radius: 18px;
  box-shadow: 6px 0 24px rgba(15,23,42,0.25);
}}
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] label {{ color: #e2e8f0 !important; }}

/* ===== Header (card) — stronger shadow, subtle gradient ===== */
.header-card {{
  background: linear-gradient(135deg, #ffffff 0%, #f7fbff 100%);
  border: 1px solid #e6eef7;
  border-radius: 16px;
  padding: 16px 20px;
  box-shadow: 0 10px 28px rgba(15,23,42,0.10), 0 2px 8px rgba(15,23,42,0.06);
}}
.brand {{
  font-weight: 900; font-size: 1.35rem;
  background: linear-gradient(90deg, {SECONDARY} 0%, {ACCENT} 60%, {SECONDARY} 100%);
  -webkit-background-clip: text; background-clip: text; color: transparent;
  letter-spacing: .3px;
}}
.subbrand {{ color: #64748b; font-weight: 500; }}

/* Section title */
.section-title {{
  font-weight: 800; color: #0f172a; font-size: 1.1rem; margin: 0.35rem 0 0.7rem 0;
  border-left: 7px solid {PRIMARY}; padding-left: 12px;
}}

/* Cards & KPI — deeper shadows */
.card {{
  background: #ffffff;
  border: 1px solid #e7edf5;
  border-radius: 14px;
  padding: 14px;
  box-shadow:
    0 14px 28px rgba(15,23,42,0.10),
    0 6px 12px rgba(15,23,42,0.06);
}}
.kpi {{
  background: linear-gradient(180deg,#ffffff 0%, #fafcff 100%);
  border: 1px solid #e7edf5;
  border-radius: 14px;
  padding: 12px;
  text-align: center;
  box-shadow:
    0 10px 22px rgba(29,53,87,0.10),
    0 3px 8px rgba(29,53,87,0.06);
  border-top: 5px solid {ACCENT};
}}
.kpi h4 {{ margin: 0 0 6px 0; color: {SECONDARY}; font-weight: 800; }}
.kpi .val {{ font-size: 1.65rem; font-weight: 900; color: {PRIMARY}; }}

/* Chart wrapper — left accent + shadow */
.chart {{
  background: #ffffff; border: 1px solid #e7edf5; border-radius: 14px;
  padding: 12px; border-left: 5px solid {PRIMARY};
  box-shadow: 0 12px 26px rgba(15,23,42,0.10), 0 3px 8px rgba(15,23,42,0.05);
}}

/* Headings */
h1, h2, h3 {{ color: #0f172a; }}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Simple Rules/"Model"
# -----------------------------
OPT = {"StudyHours": 3.0, "SleepHours": 9.5, "ClassSize": 28.0}
clip = lambda x: float(np.clip(x, 0.0, 100.0))

def perf_component(v: Dict[str,float]):
    return {
        "StudyHours": clip(100*np.exp(-((v["StudyHours"]-OPT["StudyHours"])**2)/(2*(1.5**2)))) ,
        "SleepHours": clip(100*np.exp(-((v["SleepHours"]-OPT["SleepHours"])**2)/(2*(1.0**2)))) ,
        "Attendance": v["Attendance"],
        "ClassSize": clip(100*(1-np.clip((v["ClassSize"]-15)/(45-15),0,1))),
        "SchoolSupport": v["SchoolSupport"],
        "Workload": clip(100*(1 - v["Workload"]/100))
    }

def stress_component(v: Dict[str,float]):
    study_good = clip(100 - 100*(1 - np.exp(-((v["StudyHours"]-OPT["StudyHours"])**2)/(2*(1.5**2)))))
    return {
        "StudyHours": study_good,
        "SleepHours": clip(100*(1 - np.clip(abs(v["SleepHours"]-OPT["SleepHours"])/2.0,0,1))),
        "Attendance": v["Attendance"],
        "ClassSize": clip(100*(1 - np.clip((v["ClassSize"]-15)/(45-15),0,1))),
        "SchoolSupport": v["SchoolSupport"],
        "Workload": clip(100*(1 - v["Workload"]/100))
    }

def weighted_score(c: Dict[str,float]): return float(sum(c.values())/len(c))
def traffic_light(s: float): return "Baik" if s>=75 else "Perlu Perhatian" if s>=50 else "Risiko Tinggi"

def recommendation(v: Dict[str,float]) -> str:
    s=[]
    if v["SleepHours"]<8.5: s.append("Kamu perlu tidur yang cukup, idealnya sekitar 9–10 jam per hari.")
    if v["Workload"]>70: s.append("Kurangi beban tugas agar waktu istirahat dan rekreasi lebih seimbang.")
    if v["ClassSize"]>35: s.append("Ukuran kelas yang besar dapat meningkatkan tekanan belajar, pertimbangkan pengelompokan ulang kelas.")
    if v["SchoolSupport"]<60: s.append("Tingkatkan dukungan sekolah melalui kegiatan positif dan layanan konseling.")
    if v["StudyHours"]<2.0: s.append("Tambahkan waktu belajar mandiri sekitar 15–30 menit setiap hari.")
    if v["Attendance"]<90: s.append("Tingkatkan kehadiran di sekolah untuk menjaga keterlibatan akademik.")
    return " ".join(s) if s else "Kondisi belajar dan stres tampak seimbang. Pertahankan pola tidur dan belajar yang sudah baik."

def title(text: str):
    st.markdown(f'<div class="section-title">{text}</div>', unsafe_allow_html=True)

# -----------------------------
# Header (Branding Gen-Z)
# -----------------------------
st.markdown('<div class="top-ribbon"></div>', unsafe_allow_html=True)
st.markdown("""
<div class="header-card">
  <div class="brand">StudiSantuy</div>
  <div class="subbrand">Insight Stres & Performa</div>
</div>
""", unsafe_allow_html=True)
st.caption("Alat sederhana untuk memahami keseimbangan antara stres dan performa belajar siswa.")

# Sidebar nav
section = st.sidebar.radio("Navigasi", ["Input & Hasil", "Evaluasi & Saran"], index=0)

# -----------------------------
# Section 1 — Input & Hasil
# -----------------------------
if section=="Input & Hasil":
    title("Rutinitas Harian")
    c1,c2 = st.columns(2)
    with c1: study = st.slider("Jam Belajar / Hari", 0.0, 8.0, 3.0, 0.5)
    with c2: sleep  = st.slider("Jam Tidur / Hari", 6.0, 11.0, 9.5, 0.5)

    title("Lingkungan Sekolah")
    c3,c4 = st.columns(2)
    with c3: attend    = st.slider("Kehadiran (%)", 50, 100, 95, 1)
    with c4: classsize = st.slider("Ukuran Kelas", 15, 45, 28, 1)

    title("Dukungan & Beban Belajar")
    c5,c6 = st.columns(2)
    with c5: support  = st.slider("Dukungan Sekolah (0–100)", 0, 100, 70, 5)
    with c6: workload = st.slider("Beban Tugas (0–100)", 0, 100, 50, 5)

    vals   = {"StudyHours":study,"SleepHours":sleep,"Attendance":attend,"ClassSize":classsize,"SchoolSupport":support,"Workload":workload}
    perf   = perf_component(vals)
    stress = stress_component(vals)
    perf_score, stress_score = weighted_score(perf), weighted_score(stress)
    overall = min(perf_score, stress_score)
    st.session_state["data"] = {"vals":vals,"perf":perf,"stress":stress,"perf_score":perf_score,"stress_score":stress_score,"overall":overall}

    # KPI tiles
    k1,k2,k3 = st.columns(3)
    k1.markdown(f'<div class="kpi"><h4>Kesiapan Belajar</h4><div class="val">{perf_score:.1f}</div></div>', unsafe_allow_html=True)
    k2.markdown(f'<div class="kpi"><h4>Kesehatan Stres</h4><div class="val">{stress_score:.1f}</div></div>', unsafe_allow_html=True)
    k3.markdown(f'<div class="kpi"><h4>Kesimpulan Umum</h4><div class="val">{traffic_light(overall)}</div></div>', unsafe_allow_html=True)

    # Gauge
    st.markdown('<div class="card">', unsafe_allow_html=True)
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=overall,
        gauge={{
            'axis': {{'range':[0,100]}},
            'bar': {{'thickness':0.3, 'color': ACCENT}},
            'steps': [
                {{'range':[0,50],  'color':'#fde2e2'}},
                {{'range':[50,75], 'color':'#fff4cc'}},
                {{'range':[75,100],'color':'#d9eaf7'}}
            ]
        }},
        title={{'text':'Keseimbangan Umum'}}
    ))
    fig.update_layout(height=230, margin=dict(l=10,r=10,t=40,b=10))
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------
# Section 2 — Evaluasi & Saran
# -----------------------------
else:
    data = st.session_state.get("data")
    if not data:
        st.info("Silakan isi bagian 'Input & Hasil' terlebih dahulu.")
        st.stop()

    vals, perf, stress = data["vals"], data["perf"], data["stress"]

    # Radar
    radar = pd.DataFrame({
        'Faktor': list(vals.keys()),
        'Performa': [perf[k] for k in vals],
        'KesehatanStres': [stress[k] for k in vals],
    })
    fig_r = px.line_polar(radar, r='Performa', theta='Faktor', line_close=True, range_r=[0,100],
                          color_discrete_sequence=[PRIMARY])
    fig_r.add_trace(px.line_polar(radar, r='KesehatanStres', theta='Faktor', line_close=True,
                                  color_discrete_sequence=[SECONDARY]).data[0])
    fig_r.update_layout(height=420, legend=dict(orientation='h', yanchor='bottom', y=-0.15, xanchor='center', x=0.5),
                        polar=dict(radialaxis=dict(showline=True, linewidth=1, gridcolor="#e5e7eb")))
    st.markdown('<div class="chart">', unsafe_allow_html=True)
    st.plotly_chart(fig_r, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Bar — strength
    strength = pd.DataFrame({
        'Faktor': list(vals.keys()),
        'Performa': [perf[k] for k in vals],
        'KesehatanStres': [stress[k] for k in vals],
    })
    strength['Gabungan'] = (strength['Performa'] + strength['KesehatanStres'])/2.0
    strength = strength.sort_values('Gabungan', ascending=False)
    melt = strength.melt(id_vars='Faktor', value_vars=['Performa','KesehatanStres'],
                         var_name='Dimensi', value_name='Skor')
    fig_b = px.bar(melt, x='Faktor', y='Skor', color='Dimensi', barmode='group', height=400,
                   color_discrete_map={'Performa':PRIMARY, 'KesehatanStres':SECONDARY})
    st.markdown('<div class="chart">', unsafe_allow_html=True)
    st.plotly_chart(fig_b, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Sensitivity Explorer
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("**Sensitivity Explorer**")
    factor = st.selectbox("Pilih faktor untuk disimulasikan",
                          ["Jam Tidur / Hari", "Jam Belajar / Hari", "Kehadiran (%)", "Ukuran Kelas", "Dukungan Sekolah (0–100)", "Beban Tugas (0–100)"], index=0)
    key_map = {
        "Jam Belajar / Hari": ("StudyHours", np.linspace(0, 8, 33)),
        "Jam Tidur / Hari": ("SleepHours", np.linspace(6, 11, 26)),
        "Kehadiran (%)": ("Attendance", np.linspace(50, 100, 26)),
        "Ukuran Kelas": ("ClassSize", np.linspace(15, 45, 31)),
        "Dukungan Sekolah (0–100)": ("SchoolSupport", np.linspace(0, 100, 26)),
        "Beban Tugas (0–100)": ("Workload", np.linspace(0, 100, 26)),
    }
    key, grid = key_map[factor]
    base = vals.copy()
    perf_list, stress_list = [], []
    for g in grid:
        v = base.copy(); v[key] = float(g)
        perf_list.append(weighted_score(perf_component(v)))
        stress_list.append(weighted_score(stress_component(v)))
    sim = pd.DataFrame({factor: grid, "Kesiapan Belajar": perf_list, "Kesehatan Stres": stress_list})
    fig_s = px.line(sim, x=factor, y=["Kesiapan Belajar", "Kesehatan Stres"],
                    color_discrete_map={"Kesiapan Belajar":PRIMARY, "Kesehatan Stres":SECONDARY},
                    height=360, title="Dampak perubahan faktor terhadap skor")
    st.plotly_chart(fig_s, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Saran
    st.markdown('<div class="card"><b>Saran</b></div>', unsafe_allow_html=True)
    st.write(recommendation(vals))

    # Evidence & References
    st.markdown('<div class="card"><b>Evidence & References</b></div>', unsafe_allow_html=True)
    st.markdown("""
- Jam tidur anak usia sekolah 9–12 jam/hari — CDC & AASM  
  - https://www.cdc.gov/sleep/about/index.html  
  - https://aasm.org/resources/pdf/pediatricsleepdurationconsensus.pdf
- Ukuran kelas & rasio siswa–guru — OECD  
  - https://www.oecd.org/en/topics/sub-issues/class-size-and-student-teacher-ratios.html
- Beban tugas & burnout — APA, Stanford  
  - https://www.apa.org/monitor/2016/03/homework  
  - https://news.stanford.edu/stories/2014/03/too-much-homework-031014
- Kehadiran & capaian akademik — NZCER  
  - https://www.nzcer.org.nz/news-and-blogs/student-attendance-engagement-and-achievement-sustaining-change
    """)

# Footer
st.markdown("---")
st.caption("StudiSantuy membantu memahami keseimbangan antara stres dan performa belajar. Gunakan hasil ini sebagai refleksi, bukan diagnosis.")

