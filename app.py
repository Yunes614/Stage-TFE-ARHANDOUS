import streamlit as st
import serial
import time
import pandas as pd
import matplotlib.pyplot as plt

# =============================
# CONFIG
# =============================
PORT = "COM3"
BAUDRATE = 115200

SURFACE_MM2 = 41.6        # section éprouvette
ADC_TO_FORCE = 0.5        # N / ADC (à calibrer)
ADC_TO_DEFORM = 1e-5      # déformation / ADC (à calibrer)

REFRESH_DELAY = 0.15      # secondes (≈ fluide sans clignotement)

# =============================
# STREAMLIT SETUP
# =============================
st.set_page_config(page_title="Banc d'essai de traction", layout="wide")
st.title("📊 Banc d’essai de traction – Interface Streamlit")

# =============================
# SESSION STATE
# =============================
if "running" not in st.session_state:
    st.session_state.running = False

if "data" not in st.session_state:
    st.session_state.data = []

if "t0" not in st.session_state:
    st.session_state.t0 = None

if "ser" not in st.session_state:
    st.session_state.ser = None

if "figs_created" not in st.session_state:
    st.session_state.figs_created = False

# =============================
# SIDEBAR – PARAMÈTRES ÉPROUVETTE
# =============================
st.sidebar.title("🧪 Paramètres éprouvette 3D")

st.sidebar.selectbox("Type de filament", ["PLA", "ABS", "PETG", "TPU"])
st.sidebar.selectbox("Motif de remplissage", ["Gyroïde", "Rectiligne", "Monotone"])
st.sidebar.slider("Taux de remplissage (%)", 0, 100, 100)
st.sidebar.number_input("Hauteur de couche (mm)", 0.05, 0.4, 0.2)
st.sidebar.number_input("Température buse (°C)", 180, 260, 210)
st.sidebar.number_input("Température plateau (°C)", 0, 120, 60)

# =============================
# BOUTONS
# =============================
c1, c2 = st.columns(2)

with c1:
    if st.button("▶️ Démarrer acquisition"):
        st.session_state.running = True
        st.session_state.data = []
        st.session_state.t0 = time.time()

        if st.session_state.ser is None:
            try:
                st.session_state.ser = serial.Serial(PORT, BAUDRATE, timeout=1)
                time.sleep(0.3)
            except Exception as e:
                st.error(f"Erreur série : {e}")
                st.session_state.running = False

with c2:
    if st.button("⏹️ Stop"):
        st.session_state.running = False
        if st.session_state.ser:
            st.session_state.ser.close()
            st.session_state.ser = None

# =============================
# ZONE D'AFFICHAGE
# =============================
g1, g2, g3 = st.columns(3)
table_zone = st.container()

# =============================
# INITIALISATION DES FIGURES
# =============================
if not st.session_state.figs_created:
    st.session_state.fig_t, st.session_state.ax_t = plt.subplots(figsize=(4, 3))
    st.session_state.fig_f, st.session_state.ax_f = plt.subplots(figsize=(4, 3))
    st.session_state.fig_s, st.session_state.ax_s = plt.subplots(figsize=(4, 3))
    st.session_state.figs_created = True

# =============================
# LECTURE SÉRIE (1 PAS)
# =============================
if st.session_state.running and st.session_state.ser:
    try:
        line = st.session_state.ser.readline().decode(errors="ignore").strip()

        if line.count(";") >= 2:
            parts = line.split(";")
            temp = float(parts[0])
            hum = float(parts[1])
            adc = int(parts[2]) if len(parts) > 2 else 0

            t = time.time() - st.session_state.t0
            force = adc * ADC_TO_FORCE
            deformation = adc * ADC_TO_DEFORM
            contrainte = force / SURFACE_MM2 if SURFACE_MM2 > 0 else 0

            st.session_state.data.append({
                "time": t,
                "temperature": temp,
                "humidity": hum,
                "adc": adc,
                "force": force,
                "deformation": deformation,
                "contrainte": contrainte
            })

    except Exception as e:
        st.error(f"Erreur série : {e}")

# =============================
# AFFICHAGE COURBES (STABLE)
# =============================
if len(st.session_state.data) >= 2:
    df = pd.DataFrame(st.session_state.data)

    ax_t = st.session_state.ax_t
    ax_f = st.session_state.ax_f
    ax_s = st.session_state.ax_s

    # Température / Humidité
    ax_t.clear()
    ax_t.plot(df["time"], df["temperature"], "r-", label="Température (°C)")
    ax_t.plot(df["time"], df["humidity"], "b-", label="Humidité (%)")
    ax_t.set_ylim(0, 100)
    ax_t.set_title("Température / Humidité")
    ax_t.legend()
    ax_t.grid(True)

    # Force
    ax_f.clear()
    ax_f.plot(df["time"], df["force"], "g-")
    ax_f.set_ylim(0, max(1, df["force"].max() * 1.2))
    ax_f.set_title("Force (N)")
    ax_f.grid(True)

    # Contrainte / Déformation
    ax_s.clear()
    ax_s.plot(df["deformation"], df["contrainte"], "y.")
    ax_s.set_xlim(left=0)
    ax_s.set_ylim(bottom=0)
    ax_s.set_title("Contrainte / Déformation")
    ax_s.grid(True)

    with g1:
        st.pyplot(st.session_state.fig_t)
    with g2:
        st.pyplot(st.session_state.fig_f)
    with g3:
        st.pyplot(st.session_state.fig_s)

    table_zone.dataframe(df.tail(10), width="stretch")

# =============================
# EXPORT CSV
# =============================
if len(st.session_state.data) > 0:
    df = pd.DataFrame(st.session_state.data)
    st.download_button(
        "💾 Télécharger les données (CSV)",
        df.to_csv(index=False),
        file_name="essai_traction.csv"
    )

# =============================
# RAFRAÎCHISSEMENT
# =============================
if st.session_state.running:
    time.sleep(REFRESH_DELAY)
    st.rerun()
