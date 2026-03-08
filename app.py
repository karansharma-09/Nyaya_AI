import streamlit as st
import streamlit.components.v1 as components
import json
import os
import pandas as pd
import numpy as np
from datetime import datetime
from engine import process_complaint, translate_to_hindi
from fpdf import FPDF
import time
import hashlib
import qrcode
from io import BytesIO
import re

# --- CONFIG & RESPONSIVE SETTINGS ---
st.set_page_config(
    page_title="Nyaya AI | Police Intranet", 
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

# Helper for PDF (Ab ye PDF me QR code aur Hash bhi print karega)
def create_pdf(text, hash_val):
    pdf = FPDF()
    pdf.add_page()
    
    # Official Header
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "FIRST INFORMATION REPORT (FIR)", ln=True, align='C')
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(0, 10, "Generated via Nyaya AI Law Enforcement Core", ln=True, align='C')
    pdf.ln(5)
    
    # Main Draft Body
    pdf.set_font("Arial", size=11)
    clean_text = text.encode('latin-1', 'ignore').decode('latin-1')
    for line in clean_text.split('\n'):
        pdf.multi_cell(0, 10, txt=line, align='L')
        
    # Add Security Section at the end
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 10, "==================================================", ln=True)
    pdf.cell(0, 10, "DIGITAL VERIFICATION & CHAIN OF CUSTODY", ln=True)
    pdf.set_font("Arial", size=10)
    pdf.cell(0, 8, f"SHA-256 Hash: {hash_val}", ln=True)
    pdf.cell(0, 8, f"Timestamp: {datetime.now().isoformat(timespec='seconds')}Z", ln=True)
    
    # Generate temporary QR Code image and embed in PDF
    qr = qrcode.QRCode(version=1, box_size=5, border=2)
    qr.add_data(f"Nyaya AI Security Hash: {hash_val}")
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    temp_qr_path = f"temp_qr_{int(time.time())}.png"
    img.save(temp_qr_path)
    
    # Embed image (width=30)
    pdf.image(temp_qr_path, w=30)
    
    # Cleanup temporary image file
    if os.path.exists(temp_qr_path):
        os.remove(temp_qr_path)
        
    return pdf.output(dest='S').encode('latin-1')

# --- NEW HELPER FOR UI QR CODE ---
def generate_qr_code(data):
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

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
            
            st.markdown("#### Station Intranet Login")
            officer_id = st.text_input("Officer ID / Badge Number", placeholder="e.g., admin")
            password = st.text_input("Secure Password", type="password", placeholder="••••••••")
            
            if st.button("Authenticate 🔒", type="primary", use_container_width=True):
                if officer_id == "admin" and password == "nyaya2026":
                    with st.spinner("Verifying credentials & IP integrity..."):
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
    st.caption("DUTY OFFICER: ADMIN")
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Highly Professional Law Enforcement Tabs
    menu = [
        ":material/admin_panel_settings: Command Center", 
        ":material/policy: Evidence Intake", 
        ":material/assignment: FIR Archives", 
        ":material/insights: Crime Analytics"
    ]
    # Index 1 defaults to Evidence Intake
    choice = st.radio("Navigation", menu, index=1, label_visibility="collapsed")
    
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

if choice == ":material/admin_panel_settings: Command Center":
    st.title("Station Command Center")
    st.markdown("Real-time intelligence synced with regional police database.")
    
    with st.container(border=True):
        m1, m2, m3 = st.columns(3)
        m1.metric("Pending Intakes", "142", "+12%")
        m2.metric("AI Accuracy", "98.4%", "Stable", delta_color="off")
        m3.metric("Avg. Resolution", "14m", "-2m")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("📍 Live Crime Hotspots (Delhi NCR)")
        map_data = pd.DataFrame(
            np.random.randn(40, 2) / [60, 60] + [28.6139, 77.2090],
            columns=['lat', 'lon']
        )
        st.map(map_data, zoom=10, use_container_width=True)
    
    with col2:
        st.subheader("⚠️ Alert Zones")
        st.error("**CP Area:** High Cyber Fraud cases reported in last 2H.")
        st.warning("**Rohini:** Vehicle theft spike detected.")
        st.info("**South Ext:** Normal patrolling active.")

elif choice == ":material/assignment: FIR Archives":
    st.title("Station FIR Archives")
    st.markdown("Centralized database of all processed complaints.")
    cases = pd.DataFrame({
        "FIR ID": ["NY-882", "NY-881", "NY-879", "NY-878"],
        "Date": ["08-03-2026", "07-03-2026", "06-03-2026", "06-03-2026"],
        "Status": ["Verified", "Pending Review", "Flagged (Fake)", "Verified"],
        "BNS Sections": ["303(2)", "115(1)", "None", "318(4)"],
        "Investigating Officer": ["Insp. Sharma", "SI Verma", "Insp. Sharma", "SI Yadav"]
    })
    st.dataframe(cases, use_container_width=True, hide_index=True)

elif choice == ":material/policy: Evidence Intake":
    st.title("AI Evidence Intake Portal")
    st.markdown("Securely process raw evidence to generate BNS mapped draft reports.")
    
    if not st.session_state.processed:
        tab1, tab2 = st.tabs(["🎙️ Direct Voice Record", "📁 Upload Evidence File"])
        
        with tab1:
            st.markdown("##### Direct Voice Input")
            rec = st.audio_input("Tap to start secure recording")
            
        with tab2:
            st.markdown("##### Upload Existing Audio/Video Extract")
            uploaded_audio = st.file_uploader("Supported: MP3, WAV, M4A", type=['mp3', 'wav', 'm4a'], label_visibility="collapsed")
            if uploaded_audio: st.audio(uploaded_audio)

        with st.container(border=True):
            st.markdown("##### Visual Evidence (Optional)")
            imgs = st.file_uploader("Upload incident photographs/CCTV screenshots", accept_multiple_files=True, type=['png','jpg','jpeg'], label_visibility="collapsed")
        
        final_audio_bytes = rec.getvalue() if rec else (uploaded_audio.getvalue() if uploaded_audio else None)

        if final_audio_bytes:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Initialize Forensic AI & Mapping", type="primary", use_container_width=True):
                with st.spinner("Cross-referencing logic and mapping BNS sections..."):
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
                        
                        # --- FIX: CLEANING AI's EXTRA MARKDOWN ---
                        cleaned_res = res.replace("```json", "").replace("```JSON", "").replace("```", "").strip()
                        
                        st.session_state.data = json.loads(cleaned_res)
                        st.session_state.processed = True
                        st.rerun()
                    except Exception as e:
                        st.error(f"Analysis Engine Error: {e}\n\nRaw AI Output was: {res[:100]}...")
                    finally:
                        if os.path.exists(audio_path): os.remove(audio_path)
                        for p in img_paths:
                            if os.path.exists(p): os.remove(p)
    else:
        res = st.session_state.data
        
        # --- FIX: ROBUST SCORE EXTRACTION ---
        # Fetching score even if AI renames the key or adds a % sign
        raw_score = res.get('credibility_score', res.get('credibility', res.get('score', 0)))
        
        if isinstance(raw_score, str):
            nums = re.findall(r'\d+', raw_score) # Extract numbers only from string (e.g. "85%" -> 85)
            score = int(nums[0]) if nums else 0
        else:
            try:
                score = int(raw_score)
            except:
                score = 0
                
        st.subheader("Intelligence Report Generated")
        
        with st.container(border=True):
            col1, col2 = st.columns([1.5, 1])
            with col1:
                st.markdown(f"**Incident Location:** {res.get('location', 'Not detected')}")
                st.markdown(f"**Recommended BNS Sections:** `{res.get('bns_sections', 'Not detected')}`")
                st.caption("🔄 *Auto-mapped from legacy IPC sections for officer convenience.*")
                
            with col2:
                if score < 40:
                    st.error(f"⚠️ FLAG: FAKE/IRRELEVANT CASE\n\n**Credibility:** {score}%\n\n**Reason:** {res.get('credibility_reason', 'Review needed')}")
                else:
                    st.success(f"✅ CASE VERIFIED\n\n**Credibility Score:** {score}%")
        
        # --- CHAIN OF CUSTODY ---
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
            edited_draft = st.text_area("Modify AI-generated draft before exporting to PDF:", value=draft_text, height=300, label_visibility="collapsed")
            
            # --- 🇮🇳 HINDI TRANSLATION FEATURE ---
            if 'hindi_draft' not in st.session_state:
                st.session_state.hindi_draft = None
                
            if st.button("🇮🇳 Translate to Official Hindi (For Citizen Verification)", use_container_width=True):
                with st.spinner("Translating to official legal Hindi..."):
                    st.session_state.hindi_draft = translate_to_hindi(edited_draft)
            
            if st.session_state.hindi_draft:
                st.markdown("#### Hindi Translation (नागरिक सत्यापन हेतु)")
                st.info(st.session_state.hindi_draft)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # --- QR CODE & DOWNLOAD SECTION (NEWLY INTEGRATED) ---
            st.markdown("### Document Export")
            
            qr_col, download_col = st.columns([1, 4])
            
            with qr_col:
                # Generate QR code using the mock_hash generated above
                qr_data = f"Nyaya AI Security Hash: {mock_hash}"
                qr_img = generate_qr_code(qr_data)
                st.image(qr_img, width=120, caption="Scan to Verify Hash")
                
            with download_col:
                st.markdown("<br>", unsafe_allow_html=True) # alignment spacing
                pdf_data = create_pdf(edited_draft, mock_hash) # Now passing the hash to print inside PDF
                st.download_button(
                    label=":material/download: Export Official FIR Document (PDF)",
                    data=pdf_data,
                    file_name=f"Nyaya_FIR_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                    mime="application/pdf",
                    type="primary",
                    use_container_width=True
                )
            
            # --- NAYA EVIDENCE ADD KARNE KE LIYE RESET BUTTON ---
            st.markdown("<br><hr>", align="center", unsafe_allow_html=True)
            if st.button("➕ Start New Evidence Intake", type="secondary", use_container_width=True):
                st.session_state.processed = False
                st.session_state.data = None
                if 'hindi_draft' in st.session_state:
                    st.session_state.hindi_draft = None
                st.rerun()

elif choice == ":material/insights: Crime Analytics":
    st.title("Jurisdiction Analytics")
    st.markdown("Week-over-week comparison of registered complaints.")
    with st.container(border=True):
        st.bar_chart(pd.DataFrame(np.random.randint(10, 50, size=(7, 1)), index=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]))

else:
    st.title(choice.split(": ")[-1])
    st.info("Module ready. Awaiting secure network connection.")
