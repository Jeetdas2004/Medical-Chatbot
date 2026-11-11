# 🩺 Dr. Gemini - Multimodal Medical AI Chatbot

An AI-powered Medical Assistant chatbot designed with the look, feel, and capabilities of **Google Gemini AI**.

---

## ✨ Features

1. **👨‍⚕️ Comprehensive Medical Clinical Knowledge**:
   - Responds like a clinical doctor / medical consultant across pathology, pharmacology, symptoms, triage, and nutrition.
   - Clinical structuring: Potential Causes, Self-Care & Recommended Actions, **Red Flag Warning Signs** (Emergency triage), and Questions to Ask Your Doctor.
   - Detailed drug information: Indications, mechanisms, dosages, contraindications, and drug-drug interactions.
   - Built-in patient safety notices and medical disclaimers.

2. **✏️ Edit Prompt (Gemini AI Feature)**:
   - Every sent prompt has an **"✏️ Edit prompt"** button.
   - Allows modifying questions in-place.
   - On saving, the conversation updates to that point and automatically regenerates the AI doctor's response!

3. **📷 Insert / Attach Image (Multimodal Vision)**:
   - Dedicated **Insert Image button (📷)** in the prompt bar.
   - **Drag & drop** image support directly onto the chat window.
   - **Clipboard paste (`Ctrl + V`)** image support.
   - Interactive attachment preview chip with thumbnail and remove (`✕`) button.
   - Supports medical lab reports, prescriptions, rash/skin photos, X-rays, ECGs, and pill labels.
   - Click any sent image in chat to view it in full enlarged modal resolution.

4. **⚡ Seamless Gemini Models & Auto-Fallback**:
   - Supports current working models:
     * `gemini-3.5-flash` (Fast, high intelligence)
     * `gemini-3-flash-preview`
     * `gemini-3.1-flash-lite`
     * `gemini-3.8-flash`
   - Built-in intelligent auto-fallback: If a model experiences high demand (HTTP 503) or is deprecated (HTTP 404), the system automatically retries with the next active model seamlessly.

5. **🔊 Bonus Features**:
   - **Copy response** button with one click.
   - **Read Aloud (TTS)** voice readout using speech synthesis.
   - Zero external pip dependencies required to launch the web app.

---

## 🚀 How to Run

### Method 1: Double-Click (Easiest)
Simply double-click:
```
run_chatbot.bat
```
Your browser will automatically open to `http://localhost:8000`.

### Method 2: Command Line
Open PowerShell or Command Prompt in this directory and run:
```bash
python app.py
```
*(or `python web_chatbot.py`)*

---

## 🔑 API Key
- The bot automatically loads your key from `Gemini.txt` or the `GEMINI_API_KEY` environment variable.
- You can also view, enter, or update your API key anytime in the sidebar of the chat interface (persisted locally in browser).

---

## 🌐 Deploy to Vercel

1. Commit and push your latest code to GitHub:
   ```bash
   git add .
   git commit -m "Configure Vercel serverless deployment"
   git push origin main
   ```
2. Go to [vercel.com](https://vercel.com) and log in.
3. Click **"Add New..."** -> **"Project"**.
4. Select your GitHub repository (`Multilingual-RAG-based-Chatbot`) and click **Import**.
5. Leave the default Build & Output settings.
6. Expand **Environment Variables** and add:
   - **Key**: `GEMINI_API_KEY`
   - **Value**: Your Google Gemini API Key
7. Click **Deploy**. Your medical assistant is now live on the web!

