from http.server import BaseHTTPRequestHandler
import json
import os
import sys

# Ensure local api folder can be imported from
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from _gemini import load_api_key, DEFAULT_MODELS
except ImportError:
    from api._gemini import load_api_key, DEFAULT_MODELS


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        api_key = load_api_key()
        has_key = bool(api_key and len(api_key) > 20)
        masked_key = f"{api_key[:6]}...{api_key[-4:]}" if has_key else ""
        res = {
            "has_key": has_key,
            "masked_key": masked_key,
            "default_model": DEFAULT_MODELS[0],
            "available_models": DEFAULT_MODELS,
        }
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(json.dumps(res).encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
