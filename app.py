
import streamlit as st
import pandas as pd
import lightgbm as lgb
import os

st.set_page_config(page_title="ASBK Test Sandbox", page_icon="🌾", layout="centered")

st.title("🌾 AgroSmart Borno-Kano (ASBK) Sandbox")
st.write("Test how smallholders (via USSD) and cooperatives (via API) interact with the AI Engine live.")

# Securely load the optimized model weights generated in Phase 2
MODEL_PATH = 'asbk_optimized_yield_engine.txt'
if os.path.exists(MODEL_PATH):
    engine = lgb.Booster(model_file=MODEL_PATH)
else:
    st.error("⚠️ Prediction engine file 'asbk_optimized_yield_engine.txt' missing! Please run your training pipeline cell first.")
    st.stop()

# Establish clear navigation tabs for the two user personas
tab1, tab2 = st.tabs(["📱 Feature Phone (USSD Simulation)", "📊 Smartphone App Interface"])

# -------------------------------------------------------------------------
# TAB 1: USSD SIMULATOR (Low-Bandwidth Option)
# -------------------------------------------------------------------------
with tab1:
    st.subheader("Interactive USSD Interface (`*384#`)")
    st.info("Simulates what a smallholder farmer sees on a basic phone screen with zero mobile data.")

    if 'ussd_step' not in st.session_state:
        st.session_state.ussd_step = 0
        st.session_state.choices = []

    with st.container(border=True):
        if st.session_state.ussd_step == 0:
            st.code("Screen: Maraba da zuwa AgroSmart (ASBK)\nZabi amfanin gona (Select Crop):\n1. Gero (Millet)\n2. Dawa (Sorghum)\n3. Masara (Maize)", language="text")
            crop = st.selectbox("Your Input:", ["1", "2", "3"], key="c_select")
            if st.button("Send", key="b0"):
                st.session_state.choices.append(crop)
                st.session_state.ussd_step = 1
                st.rerun()

        elif st.session_state.ussd_step == 1:
            st.code("Screen: Zabi Jihar ku (Select State):\n1. Kano\n2. Borno\n3. Kaduna\n4. Katsina", language="text")
            state = st.selectbox("Your Input:", ["1", "2", "3", "4"], key="s_select")
            if st.button("Send", key="b1"):
                st.session_state.choices.append(state)
                st.session_state.ussd_step = 2
                st.rerun()

        elif st.session_state.ussd_step == 2:
            st.code("Screen: Wani taki za a yi amfani da shi? (Select Fertilizer Plans):\n1. NPK 15:15:15\n2. Urea\n3. Babu Taki (None)", language="text")
            fert = st.selectbox("Your Input:", ["1", "2", "3"], key="f_select")
            if st.button("Send", key="b2"):
                st.session_state.choices.append(fert)

                crop_map = {"1": "Millet", "2": "Sorghum", "3": "Maize"}
                state_map = {"1": "Kano", "2": "Borno", "3": "Kaduna", "4": "Katsina"}
                fert_map = {"1": "NPK_15_15_15", "2": "Urea", "3": "None"}

                c = crop_map[st.session_state.choices[0]]
                s = state_map[st.session_state.choices[1]]
                f = fert_map[st.session_state.choices[2]]

                # Fetch baseline local weather attributes matched to state parameters
                rain = 580.0 if s == "Borno" else (940.0 if s == "Kaduna" else 820.0)
                temp = 33.8 if s == "Borno" else (29.8 if s == "Kaduna" else 31.2)

                payload = pd.DataFrame([{
                    'state': s, 'latitude': 11.8, 'longitude': 8.5,
                    'crop_type': c, 'annual_rainfall_mm': rain, 'avg_temperature_c': temp,
                    'fertilizer_applied': f, 'satellite_ndvi_peak': 0.45,
                    'heat_moisture_index': rain / (temp + 10)
                }])
                for col in ['state', 'crop_type', 'fertilizer_applied']:
                    payload[col] = payload[col].astype('category')

                pred = engine.predict(payload)[0]
                st.session_state.result = f"END Hasashen amfanin gona ({c} in {s}): {pred:.2f} Tons/Ha.\n\nShawara: Yanayin damina yana da kyau. Tabbatar an cire ciyawa akan lokaci."
                st.session_state.ussd_step = 3
                st.rerun()

        elif st.session_state.ussd_step == 3:
            st.code(st.session_state.result, language="text")
            if st.button("Reset Session"):
                st.session_state.ussd_step = 0
                st.session_state.choices = []
                st.rerun()

# -------------------------------------------------------------------------
# TAB 2: SMARTPHONE APP INTERFACE (High-Bandwidth Option)
# -------------------------------------------------------------------------
with tab2:
    st.subheader("High-Fidelity Cooperative Dashboard Scenario Engine")
    st.write("Simulates interactive app requests using real-time variable mapping sliders.")

    col1, col2 = st.columns(2)
    with col1:
        in_state = st.selectbox("State Territory Location", ["Kano", "Borno", "Kaduna", "Katsina"])
        in_crop = st.selectbox("Cultivated Security Crop", ["Maize", "Sorghum", "Millet"])
        in_fert = st.selectbox("Fertilizer Input Matrix", ["Urea", "NPK_15_15_15", "None"])
    with col2:
        in_rain = st.slider("Annual Rainfall Depth (mm)", 400.0, 1200.0, 750.0)
        in_temp = st.slider("Average Ambient Temperature (°C)", 20.0, 45.0, 31.0)
        in_ndvi = st.slider("Satellite NDVI Vegetation Index", 0.1, 0.9, 0.52)

    smart_payload = pd.DataFrame([{
        'state': in_state, 'latitude': 11.5, 'longitude': 8.5,
        'crop_type': in_crop, 'annual_rainfall_mm': in_rain, 'avg_temperature_c': in_temp,
        'fertilizer_applied': in_fert, 'satellite_ndvi_peak': in_ndvi,
        'heat_moisture_index': in_rain / (in_temp + 10)
    }])
    for col in ['state', 'crop_type', 'fertilizer_applied']:
        smart_payload[col] = smart_payload[col].astype('category')

    smart_pred = engine.predict(smart_payload)[0]
    st.metric(label=f"Predicted {in_crop} Yield Output", value=f"{smart_pred:.2f} Metric Tons / Hectare")
    st.progress(min(max(smart_pred / 4.0, 0.0), 1.0))
