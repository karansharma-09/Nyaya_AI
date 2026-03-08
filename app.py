import streamlit as st
import os
import json
import hashlib
import qrcode
from io import BytesIO
from datetime import datetime
from fpdf import FPDF
from engine import process_complaint, translate_to_hindi

st.set_page_config(page_title="Nyaya AI | BNS Forensic Portal", page_icon="⚖️", layout="wide")

# --- UTILITY FUNCTIONS ---
def generate_evidence_hash(text):
    """Generates a SHA-256 hash for document integrity"""
    return hashlib.sha256(text.encode()).hexdigest()

def generate_qr_code(data):
    """Generates a QR code for verification"""
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
    
    # Header
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="POLICE DEPARTMENT - GOVERNMENT OF INDIA", ln=True, align='C')
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="FIRST INFORMATION REPORT (Section 173 BNSS)", ln=True, align='C')
    pdf.ln(10)
    
    # Content
    pdf.set_font("Arial", size=11)
    clean_text = text.encode('latin-1', 'ignore').decode('latin-1')
    for line in clean_text.split('\n'):
        pdf.multi_cell(0, 8, txt=line, align='L')
    
    # Security Footer
    pdf.ln(10)
    pdf.set_draw_color(200, 200, 200)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    pdf.set_font("Arial", 'I', 8)
    pdf.multi_cell(0, 5, txt=f"DIGITAL INTEGRITY HASH (SHA-256): {evidence_hash}")
    pdf.cell(0, 5, txt=f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True)
    
    # QR Code Placeholder (Simplified for PDF)
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 8)
    pdf.cell(0, 5, txt="SCAN QR ON PORTAL TO VERIFY ORIGINAL DOCUMENT", ln=True)
    
    return pdf.output(dest='S').encode('latin-1')

# --- UI LAYOUT ---
st.title("⚖️ Nyaya AI: Forensic FIR Intake")
st.markdown("---")

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📁 Evidence Upload")
    audio = st.file_uploader("Upload Complaint Audio/Video", type=['wav', 'mp3', 'm4a', 'mp4'])
    images = st.file_uploader("Upload Scene Images (Optional)", type=['jpg', 'jpeg', 'png'], accept_multiple_files=True)
    
    if st.button("🚀 Run Forensic Analysis", use_container_width=True, type="primary"):
        if audio:
            with st.spinner("AI SIO is evaluating evidence..."):
                # Save temp files
                with open("temp_audio.mp3", "wb") as f:
                    f.write(audio.read())
                
                img_paths = []
                if images:
                    for i, img in enumerate(images):
                        path = f"temp_img_{i}.png"
                        with open(path, "wb") as f:
                            f.write(img.read())
                        img_paths.append(path)
                
                # Process
                res_raw = process_complaint("temp_audio.mp3", img_paths)
                st.session_state.analysis = json.loads(res_raw)
        else:
            st.error("Please upload an audio statement.")

with col2:
    if 'analysis' in st.session_state:
        res = st.session_state.analysis
        score = res.get('credibility_score', 0)
        
        # --- FEATURE: CONFIDENCE METER ---
        st.subheader("🛡️ AI Confidence Score")
        color = "red" if score < 40 else "orange" if score < 70 else "green"
        st.markdown(f"<h1 style='color: {color}; text-align: center;'>{score}%</h1>", unsafe_allow_html=True)
        st.progress(score / 100)
        
        with st.expander("🔍 Forensic Reasoning"):
            st.write(res.get('credibility_reason', 'N/A'))
        
        if score >= 40:
            st.success(f"BNS Mapping: {res.get('bns_sections', 'Unknown')}")
            
            # --- DRAFT REVIEW & HASHING ---
            draft_text = res.get('draft_letter', '')
            edited_draft = st.text_area("Review Official Draft:", value=draft_text, height=250)
            
            # Generate Hash
            doc_hash = generate_evidence_hash(edited_draft)
            st.caption(f"🔒 Document Lock Hash: {doc_hash}")
            
            # --- FEATURE: HINDI TRANSLATION ---
            if st.button("🇮🇳 Translate for Citizen Verification"):
                with st.spinner("Translating..."):
                    hindi_text = translate_to_hindi(edited_draft)
                    st.info(hindi_text)
            
            # --- FEATURE: QR & EXPORT ---
            qr_img = generate_qr_code(f"NyayaAI-Verified-{doc_hash}")
            st.image(qr_img, width=150, caption="Verification QR")
            
            pdf_data = create_pdf(edited_draft, doc_hash)
            st.download_button(
                label="📥 Download Secure FIR PDF",
                data=pdf_data,
                file_name=f"FIR_{doc_hash[:8]}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
