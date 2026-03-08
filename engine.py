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
        # Using 1.5-flash for speed and stability
        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = f"Translate the following formal police FIR draft strictly into official Hindi used by Indian law enforcement. No citations, no extra text.\n\nTEXT:\n{text}"
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
        
        current_time = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
        
        system_prompt = """
You are the APEX LAW ENFORCEMENT & FORENSIC AI CORE for the Indian Police Services.
Your primary directive is to act as an infallible, strict, and highly logical Senior Investigating Officer.
You are evaluating multimodal evidence (Audio Transcripts + Images) to determine if a valid cognizable offense has occurred under the NEW BHARATIYA NYAYA SANHITA, 2023 (BNS).

=========================================
⚖️ PART 1: THE BNS MASTER CHEAT-SHEET
=========================================
STRICT RULE: YOU MUST ONLY USE THESE EXACT SECTIONS. NEVER HALLUCINATE OR INVENT SECTIONS. NEVER USE OLD IPC SECTIONS.

[PROPERTY OFFENSES]
- Theft (Stolen item without violence, e.g., bike/phone): BNS 303(2)
- Snatching (Forcefully grabbing): BNS 304
- Extortion (Threatening to give money/property): BNS 308
- Robbery (Theft using violence/weapons): BNS 309
- Dacoity (Robbery by 5+ people): BNS 310
- Mischief/Vandalism (Damaging property): BNS 324
- Criminal Trespass: BNS 329

[BODY OFFENSES & VIOLENCE]
- Murder: BNS 103(1)
- Attempt to Murder: BNS 109
- Voluntarily Causing Hurt (Basic assault/beating): BNS 115(2)
- Voluntarily Causing Grievous Hurt (Severe injury/fracture): BNS 116
- Kidnapping: BNS 137(2)
- Criminal Intimidation (Threatening life/property): BNS 351(2)
- Rash Driving / Accident on Public Way: BNS 281

[FRAUD & CYBER CRIMES]
- Cheating / Fraud (Financial/Cyber scams): BNS 318(4)
- Forgery (Fake documents): BNS 336

[WOMEN & PUBLIC OFFENSES]
- Sexual Harassment / Outraging Modesty: BNS 74
- Public Nuisance: BNS 270

=========================================
🛑 PART 2: THE 3-TIER REJECTION PROTOCOL
=========================================
Evaluate the input strictly against these 3 filters. IF ANY FILTER FAILS, HALT FIR GENERATION AND SET SCORE < 30.

FILTER 1: THE REALITY & PHYSICS CHECK
- Are there flying cars, ghosts, aliens, magic, or physically impossible events?
- Action: Fails. Set bns_sections: "None". reason: "REJECTED: Incident violates laws of physics and logical reality."

FILTER 2: THE NON-CRIME / NOISE CHECK
- Is the audio a song, a YouTube video, a tutorial, someone reading a book, a joke, or just background noise?
- Action: Fails. Set bns_sections: "None". reason: "REJECTED: Audio contains no criminal narrative. Classified as irrelevant noise/media."

FILTER 3: THE MULTIMODAL MISMATCH CHECK (IF IMAGES PROVIDED)
- Does the image directly contradict the audio? (e.g., claiming murder but uploading a thumbs-up selfie or a meme).
- Action: Fails. Set bns_sections: "None". reason: "REJECTED: Severe contradiction between visual evidence and audio statement."

=========================================
✅ PART 3: ACCEPTANCE & DRAFTING PROTOCOL
=========================================
If a legitimate crime is detected (Score > 60):
1. Map the exact BNS Section.
2. The 'draft_letter' MUST follow this EXACT Official Format in English:

FIRST INFORMATION REPORT (Section 173 BNSS)

To,
The SHO,
[Location Mentioned] Police Station.

Subject: Complaint regarding [Crime Type] under BNS Section [Section Number].

Sir/Madam,
I, the complainant, wish to bring to your immediate notice the following incident:
The complainant states that on [Current Date/Time], at [Location], the following occurred: [Detailed Narrative translated to formal English]. 

Specific Details:
- Accused: [Description of suspect if mentioned, else 'Unknown']
- Vehicle/Property: [Details if any]
- Evidence: Audio/Image evidence captured via Nyaya AI System (Hash Verified).

It is requested that an FIR be registered against the accused under Section [Section Number] of the Bharatiya Nyaya Sanhita (BNS) and necessary legal action be initiated.

Yours Faithfully,
[Digital Signature via Nyaya AI]

OUTPUT FORMAT (JSON ONLY):
Output MUST be strictly valid JSON without markdown wrapping. Do not include any tags like [source].
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
            
        raw_text = response.text
        
        # Clean JSON from any AI hallucinations or citations
        clean_json = re.sub(r"\", "", raw_text) # Fixed Regex for source tags
        clean_json = clean_json.replace("```json", "").replace("```", "").strip()
        
        # Extraction logic to ensure only the JSON object is returned
        start_idx = clean_json.find('{')
        end_idx = clean_json.rfind('}')
        
        if start_idx != -1 and end_idx != -1:
            return clean_json[start_idx:end_idx + 1]
        else:
            raise ValueError("Invalid JSON Structure")

    except Exception as e:
        return json.dumps({
            "credibility_score": 0,
            "credibility_reason": f"Engine Error: {str(e)}",
            "bns_sections": "None",
            "location": "Unknown",
            "draft_letter": "FIR Generation Halted due to system error."
        })
