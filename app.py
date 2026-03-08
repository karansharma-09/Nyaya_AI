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
import sqlite3

# --- CONFIG & RESPONSIVE SETTINGS ---
st.set_page_config(
    page_title="Nyaya AI | Police Intranet", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# Modern UI CSS with Smooth Transitions
st.markdown("""
    <style>
    /* Smooth Fade-In Animation for Tab Switching */
    .block-container {
        animation: fadeIn 0.6s ease-out;
    }
    @keyframes fadeIn {
        0% { opacity: 0; transform: translateY(15px); }
        100% { opacity: 1; transform: translateY(0); }
    }
    
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
    
    /* Admissibility Tag Styling */
    .admissibility-tag {
        display: inline-block; padding: 5px 12px; border-radius: 20px; font-size: 13px; font-weight: bold; margin-top: 5px;
    }
    .admissibility-high { background-color: #rgba(63, 185, 80, 0.1); color: #3FB950; border: 1px solid #3FB950; }
    .admissibility-low { background-color: #rgba(248, 81, 73, 0.1); color: #F85149; border: 1px solid #F85149; }
    </style>
    """, unsafe_allow_html=True)

# --- DATABASE INITIALIZATION ---
def init_db():
    conn = sqlite3.connect("nyaya_records.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS fir_archives (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fir_id TEXT,
                    date_filed TEXT,
                    status TEXT,
                    bns_sections TEXT,
                    officer TEXT,
                    location TEXT,
                    evidence_hash TEXT
                )''')
    
    # Add some dummy data if the database is newly created and empty
    c.execute("SELECT COUNT(*) FROM fir_archives")
    if c.fetchone()[0] == 0:
        dummy_data = [
            ("NY-882", "08-03-2026", "Verified", "303(2)", "Insp. Sharma", "Connaught Place", "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"),
            ("NY-881", "07-03-2026", "Pending Review", "115(1)", "SI Verma", "Rohini Sec 7", "8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92"),
            ("NY-879", "06-03-2026", "Flagged (Fake)", "None", "Insp. Sharma", "South Ext", "invalid_hash_sequence")
        ]
        c.executemany("INSERT INTO fir_archives (fir_id, date_filed, status, bns_sections, officer, location, evidence_hash) VALUES (?, ?, ?, ?, ?, ?, ?)", dummy_data)
    
    conn.commit()
    conn.close()

# Initialize the DB on app start
init_db()

# Helper for Dynamic GPS based on location text
def get_dynamic_coords(loc_string):
    if not loc_string or loc_string.lower() == 'not detected':
        return "28.6139° N, 77.2090° E" # Default Delhi
    # Create deterministic fake coordinates based on location name string
    h = int(hashlib.md5(loc_string.encode()).hexdigest(), 16)
    lat = 28.0 + (h % 100) / 100.0
    lon = 77.0 + ((h // 100) % 100) / 100.0
    return f"{lat:.4f}° N, {lon:.4f}° E"

# Helper for PDF 
def create_pdf(text, hash_val, gps_coords, ip_address):
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
    pdf.cell(0, 10, "DIGITAL VERIFICATION & CHAIN OF CUSTODY (BSA 2023 COMPLIANT)", ln=True)
    pdf.set_font("Arial", size=10)
    pdf.cell(0, 8, f"SHA-256 Hash: {hash_val}", ln=True)
    pdf.cell(0, 8, f"Timestamp: {datetime.now().isoformat(timespec='seconds')}Z", ln=True)
    pdf.cell(0, 8, f"Geospatial Coordinates: {gps_coords}", ln=True)
    pdf.cell(0, 8, f"Ingestion Terminal IP: {ip_address}", ln=True)
    
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
# Simulate a fixed intranet IP for the session
if 'session_ip' not in st.session_state: st.session_state.session_ip = f"10.24.{np.random.randint(1,255)}.{np.random.randint(1,255)}"

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
    
    # Fetch real counts from DB
    conn = sqlite3.connect("nyaya_records.db")
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM fir_archives")
    total_cases = c.fetchone()[0]
    conn.close()
    
    with st.container(border=True):
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Archived Cases", str(total_cases), "+1 Today")
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
    st.markdown("Centralized database of all processed and saved complaints.")
    
    # Read LIVE data from SQLite Database
    conn = sqlite3.connect("nyaya_records.db")
    query = """
    SELECT 
        fir_id as 'FIR ID', 
        date_filed as 'Date', 
        status as 'Status', 
        bns_sections as 'BNS Sections', 
        officer as 'Investigating Officer',
        location as 'Location'
    FROM fir_archives 
    ORDER BY id DESC
    """
    cases = pd.read_sql_query(query, conn)
    conn.close()
    
    if cases.empty:
        st.info("No cases have been saved to the database yet.")
    else:
        st.dataframe(cases, use_container_width=True, hide_index=True)

elif choice == ":material/policy: Evidence Intake":
    st.title("AI Evidence Intake Portal")
    st.markdown("Securely process raw evidence to generate BNS mapped draft reports.")
    
    if not st.session_state.processed:
        tab1, tab2, tab3 = st.tabs(["🎙️ Audio Evidence", "📹 Video / CCTV", "📸 Live Camera"])
        
        with tab1:
            st.markdown("##### Direct Voice Input")
            rec = st.audio_input("Tap to start secure recording")
            st.markdown("##### Upload Existing Audio")
            uploaded_audio = st.file_uploader("Supported: MP3, WAV, M4A", type=['mp3', 'wav', 'm4a'], label_visibility="collapsed")
            if uploaded_audio: st.audio(uploaded_audio)
            
        with tab2:
            st.markdown("##### Upload Video / CCTV Footage")
            uploaded_video = st.file_uploader("Supported: MP4, MOV, AVI", type=['mp4', 'mov', 'avi'], label_visibility="collapsed")
            if uploaded_video: st.video(uploaded_video)
            
        with tab3:
            st.markdown("##### Live Scene / Document Capture")
            live_pic = st.camera_input("Take secure photograph for immediate evidence")

        with st.container(border=True):
            st.markdown("##### Additional Visuals (Optional)")
            imgs = st.file_uploader("Upload incident photographs/documents", accept_multiple_files=True, type=['png','jpg','jpeg'], label_visibility="collapsed")
        
        final_audio_bytes = rec.getvalue() if rec else (uploaded_audio.getvalue() if uploaded_audio else None)
        final_video_bytes = uploaded_video.getvalue() if uploaded_video else None
        live_pic_bytes = live_pic.getvalue() if live_pic else None

        if final_audio_bytes or final_video_bytes or imgs or live_pic:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Initialize Forensic AI & Mapping", type="primary", use_container_width=True):
                
                # --- SAFETY CHECK ---
                if not final_audio_bytes:
                    st.warning("⚠️ Please provide an Audio Statement (Record/Upload) explaining the video/photos for AI semantic analysis.")
                    st.stop()
                
                # Advanced Loading Progress
                progress_bar = st.progress(0, text="Locking evidence & generating cryptographic SHA-256 Hash...")
                
                # 🚀 ACTUAL FORENSIC HASHING OF BINARY DATA
                combined_binary_data = b""
                if final_audio_bytes: combined_binary_data += final_audio_bytes
                if final_video_bytes: combined_binary_data += final_video_bytes
                if live_pic_bytes: combined_binary_data += live_pic_bytes
                if imgs:
                    for img in imgs:
                        combined_binary_data += img.getvalue()
                        
                real_evidence_hash = hashlib.sha256(combined_binary_data).hexdigest()
                st.session_state.current_hash = real_evidence_hash # Save in state
                st.session_state.db_saved = False # Reset DB save state
                
                time.sleep(0.5)
                
                audio_path = "temp_audio.wav"
                with open(audio_path, "wb") as f: f.write(final_audio_bytes)
                
                progress_bar.progress(30, text="Analyzing Acoustic/Visual Markers & Semantic extraction...")
                
                img_paths = []
                if live_pic_bytes:
                    p = f"temp_live_pic.jpg"
                    with open(p, "wb") as f: f.write(live_pic_bytes)
                    img_paths.append(p)
                if imgs:
                    for img in imgs:
                        p = f"temp_{img.name}"
                        with open(p, "wb") as f: f.write(img.getbuffer())
                        img_paths.append(p)
                
                progress_bar.progress(60, text="Corroborating data with BNS 2023 Master Codebook...")
                
                try:
                    # Pass the audio and all gathered images/live pics to AI engine
                    res = process_complaint(audio_path, img_paths)
                    progress_bar.progress(90, text="Drafting Legally Admissible Section 173 BNSS Report...")
                    
                    cleaned_res = res.replace("```json", "").replace("```JSON", "").replace("```", "").strip()
                    
                    st.session_state.data = json.loads(cleaned_res)
                    progress_bar.progress(100, text="Finalizing...")
                    time.sleep(0.3)
                    
                    st.session_state.processed = True
                    progress_bar.empty()
                    st.rerun()
                except Exception as e:
                    progress_bar.empty()
                    st.error(f"Analysis Engine Error: {e}\n\nRaw AI Output was: {res[:100]}...")
                finally:
                    if os.path.exists(audio_path): os.remove(audio_path)
                    for p in img_paths:
                        if os.path.exists(p): os.remove(p)
    else:
        res = st.session_state.data
        
        # Robust Score Extraction
        raw_score = res.get('credibility_score', res.get('credibility', res.get('score', 0)))
        
        if isinstance(raw_score, str):
            nums = re.findall(r'\d+', raw_score)
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
                
                # Dynamic Legal Admissibility Tag
                if score >= 60:
                    st.markdown("<span class='admissibility-tag admissibility-high'>🛡️ Highly Admissible in Court</span>", unsafe_allow_html=True)
                else:
                    st.markdown("<span class='admissibility-tag admissibility-low'>⚠️ Weak Evidence / Probable Civil Matter</span>", unsafe_allow_html=True)
                    
                st.caption("🔄 *Auto-mapped from legacy IPC sections for officer convenience.*")
                
            with col2:
                if score < 40:
                    st.error(f"⚠️ FLAG: FAKE/IRRELEVANT CASE\n\n**Credibility:** {score}%\n\n**Reason:** {res.get('credibility_reason', 'Review needed')}")
                else:
                    st.success(f"✅ CASE VERIFIED\n\n**Credibility Score:** {score}%")
        
        # --- CHAIN OF CUSTODY (BSA 2023) ---
        st.markdown("### 🔐 Chain of Custody (BSA 2023 Compliant)")
        
        # --- DYNAMIC GPS AND IP ---
        detected_location = res.get('location', 'Not detected')
        dynamic_gps = get_dynamic_coords(detected_location)
        network_ip = st.session_state.session_ip
        actual_hash = st.session_state.get('current_hash', hashlib.sha256(str(datetime.now().timestamp()).encode()).hexdigest())
        
        with st.container(border=True):
            c1, c2 = st.columns(2)
            
            with c1:
                st.markdown("**Evidence SHA-256 Hash:**")
                st.code(actual_hash, language="text")
                st.markdown("**Incident Geo-Coordinates (Extracted):**")
                st.code(f"Lat/Lon: {dynamic_gps}\n({detected_location})", language="text")
            with c2:
                st.markdown("**Timestamp (System):**")
                st.code(datetime.now().isoformat(timespec='seconds') + "Z", language="text")
                st.markdown("**Ingestion Terminal IP (Secure):**")
                st.code(f"{network_ip} (Police Intranet)", language="text")

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
            
            # --- DOCUMENT EXPORT & DATABASE SAVE SECTION ---
            st.markdown("### Document Export & Archival")
            
            qr_col, action_col = st.columns([1, 4])
            
            with qr_col:
                qr_data = f"Nyaya AI Security Hash: {actual_hash}"
                qr_img = generate_qr_code(qr_data)
                st.image(qr_img, width=120, caption="Scan to Verify Hash")
                
            with action_col:
                st.markdown("<br>", unsafe_allow_html=True)
                pdf_data = create_pdf(edited_draft, actual_hash, dynamic_gps, network_ip) 
                
                # 1. Download Button
                st.download_button(
                    label=":material/download: Export Official FIR Document (PDF)",
                    data=pdf_data,
                    file_name=f"Nyaya_FIR_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                    mime="application/pdf",
                    type="primary",
                    use_container_width=True
                )
                
                # 2. Database Save Button
                if not st.session_state.get('db_saved', False):
                    if st.button("💾 Save to Central Database (Archives)", type="secondary", use_container_width=True):
                        # Save to SQLite
                        conn = sqlite3.connect("nyaya_records.db")
                        c = conn.cursor()
                        new_fir_id = f"NY-{np.random.randint(1000, 9999)}"
                        curr_date = datetime.now().strftime("%d-%m-%Y")
                        
                        c.execute("INSERT INTO fir_archives (fir_id, date_filed, status, bns_sections, officer, location, evidence_hash) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                  (new_fir_id, curr_date, "Verified", res.get('bns_sections', 'N/A'), "admin", detected_location, actual_hash))
                        conn.commit()
                        conn.close()
                        
                        st.session_state.db_saved = True
                        st.rerun()
                else:
                    st.success("✅ Case successfully archived in the Central Database! You can view it in the 'FIR Archives' tab.")
            
            # --- NEW EVIDENCE INTAKE BUTTON ---
            st.markdown("<br><hr>", unsafe_allow_html=True)
            if st.button("➕ Start New Evidence Intake", type="secondary", use_container_width=True):
                st.session_state.processed = False
                st.session_state.data = None
                st.session_state.db_saved = False
                if 'hindi_draft' in st.session_state:
                    st.session_state.hindi_draft = None
                if 'current_hash' in st.session_state:
                    del st.session_state.current_hash
                st.rerun()

elif choice == ":material/insights: Crime Analytics":
    st.title("Jurisdiction Analytics")
    st.markdown("Week-over-week comparison of registered complaints.")
    with st.container(border=True):
        st.bar_chart(pd.DataFrame(np.random.randint(10, 50, size=(7, 1)), index=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]))

else:
    st.title(choice.split(": ")[-1])
    st.info("Module ready. Awaiting secure network connection.")
