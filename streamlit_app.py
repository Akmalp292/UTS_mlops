import os, json, glob
import streamlit as st
import numpy as np
from PIL import Image
import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import img_to_array
from tensorflow.keras.applications import mobilenet_v3

# ====== Config & helpers ======
TARGET_SIZE = (224, 224)
PREPROCESS = mobilenet_v3.preprocess_input

def find_first(*candidates):
    """Return first existing path from candidates; else ''."""
    for c in candidates:
        if c and os.path.exists(c):
            return c
    return ""

# Kandidat lokasi model (urutkan yang paling kamu inginkan dulu)
MODEL_PATH = "models/padang_food_mobilenetv3.keras"
CLASSES_PATH = "models/classes.json"

# Debug info kalau gagal
if not MODEL_PATH:
    st.error(
        "Model file tidak ditemukan di candidate paths. "
        "Isi repo saat runtime:\n"
        f"Root files: {os.listdir('.')}\n"
        f"Models dir: {os.listdir('models') if os.path.exists('models') else 'tidak ada'}"
    )
    st.stop()

if not CLASSES_PATH:
    st.error(
        "classes.json tidak ditemukan. Pastikan file mapping label ada di "
        "`models/classes.json` atau `classes.json`."
    )
    st.stop()

@st.cache_resource(show_spinner=False)
def load_model_and_labels(model_path, classes_path):
    model = load_model(model_path)
    with open(classes_path, "r", encoding="utf-8") as f:
        index_to_label = json.load(f)
    # dukung format dict ataupun list
    if isinstance(index_to_label, dict):
        num_classes = model.output_shape[-1]
        labels = [index_to_label[str(i)] for i in range(num_classes)]
    else:
        labels = index_to_label
    return model, labels

def preprocess_pil(img_pil: Image.Image):
    """Resize -> RGB -> array -> preprocess_input -> add batch dim"""
    img = img_pil.convert("RGB").resize(TARGET_SIZE)
    arr = img_to_array(img)
    arr = PREPROCESS(arr)  # MobileNetV3 preprocess
    arr = np.expand_dims(arr, axis=0)  # (1, h, w, 3)
    return arr

def predict_topk(model, arr, labels, k=3):
    """Return top-k (label, prob) sorted desc."""
    probs = model.predict(arr, verbose=0)[0]  # shape (num_classes,)
    top_idx = np.argsort(probs)[::-1][:k]
    return [(labels[i], float(probs[i])) for i in top_idx], probs

def plot_probs(labels, probs, top_k=5):
    """Bar chart probs untuk top-k"""
    idx = np.argsort(probs)[::-1][:top_k]
    plt.figure(figsize=(6, 3.5))
    plt.bar([labels[i] for i in idx], [probs[i] for i in idx])
    plt.xticks(rotation=30, ha="right")
    plt.ylabel("Probability")
    plt.title(f"Top-{top_k} Predictions")
    st.pyplot(plt.gcf())
    plt.close()

# ==============================
# UI
# ==============================
st.title("🍛 Padang Cuisine Classifier")
st.caption("Upload foto makanan Padang → model akan memprediksi kelasnya (MobileNetV3).")

# Load model
with st.spinner("Loading model & labels..."):
    try:
        model, labels = load_model_and_labels(MODEL_PATH, CLASSES_PATH)
        st.success(f"Model loaded. {len(labels)} classes.")
    except Exception as e:
        st.error(f"Gagal load model/labels: {e}")
        st.stop()

# Sidebar info
with st.sidebar:
    st.header("Model Info")
    st.write(f"**Backbone**: MobileNetV3Large")
    st.write(f"**Input size**: {TARGET_SIZE[0]}×{TARGET_SIZE[1]}")
    st.write(f"**Classes ({len(labels)}):**")
    st.write(", ".join(labels))

# Upload
uploaded = st.file_uploader("Upload image (JPG/PNG)", type=["jpg", "jpeg", "png"])

if uploaded is not None:
    # Preview image
    img_bytes = uploaded.read()
    img_pil = Image.open(BytesIO(img_bytes))
    st.image(img_pil, caption="Preview", use_container_width=True)

    # Predict
    arr = preprocess_pil(img_pil)
    topk, probs = predict_topk(model, arr, labels, k=3)

    st.subheader("Top-3 Predictions")
    for i, (label, p) in enumerate(topk, 1):
        st.write(f"{i}. **{label}** — {p*100:.2f}%")

    # Plot bar
    plot_probs(labels, probs, top_k=min(5, len(labels)))

    # Show raw probabilities (optional)
    with st.expander("Show raw probabilities"):
        prob_table = {labels[i]: float(probs[i]) for i in range(len(labels))}
        st.json(prob_table)
else:
    st.info("Silakan upload gambar untuk diprediksi.")
