# 🩺 MediAssist - AI Medical & Health Chatbot

An intelligent, empathetic, and evidence-informed Medical AI Assistant built with **Streamlit** and the official **Google GenAI SDK (`google-genai`)** powered by **Gemini 3.8 Flash**.

---

## 🌟 Key Features

1. **Clinical Guidance & Triage Tools (Function Calling):**
   - `get_drug_info`: Detailed uses, side effects, precautions, and contraindications.
   - `suggest_common_otc_medicine`: Safe over-the-counter and supportive remedies for non-emergency conditions.
   - `triage_and_self_care_advice`: Evidence-based home care steps plus critical **Red Flag Emergency Alerts** (e.g., stroke FAST signs, cardiac symptoms).

2. **Multimodal Image Analysis:**
   - Upload photos of medicine strips/boxes, skin symptoms, lab reports, or prescriptions for educational explanations and label breakdown.

3. **User-Friendly Web Interface:**
   - Interactive prompt shortcuts for common clinical questions.
   - Live sidebar API Key management and model selection (`gemini-3.8-flash` / `gemini-2.5-flash`).
   - One-click conversation reset.
   - Medical and emergency disclaimer banners.

---

## 🚀 How to Run

### Method 1: Double-Click Launcher
Double-click `run_chatbot.bat` in this folder.

### Method 2: Command Line
Open a PowerShell or Command Prompt terminal in this directory and run:
```powershell
.venv\Scripts\python.exe -m streamlit run web_chatbot.py
```
Then open your browser at: **`http://localhost:8501`**

---

## 🔑 Setting Up Your Gemini API Key

1. Generate a free Gemini API Key at [Google AI Studio](https://aistudio.google.com/app/apikey).
2. Enter it directly in the **MediAssist Settings** sidebar in the web application, or save it in your `.env` file:
   ```env
   GEMINI_API_KEY=your_actual_api_key_here
   ```

