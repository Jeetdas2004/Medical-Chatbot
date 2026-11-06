"""
AI Medical Chatbot - Gemini Multimodal Assistant
Zero-dependency Python server with full Gemini AI capabilities:
- Multimodal image analysis (prescriptions, reports, symptoms, pills)
- Medical doctor knowledge persona with clinical triage and advice
- Edit prompt feature (regenerate from any turn)
- Automatic model fallback (gemini-3.5-flash, gemini-3-flash-preview, gemini-3.1-flash-lite, gemini-3.8-flash)
- Modern Gemini AI web interface
"""

import os
import re
import sys
import json
import base64
import urllib.request
import urllib.error
import webbrowser
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

PORT = 8000
HOST = "localhost"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Candidate models in priority order
DEFAULT_MODELS = [
    "gemini-3.5-flash",
    "gemini-3-flash-preview",
    "gemini-3.1-flash-lite",
    "gemini-3.8-flash",
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
    """Load API key from environment variable or Gemini.txt."""
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if key and key != "YOUR_GEMINI_API_KEY_HERE":
        return key

    gemini_txt_path = os.path.join(SCRIPT_DIR, "Gemini.txt")
    if os.path.exists(gemini_txt_path):
        try:
            with open(gemini_txt_path, "r", encoding="utf-8") as f:
                content = f.read()
                # Find Google API key pattern (AIzaSy...)
                match = re.search(r"AIza[0-9A-Za-z\-_]{35}", content)
                if match:
                    return match.group(0)
        except Exception as e:
            print(f"Error reading Gemini.txt: {e}")

    env_path = os.path.join(SCRIPT_DIR, ".env")
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip().startswith("GEMINI_API_KEY="):
                        val = line.strip().split("=", 1)[1].strip().strip('"').strip("'")
                        if val:
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
            print(f"[Gemini API] {last_error}. Attempting fallback...")
            # If 404 (model deprecated) or 503 (high demand), try next model
            if e.code in (404, 503, 429):
                continue
            else:
                return {"success": False, "error": last_error}

        except Exception as e:
            last_error = f"Connection error with {m}: {str(e)}"
            print(f"[Gemini API] {last_error}")
            continue

    return {"success": False, "error": last_error}


class MedicalChatbotHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=SCRIPT_DIR, **kwargs)

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            index_path = os.path.join(SCRIPT_DIR, "index.html")
            with open(index_path, "rb") as f:
                self.wfile.write(f.read())
            return

        if self.path == "/api/config":
            api_key = load_api_key()
            has_key = bool(api_key and len(api_key) > 20)
            masked_key = f"{api_key[:6]}...{api_key[-4:]}" if has_key else ""
            res = {
                "has_key": has_key,
                "masked_key": masked_key,
                "default_model": DEFAULT_MODELS[0],
                "available_models": DEFAULT_MODELS,
            }
            self.send_json(res)
            return

        super().do_GET()

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length)

        if self.path == "/api/chat":
            try:
                body = json.loads(post_data.decode("utf-8"))
            except Exception as e:
                self.send_json({"success": False, "error": f"Invalid JSON: {e}"}, status=400)
                return

            api_key = body.get("api_key", "").strip() or load_api_key()
            if not api_key:
                self.send_json({
                    "success": False,
                    "error": "No Gemini API Key found. Please add your key in the settings panel."
                }, status=400)
                return

            messages = body.get("messages", [])
            if not messages:
                self.send_json({"success": False, "error": "No messages provided."}, status=400)
                return

            model = body.get("model", DEFAULT_MODELS[0])

            # Prepare Gemini contents payload
            gemini_contents = []
            for msg in messages:
                role = "user" if msg.get("role") == "user" else "model"
                parts = []
                
                # If message has an image attachment (base64)
                if msg.get("image"):
                    img_info = msg["image"]
                    parts.append({
                        "inline_data": {
                            "mime_type": img_info.get("mime_type", "image/jpeg"),
                            "data": img_info.get("data", "")
                        }
                    })

                text_content = msg.get("text", "").strip()
                if text_content:
                    parts.append({"text": text_content})
                elif not parts:
                    parts.append({"text": "Please analyze this image from a medical standpoint."})

                gemini_contents.append({
                    "role": role,
                    "parts": parts
                })

            result = call_gemini_api(api_key, model, gemini_contents)
            self.send_json(result)
            return

        if self.path == "/api/save_key":
            try:
                body = json.loads(post_data.decode("utf-8"))
                new_key = body.get("api_key", "").strip()
                if not new_key:
                    self.send_json({"success": False, "error": "API key cannot be empty"}, status=400)
                    return

                gemini_txt_path = os.path.join(SCRIPT_DIR, "Gemini.txt")
                with open(gemini_txt_path, "w", encoding="utf-8") as f:
                    f.write(f"{new_key} - < GEMINI API KEY\n\n$env:GEMINI_API_KEY=\"{new_key}\"\n")
                
                os.environ["GEMINI_API_KEY"] = new_key
                self.send_json({"success": True, "message": "API Key saved successfully!"})
            except Exception as e:
                self.send_json({"success": False, "error": str(e)}, status=500)
            return

        self.send_json({"error": "Endpoint not found"}, status=404)

    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def log_message(self, format, *args):
        # Clean console logging
        sys.stderr.write(f"[{self.log_date_time_string()}] {args[0]} {args[1]}\n")


def start_server(port=PORT, open_browser=True):
    server_address = (HOST, port)
    try:
        httpd = ThreadingHTTPServer(server_address, MedicalChatbotHandler)
    except OSError:
        # Port might be busy, pick another
        port = port + 1
        server_address = (HOST, port)
        httpd = ThreadingHTTPServer(server_address, MedicalChatbotHandler)

    url = f"http://{HOST}:{port}"
    print("=" * 65)
    print("🩺 Dr. Gemini - Multimodal Medical AI Chatbot")
    print("=" * 65)
    print(f"🚀 Server is live at: {url}")
    print("✨ Features: Full Medical Knowledge, Edit Prompt, Insert Image, Auto-fallback")
    print("Press Ctrl+C to stop the server.")
    print("=" * 65)

    if open_browser:
        webbrowser.open(url)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        httpd.server_close()


if __name__ == "__main__":
    start_server(open_browser=True)

