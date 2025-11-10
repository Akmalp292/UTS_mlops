import os
import json
import numpy as np
from io import BytesIO
from PIL import Image

import streamlit as st
import tensorflow as tf
from tensorflow.keras.preprocessing.image import img_to_array
from tensorflow.keras.applications import mobilenet_v3
from tensorflow.keras.models import load_model
import matplotlib.pyplot as plt

# ==============================
# CONFIG
# ==============================
MODEL_PATH = "models/padang_food_mobilenetv3.keras"
CLASSES_PATH = "models/classes.json"
TARGET_SIZE = (224, 224)  # sama seperti training
PREPROCESS = mobilenet_v3.preprocess_input

st.set_page_config(
    page_title="Padang Cuisine Classifier",
    page_icon="🍛",
    layout="centered"
)

@st.cache_resource(show_spinner=False)
def load_model_and_labels(model_path: str, classes_path: str):
    # Load model
    model = load_model(model_path)
    # Load label list (index -> label name)
    with open(classes_path, "r", encoding="utf-8") as f:
        index_to_label = json.load(f)

    # Pastikan urutan label benar (0..N-1)
    num_classes = model.output_shape[-1]
    labels = [index_to_label[str(i)] if isinstance(index_to_label, dict) and str(i) in index_to_label
              else index_to_label[i]  # kalau list
              for i in range(num_classes)]
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
