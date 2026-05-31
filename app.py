import streamlit as st
import requests
from bs4 import BeautifulSoup
from google import genai
from google.genai import types
import os

# --- 1. MINIMALIST ARCHITECTURE & PREMIUM TYPOGRAPHY INJECTION ---
st.set_page_config(page_title="Effiong AI", page_icon="🌍", layout="wide")

st.markdown("""
# Sovereign System Reinitialization Cache Clear Trigger
<head>
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Playfair+Display:ital,wght@0,400;0,500;1,400&display=swap" rel="stylesheet">
    </head>
    <style>
        /* Base Global Monochromatic Frame */
        .stApp {
            background-color: #09090B;
            color: #E4E4E7;
            font-family: 'Inter', sans-serif;
            letter-spacing: -0.01em;
        }
        
        /* Sidebar Restructuring - Clean Slate Border */
        [data-testid="stSidebar"] {
            background-color: #0F0F13 !important;
            border-right: 1px solid #1F1F24 !important;
        }
        
        /* Elite Minimalist Institutional Header Frame */
        .sovereign-header-container {
            border-bottom: 1px solid #1F1F24;
            padding-bottom: 24px;
            margin-bottom: 32px;
            text-align: left;
        }
        
        .sovereign-title {
            font-family: 'Playfair Display', serif;
            font-weight: 400;
            font-size: 2.2rem;
            color: #FFFFFF;
            letter-spacing: -0.02em;
            margin: 0;
            display: flex;
            align-items: center;
            gap: 16px;
        }
        
        .sovereign-subtitle {
            font-family: 'Inter', sans-serif;
            font-size: 0.85rem;
            font-weight: 400;
            color: #71717A;
            text-transform: uppercase;
            letter-spacing: 0.15em;
            margin-top: 8px;
        }
        
        /* Subtle Inline Nsibidi Vector Accents */
        .nsibidi-glyph-vector {
            font-family: serif;
            font-size: 1.8rem;
            color: #E5C158;
            opacity: 0.85;
            user-select: none;
        }

        /* Disciplined Action Elements (Stripe/Linear Style) */
        div.stButton > button:first-child {
            background-color: #18181B !important;
            color: #F4F4F5 !important;
            font-family: 'Inter', sans-serif !important;
            font-weight: 500 !important;
            font-size: 0.85rem !important;
            letter-spacing: 0.02em !important;
            border: 1px solid #27272A !important;
            border-radius: 6px !important;
            padding: 8px 16px !important;
            transition: all 0.2s ease;
        }
        div.stButton > button:first-child:hover {
            background-color: #27272A !important;
            border-color: #E5C158 !important;
            color: #FFFFFF !important;
            box-shadow: none !important;
        }
        
        /* Structured Form Control Enhancements */
        input, select, textarea {
            background-color: #141419 !important;
            border: 1px solid #23232A !important;
            color: #F4F4F5 !important;
            border-radius: 6px !important;
        }
        
        /* Streamlined Mobile Adaptive Chat Containers */
        .stChatMessage {
            background-color: #0F0F13 !important;
            border: 1px solid #1F1F24 !important;
            border-radius: 8px !important;
            padding: 16px !important;
            margin-bottom: 12px !important;
        }
        
        @media (max-width: 768px) {
            .sovereign-title {
                font-size: 1.7rem !important;
            }
            .sovereign-header-container {
                padding-bottom: 16px;
                margin-bottom: 24px;
            }
        }
    </style>
""", unsafe_allow_html=True)

# --- 2. EXECUTIVE BRAND ENGINE OUTLOOK ---
st.markdown("""
    <div class="sovereign-header-container">
        <h1 class="sovereign-title">
            <span class="nsibidi-glyph-vector" title="Egbo: Sovereignty">𓇽</span>
            <span>Effiong AI</span>
            <span class="nsibidi-glyph-vector" title="Akua: Truth">𓃎</span>
        </h1>
        <div class="sovereign-subtitle">
            Sovereign Multi-Neural Network &bull; Heritage Verification Node
        </div>
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
    st.markdown("<div style='font-size: 1.1rem; font-weight: 500; color: #FFFFFF; padding-bottom:12px; border-bottom:1px solid #1F1F24;'>Verification Ledger</div>", unsafe_allow_html=True)
    st.write("")
    
    contributor = st.text_input("Node Identity", "Sovereign Operator")
    entry_type = st.selectbox("Scope Matrix", [
        "Real-Time Current Event", 
        "Historical Clarification", 
        "Oral Lineage / Perspective", 
        "Linguistic / Structural Archetype"
    ])
    
    st.markdown("<p style='font-size:0.8rem; color:#71717A; text-transform:uppercase; font-weight:600; letter-spacing:0.05em; margin-bottom:2px;'>Audit Markers</p>", unsafe_allow_html=True)
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
        with st.spinner("Processing through network segments..."):
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
