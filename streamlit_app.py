# =============================================
# SSPI — Student Stress & Performance Insights
# Dashboard style (Weather Forecast-like), RWB theme, EDA & References
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
st.session_state.setdefault("VERSION", "v2.0-forecast")
st.session_state.setdefault("sspi_data", None)

# -----------------------------
# THEME (Red–White–Blue) + Patterned Background + Forecast-like UI
# -----------------------------
PRIMARY   = "#d90429"   # red
SECONDARY = "#1d3557"   # dark blue
ACCENT    = "#457b9d"   # light blue

st.markdown(
    f"""
    <style>
      /* App background: subtle gradient + diagonal stripes */
      [data-testid="stAppViewContainer"] {{
        background-image:
          linear-gradient(180deg, #ffffffcc 0%, #ffffff 30%),
          repeating-linear-gradient(45deg, rgba(29,53,87,0.045) 0px, rgba(29,53,87,0.045) 2px, transparent 3px, transparent 8px),
          linear-gradient(180deg,#e8f0fe 0%, #ffffff 60%);
      }}

      /* Tricolor ribbon at top */
      .top-ribbon {{
        height: 8px; width: 100%;
        background: linear-gradient(90deg, {PRIMARY} 0%, #ffffff 50%, {SECONDARY} 100%);
        margin: 0 0 12px 0;
        border-radius: 8px;
      }}

      /* Sidebar: dark blue */
      [data-testid="stSidebar"] {{
        background: {SECONDARY};
        color: #e2e8f0;
        border-top-right-radius: 16px;
        border-bottom-right-radius: 16px;
      }}
      [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3,
      [data-testid="stSidebar"] label, [data-testid="stSidebar"] p {{
        color: #e2e8f0 !important;
      }}

      /* Header card (like forecast navbar) */
      .header-card {{
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 14px;
        padding: 14px 18px;
        box-shadow: 0 6px 18px rgba(0,0,0,0.05);
        margin-bottom: 10px;
      }}
      .brand {{
        font-weight: 800; font-size: 1.25rem; color: {SECONDARY};
      }}
      .subbrand {{
        font-weight: 500; font-size: 0.9rem; color: #6b7280;
      }}
      .inline {{
        display: flex; align-items: center; gap: 16px; justify-content: space-between;
      }}
      .search-input {{
        background: #f2f6ff; border: 1px solid #e5e7eb; border-radius: 10px;
        padding: 8px 12px; width: 260px; color: #0f172a;
      }}

      /* Section title (bold black, with red accent bar) */
      .section-title {{
        font-weight: 800; color: #0f172a; font-size: 1.1rem; margin: 0.25rem 0 0.6rem 0;
        border-left: 6px solid {PRIMARY}; padding-left: 10px;
      }}

      /* Cards & KPI tiles */
      .card {{
        background: #ffffff; border: 1px solid #e5e7eb; border-radius: 12px;
        padding: 14px; box-shadow: 0 2px 10px rgba(15,23,42,0.06);
      }}
      .kpi {{
        background: #ffffff; border: 1px solid #e5e7eb; border-radius: 12px;
        padding: 10px 12px; box-shadow: 0 2px 8px rgba(15,23,42,0.05);
        border-top: 4px solid {ACCENT};
        text-align: center;
      }}
      .kpi h4 {{ margin: 0 0 6px 0; color: {SECONDARY}; font-weight: 700; }}
      .kpi .val {{ font-size: 1.6rem; font-weight: 800; color: {PRIMARY}; }}

      /* Divider */
      .divider {{
        height: 1px; background: linear-gradient(90deg, rgba(15,23,42,0), rgba(15,23,42,.18), rgba(15,23,42,0));
        margin: 14px 0;
      }}

      /* Chart wrapper (left border accent) */
      .chart {{
        background: #ffffff; border: 1px solid #e5e7eb; border-radius: 12px;
        padding: 10px; box-shadow: 0 2px 8px rgba(15,23,42,0.04);
        border-left: 4px solid {PRIMARY};
      }}

      /* Headers & metric text color */
      h1, h2, h3 {{ color: #0f172a; }}
      .stMetric > div > div {{ color: #0f172a !important; }}
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# Simple Model / Rules
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
    return {"StudyHours": CLIP(sh), "SleepHours": CLIP(sl), "Attendance": CLIP(at),
            "ClassSize": CLIP(cs), "SchoolSupport": CLIP(sp), "Workload": CLIP(wl)}

def stress_component(v: Dict[str, float]) -> Dict[str, float]:
    sh = 100 * (1 - np.exp(-((v["StudyHours"] - OPT["StudyHours"])**2)/(2*(1.5**2))))
    sl = 100 * (1 - np.clip(abs(v["SleepHours"]-OPT["SleepHours"])/2.0, 0, 1))
    at = v["Attendance"]
    cs = 100 * (1 - np.clip((v["ClassSize"]-15)/(45-15), 0, 1))
    sp = v["SchoolSupport"]
    wl = 100 * (1 - v["Workload"]/100)
    study_good = CLIP(100 - sh)
    return {"StudyHours": study_good, "SleepHours": CLIP(sl), "Attendance": CLIP(at),
            "ClassSize": CLIP(cs), "SchoolSupport": CLIP(sp), "Workload": CLIP(wl)}

def weighted_score(c: Dict[str, float], weights: Dict[str, float]) -> float:
    return float(sum(c[k]*weights[k] for k in weights)/sum(weights.values()))

def traffic_light(score: float) -> str:
    if score >= 75: return "Baik"
    if score >= 50: return "Perlu Perhatian"
    return "Risiko Tinggi"

def build_recommendation(vals: Dict[str, float]) -> str:
    s = []
    if vals["SleepHours"] < 8.5:
        s.append("Kamu perlu tidur yang cukup, idealnya sekitar 9–10 jam per hari.")
    if vals["Workload"] > 70:
        s.append("Kurangi beban tugas agar waktu istirahat dan rekreasi lebih seimbang.")
    if vals["ClassSize"] > 35:
        s.append("Ukuran kelas yang besar dapat meningkatkan tekanan belajar, pertimbangkan pengelompokan ulang kelas.")
    if vals["SchoolSupport"] < 60:
        s.append("Tingkatkan dukungan sekolah melalui kegiatan positif dan layanan konseling.")
    if vals["StudyHours"] < 2.0:
        s.append("Tambahkan waktu belajar mandiri sekitar 15–30 menit setiap hari untuk meningkatkan pemahaman.")
    if vals["Attendance"] < 90:
        s.append("Tingkatkan kehadiran di sekolah untuk menjaga keterlibatan akademik yang konsisten.")
    if not s:
        return "Kondisi belajar dan stres tampak seimbang. Pertahankan pola tidur, waktu belajar, dan dukungan sekolah yang sudah baik."
    return " ".join(s)

def section_title(text: str):
    st.markdown(f'<div class="section-title">{text}</div>', unsafe_allow_html=True)

# -----------------------------
# Header (Forecast-like) & Navigation
# -----------------------------
st.markdown('<div class="top-ribbon"></div>', unsafe_allow_html=True)
with st.container():
    c1, c2, c3 = st.columns([1.2, 2.0, 0.8])
    with c1:
        st.markdown('<div class="header-card"><div class="inline"><div><div class="brand">SSPI Forecast</div><div class="subbrand">Student Stress & Performance Insights</div></div></div></div>', unsafe_allow_html=True)
    with c2:
        # Non-functional cosmetic search bar (visual parity with template)
        st.markdown(f'<div class="header-card"><input class="search-input" placeholder="Search..." /></div>', unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="header-card" style="text-align:right;">Versi: v2.0-forecast</div>', unsafe_allow_html=True)

st.caption("Alat sederhana untuk memahami keseimbangan antara stres dan performa belajar siswa.")

# Sidebar navigation
section = st.sidebar.radio("Navigasi", ["Input & Hasil", "Evaluasi & Saran"], index=0)

# -----------------------------
# SECTION — Input & Hasil
# -----------------------------
if section == "Input & Hasil":
    section_title("Rutinitas Harian")
    c1, c2 = st.columns(2)
    with c1:
        study = st.slider("Jam Belajar / Hari", 0.0, 8.0, 3.0, 0.5, help="Waktu belajar mandiri di luar jam sekolah.")
    with c2:
        sleep = st.slider("Jam Tidur / Hari", 6.0, 11.0, 9.5, 0.5, help="Durasi tidur rata-rata setiap malam.")

    section_title("Lingkungan Sekolah")
    c3, c4 = st.columns(2)
    with c3:
        attend = st.slider("Kehadiran (%)", 50, 100, 95, 1, help="Persentase kehadiran siswa di sekolah.")
    with c4:
        classsize = st.slider("Ukuran Kelas", 15, 45, 28, 1, help="Jumlah siswa rata-rata dalam satu kelas.")

    section_title("Dukungan & Beban Belajar")
    c5, c6 = st.columns(2)
    with c5:
        support = st.slider("Dukungan Sekolah (0–100)", 0, 100, 70, 5, help="Konselor, kegiatan positif, komunikasi orang tua.")
    with c6:
        workload = st.slider("Beban Tugas (0–100)", 0, 100, 50, 5, help="PR, ujian, proyek, dll.")

    # Computation (live)
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
    overall = min(perf_score, stress_score)

    # persist for Section 2
    st.session_state["sspi_data"] = {
        "vals": vals, "perf": perf, "stress": stress,
        "perf_score": perf_score, "stress_score": stress_score, "overall": overall
    }

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # KPI Tiles (like "Today's Highlights")
    k1, k2, k3 = st.columns(3)
    with k1:
        st.markdown('<div class="kpi"><h4>Kesiapan Belajar</h4><div class="val">{:.1f}</div></div>'.format(perf_score), unsafe_allow_html=True)
    with k2:
        st.markdown('<div class="kpi"><h4>Kesehatan Stres</h4><div class="val">{:.1f}</div></div>'.format(stress_score), unsafe_allow_html=True)
    with k3:
        st.markdown('<div class="kpi"><h4>Kesimpulan Umum</h4><div class="val">{}</div></div>'.format(traffic_light(overall)), unsafe_allow_html=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # Gauge
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        fig_g = go.Figure(go.Indicator(
            mode="gauge+number",
            value=overall,
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
        fig_g.update_layout(height=240, margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig_g, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------
# SECTION — Evaluasi & Saran
# -----------------------------
elif section == "Evaluasi & Saran":
    section_title("Evaluasi & Saran")
    data = st.session_state.get("sspi_data")
    if not data:
        st.info("Silakan isi bagian 'Input & Hasil' terlebih dahulu.")
        st.stop()

    vals = data["vals"]; perf = data["perf"]; stress = data["stress"]

    # Radar (two layers)
    radar_df = pd.DataFrame({
        'Faktor': list(vals.keys()),
        'Performa': [perf[k] for k in vals],
        'KesehatanStres': [stress[k] for k in vals],
    })
    fig_radar = px.line_polar(
        radar_df, r='Performa', theta='Faktor', line_close=True, range_r=[0,100],
        color_discrete_sequence=[PRIMARY]
    )
    fig_radar.add_trace(px.line_polar(
        radar_df, r='KesehatanStres', theta='Faktor', line_close=True,
        color_discrete_sequence=[SECONDARY]
    ).data[0])
    fig_radar.update_layout(
        height=420,
        legend=dict(orientation='h', yanchor='bottom', y=-0.15, xanchor='center', x=0.5),
        polar=dict(radialaxis=dict(showline=True, linewidth=1, gridcolor="#e5e7eb"))
    )
    st.markdown('<div class="chart">', unsafe_allow_html=True)
    st.plotly_chart(fig_radar, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Bar — factor strengths
    strength_df = pd.DataFrame({
        'Faktor': list(vals.keys()),
        'Performa': [perf[k] for k in vals],
        'KesehatanStres': [stress[k] for k in vals],
    })
    strength_df['Gabungan'] = (strength_df['Performa'] + strength_df['KesehatanStres']) / 2.0
    strength_df = strength_df.sort_values('Gabungan', ascending=False)
    melted = strength_df.melt(id_vars='Faktor', value_vars=['Performa','KesehatanStres'],
                              var_name='Dimensi', value_name='Skor')
    fig_bar = px.bar(
        melted, x='Faktor', y='Skor', color='Dimensi', barmode='group', height=420,
        title='Kekuatan Faktor — Semakin Tinggi Semakin Baik',
        color_discrete_map={'Performa': PRIMARY, 'KesehatanStres': SECONDARY}
    )
    fig_bar.update_layout(
        xaxis_tickangle=-20,
        margin=dict(l=10, r=10, t=50, b=100),
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff"
    )
    st.markdown('<div class="chart">', unsafe_allow_html=True)
    st.plotly_chart(fig_bar, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Sensitivity Explorer (what-if 1D)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("**Sensitivity Explorer**")
    factor = st.selectbox("Pilih faktor untuk disimulasikan",
                          ["Jam Tidur / Hari", "Jam Belajar / Hari", "Kehadiran (%)", "Ukuran Kelas", "Dukungan Sekolah (0–100)", "Beban Tugas (0–100)"],
                          index=0)
    key_map = {
        "Jam Belajar / Hari": ("StudyHours", np.linspace(0, 8, 33)),
        "Jam Tidur / Hari": ("SleepHours", np.linspace(6, 11, 26)),
        "Kehadiran (%)": ("Attendance", np.linspace(50, 100, 26)),
        "Ukuran Kelas": ("ClassSize", np.linspace(15, 45, 31)),
        "Dukungan Sekolah (0–100)": ("SchoolSupport", np.linspace(0, 100, 26)),
        "Beban Tugas (0–100)": ("Workload", np.linspace(0, 100, 26)),
    }
    var_key, grid = key_map[factor]
    base = vals.copy()
    perf_list, stress_list = [], []
    for g in grid:
        v = base.copy()
        v[var_key] = float(g)
        perf_list.append(weighted_score(perf_component(v), {k:1 for k in v}))
        stress_list.append(weighted_score(stress_component(v), {k:1 for k in v}))
    sim_df = pd.DataFrame({factor: grid, "Kesiapan Belajar": perf_list, "Kesehatan Stres": stress_list})
    fig_sim = px.line(sim_df, x=factor, y=["Kesiapan Belajar", "Kesehatan Stres"],
                      color_discrete_map={"Kesiapan Belajar": PRIMARY, "Kesehatan Stres": SECONDARY},
                      height=360, title="Dampak perubahan faktor terhadap skor")
    st.plotly_chart(fig_sim, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Saran (paragraf argumentatif)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("**Saran**")
    paragraph = build_recommendation(vals)
    st.write(paragraph)
    st.markdown('</div>', unsafe_allow_html=True)

    # Evidence & References
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("**Evidence & References**")
    st.markdown("""
- Rekomendasi jam tidur anak usia sekolah 9–12 jam/hari — CDC & American Academy of Sleep Medicine.  
  - CDC: https://www.cdc.gov/sleep/about/index.html  
  - AASM Consensus: https://aasm.org/resources/pdf/pediatricsleepdurationconsensus.pdf

- Ukuran kelas & rasio siswa–guru: ringkasan kebijakan & data komparatif.  
  - OECD overview: https://www.oecd.org/en/topics/sub-issues/class-size-and-student-teacher-ratios.html  
  - Education at a Glance (variabilitas PTR & class size): https://www.oecd.org/en/publications/education-at-a-glance-2025_1c0d9c79-en/full-report/how-do-student-teacher-ratios-and-class-sizes-vary-across-education-levels-up-to-upper-secondary-education_76b87b21.html

- Beban tugas berlebihan & burnout siswa.  
  - APA Monitor: https://www.apa.org/monitor/2016/03/homework  
  - Stanford (Journal of Experimental Education): https://news.stanford.edu/stories/2014/03/too-much-homework-031014

- Kehadiran & capaian akademik.  
  - Ringkasan kebijakan (mengacu meta-analisis Credé dkk.): https://www.nzcer.org.nz/news-and-blogs/student-attendance-engagement-and-achievement-sustaining-change
    """)
    st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------
# Footer
# -----------------------------
st.markdown("---")
st.caption("SSPI membantu memahami keseimbangan antara stres dan performa siswa. Gunakan hasil ini sebagai refleksi, bukan diagnosis.")

