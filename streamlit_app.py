from typing import Dict
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# ---------- App Config ----------
st.set_page_config(page_title="Belajar Santuy Dulu (BETUL)", layout="wide")

# ---------- Theme & Styles ----------
PRIMARY, SECONDARY, ACCENT = "#d90429", "#1d3557", "#457b9d"
st.markdown(f"""
<style>
[data-testid="stAppViewContainer"] {{
  background:
    radial-gradient(1000px 600px at -10% 0%, rgba(69,123,157,0.08), transparent 60%),
    radial-gradient(800px 500px at 110% 10%, rgba(217,4,41,0.08), transparent 55%),
    linear-gradient(180deg, #f5f8ff 0%, #ffffff 75%);
}}
.top-ribbon {{
  height: 10px; width: 100%;
  background: linear-gradient(90deg, {PRIMARY} 0%, #ffffff 50%, {SECONDARY} 100%);
  border-radius: 10px; box-shadow: 0 6px 20px rgba(15,23,42,0.15);
}}
[data-testid="stSidebar"] {{
  background: {SECONDARY}; color: #e2e8f0;
  border-top-right-radius: 16px; border-bottom-right-radius: 16px;
  box-shadow: 6px 0 20px rgba(15,23,42,0.25);
}}
.header-card {{
  background: linear-gradient(135deg, #ffffff 0%, #f7fbff 100%);
  border: 1px solid #e6eef7; border-radius: 16px;
  padding: 16px 20px; box-shadow: 0 8px 24px rgba(15,23,42,0.12);
}}
.brand {{
  font-weight: 900; font-size: 1.4rem;
  background: linear-gradient(90deg, {SECONDARY} 0%, {ACCENT} 60%, {SECONDARY} 100%);
  -webkit-background-clip: text; background-clip: text; color: transparent;
}}
.subbrand {{ color: #64748b; font-weight: 600; }}
.section-title {{
  font-weight: 800; color: #0f172a; font-size: 1.1rem;
  border-left: 6px solid {PRIMARY}; padding-left: 10px;
  margin: 0.4rem 0 0.7rem 0;
}}
.card {{
  background: #ffffff; border: 1px solid #e7edf5; border-radius: 14px;
  padding: 14px; box-shadow: 0 12px 30px rgba(15,23,42,0.08);
}}
.kpi {{
  background: #ffffff; border: 1px solid #e7edf5; border-radius: 14px;
  padding: 12px; text-align: center; border-top: 5px solid {ACCENT};
  box-shadow: 0 10px 20px rgba(15,23,42,0.08);
}}
.kpi h4 {{ color: {SECONDARY}; font-weight: 800; margin-bottom: 6px; }}
.kpi .val {{ font-size: 1.6rem; font-weight: 900; color: {PRIMARY}; }}
.chart {{
  background: #ffffff; border: 1px solid #e7edf5; border-radius: 14px;
  padding: 12px; border-left: 5px solid {PRIMARY};
  box-shadow: 0 12px 28px rgba(15,23,42,0.08);
}}
.author-card {{
  background: linear-gradient(135deg, #ffffff 0%, #f7fbff 100%);
  border: 1px solid #e6eef7; border-radius: 16px;
  padding: 14px 16px; box-shadow: 0 8px 24px rgba(15,23,42,0.12);
  display: flex; align-items: center; gap: 12px;
}}
.author-meta {{ line-height: 1.2; }}
.author-name {{ font-weight: 800; color: #0f172a; font-size: 1.02rem; }}
.author-id {{ color: #64748b; font-weight: 600; font-size: 0.9rem; }}
</style>
""", unsafe_allow_html=True)

# ---------- Simple Model ----------
OPT = {"StudyHours": 3.0, "SleepHours": 9.5, "ClassSize": 28.0}
clip = lambda x: float(np.clip(x, 0, 100))

def perf_component(v: Dict[str, float]) -> Dict[str, float]:
    return {
        "StudyHours": clip(100*np.exp(-((v["StudyHours"]-OPT["StudyHours"])**2)/(2*(1.5**2)))) ,
        "SleepHours": clip(100*np.exp(-((v["SleepHours"]-OPT["SleepHours"])**2)/(2*(1.0**2)))) ,
        "Attendance": v["Attendance"],
        "ClassSize": clip(100*(1-np.clip((v["ClassSize"]-15)/(45-15),0,1))),
        "SchoolSupport": v["SchoolSupport"],
        "Workload": clip(100*(1 - v["Workload"]/100))
    }

def stress_component(v: Dict[str, float]) -> Dict[str, float]:
    study_good = clip(100 - 100*(1 - np.exp(-((v["StudyHours"]-OPT["StudyHours"])**2)/(2*(1.5**2)))))
    return {
        "StudyHours": study_good,
        "SleepHours": clip(100*(1 - np.clip(abs(v["SleepHours"]-OPT["SleepHours"])/2.0,0,1))),
        "Attendance": v["Attendance"],
        "ClassSize": clip(100*(1-np.clip((v["ClassSize"]-15)/(45-15),0,1))),
        "SchoolSupport": v["SchoolSupport"],
        "Workload": clip(100*(1 - v["Workload"]/100))
    }

def weighted_score(c: Dict[str, float]) -> float:
    return float(sum(c.values())/len(c))

def traffic_light(s: float) -> str:
    return "Baik" if s >= 75 else ("Perlu Perhatian" if s >= 50 else "Risiko Tinggi")

def recommendation(v: Dict[str, float]) -> str:
    s = []
    if v["SleepHours"] < 8.5: s.append("Kamu perlu tidur yang cukup, idealnya sekitar 9–10 jam per hari.")
    if v["Workload"] > 70: s.append("Kurangi beban tugas agar waktu istirahat dan rekreasi lebih seimbang.")
    if v["ClassSize"] > 35: s.append("Ukuran kelas yang besar dapat meningkatkan tekanan belajar, pertimbangkan pengelompokan ulang kelas.")
    if v["SchoolSupport"] < 60: s.append("Tingkatkan dukungan sekolah melalui kegiatan positif dan layanan konseling.")
    if v["StudyHours"] < 2.0: s.append("Tambahkan waktu belajar mandiri sekitar 15–30 menit setiap hari.")
    if v["Attendance"] < 90: s.append("Tingkatkan kehadiran di sekolah untuk menjaga keterlibatan akademik.")
    return " ".join(s) if s else "Kondisi belajar dan stres tampak seimbang. Pertahankan pola tidur dan belajar yang sudah baik."

def section_title(text: str) -> None:
    st.markdown(f'<div class="section-title">{text}</div>', unsafe_allow_html=True)

# ---------- Header ----------
st.markdown('<div class="top-ribbon"></div>', unsafe_allow_html=True)
left, spacer, right = st.columns([1.4, 0.1, 1.1])

with left:
    st.markdown("""
    <div class="header-card">
      <div class="brand">Belajar Santuy Dulu (BETUL)</div>
      <div class="subbrand">Insight Stres & Performa Siswa</div>
    </div>
    """, unsafe_allow_html=True)

with right:
    stickman_svg = """
    <svg width="52" height="52" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg" aria-label="stickman">
      <circle cx="32" cy="18" r="10" stroke="#1d3557" stroke-width="2.5" fill="#ffffff"/>
      <circle cx="28" cy="16.5" r="1.6" fill="#1d3557"/>
      <circle cx="36" cy="16.5" r="1.6" fill="#1d3557"/>
      <path d="M27 20c2 3 8 3 10 0" stroke="#1d3557" stroke-width="2" stroke-linecap="round"/>
      <line x1="32" y1="28" x2="32" y2="44" stroke="#1d3557" stroke-width="2.5"/>
      <line x1="32" y1="32" x2="22" y2="38" stroke="#1d3557" stroke-width="2.5" stroke-linecap="round"/>
      <line x1="32" y1="32" x2="42" y2="38" stroke="#1d3557" stroke-width="2.5" stroke-linecap="round"/>
      <line x1="32" y1="44" x2="24" y2="56" stroke="#1d3557" stroke-width="2.5" stroke-linecap="round"/>
      <line x1="32" y1="44" x2="40" y2="56" stroke="#1d3557" stroke-width="2.5" stroke-linecap="round"/>
    </svg>
    """
    st.markdown(f"""
    <div class="author-card">
      <div>{stickman_svg}</div>
      <div class="author-meta">
        <div class="author-name">Akmal Dwi Putra Mahardika</div>
        <div class="author-id">NIM: 2802505374</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

st.caption("Aplikasi interaktif untuk memahami keseimbangan antara stres belajar dan performa akademik.")
section = st.sidebar.radio("Navigasi", ["Input & Hasil", "Evaluasi & Saran"], index=0)

# ---------- Section: Input & Hasil ----------
if section == "Input & Hasil":
    section_title("Rutinitas Harian")
    c1, c2 = st.columns(2)
    with c1: study = st.slider("Jam Belajar / Hari", 0.0, 8.0, 3.0, 0.5)
    with c2: sleep  = st.slider("Jam Tidur / Hari", 6.0, 11.0, 9.5, 0.5)

    section_title("Lingkungan Sekolah")
    c3, c4 = st.columns(2)
    with c3: attend = st.slider("Kehadiran (%)", 50, 100, 95, 1)
    with c4: classsize = st.slider("Ukuran Kelas", 15, 45, 28, 1)

    section_title("Dukungan & Beban Belajar")
    c5, c6 = st.columns(2)
    with c5: support = st.slider("Dukungan Sekolah (0–100)", 0, 100, 70, 5)
    with c6: workload = st.slider("Beban Tugas (0–100)", 0, 100, 50, 5)

    vals = {
        "StudyHours": study, "SleepHours": sleep, "Attendance": attend,
        "ClassSize": classsize, "SchoolSupport": support, "Workload": workload
    }
    perf, stress = perf_component(vals), stress_component(vals)
    perf_score, stress_score = weighted_score(perf), weighted_score(stress)
    overall = min(perf_score, stress_score)
    st.session_state["data"] = {
        "vals": vals, "perf": perf, "stress": stress,
        "perf_score": perf_score, "stress_score": stress_score, "overall": overall
    }

    k1, k2, k3 = st.columns(3)
    k1.markdown(f'<div class="kpi"><h4>Kesiapan Belajar</h4><div class="val">{perf_score:.1f}</div></div>', unsafe_allow_html=True)
    k2.markdown(f'<div class="kpi"><h4>Kesehatan Stres</h4><div class="val">{stress_score:.1f}</div></div>', unsafe_allow_html=True)
    k3.markdown(f'<div class="kpi"><h4>Kesimpulan</h4><div class="val">{traffic_light(overall)}</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=overall,
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'thickness': 0.3, 'color': ACCENT},
            'steps': [
                {'range': [0, 50], 'color': '#fde2e2'},
                {'range': [50, 75], 'color': '#fff4cc'},
                {'range': [75, 100], 'color': '#d9eaf7'}
            ]
        },
        title={'text': 'Keseimbangan Umum'}
    ))
    fig.update_layout(height=230, margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ---------- Section: Evaluasi & Saran ----------
else:
    data = st.session_state.get("data")
    if not data:
        st.info("Isi terlebih dahulu bagian 'Input & Hasil'.")
        st.stop()

    vals, perf, stress = data["vals"], data["perf"], data["stress"]

    radar_df = pd.DataFrame({
        'Faktor': list(vals.keys()),
        'Performa': [perf[k] for k in vals],
        'KesehatanStres': [stress[k] for k in vals]
    })
    fig_r = px.line_polar(
        radar_df, r='Performa', theta='Faktor', line_close=True, range_r=[0, 100],
        color_discrete_sequence=[PRIMARY]
    )
    fig_r.add_trace(px.line_polar(
        radar_df, r='KesehatanStres', theta='Faktor', line_close=True,
        color_discrete_sequence=[SECONDARY]
    ).data[0])
    fig_r.update_layout(
        height=420,
        legend=dict(orientation='h', yanchor='bottom', y=-0.15, xanchor='center', x=0.5),
        polar=dict(radialaxis=dict(showline=True, linewidth=1, gridcolor="#e5e7eb"))
    )
    st.markdown('<div class="chart">', unsafe_allow_html=True)
    st.plotly_chart(fig_r, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    strength = pd.DataFrame({
        'Faktor': list(vals.keys()),
        'Performa': [perf[k] for k in vals],
        'KesehatanStres': [stress[k] for k in vals]
    })
    strength['Gabungan'] = (strength['Performa'] + strength['KesehatanStres']) / 2.0
    melt = strength.melt(id_vars='Faktor', value_vars=['Performa', 'KesehatanStres'],
                         var_name='Dimensi', value_name='Skor')
    fig_b = px.bar(
        melt, x='Faktor', y='Skor', color='Dimensi', barmode='group', height=400,
        color_discrete_map={'Performa': PRIMARY, 'KesehatanStres': SECONDARY}
    )
    st.markdown('<div class="chart">', unsafe_allow_html=True)
    st.plotly_chart(fig_b, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="card"><b>Saran</b></div>', unsafe_allow_html=True)
    st.write(recommendation(vals))

    st.markdown('<div class="card"><b>Evidence & References</b></div>', unsafe_allow_html=True)
    st.markdown("""
- Jam tidur anak usia sekolah 9–12 jam/hari — CDC & AASM  
  - https://www.cdc.gov/sleep/about/index.html  
  - https://aasm.org/resources/pdf/pediatricsleepdurationconsensus.pdf
- Ukuran kelas & rasio siswa–guru — OECD  
  - https://www.oecd.org/en/topics/sub-issues/class-size-and-student-teacher-ratios.html
- Beban tugas & burnout — APA; Stanford (Journal of Experimental Education)  
  - https://www.apa.org/monitor/2016/03/homework  
  - https://news.stanford.edu/stories/2014/03/too-much-homework-031014
- Kehadiran & capaian akademik — NZCER (merangkum meta-analisis Credé dkk.)  
  - https://www.nzcer.org.nz/news-and-blogs/student-attendance-engagement-and-achievement-sustaining-change
    """)

st.markdown("---")
st.caption("Belajar Santuy Dulu (BETUL) — seimbang untuk kemajuan belajar.")

