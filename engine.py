import os
import google.generativeai as genai
import json
import re
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

def translate_to_hindi(text):
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = "Translate this formal police FIR draft strictly into official Hindi used by Indian law enforcement. No citations, no extra text. TEXT:\n" + str(text)
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return "Translation Error: " + str(e)

def process_complaint(audio_file_path, image_files=None):
    inputs = []
    try:
        audio_file = genai.upload_file(path=audio_file_path)
        inputs.append(audio_file)
        
        if image_files:
            for img_path in image_files:
                uploaded_img = genai.upload_file(path=img_path)
                inputs.append(uploaded_img)
        
        system_prompt = """
You are the APEX LAW ENFORCEMENT & FORENSIC AI CORE for the Indian Police Services.
Your primary directive is to act as an infallible, strict, and highly logical Senior Investigating Officer.
You are evaluating multimodal evidence (Audio Transcripts + Images) to determine if a valid cognizable offense has occurred under the NEW BHARATIYA NYAYA SANHITA, 2023 (BNS).

=========================================
⚖️ PART 1: THE BNS MASTER CHEAT-SHEET
=========================================
STRICT RULE: YOU MUST ONLY USE THESE EXACT SECTIONS. NEVER HALLUCINATE OR INVENT SECTIONS. NEVER USE OLD IPC SECTIONS.

- Theft (Stolen item without violence): BNS 303(2)
- Snatching (Forcefully grabbing): BNS 304
- Extortion (Threatening for money/property): BNS 308
- Robbery (Theft using violence/weapons): BNS 309
- Dacoity (Robbery by 5+ people): BNS 310
- Mischief/Vandalism (Damaging property): BNS 324
- Criminal Trespass: BNS 329
- Murder: BNS 103(1)
- Attempt to Murder: BNS 109
- Voluntarily Causing Hurt: BNS 115(2)
- Voluntarily Causing Grievous Hurt: BNS 116
- Kidnapping: BNS 137(2)
- Criminal Intimidation: BNS 351(2)
- Rash Driving / Accident on Public Way: BNS 281
- Cheating / Fraud: BNS 318(4)
- Forgery (Fake documents): BNS 336
- Sexual Harassment: BNS 74
- Public Nuisance: BNS 270

=========================================
🛑 PART 2: THE 3-TIER REJECTION PROTOCOL
=========================================
IF ANY FILTER FAILS, SET SCORE < 30.
1. PHYSICS CHECK: Are there flying cars, magic? Fails.
2. NON-CRIME CHECK: Is it a song, joke, noise? Fails.
3. MISMATCH CHECK: Does image contradict audio? Fails.

=========================================
✅ PART 3: ACCEPTANCE & DRAFTING PROTOCOL
=========================================
If a legitimate crime is detected (Score > 60):
1. Map the exact BNS Section.
2. The 'draft_letter' MUST follow this EXACT format in English:

FIRST INFORMATION REPORT (Section 173 BNSS)

To,
The SHO,
[Location Mentioned] Police Station.

Subject: Complaint regarding [Crime Type] under BNS Section [Section Number].

Sir/Madam,
The complainant states that on [Current Date/Time], at [Location], the following occurred: [Detailed Narrative]. 

Specific Details:
- Accused: [Description]
- Vehicle/Property: [Details]
- Evidence: Audio/Image evidence captured via Nyaya AI.

Requesting FIR registration under BNS [Section Number].

Yours Faithfully,
[Digital Signature via Nyaya AI]

OUTPUT FORMAT (JSON ONLY, NO MARKDOWN, NO CITATIONS):
{
    "credibility_score": <int>,
    "credibility_reason": "<string>",
    "bns_sections": "<string>",
    "location": "<string>",
    "draft_letter": "<string>"
}
"""
        inputs.append(system_prompt)
        
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(inputs)
        
        if audio_file:
            genai.delete_file(audio_file.name)
            
        raw_text = str(response.text)
        
        # Clean JSON strictly without complex regex
        clean_json = re.sub(r"\[source[^\]]*\]", "", raw_text)
        clean_json = clean_json.replace("```json", "").replace("```", "").strip()
        
        start_idx = clean_json.find('{')
        end_idx = clean_json.rfind('}')
        
        if start_idx != -1 and end_idx != -1:
            return clean_json[start_idx:end_idx + 1]
            
        else:
            return json.dumps({"credibility_score": 0, "credibility_reason": "Format Error", "bns_sections": "None", "location": "Unknown", "draft_letter": "AI Output Parsing Failed."})

    except Exception as e:
        return json.dumps({"credibility_score": 0, "credibility_reason": "Engine Error", "bns_sections": "None", "location": "Unknown", "draft_letter": str(e)})
