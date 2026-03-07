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
    # Cleaning text for FPDF compatibility
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
        "Date": ["07-03-2026", "06-03-2026", "05-03-2026"],
        "Status": ["Verified", "Pending", "Flagged"],
        "BNS": ["303(2)", "115(1)", "318(4)"]
    })
    st.dataframe(cases, use_container_width=True)

elif choice == "🎙️ Secure Evidence":
    st.title("Evidence Intake & Analysis")
    
    if not st.session_state.processed:
        input_type = st.tabs(["🎙️ Record Live", "📁 Upload Audio"])
        
        with input_type[0]:
            st.markdown("### Live Voice Recording")
            rec = audio_recorder(text="Tap to Record Statement", icon_size="2x", icon_name="microphone")
            if rec: st.audio(rec)
        
        with input_type[1]:
            st.markdown("### Upload Pre-recorded Audio")
            uploaded_audio = st.file_uploader("Select MP3, WAV, or M4A", type=['mp3', 'wav', 'm4a'])
            if uploaded_audio: st.audio(uploaded_audio)

        st.divider()
        st.markdown("### 📸 Visual Evidence (Optional)")
        imgs = st.file_uploader("Incident Photos", accept_multiple_files=True, type=['png','jpg','jpeg'])
        
        final_audio_bytes = rec if rec else (uploaded_audio.getbuffer() if uploaded_audio else None)

        if final_audio_bytes:
            if st.button("Generate Intelligence Report 🚀", type="primary", use_container_width=True):
                with st.spinner("Analyzing forensics..."):
                    audio_path = "temp_audio.wav"
                    with open(audio_path, "wb") as f: f.write(final_audio_bytes)
                    
                    img_paths = []
                    if imgs:
                        for img in imgs:
                            p = f"temp_{img.name}"; with open(p, "wb") as f: f.write(img.getbuffer())
                            img_paths.append(p)
                    
                    try:
                        res = process_complaint(audio_path, img_paths)
                        st.session_state.data = json.loads(res)
                        st.session_state.processed = True
                        st.rerun()
                    except Exception as e:
                        st.error(f"Analysis Failed: {e}")
                    finally:
                        if os.path.exists(audio_path): os.remove(audio_path)
                        for p in img_paths: 
                            if os.path.exists(p): os.remove(p)
    else:
        # RESULTS VIEW
        res = st.session_state.data
        score = res.get('credibility_score', 0)
        
        col1, col2 = st.columns(2)
        with col1:
            if score < 40:
                st.error(f"🚨 FAKE CASE DETECTED (Score: {score})")
                st.warning(f"Reason: {res.get('credibility_reason')}")
            else:
                st.success(f"Case Verified (Score: {score}%)")
                st.write(f"**Location:** {res.get('location')}")
                st.write(f"**BNS Mapping:** {res.get('bns_sections')}")
        
        if score >= 40:
            st.divider()
            draft_text = res.get('draft_letter', '')
            edited_draft = st.text_area("Final Review:", value=draft_text, height=300)
            
            pdf_data = create_pdf(edited_draft)
            st.download_button(
                label="📥 Download Official FIR PDF",
                data=pdf_data,
                file_name=f"FIR_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                mime="application/pdf",
                type="primary"
            )

elif choice == "📉 Reports":
    st.title("Jurisdiction Analytics")
    st.bar_chart(pd.DataFrame(np.random.randint(10, 50, size=(7, 1)), index=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]))

else:
    st.title(choice)
    st.info("System Ready. Waiting for local API sync.")
