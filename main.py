import streamlit as st
import pandas as pd
import numpy as np
import math
import joblib

# Load model and data
model = joblib.load("mlp_regressor_model.pkl")
# Load data directly from GitHub Excel
csv_url = "https://raw.githubusercontent.com/H-AYAH/Teachershortage-app/main/Schools(Secondary) (11).csv"
df = pd.read_csv(csv_url)

# Define policy brackets
policy_brackets = [
    {'streams': 1, 'enr_min': 0, 'enr_max': 180, 'cbe': 9},
    {'streams': 2, 'enr_min': 181, 'enr_max': 360, 'cbe': 19},
    {'streams': 3, 'enr_min': 361, 'enr_max': 540, 'cbe': 28},
    {'streams': 4, 'enr_min': 541, 'enr_max': 720, 'cbe': 38},
    {'streams': 5, 'enr_min': 721, 'enr_max': 900, 'cbe': 47},
    {'streams': 6, 'enr_min': 901, 'enr_max': 1080, 'cbe': 55},
    {'streams': 7, 'enr_min': 1081, 'enr_max': 1260, 'cbe': 63},
    {'streams': 8, 'enr_min': 1261, 'enr_max': 1440, 'cbe': 68},
    {'streams': 9, 'enr_min': 1441, 'enr_max': 1620, 'cbe': 76},
    {'streams': 10, 'enr_min': 1621, 'enr_max': 1800, 'cbe': 85},
    {'streams': 11, 'enr_min': 1801, 'enr_max': 1980, 'cbe': 93},
    {'streams': 12, 'enr_min': 1981, 'enr_max': 2160, 'cbe': 101},
]

# Helper functions
def get_policy_cbe(enrollment):
    for bracket in policy_brackets:
        if bracket['enr_min'] <= enrollment <= bracket['enr_max']:
            return bracket['cbe']
    return 93 + 8 * (math.ceil(enrollment / 180) - 11)

def calculate_likely_streams(cbe_actual):
    for bracket in policy_brackets:
        if cbe_actual <= bracket['cbe']:
            return bracket['streams']
    return math.ceil((cbe_actual - 93) / 8) + 11

# Streamlit UI
st.set_page_config(page_title="Teacher Shortage App", layout="centered")
st.title("📘 Teacher Shortage Predictor (Kenya)")

school_name = st.selectbox("🏫 Select a School", df['Institution_Name'].unique())

if school_name:
    school = df[df['Institution_Name'] == school_name].iloc[0]
    enrollment = school['TotalEnrolment']
    tod = school['TOD']
    policy_cbe = get_policy_cbe(enrollment)
    likely_streams = calculate_likely_streams(policy_cbe)

    input_data = pd.DataFrame({
        'TotalEnrolment': [enrollment],
        'TOD': [tod],
        'PolicyCBE': [policy_cbe],
        'Likely_Streams': [likely_streams]
    })

    prediction = model.predict(input_data)[0]

    st.subheader("📊 Prediction Summary")
    st.markdown(f"**Enrollment:** {int(enrollment)}")
    st.markdown(f"**Teachers on Duty (TOD):** {int(tod)}")
    st.markdown(f"**Policy CBE Required:** {int(policy_cbe)}")
    st.markdown(f"**Estimated Streams:** {likely_streams}")
    st.markdown(f"**Predicted Teacher Shortage:** 🧑‍🏫 **{round(prediction)}**")
