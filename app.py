import streamlit as st
import streamlit.components.v1 as components
import json
import os
import pandas as pd
import numpy as np
from datetime import datetime
from audio_recorder_streamlit import audio_recorder
from engine import process_complaint
from fpdf import FPDF

# --- CONFIG & RESPONSIVE SETTINGS ---
st.set_page_config(
    page_title="Nyaya AI | BNS Portal", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# Custom CSS for Mobile Optimization & Dark Theme
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #E6EDF3; }
    [data-testid="stMetricValue"] { font-size: 1.8rem !important; color: #58A6FF; }
    [data-testid="stSidebar"] { background-color: #161B22 !important; border-right: 1px solid #30363D; }
    @media (max-width: 640px) {
        .main-title { font-size: 24px !important; }
    }
    div[role="radiogroup"] > label {
        padding: 12px 15px; border-radius: 8px; margin-bottom: 5px;
        color: #8B949E !important; font-weight: bold; transition: 0.2s;
    }
    div[role="radiogroup"] > label[aria-checked="true"] {
        background-color: #1F6FEB; color: white !important;
    }
    div[role="radiogroup"] > label[data-baseweb="radio"] > div:first-child { display: none; }
    </style>
    """, unsafe_allow_html=True)

# Helper for PDF
def create_pdf(text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=11)
    clean_text = text.encode('latin-1', 'ignore').decode('latin-1')
    for line in clean_text.split('\n'):
        pdf.multi_cell(0, 10, txt=line, align='L')
    return pdf.output(dest='S').encode('latin-1')

# --- SESSION STATE ---
if 'processed' not in st.session_state: st.session_state.processed = False
if 'data' not in st.session_state: st.session_state.data = None

# --- SIDEBAR & LIVE CLOCK ---
with st.sidebar:
    st.markdown("<h1 style='color: #58A6FF; margin-bottom:0;'>Nyaya <span style='color:white; font-style:italic;'>AI</span></h1>", unsafe_allow_html=True)
    st.caption("v2.5 | Bharat Legal Network")
    
    components.html("""
        <div id="clock" style="color: #3FB950; font-family: monospace; font-size: 14px; text-align: center; padding: 5px; background: #0D1117; border-radius: 5px; border: 1px solid #30363D;"></div>
        <script>
            function update() {
                const now = new Date();
                document.getElementById('clock').innerHTML = "SYSTEM TIME: " + now.toLocaleTimeString('en-IN');
                setTimeout(update, 1000);
            }
            update();
        </script>
    """, height=40)
    
    menu = ["🧱 Dashboard", "⚖️ My Cases", "📄 FIR Drafts", "🎙️ Secure Evidence", "👤 Profile", "📉 Reports"]
    choice = st.radio("Navigation", menu, index=3, label_visibility="collapsed")
    
    st.markdown("---")
    if st.button("Reset Session", use_container_width=True):
        st.session_state.processed = False
        st.session_state.data = None
        st.rerun()

# ==========================================
# 🧱 TABS LOGIC
# ==========================================

if choice == "🧱 Dashboard":
    st.title("Station Command Center")
    m1, m2, m3 = st.columns(3)
    m1.metric("Pending FIRs", "142", "+12%")
    m2.metric("AI Accuracy", "98.4%", "Stable")
    m3.metric("Avg. Response", "14m", "-2m")
    st.subheader("Crime Trends - Last 24 Hours (Real-time Sync)")
    st.line_chart(pd.DataFrame(np.random.randn(24, 3), columns=['Theft', 'Assault', 'Cyber']))

elif choice == "⚖️ My Cases":
    st.title("Active Case Files")
    cases = pd.DataFrame({
        "ID": ["NY-882", "NY-881", "NY-879"],
        "Date": ["0
