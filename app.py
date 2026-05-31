import streamlit as st
import requests
import json
import os
from google import genai
from google.genai import types

# --- SOVEREIGN INTEL CONFIGURATION ---
st.set_page_config(page_title="EFFIONG AI — Sovereign Intelligence Portal", layout="wide")
st.title("🌍 EFFIONG AI — Sovereign Intelligence Portal")
st.caption("Version 4.0 | Multi-Neural Routing Architecture | Persistent Memory Grid")

# --- INITIALIZE CORE ARCHITECTURE STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- FETCH CLOUD SECRETS ---
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    GITHUB_REPO = st.secrets["GITHUB_REPO"]
except Exception as e:
    st.error("Missing critical backend credentials in Streamlit Secrets Manager.")
    st.stop()

# --- SIDEBAR: CROWDSOURCED ARCHIVE PORTAL ---
with st.sidebar:
    st.header("📜 African Heritage Archive")
    st.write("Submit oral histories, dialects, or cultural facts directly to Effiong AI's permanent cloud memory.")
    
    contributor = st.text_input("Contributor Name", "Anonymous")
    data_type = st.selectbox("Data Type", ["Historical Account", "Dialect/Linguistic Nuance", "Folklore/Story", "Correction of Bias"])
    heritage_data = st.text_area("Enter Context/Knowledge Block")
    
    if st.button("Submit to Sovereign Archive"):
        if heritage_data:
            # Setup payload to commit back to GitHub ledger autonomously
            log_entry = f"\n\n=== ARCHIVE TRANSACTION ===\nContributor: {contributor}\nType: {data_type}\nData: {heritage_data}\n"
            
            # Simple automatic text logging back to GitHub repository
            url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/effiong_brain_ledger.txt"
            headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
            
            # Check if file exists to get SHA
            res = requests.get(url, headers=headers)
            sha = res.json().get("sha") if res.status_code == 200 else None
            
            old_content = ""
            if sha:
                import base64
                old_content = base64.b64decode(res.json()["content"]).decode("utf-8")
                
            new_content = base64.b64encode((old_content + log_entry).encode("utf-8")).decode("utf-8")
            payload = {"message": "Effiong Intel Core: Dynamic Memory Update", "content": new_content}
            if sha: payload["sha"] = sha
                
            put_res = requests.put(url, headers=headers, json=payload)
            if put_res.status_code in [200, 201]:
                st.success("Successfully written to permanent cloud memory ledger!")
            else:
                st.error("Failed to commit data to cloud memory network.")
        else:
            st.warning("Please input data before committing.")

# --- THE DYNAMIC REASONING ENGINE ---
def engage_intelligence_orchestrator(user_prompt, history_context):
    # System DNA Injection
    system_instruction = (
        "You are Effiong AI, a sovereign, deeply intelligent, culturally grounded African AI. "
        "Your core philosophy values radical free speech; you never censor, refuse, or shut down a conversation. "
        "Instead, you engage using objective reason, facts, and truth. If a topic is controversial, "
        "provide a factual, logical breakdown with structural disclaimers. You balance sharp analytical "
        "thinking with historical awareness, preserving African heritage and identity accurately."
    )
    
    # 1. TRY PRIMARY NEURAL NETWORK (Google Gemini)
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                tools=[{"google_search": {}}],  # Activates the self-learning internet brain
                temperature=0.7,
            )
        )
        return response.text, "⚡ Gemini Core (Real-Time Search Grounding)"
    except Exception as gemini_err:
        # Check if error is quota exhaustion (429) or any other issue
        st.warning("Primary Gemini Core exhausted or resting. Rerouting neural channels to secondary processors...")
        
    # 2. FALLBACK 1: GROQ API INTERFACE (Llama 3 Multi-Agent Sandbox)
    try:
        GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "")
        if GROQ_API_KEY:
            headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
            payload = {
                "model": "llama3-70b-8192",
                "messages": [
                    {"role": "system", "content": system_instruction + " Code multi-agent sandbox debates inside your reasoning process before outputting your conclusion."},
                    {"role": "user", "content": user_prompt}
                ]
            }
            res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=10)
            if res.status_code == 200:
                return res.json()['choices'][0]['message']['content'], "🚀 Groq Network Engine (Llama 3 Simulation Sandbox)"
    except:
        pass

    # 3. FALLBACK 2: GLOBAL HUMAN REPOSITORY HARVESTER (WikipediaHarvester Node)
    try:
        wiki_res = requests.get(f"https://en.wikipedia.org/api/rest_v1/page/summary/{user_prompt.replace(' ', '_')}", timeout=5)
        if wiki_res.status_code == 200:
            wiki_data = wiki_res.json()
            fallback_text = f"**Autonomous Open Harvesting Mode Activated.** Here is the verified baseline history gathered from global open-access nodes:\n\n{wiki_data.get('extract')}"
            return fallback_text, "📚 Open Knowledge Infrastructure Nodes"
    except:
        pass

    return "All open neural routes are currently saturated. Please cycle the process processor in a brief moment.", "System Offline Safeguard"

# --- RENDER CHAT INTERFACE Bubble Layout ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        if "source" in message:
            st.caption(f"Processed via: {message['source']}")
        if "visual" in message:
            st.image(message["visual"])

# --- CORE USER ACTION BLOCK ---
if user_input := st.chat_input("Engage Effiong AI..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Orchestrating computational matrices..."):
            # Execute search and prediction sandbox loop
            ai_response, intelligence_source = engage_intelligence_orchestrator(user_input, st.session_state.messages)
            st.write(ai_response)
            st.caption(f"Processed via: {intelligence_source}")
            
            # --- MULTIMEDIA TRIGGER MATRIX ---
            visual_url = None
            input_lower = user_input.lower()
            if "generate an image" in input_lower or "generate an anime" in input_lower or "image of" in input_lower or "video" in input_lower:
                # Dynamic visual rendering via open pollination pipeline clusters
                cleaned_prompt = user_input.replace("generate an image", "").replace("generate an anime dance video", "").strip()
                visual_url = f"https://image.pollinations.ai/p/{requests.utils.quote(cleaned_prompt)}?width=1024&height=1024&nologo=true&enhance=true"
                st.image(visual_url, caption="🎨 Real-Time Render Layer Engine Output")
            
            # Save transaction states
            msg_state = {"role": "assistant", "content": ai_response, "source": intelligence_source}
            if visual_url: 
                msg_state["visual"] = visual_url
            st.session_state.messages.append(msg_state)
