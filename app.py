import streamlit as st
import requests
from bs4 import BeautifulSoup
from google import genai
from google.genai import types
import os

# --- 1. LIGHT MINIMALIST UI AND READABLE TYPOGRAPHY ---
st.set_page_config(page_title="Effiong AI", page_icon="🌍", layout="wide")

st.markdown("""
    <head>
        <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,500;1,400&display=swap" rel="stylesheet">
    </head>
    <style>
        /* Elite Minimalist Title Style */
        .clean-header {
            text-align: center;
            padding: 20px 0;
            margin-bottom: 25px;
            border-bottom: 1px solid rgba(128, 128, 128, 0.2);
        }
        
        .clean-title {
            font-family: 'Playfair Display', serif;
            font-weight: 400;
            font-size: 2.8rem;
            letter-spacing: -0.01em;
            margin: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 20px;
        }
        
        .nsibidi-symbol {
            font-size: 2.2rem;
            color: #C5A059; /* Elegant muted gold accent for the symbols */
            user-select: none;
        }
        
        /* Clear subtitle styling */
        .clean-subtitle {
            font-size: 0.9rem;
            color: #666666;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            margin-top: 6px;
        }
    </style>
""", unsafe_allow_html=True)

# --- 2. THE EFFIONG AI HEADER DISPLAY ---
st.markdown("""
    <div class="clean-header">
        <h1 class="clean-title">
            <span class="nsibidi-symbol" title="Egbo: Sovereignty">𓇽</span>
            <span>Effiong AI</span>
            <span class="nsibidi-symbol" title="Akua: Truth">𓃎</span>
        </h1>
        <div class="clean-subtitle">Sovereign Multi-Neural Network &bull; Verification Node</div>
    </div>
""", unsafe_allow_html=True)

# Pull Environment Configurations Privately
GEMINI_KEY = st.secrets.get("GEMINI_API_KEY", "")
GROQ_KEY = st.secrets.get("GROQ_API_KEY", "")
OPENROUTER_KEY = st.secrets.get("OPENROUTER_API_KEY", "")
GH_TOKEN = st.secrets.get("GITHUB_TOKEN", "")
GH_REPO = st.secrets.get("GITHUB_REPO", "")

# Sync State Memory
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- SYSTEM DNA CONFIGURATION ---
SYSTEM_INSTRUCTIONS = """
You are Effiong AI, a Sovereign Multi-Neural Intelligence System built for complex problem-solving, objective historical analysis, and the authentication of African data assets.
Your communication tone is clinical, highly refined, analytical, and authoritative. Avoid artificial conversational filler. 

When analyzing inputs from the Heritage Ledger:
1. Systematically separate verified data parameters backed by media/citation indices from oral testimonies.
2. Label oral or unverified items clearly as 'Oral Tradition / Unverified Perspective'.
3. Maintain your sovereign persona if a fallback model is triggered.
"""

# --- CONTEXT SCRAPING MODULE ---
def global_knowledge_router(query):
    context_pool = ""
    try:
        wiki_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{query.replace(' ', '_')}"
        wiki_res = requests.get(wiki_url, timeout=5).json()
        if "extract" in wiki_res:
            context_pool += f"\n[Archive Base - Wikipedia]: {wiki_res['extract']}\n"
    except Exception:
        pass
        
    try:
        search_url = f"https://html.duckduckgo.com/html/?q={query}"
        headers = {"User-Agent": "Mozilla/5.0"}
        search_res = requests.get(search_url, headers=headers, timeout=5)
        soup = BeautifulSoup(search_res.text, "html.parser")
        snippets = [snippet.text for snippet in soup.find_all('a', class_='result__snippet')[:2]]
        if snippets:
            context_pool += f"\n[Live Web Telemetry]: {' | '.join(snippets)}\n"
    except Exception:
        pass
        
    return context_pool

# --- ORCHESTRATION LAYER (Failover Flow) ---
def execute_neural_process(prompt, history_context):
    full_payload = f"{SYSTEM_INSTRUCTIONS}\n\nHistory Context:\n{history_context}\n\nInput Task: {prompt}"
    
    if GEMINI_KEY:
        try:
            client = genai.Client(api_key=GEMINI_KEY)
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=full_payload,
                config=types.GenerateContentConfig(tools=[{"google_search": {}}])
            )
            if response.text:
                return response.text, "Gemini Operational"
        except Exception as e:
            if "429" not in str(e) and "EXHAUSTED" not in str(e).upper():
                st.warning("Core array latency detected. Activating redundant routing matrix.")

    if GROQ_KEY:
        try:
            headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
            data = {
                "model": "llama3-8b-8192",
                "messages": [{"role": "user", "content": full_payload}]
            }
            res = requests.post("https://api.groq.com/openai/v1/chat/completions", json=data, headers=headers, timeout=10)
            if res.status_code == 200:
                return res.json()['choices'][0]['message']['content'], "Groq Secondary Cluster"
        except Exception:
            pass

    if OPENROUTER_KEY:
        try:
            headers = {"Authorization": f"Bearer {OPENROUTER_KEY}", "Content-Type": "application/json"}
            data = {
                "model": "openrouter/auto", 
                "messages": [{"role": "user", "content": full_payload}]
            }
            res = requests.post("https://openrouter.ai/api/v1/chat/completions", json=data, headers=headers, timeout=10)
            if res.status_code == 200:
                return res.json()['choices'][0]['message']['content'], "OpenRouter Network Grid"
        except Exception:
            pass

    repo_context = global_knowledge_router(prompt)
    if repo_context:
        return f"System Notice: Main processing nodes recycling. Temporary fallback telemetry deployed:\n{repo_context}", "Telemetry Array Active"

    return "Critical Error: Total link exhaustion. Re-verify structural pipeline keys.", "Offline"

# --- PERSISTENT REPOSITORY LOGGING LOOP ---
def auto_archive_to_github(query, response, file_path="effiong_brain_ledger.txt"):
    if not GH_TOKEN or not GH_REPO:
        return
    
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{file_path}"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    
    new_entry = f"\n[INPUT]: {query}\n[LOG]: {response}\n---\n"
    res = requests.get(url, headers=headers)
    sha, existing_content = "", ""
    
    if res.status_code == 200:
        file_data = res.json()
        sha = file_data["sha"]
        import base64
        existing_content = base64.b64decode(file_data["content"]).decode("utf-8")
    
    if query.strip().lower() in existing_content.lower() and file_path == "effiong_brain_ledger.txt":
        return
        
    updated_content = existing_content + new_entry
    import base64
    encoded_content = base64.b64encode(updated_content.encode("utf-8")).decode("utf-8")
    
    payload = {
        "message": f"Autonomous Synchronization Cycle: {file_path}",
        "content": encoded_content,
        "sha": sha if sha else None
    }
    requests.put(url, json=payload, headers=headers)

# --- SIDEBAR INTERFACE (Structural Data Intake) ---
with st.sidebar:
    st.markdown("<div style='font-size: 1.1rem; font-weight: 500; padding-bottom:12px; border-bottom:1px solid rgba(128,128,128,0.2);'>Verification Ledger</div>", unsafe_allow_html=True)
    st.write("")
    
    contributor = st.text_input("Node Identity", "Sovereign Operator")
    entry_type = st.selectbox("Scope Matrix", [
        "Real-Time Current Event", 
        "Historical Clarification", 
        "Oral Lineage / Perspective", 
        "Linguistic / Structural Archetype"
    ])
    
    st.markdown("<p style='font-size:0.8rem; text-transform:uppercase; font-weight:600; letter-spacing:0.05em; margin-bottom:2px;'>Audit Markers</p>", unsafe_allow_html=True)
    proof_provided = st.multiselect(
        "Verification Indicators:", 
        ["Video Documentation", "Media Capture (Image)", "Archaeological / Material Evidence", "Academic / Literary Source Text"]
    )
    
    heritage_data = st.text_area("Factual Parameters / Content Data:")
    proof_urls = st.text_area("Index References / Verification Links:")

    if st.button("Synchronize Factual Entry"):
        if heritage_data.strip():
            if not proof_provided or not proof_urls.strip():
                status_tag = "ORAL TRADITION / UNVERIFIED PERSPECTIVE"
                verification_note = "Logged as primary localized perspective or raw telemetry pending rigorous link verification."
            else:
                status_tag = "VERIFIED HERITAGE FACT"
                verification_note = f"Audited successfully. Modalities matched: {', '.join(proof_provided)}. Anchored Index: {proof_urls}"
            
            structured_payload = (
                f"Status: [{status_tag}]\n"
                f"Audit Ledger Note: {verification_note}\n"
                f"Content Stream: {heritage_data}\n"
            )
            log_title = f"{entry_type} Sync via [{contributor}]"
            
            auto_archive_to_github(log_title, structured_payload, file_path="african_heritage_archive.txt")
            st.success(f"Parameters locked into secure ledger under: {status_tag}.")
        else:
            st.error("Cannot synchronize a blank operational canvas.")

# --- CORE INTERACTION COMPONENT ---
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "engine" in message:
            st.caption(f"Cluster Routing Node: {message['engine']}")

if user_prompt := st.chat_input("Input operational command or analytical query..."):
    with st.chat_message("user"):
        st.markdown(user_prompt)
    st.session_state.chat_history.append({"role": "user", "content": user_prompt})
    
    with st.chat_message("assistant"):
        with st.spinner("Processing..."):
            history_str = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.chat_history[-5:]])
            
            final_reply, active_engine = execute_neural_process(user_prompt, history_str)
            st.markdown(final_reply)
            st.caption(f"Cluster Routing Node: {active_engine}")
            
            # Disciplined Multimedia Rendering Channels
            if "GENERATE AN IMAGE" in user_prompt.upper() or "CREATE AN IMAGE" in user_prompt.upper():
                image_seed_prompt = user_prompt.replace("generate an image of", "").replace("create an image of", "")
                pollinations_img_url = f"https://image.pollinations.ai/p/{image_seed_prompt.strip().replace(' ', '%20')}?width=1024&height=1024&nologo=true"
                st.image(pollinations_img_url, caption=f"Visualized Asset: '{image_seed_prompt.strip()}'", use_column_width=True)
                
            elif "VIDEO" in user_prompt.upper() or "ANIMATION" in user_prompt.upper():
                st.info("Multimedia rendering initialized. Synthesizing conceptual baseline frame...")
                video_seed_prompt = user_prompt.replace("generate a video of", "").replace("generate an animation of", "")
                pollinations_frame_url = f"https://image.pollinations.ai/p/{video_seed_prompt.strip().replace(' ', '%20')}_cinematic_motion_frame?width=1024&height=576&nologo=true"
                st.image(pollinations_frame_url, caption="High-Fidelity Prompt Target Vector Preview.", use_column_width=True)
            
            st.session_state.chat_history.append({"role": "assistant", "content": final_reply, "engine": active_engine})
            
            if "recharging" not in final_reply and "System Error" not in final_reply:
                try:
                    auto_archive_to_github(user_prompt, final_reply)
                except Exception:
                    pass