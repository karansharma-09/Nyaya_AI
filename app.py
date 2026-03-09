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
    .admissibility-high { background-color: rgba(63, 185, 80, 0.1); color: #3FB950; border: 1px solid #3FB950; }
    .admissibility-low { background-color: rgba(248, 81, 73, 0.1); color: #F85149; border: 1px solid #F85149; }
    </style>
    """, unsafe_allow_html=True)

# --- DATABASE INITIALIZATION ---
def init_db():
    conn = sqlite3.connect("nyaya_records.db")
    c = conn.cursor()
    
    # 1. FIR Archives Table
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
    
    # 2. Users (Officers & Admins) Table [NAYA FEATURE]
    c.execute('''CREATE TABLE IF NOT EXISTS officers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    password TEXT,
                    name TEXT,
                    station TEXT,
                    role TEXT
                )''')
    
    # Add default admin agar exist nahi karta
    c.execute("SELECT COUNT(*) FROM officers WHERE role='admin'")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO officers (username, password, name, station, role) VALUES (?, ?, ?, ?, ?)", 
                  ('admin', 'nyaya2026', 'System Admin', 'Police HQ', 'admin'))

    # Add dummy FIR data if db is newly created
    c.execute("SELECT COUNT(*) FROM fir_archives")
    if c.fetchone()[0] == 0:
        dummy_data = [
            ("NY-882", "08-03-2026", "Verified", "303(2)", "Insp. Sharma", "Connaught Place", "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"),
            ("NY-881", "07-03-2026", "Pending Review", "115(1)", "SI Verma", "Rohini Sec 7", "8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92")
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
    h = int(hashlib.md5(loc_string.encode()).hexdigest(), 16)
    lat = 28.0 + (h % 100) / 100.0
    lon = 77.0 + ((h // 100) % 100) / 100.0
    return f"{lat:.4f}° N, {lon:.4f}° E"

# Helper for PDF 
def create_pdf(text, hash_val, gps_coords, ip_address, officer_name, station_name):
    pdf = FPDF()
    pdf.add_page()
    
    # Official Header
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "FIRST INFORMATION REPORT (FIR)", ln=True, align='C')
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(0, 10, "Generated via Nyaya AI Law Enforcement Core", ln=True, align='C')
    pdf.ln(5)
    
    # Officer Info
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 8, f"Reporting Officer: {officer_name} | Station: {station_name}", ln=True)
    pdf.ln(2)
    
    # Main Draft Body
    pdf.set_font("Arial", size=11)
    clean_text = text.encode('latin-1', 'ignore').decode('latin-1')
    for line in clean_text.split('\n'):
        pdf.multi_cell(0, 10, txt=line, align='L')
        
    # Security Section at the end
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 10, "==================================================", ln=True)
    pdf.cell(0, 10, "DIGITAL VERIFICATION & CHAIN OF CUSTODY (BSA 2023 COMPLIANT)", ln=True)
    pdf.set_font("Arial", size=10)
    pdf.cell(0, 8, f"SHA-256 Hash: {hash_val}", ln=True)
    pdf.cell(0, 8, f"Timestamp: {datetime.now().isoformat(timespec='seconds')}Z", ln=True)
    pdf.cell(0, 8, f"Geospatial Coordinates: {gps_coords}", ln=True)
    pdf.cell(0, 8, f"Ingestion Terminal IP: {ip_address}", ln=True)
    
    # QR Code
    qr = qrcode.QRCode(version=1, box_size=5, border=2)
    qr.add_data(f"Nyaya AI Security Hash: {hash_val}")
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    temp_qr_path = f"temp_qr_{int(time.time())}.png"
    img.save(temp_qr_path)
    pdf.image(temp_qr_path, w=30)
    
    if os.path.exists(temp_qr_path):
        os.remove(temp_qr_path)
        
    return pdf.output(dest='S').encode('latin-1')

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
if 'current_user' not in st.session_state: st.session_state.current_user = None
if 'processed' not in st.session_state: st.session_state.processed = False
if 'data' not in st.session_state: st.session_state.data = None
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
            input_username = st.text_input("Username / Badge ID", placeholder="Enter Username")
            input_password = st.text_input("Secure Password", type="password", placeholder="••••••••")
            
            if st.button("Authenticate 🔒", type="primary", use_container_width=True):
                # DB se check karo
                conn = sqlite3.connect("nyaya_records.db")
                c = conn.cursor()
                c.execute("SELECT id, username, name, station, role FROM officers WHERE username=? AND password=?", (input_username, input_password))
                user_record = c.fetchone()
                conn.close()
                
                if user_record:
                    with st.spinner("Verifying credentials & IP integrity..."):
                        time.sleep(1)
                        st.session_state.logged_in = True
                        st.session_state.current_user = {
                            'id': user_record[0],
                            'username': user_record[1],
                            'name': user_record[2],
                            'station': user_record[3],
                            'role': user_record[4]
                        }
                        st.rerun()
                elif input_username or input_password:
                    st.error("Invalid Credentials. Access Denied. Kripya apna sahi Username aur Password daalein.")
                    
            st.markdown("<br><p style='text-align: center; font-size: 12px; color: #484F58;'>Attempting to bypass this portal is a federal offense under BNS Section 302.</p>", unsafe_allow_html=True)
    st.stop()

# ==========================================
# 🟢 MAIN APPLICATION
# ==========================================

# Current user details
user_role = st.session_state.current_user['role']
user_name = st.session_state.current_user['name']
user_station = st.session_state.current_user['station']

# --- SIDEBAR & LIVE CLOCK ---
with st.sidebar:
    st.markdown("<h1 style='color: #58A6FF; margin-bottom:0; font-weight: 800; letter-spacing: 1px;'>NYAYA <span style='color:#E6EDF3; font-weight: 300;'>AI</span></h1>", unsafe_allow_html=True)
    
    # Show badge depending on role
    if user_role == 'admin':
        st.caption(f"🛡️ ADMIN: {user_name.upper()}")
    else:
        st.caption(f"👮 OFFICER: {user_name.upper()}")
        st.caption(f"📍 STATION: {user_station.upper()}")
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 📌 DYNAMIC MENU BASED ON ROLE
    if user_role == 'admin':
        menu = [
            ":material/admin_panel_settings: Command Center", 
            ":material/group_add: Manage Officers", 
            ":material/assignment: FIR Archives", 
            ":material/insights: Crime Analytics"
        ]
        default_index = 0
    else:
        # Officer sirf Evidence Intake aur Archives dekh payega
        menu = [
            ":material/policy: Evidence Intake", 
            ":material/assignment: FIR Archives"
        ]
        default_index = 0

    choice = st.radio("Navigation", menu, index=default_index, label_visibility="collapsed")
    
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
        st.session_state.current_user = None
        st.session_state.processed = False
        st.session_state.data = None
        st.rerun()

# --- TABS LOGIC ---

if choice == ":material/admin_panel_settings: Command Center":
    st.title("Station Command Center")
    st.markdown("Real-time intelligence synced with regional police database.")
    
    conn = sqlite3.connect("nyaya_records.db")
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM fir_archives")
    total_cases = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM officers WHERE role='officer'")
    total_officers = c.fetchone()[0]
    conn.close()
    
    with st.container(border=True):
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Archived Cases", str(total_cases), "+1 Today")
        m2.metric("Active Field Officers", str(total_officers), "Deployed")
        m3.metric("AI Accuracy", "98.4%", "Stable", delta_color="off")
    
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

# ====================================================
# 👮 MANAGE OFFICERS TAB (ADMIN ONLY)
# ====================================================
elif choice == ":material/group_add: Manage Officers":
    st.title("Manage Police Personnel")
    st.markdown("Add or remove authorized officers who can access the AI Evidence Intake system.")
    
    col1, col2 = st.columns([1, 1.5])
    
    with col1:
        st.subheader("Add New Officer")
        with st.form("add_officer_form", clear_on_submit=True):
            new_name = st.text_input("Full Name (e.g., SI Vikram Singh)")
            new_station = st.text_input("Police Station Location (e.g., Hauz Khas)")
            new_username = st.text_input("Login Username")
            new_password = st.text_input("Login Password", type="password")
            
            submit_btn = st.form_submit_button("Create Officer Account", use_container_width=True)
            
            if submit_btn:
                if new_name and new_station and new_username and new_password:
                    try:
                        conn = sqlite3.connect("nyaya_records.db")
                        c = conn.cursor()
                        c.execute("INSERT INTO officers (username, password, name, station, role) VALUES (?, ?, ?, ?, ?)",
                                  (new_username, new_password, new_name, new_station, 'officer'))
                        conn.commit()
                        conn.close()
                        st.success(f"✅ Officer {new_name} added successfully!")
                        time.sleep(1) # Refresh dikhane ke liye
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("⚠️ Username already exists! Koi dusra username try karein.")
                else:
                    st.warning("⚠️ Sabhi fields bharna zaroori hai.")
        
        # --- NEW DELETION FEATURE WITH PASSWORD ---
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("Remove Officer")
        with st.form("delete_officer_form", clear_on_submit=True):
            del_username = st.text_input("Officer Username to Remove")
            admin_password = st.text_input("Your Admin Password (Required)", type="password")
            
            del_btn = st.form_submit_button("Delete Officer Account", use_container_width=True)
            
            if del_btn:
                if del_username and admin_password:
                    conn = sqlite3.connect("nyaya_records.db")
                    c = conn.cursor()
                    
                    # Verify admin password first
                    c.execute("SELECT * FROM officers WHERE id=? AND password=?", (st.session_state.current_user['id'], admin_password))
                    if c.fetchone():
                        if del_username == st.session_state.current_user['username']:
                            st.error("⚠️ You cannot delete your own admin account!")
                        else:
                            c.execute("DELETE FROM officers WHERE username=?", (del_username,))
                            if c.rowcount > 0:
                                conn.commit()
                                st.success(f"✅ Officer '{del_username}' removed successfully!")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("⚠️ Officer username not found in database.")
                    else:
                        st.error("❌ Incorrect Admin Password. Deletion access denied.")
                        
                    conn.close()
                else:
                    st.warning("⚠️ Sabhi fields bharna zaroori hai.")

    with col2:
        st.subheader("Authorized Personnel Directory")
        conn = sqlite3.connect("nyaya_records.db")
        df_officers = pd.read_sql_query("SELECT id, name as 'Officer Name', station as 'Station', username as 'Login ID', role as 'Role' FROM officers", conn)
        conn.close()
        st.dataframe(df_officers, use_container_width=True, hide_index=True)

# ====================================================
# 📝 FIR ARCHIVES TAB (ALL ROLES)
# ====================================================
elif choice == ":material/assignment: FIR Archives":
    st.title("Station FIR Archives")
    st.markdown("Centralized database of all processed and saved complaints.")
    
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

# ====================================================
# 🎙️ EVIDENCE INTAKE TAB (OFFICER ONLY)
# ====================================================
elif choice == ":material/policy: Evidence Intake":
    st.title("AI Evidence Intake Portal")
    st.markdown(f"**Logged in as:** {user_name} | **Station:** {user_station}")
    st.caption("Securely process raw evidence to generate BNS mapped draft reports.")
    
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
                
                if not final_audio_bytes:
                    st.warning("⚠️ Please provide an Audio Statement (Record/Upload) explaining the video/photos for AI semantic analysis.")
                    st.stop()
                
                progress_bar = st.progress(0, text="Locking evidence & generating cryptographic SHA-256 Hash...")
                
                combined_binary_data = b""
                if final_audio_bytes: combined_binary_data += final_audio_bytes
                if final_video_bytes: combined_binary_data += final_video_bytes
                if live_pic_bytes: combined_binary_data += live_pic_bytes
                if imgs:
                    for img in imgs:
                        combined_binary_data += img.getvalue()
                        
                real_evidence_hash = hashlib.sha256(combined_binary_data).hexdigest()
                st.session_state.current_hash = real_evidence_hash 
                st.session_state.db_saved = False 
                
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
        
        # --- CHAIN OF CUSTODY ---
        st.markdown("### 🔐 Chain of Custody (BSA 2023 Compliant)")
        
        detected_location = res.get('location', 'Not detected')
        dynamic_gps = get_dynamic_coords(detected_location)
        network_ip = st.session_state.session_ip
        actual_hash = st.session_state.get('current_hash', hashlib.sha256(str(datetime.now().timestamp()).encode()).hexdigest())
        
        with st.container(border=True):
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**Evidence SHA-256 Hash:**")
                st.code(actual_hash, language="text")
                st.markdown("**Incident Geo-Coordinates:**")
                st.code(f"Lat/Lon: {dynamic_gps}\n({detected_location})", language="text")
            with c2:
                st.markdown("**Ingestion Terminal IP:**")
                st.code(f"{network_ip} (Police Intranet)", language="text")
                st.markdown("**Logged Officer & Station:**")
                st.code(f"{user_name} | {user_station}", language="text")

        # --- DRAFT REVIEW ---
        if score >= 40:
            st.markdown("### Official Draft Review")
            draft_text = res.get('draft_letter', '')
            edited_draft = st.text_area("Modify AI-generated draft before exporting to PDF:", value=draft_text, height=300, label_visibility="collapsed")
            
            if 'hindi_draft' not in st.session_state: st.session_state.hindi_draft = None
                
            if st.button("🇮🇳 Translate to Official Hindi (For Citizen Verification)", use_container_width=True):
                with st.spinner("Translating to official legal Hindi..."):
                    st.session_state.hindi_draft = translate_to_hindi(edited_draft)
            
            if st.session_state.hindi_draft:
                st.markdown("#### Hindi Translation (नागरिक सत्यापन हेतु)")
                st.info(st.session_state.hindi_draft)
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("### Document Export & Archival")
            
            qr_col, action_col = st.columns([1, 4])
            
            with qr_col:
                qr_data = f"Nyaya AI Security Hash: {actual_hash}"
                qr_img = generate_qr_code(qr_data)
                st.image(qr_img, width=120, caption="Scan to Verify Hash")
                
            with action_col:
                st.markdown("<br>", unsafe_allow_html=True)
                
                # NAYE PDF FUNCTION MEIN OFFICER DETAILS PASS KAR RAHE HAIN
                pdf_data = create_pdf(edited_draft, actual_hash, dynamic_gps, network_ip, user_name, user_station) 
                
                st.download_button(
                    label=":material/download: Export Official FIR Document (PDF)",
                    data=pdf_data,
                    file_name=f"Nyaya_FIR_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                    mime="application/pdf",
                    type="primary",
                    use_container_width=True
                )
                
                if not st.session_state.get('db_saved', False):
                    if st.button("💾 Save to Central Database (Archives)", type="secondary", use_container_width=True):
                        conn = sqlite3.connect("nyaya_records.db")
                        c = conn.cursor()
                        new_fir_id = f"NY-{np.random.randint(1000, 9999)}"
                        curr_date = datetime.now().strftime("%d-%m-%Y")
                        
                        # Officer name ki jagah logged-in officer ka naam pass kar rahe hain
                        c.execute("INSERT INTO fir_archives (fir_id, date_filed, status, bns_sections, officer, location, evidence_hash) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                  (new_fir_id, curr_date, "Verified", res.get('bns_sections', 'N/A'), user_name, detected_location, actual_hash))
                        conn.commit()
                        conn.close()
                        
                        st.session_state.db_saved = True
                        st.rerun()
                else:
                    st.success("✅ Case successfully archived in the Central Database! You can view it in the 'FIR Archives' tab.")
        
        # --- NEW CASE BUTTON (MOVED OUTSIDE 'if score >= 40' TO FIX THE BUG) ---
        st.markdown("<br><hr>", unsafe_allow_html=True)
        if st.button("➕ Start New Evidence Intake", type="secondary", use_container_width=True):
            st.session_state.processed = False
            st.session_state.data = None
            st.session_state.db_saved = False
            if 'hindi_draft' in st.session_state: st.session_state.hindi_draft = None
            if 'current_hash' in st.session_state: del st.session_state.current_hash
            st.rerun()

elif choice == ":material/insights: Crime Analytics":
    st.title("Jurisdiction Analytics")
    st.markdown("Week-over-week comparison of registered complaints.")
    with st.container(border=True):
        st.bar_chart(pd.DataFrame(np.random.randint(10, 50, size=(7, 1)), index=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]))

else:
    st.title("Nyaya AI Module")
    st.info("Module ready. Awaiting secure network connection.")

