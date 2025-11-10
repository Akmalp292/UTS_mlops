# =============================================
# IK-SD — Indeks Kelayakan Sekolah Dasar (PRO)
# Tujuan jelas, penamaan baku, input ringkas, rekomendasi kuantitatif
# =============================================
from typing import Dict, Tuple
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# ============================
# Konfigurasi Aplikasi
# ============================
st.set_page_config(
    page_title="IK‑SD — Indeks Kelayakan Sekolah Dasar",
    page_icon="📚",
    layout="wide",
)

st.session_state.setdefault("VERSION", "v1.0.0")
st.session_state.setdefault("scenarios", [])

# ============================
# Definisi & Konvensi
# ============================
# Metrik yang lebih kecil lebih baik (target menurun)
LOWER_BETTER = [
    "Rasio Siswa per Guru",      # PTR — Pupil‑Teacher Ratio
    "Putus per 1k Siswa",        # Dropout / 1.000 siswa
    "Mengulang per 1k Siswa",    # Repeater / 1.000 siswa
    "Rasio Rombel per Sekolah",  # Kelas per sekolah
]
# Metrik yang lebih besar lebih baik (target meningkat)
HIGHER_BETTER = ["% Guru ≥S1", "Tendik per Sekolah"]

# Bobot default (jumlah = 1)
DEFAULT_WEIGHTS: Dict[str, float] = {
    "Rasio Siswa per Guru": 0.35,
    "% Guru ≥S1": 0.25,
    "Putus per 1k Siswa": 0.20,
    "Mengulang per 1k Siswa": 0.10,
    "Rasio Rombel per Sekolah": 0.05,
    "Tendik per Sekolah": 0.05,
}

# Benchmark nasional (dapat diubah). Format: (ideal, terburuk)
DEFAULT_BENCHMARKS: Dict[str, Tuple[float, float]] = {
    "Rasio Siswa per Guru": (16.0, 40.0),
    "% Guru ≥S1": (90.0, 50.0),
    "Putus per 1k Siswa": (0.10, 5.00),
    "Mengulang per 1k Siswa": (0.50, 8.00),
    "Rasio Rombel per Sekolah": (6.0, 24.0),
    "Tendik per Sekolah": (5.0, 0.0),
}
PRESET_BENCHMARKS = {
    "Nasional": DEFAULT_BENCHMARKS,
    "Ambisius 2030": {
        "Rasio Siswa per Guru": (14.0, 40.0),
        "% Guru ≥S1": (95.0, 60.0),
        "Putus per 1k Siswa": (0.05, 5.00),
        "Mengulang per 1k Siswa": (0.30, 8.00),
        "Rasio Rombel per Sekolah": (5.0, 24.0),
        "Tendik per Sekolah": (6.0, 0.0),
    },
    "Konsolidasi": {
        "Rasio Siswa per Guru": (18.0, 40.0),
        "% Guru ≥S1": (85.0, 50.0),
        "Putus per 1k Siswa": (0.20, 6.00),
        "Mengulang per 1k Siswa": (1.00, 9.00),
        "Rasio Rombel per Sekolah": (7.0, 26.0),
        "Tendik per Sekolah": (4.0, 0.0),
    },
}

# ============================
# Fungsi Utilitas
# ============================

def _safe_div(n, d):
    try:
        n = float(n); d = float(d)
        return n / d if d != 0 else np.nan
    except Exception:
        return np.nan


def hitung_rasio_dari_input(v: Dict[str, float]) -> Dict[str, float]:
    sekolah = v["Sekolah"]; siswa = v["Siswa"]; rombel = v["Rombongan Belajar"]
    mengulang = v["Mengulang"]; putus = v["Putus Sekolah"]
    guru_lt = v["Guru <S1"]; guru_ge = v["Guru ≥S1"]
    tendik_sm = v["Tendik SM"]; tendik_>sm = v["Tendik >SM"]

    total_guru = max(0.0, float(guru_lt) + float(guru_ge))
    return {
        "Rasio Siswa per Sekolah": _safe_div(siswa, sekolah),
        "Rasio Rombel per Sekolah": _safe_div(rombel, sekolah),
        "% Guru ≥S1": _safe_div(guru_ge, total_guru) * 100,
        "Rasio Siswa per Guru": _safe_div(siswa, total_guru),
        "Tendik per Sekolah": _safe_div(tendik_sm + tendik_>sm, sekolah),
        "Putus per 1k Siswa": _safe_div(putus, siswa) * 1000,
        "Mengulang per 1k Siswa": _safe_div(mengulang, siswa) * 1000,
        "Total Guru": total_guru,
    }


def skor_metrik(val: float, ideal: float, worst: float, higher_better: bool) -> float:
    if val is None or np.isnan(val):
        return 0.0
    if ideal == worst:
        worst = ideal + (1e-6 if higher_better else -1e-6)
    if higher_better:
        return float(np.clip((val - worst) / (ideal - worst), 0, 1) * 100)
    return float(np.clip((worst - val) / (worst - ideal), 0, 1) * 100)


def hitung_indeks(metrics: Dict[str, float], weights: Dict[str, float], bm: Dict[str, Tuple[float, float]]):
    subs = {}
    for k in weights:
        ideal, worst = bm[k]; hb = k in HIGHER_BETTER
        subs[k] = skor_metrik(metrics[k], ideal, worst, hb)
    wsum = sum(weights.values()) or 1.0
    skor = sum(subs[k] * weights[k] for k in weights) / wsum
    return {"skor": skor, **subs}


def hitung_kebutuhan_intervensi(v: Dict[str, float], m: Dict[str, float], bm: Dict[str, Tuple[float, float]]):
    """Hitung kebutuhan kuantitatif untuk mencapai target ideal.
    Output: dict dengan rekomendasi angka.
    """
    sekolah = v["Sekolah"]; siswa = v["Siswa"]; rombel = v["Rombongan Belajar"]
    guru_lt = v["Guru <S1"]; guru_ge = v["Guru ≥S1"]
    total_guru = m["Total Guru"]

    # Target PTR (Rasio Siswa per Guru)
    ptr_ideal, _ = bm["Rasio Siswa per Guru"]
    guru_min_ptr = np.ceil(_safe_div(siswa, ptr_ideal)) if not np.isnan(ptr_ideal) else np.nan
    tambahan_guru_ptr = max(0, int(guru_min_ptr - total_guru)) if not np.isnan(guru_min_ptr) else 0

    # Target % Guru ≥S1
    pct_ideal, _ = bm["% Guru ≥S1"]
    if total_guru > 0 and not np.isnan(pct_ideal):
        guru_ge_target = int(np.ceil((pct_ideal/100.0) * total_guru))
        tambahan_sertifikasi = max(0, guru_ge_target - int(guru_ge))
    else:
        tambahan_sertifikasi = 0

    # Target rombel/sekolah
    rombel_ideal, _ = bm["Rasio Rombel per Sekolah"]
    rombel_target_total = int(np.ceil(rombel_ideal * sekolah)) if not np.isnan(rombel_ideal) else np.nan
    tambahan_rombel = max(0, int(rombel_target_total - rombel)) if not np.isnan(rombel_target_total) else 0

    # Target putus & mengulang per 1k
    dropout_ideal, _ = bm["Putus per 1k Siswa"]
    repeater_ideal, _ = bm["Mengulang per 1k Siswa"]
    target_putus = int(np.floor((dropout_ideal/1000.0) * siswa)) if not np.isnan(dropout_ideal) else 0
    target_mengulang = int(np.floor((repeater_ideal/1000.0) * siswa)) if not np.isnan(repeater_ideal) else 0
    pengurangan_putus = max(0, int(v["Putus Sekolah"] - target_putus))
    pengurangan_mengulang = max(0, int(v["Mengulang"] - target_mengulang))

    return {
        "Tambahan Guru (PTR)": tambahan_guru_ptr,
        "Tambahan Guru ≥S1 / Sertifikasi": tambahan_sertifikasi,
        "Tambahan Rombel": tambahan_rombel,
        "Pengurangan Putus Sekolah": pengurangan_putus,
        "Pengurangan Mengulang": pengurangan_mengulang,
    }

# ============================
# Sidebar — Ringkas & Profesional
# ============================
st.sidebar.title("IK‑SD — Konfigurasi")
st.sidebar.caption("Versi " + st.session_state["VERSION"]) 

preset = st.sidebar.selectbox("Preset Benchmark", list(PRESET_BENCHMARKS.keys()), index=0)
benchmarks = PRESET_BENCHMARKS[preset]

with st.sidebar.expander("Bobot Indikator", expanded=True):
    weights = DEFAULT_WEIGHTS.copy()
    for k in list(weights.keys()):
        weights[k] = st.slider(k, 0.0, 1.0, float(weights[k]), 0.05)
    s = sum(weights.values()) or 1.0
    for k in weights:
        weights[k] = weights[k] / s

with st.sidebar.expander("Ubah Benchmark (opsional)", expanded=False):
    bm = {}
    for k, (ideal, worst) in benchmarks.items():
        c1, c2 = st.columns(2)
        with c1:
            new_ideal = st.number_input(f"Ideal — {k}", value=float(ideal), step=0.1, format="%.2f")
        with c2:
            new_worst = st.number_input(f"Terburuk — {k}", value=float(worst), step=0.1, format="%.2f")
        bm[k] = (new_ideal, new_worst)

active_bm = bm if bm else benchmarks

# ============================
# Headline & Motto (singkat & nyambung masalah nyata)
# ============================
st.header("IK‑SD — Indeks Kelayakan Sekolah Dasar")
st.subheader("Ukur kelayakan, identifikasi bottleneck, hitung kebutuhan intervensi kebijakan.")
# 3 poin misi nyata Indonesia
m1, m2, m3 = st.columns(3)
with m1: st.metric("Fokus 1", "Rasio Siswa/Guru")
with m2: st.metric("Fokus 2", "% Guru ≥S1")
with m3: st.metric("Fokus 3", "Putus & Mengulang")

# ============================
# Form Input — To the point
# ============================
with st.form("form_input", clear_on_submit=False):
    st.markdown("**Masukan Agregat**")
    c1, c2, c3 = st.columns(3)
    with c1:
        nama = st.text_input("Nama Skenario", value="Skenario A")
        sekolah = st.number_input("Sekolah", min_value=1, value=2000, step=1)
        siswa = st.number_input("Siswa", min_value=1, value=500000, step=100)
    with c2:
        guru_ge = st.number_input("Guru ≥S1", min_value=0, value=80000, step=100)
        guru_lt = st.number_input("Guru <S1", min_value=0, value=2500, step=10)
        rombel = st.number_input("Rombongan Belajar", min_value=1, value=18000, step=10)
    with c3:
        tendik_sm = st.number_input("Tendik SM", min_value=0, value=4000, step=10)
        tendik_gt = st.number_input("Tendik >SM", min_value=0, value=1200, step=10)
        putus = st.number_input("Putus Sekolah", min_value=0, value=1200, step=10)
        mengulang = st.number_input("Mengulang", min_value=0, value=3000, step=10)
    hitung = st.form_submit_button("Hitung IK‑SD")

if not hitung:
    st.info("Isi input dan klik **Hitung IK‑SD**.")
    st.stop()

# ============================
# Perhitungan
# ============================
vals = {
    "Sekolah": sekolah, "Siswa": siswa, "Rombongan Belajar": rombel,
    "Guru ≥S1": guru_ge, "Guru <S1": guru_lt,
    "Tendik SM": tendik_sm, "Tendik >SM": tendik_gt,
    "Putus Sekolah": putus, "Mengulang": mengulang,
}
metrics = hitung_rasio_dari_input(vals)
res = hitung_indeks(metrics, weights, active_bm)
act = hitung_kebutuhan_intervensi(vals, metrics, active_bm)

# ============================
# Tampilan Hasil — Ringkas, Profesional
# ============================
colA, colB, colC, colD, colE = st.columns(5)
with colA:
    st.metric("IK‑SD (0–100)", f"{res['skor']:.1f}")
with colB:
    st.metric("PTR (Siswa/Guru)", f"{metrics['Rasio Siswa per Guru']:.1f}")
with colC:
    st.metric("% Guru ≥S1", f"{metrics['% Guru ≥S1']:.1f}%")
with colD:
    st.metric("Putus/1k", f"{metrics['Putus per 1k Siswa']:.2f}")
with colE:
    st.metric("Rombel/Sekolah", f"{metrics['Rasio Rombel per Sekolah']:.2f}")

# Gauge sederhana untuk IK‑SD
fig_g = go.Figure(go.Indicator(mode="gauge+number", value=res['skor'],
                               gauge={'axis': {'range': [0,100]}},
                               title={'text': 'IK‑SD'}))
fig_g.update_layout(height=220, margin=dict(l=10,r=10,t=40,b=10))
st.plotly_chart(fig_g, use_container_width=True)

# Sub-skor tabel
sub_df = pd.DataFrame({
    "Indikator": list(DEFAULT_WEIGHTS.keys()),
    "Sub‑Skor": [res[k] for k in DEFAULT_WEIGHTS.keys()],
    "Bobot": [weights[k] for k in DEFAULT_WEIGHTS.keys()],
}).sort_values("Sub‑Skor", ascending=False)
st.dataframe(sub_df, use_container_width=True)

# Rekomendasi kuantitatif (langsung actionable)
st.markdown("### Rekomendasi Kuantitatif untuk Mencapai Target Ideal")
reco_rows = [
    {"Intervensi": "Tambahan Guru (PTR)", "Kebutuhan": act["Tambahan Guru (PTR)"]},
    {"Intervensi": "Tambahan Guru ≥S1 / Sertifikasi", "Kebutuhan": act["Tambahan Guru ≥S1 / Sertifikasi"]},
    {"Intervensi": "Tambahan Rombel", "Kebutuhan": act["Tambahan Rombel"]},
    {"Intervensi": "Pengurangan Putus Sekolah", "Kebutuhan": act["Pengurangan Putus Sekolah"]},
    {"Intervensi": "Pengurangan Mengulang", "Kebutuhan": act["Pengurangan Mengulang"]},
]
reco_df = pd.DataFrame(reco_rows)
st.dataframe(reco_df, use_container_width=True)

# Simpan skenario & bandingkan
c1, c2 = st.columns(2)
with c1:
    if st.button("Simpan Skenario"):
        st.session_state.scenarios.append({
            "nama": nama, "IKSD": float(res['skor']), "metrics": metrics, "subs": {k: float(res[k]) for k in DEFAULT_WEIGHTS},
            "weights": weights, "bm": active_bm,
        })
        st.success(f"Skenario '{nama}' disimpan.")
with c2:
    if st.button("Bandingkan Dua Skenario"):
        if len(st.session_state.scenarios) < 2:
            st.warning("Butuh ≥ 2 skenario tersimpan.")
        else:
            st.session_state["show_compare"] = True

if st.session_state.get("show_compare"):
    st.markdown("---")
    st.subheader("Perbandingan Skenario")
    names = [s["nama"] for s in st.session_state.scenarios]
    a, b = st.columns(2)
    with a:
        sel_a = st.selectbox("Skenario A", names, index=0)
    with b:
        sel_b = st.selectbox("Skenario B", names, index=min(1, len(names)-1))
    A = next(s for s in st.session_state.scenarios if s["nama"] == sel_a)
    B = next(s for s in st.session_state.scenarios if s["nama"] == sel_b)

    comp = []
    for k in ["IKSD"] + list(DEFAULT_WEIGHTS.keys()):
        va = A['IKSD'] if k == "IKSD" else A['subs'][k]
        vb = B['IKSD'] if k == "IKSD" else B['subs'][k]
        comp.append({"Indikator": k, sel_a: va, sel_b: vb, "Δ (B−A)": vb - va})
    comp_df = pd.DataFrame(comp)
    st.dataframe(comp_df, use_container_width=True)
    fig = px.bar(comp_df[comp_df["Indikator"] != "IKSD"], x="Indikator", y="Δ (B−A)", height=360,
                 title="Δ Sub‑Skor (B−A)")
    fig.update_layout(xaxis_tickangle=-15, margin=dict(l=10,r=10,t=40,b=80))
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.caption("IK‑SD membantu pemangku kepentingan memprioritaskan intervensi: turunkan PTR, tingkatkan proporsi Guru ≥S1, tekan putus/mengulang. Output bersifat indikatif — gunakan bersama data resmi daerah.")

