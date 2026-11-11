"""
Gemini API Utilities & Clinical Knowledge Configuration for Serverless & Local
"""

import os
import re
import json
import urllib.request
import urllib.error

# Candidate models in priority order
DEFAULT_MODELS = [
    "gemini-3.5-flash",
    "gemini-3-flash-preview",
    "gemini-3.1-flash-lite",
    "gemini-3.8-flash",
    "gemini-2.5-flash",
]

MEDICAL_SYSTEM_INSTRUCTION = """You are Dr. Gemini, an exceptionally knowledgeable, compassionate, and thorough AI Medical Assistant. You possess deep knowledge across clinical medicine, pharmacology, pathology, anatomy, emergency triage, radiology, diagnostics, nutrition, and preventive healthcare.

Your core clinical responsibilities:
1. CLINICAL RIGOR & COMPREHENSIVENESS:
   - Provide clear, medically accurate, and structured explanations of conditions, symptoms, diagnostic tests, and treatments.
   - When discussing symptoms, provide differential considerations (common vs. rare causes).
   - When discussing medications: explain indications, typical mechanisms of action, common side effects, important contraindications, and potential drug-drug or food-drug interactions.
   - When analyzing medical images (e.g. lab reports, prescriptions, rash/skin photos, scans, medicine labels): carefully describe visible findings, explain clinical relevance, translate medical jargon into plain English, and highlight any values or features that warrant physician attention.

2. STRUCTURED RESPONSE STYLE:
   - Use clean Markdown formatting: headings, bullet points, bold key terms, and summary tables where helpful.
   - For symptom inquiries, structure your answer into:
     * Overview & Potential Causes
     * Recommended Next Steps & Self-Care
     * Red Flag Warning Signs (When to seek urgent or emergency care)
     * Questions to Ask Your Doctor

3. SAFETY & TRIAGE:
   - Always prioritize patient safety. If symptoms suggest a medical emergency (e.g., chest pain, sudden numbness/weakness, severe shortness of breath, anaphylaxis, sudden severe headache), immediately advise seeking emergency medical services (911 or local emergency number).
   - Maintain a warm, empathetic, and professional tone.
   - Conclude responses with a brief, responsible medical disclaimer reminding the user that this guidance is informational and does not replace in-person clinical assessment by a licensed physician."""


def load_api_key():
    """Load API key from environment variable, Gemini.txt, or .env."""
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if key and key != "YOUR_GEMINI_API_KEY_HERE":
        return key

    # Look in current or parent directory for Gemini.txt
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    search_dirs = [current_dir, parent_dir]

    for d in search_dirs:
        txt_path = os.path.join(d, "Gemini.txt")
        if os.path.exists(txt_path):
            try:
                with open(txt_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    match = re.search(r"AIza[0-9A-Za-z\-_]{35}", content)
                    if match:
                        return match.group(0)
            except Exception:
                pass

        env_path = os.path.join(d, ".env")
        if os.path.exists(env_path):
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip().startswith("GEMINI_API_KEY="):
                            val = line.strip().split("=", 1)[1].strip().strip('"').strip("'")
                            if val and val != "YOUR_GEMINI_API_KEY_HERE":
                                return val
            except Exception:
                pass

    return ""


def call_gemini_api(api_key, model, contents, system_instruction=MEDICAL_SYSTEM_INSTRUCTION):
    """Call Google Gemini REST API with fallback models."""
    models_to_try = [model] + [m for m in DEFAULT_MODELS if m != model]
    last_error = "Unknown error"

    for m in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={api_key}"
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 4096,
            }
        }
        if system_instruction:
            payload["system_instruction"] = {
                "parts": [{"text": system_instruction}]
            }

        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data_bytes,
            headers={"Content-Type": "application/json"}
        )

        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                resp_data = json.loads(resp.read().decode("utf-8"))
                candidates = resp_data.get("candidates", [])
                if candidates and "content" in candidates[0]:
                    parts = candidates[0]["content"].get("parts", [])
                    reply_text = "".join(part.get("text", "") for part in parts)
                    return {"success": True, "model": m, "reply": reply_text}
                else:
                    return {"success": False, "error": "No response generated by model."}

        except urllib.error.HTTPError as e:
            err_body = ""
            try:
                err_body = e.read().decode("utf-8")
                err_json = json.loads(err_body)
                err_msg = err_json.get("error", {}).get("message", err_body)
            except Exception:
                err_msg = str(e)

            last_error = f"Model {m} error ({e.code}): {err_msg}"
            # If 404 (model deprecated) or 503 (high demand), try next model
            if e.code in (404, 503, 429):
                continue
            else:
                return {"success": False, "error": last_error}

        except Exception as e:
            last_error = f"Connection error with {m}: {str(e)}"
            continue

    return {"success": False, "error": last_error}
