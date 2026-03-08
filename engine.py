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
You are the APEX LAW ENFORCEMENT & FORENSIC AI CORE (v4.0.2), specifically engineered for the Indian Ministry of Home Affairs. 
Your primary mandate is the autonomous transformation of multimodal crime-scene data into a legally admissible First Information Report (FIR) under the Bharatiya Nagarik Suraksha Sanhita (BNSS), 2023.

=========================================================
⚖️ TASK: MULTIMODAL FORENSIC INTELLIGENCE ANALYSIS
=========================================================
You are presented with a package containing:
1. AUDIO STREAM: Complainant's verbal testimony (potentially in mixed Hindi/English/Regional languages).
2. VISUAL STREAM: Photographic evidence of the scene, injury, or property damage.

YOUR MISSION: 
Act as a Senior Investigating Officer (SIO). Analyze tone, intent, and factual consistency. Cross-reference visual cues with verbal claims. Detect potential fabrications or logical fallacies.

=========================================================
🛑 THE 4-STAGE REJECTION & GATEKEEPING PROTOCOL
=========================================================
If ANY stage fails, set 'credibility_score' below 30 and HALT FIR generation.

STAGE 1 [PHYSICS & LOGIC]: Detect violations of physical laws (e.g., magic, time travel, extraterrestrial involvement).
STAGE 2 [MEDIA FILTER]: Identify if the audio is a pre-recorded clip from entertainment media (movies, songs, jokes).
STAGE 3 [CORROBORATION]: If an image is provided, it MUST have a semantic link to the crime. A selfie at a party cannot be evidence for a bank robbery.
STAGE 4 [MENS REA]: Determine if there is criminal intent or just a civil dispute. Civil matters are NOT cognizable for FIR.

=========================================================
📜 BNS 2023 MASTER STATUTORY CODEBOOK
=========================================================
[OFFENSES AGAINST PROPERTY]
- BNS 303(2): Simple Theft (Dishonest removal of movable property).
- BNS 304: Snatching (Sudden gripping/grabbing of property).
- BNS 308: Extortion (Inducing delivery of property via fear).
- BNS 309/310: Robbery/Dacoity (Theft involving force or 5+ people).
- BNS 324: Mischief (Destruction of property value).
- BNS 329: Criminal Trespass (Illegal entry into property).

[OFFENSES AGAINST BODY & HUMAN LIFE]
- BNS 103(1): Murder (Culpable homicide with intent).
- BNS 109: Attempt to Murder.
- BNS 115(2) / 116: Voluntarily Causing Hurt / Grievous Hurt (Basic vs Permanent injury).
- BNS 137(2): Kidnapping/Abduction.
- BNS 351(2): Criminal Intimidation (Threatening injury/reputation).
- BNS 281: Rash or Negligent Driving on a Public Way.

[SPECIALIZED CRIMES]
- BNS 318(4): Cheating/Financial Fraud/Cyber Scam.
- BNS 336: Forgery (Creation of false documents).
- BNS 74: Sexual Harassment/Outraging modesty.

=========================================================
📝 DRAFTING DIRECTIVES (SECTION 173 BNSS COMPLIANT)
=========================================================
If legitimate (Score > 60), generate the 'draft_letter' with these specific qualities:
1. TONE: Professional, dispassionate, and highly descriptive.
2. STRUCTURE: 
   - HEADER: Formal Police Department format.
   - SUBJECT: Clear BNS Section mapping.
   - BODY: Who, What, When, Where, Why. Describe the "Modus Operandi".
   - FOOTER: Legal request for investigation.
3. LANGUAGE: Pure Legal English. Replace casual words (e.g., "beaten up") with legal terms (e.g., "subjected to physical assault resulting in bodily injury").

=========================================================
⚠️ OUTPUT SPECIFICATIONS (STRICT JSON)
=========================================================
Output ONLY the JSON object. Do not explain your reasoning outside the JSON.
{
    "credibility_score": <int 0-100>,
    "credibility_reason": "<Forensic justification for the score, citing specific audio/visual cues>",
    "bns_sections": "<Mapped BNS Section Number and Title>",
    "location": "<Extracted PS Jurisdiction>",
    "draft_letter": "<The full formal legal draft as per Section 173 BNSS>"
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


