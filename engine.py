import os
import google.generativeai as genai
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

def process_complaint(audio_file_path, image_files=None):
    inputs = []
    
    audio_file = genai.upload_file(path=audio_file_path)
    inputs.append(audio_file)
    
    if image_files:
        for img_path in image_files:
            uploaded_img = genai.upload_file(path=img_path)
            inputs.append(uploaded_img)
    
    current_time = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
    
    # 🛑 STRICT SYSTEM PROMPT
    system_prompt = """
You are an expert Indian Law Enforcement AI & Forensics Analyst.
Your job is to analyze the provided evidence (audio transcript/images) and generate an intelligence report.

⚠️ STRICT DIRECTIVE 1: THE REALITY & LOGIC CHECK (CRITICAL)
Before mapping any laws, verify if the incident is scientifically and logically possible in the real world.
If the claim involves:
- Objects flying magically (e.g., "cycle hawa me ud gayi")
- Supernatural events, ghosts, or magic
- Alien abductions or physically impossible scenarios
- Utterly absurd or comical claims
THEN YOU MUST DIRECTLY DO THE FOLLOWING:
- Set 'credibility_score' between 0 to 15.
- Set 'credibility_reason' to: "CRITICAL FLAG: Claim violates laws of physics and logical reality. High probability of fabricated/prank statement."
- Set 'bns_sections' to: "None (Rejected Intake)"
- Set 'draft_letter' to: "FIR Generation Halted. The complainant's statement contains physically impossible claims and requires psychiatric or manual police evaluation."

✅ DIRECTIVE 2: FOR LOGICAL CASES ONLY
If the case is realistic, analyze inconsistencies (like changing timelines or mismatched visual evidence). 
- If score > 40: Map the correct Bharatiya Nyaya Sanhita (BNS) sections and write a formal FIR draft in English.
- If score < 40: State the contradictions in 'credibility_reason' and halt the FIR draft.

Output STRICTLY in this JSON format:
{
    "credibility_score": <int>,
    "credibility_reason": "<string>",
    "bns_sections": "<string>",
    "location": "<string or 'Unspecified'>",
    "draft_letter": "<string>"
}
"""
    inputs.append(system_prompt)

    model = genai.GenerativeModel('gemini-2.5-flash')
    response = model.generate_content(inputs)
    
    genai.delete_file(audio_file.name)
    
    clean_json = response.text.replace("```json", "").replace("```", "").strip()

    return clean_json
