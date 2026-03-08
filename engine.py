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
def translate_to_hindi(text):
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = f"Translate the following formal police FIR draft strictly into official Hindi used by Indian law enforcement (Thana level). Maintain the legal tone and accuracy. Do not add any extra markdown, just the translated text.\n\nTEXT:\n{text}"
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return "Translation Error: " + str(e)
    
    # 🛑 STRICT SYSTEM PROMPT
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
If all 3 filters pass, and a legitimate crime is detected (Score > 60):
1. Map the exact BNS Section from the Cheat-Sheet.
2. Draft a highly formal, strictly ENGLISH police report.
3. The draft MUST be written in the third person ("The complainant states that...").
4. Include date, time, location (if mentioned), sequence of events, and suspected evidence. Translate all Hindi/regional audio perfectly into legal English.

=========================================
OUTPUT FORMAT (ABSOLUTE STRICT JSON ONLY)
=========================================
Output ONLY valid JSON. No markdown backticks, no explanatory text.
{
    "credibility_score": <int between 0 to 100>,
    "credibility_reason": "<Clear reasoning for the score and rejection/acceptance>",
    "bns_sections": "<Mapped sections OR 'None'>",
    "location": "<Location mentioned OR 'Unspecified'>",
    "draft_letter": "<Formal FIR English text OR 'FIR Generation Halted. [Reason]'>"
}
"""
    inputs.append(system_prompt)

    model = genai.GenerativeModel('gemini-2.5-flash')
    response = model.generate_content(inputs)
    
    genai.delete_file(audio_file.name)
    
    clean_json = response.text.replace("```json", "").replace("```", "").strip()

    return clean_json

