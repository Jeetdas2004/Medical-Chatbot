from http.server import BaseHTTPRequestHandler
import json
import os
import sys


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length)

        try:
            body = json.loads(post_data.decode("utf-8"))
            new_key = body.get("api_key", "").strip()
            if not new_key:
                self.send_json({"success": False, "error": "API key cannot be empty"}, status=400)
                return

            os.environ["GEMINI_API_KEY"] = new_key

            # In local environment, attempt saving to Gemini.txt
            try:
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                gemini_txt_path = os.path.join(base_dir, "Gemini.txt")
                with open(gemini_txt_path, "w", encoding="utf-8") as f:
                    f.write(f"{new_key} - < GEMINI API KEY\n\n$env:GEMINI_API_KEY=\"{new_key}\"\n")
            except OSError:
                # Read-only filesystem on serverless environments like Vercel
                pass

            self.send_json({"success": True, "message": "API Key saved successfully!"})
        except Exception as e:
            self.send_json({"success": False, "error": str(e)}, status=500)

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
