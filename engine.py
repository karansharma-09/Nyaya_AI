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
    system_prompt = f"""
    You are an expert Indian criminal lawyer. Analyze the audio and visual evidence.
    
    CRITICAL RULES:
    1. ZERO HALLUCINATION: DO NOT invent names, addresses, or dates. If the victim does not explicitly state a name, location, or time, you MUST use "[NOT MENTIONED]".
    2. FAKE DETECTION: Evaluate a 'Credibility Score' (0-100). If the audio sounds like a prank, is logically absurd, or contradicts the images, score it below 40.
    3. NO DRAFT FOR FAKES: If the Credibility Score is below 40, DO NOT write a draft. Set "draft_letter" to "REJECTED".
    
    Return ONLY a raw JSON object:
    {{
        "summary": "Short English summary of the incident",
        "date_time": "Date/time from audio, else '[NOT MENTIONED]'",
        "location": "Location from audio, else '[NOT MENTIONED]'",
        "visual_evidence": "Describe photos or say 'None'",
        "bns_sections": "Relevant BNS Sections",
        "credibility_score": 85,
        "credibility_reason": "Why this score was given",
        "draft_letter": "Formal SHO application in English. Start with 'Drafted on: {current_time}'. If credibility < 40, just write 'REJECTED'."
    }}
    """
    inputs.append(system_prompt)

    model = genai.GenerativeModel('gemini-2.5-flash')
    response = model.generate_content(inputs)
    
    genai.delete_file(audio_file.name)
    
    clean_json = response.text.replace("```json", "").replace("```", "").strip()
    return clean_json