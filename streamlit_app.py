# =============================================
# SSPI — Student Stress & Performance Insights (Safe Run Version)
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
    layout="wide",
)

st.session_state.setdefault("VERSION", "v1.4-safe")
st.session_state.setdefault("sspi_data", None)

# -----------------------------
# Global Styles
# -----------------------------
st.markdown(
    """
    <style>
      [data-testid="stAppViewContainer"] {
        background: linear-gradient(180deg,#f7f9fc 0%, #ffffff 40%);
      }
      [data-testid="stSidebar"] {
        background: #0f172a;
        color: #e2e8f0;
      }
      [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2,
      [data-testid="stSidebar"] h3, [data-testid="stSidebar"] label,
      [data-testid="stSidebar"] p {
        color: #e2e8f0 !important;
      }
      .section-title {
        font-weight: 800; color: #0f172a; font-size: 1.15rem; 
        margin: 0.25rem 0 0.5rem 0;
      }
      .card { background: #ffffff; border: 1px solid #e5e7eb; 
        border-radius: 12px; padding: 16px; 
        box-shadow: 0 2px 8px rgba(15,23,42,0.06); }
      .kpi { background: #ffffff; border: 1px solid #e5e7eb; 
        border-radius: 12px; padding: 8px 12px; 
        box-shadow: 0 2px 8px rgba(15,23,42,0.04); }
      .divider { height: 1px; 
        background: linear-gradient(90deg, rgba(15,23,42,0), rgba(15,23,42,.15), rgba(15,23,42,0)); 
        margin: 14px 0; }
      .chart { background: #ffffff; border: 1px solid #e5e7eb; 
        border-radius: 12px; padding: 8px; 
        box-shadow: 0 2px 8px rgba(15,23,42,0.04); }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# Header & Navigation
# -----------------------------
st.header("SSPI — Student Stress & Performance Insights")
st.caption("Alat sederhana untuk memahami keseimbangan antara stres dan performa belajar siswa.")

section = st.sidebar.radio("Navigasi", ["Input & Hasil", "Evaluasi & Saran"], index=0)

# -----------------------------
# Section Title Helper
# -----------------------------
def section_title(text):
    """Render bold black section title safely."""
    st.markdown(f'<div class="section-title">{text}</div>', unsafe_allow_html=True)

# -----------------------------
# Input & Output Section (Example)
# -----------------------------
if section == "Input & Hasil":
    section_title("Rutinitas Harian")
    col1, col2 = st.columns(2)
    with col1:
        study = st.slider("Jam Belajar / Hari", 0.0, 8.0, 3.0, 0.5)
    with col2:
        sleep = st.slider("Jam Tidur / Hari", 6.0, 11.0, 9.5, 0.5)

    section_title("Lingkungan Sekolah")
    col3, col4 = st.columns(2)
    with col3:
        attend = st.slider("Kehadiran (%)", 50, 100, 95, 1)
    with col4:
        classsize = st.slider("Ukuran Kelas", 15, 45, 28, 1)

    section_title("Dukungan & Beban Belajar")
    col5, col6 = st.columns(2)
    with col5:
        support = st.slider("Dukungan Sekolah (0–100)", 0, 100, 70, 5)
    with col6:
        workload = st.slider("Beban Tugas (0–100)", 0, 100, 50, 5)

    # Example metrics for demo (replace with real logic)
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    colA, colB, colC = st.columns(3)
    with colA:
        st.markdown('<div class="kpi">', unsafe_allow_html=True)
        st.metric("Kesiapan Belajar", "82.5")
        st.markdown('</div>', unsafe_allow_html=True)
    with colB:
        st.markdown('<div class="kpi">', unsafe_allow_html=True)
        st.metric("Kesehatan Stres", "75.2")
        st.markdown('</div>', unsafe_allow_html=True)
    with colC:
        st.markdown('<div class="kpi">', unsafe_allow_html=True)
        st.metric("Kesimpulan Umum", "Baik")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="card">Contoh grafik atau gauge dapat ditampilkan di sini.</div>', unsafe_allow_html=True)

elif section == "Evaluasi & Saran":
    section_title("Evaluasi & Saran")
    st.markdown('<div class="card">Bagian ini menampilkan grafik evaluasi dan saran argumentatif.</div>', unsafe_allow_html=True)

# -----------------------------
# Footer
# -----------------------------
st.markdown("---")
st.caption("SSPI membantu memahami keseimbangan antara stres dan performa siswa. Gunakan hasil ini sebagai refleksi, bukan diagnosis.")
