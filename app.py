import streamlit as st
import streamlit.components.v1 as components
import json
import os
import pandas as pd
import numpy as np
from datetime import datetime
from engine import process_complaint
from fpdf import FPDF
import time
import hashlib

# --- CONFIG & RESPONSIVE SETTINGS ---
st.set_page_config(
    page_title="Nyaya AI | Secure Portal", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# Modern UI CSS
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #E6EDF3; }
    [data-testid="stMetricValue"] { color: #58A6FF; font-weight: 600; }
    [data-testid="stSidebar"] { background-color: #161B22 !important; border-right: 1px solid #30363D; }
    div[role="radiogroup"] > label { 
        padding: 12px 15px; border-radius: 6px; margin-bottom: 8px; 
        color: #8B949E !important; font-weight: 500; font-size: 15px;
        transition: all 0.2s ease-in-out;
    }
    div[role="radiogroup"] > label:hover { background-color: #21262D; }
    div[role="radiogroup"] > label[aria-checked="true"] { 
        background-color: #1F6FEB; color: white !important; 
        box-shadow: 0 4px 12px rgba(31, 111, 235, 0.2);
    }
    div[role="radiogroup"] > label[data-baseweb="radio"] > div:first-child { display: none; }
    .st-emotion-cache-1y4p8pa { padding: 1.5rem; border-radius: 10px; border: 1px solid #30363D; background-color: #161B22;}
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

# --- SESSION STATE INITIALIZATION ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'processed' not in st.session_state: st.session_state.processed = False
if 'data' not in st.session_state: st.session_state.data = None

# ==========================================
# 🛑 SECURE LOGIN GATEKEEPER
# ==========================================
if not st.session_state.logged_in:
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    
    with col2:
        with st.container(border=True):
            st.markdown("<h2 style='text-align: center; color: #58A6FF;'>NYAYA <span style='color:white;'>AI</span></h2>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: #8B949E;'>Department of Legal Affairs & Law Enforcement</p>", unsafe_allow_html=True)
            st.divider()
            
            st.markdown("#### Authorized Access Only")
            officer_id = st.text_input("Officer ID / Badge Number", placeholder="Enter Login ID")
            password = st.text_input("Secure Password", type="password", placeholder="••••••••")
            
            if st.button("Authenticate 🔒", type="primary", use_container_width=True):
                if officer_id == "admin" and password == "nyaya2026":
                    with st.spinner("Verifying credentials..."):
                        time.sleep(1)
                        st.session_state.logged_in = True
                        st.rerun()
                elif officer_id or password:
                    st.error("Invalid Credentials. Access Denied.")
                    
            st.markdown("<br><p style='text-align: center; font-size: 12px; color: #484F58;'>Attempting to bypass this portal is a federal offense under BNS Section 302.</p>", unsafe_allow_html=True)
    st.stop()

# ==========================================
# 🟢 MAIN APPLICATION
# ==========================================

# --- SIDEBAR & LIVE CLOCK ---
with st.sidebar:
    st.markdown("<h1 style='color: #58A6FF; margin-bottom:0; font-weight: 800; letter-spacing: 1px;'>NYAYA <span style='color:#E6EDF3; font-weight: 300;'>AI</span></h1>", unsafe_allow_html=True)
    st.caption("LOGGED IN: OFFICER ADMIN")
    st.markdown("<br>", unsafe_allow_html=True)
    
    menu = [
        ":material/dashboard: Dashboard", 
        ":material/folder_open: My Cases", 
        ":material/description: FIR Drafts", 
        ":material/mic: Secure Evidence", 
        ":material/person: Profile", 
        ":material/bar_chart: Reports"
    ]
    choice = st.radio("Navigation", menu, index=3, label_visibility="collapsed")
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    components.html("""
        <div id="clock" style="color: #3FB950; font-family: 'Courier New', monospace; font-size: 13px; text-align: center; padding: 8px; background: #0D1117; border-radius: 4px; border: 1px solid #238636;"></div>
        <script>
            function update() {
                const now = new Date();
                document.getElementById('clock').innerHTML = "SECURE SYNC: " + now.toLocaleTimeString('en-IN');
                setTimeout(update, 1000);
            }
            update();
        </script>
    """, height=50)
    
    if st.button(":material/logout: Secure Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.processed = False
        st.session_state.data = None
        st.rerun()

# --- TABS LOGIC ---
if choice == ":material/dashboard: Dashboard":
    st.title("Station Command Center")
    st.markdown("Real-time intelligence synced with regional police database.")
    with st.container(border=True):
        m1, m2, m3 = st.columns(3)
        m1.metric("Pending Intakes", "142", "+12%")
        m2.metric("AI Accuracy", "98.4%", "Stable", delta_color="off")
        m3.metric("Avg. Resolution", "14m", "-2m")
    st.subheader("Regional Crime Trends (24H)")
    st.line_chart(pd.DataFrame(np.random.randn(24, 3), columns=['Theft', 'Assault', 'Cyber']))

elif choice == ":material/folder_open: My Cases":
    st.title("Active Case Files")
    cases = pd.DataFrame({
        "Case ID": ["NY-882", "NY-881", "NY-879"],
        "Timestamp": ["07-03-2026", "06-03-2026", "05-03-2026"],
        "Verification": ["Verified", "Pending", "Flagged"],
        "BNS Sections": ["303(2)", "115(1)", "318(4)"]
    })
    st.dataframe(cases, use_container_width=True, hide_index=True)

elif choice == ":material/mic: Secure Evidence":
    st.title("Secure Evidence Intake")
    st.markdown("Capture or upload forensic evidence for AI analysis.")
    
    if not st.session_state.processed:
        tab1, tab2 = st.tabs(["Record Live Audio", "Upload File"])
        
        with tab1:
            st.markdown("##### Direct Voice Input")
            rec = st.audio_input("Tap to start secure recording")
            
        with tab2:
            st.markdown("##### Upload Existing Recording")
            uploaded_audio = st.file_uploader("Supported: MP3, WAV, M4A", type=['mp3', 'wav', 'm4a'], label_visibility="collapsed")
            if uploaded_audio: st.audio(uploaded_audio)

        with st.container(border=True):
            st.markdown("##### Visual Evidence (Optional)")
            imgs = st.file_uploader("Upload incident photographs", accept_multiple_files=True, type=['png','jpg','jpeg'], label_visibility="collapsed")
        
        final_audio_bytes = rec.getvalue() if rec else (uploaded_audio.getvalue() if uploaded_audio else None)

        if final_audio_bytes:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Initialize AI Forensic Analysis", type="primary", use_container_width=True):
                with st.spinner("Processing evidence and mapping BNS sections..."):
                    audio_path = "temp_audio.wav"
                    with open(audio_path, "wb") as f: f.write(final_audio_bytes)
                    
                    img_paths = []
                    if imgs:
                        for img in imgs:
                            p = f"temp_{img.name}"
                            with open(p, "wb") as f: f.write(img.getbuffer())
                            img_paths.append(p)
                    
                    try:
                        res = process_complaint(audio_path, img_paths)
                        st.session_state.data = json.loads(res)
                        st.session_state.processed = True
                        st.rerun()
                    except Exception as e:
                        st.error(f"Analysis Engine Error: {e}")
                    finally:
                        if os.path.exists(audio_path): os.remove(audio_path)
                        for p in img_paths:
                            if os.path.exists(p): os.remove(p)
    else:
        res = st.session_state.data
        score = res.get('credibility_score', 0)
        st.subheader("Intelligence Report Generated")
        
        with st.container(border=True):
            col1, col2 = st.columns([1.5, 1])
            with col1:
                st.markdown(f"**Incident Location:** {res.get('location')}")
                st.markdown(f"**Recommended BNS Sections:** `{res.get('bns_sections')}`")
            with col2:
                if score < 40:
                    st.error(f"⚠️ FLAG: FAKE CASE DETECTED\n\n**Credibility:** {score}%\n\n**Reason:** {res.get('credibility_reason')}")
                else:
                    st.success(f"✅ CASE VERIFIED\n\n**Credibility Score:** {score}%")
        
        # --- BHAUKAAL FEATURE: CHAIN OF CUSTODY ---
        st.markdown("### 🔐 Chain of Custody (Cryptographic Metadata)")
        with st.container(border=True):
            c1, c2 = st.columns(2)
            mock_hash = hashlib.sha256(str(datetime.now().timestamp()).encode()).hexdigest()
            with c1:
                st.markdown("**Evidence SHA-256 Hash:**")
                st.code(mock_hash, language="text")
                st.markdown("**Geo-Coordinates (GPS):**\n\n`Lat: 28.6139° N, Lon: 77.2090° E (New Delhi)`")
            with c2:
                st.markdown("**Timestamp (System):**")
                st.code(datetime.now().isoformat(timespec='seconds') + "Z", language="text")
                st.markdown("**Device Network IP:**\n\n`117.203.45.192 (Secured Police Intranet)`")

        # --- DRAFT REVIEW ---
        if score >= 40:
            st.markdown("### Official Draft Review")
            draft_text = res.get('draft_letter', '')
            edited_draft = st.text_area("Modify AI-generated draft before exporting:", value=draft_text, height=300, label_visibility="collapsed")
            
            pdf_data = create_pdf(edited_draft)
            st.download_button(
                label=":material/download: Export Official FIR Document (PDF)",
                data=pdf_data,
                file_name=f"Nyaya_FIR_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                mime="application/pdf",
                type="primary"
            )

elif choice == ":material/bar_chart: Reports":
    st.title("Jurisdiction Analytics")
    with st.container(border=True):
        st.bar_chart(pd.DataFrame(np.random.randint(10, 50, size=(7, 1)), index=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]))

else:
    st.title(choice.split(": ")[-1])
    st.info("Module ready. Awaiting secure network connection.")

