# =============================================
# SSPI — Student Stress & Performance Insights
# Dashboard (Weather Forecast-style) tanpa Search Bar
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
st.set_page_config(page_title="SSPI — Student Stress & Performance Insights", layout="wide")

# -----------------------------
# THEME (Red–White–Blue) + Forecast UI
# -----------------------------
PRIMARY, SECONDARY, ACCENT = "#d90429", "#1d3557", "#457b9d"

st.markdown(f"""
<style>
[data-testid="stAppViewContainer"] {{
  background-image:
    linear-gradient(180deg, #ffffffcc 0%, #ffffff 30%),
    repeating-linear-gradient(45deg, rgba(29,53,87,0.045) 0px, rgba(29,53,87,0.045) 2px, transparent 3px, transparent 8px),
    linear-gradient(180deg,#e8f0fe 0%, #ffffff 60%);
}}
.top-ribbon {{
  height: 8px; width: 100%;
  background: linear-gradient(90deg, {PRIMARY} 0%, #ffffff 50%, {SECONDARY} 100%);
  margin: 0 0 12px 0; border-radius: 8px;
}}
[data-testid="stSidebar"] {{
  background: {SECONDARY}; color: #e2e8f0; border-top-right-radius: 16px; border-bottom-right-radius: 16px;
}}
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] label {{ color: #e2e8f0 !important; }}
.header-card {{
  background: #ffffff; border: 1px solid #e5e7eb; border-radius: 14px;
  padding: 14px 18px; box-shadow: 0 6px 18px rgba(0,0,0,0.05);
}}
.brand {{ font-weight: 800; font-size: 1.25rem; color: {SECONDARY}; }}
.subbrand {{ font-weight: 500; font-size: 0.9rem; color: #6b7280; }}
.section-title {{
  font-weight: 800; color: #0f172a; font-size: 1.1rem; margin: 0.25rem 0 0.6rem 0;
  border-left: 6px solid {PRIMARY}; padding-left: 10px;
}}
.card {{
  background: #ffffff; border: 1px solid #e5e7eb; border-radius: 12px;
  padding: 14px; box-shadow: 0 2px 10px rgba(15,23,42,0.06);
}}
.kpi {{
  background: #ffffff; border: 1px solid #e5e7eb; border-radius: 12px;
  padding: 10px 12px; box-shadow: 0 2px 8px rgba(15,23,42,0.05);
  border-top: 4px solid {ACCENT}; text-align: center;
}}
.kpi h4 {{ margin: 0 0 6px 0; color: {SECONDARY}; font-weight: 700; }}
.kpi .val {{ font-size: 1.6rem; font-weight: 800; color: {PRIMARY}; }}
.chart {{
  background: #ffffff; border: 1px solid #e5e7eb; border-radius: 12px;
  padding: 10px; box-shadow: 0 2px 8px rgba(15,23,42,0.04);
  border-left: 4px solid {PRIMARY};
}}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Simple Model / Rules
# -----------------------------
OPT = {"StudyHours": 3.0, "SleepHours": 9.5, "ClassSize": 28.0}
clip = lambda x: float(np.clip(x, 0.0, 100.0))

def perf_component(v):
    return {
        "StudyHours": clip(100 * np.exp(-((v["StudyHours"]-OPT["StudyHours"])**2)/(2*(1.5**2)))),
        "SleepHours": clip(100 * np.exp(-((v["SleepHours"]-OPT["SleepHours"])**2)/(2*(1.0**2)))),
        "Attendance": v["Attendance"],
        "ClassSize": clip(100 * (1 - np.clip((v["ClassSize"]-15)/(45-15),0,1))),
        "SchoolSupport": v["SchoolSupport"],
        "Workload": clip(100 * (1 - v["Workload"]/100))
    }

def stress_component(v):
    study_good = clip(100 - 100 * (1 - np.exp(-((v["StudyHours"]-OPT["StudyHours"])**2)/(2*(1.5**2)))))
    return {
        "StudyHours": study_good,
        "SleepHours": clip(100 * (1 - np.clip(abs(v["SleepHours"]-OPT["SleepHours"])/2.0, 0, 1))),
        "Attendance": v["Attendance"],
        "ClassSize": clip(100 * (1 - np.clip((v["ClassSize"]-15)/(45-15), 0, 1))),
        "SchoolSupport": v["SchoolSupport"],
        "Workload": clip(100 * (1 - v["Workload"]/100))
    }

def weighted_score(c): return float(sum(c.values()) / len(c))
def traffic_light(score): return "Baik" if score>=75 else "Perlu Perhatian" if score>=50 else "Risiko Tinggi"

def recommendation(v):
    s=[]
    if v["SleepHours"]<8.5: s.append("Kamu perlu tidur yang cukup, idealnya sekitar 9–10 jam per hari.")
    if v["Workload"]>70: s.append("Kurangi beban tugas agar waktu istirahat dan rekreasi lebih seimbang.")
    if v["ClassSize"]>35: s.append("Ukuran kelas yang besar dapat meningkatkan tekanan belajar, pertimbangkan pengelompokan ulang kelas.")
    if v["SchoolSupport"]<60: s.append("Tingkatkan dukungan sekolah melalui kegiatan positif dan layanan konseling.")
    if v["StudyHours"]<2: s.append("Tambahkan waktu belajar mandiri sekitar 15–30 menit setiap hari.")
    if v["Attendance"]<90: s.append("Tingkatkan kehadiran di sekolah untuk menjaga keterlibatan akademik.")
    return " ".join(s) if s else "Kondisi belajar dan stres tampak seimbang. Pertahankan pola tidur dan belajar yang sudah baik."

# -----------------------------
# Header
# -----------------------------
st.markdown('<div class="top-ribbon"></div>', unsafe_allow_html=True)
st.markdown(f"""
<div class="header-card">
  <div class="brand">SSPI Forecast</div>
  <div class="subbrand">Student Stress & Performance Insights</div>
</div>
""", unsafe_allow_html=True)
st.caption("Alat sederhana untuk memahami keseimbangan antara stres dan performa belajar siswa.")

section = st.sidebar.radio("Navigasi", ["Input & Hasil", "Evaluasi & Saran"], index=0)

# -----------------------------
# Section 1 — Input & Hasil
# -----------------------------
if section=="Input & Hasil":
    st.markdown('<div class="section-title">Rutinitas Harian</div>', unsafe_allow_html=True)
    c1,c2=st.columns(2)
    with c1: study=st.slider("Jam Belajar / Hari",0.0,8.0,3.0,0.5)
    with c2: sleep=st.slider("Jam Tidur / Hari",6.0,11.0,9.5,0.5)

    st.markdown('<div class="section-title">Lingkungan Sekolah</div>', unsafe_allow_html=True)
    c3,c4=st.columns(2)
    with c3: attend=st.slider("Kehadiran (%)",50,100,95,1)
    with c4: classsize=st.slider("Ukuran Kelas",15,45,28,1)

    st.markdown('<div class="section-title">Dukungan & Beban Belajar</div>', unsafe_allow_html=True)
    c5,c6=st.columns(2)
    with c5: support=st.slider("Dukungan Sekolah (0–100)",0,100,70,5)
    with c6: workload=st.slider("Beban Tugas (0–100)",0,100,50,5)

    vals={"StudyHours":study,"SleepHours":sleep,"Attendance":attend,"ClassSize":classsize,"SchoolSupport":support,"Workload":workload}
    perf,stress=perf_component(vals),stress_component(vals)
    perf_score,stress_score=weighted_score(perf),weighted_score(stress)
    overall=min(perf_score,stress_score)
    st.session_state["data"]={"vals":vals,"perf":perf,"stress":stress,"perf_score":perf_score,"stress_score":stress_score,"overall":overall}

    k1,k2,k3=st.columns(3)
    k1.markdown(f'<div class="kpi"><h4>Kesiapan Belajar</h4><div class="val">{perf_score:.1f}</div></div>',unsafe_allow_html=True)
    k2.markdown(f'<div class="kpi"><h4>Kesehatan Stres</h4><div class="val">{stress_score:.1f}</div></div>',unsafe_allow_html=True)
    k3.markdown(f'<div class="kpi"><h4>Kesimpulan Umum</h4><div class="val">{traffic_light(overall)}</div></div>',unsafe_allow_html=True)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    fig=go.Figure(go.Indicator(mode="gauge+number",value=overall,
        gauge={'axis':{'range':[0,100]},'bar':{'color':ACCENT},
               'steps':[{'range':[0,50],'color':'#fde2e2'},{'range':[50,75],'color':'#fff4cc'},{'range':[75,100],'color':'#d9eaf7'}]},
        title={'text':'Keseimbangan Umum'}))
    fig.update_layout(height=230,margin=dict(l=10,r=10,t=40,b=10))
    st.plotly_chart(fig,use_container_width=True)
    st.markdown('</div>',unsafe_allow_html=True)

# -----------------------------
# Section 2 — Evaluasi & Saran
# -----------------------------
else:
    data=st.session_state.get("data")
    if not data: st.info("Silakan isi bagian 'Input & Hasil' terlebih dahulu."); st.stop()

    vals,perf,stress=data["vals"],data["perf"],data["stress"]
    radar=pd.DataFrame({'Faktor':list(vals.keys()),'Performa':[perf[k] for k in vals],'KesehatanStres':[stress[k] for k in vals]})
    fig_r=px.line_polar(radar,r='Performa',theta='Faktor',line_close=True,range_r=[0,100],color_discrete_sequence=[PRIMARY])
    fig_r.add_trace(px.line_polar(radar,r='KesehatanStres',theta='Faktor',line_close=True,color_discrete_sequence=[SECONDARY]).data[0])
    fig_r.update_layout(height=420,legend=dict(orientation='h',yanchor='bottom',y=-0.15,xanchor='center',x=0.5))
    st.markdown('<div class="chart">',unsafe_allow_html=True); st.plotly_chart(fig_r,use_container_width=True); st.markdown('</div>',unsafe_allow_html=True)

    strength=pd.DataFrame({'Faktor':list(vals.keys()),'Performa':[perf[k] for k in vals],'KesehatanStres':[stress[k] for k in vals]})
    strength['Gabungan']=(strength['Performa']+strength['KesehatanStres'])/2; strength=strength.sort_values('Gabungan',ascending=False)
    melt=strength.melt(id_vars='Faktor',value_vars=['Performa','KesehatanStres'],var_name='Dimensi',value_name='Skor')
    fig_b=px.bar(melt,x='Faktor',y='Skor',color='Dimensi',barmode='group',height=400,color_discrete_map={'Performa':PRIMARY,'KesehatanStres':SECONDARY})
    st.markdown('<div class="chart">',unsafe_allow_html=True); st.plotly_chart(fig_b,use_container_width=True); st.markdown('</div>',unsafe_allow_html=True)

    st.markdown('<div class="card"><b>Saran</b></div>',unsafe_allow_html=True)
    st.write(recommendation(vals))

    st.markdown('<div class="card"><b>Evidence & References</b></div>',unsafe_allow_html=True)
    st.markdown("""
- Jam tidur anak usia sekolah 9–12 jam/hari — CDC & AASM Consensus  
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

st.markdown("---")
st.caption("SSPI membantu memahami keseimbangan antara stres dan performa siswa. Gunakan hasil ini sebagai refleksi, bukan diagnosis.")
