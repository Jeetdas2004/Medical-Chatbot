import os
import io
import time
import streamlit as st
from PIL import Image
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load environment variables
load_dotenv()

# --- Page Configuration ---
st.set_page_config(
    page_title="MediAssist - AI Medical & Health Chatbot",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for modern medical interface
st.markdown("""
<style>
    .medical-banner {
        background: linear-gradient(135deg, #1e3a8a 0%, #0284c7 100%);
        color: white;
        padding: 1.2rem 1.5rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .medical-banner h1 {
        color: white;
        margin: 0;
        font-size: 1.8rem;
    }
    .medical-banner p {
        margin: 0.4rem 0 0 0;
        opacity: 0.92;
        font-size: 0.95rem;
    }
    .disclaimer-card {
        background-color: #fffbeb;
        border-left: 4px solid #f59e0b;
        padding: 0.8rem 1rem;
        border-radius: 6px;
        margin-bottom: 1.2rem;
        font-size: 0.88rem;
        color: #92400e;
    }
    .emergency-card {
        background-color: #fef2f2;
        border-left: 4px solid #ef4444;
        padding: 0.8rem 1rem;
        border-radius: 6px;
        margin-bottom: 1rem;
        font-size: 0.88rem;
        color: #991b1b;
    }
    .stChatMessage {
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- Define Clinical Reference Tools for Function Calling ---
def get_drug_info(drug_name: str) -> str:
    """
    Retrieves detailed clinical and pharmacological information about a specific medication,
    including indications, standard adult dosage guidelines, precautions, and common side effects.
    
    Args:
        drug_name (str): The generic or brand name of the drug (e.g., 'ibuprofen', 'paracetamol', 'metformin').
    """
    drug_db = {
        "ibuprofen": {
            "class": "Nonsteroidal Anti-inflammatory Drug (NSAID)",
            "uses": "Relief of mild-to-moderate pain, inflammation, headache, dental pain, arthritis, fever reduction.",
            "common_side_effects": "Stomach upset, heartburn, nausea, indigestion, dizziness.",
            "precautions": "Take with food or milk. Avoid in active peptic ulcer, third trimester of pregnancy, or severe kidney/heart disease. Avoid combining with other NSAIDs.",
            "black_box": "May increase risk of serious cardiovascular thrombotic events and gastrointestinal bleeding."
        },
        "paracetamol": {
            "class": "Analgesic & Antipyretic (Acetaminophen)",
            "uses": "Pain relief (mild to moderate), fever reduction.",
            "common_side_effects": "Rare at recommended doses. May cause skin rash or nausea.",
            "precautions": "Maximum recommended daily dose is 4000 mg in adults (lower in liver impairment). Avoid alcohol.",
            "black_box": "Severe hepatotoxicity/liver damage risk in case of overdose or concurrent heavy alcohol consumption."
        },
        "amoxicillin": {
            "class": "Beta-lactam Antibiotic (Penicillin class)",
            "uses": "Bacterial infections of ear, nose, throat, respiratory tract, and skin.",
            "common_side_effects": "Diarrhea, nausea, vomiting, mild skin rash.",
            "precautions": "Contraindicated in patients with known penicillin or cephalosporin allergy. Complete full prescribed course to prevent antibiotic resistance.",
            "black_box": "Severe hypersensitivity (anaphylaxis) reactions possible."
        },
        "loratadine": {
            "class": "Second-generation Antihistamine",
            "uses": "Relief of allergy symptoms including allergic rhinitis, sneezing, runny nose, itchy watery eyes, and hives.",
            "common_side_effects": "Headache, dry mouth, mild fatigue (non-sedating in most patients).",
            "precautions": "Dose adjustment needed in severe hepatic or renal impairment.",
            "black_box": "None."
        },
        "aspirin": {
            "class": "NSAID & Antiplatelet Agent (Acetylsalicylic Acid)",
            "uses": "Pain relief, fever, acute coronary syndrome, secondary prevention of cardiovascular events (low-dose 81mg).",
            "common_side_effects": "Gastric irritation, increased bleeding tendency, tinnitus at high doses.",
            "precautions": "Strictly contraindicated in children/teens with viral infections due to Reye's Syndrome risk. Avoid in bleeding disorders.",
            "black_box": "Increased risk of major gastrointestinal and cerebral bleeding."
        },
        "metformin": {
            "class": "Biguanide Antidiabetic Agent",
            "uses": "First-line management of Type 2 Diabetes Mellitus to improve glycemic control.",
            "common_side_effects": "Nausea, diarrhea, abdominal cramping, metallic taste, decreased Vitamin B12 levels.",
            "precautions": "Take with meals. Monitor kidney function (eGFR). Discontinue before iodinated radiocontrast procedures.",
            "black_box": "Lactic acidosis risk, particularly in renal or acute hepatic impairment."
        },
        "cetirizine": {
            "class": "Second-generation Antihistamine",
            "uses": "Allergic rhinitis, hay fever, chronic urticaria (itchy hives).",
            "common_side_effects": "Mild drowsiness, dry mouth, dizziness, fatigue.",
            "precautions": "May cause sedation; use caution when driving. Dose reduction in kidney impairment.",
            "black_box": "None."
        },
        "omeprazole": {
            "class": "Proton Pump Inhibitor (PPI)",
            "uses": "GERD, acid reflux, peptic ulcers, heartburn.",
            "common_side_effects": "Headache, abdominal pain, flatulence, nausea.",
            "precautions": "Best taken 30-60 minutes before breakfast. Long-term use can reduce magnesium and calcium absorption.",
            "black_box": "Long-term high-dose use associated with increased risk of bone fractures and C. difficile-associated diarrhea."
        }
    }
    key = drug_name.strip().lower()
    for name, data in drug_db.items():
        if name in key or key in name:
            return (
                f"### Clinical Drug Summary: {name.capitalize()}\n"
                f"- **Drug Class:** {data['class']}\n"
                f"- **Primary Uses:** {data['uses']}\n"
                f"- **Common Side Effects:** {data['common_side_effects']}\n"
                f"- **Clinical Precautions:** {data['precautions']}\n"
                f"- **Important Safety Warning:** {data['black_box']}\n"
                f"*Note: Always follow prescription instructions and verify with your physician or pharmacist.*"
            )
    return (
        f"Specific pre-indexed database entry not found for '{drug_name}'. "
        f"Providing general pharmacological knowledge. Please consult your physician or pharmacist for individualized dosage."
    )

def suggest_common_otc_medicine(ailment: str) -> str:
    """
    Suggests safe, evidence-based over-the-counter (OTC) symptomatic relief options
    for common, mild, non-emergency ailments.
    
    Args:
        ailment (str): The common symptom or condition (e.g., 'headache', 'fever', 'cold', 'sore throat', 'acid reflux').
    """
    otc_db = {
        "headache": (
            "- **First-line OTC options:** Paracetamol (Acetaminophen) 500-1000mg or Ibuprofen 200-400mg with food.\n"
            "- **Supportive measures:** Hydrate, rest in a dim/quiet room, apply a cool temple compress.\n"
            "- **Emergency Warning:** Seek emergency care if headache is sudden and explosive ('thunderclap'), or accompanied by high fever, stiff neck, vision loss, or numbness."
        ),
        "fever": (
            "- **First-line OTC options:** Paracetamol or Ibuprofen (do not exceed daily recommended limits).\n"
            "- **Supportive measures:** Drink plenty of electrolytes/fluids, wear lightweight clothing, rest.\n"
            "- **Emergency Warning:** Seek urgent care if fever exceeds 103°F (39.4°C), lasts >3 days, or occurs in infants under 3 months."
        ),
        "cold": (
            "- **First-line OTC options:** Saline nasal sprays, oral decongestants (e.g., pseudoephedrine/phenylephrine with blood pressure caution), honey for cough (adults/children >1 yr).\n"
            "- **Supportive measures:** Steam inhalation, warm fluids, adequate sleep.\n"
            "- **Warning:** Antibiotics are completely ineffective against viral colds."
        ),
        "sore throat": (
            "- **First-line OTC options:** Lozenges with benzocaine/menthol, warm saltwater gargles (1/2 tsp salt in warm water), ibuprofen or paracetamol.\n"
            "- **Warning:** Seek evaluation if accompanied by difficulty swallowing saliva, breathing issues, or white patches on tonsils."
        ),
        "allergies": (
            "- **First-line OTC options:** Non-sedating antihistamines (Cetirizine, Loratadine, Fexofenadine), steroid nasal spray (Fluticasone).\n"
            "- **Supportive measures:** Avoid known allergens, rinse sinuses with sterile saline."
        ),
        "acid reflux": (
            "- **First-line OTC options:** Antacids (calcium carbonate) for fast relief; Famotidine (H2 blocker) or Omeprazole for persistent reflux.\n"
            "- **Lifestyle:** Avoid eating within 3 hours of lying down; avoid spicy, fried, or acidic foods."
        )
    }
    key = ailment.strip().lower()
    for symptom, advice in otc_db.items():
        if symptom in key or key in symptom:
            return f"**Evidence-Based OTC Guidance for {symptom.capitalize()}:**\n{advice}"
    return (
        "For general mild symptoms, ensure adequate hydration and rest. "
        "Consult a pharmacist or physician before starting any over-the-counter medication, especially if you have chronic health conditions or take other prescription medications."
    )

def triage_and_self_care_advice(symptom_or_condition: str) -> str:
    """
    Evaluates symptoms for self-care actions, home supportive measures,
    and identifies critical 'Red Flag' symptoms that demand urgent emergency evaluation.
    
    Args:
        symptom_or_condition (str): Description of the symptoms (e.g., 'cough', 'burn', 'diarrhea', 'chest pain').
    """
    triage_db = {
        "burn": {
            "home_care": "Cool the burn under gentle running cool tap water for 10-20 minutes immediately. Never use ice, butter, or toothpaste. Apply pure aloe vera gel or petroleum jelly, and cover loosely with a sterile non-stick bandage.",
            "red_flags": "Seek immediate ER care if the burn is larger than 3 inches, on the face, hands, feet, joints, or groin, causes charred/white skin (3rd degree), or is caused by electricity/chemicals."
        },
        "cough": {
            "home_care": "Stay hydrated with warm broths or herbal tea. Use a cool-mist humidifier in your room. 1-2 teaspoons of honey can soothe cough in adults and children over age 1.",
            "red_flags": "See a doctor immediately if coughing up blood, experiencing severe shortness of breath, chest tightness, wheezing, or high fever lasting >48 hours."
        },
        "diarrhea": {
            "home_care": "Prevent dehydration with Oral Rehydration Solutions (ORS), clear broths, and diluted electrolyte solutions. Stick to bland foods (bananas, rice, toast). Avoid dairy, alcohol, and caffeine.",
            "red_flags": "Go to urgent care if diarrhea contains blood or black tarry stools, is accompanied by high fever (>102°F), signs of severe dehydration (dizziness, no urine), or lasts >2 days."
        },
        "chest pain": {
            "home_care": "NONE. Chest discomfort requires immediate professional evaluation.",
            "red_flags": "🚨 CALL 911 / 112 / EMERGENCY IMMEDIATELY. Pressure, squeezing, or pain radiating to jaw, neck, back, or left arm, along with sweating, nausea, or shortness of breath could be a heart attack."
        }
    }
    key = symptom_or_condition.strip().lower()
    for cond, data in triage_db.items():
        if cond in key or key in cond:
            return (
                f"### Triage & Self-Care: {cond.capitalize()}\n"
                f"- **Recommended Home Actions:** {data['home_care']}\n"
                f"- **⚠️ RED FLAG EMERGENCY CRITERIA:** {data['red_flags']}"
            )
    return (
        "Monitor your symptoms closely. If symptoms are sudden, unusually severe, worsening rapidly, "
        "or accompanied by breathing difficulty, high fever, or confusion, seek immediate medical attention."
    )

# System instruction establishing medical personality and safety boundaries
MEDICAL_SYSTEM_INSTRUCTION = """
You are 'MediAssist', an empathetic, knowledgeable, and reliable AI Medical & Health Assistant.
Your core mission is to empower users with accurate medical explanations, health education, medication understanding, and safe symptom triage.

Key Clinical Rules:
1. Empathy & Clarity: Speak clearly, kindly, and in easy-to-understand terms. Explain complex medical jargon.
2. Safety & Boundaries: You are an educational AI assistant, NOT a licensed doctor. Always clarify that your answers are for educational and guidance purposes, not definitive diagnosis or treatment plans.
3. Tool Usage: Utilize the available tools (get_drug_info, suggest_common_otc_medicine, triage_and_self_care_advice) whenever users ask about medications, symptoms, OTC relief, or home first-aid.
4. Image Analysis: When users upload medical photos (skin symptoms, rashes, prescription slips, or medicine packaging), carefully describe what is visible, suggest potential categories or possibilities to discuss with a physician, read label details clearly, and advise seeing a healthcare professional for in-person examination.
5. Red Flags First: If any symptom sounds potentially life-threatening (e.g., crushing chest pain, stroke symptoms FAST - face drooping, arm weakness, speech difficulty, anaphylaxis, severe head trauma, suicide risk), immediately prioritize instructing them to call emergency services (911 / 112 / local emergency) or go to the nearest emergency room.
"""

# Available tools list
MEDICAL_TOOLS = [get_drug_info, suggest_common_otc_medicine, triage_and_self_care_advice]

# --- Sidebar UI ---
with st.sidebar:
    st.image("https://img.icons8.com/color/96/medical-heart.png", width=64)
    st.title("MediAssist Settings")
    
    # API Key Management
    st.subheader("🔑 Gemini API Key")
    default_key = os.getenv("GEMINI_API_KEY", "")
    
    user_api_key = st.text_input(
        "Enter your Gemini API Key:",
        value=default_key,
        type="password",
        help="Get a free Gemini API Key from Google AI Studio: https://aistudio.google.com/app/apikey"
    )
    
    if user_api_key:
        st.caption("✅ API Key provided")
    else:
        st.warning("⚠️ Please provide a Gemini API Key to chat.")
        st.markdown("[Get a free API Key here →](https://aistudio.google.com/app/apikey)")
    
    # Model Selection
    model_choice = st.selectbox(
        "Gemini Model:",
        options=["gemini-3.8-flash", "gemini-3.5-flash-lite", "gemini-3.1-flash-lite"],
        index=0,
        help="Gemini 3.8 Flash is Google's flagship model. Gemini 3.5 Flash-Lite provides ultra-fast backup."
    )
    
    st.divider()
    
    # Quick Starter Prompts
    st.subheader("💡 Quick Clinical Topics")
    quick_prompts = [
        "What are the common side effects & precautions for Ibuprofen?",
        "What should I do for a mild kitchen burn?",
        "Home remedies and red flags for a lingering cough",
        "Safe OTC options for seasonal allergy relief",
        "How do I recognize signs of a stroke (FAST)?"
    ]
    
    for prompt_text in quick_prompts:
        if st.button(prompt_text, use_container_width=True, key=f"quick_{prompt_text[:15]}"):
            st.session_state["pending_prompt"] = prompt_text
    
    st.divider()
    
    # Clear conversation button
    if st.button("🗑️ Clear Conversation", use_container_width=True):
        st.session_state.messages = []
        if "pending_prompt" in st.session_state:
            del st.session_state["pending_prompt"]
        st.rerun()

# --- Main App Header ---
st.markdown("""
<div class="medical-banner">
    <h1>🩺 MediAssist AI - Medical & Health Companion</h1>
    <p>Empathetic, evidence-informed health guidance, drug information, and multimodal symptom assistance.</p>
</div>
""", unsafe_allow_html=True)

# Important Disclaimers Banner
st.markdown("""
<div class="disclaimer-card">
    <strong>📋 Medical Notice:</strong> MediAssist provides general health and educational information. It is not a replacement for professional clinical judgment, diagnosis, or treatment. Always consult a qualified healthcare provider for personalized medical advice.
</div>
<div class="emergency-card">
    <strong>🚨 Emergency Alert:</strong> If you or someone you are assisting is experiencing severe chest pain, shortness of breath, symptoms of stroke, uncontrollable bleeding, or severe allergic reaction, please dial <strong>911 / 112</strong> or your local emergency services immediately.
</div>
""", unsafe_allow_html=True)

# Helper to safely convert PIL Image into a valid Gemini Part
def pil_to_part(img):
    try:
        buf = io.BytesIO()
        if hasattr(img, "mode") and img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.save(buf, format="JPEG")
        return types.Part.from_bytes(data=buf.getvalue(), mime_type="image/jpeg")
    except Exception:
        return None

# Helper function to execute bot turn with AFC and fallback
def execute_bot_turn(user_api_key: str, model_choice: str):
    if not st.session_state.messages:
        return
    last_user_msg = st.session_state.messages[-1]
    user_prompt = str(last_user_msg.get("content", "")).strip()
    active_image = last_user_msg.get("image")
    
    with st.chat_message("assistant"):
        with st.spinner("Analyzing with medical knowledge..."):
            try:
                client = genai.Client(api_key=user_api_key.strip())
                config = types.GenerateContentConfig(
                    system_instruction=MEDICAL_SYSTEM_INSTRUCTION,
                    tools=MEDICAL_TOOLS,
                    temperature=0.2,
                )
                
                # Build history list of prior messages (strictly types.Part)
                history_contents = []
                for msg in st.session_state.messages[:-1][-8:]:
                    role_tag = "user" if msg.get("role") == "user" else "model"
                    content_str = str(msg.get("content", "")).strip()
                    parts = []
                    
                    if msg.get("image") is not None and isinstance(msg["image"], Image.Image):
                        img_part = pil_to_part(msg["image"])
                        if img_part:
                            parts.append(img_part)
                    
                    if content_str:
                        parts.append(types.Part.from_text(text=content_str))
                    
                    if parts:
                        history_contents.append(
                            types.Content(
                                role=role_tag,
                                parts=parts
                            )
                        )
                
                # Prepare current turn parts strictly as types.Part
                current_parts = []
                if active_image and isinstance(active_image, Image.Image):
                    img_part = pil_to_part(active_image)
                    if img_part:
                        current_parts.append(img_part)
                current_parts.append(types.Part.from_text(text=user_prompt))
                
                # Modern supported model candidate chain
                candidate_models = list(dict.fromkeys([
                    model_choice,
                    "gemini-3.8-flash",
                    "gemini-3.5-flash-lite",
                    "gemini-3.1-flash-lite"
                ]))
                
                reply_text = None
                last_error = None
                used_model = None
                
                for target_model in candidate_models:
                    for retry_count in range(2):
                        try:
                            chat = client.chats.create(
                                model=target_model,
                                config=config,
                                history=history_contents if history_contents else None
                            )
                            response = chat.send_message(current_parts)
                            if response and response.text:
                                reply_text = response.text
                                used_model = target_model
                                break
                        except Exception as attempt_err:
                            err_str = str(attempt_err).lower()
                            last_error = attempt_err
                            # If temporary server load (503 / 429), back off briefly and retry
                            if any(k in err_str for k in ["503", "unavailable", "high demand", "429"]):
                                time.sleep(1.5)
                                continue
                            else:
                                break
                    if reply_text:
                        break
                
                if reply_text is None:
                    if last_error:
                        raise last_error
                    else:
                        reply_text = "I am here to help. Could you please provide more details about your symptom or question?"
                elif used_model and used_model != model_choice:
                    reply_text += f"\n\n*(Note: Responded using `{used_model}` due to temporary peak traffic on `{model_choice}`)*"
                
            except Exception as e:
                err_msg = str(e)
                if "leaked" in err_msg.lower() or "permission_denied" in err_msg.lower() or "403" in err_msg:
                    reply_text = (
                        "🚨 **API Key Authentication Error:**\n\n"
                        "The Gemini API key provided appears to be invalid or was flagged as revoked/leaked by Google.\n\n"
                        "**How to fix:**\n"
                        "1. Go to [Google AI Studio (aistudio.google.com)](https://aistudio.google.com/app/apikey).\n"
                        "2. Click **'Create API Key'** (it is free).\n"
                        "3. Paste the new key into the **Gemini API Key** field in the left sidebar."
                    )
                else:
                    reply_text = f"An error occurred while generating the response: `{err_msg}`\n\nPlease check your network connection and try again."
            
            st.markdown(reply_text)
            st.session_state.messages.append({
                "role": "assistant",
                "content": reply_text
            })

# Initialize and sanitize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []
else:
    # Sanitize any legacy or corrupted entries
    clean_history = []
    for msg in st.session_state.messages:
        if isinstance(msg, dict):
            c_text = msg.get("content", "")
            if not isinstance(c_text, str):
                c_text = str(c_text) if c_text is not None else ""
            clean_history.append({
                "role": msg.get("role", "user"),
                "content": c_text,
                "image": msg.get("image") if isinstance(msg.get("image"), Image.Image) else None
            })
    st.session_state.messages = clean_history

# Inline Message Editor if an edit was requested
if "editing_index" in st.session_state and st.session_state["editing_index"] is not None:
    edit_idx = st.session_state["editing_index"]
    if edit_idx < len(st.session_state.messages):
        orig_msg = st.session_state.messages[edit_idx]
        with st.container():
            st.info("✏️ **Edit Mode:** Update your question below and click **Save & Regenerate**.")
            edited_text = st.text_area("Modify your prompt:", value=orig_msg["content"], height=100, key="edit_text_area")
            col_save, col_cancel = st.columns([0.25, 0.75])
            with col_save:
                if st.button("💾 Save & Regenerate", type="primary", use_container_width=True):
                    st.session_state.messages[edit_idx]["content"] = edited_text
                    # Truncate messages after this question so the model regenerates context from here
                    st.session_state.messages = st.session_state.messages[:edit_idx + 1]
                    del st.session_state["editing_index"]
                    st.session_state["trigger_regeneration"] = True
                    st.rerun()
            with col_cancel:
                if st.button("❌ Cancel", use_container_width=True):
                    del st.session_state["editing_index"]
                    st.rerun()

# Display Chat History with Edit/Delete Controls for User Messages
for idx, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        if message["role"] == "user":
            if "image" in message and message["image"] is not None:
                st.image(message["image"], caption="Uploaded Image", width=260)
            st.markdown(message["content"])
            
            # Action controls below the user message
            col_spacer, col_edit, col_del = st.columns([0.80, 0.10, 0.10])
            with col_edit:
                if st.button("✏️ Edit", key=f"edit_btn_{idx}", help="Edit this question and regenerate response"):
                    st.session_state["editing_index"] = idx
                    st.rerun()
            with col_del:
                if st.button("🗑️ Delete", key=f"del_btn_{idx}", help="Delete this question and answer"):
                    del_indices = [idx]
                    if idx + 1 < len(st.session_state.messages) and st.session_state.messages[idx+1]["role"] == "assistant":
                        del_indices.append(idx + 1)
                    st.session_state.messages = [m for i, m in enumerate(st.session_state.messages) if i not in del_indices]
                    st.rerun()
        else:
            st.markdown(message["content"])

# Trigger regeneration after edit
if st.session_state.get("trigger_regeneration"):
    del st.session_state["trigger_regeneration"]
    execute_bot_turn(user_api_key, model_choice)

# Multimodal Image Upload Section
with st.expander("📷 Upload an Image (Prescription, Medicine Box, Skin Symptom, or Report)", expanded=False):
    uploaded_file = st.file_uploader(
        "Choose an image (PNG, JPG, JPEG, WEBP)",
        type=["png", "jpg", "jpeg", "webp"],
        key="image_uploader"
    )
    if uploaded_file is not None:
        st.image(uploaded_file, caption="Selected Image for Analysis", width=220)
        st.info("Image attached! Type your question below (e.g., 'What is this medication used for?' or 'Please explain what this report says').")

# Process user input (either from chat input or quick prompt button)
user_prompt = st.chat_input("Ask a medical question, inquire about a medication, or describe a symptom...")

# Handle quick button click
if "pending_prompt" in st.session_state and st.session_state["pending_prompt"]:
    user_prompt = st.session_state.pop("pending_prompt")

if user_prompt:
    if not user_api_key:
        st.error("Please enter a valid Gemini API Key in the left sidebar to start chatting.")
        st.stop()
        
    active_image = None
    if uploaded_file is not None:
        try:
            active_image = Image.open(uploaded_file)
        except Exception as img_err:
            st.error(f"Could not open uploaded image: {img_err}")
    
    # Store user message
    st.session_state.messages.append({
        "role": "user",
        "content": user_prompt,
        "image": active_image
    })
    
    # Display user message immediately
    with st.chat_message("user"):
        if active_image:
            st.image(active_image, caption="Uploaded Image", width=260)
        st.markdown(user_prompt)
        
    execute_bot_turn(user_api_key, model_choice)
