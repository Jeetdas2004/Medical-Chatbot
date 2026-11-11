from http.server import BaseHTTPRequestHandler
import json
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from _gemini import load_api_key, call_gemini_api, DEFAULT_MODELS
except ImportError:
    from api._gemini import load_api_key, call_gemini_api, DEFAULT_MODELS


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length)

        try:
            body = json.loads(post_data.decode("utf-8"))
        except Exception as e:
            self.send_json({"success": False, "error": f"Invalid JSON: {e}"}, status=400)
            return

        api_key = body.get("api_key", "").strip() or load_api_key()
        if not api_key:
            self.send_json({
                "success": False,
                "error": "No Gemini API Key found. Please add your key in the settings panel or set GEMINI_API_KEY environment variable."
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

            # Multimodal image attachment
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

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))
