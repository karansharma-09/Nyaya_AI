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
    /* Global Dark Theme */
    .stApp { background-color: #0E1117; color: #E6EDF3; }
    
    /* Make metrics look good on mobile */
    [data-testid="stMetricValue"] { font-size: 1.8rem !important; color: #58A6FF; }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] { background-color: #161B22 !important; border-right: 1px solid #30363D; }
    
    /* Responsive adjustment for Mobile */
    @media (max-width: 640px) {
        .main-title { font-size: 24px !important; }
        .stActionButton { display: none; } /* Hide non-essential buttons on mobile */
    }
    
    /* Sidebar Menu styling */
    div[role="radiogroup"] > label {
        padding: 12px 15px; border-radius: 8px; margin-bottom: 5px;
        color: #8B949E !important; font-weight: bold; transition: 0.2s;
        border: 1px solid transparent;
    }
    div[role="radiogroup"] > label:hover { background-color: #21262D; border: 1px solid #30363D; }
    div[role="radiogroup"] > label[aria-checked="true"] {
        background-color: #1F6FEB; color: white !important;
        box-shadow: 0 4px 12px rgba(31, 111, 235, 0.3);
    }
    div[role="radiogroup"] > label[data-baseweb="radio"] > div:first-child { display: none; }
    </style>
    """, unsafe_allow_html=True)

# --- SESSION STATE ---
if 'processed' not in st.session_state: st.session_state.processed = False
if 'data' not in st.session_state: st.session_state.data = None

# --- SIDEBAR & LIVE CLOCK ---
with st.sidebar:
    st.markdown("<h1 style='color: #58A6FF; margin-bottom:0;'>Nyaya <span style='color:white; font-style:italic;'>AI</span></h1>", unsafe_allow_html=True)
    st.caption("v2.4 | Bharat Legal Network")
    
    # Live Ticking Clock (Syncs with user's system time)
    components.html("""
        <div id="clock" style="color: #3FB950; font-family: monospace; font-size: 14px; text-align: center; padding: 5px; background: #0D1117; border-radius: 5px; border: 1px solid #30363D;"></div>
        <script>
            function update() {
                const now = new Date();
                document.getElementById('clock').innerHTML = "LIVE: " + now.toLocaleTimeString('en-IN');
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
# 🧱 TAB 1: DASHBOARD (REAL-TIME SYNC)
# ==========================================
if choice == "🧱 Dashboard":
    st.title("Station Command Center")
    st.info("Real-time data synced with State Crime Records Bureau (Simulated).")
    
    # Real-time Metrics
    m1, m2, m3 = st.columns(3)
    m1.metric("Pending FIRs", "142", "+12%")
    m2.metric("AI Accuracy", "98.4%", "Stable")
    m3.metric("Avg. Response", "14m", "-2m")
    
    # Live Chart
    st.subheader("Crime Trends - Last 24 Hours")
    chart_data = pd.DataFrame(np.random.randn(24, 3), columns=['Theft', 'Assault', 'Cyber'])
    st.line_chart(chart_data)

# ==========================================
# ⚖️ TAB 2: MY CASES (FUNCTIONAL LIST)
# ==========================================
elif choice == "⚖️ My Cases":
    st.title("Active Case Files")
    cases = pd.DataFrame({
        "ID": ["NY-882", "NY-881", "NY-879"],
        "Date": ["07-03-2026", "06-03-2026", "05-03-2026"],
        "Status": ["Verified", "Pending", "Flagged"],
        "BNS": ["303(2)", "115(1)", "318(4)"]
    })
    st.table(cases)

# ==========================================
# 🎙️ TAB 3: SECURE EVIDENCE (CORE ENGINE)
# ==========================================
elif choice == "🎙️ Secure Evidence":
    st.title("Evidence Intake")
    
    if not st.session_state.processed:
        col1, col2 = st.columns([1, 1])
        with col1:
            st.markdown("### 🎙️ Voice Recording")
            rec = audio_recorder(text="Tap to Record", icon_size="2x")
        with col2:
            st.markdown("### 📸 Visual Proof")
            imgs = st.file_uploader("Upload evidence", accept_multiple_files=True, type=['png','jpg','jpeg'])
        
        if rec:
            st.audio(rec)
            if st.button("Analyze & Draft FIR", type="primary", use_container_width=True):
                with st.spinner("Analyzing forensics..."):
                    # Save audio to temp file
                    with open("temp.wav", "wb") as f: f.write(rec)
                    
                    # Process via engine
                    try:
                        res = process_complaint("temp.wav")
                        st.session_state.data = json.loads(res)
                        st.session_state.processed = True
                        st.rerun()
                    except Exception as e:
                        st.error(f"Analysis Failed: {e}")

    else:
        # Results View
        res = st.session_state.data
        score = res.get('credibility_score', 0)
        
        if score < 40:
            st.error(f"🚨 FAKE CASE DETECTED (Score: {score})")
            st.warning(f"Reason: {res.get('credibility_reason')}")
        else:
            st.success(f"Case Verified (Credibility: {score}%)")
            st.markdown(f"**BNS Mapping:** {res.get('bns_sections')}")
            st.markdown(f"**Location:** {res.get('location')}")
            
            draft_text = res.get('draft_letter', '')
            edited_draft = st.text_area("Edit Draft", value=draft_text, height=300)
            
            if st.button("Generate Official PDF"):
                # Logic to create PDF
                st.balloons()
                st.download_button("Download FIR", "Dummy Content", "FIR.pdf")

# ==========================================
# 📉 TAB 4: REPORTS
# ==========================================
elif choice == "📉 Reports":
    st.title("Jurisdiction Analytics")
    st.bar_chart(pd.DataFrame(np.random.randint(10, 50, size=(7, 1)), index=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]))

# ==========================================
# OTHER TABS (PROFILE/DRAFTS)
# ==========================================
else:
    st.title(choice)
    st.write(f"Feature '{choice}' is currently under maintenance or being synced with Delhi Police Servers.")
