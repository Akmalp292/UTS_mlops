import os
import json
import math
from typing import Dict, List

import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# ==========================
# App Config
# ==========================
st.set_page_config(
    page_title="Analisis Kelayakan SD Indonesia",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.session_state.setdefault("VERSION", "v0.1.0")

# ==========================
# Helper & Caching
# ==========================
REQUIRED_COLUMNS = [
    "Provinsi",
    "Sekolah",
    "Siswa",
    "Mengulang",
    "Putus Sekolah",
    "Kepala Sekolah dan Guru(<S1)",
    "Kepala Sekolah dan Guru(≥ S1)",
    "Tenaga Kependidikan(SM)",
    "Tenaga Kependidikan(>SM)",
    "Rombongan Belajar",
]


@st.cache_data(show_spinner=False)
def load_data(path_or_buffer) -> pd.DataFrame:
    df = pd.read_csv(path_or_buffer)
    df.columns = [c.strip() for c in df.columns]
    rename_map = {
        "Kepala Sekolah dan Guru(>= S1)": "Kepala Sekolah dan Guru(≥ S1)",
        "Tenaga Kependidikan(> SM)": "Tenaga Kependidikan(>SM)",
        "Putus sekolah": "Putus Sekolah",
        "Rombel": "Rombongan Belajar",
        "Prov.": "Provinsi",
    }
    df = df.rename(columns=rename_map)

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        st.warning(
            f"Kolom wajib berikut tidak ditemukan di CSV: {missing}.\n\n"
            "Pastikan nama kolom sesuai."
        )
    return df


def _safe_div(n, d):
    try:
        return float(n) / float(d) if float(d) != 0 else np.nan
    except Exception:
        return np.nan


def compute_ratios(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["Rasio Siswa per Sekolah"] = out.apply(lambda r: _safe_div(r["Siswa"], r["Sekolah"]), axis=1)
    out["Rasio Rombel per Sekolah"] = out.apply(lambda r: _safe_div(r["Rombongan Belajar"], r["Sekolah"]), axis=1)

    out["Total Guru"] = out["Kepala Sekolah dan Guru(<S1)"] + out["Kepala Sekolah dan Guru(≥ S1)"]
    out["% Guru ≥S1"] = out.apply(lambda r: _safe_div(r["Kepala Sekolah dan Guru(≥ S1)"], r["Total Guru"]) * 100, axis=1)
    out["Rasio Siswa per Guru"] = out.apply(lambda r: _safe_div(r["Siswa"], r["Total Guru"]), axis=1)

    out["Tendik per Sekolah"] = out.apply(
        lambda r: _safe_div(r["Tenaga Kependidikan(SM)"] + r["Tenaga Kependidikan(>SM)"], r["Sekolah"]), axis=1
    )

    out["Putus per 1k Siswa"] = out.apply(lambda r: _safe_div(r["Putus Sekolah"], r["Siswa"]) * 1000, axis=1)
    out["Mengulang per 1k Siswa"] = out.apply(lambda r: _safe_div(r["Mengulang"], r["Siswa"]) * 1000, axis=1)
    return out


# ==========================
# Feasibility Score
# ==========================
DEFAULT_WEIGHTS = {
    "Rasio Siswa per Guru": 0.30,
    "% Guru ≥S1": 0.25,
    "Putus per 1k Siswa": 0.20,
    "Mengulang per 1k Siswa": 0.10,
    "Rasio Rombel per Sekolah": 0.10,
    "Tendik per Sekolah": 0.05
}


@st.cache_data(show_spinner=False)
def compute_scores(df_ratios: pd.DataFrame, weights: Dict[str, float]) -> pd.DataFrame:
    df = df_ratios.copy()

    pos_feats = ["% Guru ≥S1", "Tendik per Sekolah"]
    neg_feats = ["Rasio Siswa per Guru", "Putus per 1k Siswa", "Mengulang per 1k Siswa", "Rasio Rombel per Sekolah"]

    for col in pos_feats + neg_feats:
        mu = df[col].mean()
        sd = df[col].std(ddof=0) or 1.0
        df[f"z_{col}"] = (df[col] - mu) / sd

    def sigmoid(x):
        return 1 / (1 + np.exp(-x))

    for col in pos_feats:
        df[f"s_{col}"] = sigmoid(df[f"z_{col}"])
    for col in neg_feats:
        df[f"s_{col}"] = sigmoid(-df[f"z_{col}"])

    def row_score(row):
        s = 0.0
        for k, w in weights.items():
            s += w * row[f"s_{k}"]
        s = s / sum(weights.values())
        return float(s) * 100.0

    df["Feasibility Score"] = df.apply(row_score, axis=1)
    return df


# ==========================
# Sidebar
# ==========================
st.sidebar.title("📚 Analisis Kelayakan SD — Indonesia")
st.sidebar.caption("Streamlit app — " + st.session_state["VERSION"])

st.sidebar.markdown("### 1) Unggah Dataset CSV")
uploaded = st.sidebar.file_uploader(
    "Pilih file CSV 'kelayakan-pendidikan-indonesia.csv'",
    type=["csv"],
    help="Gunakan dataset Kemendikbudristek yang berisi agregat provinsi."
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 2) Bobot Skor (opsional)")
with st.sidebar.expander("Tuning Bobot Feasibility Score"):
    weights = DEFAULT_WEIGHTS.copy()
    for k in list(weights.keys()):
        weights[k] = st.slider(k, 0.0, 1.0, float(weights[k]), 0.05)
    s = sum(weights.values()) or 1.0
    for k in weights:
        weights[k] = weights[k] / s

st.sidebar.markdown("---")
st.sidebar.markdown("### 3) Tampilan")
show_kpis = st.sidebar.checkbox("Tampilkan KPI Ringkas", value=True)
show_rank = st.sidebar.checkbox("Tampilkan Peringkat Provinsi", value=True)
show_charts = st.sidebar.checkbox("Tampilkan Grafik", value=True)

# ==========================
# Main Page
# ==========================
st.title("🇮🇩 Analisis Kelayakan Sekolah Dasar (2023–2024)")
st.write(
    "Aplikasi interaktif untuk mengeksplor data agregat SD per provinsi dan menghitung **Feasibility Score** yang mudah diinterpretasi."
)

if uploaded is None:
    st.info("Silakan unggah CSV untuk mulai. Contoh kolom wajib: " + ", ".join(REQUIRED_COLUMNS))
    st.stop()

try:
    df_raw = load_data(uploaded)
except Exception as e:
    st.error(f"Gagal membaca CSV: {e}")
    st.stop()

if df_raw.empty:
    st.warning("CSV kosong atau gagal diparsing.")
    st.stop()

_df = compute_ratios(df_raw)
_df = compute_scores(_df, weights)

# ==========================
# KPI
# ==========================
if show_kpis:
    total_students = int(_df["Siswa"].sum())
    total_schools = int(_df["Sekolah"].sum())
    total_rombel = int(_df["Rombongan Belajar"].sum())
    avg_ptr = _safe_div(_df["Siswa"].sum(), _df["Total Guru"].sum())
    avg_pct_s1 = _safe_div(_df["Kepala Sekolah dan Guru(≥ S1)"].sum(), _df["Total Guru"].sum()) * 100

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Siswa", f"{total_students:,}")
    c2.metric("Total Sekolah", f"{total_schools:,}")
    c3.metric("Total Rombel", f"{total_rombel:,}")
    c4.metric("Rata2 Rasio Siswa/Guru", f"{avg_ptr:.1f} : 1")
    c5.metric("% Guru ≥S1 (agregat)", f"{avg_pct_s1:.1f}%")

# ==========================
# Ranking
# ==========================
if show_rank:
    st.subheader("🏅 Peringkat Feasibility Score per Provinsi")
    top_n = st.slider("Tampilkan Top-N & Bottom-N", 3, 15, 5)

    df_rank = _df[[
        "Provinsi", "Feasibility Score", "% Guru ≥S1", "Rasio Siswa per Guru",
        "Putus per 1k Siswa", "Mengulang per 1k Siswa", "Rasio Rombel per Sekolah", "Tendik per Sekolah"
    ]]
    df_sorted = df_rank.sort_values("Feasibility Score", ascending=False)

    c1, c2 = st.columns(2)
    c1.write("**Top Provinces**")
    c1.dataframe(df_sorted.head(top_n), use_container_width=True)

    c2.write("**Bottom Provinces**")
    c2.dataframe(df_sorted.tail(top_n).sort_values("Feasibility Score", ascending=True), use_container_width=True)

# ==========================
# Charts
# ==========================
if show_charts:
    st.subheader("📊 Visualisasi Utama")
    sel = st.multiselect(
        "Pilih indikator untuk bar chart",
        ["Feasibility Score", "% Guru ≥S1", "Rasio Siswa per Guru",
         "Putus per 1k Siswa", "Mengulang per 1k Siswa", "Rasio Rombel per Sekolah", "Tendik per Sekolah"],
        default=["Feasibility Score", "% Guru ≥S1", "Rasio Siswa per Guru"],
    )

    if sel:
        view = _df[["Provinsi"] + sel].sort_values("Feasibility Score", ascending=False)
        for metric in sel:
            fig = px.bar(view, x="Provinsi", y=metric, title=metric, height=420)
            fig.update_layout(xaxis_tickangle=-45, margin=dict(l=10, r=10, t=50, b=100))
            st.plotly_chart(fig, use_container_width=True)

# ==========================
# Province Explorer
# ==========================
st.subheader("🧭 Province Explorer & What-if Simulator")
prov_list = _df["Provinsi"].dropna().unique().tolist()
prov = st.selectbox("Pilih Provinsi", prov_list)
row = _df[_df["Provinsi"] == prov].iloc[0]

cA, cB, cC, cD = st.columns(4)
cA.metric("Feasibility Score", f"{row['Feasibility Score']:.1f}")
cB.metric("% Guru ≥S1", f"{row['% Guru ≥S1']:.1f}%")
cC.metric("Rasio Siswa/Guru", f"{row['Rasio Siswa per Guru']:.1f} : 1")
cD.metric("Putus per 1k", f"{row['Putus per 1k Siswa']:.2f}")

with st.expander("What-if: Simulasikan Perubahan (slider)"):
    s1 = st.slider("Δ % Guru ≥S1", -20.0, 20.0, 5.0, 0.5)
    s2 = st.slider("Δ Rasio Siswa/Guru", -10.0, 10.0, -2.0, 0.5)
    s3 = st.slider("Δ Putus per 1k Siswa", -2.0, 2.0, -0.5, 0.1)
    s4 = st.slider("Δ Mengulang per 1k Siswa", -2.0, 2.0, -0.3, 0.1)
    s5 = st.slider("Δ Rasio Rombel/Sekolah", -3.0, 3.0, 0.0, 0.1)
    s6 = st.slider("Δ Tendik/Sekolah", -1.0, 1.0, 0.2, 0.05)

    sim = row.copy()
    sim["% Guru ≥S1"] = max(0.0, min(100.0, row["% Guru ≥S1"] + s1))
    sim["Rasio Siswa per Guru"] = max(0.1, row["Rasio Siswa per Guru"] + s2)
    sim["Putus per 1k Siswa"] = max(0.0, row["Putus per 1k Siswa"] + s3)
    sim["Mengulang per 1k Siswa"] = max(0.0, row["Mengulang per 1k Siswa"] + s4)
    sim["Rasio Rombel per Sekolah"] = max(0.1, row["Rasio Rombel per Sekolah"] + s5)
    sim["Tendik per Sekolah"] = max(0.0, row["Tendik per Sekolah"] + s6)

    _tmp = pd.concat([_df, pd.DataFrame([sim])], ignore_index=True)
    _tmp = compute_scores(_tmp, weights)
    new_score = float(_tmp.iloc[-1]["Feasibility Score"])

    c1, c2 = st.columns(2)
    with c1:
        st.metric("Skor Baru (simulasi)", f"{new_score:.1f}",
                  delta=f"{new_score - row['Feasibility Score']:.1f}")
    with c2:
        st.write("**Saran otomatis:**")
        recs = []
        if s1 > 0: recs.append("Tingkatkan proporsi guru ≥S1 melalui rekrutmen atau beasiswa penyetaraan.")
        if s2 < 0: recs.append("Pertahankan penurunan rasio siswa/guru (tambah guru atau kurangi beban rombel).")
        if s3 < 0: recs.append("Program pencegahan putus sekolah efektif — perluasan dukungan beasiswa.")
        if s4 < 0: recs.append("Intervensi remedial menurunkan angka mengulang — lanjutkan kebijakan.")
        if s5 < 0: recs.append("Optimasi penjadwalan untuk menekan rombel per sekolah.")
        if s6 > 0: recs.append("Tambahan tenaga kependidikan meningkatkan tata kelola sekolah.")
        if not recs:
            recs = ["Tidak ada perubahan berarti."]
        for r in recs:
            st.markdown(f"- {r}")

# ==========================
# Footer
# ==========================
st.markdown("---")
st.caption(
    "© 2025 — Analisis Kelayakan SD | Dibuat dengan Streamlit. | "
    "Skor kelayakan bersifat indikatif, bukan penilaian resmi."
)
