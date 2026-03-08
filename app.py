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

# --- UI HEADER ---
st.title("⚖️ Nyaya AI: Advanced Forensic Intake")
st.info("BNS 2023 Compliant | Real-time Evidence Analysis")

# --- MAIN TABS ---
tab1, tab2, tab3 = st.tabs(["🎙️ Evidence Upload", "📋 AI Analysis & FIR", "📜 Case History"])

with tab1:
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Audio Testimony")
        audio = st.file_uploader("Upload Complaint Audio", type=['wav', 'mp3', 'm4a'])
        st.caption("AI will analyze voice stress and narrative logic.")
        
    with col_b:
        st.subheader("Visual Evidence")
        images = st.file_uploader("Upload Scene Photos", type=['jpg', 'png', 'jpeg'], accept_multiple_files=True)
        st.caption("AI will cross-verify photos with the audio statement.")

    if st.button("🚀 Process Forensic Package", use_container_width=True, type="primary"):
        if audio:
            with st.spinner("AI SIO is evaluating evidence..."):
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
                st.success("Analysis Complete! Switch to 'AI Analysis' tab.")
        else:
            st.warning("Please upload at least an audio file.")

with tab2:
    if 'analysis' in st.session_state:
        res = st.session_state.analysis
        score = res.get('credibility_score', 0)
        
        # Dashboard style columns
        m1, m2, m3 = st.columns(3)
        m1.metric("Confidence Score", f"{score}%")
        m2.metric("Jurisdiction", res.get('location', 'Unknown'))
        m3.metric("Legal Act", "BNS 2023")

        # Confidence Bar
        color = "red" if score < 40 else "orange" if score < 70 else "green"
        st.progress(score / 100)
        
        c1, c2 = st.columns([1.5, 1])
        with c1:
            st.subheader("📝 Official Draft FIR")
            draft_text = res.get('draft_letter', '')
            edited_draft = st.text_area("Finalize Content:", value=draft_text, height=350)
            
            # Feature: Digital Lock
            doc_hash = generate_evidence_hash(edited_draft)
            st.code(f"SHA-256 Hash: {doc_hash}", language="text")

        with c2:
            st.subheader("🔍 Forensic Logic")
            st.write(res.get('credibility_reason', 'Analysis pending...'))
            
            # Translation Feature
            if st.button("🇮🇳 Translate to Hindi"):
                hindi = translate_to_hindi(edited_draft)
                st.info(hindi)

            # Export Features
            st.divider()
            qr_img = generate_qr_code(f"Verified-NyayaAI-{doc_hash}")
            st.image(qr_img, width=120, caption="Verification QR")
            
            pdf_data = create_pdf(edited_draft, doc_hash)
            st.download_button("📥 Download Signed PDF", data=pdf_data, file_name="Nyaya_FIR.pdf", use_container_width=True)
    else:
        st.info("Upload evidence in the first tab to see analysis.")

with tab3:
    st.subheader("Recent Case Logs")
    st.write("Current Case: " + (st.session_state.analysis.get('bns_sections', 'None') if 'analysis' in st.session_state else "No active case"))
    st.table([{"Timestamp": datetime.now().strftime("%H:%M"), "Status": "Encrypted", "Node": "Forensic-AI-Node-01"}])
