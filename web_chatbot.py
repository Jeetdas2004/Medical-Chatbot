"""
Dr. Gemini - Multimodal Medical AI Chatbot Launcher
Compatible with both direct Python execution (Zero-dependency web app)
and existing workflows.
"""

import os
import sys

def main():
    print("=" * 65)
    print("🩺 Starting Dr. Gemini Medical AI Chatbot...")
    print("=" * 65)
    
    # Import and start the web server from app.py
    try:
        from app import start_server
        start_server(port=8000, open_browser=True)
    except Exception as e:
        print(f"Error launching chatbot server: {e}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()
