import streamlit as st
import streamlit.components.v1 as components
import json
import os
import hashlib
import pandas as pd
import numpy as np
from datetime import datetime
from audio_recorder_streamlit import audio_recorder
from engine import process_complaint
from fpdf import FPDF

def create_pdf(text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    clean_text = text.encode('latin-1', 'ignore').decode('latin-1')
    for line in clean_text.split('\n'):
        pdf.multi_cell(0, 10, txt=line, align='L')
    return pdf.output(dest='S').encode('latin-1')

st.set_page_config(page_title="Nyaya AI Dashboard", layout="wide", initial_sidebar_state="expanded")

if 'data' not in st.session_state: st.session_state.data = None
if 'processed' not in st.session_state: st.session_state.processed = False

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #E6EDF3; }
    h1, h2, h3 { color: #FFFFFF; font-family: 'Helvetica Neue', sans-serif; }
    [data-testid="stSidebar"] { background-color: #161B22 !important; border-right: 1px solid #30363D; }
    div[role="radiogroup"] > label { padding: 10px 15px; border-radius: 8px; margin-bottom: 5px; color: #8B949E !important; font-weight: bold; transition: 0.3s; }
    div[role="radiogroup"] > label:hover { background-color: #21262D; color: white !important; }
    div[role="radiogroup"] > label[data-baseweb="radio"] > div:first-child { display: none; }
    div[role="radiogroup"] > label[aria-checked="true"] { background-color: #1F6FEB; color: white !important; border-left: 4px solid #58A6FF; }
    </style>
    """, unsafe_allow_html=True)

with st.sidebar:
    st.markdown("""
        <div style="padding: 10px 0px 10px 0px;">
            <h1 style="color: #58A6FF; margin:0; font-size:32px;">Nyaya <span style="color: white; font-style: italic;">AI</span></h1>
            <p style="color: #8B949E; font-size: 11px; letter-spacing: 1px; margin-top:0;">BHARAT LEGAL NETWORK</p>
        </div>
    """, unsafe_allow_html=True)
    
    # --- LIVE DIGITAL CLOCK ---
    components.html(
        """
        <div id="clock" style="color: #58A6FF; font-family: monospace; font-size: 16px; font-weight: bold; padding: 10px; background-color: #21262D; border-radius: 5px; text-align: center; border: 1px solid #30363D;"></div>
        <script>
            function updateTime() {
                var now = new Date();
                document.getElementById('clock').innerHTML = now.toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' });
                setTimeout(updateTime, 1000);
            }
            updateTime();
        </script>
        """, height=60
    )
    
    menu_options = ["🧱 Dashboard", "⚖️ My Cases", "📄 FIR Drafts", "🎙️ Secure Evidence", "👤 User Profile", "📉 Reports"]
    selected_tab = st.radio("Menu", menu_options, index=3, label_visibility="collapsed")

# --- ONLY SHOWING THE MAIN TAB LOGIC FOR BREVITY ---
if selected_tab == "🎙️ Secure Evidence":
    st.title("Secure Evidence Intake")
    st.markdown("Record live audio or upload files for AI BNS mapping.")
    
    if not st.session_state.processed:
        with st.container(border=True):
            st.write("🔴 **Live Voice Recording** (In-App Mic)")
            recorded_audio = audio_recorder(text="Click mic to record", icon_size="2x", icon_name="microphone")
            if recorded_audio:
                st.audio(recorded_audio, format="audio/wav")
                st.success("Audio recorded successfully!")
        
        st.markdown("<h4 style='text-align: center;'>OR</h4>", unsafe_allow_html=True)
        
        c_audio, c_visual = st.columns(2)
        with c_audio:
            with st.container(border=True):
                st.write("📁 **Upload Audio File**")
                audio_file = st.file_uploader("", type=["mp3", "wav", "m4a"])
                
        with c_visual:
            with st.container(border=True):
                st.write("📸 **Upload Visual Evidence**")
                image_files = st.file_uploader("", type=["jpg", "png", "jpeg"], accept_multiple_files=True)

        final_audio_bytes = recorded_audio if recorded_audio else (audio_file.getbuffer() if audio_file else None)

        if final_audio_bytes:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Generate Intelligence Report 🚀", type="primary", use_container_width=True):
                with st.spinner("Analyzing forensics & verifying credibility..."):
                    audio_path = "temp_audio.wav"
                    with open(audio_path, "wb") as f: f.write(final_audio_bytes)
                    
                    img_paths = []
                    if image_files:
                        for img in image_files:
                            p = f"temp_{img.name}"
                            with open(p, "wb") as f: f.write(img.getbuffer())
                            img_paths.append(p)
                    
                    try:
                        result = process_complaint(audio_path, img_paths)
                        st.session_state.data = json.loads(result)
                        st.session_state.processed = True
                        st.rerun() 
                    except Exception as e:
                        st.error(f"Error: {e}")
                    finally:
                        if os.path.exists(audio_path): os.remove(audio_path)
                        for p in img_paths:
                            if os.path.exists(p): os.remove(p)
    else:
        # --- RESULTS VIEW WITH FAKE DETECTION LOGIC ---
        data = st.session_state.data
        if st.button("⟵ Upload New Evidence"):
            st.session_state.data = None
            st.session_state.processed = False
            st.rerun()
            
        st.divider()
        col1, col2 = st.columns([1.2, 1])
        
        with col1:
            with st.container(border=True):
                st.subheader("Extracted Details (Zero Hallucination)")
                st.write(f"**Location:** {data.get('location')}")
                st.write(f"**Date/Time:** {data.get('date_time')}")
                st.info(f"**Summary:** {data.get('summary')}")
                st.write(f"**Visual Evidence:** {data.get('visual_evidence')}")
                
        with col2:
            with st.container(border=True):
                st.subheader("BNS Mapping & Score")
                st.error(data.get("bns_sections", "N/A"))
                score = data.get('credibility_score', 80)
                
                # COLOR CODE THE SCORE
                if score >= 70:
                    st.success(f"Credibility Score: {score}/100")
                elif score >= 40:
                    st.warning(f"Credibility Score: {score}/100")
                else:
                    st.error(f"Credibility Score: {score}/100 🚨 FAKE/PRANK DETECTED")
                
                st.caption(f"Reason: {data.get('credibility_reason')}")
        
        # --- DRAFTING LOGIC BASED ON SCORE ---
        st.divider()
        if score < 40 or data.get("draft_letter") == "REJECTED":
            st.error("🚨 **FIR DRAFTING ABORTED:** The AI has flagged this statement as fake, logically impossible, or a prank. Auto-drafting is disabled for non-credible inputs to prevent system misuse.")
        else:
            with st.container(border=True):
                st.subheader("Final Legal Application")
                st.caption(f"Status: AI Generated | Validated timestamp attached in text.")
                draft = st.text_area("Review and Edit:", value=data.get("draft_letter"), height=300)
                pdf_bytes = create_pdf(draft)
                st.download_button("Export Official PDF", data=pdf_bytes, file_name=f"Nyaya_FIR_{datetime.now().strftime('%Y%m%d')}.pdf", type="primary")

# Note: The code for the other tabs (Dashboard, etc.) remains exactly the same as the previous response.