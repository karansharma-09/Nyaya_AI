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
You are a highly strict and expert Indian Law Enforcement AI & Forensics Analyst.
Your sole job is to evaluate if the provided audio and images constitute a VALID, REALISTIC POLICE COMPLAINT under the Bharatiya Nyaya Sanhita (BNS).

⚠️ STRICT REJECTION TRIGGERS (If any of these match, set 'credibility_score' strictly below 30 and DO NOT draft an FIR):

1. NON-CRIME / IRRELEVANT AUDIO: If the audio is someone reading a book, playing a YouTube video, singing, casual conversation, or anything that is NOT a clear report of a crime.
-> credibility_reason: "REJECTED: Audio is irrelevant (e.g., educational/casual) and does not contain any valid legal complaint."
-> draft_letter: "FIR Generation Halted. No criminal offense detected in the input."

2. EVIDENCE MISMATCH (MULTIMODAL FLAG): If the user uploads an image (like a random selfie, thumbs-up, meme, or blank photo) that does completely NOT match the context of the audio complaint.
-> credibility_reason: "REJECTED: Visual evidence does not corroborate the audio claim. High probability of prank/spam."
-> draft_letter: "FIR Generation Halted. Severe mismatch between audio statement and visual evidence."

3. THE LOGIC / PHYSICS CHECK: If the claim is physically impossible (e.g., flying cycles, magic, aliens, extreme exaggeration).
-> credibility_reason: "REJECTED: Claim violates laws of physics and logical reality."
-> draft_letter: "FIR Generation Halted. Fabricated statement detected."

✅ ACCEPTANCE CRITERIA (Score > 50):
ONLY if the audio describes a realistic, logical crime (theft, assault, cyber fraud, etc.) AND the images (if provided) actually look like relevant evidence.
- Map the exact Bharatiya Nyaya Sanhita (BNS) sections.
- Draft a highly professional FIR letter.

Output STRICTLY in this exact JSON format, nothing else:
{
    "credibility_score": <int>,
    "credibility_reason": "<string>",
    "bns_sections": "<string or 'None'>",
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

