import google.generativeai as genai

# PASTE YOUR REAL API KEY HERE
genai.configure(api_key="AIzaSyAarftk48p_NKVycxEztqJidmG_yLKlr1E")

print("Asking Google for your available models...")
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(m.name)