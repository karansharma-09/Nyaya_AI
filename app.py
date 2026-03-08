import streamlit as st
import os
import json
import hashlib
import qrcode
from io import BytesIO
from datetime import datetime
from fpdf import FPDF
from engine import process_complaint, translate_to_hindi

st.set_page_config(page_title="Nyaya AI | Forensic Portal", page_icon="⚖️", layout="wide")

# --- UTILITY FUNCTIONS ---
def generate_evidence_hash(text):
    return hashlib.sha256(text.encode()).hexdigest()

def generate_qr_code(data):
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def create_pdf(text, evidence_hash):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="POLICE DEPARTMENT - GOVERNMENT OF INDIA", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=11)
    clean_text = text.encode('latin-1', 'ignore').decode('latin-1')
    for line in clean_text.split('\n'):
        pdf.multi_cell(0, 8, txt=line, align='L')
    pdf.ln(10)
    pdf.set_font("Arial", 'I', 8)
    pdf.multi_cell(0, 5, txt=f"DIGITAL INTEGRITY HASH: {evidence_hash}")
    return pdf.output(dest='S').encode('latin-1')

# ==========================================
# 🧭 SIDEBAR NAVIGATION (Wapas aa gaya!)
# ==========================================
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/5/55/Emblem_of_India.svg/120px-Emblem_of_India.svg.png", width=80)
st.sidebar.title("Nyaya AI Portal")
st.sidebar.markdown("---")

app_mode = st.sidebar.radio(
    "Select Module:",
    ["📝 New FIR Intake", "📁 FIR Archive", "📊 Analytics Dashboard", "⚙️ System Settings"]
)

st.sidebar.markdown("---")
st.sidebar.caption("Secured by SHA-256 Hashing")
st.sidebar.caption(f"Date: {datetime.now().strftime('%d-%m-%Y')}")


# ==========================================
# 📄 PAGE 1: NEW FIR INTAKE (Main Application)
# ==========================================
if app_mode == "📝 New FIR Intake":
    st.title("⚖️ Evidence Processing & BNS Mapping")
    st.info("Upload multi-modal evidence for AI-driven Section 173 BNSS drafting.")
    
    col_a, col_b = st.columns([1, 1.5]) # Left side for upload, Right side for AI output
    
    with col_a:
        st.subheader("1. Input Evidence")
        audio = st.file_uploader("🎙️ Upload Audio Testimony", type=['wav', 'mp3', 'm4a'])
        images = st.file_uploader("📸 Upload Scene Photos", type=['jpg', 'png', 'jpeg'], accept_multiple_files=True)
        
        if st.button("🚀 Process Forensic Package", use_container_width=True, type="primary"):
            if audio:
                with st.spinner("AI SIO is evaluating evidence & mapping BNS..."):
                    with open("temp_audio.mp3", "wb") as f:
                        f.write(audio.read())
                    
                    img_paths = []
                    if images:
                        for i, img in enumerate(images):
                            path = f"temp_img_{i}.png"
                            with open(path, "wb") as f:
                                f.write(img.read())
                            img_paths.append(path)
                    
                    res_raw = process_complaint("temp_audio.mp3", img_paths)
                    st.session_state.analysis = json.loads(res_raw)
            else:
                st.warning("Please upload at least an audio file.")

    with col_b:
        st.subheader("2. AI SIO Report")
        if 'analysis' in st.session_state:
            res = st.session_state.analysis
            score = res.get('credibility_score', 0)
            
            # Confidence Metrics
            m1, m2, m3 = st.columns(3)
            m1.metric("Confidence Score", f"{score}%")
            m2.metric("Jurisdiction", res.get('location', 'Unknown')[:15])
            m3.metric("Legal Act", res.get('bns_sections', 'None')[:15])

            color = "red" if score < 40 else "orange" if score < 70 else "green"
            st.progress(score / 100)
            
            with st.expander("🔍 Read Forensic Logic", expanded=False):
                st.write(res.get('credibility_reason', 'Analysis pending...'))

            # FIR Draft
            st.markdown("### 📝 Official Draft FIR")
            draft_text = res.get('draft_letter', '')
            edited_draft = st.text_area("Review & Edit:", value=draft_text, height=250, label_visibility="collapsed")
            
            # Action Buttons & Security
            doc_hash = generate_evidence_hash(edited_draft)
            st.caption(f"🔒 SHA-256 Signature: {doc_hash}")
            
            col_btn1, col_btn2, col_btn3 = st.columns(3)
            with col_btn1:
                if st.button("🇮🇳 Translate (Hindi)", use_container_width=True):
                    hindi = translate_to_hindi(edited_draft)
                    st.info(hindi)
            
            with col_btn2:
                # PDF Download with QR
                pdf_data = create_pdf(edited_draft, doc_hash)
                st.download_button("📥 Download PDF", data=pdf_data, file_name="Nyaya_FIR.pdf", use_container_width=True)
                
            with col_btn3:
                qr_img = generate_qr_code(f"Verified-NyayaAI-{doc_hash}")
                st.image(qr_img, width=80)
        else:
            st.info("Awaiting evidence upload...")

# ==========================================
# 📁 PAGE 2: FIR ARCHIVE
# ==========================================
elif app_mode == "📁 FIR Archive":
    st.title("📁 Encrypted FIR Archive")
    st.write("View past generated FIRs and their digital signatures.")
    
    # Mock data for demonstration in Hackathon
    archive_data = [
        {"Date": "2026-03-08", "Crime": "Rash Driving", "BNS": "BNS 281", "Hash": "8f4a...9b1"},
        {"Date": "2026-03-07", "Crime": "Theft", "BNS": "BNS 303(2)", "Hash": "2c9d...4f2"}
    ]
    st.table(archive_data)
    st.button("🔄 Sync with CCTNS Database")

# ==========================================
# 📊 PAGE 3 & 4: PLACEHOLDERS FOR DEMO
# ==========================================
elif app_mode == "📊 Analytics Dashboard":
    st.title("📊 Crime Heatmap & Analytics")
    st.info("Integration with mapping services pending for predictive policing module.")
    
elif app_mode == "⚙️ System Settings":
    st.title("⚙️ Configure AI Nodes")
    st.write("Adjust Gemini Model parameters and Law Enforcement strictness here.")
