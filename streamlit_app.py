import os
import json
import numpy as np
import pandas as pd
import streamlit as st
import tensorflow as tf
from PIL import Image
from tensorflow.keras.models import load_model
from tensorflow.keras.applications import mobilenet_v3

# =======================
# Config
# =======================
MODEL_PATH = "padang_food_mobilenetv3.h5"   # model .h5 di root
CLASSES_PATH = "classes.json"               # mapping index->label
IMG_SIZE = (224, 224)                       # sama seperti training
PREPROCESS = mobilenet_v3.preprocess_input  # preprocessing MobileNetV3

# =======================
# Utils
# =======================
def read_labels(classes_path: str):
    """Baca label dari JSON (dict index->name atau list)."""
    with open(classes_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        # pastikan urutan 0..N-1
        labels = [data[str(i)] for i in range(len(data))]
    else:
        labels = list(data)
    return labels

def make_prediction(image: Image.Image, model):
    """Resize -> array -> preprocess -> batch -> predict."""
    image = image.convert("RGB").resize(IMG_SIZE)
    arr = tf.keras.utils.img_to_array(image)
    arr = PREPROCESS(arr)
    bat = tf.expand_dims(arr, 0)  # (1, h, w, 3)
    preds = model.predict(bat, verbose=0)  # (1, num_classes)
    return preds[0]  # (num_classes,)

# =======================
# Sanity checks
# =======================
if not os.path.exists(MODEL_PATH):
    st.error(f"❌ Model file tidak ditemukan: {MODEL_PATH}")
    st.stop()

if not os.path.exists(CLASSES_PATH):
    st.error(f"❌ File classes.json tidak ditemukan: {CLASSES_PATH}")
    st.stop()

# =======================
# Load model & labels
# =======================
@st.cache_resource(show_spinner=False)
def load_all(model_path, classes_path):
    # Gunakan compile=False biar aman lintas-versi
    model = load_model(model_path, compile=False)
    labels = read_labels(classes_path)
    return model, labels

model, labels = load_all(MODEL_PATH, CLASSES_PATH)

# =======================
# UI
# =======================
st.header("🍛 Padang Cuisine Classifier")
st.write("Upload foto makanan Padang untuk diprediksi (MobileNetV3).")

uploaded_file = st.file_uploader("Pilih gambar...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image.resize((360, 360)), caption="Uploaded Image", use_column_width=False)

    probs = make_prediction(image, model)         # ndarray shape (num_classes,)
    score = tf.nn.softmax(probs).numpy()          # softmax untuk skor 0..1

    top_idx = int(np.argmax(score))
    top_label = labels[top_idx]
    top_conf = float(score[top_idx]) * 100.0

    st.subheader("Hasil Prediksi")
    st.write(f"Prediksi: **{top_label}**")
    st.write(f"Akurasi: **{top_conf:.2f}%**")

    # Tabel probabilitas (opsional)
    st.write("Probabilitas per kelas:")
    df = pd.DataFrame({"label": labels, "prob": score})
    df = df.sort_values("prob", ascending=False)
    st.dataframe(df, use_container_width=True)
else:
    st.info("Silakan upload gambar untuk diprediksi.")
