import streamlit as st
from openai import OpenAI
import json
import re
import os
# ---------------------------
# CONFIG (OPENROUTER)
# ---------------------------
@st.cache_resource
def get_client():
    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        st.error("🚨 OPENROUTER_API_KEY not found. Set it in Streamlit Secrets.")
        st.stop()

    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key
    )

client = get_client()
# ---------------------------
# PAGE SETUP
# ---------------------------
st.set_page_config(page_title="MedAssist AI", page_icon="🏥", layout="wide")
st.title("🏥 MedAssist AI - Hospital Expert System")

# ---------------------------
# EMERGENCY KEYWORDS
# ---------------------------
EMERGENCY_SIGNS = [
    "chest pain",
    "difficulty breathing",
    "unconscious",
    "severe bleeding",
    "heart attack",
    "stroke"
]

# ---------------------------
# CLEAN JSON FUNCTION
# ---------------------------
def clean_json(text):
    try:
        text = re.sub(r"```json|```", "", text)
        start = text.find("{")
        end = text.rfind("}") + 1
        return json.loads(text[start:end])
    except:
        return None

# ---------------------------
# EMERGENCY CHECK
# ---------------------------
def check_emergency(text):
    return any(word in text.lower() for word in EMERGENCY_SIGNS)

# ---------------------------
# OPENROUTER FUNCTION
# ---------------------------
def ask_ai(prompt, json_mode=False):
    try:
        params = {
            "model": "mistralai/mixtral-8x7b-instruct",
            "messages": [
                {"role": "system", "content": "You are a helpful medical assistant."},
                {"role": "user", "content": prompt}
            ]
        }

        # ✅ JSON mode only when needed
        if json_mode:
            params["response_format"] = {"type": "json_object"}

        response = client.chat.completions.create(**params)

        return response.choices[0].message.content

    except Exception as e:
        return f"⚠️ Error: {str(e)}"

# ---------------------------
# TABS
# ---------------------------
tab1, tab2, tab3 = st.tabs([
    "🧠 Symptom Checker",
    "🏥 Help Desk",
    "💬 General Chat"
])

# ===========================
# TAB 1: SYMPTOM CHECKER
# ===========================
with tab1:
    st.subheader("🧠 Describe your symptoms")

    user_input = st.text_area("Enter symptoms here")

    if st.button("Analyze Symptoms"):

        if not user_input.strip():
            st.warning("Please enter symptoms")

        elif check_emergency(user_input):
            st.error("🚨 EMERGENCY DETECTED! Seek immediate medical attention!")

        else:
            prompt = f"""
You are a medical expert system.

Return ONLY valid JSON.

FORMAT:
{{
  "possible_conditions": ["condition1", "condition2"],
  "urgency": "Low/Medium/High",
  "recommended_action": "text",
  "precautions": ["point1", "point2"]
}}

Symptoms: {user_input}
"""

            with st.spinner("Analyzing symptoms..."):
                response_text = ask_ai(prompt, json_mode=True)

            data = clean_json(response_text)

            if not data:
                st.error("⚠️ Could not parse response. Showing raw output:")
                st.write(response_text)
            else:
                st.success("Analysis Complete")

                st.write("### 🧾 Possible Conditions")
                for cond in data.get("possible_conditions", []):
                    st.write(f"- {cond}")

                urgency = data.get("urgency", "Low")

                if urgency == "High":
                    st.error(f"⚠️ Urgency: {urgency}")
                elif urgency == "Medium":
                    st.warning(f"⚠️ Urgency: {urgency}")
                else:
                    st.success(f"✅ Urgency: {urgency}")

                st.write("### 🏥 Recommended Action")
                st.write(data.get("recommended_action", "N/A"))

                st.write("### 🛡 Precautions")
                for p in data.get("precautions", []):
                    st.write(f"- {p}")

# ===========================
# TAB 2: HELP DESK
# ===========================
with tab2:
    st.subheader("🏥 Hospital Help Desk")

    help_query = st.text_input("Ask about hospital services")

    if st.button("Get Help"):

        if not help_query.strip():
            st.warning("Please enter your query")

        else:
            prompt = f"""
You are a hospital help desk assistant.

Answer clearly and naturally:
- Department guidance
- Appointments
- Visiting hours
- Emergency info

Query: {help_query}
"""

            with st.spinner("Fetching help..."):
                response_text = ask_ai(prompt)  # ❌ NO JSON MODE

            st.write(response_text)

# ===========================
# TAB 3: CHATBOT
# ===========================
with tab3:
    st.subheader("💬 Chat with MedAssist")

    if "chat" not in st.session_state:
        st.session_state.chat = []

    for msg in st.session_state.chat:
        st.chat_message(msg["role"]).markdown(msg["content"])

    user_msg = st.chat_input("Ask anything...")

    if user_msg:
        st.session_state.chat.append({"role": "user", "content": user_msg})
        st.chat_message("user").markdown(user_msg)

        prompt = f"""
You are a medical assistant chatbot.
Keep answers safe, short, and helpful.
User: {user_msg}
"""

        with st.spinner("Thinking..."):
            reply = ask_ai(prompt)  # ❌ NO JSON MODE

        st.session_state.chat.append({"role": "assistant", "content": reply})
        st.chat_message("assistant").markdown(reply)
